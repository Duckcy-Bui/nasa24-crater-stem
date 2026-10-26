"""Quốc Anh/Đức — S2-10: thẻ khoa học gắn đúng địa điểm ảnh."""


from __future__ import annotations

from typing import Any


def _card(card_id: str, title: str, body: str, source_title: str, source_url: str) -> dict[str, Any]:
    return {"card_id": card_id, "title": title, "body": body,
            "source_title": source_title, "source_url": source_url, "position": None}


APOLLO15 = _card(
    "apollo15-hadley-region", "Apollo 15 — vùng Hadley–Apennine",
    "Ảnh thuộc vùng Hadley–Apennine, nơi Apollo 15 hạ cánh năm 1971. Mô-đun Falcon và xe tự hành không nằm trong crop 512×512 này, nên thẻ không đặt ghim vị trí.",
    "NASA — Apollo 15 Mission Details", "https://www.nasa.gov/missions/apollo/apollo-15-mission-details/",
)
APOLLO16 = _card(
    "apollo16-descartes-region", "Apollo 16 — vùng cao nguyên Descartes",
    "Ảnh thuộc vùng cao nguyên Descartes, nơi Apollo 16 hạ cánh năm 1972 để khảo sát vật liệu cao nguyên. Vị trí mô-đun Orion/ALSEP ở ngoài crop 512×512 này, nên thẻ không đặt ghim vị trí.",
    "NASA — Apollo 16 Mission Details", "https://www.nasa.gov/missions/apollo/apollo-16-mission-details/",
)
LUNOKHOD1 = _card(
    "lunokhod1-mare-imbrium-region", "Lunokhod 1 — vùng Mare Imbrium",
    "Ảnh thuộc mosaic vùng Lunokhod 1 ở Mare Imbrium. LROC đã xác định lại vị trí rover, nhưng rover không nằm trong crop 512×512 này, nên thẻ không đặt ghim vị trí.",
    "LROC — Lunokhod 1 Revisited", "https://lroc.im-ldi.com/images/402",
)
LUNOKHOD2 = _card(
    "lunokhod2-le-monnier-region", "Lunokhod 2 — vùng Le Monnier",
    "Ảnh thuộc mosaic vùng Lunokhod 2 ở hố Le Monnier. Tọa độ rover đã được LRO xác minh, nhưng rover không nằm trong crop 512×512 này, nên thẻ không đặt ghim vị trí.",
    "NASA/NSSDC — Table of Anthropogenic Impacts and Spacecraft on the Moon", "https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_artifact_impacts.html",
)


def cards_for_image(image_id: str) -> list[dict[str, Any]]:
    """Trả thẻ vùng đã kiểm chứng; ảnh không thuộc bốn vùng này không có thẻ."""
    if image_id.startswith("moon_ap15_"):
        return [dict(APOLLO15)]
    if image_id.startswith("moon_ap16_"):
        return [dict(APOLLO16)]
    if image_id.startswith("moon_lunokhod1_"):
        return [dict(LUNOKHOD1)]
    if image_id.startswith("moon_lunokhod2_"):
        return [dict(LUNOKHOD2)]
    return []
