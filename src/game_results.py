"""Đức — S2-08: kết quả một lượt chấm bài, ảnh đối chiếu và lưu lượt chơi.

Một lượt chấm = câu trả lời hiện tại của người chơi + ứng viên của máy trên
cùng ảnh + nhãn tham chiếu nếu có, chấm bằng score_player (S2-04). Mỗi lượt
được lưu thành một thư mục riêng, không ghi đè: metadata, cấu hình, thời gian,
vòng người chơi, vòng máy và kết quả chấm.
"""
from __future__ import annotations

import io
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image, ImageDraw

from src.contracts import save_run
from src.pipeline import radius_range
from src.player_annotations import build_player_crater_set
from src.scoring import score_player

PIXEL_CENTER = 0.5  # nửa pixel giữa mép và tâm pixel, như geometry.js
# Vòng người chơi cùng màu xanh như trên canvas S1-09; máy màu tím để không lẫn với người chơi.
COLORS = {"machine": "#B69CFF", "player": "#5FE3F5", "reference": "#FF8A7A"}
SPARSE_STEP_PX = 2


def radius_scope(metadata: dict[str, Any], hough: dict[str, Any]) -> dict[str, Any]:
    """Dải bán kính máy thật sự tìm: metadata kẹp trong giới hạn Hough, kèm lưới bước."""
    r_min, r_max = radius_range(metadata, hough)
    step = hough["radius_step_px"]
    radii = range(r_min, r_max + 1, step)
    scale = metadata["scale_m_per_px"]
    return {"metadata_px": [metadata["radius"]["r_min_px"], metadata["radius"]["r_max_px"]],
            "searched_px": [r_min, r_max], "step_px": step, "radii": len(radii), "last_radius_px": radii[-1],
            "diameter_m": [round(2 * r_min * scale, 1), round(2 * r_max * scale, 1)],
            "sparse": step > SPARSE_STEP_PX}


def score_round(player_circles: list[dict[str, Any]], metadata: dict[str, Any], machine: dict[str, Any],
                hough: dict[str, Any], reference: dict[str, Any] | None,
                scoring_params: dict[str, Any]) -> dict[str, Any]:
    """Chấm câu trả lời hiện tại; không đổi vòng của người chơi hay của máy."""
    player = build_player_crater_set(player_circles, metadata)
    return {"player": player, "machine": machine, "reference": reference,
            "score": score_player(player, machine, reference, scoring_params, metadata=metadata),
            "scope": radius_scope(metadata, hough)}


def save_round(output_root: str | Path, metadata: dict[str, Any], scored: dict[str, Any], *,
               config: dict[str, Any], code_version: str) -> Path:
    """Lưu một lượt chấm thành thư mục mới; lỗi giữa chừng thì không để lại thư mục dở."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_id = f"score_{metadata['image_id']}_{stamp}_{uuid4().hex[:8]}"
    params = {**config, "radius_scope": scored["scope"]}
    directory = save_run(output_root, run_id, metadata=metadata, crater_set=scored["player"], params=params,
                         code_version=code_version)
    try:
        records = {"machine.json": scored["machine"], "score.json": scored["score"]}
        if scored["reference"] is not None:
            records["reference.json"] = scored["reference"]
        for name, value in records.items():
            (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                                          encoding="utf-8")
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return directory


def render_overlay(png_bytes: bytes, scored: dict[str, Any], *, upscale: int = 2) -> bytes:
    """Ảnh 512×512 phóng to, vẽ vòng máy (nét mảnh), người chơi (nét đậm) và nhãn tham chiếu."""
    with Image.open(io.BytesIO(png_bytes)) as source:
        picture = source.convert("RGB").resize((512 * upscale, 512 * upscale), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(picture)
    layers = [("machine", scored["machine"], 1), ("reference", scored["reference"], 2), ("player", scored["player"], 3)]
    for name, crater_set, width in layers:
        for c in (crater_set or {}).get("circles", []):
            # Tâm pixel i có tọa độ nguyên i (DINH_DANG_DU_LIEU.md), nên trên ảnh phóng to nó nằm ở
            # (i + 0,5) × tỉ lệ; cùng phép quy đổi với canvas (geometry.js, pixelToScreen).
            x, y, r = (c["x"] + PIXEL_CENTER) * upscale, (c["y"] + PIXEL_CENTER) * upscale, c["r"] * upscale
            draw.ellipse((x - r, y - r, x + r, y + r), outline=COLORS[name], width=width)
    output = io.BytesIO()
    picture.save(output, format="PNG")
    return output.getvalue()
