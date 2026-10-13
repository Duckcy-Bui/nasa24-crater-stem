"""S1-08: chạy chuỗi tiền xử lý B0–B8, lưu ảnh từng bước và tham số đã dùng.

Ví dụ:
    python scripts/run_preprocessing.py --synthetic oblique
    python scripts/run_preprocessing.py --synthetic overhead
    python scripts/run_preprocessing.py --input data/raw/anh.tif --metadata data/processed/<id>.json

Kết quả ở outputs/<run_id>/ (không ghi đè lần chạy cũ):
    steps/B*.png      ảnh từng bước, tên file ghi mã bước
    overview.png      ghép các bước, nhãn TỰ VIẾT / THƯ VIỆN
    result.npz        mảng đầu ra để đưa sang Hough (S1-07)
    params.json       toàn bộ tham số thực sự đã dùng (kèm ngưỡng Canny đã tính)
    metadata.json     metadata ảnh, trường preprocess đã điền
    run.json          run_id, mã commit, thời gian
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import radius_range_px, read_json, validate_crater_set, validate_metadata  # noqa: E402
from src.preprocessing import STEPS, preprocess, read_window  # noqa: E402

# Hai cảnh thử theo S1-04 mục 9: một nắng xiên, một nắng gần đứng.
SYNTHETIC = {
    "oblique": {"azimuth_deg": 270.0, "incidence_deg": 80.0, "nodata_corner": True, "seed": 7},
    "overhead": {"azimuth_deg": 90.0, "incidence_deg": 15.0, "nodata_corner": False, "seed": 11},
}


def code_version() -> str:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    version = commit.stdout.strip() if commit.returncode == 0 else "no-git"
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if dirty.returncode == 0 and dirty.stdout.strip():
        version += "+working-tree"
    return version


def synthetic_input(name: str):
    from synthetic_scene import make_scene

    cfg = SYNTHETIC[name]
    k, src_scale = 2, 1.0
    image, craters = make_scene(cfg["azimuth_deg"], cfg["incidence_deg"], size=512 * k,
                                nodata_corner=cfg["nodata_corner"], seed=cfg["seed"])
    d_min, d_max = 40.0, 500.0
    r_min, r_max = radius_range_px(d_min, d_max, src_scale * k)
    metadata = {
        "schema_version": "1.0", "data_kind": "synthetic", "image_id": f"s108_synth_{name}",
        "source_stt": None, "product_id": None, "body": "moon",
        "crop_x0": 0, "crop_y0": 0, "downsample_k": k, "width": 512, "height": 512,
        "scale_m_per_px": src_scale * k, "center_lat": None, "center_lon": None,
        "north_up": True, "north_angle_deg": 0.0,
        "sun": {"azimuth_deg": cfg["azimuth_deg"], "incidence_deg": cfg["incidence_deg"], "quality": "measured",
                "source": "Cảnh giả lập scripts/synthetic_scene.py; hướng nắng do bộ tạo đặt."},
        "radius": {"d_min_m": d_min, "d_max_m": d_max, "r_min_px": r_min, "r_max_px": r_max},
        "valid_ratio": None, "preprocess": None,
        "note": "Ảnh giả lập để thử tiền xử lý; không phải dữ liệu NASA.",
    }
    # Hố đúng (đáp án của bộ tạo), đổi về ảnh 512: x = (x_src − (k−1)/2)/k.
    circles = []
    for x, y, r in craters:
        x512, y512, r512 = (x - (k - 1) / 2) / k, (y - (k - 1) / 2) / k, r / k
        if 0 <= x512 <= 511 and 0 <= y512 <= 511:
            circles.append({"crater_id": f"C{len(circles) + 1}", "x": round(x512, 2), "y": round(y512, 2),
                            "r": round(r512, 2), "confidence": None, "votes": None})
    truth = {"schema_version": "1.0", "data_kind": "synthetic", "image_id": metadata["image_id"],
             "source": "catalogue", "reference_source": "Đáp án bộ tạo cảnh giả lập S1-08", "circles": circles}
    return image, None, metadata, truth


def file_input(path: Path, metadata_path: Path):
    metadata = read_json(metadata_path)
    k = metadata["downsample_k"]
    suffix = path.suffix.lower()
    if suffix == ".npy":
        image, valid = np.load(path), None
    elif suffix in (".png", ".jpg", ".jpeg"):
        import cv2  # B0 [THƯ VIỆN]: chỉ đọc file, không xử lý

        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise SystemExit(f"Không đọc được {path}")
        if image.ndim == 3:
            image = image[..., 2::-1] if image.shape[2] >= 3 else image  # BGR → RGB
        valid = None
    else:  # GeoTIFF, PDS .IMG, JP2: cắt cửa sổ 512·k bằng rasterio
        image, valid = read_window(str(path), metadata["crop_x0"], metadata["crop_y0"], k)
    return image, valid, metadata, None


# ------------------------------------------------------------ lưu ảnh từng bước
def to_u8(a: np.ndarray) -> np.ndarray:
    return np.round(np.clip(a, 0, 1) * 255).astype(np.uint8)


def stretch(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(a[valid], [0.5, 99.5]) if valid.any() else (0, 1)
    return np.clip((a - lo) / max(hi - lo, 1e-12), 0, 1)


def signed(a: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """gx, gy: xanh âm, đỏ dương, trắng 0."""
    import matplotlib

    v = np.percentile(np.abs(a[valid]), 99) or 1
    return matplotlib.colormaps["RdBu_r"](np.clip(a / v * 0.5 + 0.5, 0, 1))[..., :3]


def theta_rgb(theta: np.ndarray, mag: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Hướng gradient: màu = góc θ, độ sáng = |G|."""
    import matplotlib

    rgb = matplotlib.colormaps["hsv"]((theta + np.pi) / (2 * np.pi))[..., :3]
    return rgb * stretch(mag, valid)[..., None]


def overlay(gray: np.ndarray, edges: np.ndarray, valid: np.ndarray) -> np.ndarray:
    rgb = np.repeat(gray[..., None], 3, axis=2) * 0.85
    rgb[~valid] = (0.25, 0.25, 0.45)
    rgb[edges] = (1.0, 0.2, 0.1)
    return rgb


def step_images(out: dict) -> list[tuple[str, str, np.ndarray]]:
    v = out["valid_mask"]
    impl = {s: i for s, _, i in STEPS}
    return [
        ("B1-B2_downsampled", f"B1–B2 Thu nhỏ + xám (thang gốc)\n{impl['B1']}", stretch(out["downsampled"], v)),
        ("B3_gray", f"B3 Chuẩn hóa phân vị\n{impl['B3']}", out["gray"]),
        ("B4_enhanced", f"B4 CLAHE\n{impl['B4']}", out["enhanced"]),
        ("B5_smooth", f"B5 Gaussian σ={out['params']['gauss_sigma']}\n{impl['B5']}", out["smooth"]),
        ("B6_gx", f"B6 Sobel gx (đỏ +, xanh −)\n{impl['B6']}", signed(out["gx"], v)),
        ("B6_gy", f"B6 Sobel gy (đỏ +, xanh −)\n{impl['B6']}", signed(out["gy"], v)),
        ("B6_mag", f"B6 |G|\n{impl['B6']}", stretch(out["mag"], v)),
        ("B6_theta", f"B6 θ (màu) × |G| (độ sáng)\n{impl['B6']}", theta_rgb(out["theta"], out["mag"], v)),
        ("B7_canny", f"B7 Canny ({out['params']['edge_px_canny']} px)\n{impl['B7']}", out["edges_canny"].astype(float)),
        ("B8_edges", f"B8 Biên sau mặt nạ ({out['params']['edge_px_final']} px)\n{impl['B8']}", out["edges"].astype(float)),
        ("valid_mask", "Mặt nạ hợp lệ (trắng = hợp lệ)", v.astype(float)),
        ("B8_overlay", "Biên B8 chồng lên B3 (tím = nodata)", overlay(out["gray"], out["edges"], v)),
    ]


def save_images(out: dict, directory: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = directory / "steps"
    steps.mkdir()
    images = step_images(out)
    for name, _, img in images:
        if img.ndim == 2:
            plt.imsave(steps / f"{name}.png", to_u8(img), cmap="gray", vmin=0, vmax=255)
        else:
            plt.imsave(steps / f"{name}.png", to_u8(img))

    fig, axes = plt.subplots(3, 4, figsize=(16, 14.5))
    for ax, (_, label, img) in zip(axes.ravel(), images):
        ax.imshow(img, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        color = "#b03000" if "THƯ VIỆN" in label else "#00508c"
        ax.set_title(label, fontsize=10, color=color)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(title + "\nXanh dương = tự viết NumPy · Đỏ = thư viện", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95), h_pad=2.5)
    fig.savefig(directory / "overview.png", dpi=110)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--synthetic", choices=sorted(SYNTHETIC))
    source.add_argument("--input", type=Path, help=".npy/.png/.jpg hoặc ảnh địa lý (.tif/.img/.jp2)")
    parser.add_argument("--metadata", type=Path, help="JSON metadata theo DINH_DANG_DU_LIEU.md (bắt buộc với --input)")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.json")
    parser.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE", help="ghi đè tham số, vd gauss_sigma=2")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    if args.input and not args.metadata:
        parser.error("--input cần --metadata")
    image, valid, metadata, truth = synthetic_input(args.synthetic) if args.synthetic else file_input(args.input, args.metadata)

    params = dict(read_json(args.config)["preprocess"])
    for item in args.set:
        key, _, value = item.partition("=")
        params[key] = json.loads(value)
    version = code_version()
    params["version"] = version

    out = preprocess(image, metadata, params, valid_mask=valid)
    used = out["params"]
    metadata["valid_ratio"] = round(used["valid_ratio"], 6)
    metadata["preprocess"] = {k: v for k, v in used.items() if k != "steps"}
    validate_metadata(metadata)
    if truth:
        validate_crater_set(truth, metadata)

    run_id = args.run_id or f"s108_{metadata['image_id']}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    directory = ROOT / "outputs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    save_images(out, directory, f"{metadata['image_id']} — nắng: phương vị {metadata['sun']['azimuth_deg']}°, "
                                f"góc tới {metadata['sun']['incidence_deg']}°")
    np.savez_compressed(directory / "result.npz", **{k: v for k, v in out.items() if k != "params"})
    records = {
        "params.json": used,
        "metadata.json": metadata,
        "run.json": {"run_id": run_id, "task": "S1-08", "image_id": metadata["image_id"],
                     "data_kind": metadata["data_kind"], "code_version": version,
                     "config": str(args.config.relative_to(ROOT) if args.config.is_relative_to(ROOT) else args.config),
                     "overrides": args.set, "created_at_utc": datetime.now(timezone.utc).isoformat()},
    }
    if truth:
        records["truth_craters.json"] = truth
    for name, value in records.items():
        (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    print(f"Đã lưu: {directory.relative_to(ROOT)}")
    print(f"  pixel hợp lệ {used['valid_ratio']:.1%} | P{used['p_lo']}={used['p_lo_value']:.1f}, "
          f"P{used['p_hi']}={used['p_hi_value']:.1f} | Canny low/high = {used['canny_low']:.1f}/{used['canny_high']:.1f}")
    print(f"  biên Canny {used['edge_px_canny']} px → sau mặt nạ {used['edge_px_final']} px")


if __name__ == "__main__":
    main()
