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
)
DEFAULT_HOLDOUT_IMAGES = ("moon_ap15_loc_c01", "moon_marefrig_loc_c01")

PARAMETER_VARIANTS = {
    "baseline": {},
    "min_vote_ratio_030": {"min_vote_ratio": 0.30},
    "min_vote_ratio_040": {"min_vote_ratio": 0.40},
    "radius_step_2": {"radius_step_px": 2},
}


def known_references(reference: dict[str, Any]) -> list[dict[str, Any]]:
    """Nhãn uncertain không thuộc mẫu Recall chính thức."""
    return [c for c in reference["circles"] if "uncertain" not in c["crater_id"].lower()]


def recall_summary(circles: list[dict[str, Any]], reference: dict[str, Any], *,
                   radius_bounds: tuple[int, int] | None = None,
                   max_circles: int | None = None) -> dict[str, Any]:
    refs = known_references(reference)
    pairs = match_one_to_one(circles, refs, CENTER_TOLERANCE)
    found = {p["reference_id"] for p in pairs}
    r_min, r_max = radius_bounds if radius_bounds is not None else (None, None)
    in_range = [c for c in refs if r_min is None or r_min <= c["r"] <= r_max]
    radii = [c["r"] for c in circles]
    return {
        "known_labels": len(refs),
        "true_positive_known": len(pairs),
        "missed_reference_ids": [c["crater_id"] for c in refs if c["crater_id"] not in found],
        "recall_known": round(len(pairs) / len(refs), 4) if refs else None,
        "precision": None,
        "f1": None,
        "reference_radius_in_search": len(in_range),
        "reference_radius_outside_search": len(refs) - len(in_range),
        "search_radius_px": [r_min, r_max],
        "hit_max_circles": len(circles) >= max_circles if max_circles is not None else None,
        "machine_radius_px": [min(radii), max(radii)] if radii else [None, None],
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


def shading_match_distribution(circles: list[dict[str, Any]], reference: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Phân bố nhãn S1-11 của vòng khớp nhãn thưa và vòng không khớp."""
    pairs = match_one_to_one(circles, known_references(reference), CENTER_TOLERANCE)
    matched = {p["prediction_id"] for p in pairs}
    result = {"matched_known_label": {}, "unmatched": {}}
    for circle in circles:
        group = "matched_known_label" if circle["crater_id"] in matched else "unmatched"
        status = (circle.get("shading") or {}).get("status", "missing")
        result[group][status] = result[group].get(status, 0) + 1
    return result


def validate_run_selection(image_ids: list[str], splits: dict[str, str], *, holdout: bool,
                           chosen_config: Path | None) -> None:
    held_out = [image_id for image_id in image_ids if splits[image_id] == "holdout"]
    if held_out and not holdout:
        raise ValueError("Holdout chỉ chạy với --holdout và đúng một cấu hình đã chốt trên tuning.")
    if holdout and not held_out:
        raise ValueError("--holdout yêu cầu ít nhất một image_id thuộc holdout.")
    if holdout and chosen_config is None:
        raise ValueError("--holdout yêu cầu --chosen-config <JSON> để không quét nhiều biến thể E2.")


def e1_status(split: str, sun_usable: bool) -> str:
    if split == "holdout":
        return "not_evaluable_on_holdout"
    return "diagnostic_tuning_only" if sun_usable else "not_evaluable_no_usable_sun"


def run_one(image_id: str, processed_dir: Path, split: str, *,
            parameter_variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
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
    bounds = (baseline["r_min"], baseline["r_max"])
    max_circles = baseline["hough"]["max_circles"]
    inverted_kept, inverted_removed = apply_filter(shaded, remove_shading=("inverted",))

    e1_evaluation_status = e1_status(split, sun_usable)
    result: dict[str, Any] = {
        "image_id": image_id,
        "split": split,
        "scale_m_per_px": metadata["scale_m_per_px"],
        "sun_quality": metadata["sun"]["quality"],
        "experiment_1_s111": {
            "baseline": recall_summary(raw, reference, radius_bounds=bounds, max_circles=max_circles),
            "with_s111_annotation": recall_summary(shaded, reference, radius_bounds=bounds, max_circles=max_circles),
            "remove_inverted_experiment": {
                "candidates_kept": len(inverted_kept),
                "candidates_removed": len(inverted_removed),
                "recall": recall_summary(inverted_kept, reference, radius_bounds=bounds, max_circles=max_circles),
                "note": "Nhánh thí nghiệm S1-11, không phải cấu hình mặc định.",
            },
            "shading_by_label_match": shading_match_distribution(shaded, reference),
            "candidates_baseline": len(raw),
            "candidates_with_s111": len(shaded),
            "shading_counts": sun_counts,
            "status": e1_evaluation_status,
            "note": (
                "S1-11 chỉ gắn nhãn sáng-tối; nhánh remove_inverted đo trực tiếp rủi ro mất hố. "
                "Không dùng nhánh này làm cấu hình chính nếu làm giảm Recall_known."
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
                "recall": recall_summary(texture_kept, reference, radius_bounds=bounds, max_circles=max_circles),
                "scope": "tuning_diagnostic" if split == "tuning" else "holdout_descriptive",
            },
            "dedupe": {
                "candidates_kept": len(deduped),
                "candidates_removed": len(duplicates),
                "recall": recall_summary(deduped, reference, radius_bounds=bounds, max_circles=max_circles),
                "report": dedupe_report,
            },
        },
    }
    for name, override in parameter_variants.items():
        detected = detect_machine(metadata, image, valid, hough_params=resolve_hough_params(override))
        result["experiment_2_parameters"].append({
            "variant": name,
            "hough_params_override": override,
            "candidates": len(detected["raw_circles"]),
            "seconds_hough": round(detected["seconds_hough"], 3),
            "recall": recall_summary(detected["raw_circles"], reference,
                                      radius_bounds=(detected["r_min"], detected["r_max"]),
                                      max_circles=detected["hough"]["max_circles"]),
            "scope": "tuning_selection" if split == "tuning" else "holdout_report_only",
        })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S2-07: ba kịch bản thí nghiệm")
    parser.add_argument("--images", nargs="*", help="mặc định là ba ảnh tuning")
    parser.add_argument("--holdout", action="store_true", help="chỉ báo cáo holdout bằng một cấu hình đã chốt")
    parser.add_argument("--chosen-config", type=Path, help="JSON Hough đã chốt trên tuning; bắt buộc cùng --holdout")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evidence" / "s2-07" / "results.json")
    parser.add_argument("--write", action="store_true", help="ghi JSON kết quả; mặc định chỉ in ra stdout")
    args = parser.parse_args(argv)
    splits = split_by_image()
    image_ids = args.images if args.images is not None else (list(DEFAULT_HOLDOUT_IMAGES) if args.holdout else list(DEFAULT_IMAGES))
    unknown = [image_id for image_id in image_ids if image_id not in splits]
    if unknown:
        parser.error("image_id không thuộc split S2-03: " + ", ".join(unknown))
    try:
        validate_run_selection(image_ids, splits, holdout=args.holdout, chosen_config=args.chosen_config)
    except ValueError as error:
        parser.error(str(error))
    variants = PARAMETER_VARIANTS
    chosen = None
    if args.holdout:
        try:
            supplied = read_json(args.chosen_config)
            chosen = resolve_hough_params(supplied.get("hough", supplied))
        except (OSError, TypeError, ValueError) as error:
            parser.error(f"Không đọc được --chosen-config: {error}")
        variants = {"chosen_on_tuning": chosen}
    rows = [run_one(image_id, args.processed_dir, splits[image_id], parameter_variants=variants) for image_id in image_ids]
    report = {
        "task_id": "S2-07",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_version": code_version(),
        "metric_scope": "reviewed sparse labels; Recall known only",
        "holdout_mode": args.holdout,
        "chosen_config_path": str(args.chosen_config) if args.chosen_config else None,
        "chosen_hough_params": chosen,
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
