"""Đo sai số phần tiền xử lý tự viết và kiểm ví dụ Hough 5×5 cho báo cáo."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _machine_info() -> dict:
    """Chỉ ghi cấu hình máy đang chạy lượt kiểm này."""
    cpu = platform.processor()
    memory = None
    cpuinfo = Path("/proc/cpuinfo")
    meminfo = Path("/proc/meminfo")
    if cpuinfo.exists():
        cpu = next((line.split(":", 1)[1].strip()
                    for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), cpu)
    if meminfo.exists():
        memory = next((int(line.split()[1])
                       for line in meminfo.read_text().splitlines()
                       if line.startswith("MemTotal:")), None)
    return {"cpu": cpu, "ram_os_kib": memory, "platform": platform.platform(),
            "python": platform.python_version()}


def main() -> None:
    """Đối chiếu đủ 26 ảnh và lưu bảng sai số cùng hash đầu vào/mã."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="file JSON mới")
    args = parser.parse_args()

    import cv2
    import numpy as np
    from scripts.verify_hough_examples import tiny_example
    from src import preprocessing as pp

    if args.out.exists():
        raise SystemExit("Không ghi đè kết quả đã có.")
    paths = sorted(p for p in (ROOT / "data/processed").glob("*.npy")
                   if not p.stem.endswith("_valid_mask"))
    if len(paths) != 26:
        raise SystemExit(f"Cần đủ 26 ảnh, hiện có {len(paths)}.")
    rows = []
    for path in paths:
        image = np.load(path).astype(np.float32)
        valid = np.load(path.with_name(path.stem + "_valid_mask.npy"))
        if image.shape != (512, 512) or not valid.all():
            raise SystemExit(
                f"Phép đối chiếu yêu cầu ảnh 512×512 hoàn toàn hợp lệ: {path.name}")
        ours_small, _ = pp.block_mean(image, valid, 2)
        gx, gy, _, _ = pp.sobel(image)
        pairs = {
            "block_mean_k2": (
                ours_small, cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)),
            "gaussian_sigma1.5": (
                pp.gaussian_blur(image, 1.5),
                cv2.GaussianBlur(image, (11, 11), 1.5, borderType=cv2.BORDER_REFLECT_101)),
            "sobel_xy": (
                np.stack([gx, gy]), np.stack([
                    cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3,
                              borderType=cv2.BORDER_REFLECT_101),
                    cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3,
                              borderType=cv2.BORDER_REFLECT_101)])),
        }
        for name, (ours, reference) in pairs.items():
            error = ours.astype(np.float64) - reference.astype(np.float64)
            rows.append({"image": path.stem, "method": name, "elements": int(error.size),
                         "max_abs": float(np.abs(error).max()),
                         "mse": float(np.mean(error ** 2))})
    summary = {}
    for name in sorted({r["method"] for r in rows}):
        group = [r for r in rows if r["method"] == name]
        total = sum(r["elements"] for r in group)
        summary[name] = {
            "images": len(group), "max_abs": max(r["max_abs"] for r in group),
            "mse": sum(r["mse"] * r["elements"] for r in group) / total,
        }
        assert summary[name]["max_abs"] < 1e-5
    environment = _machine_info()
    environment.update(numpy=np.__version__, opencv=cv2.__version__)
    source_paths = (Path(__file__).resolve(), ROOT / "src/preprocessing.py",
                    ROOT / "src/hough.py", ROOT / "scripts/verify_hough_examples.py")
    result = {
        "purpose": "Report numerical verification; not a detection benchmark or S3-05 experiment",
        "seed": 0, "environment": environment,
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_paths},
        "summary": summary, "rows": rows, "tiny_hough": tiny_example(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("PASS: 78 comparisons on 26 images; tiny Hough matches manual matrices")


if __name__ == "__main__":
    main()
