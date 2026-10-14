"""Create one S1-06 sample using the same safe reader as the full dataset."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_s106_crops import BUNDLE_DIR, CROPS_CONFIG, make_crop, sha256_file
import json


def make_sample_crop(tif_path: str | Path, image_id: str, x0: int, y0: int,
                     size: int = 512, output_dir: str | Path = ROOT / "data" / "processed") -> dict:
    path = Path(tif_path)
    if size != 512:
        raise ValueError("Hợp đồng yêu cầu ảnh 512×512.")
    choices = [c for c in CROPS_CONFIG if c["file"] == path.name]
    if not choices:
        raise ValueError("Nguồn chưa có trong manifest S1-06; cần bổ sung provenance trước khi tạo ảnh.")
    source = next(s for s in json.loads((BUNDLE_DIR / "sources.json").read_text()) if s["filename"] == path.name)
    if path.stat().st_size != source["bytes"] or sha256_file(path) != source["sha256"]:
        raise ValueError("Nguồn không khớp manifest SHA256.")
    cfg = {**choices[0], "image_id": image_id, "x0": x0, "y0": y0}
    return make_crop(path, cfg, source, Path(output_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args()
    first = CROPS_CONFIG[0]
    make_sample_crop(ROOT / "data" / "raw" / first["file"], "moon_ap15_hia_sample", first["x0"], first["y0"], output_dir=args.output_dir)
