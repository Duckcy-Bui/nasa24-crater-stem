"""S2-06/S3-02: frozen-config NumPy/OpenCV comparison and label integrity audit.

Run tuning before holdout. Real sparse labels permit Recall_known only.
The audit checks file consistency, not whether a person visually reviewed labels.
"""

from __future__ import annotations
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json, validate_crater_set
from src.evaluation import evaluate
from src.hough import detect_circles, resolve_hough_params
from src.pipeline import load_image, radius_range
from src.preprocessing import preprocess
from src.postprocessing import dedupe_circles
from src.scoring import reference_is_reviewed
from scripts.verify_hough_examples import tiny_example


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def code_version(repo=ROOT):
    """Return HEAD, marking it only when Git reports working-tree changes."""
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return revision + ("+working-tree" if status else "")


def summarize_report(report):
    """Keep provenance and per-image results without predictions or pair lists."""
    keys = (
        "status",
        "created_at_utc",
        "split",
        "params",
        "config_sha256",
        "manifest_sha256",
        "environment",
        "code_version",
        "source_sha256",
        "repeats",
        "warmups",
        "limitations",
        "aggregate",
    )
    summary = {key: report[key] for key in keys}
    summary["candidate_selection_by_method"] = {
        "numpy_score": "score",
        "numpy_balanced": "radius_balanced",
    }
    summary["label_audit_status"] = report["label_audit"]["status"]
    summary["images"] = []
    for image in report["images"]:
        row = {
            key: image[key]
            for key in (
                "image_id",
                "radius_px",
                "preprocess_params",
                "seconds_preprocess",
                "input_sha256",
                "label_sha256",
                "opencv_params",
            )
        }
        row["methods"] = {}
        for name, method in image["methods"].items():
            metrics = {
                key: method["metrics"][key]
                for key in ("tp", "fp", "fn", "precision", "recall", "f1")
            }
            row["methods"][name] = dict(
                **metrics,
                median_seconds=method["timing"]["median_seconds"],
                candidate_count=(
                    method["candidate_count"]
                    if "candidate_count" in method
                    else len(method["circles"])
                ),
                radii_gt16=method["radii_gt16"],
                after_dedupe={
                    key: method["dedupe"]["metrics"][key]
                    for key in ("tp", "fn", "recall")
                },
            )
        summary["images"].append(row)
    return summary


def audit_labels(manifest, processed):
    index = read_json(ROOT / "data/s203_split/label_index.json")
    rows = []
    for item in manifest["images"]:
        ident = item["image_id"]
        path = ROOT / "data/reference_labels" / item["reference_label_file"]
        ref = read_json(path)
        meta = read_json(processed / (ident + ".json"))
        validate_crater_set(ref, meta)
        uncertain = sum("uncertain" in c["crater_id"].lower() for c in ref["circles"])
        checks = dict(
            file_count=item["n_labels"]
            == len(ref["circles"])
            == index[ident]["n_circles"],
            uncertain_count=item["n_uncertain"]
            == uncertain
            == index[ident]["n_uncertain"],
            review_marker=reference_is_reviewed(ref),
            split=item["split"] == index[ident]["split"],
            overlay_exists=path.with_name(ident + "_overlay.png").exists(),
        )
        rows.append(
            dict(
                image_id=ident,
                split=item["split"],
                sha256=digest(path),
                reference_source=ref["reference_source"],
                checks=checks,
                outside_search_ids=[
                    c["crater_id"]
                    for c in ref["circles"]
                    if not meta["radius"]["r_min_px"]
                    <= c["r"]
                    <= meta["radius"]["r_max_px"]
                ],
            )
        )
    return dict(
        status="pass" if all(all(x["checks"].values()) for x in rows) else "failed",
        images=rows,
        visual_review_confirmation=read_json(
            ROOT / "data/reference_labels/review_confirmation.json"
        ),
    )


def measure(function, repeats):
    function()  # warm-up excluded
    timings = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = function()
        timings.append(time.perf_counter() - start)
    return result, dict(
        samples_seconds=timings,
        median_seconds=float(np.median(timings)),
        min_seconds=min(timings),
        max_seconds=max(timings),
    )


def run_one(ident, params, processed, repeats):
    import cv2

    meta, image, valid = load_image(ident, processed)
    ref = read_json(
        ROOT / "data/reference_labels" / (ident + "_craters_catalogue.json")
    )
    start = time.perf_counter()
    pre = preprocess(image, meta, valid_mask=valid)
    pre_seconds = time.perf_counter() - start
    lo, hi = radius_range(meta, params)
    gray = np.rint(np.clip(pre["smooth"], 0, 1) * 255).astype(np.uint8)
    cvparams = dict(
        dp=1.0, minDist=4.0, param1=100.0, param2=12.0, minRadius=lo, maxRadius=hi
    )

    def opencv():
        raw = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, **cvparams)
        return (
            []
            if raw is None
            else [
                dict(
                    crater_id=f"CV{i}",
                    x=float(x),
                    y=float(y),
                    r=float(radius),
                    confidence=None,
                    votes=None,
                )
                for i, (x, y, radius) in enumerate(raw[0], 1)
                if 0 <= x <= 511 and 0 <= y <= 511
            ]
        )

    variants = {
        "numpy_score": lambda: detect_circles(
            pre["edges"],
            lo,
            hi,
            dict(params, candidate_selection="score"),
            theta=pre["theta"],
        ),
        "numpy_balanced": lambda: detect_circles(
            pre["edges"],
            lo,
            hi,
            dict(params, candidate_selection="radius_balanced"),
            theta=pre["theta"],
        ),
        "opencv": opencv,
    }
    result = dict(
        image_id=ident,
        radius_px=[lo, hi],
        preprocess_params=pre["params"],
        seconds_preprocess=pre_seconds,
        input_sha256={
            name: digest(processed / (ident + name)) for name in (".json", ".npy")
        },
        label_sha256=digest(
            ROOT / "data/reference_labels" / (ident + "_craters_catalogue.json")
        ),
        opencv_params=cvparams,
        methods={},
    )
    for method, fn in variants.items():
        circles, timing = measure(fn, repeats)
        machine = dict(
            schema_version="1.0",
            data_kind=meta["data_kind"],
            image_id=ident,
            source="machine",
            reference_source=None,
            circles=circles,
        )
        metrics = evaluate(machine, ref, dict(metadata=meta))
        kept, removed, report = dedupe_circles(circles)
        after = evaluate(dict(machine, circles=kept), ref, dict(metadata=meta))
        result["methods"][method] = dict(
            timing=timing,
            circles=circles,
            metrics=metrics,
            radii_gt16=sum(c["r"] > 16 for c in circles),
            dedupe=dict(report=report, metrics=after),
        )
    return result


def main():
    import cv2

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--holdout", action="store_true")
    parser.add_argument("--images", nargs="+")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats phải >= 1")
    params = resolve_hough_params(read_json(args.config))
    manifest = read_json(ROOT / "data/s203_split/manifest_split.json")
    split = "holdout" if args.holdout else "tuning"
    selected = [
        i
        for i in manifest["images"]
        if i["split"] == split and (not args.images or i["image_id"] in args.images)
    ]
    if not selected or (
        args.images and set(args.images) != {i["image_id"] for i in selected}
    ):
        parser.error("Ảnh không tồn tại hoặc nằm ngoài tập đã chọn.")
    cv2.setNumThreads(1)
    # Freeze all configuration/source identities before touching holdout images.
    report = dict(
        status="running",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        split=split,
        params=params,
        config_sha256=digest(args.config),
        manifest_sha256=digest(ROOT / "data/s203_split/manifest_split.json"),
        environment=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            opencv=cv2.__version__,
            platform=platform.platform(),
            processor=platform.processor(),
            opencv_threads=cv2.getNumThreads(),
        ),
        code_version=code_version(),
        source_sha256={
            p: digest(ROOT / p)
            for p in (
                "src/hough.py",
                "src/evaluation.py",
                "src/matching.py",
                "src/preprocessing.py",
                "src/postprocessing.py",
                "scripts/evaluate_hough.py",
            )
        },
        repeats=args.repeats,
        warmups=1,
        images=[],
        limitations=[
            "Sparse labels: FP/Precision/F1 unknown; only recall on known labels.",
            "Reviewer statement is recorded in label_audit; file checks are not independent visual review.",
            "NumPy timing excludes preprocessing; OpenCV includes internal edge detection.",
            "Common smoothed gray and radius bounds; edges/thresholds/NMS differ.",
            "OpenCV centers outside [0,511] are excluded to match the public NumPy contract.",
            "Both selection policies fixed before holdout; no parameter search.",
            "Dedupe measured separately; production pipeline is unchanged.",
        ],
    )
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "report.json", report)
    try:
        report["label_audit"] = audit_labels(manifest, args.processed_dir)
        if report["label_audit"]["status"] != "pass":
            raise ValueError("Kiểm tra tính nhất quán của nhãn thất bại")
        report["tiny_example"] = tiny_example()
        for item in selected:
            result = run_one(item["image_id"], params, args.processed_dir, args.repeats)
            report["images"].append(result)
            save(args.output / (item["image_id"] + ".json"), result)
            save(args.output / "report.json", report)
            print(
                item["image_id"],
                {
                    k: (v["metrics"]["tp"], v["metrics"]["fn"], v["radii_gt16"])
                    for k, v in result["methods"].items()
                },
                flush=True,
            )
        report["aggregate"] = {}
        for method in ("numpy_score", "numpy_balanced", "opencv"):
            rows = [i["methods"][method]["metrics"] for i in report["images"]]
            tp = sum(x["tp"] for x in rows)
            fn = sum(x["fn"] for x in rows)
            recalls = [x["recall"] for x in rows if x["recall"] is not None]
            report["aggregate"][method] = dict(
                tp=tp,
                fn=fn,
                fp=None,
                precision=None,
                f1=None,
                recall_known_micro=tp / (tp + fn) if tp + fn else None,
                recall_known_macro_mean=float(np.mean(recalls)) if recalls else None,
                recall_known_macro_std=(
                    float(np.std(recalls, ddof=1)) if len(recalls) > 1 else None
                ),
            )
        fields = [
            "image_id",
            "method",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
            "median_seconds",
            "radii_gt16",
        ]
        with (args.output / "results.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for image in report["images"]:
                for method, row in image["methods"].items():
                    writer.writerow(
                        dict(
                            image_id=image["image_id"],
                            method=method,
                            **{
                                k: row["metrics"][k]
                                for k in ("tp", "fp", "fn", "precision", "recall", "f1")
                            },
                            median_seconds=row["timing"]["median_seconds"],
                            radii_gt16=row["radii_gt16"],
                        )
                    )
        report["status"] = "complete"
    except BaseException as exc:
        report.update(status="error", error=str(exc))
        raise
    finally:
        save(args.output / "report.json", report)
    save(args.output / "summary.json", summarize_report(report))
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
