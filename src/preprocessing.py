"""Hưng — S1-08. Chuỗi tiền xử lý B0–B8 theo đặc tả S1-04 mục 8.

Phân chia tự viết / thư viện (S1-04 mục 1):

| Bước | Thao tác                        | Cài đặt                     |
|------|---------------------------------|-----------------------------|
| B0   | Đọc file, cắt cửa sổ            | THƯ VIỆN rasterio (GDAL)    |
| B1   | Thu nhỏ trung bình khối k×k     | TỰ VIẾT NumPy               |
| B2   | Ảnh xám BT.601                  | TỰ VIẾT NumPy               |
| B3   | Chuẩn hóa theo phân vị          | TỰ VIẾT NumPy               |
| B4   | CLAHE                           | THƯ VIỆN OpenCV createCLAHE |
| B5   | Gaussian tách hai chiều         | TỰ VIẾT NumPy               |
| B6   | Sobel 3×3                       | TỰ VIẾT NumPy               |
| B7   | Canny                           | THƯ VIỆN OpenCV Canny       |
| B8   | Mặt nạ biên                     | TỰ VIẾT NumPy               |

Các bước tự viết chỉ dùng phép toán mảng của NumPy (cộng, nhân, cắt lát,
phân vị); không gọi hàm lọc ảnh dựng sẵn. OpenCV chỉ được import trong B4, B7
và trong tests để đối chiếu.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

SIZE = 512
MODULE_VERSION = "s108-1"

STEPS = (
    ("B0", "Đọc file và cắt cửa sổ", "THƯ VIỆN: rasterio (GDAL)"),
    ("B1", "Thu nhỏ trung bình khối k×k", "TỰ VIẾT: NumPy"),
    ("B2", "Ảnh xám BT.601", "TỰ VIẾT: NumPy"),
    ("B3", "Chuẩn hóa theo phân vị", "TỰ VIẾT: NumPy"),
    ("B4", "Tăng tương phản CLAHE", "THƯ VIỆN: OpenCV createCLAHE"),
    ("B5", "Làm trơn Gaussian tách hai chiều", "TỰ VIẾT: NumPy"),
    ("B6", "Gradient Sobel 3×3", "TỰ VIẾT: NumPy"),
    ("B7", "Biên Canny", "THƯ VIỆN: OpenCV Canny"),
    ("B8", "Mặt nạ biên", "TỰ VIẾT: NumPy"),
)

DEFAULT_PARAMS = {
    "p_lo": 0.5,
    "p_hi": 99.5,
    "clahe_clip": 2.0,
    "clahe_grid": 8,
    "clahe_bits": 8,
    "gauss_sigma": 1.5,
    "gauss_kernel_size": None,  # None: tự tính 2⌈3σ⌉+1
    "border_mode": "reflect_101",
    "canny_high_pct": 90,
    "canny_low_ratio": 0.4,
    "edge_margin_px": 6,
}


# ---------------------------------------------------------------- B0 THƯ VIỆN
def read_window(path: str, x0: int, y0: int, k: int, band: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """B0 [THƯ VIỆN rasterio]: đọc ô vuông cạnh 512·k từ (x0, y0).

    Trả (ảnh float32, valid bool). Pixel nodata/NaN/±inf → valid=False, giá trị 0.
    """
    import rasterio
    from rasterio.windows import Window

    side = SIZE * k
    with rasterio.open(path) as src:
        if x0 < 0 or y0 < 0 or x0 + side > src.width or y0 + side > src.height:
            raise ValueError(f"Cửa sổ {side}px tại ({x0}, {y0}) vượt ngoài ảnh {src.width}×{src.height}.")
        window = Window(x0, y0, side, side)
        image = src.read(band, window=window).astype(np.float32)
        valid = src.read_masks(band, window=window) > 0
    valid &= np.isfinite(image)
    image[~valid] = 0
    return image, valid


# ---------------------------------------------------------------- B1 TỰ VIẾT
def block_mean(image: np.ndarray, valid: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """B1 [TỰ VIẾT]: trung bình mỗi khối k×k; khối có pixel lỗi thì lỗi cả khối."""
    h, w = image.shape[:2]
    if k < 1 or h % k or w % k:
        raise ValueError(f"Kích thước {h}×{w} không chia hết cho k={k}.")
    shape = (h // k, k, w // k, k) + image.shape[2:]
    out = image.astype(np.float64).reshape(shape).mean(axis=(1, 3))
    out_valid = valid.reshape(h // k, k, w // k, k).all(axis=(1, 3))
    out[~out_valid] = 0
    return out.astype(np.float32), out_valid


# ---------------------------------------------------------------- B2 TỰ VIẾT
def to_gray(image: np.ndarray) -> np.ndarray:
    """B2 [TỰ VIẾT]: 1 kênh giữ nguyên; 3/4 kênh RGB(A) → Y = 0,299R + 0,587G + 0,114B."""
    if image.ndim == 2:
        return image.astype(np.float32)
    if image.ndim == 3 and image.shape[2] in (3, 4):
        r, g, b = (image[..., i].astype(np.float64) for i in range(3))
        return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)
    raise ValueError(f"Không hỗ trợ ảnh có dạng {image.shape}.")


# ---------------------------------------------------------------- B3 TỰ VIẾT
def normalize_percentile(image: np.ndarray, valid: np.ndarray, p_lo: float, p_hi: float) -> tuple[np.ndarray, float, float]:
    """B3 [TỰ VIẾT]: I' = clip((I − P_lo)/(P_hi − P_lo), 0, 1), phân vị tính trên pixel hợp lệ."""
    if not valid.any():
        raise ValueError("Ảnh không có pixel hợp lệ.")
    lo, hi = np.percentile(image[valid].astype(np.float64), [p_lo, p_hi])
    if hi <= lo:
        raise ValueError(f"Ảnh phẳng màu (P{p_lo}={lo}, P{p_hi}={hi}); không chuẩn hóa được.")
    out = np.clip((image.astype(np.float64) - lo) / (hi - lo), 0, 1)
    out[~valid] = 0
    return out.astype(np.float32), float(lo), float(hi)


# ---------------------------------------------------------------- B4 THƯ VIỆN
def clahe(image: np.ndarray, valid: np.ndarray, clip: float, grid: int, bits: int = 8) -> np.ndarray:
    """B4 [THƯ VIỆN OpenCV]: CLAHE trên uint8 (×255) hoặc uint16 (×65535), trả lại float32 [0, 1].

    Lệch S1-04 (đặc tả ghi uint16): OpenCV đặt ngưỡng cắt mỗi bin là
    max(1, clip·(số pixel một ô)/(số bin)). Với uint16 có 65536 bin, ô 64×64
    cho 2·4096/65536 < 1 nên ngưỡng luôn bằng 1 — clipLimit 1, 2, 4 cho cùng
    một kết quả và nhiễu vùng phẳng bị khuếch đại mạnh. uint8 (256 bin) cho
    ngưỡng 32, đúng ý nghĩa clipLimit. Mặc định 8 bit; giữ 16 để so sánh.
    """
    import cv2

    if bits not in (8, 16):
        raise ValueError("clahe_bits phải là 8 hoặc 16.")
    top, dtype = (255, np.uint8) if bits == 8 else (65535, np.uint16)
    quantized = np.round(np.clip(image, 0, 1) * top).astype(dtype)
    out = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid)).apply(quantized)
    out = out.astype(np.float32) / top
    out[~valid] = 0
    return out


# ------------------------------------------------- Phép nhân chập tự viết (B5, B6)
def correlate_1d(image: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
    """[TỰ VIẾT] Tương quan 1 chiều theo trục axis, biên phản chiếu kiểu BORDER_REFLECT_101.

    out[i] = Σ_j kernel[j] · I[i + j − R]. Cộng dồn các lát cắt dịch chuyển của
    ảnh đã đệm; tính trong float64 để sai số làm tròn nhỏ hơn 1e-5.
    """
    r = len(kernel) // 2
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r, r)
    # np.pad "reflect" không lặp lại pixel mép, đúng như REFLECT_101 của OpenCV.
    padded = np.pad(image.astype(np.float64), pad, mode="reflect")
    n = image.shape[axis]
    out = np.zeros(image.shape, dtype=np.float64)
    for j, weight in enumerate(kernel):
        if weight == 0:
            continue
        index = [slice(None), slice(None)]
        index[axis] = slice(j, j + n)
        out += weight * padded[tuple(index)]
    return out


# ---------------------------------------------------------------- B5 TỰ VIẾT
def gaussian_kernel(sigma: float, size: int | None = None) -> np.ndarray:
    """[TỰ VIẾT] g(i) = exp(−i²/2σ²) / Σ exp(−j²/2σ²), i = −R…R, mặc định R = ⌈3σ⌉."""
    if sigma <= 0:
        raise ValueError("gauss_sigma phải > 0.")
    if size is None:
        size = 2 * math.ceil(3 * sigma) + 1
    if size < 3 or size % 2 == 0:
        raise ValueError("gauss_kernel_size phải là số lẻ >= 3.")
    i = np.arange(size, dtype=np.float64) - size // 2
    g = np.exp(-(i ** 2) / (2 * sigma ** 2))
    return g / g.sum()


def gaussian_blur(image: np.ndarray, sigma: float, size: int | None = None) -> np.ndarray:
    """B5 [TỰ VIẾT]: Gaussian tách được — lọc theo hàng (trục x) rồi theo cột (trục y)."""
    g = gaussian_kernel(sigma, size)
    return correlate_1d(correlate_1d(image, g, axis=1), g, axis=0).astype(np.float32)


# ---------------------------------------------------------------- B6 TỰ VIẾT
SOBEL_SMOOTH = np.array([1.0, 2.0, 1.0])
SOBEL_DIFF = np.array([-1.0, 0.0, 1.0])


def sobel(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """B6 [TỰ VIẾT]: Sobel 3×3 không chia 8; trả gx, gy, |G|, θ = atan2(gy, gx).

    Kx = [1,2,1]ᵀ·[-1,0,1] và Ky = [-1,0,1]ᵀ·[1,2,1], tách thành hai lượt 1 chiều.
    x sang phải, y xuống dưới: gx > 0 khi sáng dần sang phải, gy > 0 khi sáng dần xuống dưới.
    """
    gx = correlate_1d(correlate_1d(image, SOBEL_DIFF, axis=1), SOBEL_SMOOTH, axis=0)
    gy = correlate_1d(correlate_1d(image, SOBEL_SMOOTH, axis=1), SOBEL_DIFF, axis=0)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    theta = np.arctan2(gy, gx)
    return tuple(a.astype(np.float32) for a in (gx, gy, mag, theta))


# ---------------------------------------------------------------- B7 THƯ VIỆN
def canny(smooth: np.ndarray, mag: np.ndarray, valid: np.ndarray, high_pct: float, low_ratio: float) -> tuple[np.ndarray, float, float]:
    """B7 [THƯ VIỆN OpenCV]: Canny trên uint8 (×255), L2gradient, aperture 3.

    Ngưỡng tự động (phần tự viết): high = P{high_pct} của |G|·255 trên vùng hợp lệ,
    low = low_ratio·high. |G| của B6 không chia 8 nên cùng thang với gradient
    OpenCV tính trên ảnh uint8.
    """
    import cv2

    high = float(np.percentile(mag[valid].astype(np.float64) * 255, high_pct))
    low = low_ratio * high
    if high <= 0:
        return np.zeros(smooth.shape, dtype=bool), low, high
    u8 = np.round(np.clip(smooth, 0, 1) * 255).astype(np.uint8)
    edges = cv2.Canny(u8, low, high, apertureSize=3, L2gradient=True) > 0
    return edges, low, high


# ---------------------------------------------------------------- B8 TỰ VIẾT
def erode(mask: np.ndarray, margin: int) -> np.ndarray:
    """[TỰ VIẾT] Co vùng True đi margin px (phần tử cấu trúc vuông), ngoài ảnh coi là False."""
    if margin <= 0:
        return mask.copy()
    out = mask
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (margin, margin)
        padded = np.pad(out, pad, constant_values=False)
        n = mask.shape[axis]
        result = np.ones(mask.shape, dtype=bool)
        for j in range(2 * margin + 1):
            index = [slice(None), slice(None)]
            index[axis] = slice(j, j + n)
            result &= padded[tuple(index)]
        out = result
    return out


def mask_edges(edges: np.ndarray, valid: np.ndarray, margin: int) -> tuple[np.ndarray, np.ndarray]:
    """B8 [TỰ VIẾT]: bỏ biên trong lề margin px tính từ mép ảnh và từ vùng nodata."""
    keep = erode(valid, margin)
    return edges & keep, keep


# ---------------------------------------------------------------- Chuỗi B1–B8
def resolve_params(params: dict | None) -> dict:
    """Ghép tham số người dùng với mặc định S1-04; báo lỗi nếu có khóa lạ."""
    params = dict(params or {})
    extra = set(params) - set(DEFAULT_PARAMS) - {"version", "status"}
    if extra:
        raise ValueError("Tham số tiền xử lý không biết: " + ", ".join(sorted(extra)))
    merged = {**DEFAULT_PARAMS, **{k: v for k, v in params.items() if k in DEFAULT_PARAMS}}
    if merged["border_mode"] != "reflect_101":
        raise ValueError("Chỉ hỗ trợ border_mode = reflect_101 (khớp mặc định OpenCV).")
    if merged["gauss_kernel_size"] is None:
        merged["gauss_kernel_size"] = 2 * math.ceil(3 * merged["gauss_sigma"]) + 1
    return merged


def preprocess(image: Any, metadata: dict, params: dict | None = None, valid_mask: Any = None) -> dict:
    """Chạy nối tiếp B1 → B8 trên ảnh đã đọc ở B0.

    image: ô cắt cạnh 512·k (k = metadata["downsample_k"]), 1 hoặc 3 kênh, kiểu
    số bất kỳ; hoặc ảnh đã thu nhỏ 512×512 (khi đó bỏ qua B1).
    valid_mask: bool cùng kích thước (tùy chọn); NaN/±inf luôn bị coi là lỗi.

    Trả dict theo DINH_DANG_DU_LIEU.md mục 3: gray, enhanced, smooth, gx, gy,
    mag, theta (float32 512×512), edges, valid_mask (bool), params; thêm
    downsampled (B1–B2, thang gốc) và edges_canny (B7 trước mặt nạ) để xem từng bước.
    """
    p = resolve_params(params)
    image = np.asarray(image)
    input_shape = [int(n) for n in image.shape]
    k = int(metadata.get("downsample_k", 1))

    valid = np.isfinite(image) if image.ndim == 2 else np.isfinite(image).all(axis=2)
    if valid_mask is not None:
        valid &= np.asarray(valid_mask, dtype=bool)
    image = np.where(np.isfinite(image), image, 0)

    # B1
    side = image.shape[:2]
    if side == (SIZE * k, SIZE * k) and k > 1:
        image, valid = block_mean(image, valid, k)
        b1_applied = True
    elif side == (SIZE, SIZE):
        image = image.astype(np.float32)
        b1_applied = False
    else:
        raise ValueError(f"Ảnh {side} không phải 512×512 hoặc 512·k với k={k}.")
    # B2
    downsampled = to_gray(image)
    downsampled[~valid] = 0
    # B3
    gray, lo_value, hi_value = normalize_percentile(downsampled, valid, p["p_lo"], p["p_hi"])
    # B4
    enhanced = clahe(gray, valid, p["clahe_clip"], p["clahe_grid"], p["clahe_bits"])
    # B5
    smooth = gaussian_blur(enhanced, p["gauss_sigma"], p["gauss_kernel_size"])
    # B6
    gx, gy, mag, theta = sobel(smooth)
    # B7
    edges_canny, canny_low, canny_high = canny(smooth, mag, valid, p["canny_high_pct"], p["canny_low_ratio"])
    # B8
    edges, _ = mask_edges(edges_canny, valid, p["edge_margin_px"])

    used = {
        "version": (params or {}).get("version", MODULE_VERSION),
        "module_version": MODULE_VERSION,
        **p,
        "downsample_k": k,
        "b1_applied": b1_applied,
        "input_shape": input_shape,
        "p_lo_value": lo_value,
        "p_hi_value": hi_value,
        "canny_high": canny_high,
        "canny_low": canny_low,
        "canny_aperture": 3,
        "canny_l2gradient": True,
        "valid_ratio": float(valid.mean()),
        "edge_px_canny": int(edges_canny.sum()),
        "edge_px_final": int(edges.sum()),
        "steps": [{"id": s, "name": n, "impl": i} for s, n, i in STEPS],
    }
    return {
        "downsampled": downsampled,
        "gray": gray,
        "enhanced": enhanced,
        "smooth": smooth,
        "gx": gx,
        "gy": gy,
        "mag": mag,
        "theta": theta,
        "edges_canny": edges_canny,
        "edges": edges,
        "valid_mask": valid,
        "params": used,
    }
