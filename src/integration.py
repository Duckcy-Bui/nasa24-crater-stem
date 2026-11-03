"""Đức — S2-13: ghép thống kê (S2-09) và thẻ khoa học (S2-10) vào giao diện.

Các hàm dưới đây gọi đúng API đã thống nhất (statistics.summarize,
science_cards.cards_for_image) và luôn trả một trạng thái hiển thị được:
- "pending": phần của bạn khác chưa cài (NotImplementedError);
- "ok": dữ liệu đúng hợp đồng trong docs/S2-13_TICH_HOP.md;
- "error": có dữ liệu nhưng sai hợp đồng hoặc lỗi khi chạy; ghi lý do, không đoán.
Giao diện không tự tính thống kê hay tự tạo thẻ thay cho S2-09/S2-10.
So sánh hai vùng đọc bằng chứng đếm tay S2-09, tách khỏi ứng viên máy.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src import science_cards, statistics

CARD_FIELDS = ("card_id", "title", "body", "source_title", "source_url")
ROOT = Path(__file__).resolve().parents[1]
COMPARISON_PATH = ROOT / "docs" / "evidence" / "s2-09" / "so_sanh.json"
REGIONS_PATH = ROOT / "data" / "s209_counts" / "regions.json"
LEGACY_HOUGH_LIMITATION = (
    "Hough hiện chỉ trả vòng nhỏ (chạm trần 100 ứng viên), nên hố lớn bị thiếu."
)


def _finite(value: Any) -> bool:
    """Nhận value (giá trị bất kỳ); trả bool đúng với int/float hữu hạn, trừ bool."""
    try:
        return (
            not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value)
        )
    except OverflowError:
        return False


def _check_statistics(data: Any) -> str | None:
    """Kiểm data theo các trường thống kê ở mục 3.6 báo cáo.

    Nhận data bất kỳ; trả str lý do khi một kiểm tra thất bại, hoặc None
    khi các kiểm tra hiện có đều qua. Nếu có histogram, người gọi cần
    truyền dict hoặc None; kiểu khác chưa được chặn đầy đủ và có thể
    phát sinh AttributeError thay vì chuỗi lý do.
    """
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
        if (
            not isinstance(edges, list) or not isinstance(counts, list)
            or len(edges) != len(counts) + 1 or not all(_finite(e) for e in edges)
            or any(b <= a for a, b in zip(edges, edges[1:]))
            or not all(isinstance(c, int) and not isinstance(c, bool) and c >= 0 for c in counts)
        ):
            return "histogram cần bin_edges_m tăng dần (n + 1 số) và counts (n số nguyên ≥ 0)."
    return None


def statistics_view(
    machine: dict[str, Any], metadata: dict[str, Any], valid_pixel_count: int,
) -> dict[str, Any]:
    """Đọc thống kê và chuyển lỗi thành trạng thái cho giao diện.

    Vào: machine (dict vòng px), metadata (dict tỷ lệ m/px và dải D),
    valid_pixel_count (int số pixel hợp lệ). Ra: dict status ok kèm data,
    pending khi chưa cài hoặc error kèm reason; không sửa dữ liệu vào.
    Tham chiếu: báo cáo mục 3.6, diện tích/mật độ theo (2.24)."""
    try:
        data = statistics.summarize(machine, metadata, valid_pixel_count)
    except NotImplementedError:
        return {"status": "pending", "reason": "Thống kê (S2-09, Hưng) chưa được cài trên main."}
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        return {"status": "error", "reason": f"summarize báo lỗi: {error}"}
    problem = _check_statistics(data)
    if problem:
        return {"status": "error", "reason": f"Kết quả thống kê sai hợp đồng: {problem}"}
    return {"status": "ok", "data": data}


def density_limit_view(raw_count: int, max_circles: int) -> dict[str, Any]:
    """Xác định ứng viên thô đã chạm trần Hough hay chưa.

    Vào: raw_count và max_circles (int số vòng, trần vòng). Ra: dict limited (bool)
    và reason (str hoặc None); dùng số thô trước khi lọc bớt vòng.
    Tham chiếu: báo cáo mục 3.6 về ẩn mật độ khi chạm trần."""
    limited = raw_count >= max_circles
    reason = (
        f"Máy đã chạm giới hạn max_circles = {max_circles} ứng viên thô. "
        "Mật độ bị chặn bởi giới hạn ứng viên; không dùng để so tuổi hay so vùng. "
        "Hãy mở ảnh Lunokhod 1 hoặc Mare Frigoris để xem so sánh đếm tay hai vùng."
    ) if limited else None
    return {"limited": limited, "reason": reason}


def statistics_presentation_view(
    data: dict[str, Any], raw_count: int, max_circles: int,
) -> dict[str, Any]:
    """Chuẩn bị caption và cảnh báo chạm trần để hiển thị thống kê.

    Vào: data (dict từ summarize), raw_count/max_circles (int số vòng/trần).
    Ra: dict limited, reason, captions; thay đúng caption chạm trần cũ bằng
    cảnh báo có điều kiện, giữ các limitation khác và không sửa dict/list đầu vào.
    Tham chiếu: báo cáo mục 3.6."""
    limit = density_limit_view(raw_count, max_circles)
    captions = [str(note) for note in data.get("limitations") or []
                if str(note).strip() != LEGACY_HOUGH_LIMITATION]
    return {**limit, "captions": captions}


def _check_comparison(data: Any, definitions: Any) -> None:
    """Kiểm bằng chứng mật độ so với định nghĩa vùng đếm.

    Vào: data (dict số hố, diện tích km², mật độ hố/km², CI và tỷ số/p-value),
    definitions (dict vùng, ô cắt, dải D m). Ra: None nếu khớp; phát sinh lỗi
    khi sai schema, đơn vị, cặp vùng hoặc quan hệ mật độ/tỷ số.
    Tham chiếu: báo cáo mục 3.6 và 4.8, công thức (2.24)."""
    d_range = data["d_range_m"]
    if (not isinstance(d_range, list) or len(d_range) != 2 or not all(_finite(d) for d in d_range)
            or not 0 < d_range[0] < d_range[1] or d_range != definitions["d_range_m"]):
        raise ValueError("Dải đường kính không hợp lệ hoặc không khớp vùng đếm.")
    regions = data["regions"]
    scales = []
    for key in ("lunokhod1", "marefrig"):
        region = regions[key]
        if not isinstance(region["name"], str) or not region["name"].strip():
            raise ValueError("Thiếu tên vùng.")
        if isinstance(region["n"], bool) or not isinstance(region["n"], int) or region["n"] < 0:
            raise ValueError("Số hố phải là số nguyên không âm.")
        for field in ("area_km2", "scale_m_per_px", "density_per_km2"):
            if not _finite(region[field]) or region[field] < 0:
                raise ValueError(f"{field} không hợp lệ.")
        if region["area_km2"] <= 0 or region["scale_m_per_px"] <= 0:
            raise ValueError("Diện tích và tỷ lệ ảnh phải dương.")
        if not math.isclose(
            region["density_per_km2"], region["n"] / region["area_km2"], rel_tol=1e-9,
        ):
            raise ValueError("Mật độ không khớp số hố và diện tích.")
        ci = region["density_ci95_per_km2"]
        if (not isinstance(ci, list) or len(ci) != 2 or not all(_finite(v) for v in ci)
                or not 0 <= ci[0] <= region["density_per_km2"] <= ci[1]):
            raise ValueError("Khoảng tin cậy không hợp lệ.")
        crops = region["crops"]
        if (
            not isinstance(crops, list) or not crops or not all(isinstance(c, str) for c in crops)
            or len(set(crops)) != len(crops)
            or set(crops) != set(definitions["regions"][key]["crops"])
            or region["d_range_m"] != d_range
            or not isinstance(region["product_id"], str) or not region["product_id"]
        ):
            raise ValueError("Ảnh nguồn, ô cắt hoặc dải đường kính không khớp vùng đếm.")
        scales.append(region["scale_m_per_px"])
    if (
        scales[0] != scales[1]
        or regions["lunokhod1"]["product_id"] == regions["marefrig"]["product_id"]
    ):
        raise ValueError("Hai vùng phải cùng tỷ lệ và khác ảnh nguồn.")
    comparison = data["comparison_lunokhod1_over_marefrig"]
    a, b = (regions[key]["density_per_km2"] for key in ("lunokhod1", "marefrig"))
    ratio, p = comparison["ratio_a_over_b"], comparison["binomial_p_two_sided"]
    if (not _finite(ratio) or b <= 0 or not math.isclose(ratio, a / b, rel_tol=1e-9)
            or not _finite(p) or not 0 <= p <= 1):
        raise ValueError("Tỷ lệ mật độ hoặc p-value không hợp lệ.")


def density_comparison_view(metadata: dict[str, Any], *, comparison_path: Path = COMPARISON_PATH,
                            regions_path: Path = REGIONS_PATH) -> dict[str, Any]:
    """Nạp bằng chứng đếm tay phù hợp với metadata ảnh.

    Vào: metadata (dict image_id/product_id/body/scale_m_per_px), comparison_path
    và regions_path (Path đến JSON số liệu và định nghĩa vùng). Ra: dict status
    ok kèm data/vùng/cờ ô đã đếm, hidden ngoài vùng, hoặc error kèm reason.
    Nhận vùng theo product_id và ô cắt, không đoán theo tên file.
    Tham chiếu: báo cáo mục 3.6 và 4.8."""
    try:
        data = json.loads(comparison_path.read_text(encoding="utf-8"))
        definitions = json.loads(regions_path.read_text(encoding="utf-8"))
        _check_comparison(data, definitions)
        matches = [key for key in ("lunokhod1", "marefrig")
                   if metadata.get("product_id") == data["regions"][key]["product_id"]]
        counted_in = [key for key in ("lunokhod1", "marefrig")
                      if metadata.get("image_id") in definitions["regions"][key]["crops"]]
        if counted_in and counted_in != matches:
            raise ValueError("Metadata ảnh không khớp ảnh nguồn của vùng đếm.")
        if not matches:
            return {"status": "hidden"}
        key = matches[0]
        region = data["regions"][key]
        if (
            metadata.get("body") != "moon"
            or metadata.get("scale_m_per_px") != region["scale_m_per_px"]
        ):
            raise ValueError("Thiên thể hoặc tỷ lệ metadata không khớp vùng đếm.")
        return {"status": "ok", "data": data, "region": key, "counted_crop": bool(counted_in)}
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        return {"status": "error", "reason": f"Chưa đọc được so sánh đếm tay hai vùng: {error}"}


def _check_card(card: Any) -> str | None:
    """Nhận card (bất kỳ); kiểm nội dung, nguồn http(s) và vị trí px trên ảnh.

    Trả str lý do cho các lỗi đã kiểm hoặc None khi các kiểm tra đều qua,
    theo mục 3.7 báo cáo. URL phải phân tích được bằng urlparse;
    ValueError từ bộ phân tích URL được truyền ra, không đổi thành chuỗi.
    """
    if not isinstance(card, dict):
        return "thẻ phải là object"
    missing = [
        key for key in CARD_FIELDS if not isinstance(card.get(key), str) or not card[key].strip()
    ]
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
    """Lấy thẻ khoa học và tách riêng thẻ không hợp lệ.

    Vào: image_id (str). Ra: dict status ok kèm cards/rejected, pending nếu chưa
    cài hoặc error kèm reason; loại thẻ thiếu nguồn hay sai vị trí với lý do.
    Tham chiếu: báo cáo mục 3.7."""
    try:
        cards = science_cards.cards_for_image(image_id)
    except NotImplementedError:
        return {
            "status": "pending",
            "reason": "Thẻ khoa học (S2-10, Quốc Anh) chưa được cài trên main.",
        }
    except (ValueError, TypeError, KeyError, OSError) as error:
        return {"status": "error", "reason": f"cards_for_image báo lỗi: {error}"}
    if not isinstance(cards, list):
        return {"status": "error", "reason": "cards_for_image phải trả list."}
    shown, rejected = [], []
    for index, card in enumerate(cards, 1):
        problem = _check_card(card)
        if problem:
            ident = (
                card.get("card_id") if isinstance(card, dict) and card.get("card_id")
                else f"#{index}"
            )
            rejected.append(f"{ident}: {problem}")
        else:
            shown.append(card)
    return {"status": "ok", "cards": shown, "rejected": rejected}
