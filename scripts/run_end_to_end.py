"""S1-13: chạy một ảnh (hoặc cả bộ) từ đầu đến cuối.

Ví dụ:
    python scripts/run_end_to_end.py moon_ap16_m106777343r_c01
    python scripts/run_end_to_end.py moon_ap16_m106777343r_c01 --voting gradient
    python scripts/run_end_to_end.py --all --no-render

Mỗi ảnh tạo outputs/e2e_<image_id>_<UTC>_<id>/ gồm metadata.json, params.json,
craters.json (máy), run.json, summary.json, arrays.npz và overlay.png.
Tự lấy lần lưu mới nhất của người chơi trong outputs/player_answers/ và nhãn thủ
công trong data/reference_labels/ nếu có, chỉ để vẽ cạnh. Không chấm điểm.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import ContractError, read_json  # noqa: E402
from src.pipeline import find_player_answer, run_end_to_end  # noqa: E402


def code_version() -> str:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if head.returncode != 0:
        return "unknown"
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return head.stdout.strip() + ("+working-tree" if dirty.stdout.strip() else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="S1-13: ảnh → tiền xử lý → Hough → lưu run và overlay")
    parser.add_argument("image_id", nargs="?")
    parser.add_argument("--all", action="store_true", help="Chạy mọi ảnh trong data/s106_bundle/manifest.json")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs")
    parser.add_argument("--player", type=Path, help="craters.json của người chơi; mặc định lấy lần lưu mới nhất")
    parser.add_argument("--no-player", action="store_true", help="Không vẽ vòng người chơi")
    parser.add_argument("--voting", choices=("full_circle", "gradient"), default="full_circle")
    parser.add_argument("--max-circles", type=int, default=100)
    parser.add_argument("--no-render", action="store_true", help="Không vẽ overlay.png")
    args = parser.parse_args()
    if bool(args.image_id) == args.all:
        parser.error("Cần đúng một trong: image_id hoặc --all.")

    ids = read_json(ROOT / "data" / "s106_bundle" / "manifest.json")["image_ids"] if args.all else [args.image_id]
    version = code_version()
    failed = 0
    for image_id in ids:
        player = None if args.no_player else (args.player or find_player_answer(image_id, ROOT / "outputs" / "player_answers"))
        reference = ROOT / "data" / "reference_labels" / f"{image_id}_craters_catalogue.json"
        try:
            directory, summary = run_end_to_end(
                image_id, processed_dir=args.processed_dir, output_root=args.output_root, code_version=version,
                player_path=player, reference_path=reference if reference.exists() else None,
                hough_params={"voting_method": args.voting, "max_circles": args.max_circles},
                render=not args.no_render)
        except (OSError, ValueError, ContractError) as error:
            failed += 1
            print(f"[LỖI] {image_id}: {error}")
            continue
        steps = summary["steps"]
        print(f"{image_id}: {steps['hough']['circles']} ứng viên máy "
              f"(r {steps['hough']['r_min_px']}–{steps['hough']['r_max_px']} px, {steps['hough']['voting_method']}, "
              f"{steps['hough']['seconds']} s); người chơi {steps['player']['circles']}; "
              f"nhãn thủ công {steps['reference']['circles']}; chấm điểm: bỏ qua → {directory}")
    if args.all:
        print(json.dumps({"images": len(ids), "failed": failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
