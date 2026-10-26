"""S2-07: chạy các kịch bản thí nghiệm có thể tái tạo.

Không suy Precision/F1 từ nhãn thưa.  Với S1-11, holdout có sun.quality=none
nên script chỉ ghi trạng thái not_evaluable_on_holdout; số liệu so sánh (nếu có)
chỉ là chẩn đoán trên tuning Apollo 16.

Ví dụ:
    python scripts/s207_experiments.py --write
    python scripts/s207_experiments.py --images moon_ap16_m132732855l_c01 --write
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.contracts import read_json
from src.hough import resolve_hough_params
from src.matching import CENTER_TOLERANCE, match_one_to_one
from src.pipeline import detect_machine, load_image
from src.postprocessing import apply_filter, dedupe_circles, review_candidates

DEFAULT_IMAGES = (
    "moon_ap16_m132732855l_c01",  # tuning, bóng mạnh; đã dùng khảo sát S2-02
    "moon_ap16_m102064759r_c01",  # tuning, Apollo 16, nắng xiên
    "moon_ap16_m109134835l_c01",  # tuning, nắng gần đứng; S1-11 bỏ qua
    "moon_ap15_loc_c01",          # holdout 20 m/px
    "moon_marefrig_loc_c01",      # holdout 20 m/px, mare phẳng
)

PARAMETER_VARIANTS = {
    "baseline": {},
    "min_vote_ratio_030": {"min_vote_ratio": 0.30},
    "min_vote_ratio_040": {"min_vote_ratio": 0.40},
    "radius_step_2": {"radius_step_px": 2},
}


def known_references(reference: dict[str, Any]) -> list[dict[str, Any]]:
    """Nhãn uncertain không thuộc mẫu Recall chính thức."""
    return [c for c in reference["circles"] if "uncertain" not in c["crater_id"].lower()]


def recall_summary(circles: list[dict[str, Any]], reference: dict[str, Any]) -> dict[str, Any]:
    refs = known_references(reference)
    pairs = match_one_to_one(circles, refs, CENTER_TOLERANCE)
    found = {p["reference_id"] for p in pairs}
    return {
        "known_labels": len(refs),
        "true_positive_known": len(pairs),
        "missed_reference_ids": [c["crater_id"] for c in refs if c["crater_id"] not in found],
        "recall_known": round(len(pairs) / len(refs), 4) if refs else None,
        "precision": None,
        "f1": None,
        "metric_note": "Nhãn sparse: chỉ Recall trên hố đã biết; không suy Precision/F1 toàn ảnh.",
    }


def split_by_image() -> dict[str, str]:
    manifest = read_json(ROOT / "data" / "s203_split" / "manifest_split.json")
    return {item["image_id"]: item["split"] for item in manifest["images"]}


def code_version() -> str:
    """Ghi commit để kết quả thí nghiệm tái tạo được; ngoài Git thì ghi unknown."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
        )
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def run_one(image_id: str, processed_dir: Path, split: str) -> dict[str, Any]:
    metadata, image, valid = load_image(image_id, processed_dir)
    reference = read_json(ROOT / "data" / "reference_labels" / f"{image_id}_craters_catalogue.json")
    baseline = detect_machine(metadata, image, valid)
    raw = baseline["raw_circles"]
    shaded = baseline["machine"]["circles"]
    reviewed, review_report = review_candidates(shaded, baseline["pre"])
    texture_kept, texture_removed = apply_filter(reviewed, remove_classes=("texture",))
    deduped, duplicates, dedupe_report = dedupe_circles(reviewed)
    sun_counts = baseline["postprocess"].get("shading_counts", {})
    sun_usable = sun_counts.get("not_checked", 0) != len(shaded)

    e1_status = (
        "not_evaluable_on_holdout" if split == "holdout"
        else "diagnostic_tuning_only" if sun_usable
        else "not_evaluable_no_usable_sun"
    )
    result: dict[str, Any] = {
        "image_id": image_id,
        "split": split,
        "scale_m_per_px": metadata["scale_m_per_px"],
        "sun_quality": metadata["sun"]["quality"],
        "experiment_1_s111": {
            "baseline": recall_summary(raw, reference),
            "with_s111_annotation": recall_summary(shaded, reference),
            "candidates_baseline": len(raw),
            "candidates_with_s111": len(shaded),
            "shading_counts": sun_counts,
            "status": e1_status,
            "note": (
                "S1-11 chỉ gắn nhãn sáng-tối, không loại vòng; hai Recall phải bằng nhau. "
                "Không thử loại inverted làm cấu hình chính vì S2-02 đã ghi nhận mất hố thật."
                if sun_usable else
                "Thiếu hướng nắng đủ tin cậy hoặc ảnh thuộc holdout mosaic: mọi ứng viên not_checked; không kết luận S1-11."
            ),
        },
        "experiment_2_parameters": [],
        "experiment_3_hard_cases": {
            "review_class_counts": review_report["counts"],
            "remove_texture": {
                "candidates_kept": len(texture_kept),
                "candidates_removed": len(texture_removed),
                "recall": recall_summary(texture_kept, reference),
                "scope": "tuning_diagnostic" if split == "tuning" else "holdout_descriptive",
            },
            "dedupe": {
                "candidates_kept": len(deduped),
                "candidates_removed": len(duplicates),
                "recall": recall_summary(deduped, reference),
                "report": dedupe_report,
            },
        },
    }
    for name, override in PARAMETER_VARIANTS.items():
        detected = detect_machine(metadata, image, valid, hough_params=resolve_hough_params(override))
        result["experiment_2_parameters"].append({
            "variant": name,
            "hough_params_override": override,
            "candidates": len(detected["raw_circles"]),
            "seconds_hough": round(detected["seconds_hough"], 3),
            "recall": recall_summary(detected["raw_circles"], reference),
            "scope": "tuning_selection" if split == "tuning" else "holdout_report_only",
        })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S2-07: ba kịch bản thí nghiệm")
    parser.add_argument("--images", nargs="*", default=list(DEFAULT_IMAGES))
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evidence" / "s2-07" / "results.json")
    parser.add_argument("--write", action="store_true", help="ghi JSON kết quả; mặc định chỉ in ra stdout")
    args = parser.parse_args(argv)
    splits = split_by_image()
    unknown = [image_id for image_id in args.images if image_id not in splits]
    if unknown:
        parser.error("image_id không thuộc split S2-03: " + ", ".join(unknown))
    rows = [run_one(image_id, args.processed_dir, splits[image_id]) for image_id in args.images]
    report = {
        "task_id": "S2-07",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_version": code_version(),
        "metric_scope": "reviewed sparse labels; Recall known only",
        "results": rows,
    }
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Đã ghi {args.output.relative_to(ROOT)}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
