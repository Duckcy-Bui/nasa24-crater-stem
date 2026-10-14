"""Build the deterministic, versioned S1-06 offline ZIP after crop generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_s106_crops import BUNDLE_DIR, CROPS_CONFIG, sha256_file
from scripts.install_s106_dataset import verified_bundle


def build_bundle(processed_dir: Path, bundle_dir: Path = BUNDLE_DIR) -> dict:
    image_ids = [c["image_id"] for c in CROPS_CONFIG]
    if len(image_ids) != 26 or len(set(image_ids)) != 26:
        raise ValueError("Cấu hình phải có đúng 26 image_id duy nhất.")
    payloads = {}
    for image_id in image_ids:
        if (processed_dir / f"{image_id}_craters_catalogue.json").exists():
            raise ValueError("Không đóng gói catalogue cũ chưa xác minh.")
        for suffix in (".npy", ".png", ".json", "_valid_mask.npy"):
            name = image_id + suffix
            payloads[name] = (processed_dir / name).read_bytes()
    filename = "s106_lroc_browse_v2.zip"
    archive = bundle_dir / filename
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(payloads):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, payloads[name])
    manifest = {
        "schema_version": "s106-bundle-1", "dataset_id": "s106_lroc_browse_v2",
        "total_images": len(image_ids), "image_ids": image_ids,
        "archive": {"filename": filename, "bytes": archive.stat().st_size, "sha256": sha256_file(archive)},
        "generator_sha256": sha256_file(ROOT / "scripts" / "generate_s106_crops.py"),
        "sources_sha256": sha256_file(bundle_dir / "sources.json"),
        "crops_sha256": sha256_file(bundle_dir / "crops.json"),
        "reference_status": "unavailable", "source_product_level": "browse",
        "files": {name: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()} for name, payload in sorted(payloads.items())},
    }
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verified_bundle(bundle_dir)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args()
    manifest = build_bundle(args.processed_dir)
    print(f"Bundle {manifest['archive']['bytes'] / 1024**2:.2f} MiB; SHA256 {manifest['archive']['sha256']}")
