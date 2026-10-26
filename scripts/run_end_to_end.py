"""S1-13: chạy một ảnh (hoặc cả bộ) từ đầu đến cuối.

Ví dụ:
    python scripts/run_end_to_end.py moon_ap16_m106777343r_c01
    python scripts/run_end_to_end.py moon_ap16_m106777343r_c01 --voting gradient
    python scripts/run_end_to_end.py --all --no-render --csv outputs/e2e_26_anh.csv

Mỗi ảnh tạo outputs/e2e_<image_id>_<UTC>_<id>/ gồm metadata.json, params.json,
craters.json (máy), run.json, summary.json, arrays.npz và overlay.png.
Tự lấy lần lưu mới nhất của người chơi trong outputs/player_answers/ và nhãn thủ
công trong data/reference_labels/ nếu có. Khi có người chơi, ghi thêm score.json
(S2-04): so với máy chỉ là mức trùng; so với danh mục chỉ khi nhãn đã kiểm chéo.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json  # noqa: E402
from src.pipeline import find_player_answer, run_end_to_end  # noqa: E402
from src.hough import resolve_hough_params  # noqa: E402


def code_version() -> str:
    """Commit của chính repo này; ngoài git (hoặc máy không có git) ghi "unknown"."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, capture_output=True, text=True)
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != ROOT.resolve():
            return "unknown"
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return "unknown"
    if head.returncode != 0:
        return "unknown"
    return head.stdout.strip() + ("+working-tree" if dirty.stdout.strip() else "")


CSV_COLUMNS = ("image_id", "scale_m_per_px", "reference_status", "edge_px", "r_min_px", "r_max_px",
               "ung_vien_may", "cham_tran", "giay_tien_xu_ly", "giay_hough", "nhan_tham_chieu",
               "loc_s1_11", "cham_diem", "run_dir")


def csv_row(directory: Path, metadata: dict, summary: dict) -> list:
    steps = summary["steps"]
    return [summary["image_id"], metadata["scale_m_per_px"], metadata.get("reference_status", "unavailable"),
            steps["preprocess"]["edge_px"], steps["hough"]["r_min_px"], steps["hough"]["r_max_px"],
            steps["hough"]["circles"], steps["hough"]["hit_max_circles"], steps["preprocess"]["seconds"],
            steps["hough"]["seconds"], steps["reference"]["circles"], steps["postprocess"]["status"],
            steps["scoring"]["status"], directory.name]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S1-13: ảnh → tiền xử lý → Hough → lưu run và overlay")
    parser.add_argument("image_id", nargs="?")
    parser.add_argument("--all", action="store_true", help="Chạy mọi ảnh trong data/s106_bundle/manifest.json")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs")
    parser.add_argument("--player", type=Path, help="craters.json của người chơi cho đúng image_id; mặc định lấy lần lưu mới nhất")
    parser.add_argument("--no-player", action="store_true", help="Không vẽ vòng người chơi")
    parser.add_argument("--player-root", type=Path, default=ROOT / "outputs" / "player_answers", help=argparse.SUPPRESS)
    parser.add_argument("--reference-dir", type=Path, default=ROOT / "data" / "reference_labels", help=argparse.SUPPRESS)
    parser.add_argument("--hough-config", type=Path, help="JSON Hough (hoac config co khoa hough)")
    parser.add_argument("--voting", choices=("full_circle", "gradient"), default=None)
    parser.add_argument("--max-circles", type=int, default=None)
    parser.add_argument("--no-render", action="store_true", help="Không vẽ overlay.png")
    parser.add_argument("--csv", type=Path, help="Ghi bảng tóm tắt mọi ảnh vừa chạy ra file CSV")
    args = parser.parse_args(argv)
    if bool(args.image_id) == args.all:
        parser.error("Cần đúng một trong: image_id hoặc --all.")
    if args.player and args.all:
        parser.error("--player là câu trả lời của một ảnh; không dùng cùng --all (khi đó mỗi ảnh tự lấy lần lưu mới nhất).")
    if args.player and args.no_player:
        parser.error("--player và --no-player mâu thuẫn nhau.")

    try:
        supplied = read_json(args.hough_config) if args.hough_config else {}
        hough_params = resolve_hough_params(supplied)
        if args.voting is not None:
            hough_params["voting_method"] = args.voting
        if args.max_circles is not None:
            hough_params["max_circles"] = args.max_circles
        hough_params = resolve_hough_params(hough_params)
    except (OSError, TypeError, ValueError) as error:
        parser.error(str(error))

    ids = read_json(ROOT / "data" / "s106_bundle" / "manifest.json")["image_ids"] if args.all else [args.image_id]
    scoring_params = read_json(ROOT / "configs" / "default.json")["evaluation"]
    version = code_version()
    failed, rows = 0, []
    for image_id in ids:
        player = None if args.no_player else (args.player or find_player_answer(image_id, args.player_root))
        reference = args.reference_dir / f"{image_id}_craters_catalogue.json"
        try:
            directory, summary = run_end_to_end(
                image_id, processed_dir=args.processed_dir, output_root=args.output_root, code_version=version,
                player_path=player, reference_path=reference if reference.exists() else None,
                hough_params=hough_params,
                scoring_params=scoring_params, render=not args.no_render)
        except Exception as error:  # one bad image must not stop --all; KeyboardInterrupt still stops
            failed += 1
            print(f"[LỖI] {image_id}: {type(error).__name__}: {error}")
            continue
        rows.append(csv_row(directory, read_json(directory / "metadata.json"), summary))
        steps = summary["steps"]
        scoring = steps["scoring"]
        scored = {"skipped": "bỏ qua", "machine_agreement_only": f"chỉ so máy ({scoring.get('matched_machine')} vòng trùng)",
                  "scored": f"{scoring.get('score')} điểm"}[scoring["status"]]
        print(f"{image_id}: {steps['hough']['circles']} ứng viên máy "
              f"(r {steps['hough']['r_min_px']}–{steps['hough']['r_max_px']} px, {steps['hough']['voting_method']}, "
              f"{steps['hough']['seconds']} s); người chơi {steps['player']['circles']}; "
              f"nhãn tham chiếu {steps['reference']['circles']}; chấm điểm: {scored} → {directory}")
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(CSV_COLUMNS)
            writer.writerows(rows)
    if args.all:
        print(json.dumps({"images": len(ids), "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
