"""Hưng — S2-09: số đếm, phân bố kích thước và so mật độ hai vùng.

Nguyên tắc (tiêu chí S2-09):
  - Hai vùng phải CÙNG tỷ lệ ảnh (m/px) và CÙNG dải đường kính vật lý [D_min, D_max).
  - Đường kính D = 2·r·s (m); diện tích = số pixel trong vùng đếm × s² / 10⁶ (km²).
  - Vùng gồm nhiều ô cắt có thể chồng nhau: diện tích lấy theo HỢP các vùng đếm
    trên hệ tọa độ ảnh nguồn; hố ở phần chồng chỉ đếm một lần.
  - Hố được đếm khi TÂM nằm trong vùng đếm.
  - Mật độ = N / A (hố/km²), khoảng tin cậy Poisson chính xác (Garwood).
  - So hai vùng: kiểm định nhị thức có điều kiện (Przyborowski & Wilenski 1940): với tổng
    N₁ + N₂ cố định, N₁ ~ Nhị thức(N₁ + N₂, A₁/(A₁ + A₂)) nếu hai mật độ bằng nhau.
Toàn bộ tự viết bằng Python/NumPy, không dùng scipy.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.contracts import validate_crater_set

SQRT2_BINS_START_M = 250.0  # biên dưới bin √2 đầu tiên trong báo cáo, theo CATWG (1979)


# ------------------------------------------------------------ thống kê Poisson / nhị thức
def _poisson_cdf(k: int, mu: float) -> float:
    if k < 0:
        return 0.0
    term = total = math.exp(-mu)
    for i in range(1, k + 1):
        term *= mu / i
        total += term
    return min(total, 1.0)


def poisson_interval(n: int, conf: float = 0.95) -> tuple[float, float]:
    """Khoảng tin cậy chính xác cho kỳ vọng Poisson khi quan sát n (Garwood, tìm nghiệm bằng chia đôi)."""
    if n < 0:
        raise ValueError("n phải >= 0.")
    a = (1 - conf) / 2

    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    hi_bound = n + 20 * math.sqrt(n + 1) + 20
    # Cận dưới: P(X >= n | mu) = a; cận trên: P(X <= n | mu) = a. Hàm dương khi mu còn nhỏ.
    lower = 0.0 if n == 0 else solve(lambda mu: a - (1 - _poisson_cdf(n - 1, mu)), 0.0, hi_bound)
    upper = solve(lambda mu: _poisson_cdf(n, mu) - a, 0.0, hi_bound)
    return lower, upper


def binomial_two_sided_p(k: int, n: int, p: float) -> float:
    """p-value hai phía của kiểm định nhị thức chính xác (cộng các kết quả có xác suất <= P(k))."""
    if n == 0:
        return 1.0
    probs = [math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    ref = probs[k] * (1 + 1e-9)
    return min(1.0, sum(q for q in probs if q <= ref))


# ------------------------------------------------------------ vùng đếm
def count_mask(rects: list[list[int]], exclude: list[list[int]] | None = None, size: int = 512) -> np.ndarray:
    """Mặt nạ vùng đếm trên ô 512×512 từ các hình chữ nhật [x0, y0, x1, y1) giữ lại và loại bỏ."""
    mask = np.zeros((size, size), dtype=bool)
    for x0, y0, x1, y1 in rects:
        mask[max(0, y0):min(size, y1), max(0, x0):min(size, x1)] = True
    for x0, y0, x1, y1 in exclude or []:
        mask[max(0, y0):min(size, y1), max(0, x0):min(size, x1)] = False
    return mask


def _source_shift(meta: dict) -> tuple[int, int]:
    if meta["downsample_k"] != 1:
        raise ValueError("S2-09 hiện chỉ hỗ trợ ô cắt k = 1 (mọi ô của bộ S1-06 đều k = 1).")
    return int(meta["crop_x0"]), int(meta["crop_y0"])


# ------------------------------------------------------------ đếm một vùng
def region_count(crops: list[dict], d_min_m: float, d_max_m: float, *, same_crater_center_frac: float = 0.5,
                 same_crater_radius_ratio: float = 0.7) -> dict:
    """Đếm hố của một vùng gồm nhiều ô cắt cùng ảnh nguồn.

    crops: [{"metadata": dict, "crater_set": dict (S1-05), "mask": bool 512×512, "valid": bool 512×512 | None}]
    Trả dict: scale, diện tích (px, km²), danh sách hố (tọa độ nguồn, D), số đếm, mật độ và khoảng tin cậy.
    """
    if not crops:
        raise ValueError("Vùng cần ít nhất một ô cắt.")
    scales = {float(c["metadata"]["scale_m_per_px"]) for c in crops}
    products = {c["metadata"]["product_id"] for c in crops}
    if len(scales) != 1:
        raise ValueError(f"Các ô trong một vùng phải cùng tỷ lệ: {sorted(scales)}.")
    if len(products) != 1:
        raise ValueError("Các ô trong một vùng phải cắt từ cùng một ảnh nguồn để ghép tọa độ.")
    s = scales.pop()
    if not 0 < d_min_m < d_max_m:
        raise ValueError("Cần 0 < d_min_m < d_max_m.")

    # Hợp vùng đếm trên hệ tọa độ nguồn.
    shifts = [_source_shift(c["metadata"]) for c in crops]
    gx0, gy0 = min(x for x, _ in shifts), min(y for _, y in shifts)
    gx1, gy1 = max(x for x, _ in shifts) + 512, max(y for _, y in shifts) + 512
    union = np.zeros((gy1 - gy0, gx1 - gx0), dtype=bool)
    for c, (x0, y0) in zip(crops, shifts):
        m = np.asarray(c["mask"], dtype=bool)
        if c.get("valid") is not None:
            m = m & np.asarray(c["valid"], dtype=bool)
        union[y0 - gy0:y0 - gy0 + 512, x0 - gx0:x0 - gx0 + 512] |= m

    # Hố trong dải D, tâm nằm trong vùng đếm của chính ô đó; gộp hố trùng giữa các ô chồng nhau.
    kept: list[dict] = []
    merged = 0
    for c, (x0, y0) in zip(crops, shifts):
        validate_crater_set(c["crater_set"], c["metadata"])
        m = np.asarray(c["mask"], dtype=bool)
        for cr in c["crater_set"]["circles"]:
            d = 2 * cr["r"] * s
            if not d_min_m <= d < d_max_m:
                continue
            ix, iy = int(round(cr["x"])), int(round(cr["y"]))
            if not (0 <= ix < 512 and 0 <= iy < 512 and m[iy, ix]):
                continue
            item = {"image_id": c["metadata"]["image_id"], "crater_id": cr["crater_id"],
                    "x_src": x0 + cr["x"], "y_src": y0 + cr["y"], "r_px": cr["r"], "d_m": d}
            dup = None
            for k in kept:
                R, rr = max(k["r_px"], item["r_px"]), min(k["r_px"], item["r_px"])
                if (math.hypot(k["x_src"] - item["x_src"], k["y_src"] - item["y_src"]) <= same_crater_center_frac * R
                        and rr / R >= same_crater_radius_ratio):
                    dup = k
                    break
            if dup is None:
                kept.append(item)
            else:
                merged += 1
                dup.setdefault("also_in", []).append(f"{item['image_id']}:{item['crater_id']}")

    area_px = int(union.sum())
    area_km2 = area_px * s * s / 1e6
    n = len(kept)
    lo, hi = poisson_interval(n)
    return {
        "product_id": next(iter(products)), "scale_m_per_px": s, "d_range_m": [d_min_m, d_max_m],
        "crops": [c["metadata"]["image_id"] for c in crops],
        "area_px": area_px, "area_km2": area_km2, "n": n, "merged_across_crops": merged,
        "density_per_km2": n / area_km2 if area_km2 else float("nan"),
        "density_ci95_per_km2": [lo / area_km2, hi / area_km2] if area_km2 else [float("nan")] * 2,
        "craters": kept,
    }


# ------------------------------------------------------------ phân bố kích thước
def sqrt2_bins(d_min_m: float, d_max_m: float) -> list[float]:
    """Biên bin √2 bắt đầu đúng tại d_min_m (dải đếm luôn khớp biên bin)."""
    edges = [d_min_m]
    while edges[-1] * math.sqrt(2) < d_max_m - 1e-9:
        edges.append(edges[-1] * math.sqrt(2))
    edges.append(d_max_m)
    return edges


def size_frequency(region: dict, edges: list[float] | None = None) -> dict:
    """Histogram theo bin √2 và tích lũy N(≥D)/km² tại các biên bin."""
    d0, d1 = region["d_range_m"]
    edges = edges or sqrt2_bins(d0, d1)
    ds = np.array([c["d_m"] for c in region["craters"]], dtype=float)
    counts = [int(((ds >= a) & (ds < b)).sum()) for a, b in zip(edges[:-1], edges[1:])]
    A = region["area_km2"]
    cumulative = []
    for e in edges[:-1]:
        k = int((ds >= e).sum())
        lo, hi = poisson_interval(k)
        cumulative.append({"d_m": e, "n": k, "per_km2": k / A, "ci95": [lo / A, hi / A]})
    return {"edges_m": edges, "counts": counts, "cumulative": cumulative}


# ------------------------------------------------------------ so hai vùng
def compare_regions(a: dict, b: dict) -> dict:
    """So mật độ hai vùng; từ chối nếu khác tỷ lệ hoặc khác dải D."""
    if a["scale_m_per_px"] != b["scale_m_per_px"]:
        raise ValueError("Hai vùng phải cùng tỷ lệ ảnh (m/px).")
    if list(a["d_range_m"]) != list(b["d_range_m"]):
        raise ValueError("Hai vùng phải cùng dải đường kính vật lý.")
    n1, n2, A1, A2 = a["n"], b["n"], a["area_km2"], b["area_km2"]
    p = binomial_two_sided_p(n1, n1 + n2, A1 / (A1 + A2))
    ratio = (n1 / A1) / (n2 / A2) if n2 and A2 else float("inf")
    return {"density_a": n1 / A1, "density_b": n2 / A2, "ratio_a_over_b": ratio,
            "binomial_p_two_sided": p, "n_total": n1 + n2,
            "area_fraction_a": A1 / (A1 + A2)}


def summarize(crater_set: dict, metadata: dict, valid_pixel_count: int) -> dict:
    """Thống kê một ô cho giao diện, theo hợp đồng docs/S2-13_TICH_HOP.md mục 1.

    count: số vòng trong crater_set; D = 2·r·scale (m); diện tích = valid_pixel_count·scale²/10⁶ (km²);
    histogram theo bin √2 bắt đầu tại D nhỏ nhất của dải tìm trong metadata (radius.d_min_m).
    Thêm (app bỏ qua): khoảng tin cậy 95 % của mật độ.
    """
    if isinstance(valid_pixel_count, bool) or not isinstance(valid_pixel_count, (int, np.integer)) or valid_pixel_count < 0:
        raise ValueError("valid_pixel_count phải là số nguyên ≥ 0.")
    s = float(metadata["scale_m_per_px"])
    radius = metadata.get("radius") or {}
    ds = sorted(2 * float(c["r"]) * s for c in crater_set["circles"])
    n = len(ds)
    area = int(valid_pixel_count) * s * s / 1e6
    d0 = float(radius.get("d_min_m") or (min(ds) if ds else 2 * s))
    d1 = float(radius.get("d_max_m") or (max(ds) if ds else 4 * s))
    d1 = max(d1, (max(ds) if ds else d1) * 1.0001)   # vòng đúng biên trên vẫn rơi vào bin cuối
    edges = sqrt2_bins(d0, d1)
    counts = [sum(1 for d in ds if a <= d < b) for a, b in zip(edges[:-1], edges[1:])]
    below = sum(1 for d in ds if d < d0)
    out = {"image_id": metadata.get("image_id"), "count": n,
           "valid_area_km2": area if area > 0 else None,
           "density_per_km2": n / area if area > 0 else None,
           "histogram": {"bin_edges_m": [round(e, 2) for e in edges], "counts": counts},
           "limitations": [
               "Đếm ứng viên máy chưa kiểm chứng trên một ô, không phải số hố thật; mật độ chỉ so được giữa "
               "các ảnh cùng tỷ lệ và cùng dải đường kính (xem docs/S2-09_MAT_DO_HO.md).",
               "Hough hiện chỉ trả vòng nhỏ (chạm trần 100 ứng viên), nên hố lớn bị thiếu.",
           ]}
    if below:
        out["limitations"].append(f"{below} vòng nhỏ hơn D tối thiểu {d0:g} m không nằm trong histogram.")
    if area > 0:
        lo, hi = poisson_interval(n)
        out["density_ci95_per_km2"] = [lo / area, hi / area]
    return out
