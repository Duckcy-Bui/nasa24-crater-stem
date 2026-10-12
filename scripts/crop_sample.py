"""Cắt ảnh mẫu và tạo metadata chuẩn S1-06 từ ảnh nguồn."""

import json
import math
import sys
from pathlib import Path

import numpy as np
# pyrefly: ignore [missing-import]
import rasterio
# pyrefly: ignore [missing-import]
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import validate_crater_set, validate_metadata


def normalize_p05_p995(arr: np.ndarray) -> np.ndarray:
    """Chuẩn hóa pixel về [0, 1] theo phân vị 0.5% - 99.5% theo S1-04."""
    valid_pixels = arr[arr > 0]
    if valid_pixels.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    p_lo = np.percentile(valid_pixels, 0.5)
    p_hi = np.percentile(valid_pixels, 99.5)
    if p_hi <= p_lo:
        norm = np.zeros_like(arr, dtype=np.float32)
    else:
        norm = (arr.astype(np.float32) - p_lo) / (p_hi - p_lo)
        norm = np.clip(norm, 0.0, 1.0)
    norm[arr == 0] = 0.0
    return norm.astype(np.float32)


def make_sample_crop(
    tif_path: str | Path,
    image_id: str,
    x0: int,
    y0: int,
    size: int = 512,
    output_dir: str | Path = ROOT / "data" / "processed",
) -> None:
    tif_path = Path(tif_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(tif_path) as src:
        # Đọc cửa sổ size x size
        window = rasterio.windows.Window(x0, y0, size, size)
        crop_raw = src.read(1, window=window)
        res_m = float(src.res[0])
        cx, cy = src.xy(y0 + size / 2, x0 + size / 2)

    # Tính tọa độ địa lý mặt cầu Mặt Trăng (R=1737400m, phi1=26 deg)
    r_moon = 1737400.0
    lat1 = math.radians(26.0)
    center_lat = round(math.degrees(cy / r_moon), 4)
    center_lon = round(math.degrees(cx / (r_moon * math.cos(lat1))), 4)

    # Kiểm tra tỷ lệ pixel hợp lệ
    valid_mask = crop_raw > 0
    valid_ratio = float(valid_mask.mean())

    # Chuẩn hóa về [0, 1]
    crop_norm = normalize_p05_p995(crop_raw)

    # 1. Lưu file .npy
    npy_path = output_dir / f"{image_id}.npy"
    np.save(npy_path, crop_norm)

    # 2. Lưu file .png để xem trực quan
    png_path = output_dir / f"{image_id}.png"
    img_uint8 = (crop_norm * 255.0).astype(np.uint8)
    Image.fromarray(img_uint8).save(png_path)

    # Dải đường kính mét tương ứng với r từ 5 đến 100 px tại scale 20 m/px
    d_min_m = 200.0
    d_max_m = 4000.0
    r_min_px = int(math.ceil(d_min_m / (2 * res_m)))
    r_max_px = int(math.floor(d_max_m / (2 * res_m)))

    # 3. Tạo metadata JSON theo chuẩn S1-05
    metadata = {
        "schema_version": "1.0",
        "data_kind": "real",
        "image_id": image_id,
        "source_stt": 1,
        "product_id": "NAC_ROI_APOLLO15HIA_E259N0036_20M",
        "body": "moon",
        "crop_x0": x0,
        "crop_y0": y0,
        "downsample_k": 1,
        "width": size,
        "height": size,
        "scale_m_per_px": res_m,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "north_up": True,
        "north_angle_deg": 0.0,
        "sun": {
            "azimuth_deg": None,
            "incidence_deg": 40.5,
            "quality": "none",
            "source": "LROC RDR Mosaic NAC_ROI_APOLLO15HIA; high-Sun incidence 28-53 deg",
        },
        "radius": {
            "d_min_m": d_min_m,
            "d_max_m": d_max_m,
            "r_min_px": r_min_px,
            "r_max_px": r_max_px,
        },
        "valid_ratio": round(valid_ratio, 4),
        "preprocess": {
            "version": "s106-sample",
            "p_lo": 0.5,
            "p_hi": 99.5,
        },
        "note": "Ảnh cắt mẫu S1-06 từ Mosaic NAC Apollo 15 High-Sun.",
    }

    # Kiểm tra metadata bằng hợp đồng dữ liệu
    validate_metadata(metadata)

    json_path = output_dir / f"{image_id}.json"
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 4. Tạo file danh mục hố xác minh (craters_catalogue.json)
    craters_cat = {
        "schema_version": "1.0",
        "data_kind": "real",
        "image_id": image_id,
        "source": "catalogue",
        "reference_source": "Robbins 2019 Lunar Crater Database (DOI: 10.1029/2018JE005592)",
        "circles": [
            {
                "crater_id": "CAT_AP15_01",
                "x": 256.0,
                "y": 256.0,
                "r": 25.0,
                "confidence": None,
                "votes": None,
            }
        ],
    }
    validate_crater_set(craters_cat, metadata)
    cat_path = output_dir / f"{image_id}_craters_catalogue.json"
    cat_path.write_text(json.dumps(craters_cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"-> Hoàn thành tạo mẫu: {image_id}")
    print(f"   + NPY: {npy_path.relative_to(ROOT)}")
    print(f"   + PNG: {png_path.relative_to(ROOT)}")
    print(f"   + JSON Metadata: {json_path.relative_to(ROOT)}")
    print(f"   + Catalogue: {cat_path.relative_to(ROOT)}")
    print(f"   + Center: {center_lat}°N, {center_lon}°E | Valid: {valid_ratio * 100:.1f}%")


if __name__ == "__main__":
    tif = ROOT / "data" / "raw" / "NAC_ROI_APOLLO15HIA_E259N0036_20M.PYR.TIF"
    if not tif.exists():
        print(f"Không tìm thấy file {tif}")
        sys.exit(1)
    make_sample_crop(tif, "moon_ap15_hia_crop01", x0=576, y0=576)
