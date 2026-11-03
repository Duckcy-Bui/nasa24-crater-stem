"""Tiến — S1-07. Phần chính Hough tròn phải tự cài bằng NumPy."""

from typing import Any
import numpy as np


DEFAULT_PARAMS = {
    "voting_method": "full_circle",
    "candidate_selection": "score",
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
    """Kiểm tra và ghép tham số Hough với cấu hình mặc định.

    Vào: params là dict Hough hoặc config có khóa ``hough``; bán kính/NMS
    tính bằng px, bước góc bằng độ, tỷ lệ phiếu không có đơn vị.
    Ra: dict mới với kiểu int/float chuẩn hóa; không sửa params, báo lỗi
    khi khóa, kiểu hoặc miền giá trị không hợp lệ. Tham chiếu: mục 3.3.
    """
    if not isinstance(params, dict):
        raise TypeError("params phai la dict.")

    supplied = params.get("hough", params)
    if not isinstance(supplied, dict):
        raise TypeError("params['hough'] phai la dict.")

    unknown = set(supplied) - set(DEFAULT_PARAMS)
    if unknown:
        raise ValueError(f"Tham so Hough khong ho tro: {sorted(unknown)}")

    config = {**DEFAULT_PARAMS, **supplied}

    if (
        not isinstance(config["voting_method"], str)
        or config["voting_method"] not in ("full_circle", "gradient")
    ):
        raise ValueError("voting_method phai la full_circle hoac gradient.")

    if config["candidate_selection"] not in ("score", "radius_balanced"):
        raise ValueError("candidate_selection phải là score hoặc radius_balanced.")

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
    """Tạo các độ lệch pixel duy nhất trên một đường tròn rời rạc.

    Vào: radius nguyên (px), angles là mảng góc 1 chiều (radian).
    Ra: mảng int32 cỡ (S, 2), mỗi hàng (dx, dy); mỗi độ lệch chỉ bỏ
    phiếu một lần dù nhiều góc trùng nhau. Tham chiếu: công thức (2.9).
    """
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
    """Cộng phiếu Hough toàn vòng theo từng lô điểm biên.

    Vào: ys/xs là mảng tọa độ nguyên (px), shape=(cao, rộng), offsets
    chứa (dx, dy) duy nhất; batch_size là số điểm biên mỗi lô.
    Ra: bảng phiếu int32 có shape đã cho; bỏ tâm ngoài ảnh, cộng đủ
    chỉ số trùng, không sửa đầu vào. Tham chiếu: (2.8)–(2.10), mục 3.3.
    """
    height, width = shape
    accumulator = np.zeros(height * width, dtype=np.int32)
    dx, dy = offsets.T

    for start in range(0, len(xs), batch_size):
        # a = x - r*cos(phi), b = y - r*sin(phi).
        center_x = xs[start:start + batch_size, None] - dx
        center_y = ys[start:start + batch_size, None] - dy

        inside = (
            (center_x >= 0) & (center_x < width)
            & (center_y >= 0) & (center_y < height)
        )

        # bincount cong ca cac chi so trung nhau nhu add.at, nhung nhanh hon.
        # Bo phieu theo lo de khong giu mang (so_diem_bien x so_goc) ca anh.
        indices = center_y[inside] * width + center_x[inside]
        # S2-01: row-ordered edge batches usually vote into a narrow strip.
        # Count only its flat-index interval, rather than allocating H*W bins
        # for every batch. The translation preserves every integer vote.
        if indices.size:
            first = int(indices.min())
            stop = int(indices.max()) + 1
            accumulator[first:stop] += np.bincount(
                indices - first, minlength=stop - first,
            ).astype(np.int32)

    return accumulator.reshape(shape)


def _accumulate_gradient(
    ys: np.ndarray,
    xs: np.ndarray,
    shape: tuple[int, int],
    theta: np.ndarray,
    radius: int,
) -> np.ndarray:
    """Bỏ phiếu tại hai tâm dọc theo pháp tuyến gradient của mỗi điểm biên.

    Vào: ys/xs là tọa độ nguyên (px), shape=(cao, rộng), radius tính bằng
    px; theta cùng cỡ ảnh, đơn vị radian, bằng atan2(gy, gx). Trục x sang
    phải, y xuống dưới; chưa biết hố sáng/tối nên cần cả hai đầu pháp tuyến.
    Ra: bảng phiếu int32 theo shape, bỏ tâm ngoài ảnh; không sửa đầu vào.
    Tham chiếu: công thức (2.11).
    """
    height, width = shape
    direction = theta[ys, xs]
    dx = np.rint(radius * np.cos(direction)).astype(np.int32)
    dy = np.rint(radius * np.sin(direction)).astype(np.int32)
    center_x = np.concatenate((xs - dx, xs + dx))
    center_y = np.concatenate((ys - dy, ys + dy))
    inside = (
        (center_x >= 0) & (center_x < width)
        & (center_y >= 0) & (center_y < height)
    )
    indices = center_y[inside] * width + center_x[inside]
    return np.bincount(indices, minlength=height * width).astype(
        np.int32,
    ).reshape(shape)


def _local_peaks(accumulator: np.ndarray, threshold: int) -> np.ndarray:
    """Lấy cực đại 3×3 đạt ngưỡng, hòa phiếu ưu tiên trên rồi trái.

    Vào: accumulator là mảng phiếu 2 chiều, threshold là số phiếu tối thiểu.
    Ra: mảng chỉ số nguyên (K, 2), mỗi hàng (y, x), có thể rỗng;
    không sửa bảng phiếu. Tham chiếu: ngưỡng (2.12), mục 2.2.2 và 3.3.
    """
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
    """Phát hiện vòng tròn bằng Hough NumPy, mặc định bỏ phiếu toàn vòng.

    Vào: edges là mảng bool 512×512; r_min_px/r_max_px là cận bán kính
    nguyên (px), params là cấu hình Hough. Nhánh gradient cần theta cùng
    cỡ ảnh, hữu hạn tại biên, đơn vị radian; nhánh toàn vòng không cần theta.
    Ra: list dict có crater_id, x/y/r (px), votes và confidence=None;
    không sửa đầu vào, báo ValueError khi vi phạm hợp đồng. Chỉ giữ tâm
    trong ảnh nhưng vành được cắt qua mép. Phiếu chưa được hiệu chuẩn thành
    xác suất; giới hạn max_circles có thể làm mất ứng viên hợp lệ.
    Tham chiếu: công thức (2.8)–(2.13), Thuật toán 3.3.
    """
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

    theta_array = None
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

    if config["voting_method"] == "gradient" and theta_array is None:
        raise ValueError("Bo phieu gradient can theta (radian) tai diem bien.")

    ys, xs = np.nonzero(edges)
    ys, xs = ys.astype(np.int32), xs.astype(np.int32)
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
        if config["voting_method"] == "gradient":
            # Gradient bo phieu tu moi pixel bien, khong tu mau goc 1 do.
            # Uoc luong so pixel tren duong tron bang chu vi (2*pi*r),
            # tranh uu tien r lon chi vi mau goc full_circle bi gioi han.
            support_size = int(np.ceil(2 * np.pi * radius))
            accumulator = _accumulate_gradient(
                ys, xs, edges.shape, theta_array, radius,
            )
        else:
            offsets = _circle_offsets(radius, angles)
            support_size = len(offsets)
            accumulator = _accumulate(
                ys,
                xs,
                edges.shape,
                offsets,
                config["edge_batch_size"],
            )

        threshold = max(
            config["min_votes"],
            int(np.ceil(config["min_vote_ratio"] * support_size)),
        )

        for y, x in _local_peaks(accumulator, threshold):
            votes = int(accumulator[y, x])
            score = votes / support_size

            candidates.append(
                (score, votes, int(y), int(x), radius)
            )

    # Ti le phieu giam thien vi ban kinh lon; khong phai xac suat dung.
    candidates.sort(
        key=lambda c: (-c[0], -c[1], c[2], c[3], c[4])
    )

    if config["candidate_selection"] == "radius_balanced":
        # Equal turns across octave bands prevent small-radius texture peaks
        # from consuming the entire output budget. Within a band keep score order.
        from collections import deque
        bands = {}
        for candidate in candidates:
            band = int(np.floor(np.log2(candidate[4] / 5)))
            bands.setdefault(band, deque()).append(candidate)
        queues = [bands[k] for k in sorted(bands)]
        candidates = []
        while queues:
            candidates.extend(queue.popleft() for queue in queues)
            queues = [queue for queue in queues if queue]

    selected = []
    # Any two centres in this image are closer than height + width.
    # Capping before squaring preserves NMS decisions for enormous finite radii.
    distance_squared = min(config["nms_center_px"], float(sum(edges.shape))) ** 2

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
