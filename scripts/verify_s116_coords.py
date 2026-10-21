"""S1-16: kiểm tra công thức quy đổi tọa độ trên 26 ảnh của bundle S1-06.

Chỉ dùng thư viện chuẩn. Với mỗi ảnh: đổi tâm ảnh cắt (x = y = 255.5) về pixel ảnh
nguồn theo công thức của src/contracts.py, đổi sang kinh/vĩ độ bằng affine + phép chiếu
Equirectangular của chính metadata, rồi so với center_lat/center_lon đã lưu. Kiểm tra
thêm dải bán kính theo D_min/D_max và cửa sổ cắt nằm trong ảnh nguồn.

Giới hạn: chỉ kiểm tâm ảnh cắt, và cả 26 ảnh đều có k = 1, nên số hạng (k − 1)/2 và
chiều ngược (kinh/vĩ độ → pixel ảnh cắt) của S1-10 chưa được kiểm tự động ở đây.

Chạy từ thư mục gốc repo:  python scripts/verify_s116_coords.py
"""
from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.contracts import radius_range_px, source_coordinates  # noqa: E402

BUNDLE = ROOT / "data" / "s106_bundle" / "s106_lroc_browse_v2.zip"
TOL_DEG = 1e-9


def wkt_param(wkt: str, name: str) -> float:
    return float(re.search(rf'PARAMETER\["{name}",([-0-9.eE+]+)\]', wkt).group(1))


def source_pixel_to_lonlat(meta: dict, x_src: float, y_src: float) -> tuple[float, float]:
    """x_src, y_src: tọa độ pixel ảnh nguồn, TÂM pixel ở số nguyên (quy ước contracts.py).

    Affine của rasterio tính theo GÓC pixel nên phải cộng 0,5 trước khi áp affine."""
    src = meta["source"]
    a, b, c, d, e, f = src["source_transform"]
    col, row = x_src + 0.5, y_src + 0.5
    X, Y = a * col + b * row + c, d * col + e * row + f
    wkt = src["source_crs_wkt"]
    radius = float(re.search(r'SPHEROID\["[^"]*",([0-9.]+),', wkt).group(1))
    phi1 = math.radians(wkt_param(wkt, "standard_parallel_1"))
    lon0 = wkt_param(wkt, "central_meridian")
    lat = math.degrees(Y / radius)
    lon = lon0 + math.degrees(X / (radius * math.cos(phi1)))
    return lat, (lon + 180) % 360 - 180


def main() -> int:
    failures = 0
    with zipfile.ZipFile(BUNDLE) as z:
        names = sorted(n for n in z.namelist() if n.endswith(".json"))
        for name in names:
            m = json.loads(z.read(name))
            x_src, y_src, _ = source_coordinates(255.5, 255.5, 1.0, m)
            lat, lon = source_pixel_to_lonlat(m, x_src, y_src)
            d_lat, d_lon = abs(lat - m["center_lat"]), abs(lon - m["center_lon"])
            rmin, rmax = radius_range_px(m["radius"]["d_min_m"], m["radius"]["d_max_m"], m["scale_m_per_px"])
            in_bounds = (m["crop_x0"] + 512 * m["downsample_k"] <= m["source"]["source_width"]
                         and m["crop_y0"] + 512 * m["downsample_k"] <= m["source"]["source_height"])
            ok = (d_lat < TOL_DEG and d_lon < TOL_DEG and (rmin, rmax) == (m["radius"]["r_min_px"], m["radius"]["r_max_px"])
                  and in_bounds)
            failures += not ok
            print(f"{'OK  ' if ok else 'LOI '}{m['image_id']:<30} k={m['downsample_k']} "
                  f"dlat={d_lat:.1e} dlon={d_lon:.1e} r=[{rmin},{rmax}] trong_anh_nguon={in_bounds}")
    print(f"\n{len(names)} ảnh, {failures} lỗi")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
