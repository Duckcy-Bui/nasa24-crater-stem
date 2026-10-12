"""Hưng — S1-08. Chuỗi B0–B8 theo đặc tả S1-04."""

from typing import Any


def preprocess(image: Any, metadata: dict, params: dict) -> dict:
    """Trả gray/enhanced/smooth/gx/gy/mag/theta/edges/valid_mask/params.

    gray và các ảnh trung gian: float32 512×512; edges/valid_mask: bool.
    NumPy: thu nhỏ, ảnh xám, chuẩn hóa, Gaussian, Sobel, mặt nạ.
    Thư viện theo S1-04: đọc ảnh, CLAHE và Canny.
    """
    raise NotImplementedError("S1-08: Hưng cài đặt chuỗi tiền xử lý.")
