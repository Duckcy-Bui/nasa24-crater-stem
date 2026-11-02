"""S2-15: verify the frozen game configuration on tuning images only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import dưới đây đặt sau cấu hình backend/sys.path ở trên; giữ thứ tự (E402).
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from src.contracts import read_json  # noqa: E402
from src.evaluation import evaluate  # noqa: E402
from src.hough import resolve_hough_params  # noqa: E402
from src.pipeline import detect_machine, load_image  # noqa: E402
from src.postprocessing import DEFAULT_PARAMS as SHADING_DEFAULTS  # noqa: E402
from src.preprocessing import DEFAULT_PARAMS as PRE_DEFAULTS  # noqa: E402


def digest(path):
    """Băm file nguồn/cấu hình/đầu vào của phép kiểm cấu hình game.

    Vào: path. Ra: SHA-256 dạng hex; không ghi file, không có công thức báo cáo.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    """Lưu dữ liệu JSON của lượt kiểm cấu hình.

    Vào: path là file đích, data là dữ liệu cần tuần tự hóa. Ra: None; ghi JSON UTF-8 tại path.
    Công thức báo cáo: không áp dụng cho thao tác I/O.
    """
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_selection(manifest, image_ids=None):
    """Chỉ nhận danh sách ảnh tuning duy nhất trong manifest.

    Vào: manifest chia tập và image_ids tùy chọn. Ra: list ảnh tuning được chọn hoặc ValueError.
    Quy tắc tách tập theo mục 4.4; không đọc dữ liệu holdout.
    """
    tuning = [i["image_id"] for i in manifest["images"] if i["split"] == "tuning"]
    if image_ids is None:
        return tuning
    if not image_ids or len(set(image_ids)) != len(image_ids) or not set(image_ids) <= set(tuning):
        raise ValueError("S2-15 accepts unique tuning image IDs only; holdout is forbidden.")
    return image_ids


def validate_config(frozen, active):
    """Kiểm cấu hình game trùng snapshot và khai báo đủ tham số.

    Vào: frozen và active là dict cấu hình. Ra: None nếu hợp lệ, ValueError khi lệch/thiếu.
    Giữ lựa chọn tham số mục 3.3/4.4, không có công thức toán riêng.
    """
    if frozen != active:
        raise ValueError(
            "Game config differs from S2-15 snapshot; freeze and evaluate a new version."
        )
    if set(frozen["hough"]) != set(resolve_hough_params(frozen)):
        raise ValueError("Frozen Hough parameters must be explicit.")
    if set(frozen["preprocess"]) != set(PRE_DEFAULTS):
        raise ValueError("Frozen preprocessing parameters must be explicit.")


def main():
    """Đánh giá cấu hình đóng băng trên tuning và ghi nguồn thực tế.

    Vào: CLI output/images; đọc snapshot, cấu hình game, manifest, ảnh và nhãn đã kiểm.
    Ra: None; tạo output mới, ghi report.json tổng hợp và JSON từng ảnh, in TP/FN.
    Recall_known gộp theo (2.23)/(4.1); không tìm tham số hoặc dùng holdout.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--images", nargs="+")
    args = parser.parse_args()
    frozen_path = ROOT / "configs/s215_frozen.json"
    config = read_json(frozen_path)
    validate_config(config, read_json(ROOT / "configs/default.json"))
    manifest_path = ROOT / "data/s203_split/manifest_split.json"
    selected = validate_selection(read_json(manifest_path), args.images)
    cv2.setNumThreads(1)
    files = [
        "app.py",
        "scripts/freeze_s215.py",
        "configs/default.json",
        "configs/s215_frozen.json",
        "data/s203_split/manifest_split.json",
        "data/s203_split/label_index.json",
        "data/reference_labels/review_confirmation.json",
        "data/s111_sun_checks.json",
        "requirements.txt",
        "requirements-test.txt",
    ]
    files += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "src").rglob("*.py"))]
    report = {
        "schema_version": "s215-freeze-1",
        "status": "running",
        "split": "tuning",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_version": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_status_at_start": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ),
        "source_identity_note": 'Working tree bytes are identified by SHA-256; HEAD is the base '
        'commit.',
        "config": config,
        "source_sha256": {f: digest(ROOT / f) for f in files},
        "shading_defaults": SHADING_DEFAULTS,
        "postprocess_policy": {
            "shading": "annotation_only",
            "dedupe": False,
            "remove_texture": False,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "opencv": cv2.__version__,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "opencv_threads": 1,
        },
        "timing_note": "One run per image, no warm-up: diagnostic timing, not a speed benchmark.",
        "selection_note": 'Retain production score policy; no parameter search or holdout '
        'reads in this run.',
        "images": [],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    save(args.output / "report.json", report)
    try:
        for image_id in selected:
            metadata, image, valid = load_image(image_id, ROOT / "data/processed")
            label_path = ROOT / f"data/reference_labels/{image_id}_craters_catalogue.json"
            label = read_json(label_path)
            paths = [
                ROOT / f"data/processed/{image_id}{suffix}"
                for suffix in (".json", ".npy", "_valid_mask.npy")
            ]
            paths.append(label_path)
            hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths if p.exists()}
            detected = detect_machine(
                metadata,
                image,
                valid,
                hough_params=config["hough"],
                preprocess_params=config["preprocess"],
            )
            metrics = evaluate(
                detected["machine"], label, {**config["evaluation"], "metadata": metadata}
            )
            if metrics["status"] != "evaluated":
                raise ValueError(f"Labels cannot be evaluated: {image_id}: {metrics}")
            row = {
                "image_id": image_id,
                "split": "tuning",
                "input_sha256": hashes,
                "radius_bounds_px": [detected["r_min"], detected["r_max"]],
                "candidates": len(detected["machine"]["circles"]),
                "hit_max_circles": len(detected["raw_circles"]) >= config["hough"]["max_circles"],
                "seconds_preprocess": detected["seconds_preprocess"],
                "seconds_hough": detected["seconds_hough"],
                "postprocess": detected["postprocess"],
                "metrics": metrics,
            }
            save(args.output / f"{image_id}.json", {**row, "machine": detected["machine"]})
            report["images"].append(row)
            save(args.output / "report.json", report)
            print(f"{image_id}: TP={metrics['tp']} FN={metrics['fn']}", flush=True)
        tp = sum(i["metrics"]["tp"] for i in report["images"])
        fn = sum(i["metrics"]["fn"] for i in report["images"])
        report["aggregate"] = {
            "images": len(selected),
            "tp_known": tp,
            "fn_known": fn,
            "recall_known_micro": tp / (tp + fn) if tp + fn else None,
            "fp": None,
            "precision": None,
            "f1": None,
        }
        changed = [f for f, sha in report["source_sha256"].items() if digest(ROOT / f) != sha]
        if changed:
            raise ValueError(f"Source changed during evaluation: {changed}")
        report["status"] = "complete"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        save(args.output / "report.json", report)


if __name__ == "__main__":
    main()
