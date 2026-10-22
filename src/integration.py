"""Đức — S2-13: ghép thống kê (S2-09) và thẻ khoa học (S2-10) vào giao diện.

Hai hàm dưới đây gọi đúng API đã thống nhất (statistics.summarize,
science_cards.cards_for_image) và luôn trả một trạng thái hiển thị được:
- "pending": phần của bạn khác chưa cài (NotImplementedError);
- "ok": dữ liệu đúng hợp đồng trong docs/S2-13_TICH_HOP.md;
- "error": có dữ liệu nhưng sai hợp đồng hoặc lỗi khi chạy; ghi lý do, không đoán.
Giao diện không tự tính thống kê hay tự tạo thẻ thay cho S2-09/S2-10.
"""
from __future__ import annotations

import math
from typing import Any
from urllib.parse import urlparse

from src import science_cards, statistics

CARD_FIELDS = ("card_id", "title", "body", "source_title", "source_url")


def _finite(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _check_statistics(data: Any) -> str | None:
    if not isinstance(data, dict):
        return "summarize phải trả dict."
    count = data.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return "Thiếu count (số nguyên ≥ 0)."
    for key in ("valid_area_km2", "density_per_km2"):
        if data.get(key) is not None and (not _finite(data[key]) or data[key] < 0):
            return f"{key} phải là số ≥ 0 hoặc null."
    histogram = data.get("histogram")
    if histogram is not None:
        edges, counts = (histogram or {}).get("bin_edges_m"), (histogram or {}).get("counts")
        if (not isinstance(edges, list) or not isinstance(counts, list) or len(edges) != len(counts) + 1
                or not all(_finite(e) for e in edges) or any(b <= a for a, b in zip(edges, edges[1:]))
                or not all(isinstance(c, int) and not isinstance(c, bool) and c >= 0 for c in counts)):
            return "histogram cần bin_edges_m tăng dần (n + 1 số) và counts (n số nguyên ≥ 0)."
    return None


def statistics_view(machine: dict[str, Any], metadata: dict[str, Any], valid_pixel_count: int) -> dict[str, Any]:
    """Thống kê ứng viên máy trên ảnh đang mở, theo hợp đồng S2-09."""
    try:
        data = statistics.summarize(machine, metadata, valid_pixel_count)
    except NotImplementedError:
        return {"status": "pending", "reason": "Thống kê (S2-09, Hưng) chưa được cài trên main."}
    except (ValueError, TypeError, KeyError) as error:
        return {"status": "error", "reason": f"summarize báo lỗi: {error}"}
    problem = _check_statistics(data)
    if problem:
        return {"status": "error", "reason": f"Kết quả thống kê sai hợp đồng: {problem}"}
    return {"status": "ok", "data": data}


def _check_card(card: Any) -> str | None:
    if not isinstance(card, dict):
        return "thẻ phải là object"
    missing = [key for key in CARD_FIELDS if not isinstance(card.get(key), str) or not card[key].strip()]
    if missing:
        return "thiếu " + ", ".join(missing)
    if urlparse(card["source_url"]).scheme not in ("http", "https"):
        return "source_url phải là link http(s)"
    position = card.get("position")
    if position is not None:
        if not isinstance(position, dict) or not all(_finite(position.get(k)) for k in ("x", "y")):
            return "position cần x, y là số"
        if not (0 <= position["x"] <= 511 and 0 <= position["y"] <= 511):
            return "position nằm ngoài ảnh 512×512"
    return None


def cards_view(image_id: str) -> dict[str, Any]:
    """Thẻ khoa học của ảnh đang mở; thẻ thiếu nguồn hoặc sai vị trí bị loại kèm lý do."""
    try:
        cards = science_cards.cards_for_image(image_id)
    except NotImplementedError:
        return {"status": "pending", "reason": "Thẻ khoa học (S2-10, Quốc Anh) chưa được cài trên main."}
    except (ValueError, TypeError, KeyError, OSError) as error:
        return {"status": "error", "reason": f"cards_for_image báo lỗi: {error}"}
    if not isinstance(cards, list):
        return {"status": "error", "reason": "cards_for_image phải trả list."}
    shown, rejected = [], []
    for index, card in enumerate(cards, 1):
        problem = _check_card(card)
        if problem:
            ident = card.get("card_id") if isinstance(card, dict) and card.get("card_id") else f"#{index}"
            rejected.append(f"{ident}: {problem}")
        else:
            shown.append(card)
    return {"status": "ok", "cards": shown, "rejected": rejected}
