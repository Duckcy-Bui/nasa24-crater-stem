"""Download the 16 locked official TIFF sources for full S1-06 reproduction."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(source: dict, raw_dir: Path) -> Path:
    name = source["filename"]
    if Path(name).name != name or urlparse(source["url"]).hostname != "pds.lroc.im-ldi.com":
        raise ValueError("Nguồn tải không đúng manifest LROC chính thức.")
    path = raw_dir / name
    if path.exists():
        if path.stat().st_size == source["bytes"] and digest_file(path) == source["sha256"]:
            print(f"Đã đúng SHA256: {name}", flush=True)
            return path
        raise ValueError(f"File nguồn cũ sai SHA256: {path}; di chuyển rồi chạy lại.")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=raw_dir, suffix=".part", delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            with urllib.request.urlopen(source["url"], timeout=120) as response:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > source["bytes"]:
                        raise ValueError(f"Nguồn lớn hơn manifest: {name}")
                    temp.write(chunk)
            temp.flush()
            if total != source["bytes"] or digest_file(temp_path) != source["sha256"]:
                raise ValueError(f"Nguồn sai kích thước/SHA256: {name}")
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
    print(f"Đã tải và xác minh: {name}", flush=True)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    args = parser.parse_args()
    sources = json.loads((ROOT / "data" / "s106_bundle" / "sources.json").read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda item: download(item, args.raw_dir), sources))
    print(f"Đủ {len(sources)} nguồn; chạy scripts/generate_s106_crops.py để tái tạo.")
