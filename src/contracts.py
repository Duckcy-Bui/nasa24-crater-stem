"""Hợp đồng dữ liệu giữa tiền xử lý, Hough, thống kê và game (S1-05).

Không phát hiện hố hoặc chấm điểm. Các kiểm tra này chỉ xác nhận định dạng,
hệ tọa độ và sự nhất quán theo S1-04.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Dữ liệu đầu vào không khớp chuẩn đã thống nhất."""


def _number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{name} phải là số.")
    if not math.isfinite(value) or (positive and value <= 0):
        raise ContractError(f"{name} phải hữu hạn" + (" và > 0." if positive else "."))
    return float(value)


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{name} phải là số nguyên >= {minimum}.")
    return value


def _required(data: dict[str, Any], names: tuple[str, ...]) -> None:
    missing = [name for name in names if name not in data]
    if missing:
        raise ContractError("Thiếu trường: " + ", ".join(missing))


def _image_id(value: Any) -> str:
    if not isinstance(value, str) or not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in value):
        raise ContractError("image_id dùng chữ, số, dấu _ hoặc -; không chứa đường dẫn.")
    return value


def radius_range_px(d_min_m: float, d_max_m: float, scale_m_per_px: float) -> tuple[int, int]:
    """Quy đổi đường kính mét sang bán kính pixel theo S1-04."""
    lo = _number(d_min_m, "d_min_m", positive=True)
    hi = _number(d_max_m, "d_max_m", positive=True)
    scale = _number(scale_m_per_px, "scale_m_per_px", positive=True)
    if lo > hi:
        raise ContractError("d_min_m không được lớn hơn d_max_m.")
    r_min = max(5, math.ceil(lo / (2 * scale)))
    r_max = min(128, math.floor(hi / (2 * scale)))
    if r_min > r_max:
        raise ContractError("Ảnh không phù hợp với khoảng đường kính cần tìm.")
    return r_min, r_max


def validate_metadata(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ContractError("Metadata phải là object JSON.")
    _required(data, ("schema_version", "data_kind", "image_id", "source_stt", "product_id", "body", "crop_x0", "crop_y0", "downsample_k", "width", "height", "scale_m_per_px", "center_lat", "center_lon", "north_up", "north_angle_deg", "sun", "radius", "valid_ratio", "preprocess"))
    _image_id(data["image_id"])
    if data["schema_version"] != "1.0" or data["data_kind"] not in ("synthetic", "real"):
        raise ContractError("Phiên bản hoặc loại dữ liệu không hợp lệ.")
    if data["body"] not in ("moon", "mars"):
        raise ContractError("body phải là moon hoặc mars.")
    if _integer(data["width"], "width", 1) != 512 or _integer(data["height"], "height", 1) != 512:
        raise ContractError("Ảnh xử lý phải có kích thước 512×512 theo S1-04.")
    _integer(data["crop_x0"], "crop_x0")
    _integer(data["crop_y0"], "crop_y0")
    _integer(data["downsample_k"], "downsample_k", 1)
    scale = _number(data["scale_m_per_px"], "scale_m_per_px", positive=True)
    if not 0 <= _number(data["valid_ratio"], "valid_ratio") <= 1:
        raise ContractError("valid_ratio phải nằm trong [0, 1].")
    if data["source_stt"] is not None:
        _integer(data["source_stt"], "source_stt", 1)
    if data["product_id"] is not None and (not isinstance(data["product_id"], str) or not data["product_id"]):
        raise ContractError("product_id phải là chuỗi hoặc null.")
    if data["data_kind"] == "real" and (data["source_stt"] is None or data["product_id"] is None):
        raise ContractError("Ảnh thật cần source_stt và product_id để truy xuất nguồn.")
    for key, low, high in (("center_lat", -90, 90), ("center_lon", -180, 360), ("north_angle_deg", 0, 360)):
        if data[key] is not None and not low <= _number(data[key], key) <= high:
            raise ContractError(f"{key} nằm ngoài khoảng hợp lệ.")
    if data["north_up"] is not None and not isinstance(data["north_up"], bool):
        raise ContractError("north_up phải là bool hoặc null.")
    if data["north_up"] is True and data["north_angle_deg"] != 0:
        raise ContractError("Ảnh Bắc lên trên phải có north_angle_deg = 0.")
    sun = data["sun"]
    if not isinstance(sun, dict):
        raise ContractError("sun phải là object.")
    _required(sun, ("azimuth_deg", "incidence_deg", "quality", "source"))
    if sun["quality"] not in ("measured", "side_only", "none"):
        raise ContractError("sun.quality không hợp lệ.")
    if not isinstance(sun["source"], str) or not sun["source"].strip():
        raise ContractError("sun.source cần ghi nguồn hoặc lý do thiếu dữ liệu.")
    if sun["quality"] == "none" and sun["azimuth_deg"] is not None:
        raise ContractError("Không có hướng nắng thì azimuth_deg phải là null.")
    if sun["quality"] != "none" and sun["azimuth_deg"] is None:
        raise ContractError("measured/side_only cần azimuth_deg.")
    for key, high in (("azimuth_deg", 360), ("incidence_deg", 90)):
        if sun[key] is not None and not 0 <= _number(sun[key], "sun." + key) <= high:
            raise ContractError("Góc nắng nằm ngoài khoảng hợp lệ.")
    radius = data["radius"]
    if not isinstance(radius, dict):
        raise ContractError("radius phải là object.")
    _required(radius, ("d_min_m", "d_max_m", "r_min_px", "r_max_px"))
    actual = (_integer(radius["r_min_px"], "r_min_px", 1), _integer(radius["r_max_px"], "r_max_px", 1))
    expected = radius_range_px(radius["d_min_m"], radius["d_max_m"], scale)
    if actual != expected:
        raise ContractError(f"Bán kính phải được tính từ mét và tỷ lệ ảnh: {expected}.")
    if not isinstance(data["preprocess"], dict) or not data["preprocess"].get("version"):
        raise ContractError("preprocess cần tham số và version mã chạy.")


def validate_crater_set(data: dict[str, Any], metadata: dict[str, Any]) -> None:
    validate_metadata(metadata)
    if not isinstance(data, dict):
        raise ContractError("Danh sách hố phải là object JSON.")
    _required(data, ("schema_version", "data_kind", "image_id", "source", "reference_source", "circles"))
    if data["schema_version"] != "1.0":
        raise ContractError("schema_version không được hỗ trợ.")
    if _image_id(data["image_id"]) != metadata["image_id"] or data["data_kind"] != metadata["data_kind"]:
        raise ContractError("Danh sách hố và metadata phải cùng image_id và data_kind.")
    if data["source"] not in ("machine", "catalogue", "player"):
        raise ContractError("source phải là machine, catalogue hoặc player.")
    if data["source"] == "catalogue" and (not isinstance(data["reference_source"], str) or not data["reference_source"].strip()):
        raise ContractError("Danh mục cần reference_source.")
    if not isinstance(data["circles"], list):
        raise ContractError("circles phải là danh sách.")
    seen = set()
    for circle in data["circles"]:
        if not isinstance(circle, dict):
            raise ContractError("Mỗi hố phải là object.")
        _required(circle, ("crater_id", "x", "y", "r", "confidence", "votes"))
        ident = circle["crater_id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ContractError("crater_id phải là chuỗi duy nhất trong danh sách.")
        seen.add(ident)
        x, y = _number(circle["x"], "x"), _number(circle["y"], "y")
        if not 0 <= x <= 511 or not 0 <= y <= 511:
            raise ContractError("Tâm hố nằm ngoài ảnh 512×512.")
        _number(circle["r"], "r", positive=True)
        if circle["confidence"] is not None and not 0 <= _number(circle["confidence"], "confidence") <= 1:
            raise ContractError("confidence phải nằm trong [0, 1] hoặc null.")
        if circle["votes"] is not None:
            _integer(circle["votes"], "votes")


def source_coordinates(x: float, y: float, r: float, metadata: dict[str, Any]) -> tuple[float, float, float]:
    """Đổi từ ảnh xử lý về ảnh nguồn, bao gồm độ lệch tâm khối thu nhỏ."""
    validate_metadata(metadata)
    x, y, r = _number(x, "x"), _number(y, "y"), _number(r, "r", positive=True)
    if not 0 <= x <= 511 or not 0 <= y <= 511:
        raise ContractError("Tọa độ phải nằm trong ảnh xử lý.")
    k = metadata["downsample_k"]
    return (metadata["crop_x0"] + k * x + (k - 1) / 2,
            metadata["crop_y0"] + k * y + (k - 1) / 2, k * r)


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def save_run(output_root: str | Path, run_id: str, *, metadata: dict[str, Any], crater_set: dict[str, Any], params: dict[str, Any], code_version: str) -> Path:
    """Lưu một lần chạy riêng; không ghi đè lần chạy đã có."""
    _image_id(run_id)
    validate_crater_set(crater_set, metadata)
    if not isinstance(params, dict) or not isinstance(code_version, str) or not code_version.strip():
        raise ContractError("Cần params và mã phiên bản để tái tạo.")
    records = {
        "metadata.json": metadata,
        "params.json": params,
        "craters.json": crater_set,
        "run.json": {"run_id": run_id, "image_id": metadata["image_id"], "data_kind": metadata["data_kind"], "code_version": code_version, "created_at_utc": datetime.now(timezone.utc).isoformat()}
    }
    # Kiểm tra JSON trước khi tạo thư mục để không để lại kết quả dở dang.
    serialized = {name: json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n" for name, value in records.items()}
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    for name, value in serialized.items():
        (directory / name).write_text(value, encoding="utf-8")
    return directory
