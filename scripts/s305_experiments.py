"""S3-05: run the S2-07 experiments with the S2-15 frozen baseline.

Writes new evidence only; never tunes the game or overwrites an existing run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import dưới đây đặt sau cấu hình backend/sys.path ở trên; giữ thứ tự (E402).
import cv2  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402
import numpy as np  # noqa: E402

from scripts.s207_experiments import (  # noqa: E402
    DEFAULT_IMAGES,
    PARAMETER_VARIANTS,
    e1_status,
    recall_summary,
    shading_match_distribution,
    split_by_image,
)
from src.contracts import read_json  # noqa: E402
from src.evaluation import evaluate  # noqa: E402
from src.hough import resolve_hough_params  # noqa: E402
from src.pipeline import detect_machine, load_image  # noqa: E402
from src.postprocessing import (  # noqa: E402
    DEFAULT_PARAMS as SHADING_DEFAULTS,
    apply_filter,
    dedupe_circles,
    review_candidates,
)
from src.scoring import reference_is_reviewed  # noqa: E402

TUNING = tuple(DEFAULT_IMAGES)
MARE = "moon_marefrig_loc_c01"


def sha(path):
    """Nhận path (Path); trả SHA-256 của byte file, không sửa file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    """Ghi value dạng JSON hữu hạn vào path (Path), tạo cha nếu thiếu; trả None.

    Có thể ghi đè file; đây là tiện ích lưu, không có công thức riêng.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def validate_scope(splits, frozen, active):
    """Kiểm splits và hai dict cấu hình frozen/active, trả None hoặc ValueError.

    Đòi cấu hình bằng nhau, ba ảnh chỉ định thuộc tuning và Mare thuộc
    holdout; không đọc/ghi file hay tự chọn tham số, theo mục 4.4.
    """
    if frozen != active:
        raise ValueError("Game config differs from S2-15; do not silently change the baseline.")
    if any(splits.get(i) != "tuning" for i in TUNING) or splits.get(MARE) != "holdout":
        raise ValueError("Expected S2-03 tuning/holdout scope changed; review the protocol first.")


def parameter_variants(image_id, splits):
    """Nhận image_id và splits (dict); trả PARAMETER_VARIANTS chung nếu là tuning.

    Ảnh khác tuning gây ValueError; không sao chép dict hay ghi file, mục 4.6.
    """
    if splits.get(image_id) != "tuning":
        raise ValueError("E2 parameter sweeps are forbidden on holdout.")
    return PARAMETER_VARIANTS


def plot_panels(path, gray, reference, panels, title):
    """Ghi ảnh so nhánh vào path (Path) từ gray 2D, reference và panels.

    panels chứa (tên, vòng giữ, vòng loại, độ đo, cờ tô sáng–tối), title là
    tiêu đề; tâm/r theo px. Trả None, đóng figure sau ghi PNG; màu không
    khẳng định vòng ngoài nhãn là FP, theo phạm vi nhãn thưa ở mục 4.6.
    """
    fig, axes = plt.subplots(1, len(panels), figsize=(max(6, 5 * len(panels)), 6.2), squeeze=False)
    for ax, (name, circles, removed, metrics, shading) in zip(axes[0], panels):
        ax.imshow(gray, cmap="gray", vmin=0, vmax=1, extent=(-0.5, 511.5, 511.5, -0.5))
        matched = {p["prediction_id"] for p in metrics["pairs"]}
        colors = {
            "consistent": "lime",
            "inverted": "magenta",
            "unclear": "cyan",
            "not_checked": "silver",
        }
        for c in circles:
            color = (
                colors.get((c.get("shading") or {}).get("status"), "cyan")
                if shading
                else ("lime" if c["crater_id"] in matched else "cyan")
            )
            ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color=color, lw=0.6))
        for c in removed:
            ax.add_patch(
                Circle((c["x"], c["y"]), c["r"], fill=False, color="red", ls="--", lw=0.7)
            )
        for c in reference["circles"]:
            if "uncertain" in c["crater_id"].lower():
                continue
            ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color="orange", lw=1.3))
            ax.text(c["x"], c["y"], c["crater_id"], color="orange", fontsize=6)
        ax.set(
            xlim=(-0.5, 511.5),
            ylim=(511.5, -0.5),
            title=(
                f"{name}\nN={len(circles)}, "
                f"TP_known={metrics['tp']}/{metrics['known_references']}"
            ),
        )
        ax.tick_params(labelsize=7)
    labels = [("orange", "Known reference"), ("red", "Removed (experimental)")]
    if any(p[4] for p in panels):
        labels += [
            ("lime", "Shading consistent"),
            ("magenta", "Shading inverted"),
            ("cyan", "Shading unclear / raw"),
            ("silver", "Not checked"),
        ]
    else:
        labels += [("lime", "Matched known label"), ("cyan", "Unmatched (not necessarily false)")]
    fig.legend(
        handles=[Line2D([], [], color=c, label=l) for c, l in labels],
        loc="lower center",
        ncol=1 if len(panels) == 1 else 3,
        fontsize=8,
    )
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=(0, 0.2 if len(panels) == 1 else 0.12, 1, 0.91))
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main(argv=None):
    """Nhận argv (list str hoặc None); chạy S3-05 và trả 0 khi hoàn tất.

    Đọc cấu hình S2-15, split, ảnh/nhãn; tạo --output mới với report,
    snapshot cấu hình, ba CSV cùng JSON/PNG từng nhánh. Không đổi game;
    E2 chỉ tuning, Mare chỉ mô tả nền. Một lượt/cấu hình, mục 4.4/4.6.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New, non-existing run directory"
    )
    args = parser.parse_args(argv)
    config = read_json(ROOT / "configs/s215_frozen.json")
    splits = split_by_image()
    validate_scope(splits, config, read_json(ROOT / "configs/default.json"))
    ids = (*TUNING, MARE)
    for image_id in ids:
        ref = read_json(ROOT / f"data/reference_labels/{image_id}_craters_catalogue.json")
        if not reference_is_reviewed(ref):
            raise ValueError(f"Unreviewed reference: {image_id}")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in ("E1", "E2", "E3", "configs"):
        (out / name).mkdir()
    cv2.setNumThreads(1)
    sources = [
        Path(__file__),
        ROOT / "scripts/s207_experiments.py",
        ROOT / "configs/s215_frozen.json",
        ROOT / "configs/default.json",
        ROOT / "data/s203_split/manifest_split.json",
        ROOT / "data/s203_split/label_index.json",
        ROOT / "data/s111_sun_checks.json",
        ROOT / "data/reference_labels/review_confirmation.json",
    ]
    sources += list((ROOT / "src").glob("*.py"))
    sources += list(ROOT.glob("requirements*.txt"))
    for image_id in ids:
        sources += [
            ROOT / f"data/processed/{image_id}{suffix}"
            for suffix in (".npy", ".json", "_valid_mask.npy")
        ]
        sources.append(ROOT / f"data/reference_labels/{image_id}_craters_catalogue.json")
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    report = {
        "task_id": "S3-05",
        "status": "running",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_at_start": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ),
        "source_and_input_sha256": hashes,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "opencv": cv2.__version__,
            "matplotlib": matplotlib.__version__,
            "platform": platform.platform(),
            "opencv_threads": 1,
        },
        "protocol": {
            "tuning": list(TUNING),
            "holdout_descriptive": [MARE],
            "baseline": "S2-15 score policy; shading annotation only",
            "E2": "S2-07 one factor at a time; tuning only; no production selection",
            "E3_holdout": "Frozen baseline and class distribution only; no filtering sweeps",
            "metric": "reviewed sparse labels; Recall_known only; FP/Precision/F1 null",
            "timing": "one run per variant; no warm-up; diagnostic timing, not a speed benchmark",
            "holdout": (
                "previously inspected; repeated descriptive evaluation, not unseen validation"
            ),
        },
        "shading_defaults": SHADING_DEFAULTS,
        "images": [],
    }
    tables = {e: [] for e in ("E1", "E2", "E3")}
    save(out / "configs/baseline.json", config)
    for name, override in PARAMETER_VARIANTS.items():
        save(
            out / f"configs/{name}.json",
            {**config, "hough": resolve_hough_params({**config["hough"], **override})},
        )
    save(out / "report.json", report)
    try:
        for image_id in ids:
            print(f"{image_id}: baseline", flush=True)
            metadata, image, valid = load_image(image_id, ROOT / "data/processed")
            reference = read_json(
                ROOT / f"data/reference_labels/{image_id}_craters_catalogue.json"
            )
            detected = detect_machine(
                metadata,
                image,
                valid,
                hough_params=config["hough"],
                preprocess_params=config["preprocess"],
            )
            raw, shaded = detected["raw_circles"], detected["machine"]["circles"]
            sun_counts = detected["postprocess"]["shading_counts"]
            status = e1_status(
                splits[image_id], any(k != "not_checked" and v for k, v in sun_counts.items())
            )
            details = {
                "image_id": image_id,
                "split": splits[image_id],
                "sun": metadata["sun"],
                "scale_m_per_px": metadata["scale_m_per_px"],
                "E1_status": status,
                "shading_counts": sun_counts,
                "shading_by_label_match": shading_match_distribution(shaded, reference),
            }

            def record(
                experiment,
                name,
                circles,
                removed=(),
                detection=None,
                scope="tuning_diagnostic",
                configuration="baseline",
            ):
                """Đánh giá circles của nhánh name thuộc experiment và lưu chi tiết.

                removed là vòng loại; detection hoặc kết quả nền cung cấp ảnh/tham số;
                scope/configuration là tên phạm vi/cấu hình. Dùng image_id/out/tables
                của main, ghi JSON nhánh và thêm dòng CSV trong bộ nhớ; trả dict độ đo
                (2.20)–(2.23), r theo px, thời gian Hough theo giây; nhãn thưa giữ null.
                """
                d = detection if detection is not None else detected
                machine = {**d["machine"], "circles": circles}
                metrics = evaluate(
                    machine, reference, {**config["evaluation"], "metadata": metadata}
                )
                if metrics["status"] != "evaluated":
                    raise ValueError(f"Evaluation unavailable: {image_id}: {metrics}")
                diagnostic = recall_summary(
                    circles,
                    reference,
                    radius_bounds=(d["r_min"], d["r_max"]),
                    max_circles=d["hough"]["max_circles"],
                )
                row = {
                    "image_id": image_id,
                    "split": splits[image_id],
                    "variant": name,
                    "scope": scope,
                    "configuration": configuration,
                    "candidates": len(circles),
                    "removed": len(removed),
                    "tp_known": metrics["tp"],
                    "fn_known": metrics["fn"],
                    "known_labels": metrics["known_references"],
                    "recall_known": metrics["recall"],
                    "precision": None,
                    "f1": None,
                    "seconds_hough": d["seconds_hough"],
                    "r_min_px": d["r_min"],
                    "r_max_px": d["r_max"],
                    "radius_step_px": d["hough"]["radius_step_px"],
                    "input_hit_max_circles": len(d["raw_circles"]) >= d["hough"]["max_circles"],
                    "known_labels_outside_search": diagnostic["reference_radius_outside_search"],
                }
                tables[experiment].append(row)
                save(
                    out / experiment / f"{image_id}_{name}.json",
                    {
                        **row,
                        "machine": machine,
                        "removed_circles": list(removed),
                        "reference": reference,
                        "metrics": metrics,
                        "diagnostics": diagnostic,
                        "preprocess": d["pre"]["params"],
                        "hough": d["hough"],
                        "radius_grid_px": list(
                            range(d["r_min"], d["r_max"] + 1, d["hough"]["radius_step_px"])
                        ),
                    },
                )
                return metrics

            inverted_kept, inverted_removed = apply_filter(shaded, remove_shading=("inverted",))
            panels = []
            # On holdout/no usable sun, preserve the raw result but do not claim an E1 comparison.
            e1_branches = [("raw", raw, [], True)]
            if status == "diagnostic_tuning_only":
                e1_branches += [
                    ("shading_annotation", shaded, [], True),
                    ("remove_inverted", inverted_kept, inverted_removed, True),
                ]
            for name, circles, removed, coloring in e1_branches:
                m = record("E1", name, circles, removed, scope=status)
                panels.append((name, circles, removed, m, coloring))
            plot_panels(
                out / "E1" / f"{image_id}.png",
                image,
                reference,
                panels,
                f"E1 | {image_id} | {status}",
            )

            if splits[image_id] == "tuning":
                panels = []
                for name, override in parameter_variants(image_id, splits).items():
                    print(f"{image_id}: E2 {name}", flush=True)
                    d = (
                        detected
                        if name == "baseline"
                        else detect_machine(
                            metadata,
                            image,
                            valid,
                            hough_params=resolve_hough_params({**config["hough"], **override}),
                            preprocess_params=config["preprocess"],
                        )
                    )
                    m = record("E2", name, d["raw_circles"], detection=d, configuration=name)
                    panels.append((name, d["raw_circles"], [], m, False))
                plot_panels(
                    out / "E2" / f"{image_id}.png",
                    image,
                    reference,
                    panels,
                    f"E2 | {image_id} | tuning only",
                )

            reviewed, review_report = review_candidates(shaded, detected["pre"])
            details["review_report"] = review_report
            e3_branches = [("baseline", reviewed, [])]
            if splits[image_id] == "tuning":
                kept, removed = apply_filter(reviewed, remove_classes=("texture",))
                e3_branches.append(("remove_texture", kept, removed))
                kept, removed, dedupe_report = dedupe_circles(reviewed)
                details["dedupe_report"] = dedupe_report
                e3_branches.append(("dedupe", kept, removed))
            panels = []
            for name, circles, removed in e3_branches:
                m = record(
                    "E3",
                    name,
                    circles,
                    removed,
                    scope=(
                        "tuning_diagnostic"
                        if splits[image_id] == "tuning"
                        else "holdout_descriptive_only"
                    ),
                )
                panels.append((name, circles, removed, m, False))
            plot_panels(
                out / "E3" / f"{image_id}.png",
                image,
                reference,
                panels,
                f"E3 | {image_id} | {splits[image_id]}",
            )
            report["images"].append(details)
            save(out / "report.json", report)
            print(f"{image_id}: saved E1/E2/E3 artifacts", flush=True)
        for experiment, rows in tables.items():
            with (out / f"{experiment}.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        changed = [p for p, digest in hashes.items() if sha(ROOT / p) != digest]
        if changed:
            raise ValueError(f"Source/input changed during execution: {changed}")
        report["artifacts_sha256"] = {
            p.relative_to(out).as_posix(): sha(p)
            for p in sorted(out.rglob("*"))
            if p.is_file() and p.name != "report.json"
        }
        report.update(
            status="complete",
            completed_at_utc=datetime.now(timezone.utc).isoformat(),
            table_rows={e: len(rows) for e, rows in tables.items()},
        )
    except BaseException as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        save(out / "report.json", report)
    print(f"S3-05 complete: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
