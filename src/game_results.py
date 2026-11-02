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

# Vòng người chơi cùng màu xanh như trên canvas S1-09; máy màu tím để không lẫn với người chơi.
COLORS = {"machine": "#B69CFF", "player": "#5FE3F5", "reference": "#FF8A7A"}
SPARSE_STEP_PX = 2


def radius_scope(metadata: dict[str, Any], hough: dict[str, Any]) -> dict[str, Any]:
    """Tóm tắt dải bán kính thực quét của máy.

    Vào: metadata (dict dải r px, tỷ lệ m/px), hough (dict giới hạn và bước r px).
    Ra: dict dải metadata/thực quét, bước, số bán kính, đường kính m và cờ lưới thưa.
    Tham chiếu: báo cáo mục 3.3 và 3.7."""
    r_min, r_max = radius_range(metadata, hough)
    step = hough["radius_step_px"]
    radii = range(r_min, r_max + 1, step)
    scale = metadata["scale_m_per_px"]
    return {"metadata_px": [metadata["radius"]["r_min_px"], metadata["radius"]["r_max_px"]],
            "searched_px": [r_min, r_max], "step_px": step,
            "radii": len(radii), "last_radius_px": radii[-1],
            "diameter_m": [round(2 * r_min * scale, 1), round(2 * r_max * scale, 1)],
            "sparse": step > SPARSE_STEP_PX}


def score_round(
    player_circles: list[dict[str, Any]], metadata: dict[str, Any], machine: dict[str, Any],
    hough: dict[str, Any], reference: dict[str, Any] | None,
    scoring_params: dict[str, Any],
) -> dict[str, Any]:
    """Chấm câu trả lời mà không sửa các vòng đầu vào.

    Vào: player_circles (list dict tâm/r px), metadata, machine, hough (dict),
    reference (dict nhãn hoặc None), scoring_params (dict quy tắc ghép/chấm).
    Ra: dict tập vòng người/máy/nhãn, điểm và phạm vi bán kính thực tìm.
    Tham chiếu: báo cáo mục 3.7, công thức (2.20)–(2.23) và (3.3)."""
    player = build_player_crater_set(player_circles, metadata)
    return {"player": player, "machine": machine, "reference": reference,
            "score": score_player(player, machine, reference, scoring_params, metadata=metadata),
            "scope": radius_scope(metadata, hough)}


def save_round(output_root: str | Path, metadata: dict[str, Any], scored: dict[str, Any], *,
               config: dict[str, Any], code_version: str) -> Path:
    """Lưu lượt chấm vào thư mục mới, không ghi đè lượt cũ.

    Vào: output_root (str/Path), metadata/scored/config (dict), code_version (str).
    Ra: Path thư mục đã ghi metadata, tham số, vòng và điểm; lỗi giữa chừng
    thì xóa thư mục dở và phát lại lỗi.
    Tham chiếu: báo cáo mục 3.1 và 3.7."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_id = f"score_{metadata['image_id']}_{stamp}_{uuid4().hex[:8]}"
    params = {**config, "radius_scope": scored["scope"]}
    directory = save_run(
        output_root, run_id, metadata=metadata, crater_set=scored["player"], params=params,
        code_version=code_version,
    )
    try:
        records = {"machine.json": scored["machine"], "score.json": scored["score"]}
        if scored["reference"] is not None:
            records["reference.json"] = scored["reference"]
        for name, value in records.items():
            (directory / name).write_text(
                json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return directory


def render_overlay(png_bytes: bytes, scored: dict[str, Any], *, upscale: int = 3) -> bytes:
    """Vẽ vòng máy, người chơi và nhãn lên ảnh phóng to.

    Vào: png_bytes (ảnh PNG 512×512), scored (dict tập vòng có tâm/r px),
    upscale (int hệ số phóng, mặc định 3). Ra: bytes PNG đối chiếu;
    không sửa ảnh nguồn hoặc ghi file, dùng nét mảnh cho máy và nét đậm cho người.
    Tham chiếu: báo cáo mục 3.7 về tâm pixel và ảnh đối chiếu."""
    with Image.open(io.BytesIO(png_bytes)) as source:
        picture = source.convert("RGB").resize(
            (512 * upscale, 512 * upscale), Image.Resampling.LANCZOS,
        )
    draw = ImageDraw.Draw(picture)
    layers = [
        ("machine", scored["machine"], 1), ("reference", scored["reference"], 2),
        ("player", scored["player"], 3),
    ]
    for name, crater_set, width in layers:
        for c in (crater_set or {}).get("circles", []):
            # Tâm pixel i có tọa độ nguyên i (DINH_DANG_DU_LIEU.md). Phóng k lần thì pixel i
            # thành các pixel k·i … k·i + k − 1, tâm ở k·i + (k − 1)/2 (cùng công thức đổi
            # tỷ lệ của hợp đồng). PIL vẽ theo chỉ số pixel nguyên và bỏ phần lẻ, nên dùng
            # k lẻ (mặc định 3) để tâm hố có tọa độ nguyên rơi đúng một pixel.
            x, y = upscale * c["x"] + (upscale - 1) / 2, upscale * c["y"] + (upscale - 1) / 2
            r = c["r"] * upscale
            draw.ellipse((x - r, y - r, x + r, y + r), outline=COLORS[name], width=width)
    output = io.BytesIO()
    picture.save(output, format="PNG")
    return output.getvalue()
