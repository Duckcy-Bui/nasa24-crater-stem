"""Tiến — S1-07. Phần chính Hough tròn phải tự cài bằng NumPy."""

from typing import Any


def detect_circles(edges: Any, r_min_px: int, r_max_px: int, params: dict, theta: Any = None) -> list[dict]:
    """Nhận biên bool 512×512; trả crater_id/x/y/r/confidence/votes.

    x là cột, y là hàng; bán kính theo pixel ảnh xử lý.
    Nếu chưa chuẩn hóa điểm tin cậy thì confidence = None; votes lưu số phiếu.
    Bộ gọi hàm bổ sung image_id, source='machine' và metadata khi lưu JSON.
    """
    raise NotImplementedError("S1-07: Tiến cài đặt tích lũy phiếu và chọn đỉnh.")
