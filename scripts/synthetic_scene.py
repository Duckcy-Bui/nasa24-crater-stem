"""Cảnh hố giả lập để thử tiền xử lý khi chưa có ảnh thật (S1-08).

Dựng bản đồ độ cao gồm địa hình gợn và các hố (lòng parabol + vành nâng),
rồi tô bóng Lambert theo hướng nắng quy ước S1-04 mục 6:
u = (sin φ, −cos φ) chỉ về phía Mặt Trời trong ảnh, φ = azimuth + north_angle.
Không mô phỏng bóng đổ dài; đây là ảnh thử, không phải dữ liệu khoa học.
"""

from __future__ import annotations

import math

import numpy as np


def _smooth_noise(rng: np.random.Generator, size: int, scale_px: float) -> np.ndarray:
    """Nhiễu trơn bằng lọc thông thấp Gaussian trong miền tần số, chuẩn hóa độ lệch 1."""
    f = np.fft.fftfreq(size)
    fx, fy = np.meshgrid(f, f)
    spectrum = np.fft.fft2(rng.normal(size=(size, size))) * np.exp(-2 * (math.pi * scale_px) ** 2 * (fx ** 2 + fy ** 2))
    out = np.fft.ifft2(spectrum).real
    return out / out.std()


def make_scene(azimuth_deg: float, incidence_deg: float, *, size: int = 1024, n_craters: int = 45,
               r_range: tuple[float, float] = (14, 190), nodata_corner: bool = False, seed: int = 0):
    """Trả (ảnh float32 thang 12 bit, NaN ở vùng nodata; danh sách hố [(x, y, r)] theo px ô cắt)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:size, :size].astype(np.float64)
    dem = 6 * _smooth_noise(rng, size, 40) + 0.15 * _smooth_noise(rng, size, 2)

    # Bán kính theo luật lũy thừa: hố nhỏ nhiều hơn hố lớn.
    lo, hi = r_range
    radii = np.sort(lo * (hi / lo) ** rng.random(n_craters) ** 1.8)[::-1]
    craters = []
    for r in radii:
        cx, cy = rng.uniform(-0.05, 1.05, 2) * size
        d = np.hypot(xx - cx, yy - cy) / r
        depth, rim = 0.2 * r, 0.04 * r
        inside = depth * (d ** 2 - 1) + rim
        outside = rim / np.maximum(d, 1) ** 3
        dem += np.where(d < 1, inside, outside)
        craters.append((float(cx), float(cy), float(r)))

    phi = math.radians(azimuth_deg)
    inc = math.radians(incidence_deg)
    sun = (math.sin(inc) * math.sin(phi), -math.sin(inc) * math.cos(phi), math.cos(inc))
    fy, fx = np.gradient(dem)
    norm = np.sqrt(fx ** 2 + fy ** 2 + 1)
    shade = np.clip((-fx * sun[0] - fy * sun[1] + sun[2]) / norm, 0, None)

    albedo = 1 + 0.08 * _smooth_noise(rng, size, 60)
    image = albedo * shade
    image = image / np.percentile(image, 99.9) * 3000 + 300
    image += rng.normal(0, 25, image.shape)
    image = np.clip(np.round(image), 0, 4095).astype(np.float32)
    if nodata_corner:
        image[xx - yy > size * 0.78] = np.nan  # khoảng trống kiểu mosaic ở góc trên phải
    return image, craters
