"""Verify and unpack the committed S1-06 dataset without network access."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.contracts import validate_metadata

BUNDLE_DIR = ROOT / "data" / "s106_bundle"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verified_bundle(bundle_dir: Path = BUNDLE_DIR) -> tuple[dict, dict[str, bytes]]:
    """Verify the archive, every member and the numerical/data contracts."""
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "s106-bundle-1" or manifest.get("total_images") != 26:
        raise ValueError("Phiên bản hoặc số ảnh bundle không hợp lệ.")
    archive = manifest["archive"]
    name = archive["filename"]
    if Path(name).name != name:
        raise ValueError("Đường dẫn archive không hợp lệ.")
    raw_zip = (bundle_dir / name).read_bytes()
    if len(raw_zip) != archive["bytes"] or _digest(raw_zip) != archive["sha256"]:
        raise ValueError("Bundle sai kích thước hoặc SHA256; tải lại từ Git.")
    for filename, key in (("sources.json", "sources_sha256"), ("crops.json", "crops_sha256")):
        if _digest((bundle_dir / filename).read_bytes()) != manifest[key]:
            raise ValueError(f"Manifest nguồn/tham số bị thay đổi: {filename}.")
    expected = manifest["files"]
    payloads = {}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Thành phần ZIP không khớp manifest.")
        for entry in zf.infolist():
            if Path(entry.filename).name != entry.filename or entry.file_size != expected[entry.filename]["bytes"]:
                raise ValueError("Đường dẫn/kích thước thành phần ZIP không hợp lệ.")
            payload = zf.read(entry)
            if _digest(payload) != expected[entry.filename]["sha256"]:
                raise ValueError(f"Sai SHA256: {entry.filename}")
            payloads[entry.filename] = payload
    ids = manifest["image_ids"]
    if len(ids) != 26 or len(set(ids)) != 26:
        raise ValueError("image_id bundle bị thiếu hoặc lặp.")
    names_per_image = set()
    sources = {s["filename"]: s for s in json.loads((bundle_dir / "sources.json").read_text())}
    for image_id in ids:
        metadata = json.loads(payloads[f"{image_id}.json"])
        validate_metadata(metadata)
        if metadata["image_id"] != image_id or metadata["data_kind"] != "real" or metadata.get("reference_status") != "unavailable":
            raise ValueError("Metadata hoặc trạng thái tham chiếu không hợp lệ.")
        image = np.load(io.BytesIO(payloads[f"{image_id}.npy"]), allow_pickle=False)
        mask = np.load(io.BytesIO(payloads[f"{image_id}_valid_mask.npy"]), allow_pickle=False)
        if image.shape != (512, 512) or image.dtype != np.float32 or not np.isfinite(image).all() or image.min() < 0 or image.max() > 1:
            raise ValueError(f"Ảnh sai hợp đồng: {image_id}")
        if mask.shape != image.shape or mask.dtype != np.bool_ or not mask.any():
            raise ValueError(f"Mặt nạ sai hợp đồng: {image_id}")
        if metadata["valid_ratio"] != float(mask.mean()) or np.any(image[~mask] != 0):
            raise ValueError(f"Mặt nạ/valid_ratio không khớp: {image_id}")
        png = np.asarray(Image.open(io.BytesIO(payloads[f"{image_id}.png"])))
        if not np.array_equal(png, np.rint(image * 255).astype(np.uint8)):
            raise ValueError(f"PNG không khớp ảnh chuẩn: {image_id}")
        source = metadata["source"]
        locked = sources.get(source["filename"])
        if locked is None or any(source[k] != locked[k] for k in ("sha256", "url", "bytes", "product_page_url")):
            raise ValueError(f"Nguồn không khớp manifest: {image_id}")
        prep = metadata["preprocess"]
        if prep.get("generator_sha256") != manifest["generator_sha256"] or prep.get("crops_config_sha256") != manifest["crops_sha256"]:
            raise ValueError(f"Phiên bản sinh ảnh không khớp: {image_id}")
        if metadata["valid_mask_file"] != f"{image_id}_valid_mask.npy":
            raise ValueError("Đường dẫn mặt nạ không hợp lệ.")
        names_per_image.update((f"{image_id}.npy", f"{image_id}.png", f"{image_id}.json", f"{image_id}_valid_mask.npy"))
    if names_per_image != set(payloads):
        raise ValueError("Bundle chứa thành phần ngoài dữ liệu đã khai báo.")
    return manifest, payloads


def install_dataset(output_dir: Path = ROOT / "data" / "processed", *, bundle_dir: Path = BUNDLE_DIR,
                    overwrite: bool = False) -> int:
    manifest, payloads = verified_bundle(bundle_dir)
    # Old fake catalogue files must not survive as accidental ground truth.
    for image_id in manifest["image_ids"]:
        catalogue = output_dir / f"{image_id}_craters_catalogue.json"
        if catalogue.exists():
            raise ValueError(f"Catalogue cũ chưa xác minh: {catalogue}. Di chuyển ra khỏi bộ dữ liệu trước khi cài.")
    for name, payload in payloads.items():
        path = output_dir / name
        if path.exists() and not overwrite and path.read_bytes() != payload:
            raise FileExistsError(f"Đầu ra khác bundle: {path}. Dùng thư mục mới hoặc --overwrite.")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir) as staging:
        tmp = Path(staging)
        for name, payload in payloads.items():
            (tmp / name).write_bytes(payload)
        for name in payloads:
            (tmp / name).replace(output_dir / name)
    return len(manifest["image_ids"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(f"Đã xác minh và cài {install_dataset(args.output_dir, overwrite=args.overwrite)} ảnh; nhãn hố chưa khả dụng.")
