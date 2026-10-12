"""Kiểm tra các mẫu dữ liệu S1-05 mà không cần thư viện ngoài."""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from src.contracts import read_json, save_run, validate_crater_set, validate_metadata


def main() -> None:
    examples = ROOT / "data" / "examples"
    metadata = read_json(examples / "s105_synthetic_512.json")
    validate_metadata(metadata)
    for name in ("craters_machine.json", "craters_catalogue.json", "craters_player.json"):
        validate_crater_set(read_json(examples / name), metadata)
        print("Hợp lệ:", name)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    version = commit.stdout.strip() if commit.returncode == 0 else "working-tree-before-first-commit"
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if dirty.returncode == 0 and dirty.stdout.strip():
        version += "+working-tree"
    run_id = "s105_check_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = save_run(ROOT / "outputs", run_id, metadata=metadata,
                         crater_set=read_json(examples / "craters_machine.json"),
                         params=read_json(ROOT / "configs" / "default.json"), code_version=version)
    print("Đã lưu bản chạy mẫu:", directory.relative_to(ROOT))
    print("Chỉ kiểm tra hợp đồng dữ liệu giả lập; chưa chạy Hough hoặc tiền xử lý.")


if __name__ == "__main__":
    main()
