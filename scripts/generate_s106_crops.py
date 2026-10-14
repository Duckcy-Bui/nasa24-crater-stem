"""Reproduce S1-06 crops from the locked LROC TIFF sources.

Only imagery is generated. Missing crater references stay explicitly unavailable;
this script never invents catalogue labels or treats zero intensity as nodata.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.crs import CRS
from rasterio.warp import transform
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.contracts import radius_range_px, validate_metadata

BUNDLE_DIR = ROOT / "data" / "s106_bundle"
CROPS_CONFIG = json.loads((BUNDLE_DIR / "crops.json").read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalization_info(valid_pixels: np.ndarray) -> dict:
    """Record the actual stretch, retaining sparse features on flat backgrounds."""
    valid = np.asarray(valid_pixels, dtype=np.float64)
    if valid.size == 0 or not np.isfinite(valid).all():
        raise ValueError("Không có tập pixel hữu hạn để chuẩn hóa.")
    percentile_values = np.percentile(valid, (0.5, 99.5))
    lo, hi = (float(v) for v in percentile_values)
    strategy = "percentile_0.5_99.5"
    if hi <= lo:
        lo, hi = float(valid.min()), float(valid.max())
        strategy = "min_max_fallback" if hi > lo else "constant"
    return {"percentile_values": [float(v) for v in percentile_values],
            "normalization_bounds": [lo, hi], "normalization_strategy": strategy}


def normalize_p05_p995(arr: np.ndarray, valid_mask: np.ndarray | None = None) -> np.ndarray:
    """Percentiles include all valid finite pixels, including legitimate zeros."""
    arr = np.asarray(arr)
    if arr.ndim != 2 or arr.dtype.kind not in "uif":
        raise ValueError("Ảnh phải là mảng số 2 chiều.")
    mask = np.isfinite(arr)
    if valid_mask is not None:
        valid_mask = np.asarray(valid_mask)
        if valid_mask.dtype != np.bool_ or valid_mask.shape != arr.shape:
            raise ValueError("valid_mask phải là bool và cùng kích thước ảnh.")
        mask &= valid_mask
    if not mask.any():
        raise ValueError("Cửa sổ không có pixel hợp lệ.")
    valid = arr[mask].astype(np.float64)
    lo, hi = normalization_info(valid)["normalization_bounds"]
    normalized = np.zeros(arr.shape, dtype=np.float32)
    if hi > lo:
        normalized[mask] = np.clip((valid - lo) / (hi - lo), 0, 1).astype(np.float32)
    return normalized


def read_crop(tif_path: Path, x0: int, y0: int, size: int = 512) -> tuple[np.ndarray, np.ndarray, dict]:
    """Read a complete crop with raster masks, finite checks and lunar geometry."""
    if size != 512 or any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in (x0, y0)):
        raise ValueError("Cửa sổ phải là 512×512 với x0/y0 nguyên không âm.")
    with rasterio.open(tif_path) as src:
        if src.count != 1 or src.crs is None or not src.crs.is_projected:
            raise ValueError("Nguồn phải là ảnh một băng với CRS chiếu đã xác minh.")
        if x0 + size > src.width or y0 + size > src.height:
            raise ValueError("Cửa sổ cắt vượt ra ngoài ảnh nguồn.")
        affine = src.transform
        if not (math.isclose(affine.b, 0, abs_tol=1e-10) and
                math.isclose(affine.d, 0, abs_tol=1e-10) and affine.a > 0 and affine.e < 0 and
                math.isclose(affine.a, -affine.e, rel_tol=1e-8)):
            raise ValueError("Nguồn xoay/lệch hoặc pixel không vuông; cần chuẩn hóa trước.")
        crs_info = src.crs.to_dict()
        if crs_info.get("proj") != "eqc" or crs_info.get("units") != "m":
            raise ValueError("Chỉ hỗ trợ nguồn Moon Equirectangular mét đã xác minh.")
        major = float(crs_info.get("R", crs_info.get("a", 0)))
        minor = float(crs_info.get("R", crs_info.get("b", 0)))
        if not (math.isclose(major, 1737400, rel_tol=1e-8) and math.isclose(minor, major, rel_tol=1e-8)):
            raise ValueError("CRS không phải mặt cầu Mặt Trăng R=1737400 m.")
        win = Window(x0, y0, size, size)
        arr = src.read(1, window=win)
        valid_mask = (src.read_masks(1, window=win) != 0) & np.isfinite(arr)
        # The crop centre lies between pixels (255,255) and (256,256).
        cx = affine.a * (x0 + size / 2) + affine.c
        cy = affine.e * (y0 + size / 2) + affine.f
        geographic = CRS.from_dict(proj="longlat", R=major)
        lons, lats = transform(src.crs, geographic, [cx], [cy])
        geometry = {
            "scale_m_per_px": float(affine.a),
            "center_lat": float(lats[0]),
            "center_lon": float((lons[0] + 180) % 360 - 180),
            "source_width": src.width, "source_height": src.height,
            "source_crs_wkt": src.crs.to_wkt(),
            "source_transform": list(affine)[:6],
            "source_nodata": float(src.nodata) if src.nodata is not None and math.isfinite(src.nodata) else None,
            "mask_origin": "rasterio.read_masks AND isfinite; zero intensity is not nodata",
        }
    return arr, valid_mask, geometry


def sun_metadata(cfg: dict) -> dict:
    side = cfg.get("sun_side")
    # side_only is a coarse direction, never a measured azimuth.
    source = cfg["sun_source"]
    if cfg["stt"] <= 6:
        source += "; không dùng trung điểm dải góc tới làm góc đo của cửa sổ"
    if cfg.get("sun_side_candidate"):
        source += "; phía Đông là suy từ dấu, CHƯA xác minh; không dùng S1-11"
    return {
        "azimuth_deg": 270.0 if side == "west" else None,
        "incidence_deg": cfg["sun_inc"],
        "quality": "side_only" if side == "west" else "none",
        "side": side,
        "side_candidate": cfg.get("sun_side_candidate"),
        "incidence_range_deg": cfg.get("incidence_range_deg"),
        "source": source,
    }


def make_crop(tif_path: Path, cfg: dict, source: dict, output_dir: Path, *, overwrite: bool = False) -> dict:
    image_id = cfg["image_id"]
    arr, mask, geometry = read_crop(tif_path, cfg["x0"], cfg["y0"])
    r_min, r_max = radius_range_px(cfg["d_min_m"], cfg["d_max_m"], geometry["scale_m_per_px"])
    metadata = {
        "schema_version": "1.0", "data_kind": "real", "image_id": image_id,
        "source_stt": cfg["stt"], "product_id": cfg["product_id"], "body": "moon",
        "crop_x0": cfg["x0"], "crop_y0": cfg["y0"], "downsample_k": 1,
        "width": 512, "height": 512, "scale_m_per_px": geometry["scale_m_per_px"],
        "center_lat": geometry["center_lat"], "center_lon": geometry["center_lon"],
        "north_up": True, "north_angle_deg": 0.0, "sun": sun_metadata(cfg),
        "radius": {"d_min_m": cfg["d_min_m"], "d_max_m": cfg["d_max_m"],
                   "r_min_px": r_min, "r_max_px": r_max},
        "valid_ratio": float(mask.mean()), "valid_mask_file": f"{image_id}_valid_mask.npy",
        "preprocess": {"version": "s106-crop-v2", "p_lo": 0.5, "p_hi": 99.5,
                       "generator_sha256": sha256_file(Path(__file__)),
                       "crops_config_sha256": sha256_file(BUNDLE_DIR / "crops.json"),
                       **normalization_info(arr[mask])},
        "source": {**source, **geometry, "source_product_level": "browse",
                   "radiometrically_calibrated": False,
                   "credit": "NASA/GSFC/Arizona State University (LROC)"},
        "reference_status": "unavailable",
        "reference_note": "Chưa nhập và xác minh nhãn hố thật cho cửa sổ này. Không dùng để chấm Precision/Recall hoặc điểm game theo danh mục. Robbins không bao phủ đầy đủ hố nhỏ 20–500 m.",
        "comparison_pair": cfg.get("comparison_pair"),
        "note": f"Ảnh browse thật cho demo xử lý ảnh: {cfg['region_group']}; không dùng đo quang học hoặc kết luận tuổi địa chất.",
    }
    validate_metadata(metadata)
    normalized = normalize_p05_p995(arr, mask)
    names = [f"{image_id}.npy", f"{image_id}.png", f"{image_id}.json", f"{image_id}_valid_mask.npy"]
    # Reject old fabricated labels rather than leaving them beside the new data.
    legacy = output_dir / f"{image_id}_craters_catalogue.json"
    if legacy.exists():
        raise ValueError(f"Có catalogue cũ chưa xác minh: {legacy}. Di chuyển file ra khỏi bộ dữ liệu trước khi tái tạo.")
    if not overwrite and any((output_dir / name).exists() for name in names):
        raise FileExistsError(f"Đã có đầu ra {image_id}; dùng thư mục mới hoặc --overwrite.")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir) as staging:
        tmp = Path(staging)
        np.save(tmp / names[0], normalized, allow_pickle=False)
        Image.fromarray(np.rint(normalized * 255).astype(np.uint8)).save(tmp / names[1])
        (tmp / names[2]).write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        np.save(tmp / names[3], mask.astype(bool), allow_pickle=False)
        for name in names:
            (tmp / name).replace(output_dir / name)
    return {"image_id": image_id, "source_stt": cfg["stt"], "product_id": cfg["product_id"],
            "region_group": cfg["region_group"], "crop_x0": cfg["x0"], "crop_y0": cfg["y0"],
            "scale_m_per_px": geometry["scale_m_per_px"], "center_lat": geometry["center_lat"],
            "center_lon": geometry["center_lon"], "sun_inc": cfg["sun_inc"],
            "sun_quality": metadata["sun"]["quality"], "d_min_m": cfg["d_min_m"], "d_max_m": cfg["d_max_m"],
            "r_min_px": r_min, "r_max_px": r_max, "valid_ratio": float(mask.mean()),
            "reference_status": "unavailable", "comparison_pair": cfg.get("comparison_pair")}


def process_all_crops(raw_dir: Path = ROOT / "data" / "raw", output_dir: Path = ROOT / "data" / "processed", *, overwrite: bool = False) -> list[dict]:
    sources = json.loads((BUNDLE_DIR / "sources.json").read_text(encoding="utf-8"))
    by_name = {s["filename"]: s for s in sources}
    # Check every input before emitting any crop; a partial dataset is not success.
    for source in sources:
        path = raw_dir / source["filename"]
        if not path.is_file():
            raise FileNotFoundError(f"Thiếu {path}. Chạy scripts/download_s106_sources.py hoặc dùng bundle ngoại tuyến.")
        if path.stat().st_size != source["bytes"] or sha256_file(path) != source["sha256"]:
            raise ValueError(f"Nguồn sai kích thước/SHA256: {path}")
    records = []
    for cfg in CROPS_CONFIG:
        record = make_crop(raw_dir / cfg["file"], cfg, by_name[cfg["file"]], output_dir, overwrite=overwrite)
        records.append(record)
        print(f"OK {record['image_id']}: valid={record['valid_ratio']:.6f}; reference=unavailable")
    return records


def export_documentation(records: list[dict], docs_dir: Path = ROOT / "docs") -> None:
    if not records:
        raise ValueError("Không có ảnh để lập bảng.")
    docs_dir.mkdir(parents=True, exist_ok=True)
    with (docs_dir / "S1-06_BANG_ANH_XA.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    lines = ["# Bảng ánh xạ ảnh cắt S1-06", "",
             f"{len(records)} ảnh browse LROC thật, 512×512 float32 [0,1], mặt nạ bool đi kèm. Không sinh nhãn hố giả.", "",
             "Đọc [hướng dẫn bàn giao](S1-06_HUONG_DAN_DU_LIEU.md) để giải nén, tái tạo và hiểu giới hạn.", "",
             "- Apollo 16: `moon_ap16_m102064759r_c01` (81,08°) và `moon_ap16_m109134835l_c01` (7,64°) cùng cửa sổ (1190,2750), cùng CRS/affine và 2 m/px. Đây là cặp cùng vùng để minh họa điều kiện chiếu sáng.",
             "- Apollo 15 High-Sun/Low-Sun cắt các tọa độ khác nhau, không phải cặp cùng mặt đất. Không quy mọi khác biệt phát hiện hố cho góc nắng.",
             "- Van de Graaff/Mare Frigoris cùng 20 m/px và dải D 200–4000 m: so sánh mật độ minh họa, chưa chứng minh tuổi địa chất; điều kiện chiếu sáng khác nhau.",
             "- Mọi ảnh có reference_status=unavailable: chưa dùng để đánh giá P/R hoặc chấm game theo catalogue.", "",
             "| Image ID | STT | Crop (x0,y0) | m/px | Tâm lat/lon | Góc tới | Hướng nắng | Dải r (px) | Hợp lệ |",
             "|---|---:|---|---:|---|---|---|---|---:|"]
    for r in records:
        inc = "không có số đo cửa sổ" if r["sun_inc"] is None else str(r["sun_inc"])
        lines.append(f"| `{r['image_id']}` | {r['source_stt']} | ({r['crop_x0']},{r['crop_y0']}) | {r['scale_m_per_px']} | {r['center_lat']:.6f}, {r['center_lon']:.6f} | {inc} | {r['sun_quality']} | {r['r_min_px']}–{r['r_max_px']} | {r['valid_ratio']:.6f} |")
    (docs_dir / "S1-06_BANG_ANH_XA_ANH_CAT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--export-docs", action="store_true")
    args = parser.parse_args()
    records = process_all_crops(args.raw_dir, args.output_dir, overwrite=args.overwrite)
    if args.export_docs:
        export_documentation(records)
    print(f"Đủ {len(records)} ảnh; catalogue chưa khả dụng.")


if __name__ == "__main__":
    main()
