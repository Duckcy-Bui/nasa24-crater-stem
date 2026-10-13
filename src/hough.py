"""Tiến — S1-07. Phần chính Hough tròn phải tự cài bằng NumPy."""

from typing import Any
import numpy as np


DEFAULT_PARAMS = {
    "radius_step_px": 1,
    "r_min_limit_px": 5,
    "r_max_limit_px": 128,
    "angle_step_deg": 1.0,
    "min_votes": 12,
    "min_vote_ratio": 0.35,
    "nms_center_px": 4.0,
    "nms_radius_px": 2,
    "max_circles": 100,
    "edge_batch_size": 256,
}


def resolve_hough_params(params: dict) -> dict:
    """Nhan rieng dict Hough hoac toan bo config co khoa 'hough'."""
    if not isinstance(params, dict):
        raise TypeError("params phai la dict.")

    supplied = params.get("hough", params)
    if not isinstance(supplied, dict):
        raise TypeError("params['hough'] phai la dict.")

    unknown = set(supplied) - set(DEFAULT_PARAMS)
    if unknown:
        raise ValueError(f"Tham so Hough khong ho tro: {sorted(unknown)}")

    config = {**DEFAULT_PARAMS, **supplied}

    for name in (
        "radius_step_px", "r_min_limit_px", "r_max_limit_px",
        "min_votes", "nms_radius_px", "max_circles", "edge_batch_size",
    ):
        value = config[name]
        minimum = 0 if name == "nms_radius_px" else 1

        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer))
            or value < minimum
        ):
            raise ValueError(f"{name} phai la so nguyen >= {minimum}.")

        config[name] = int(value)

    for name in ("angle_step_deg", "min_vote_ratio", "nms_center_px"):
        value = config[name]

        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, float, np.integer, np.floating))
            or not np.isfinite(value)
        ):
            raise ValueError(f"{name} phai la so huu han.")

        config[name] = float(value)

    if not 0.1 <= config["angle_step_deg"] <= 10.0:
        raise ValueError("angle_step_deg phai trong [0.1, 10].")

    if not 0 <= config["min_vote_ratio"] <= 1:
        raise ValueError("min_vote_ratio phai trong [0, 1].")

    if config["nms_center_px"] < 0:
        raise ValueError("nms_center_px phai >= 0.")

    if not 5 <= config["r_min_limit_px"] <= config["r_max_limit_px"] <= 128:
        raise ValueError("Gioi han ban kinh phai nam trong [5, 128].")

    return config


def _circle_offsets(radius: int, angles: np.ndarray) -> np.ndarray:
    """Moi do lech pixel chi bo phieu mot lan, du nhieu goc trung nhau."""
    offsets = np.column_stack((
        np.rint(radius * np.cos(angles)),
        np.rint(radius * np.sin(angles)),
    )).astype(np.int32)

    return np.unique(offsets, axis=0)  # cot dx, dy


def _accumulate(
    ys: np.ndarray,
    xs: np.ndarray,
    shape: tuple[int, int],
    offsets: np.ndarray,
    batch_size: int,
) -> np.ndarray:
    height, width = shape
    accumulator = np.zeros(shape, dtype=np.int32)
    dx, dy = offsets.T

    for start in range(0, len(xs), batch_size):
        # a = x - r*cos(phi), b = y - r*sin(phi).
        center_x = xs[start:start + batch_size, None] - dx
        center_y = ys[start:start + batch_size, None] - dy

        inside = (
            (center_x >= 0) & (center_x < width)
            & (center_y >= 0) & (center_y < height)
        )

        # add.at cong dung ca khi nhieu phieu cung tro den mot o.
        np.add.at(accumulator, (center_y[inside], center_x[inside]), 1)

    return accumulator


def _local_peaks(accumulator: np.ndarray, threshold: int) -> np.ndarray:
    """Cuc dai 3x3; hoa phieu thi uu tien o tren, roi o ben trai."""
    height, width = accumulator.shape
    padded = np.pad(accumulator, 1, constant_values=-1)
    keep = accumulator >= threshold

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue

            neighbor = padded[
                1 + dy:1 + dy + height,
                1 + dx:1 + dx + width,
            ]

            if dy < 0 or (dy == 0 and dx < 0):
                keep &= accumulator > neighbor
            else:
                keep &= accumulator >= neighbor

    return np.argwhere(keep)  # hang y, cot x


def detect_circles(
    edges: Any,
    r_min_px: int,
    r_max_px: int,
    params: dict,
    theta: Any = None,
) -> list[dict]:
    
    edges = np.asarray(edges)

    if edges.shape != (512, 512) or edges.dtype != np.bool_:
        raise ValueError(
            "edges phai la mang bool co kich thuoc (512, 512)."
        )

    config = resolve_hough_params(params)

    for name, value in (("r_min_px", r_min_px), ("r_max_px", r_max_px)):
        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer))
        ):
            raise ValueError(f"{name} phai la so nguyen.")

    if not (
        config["r_min_limit_px"] <= r_min_px <= r_max_px
        <= config["r_max_limit_px"]
    ):
        raise ValueError(
            "Dai ban kinh rong hoac ngoai gioi han cau hinh."
        )

    if theta is not None:
        theta_array = np.asarray(theta)

        if (
            theta_array.shape != edges.shape
            or theta_array.dtype.kind not in "fiu"
            or not np.isfinite(theta_array[edges]).all()
        ):
            raise ValueError(
                "theta phai cung kich thuoc, huu han tai diem bien."
            )

    ys, xs = np.nonzero(edges)
    if len(xs) == 0:
        return []

    angles = np.deg2rad(
        np.arange(0.0, 360.0, config["angle_step_deg"])
    )

    # Chi luu cac dinh, khong giu toan bo accumulator 3 chieu.
    candidates = []

    for radius in range(
        int(r_min_px),
        int(r_max_px) + 1,
        config["radius_step_px"],
    ):
        offsets = _circle_offsets(radius, angles)

        accumulator = _accumulate(
            ys,
            xs,
            edges.shape,
            offsets,
            config["edge_batch_size"],
        )

        threshold = max(
            config["min_votes"],
            int(np.ceil(config["min_vote_ratio"] * len(offsets))),
        )

        for y, x in _local_peaks(accumulator, threshold):
            votes = int(accumulator[y, x])
            score = votes / len(offsets)

            candidates.append(
                (score, votes, int(y), int(x), radius)
            )

    # Ti le phieu giam thien vi ban kinh lon; khong phai xac suat dung.
    candidates.sort(
        key=lambda c: (-c[0], -c[1], c[2], c[3], c[4])
    )

    selected = []
    distance_squared = config["nms_center_px"] ** 2

    for candidate in candidates:
        _, _, y, x, radius = candidate

        duplicate_peak = any(
            (x - old[3]) ** 2 + (y - old[2]) ** 2 <= distance_squared
            and abs(radius - old[4]) <= config["nms_radius_px"]
            for old in selected
        )

        if not duplicate_peak:
            selected.append(candidate)

            if len(selected) >= config["max_circles"]:
                break

    return [
        {
            "crater_id": f"M{index}",
            "x": float(x),
            "y": float(y),
            "r": float(radius),
            "confidence": None,
            "votes": int(votes),
        }
        for index, (_, votes, y, x, radius)
        in enumerate(selected, start=1)
    ]
