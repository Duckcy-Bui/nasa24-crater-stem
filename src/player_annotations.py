"""Player-only annotations for S1-09; no inferred answers or score."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.contracts import ContractError, save_run, validate_crater_set


def build_player_crater_set(circles: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    """Validate canvas circles and emit the shared player-answer contract."""
    if not isinstance(circles, list):
        raise ContractError("circles phải là danh sách.")
    if len(circles) > 500:
        raise ContractError("Mỗi ảnh hỗ trợ tối đa 500 vòng tròn.")
    normalized = []
    for circle in circles:
        if not isinstance(circle, dict):
            raise ContractError("Mỗi vòng tròn phải là object.")
        if any(name not in circle for name in ("crater_id", "x", "y", "r")):
            raise ContractError("Vòng tròn cần crater_id, x, y và r.")
        if circle.get("confidence") is not None or circle.get("votes") is not None:
            raise ContractError("Câu trả lời người chơi không có confidence hoặc votes.")
        normalized.append({name: copy.deepcopy(circle[name]) for name in ("crater_id", "x", "y", "r")}
                          | {"confidence": None, "votes": None})
    result = {"schema_version": "1.0", "data_kind": metadata.get("data_kind"),
              "image_id": metadata.get("image_id"), "source": "player",
              "reference_source": None, "circles": normalized}
    validate_crater_set(result, metadata)
    return result


def apply_canvas_event(draft: dict[str, Any], event: dict[str, Any] | None,
                       metadata: dict[str, Any], session_token: str) -> dict[str, Any]:
    """Ignore stale/cross-image values; validate newer events without mutation."""
    current = copy.deepcopy(draft)
    if not isinstance(current.get("revision"), int) or isinstance(current["revision"], bool) or current["revision"] < 0:
        raise ContractError("revision của bản nháp phải là số nguyên >= 0.")
    build_player_crater_set(current.get("circles"), metadata)
    if event is None:
        return current
    if not isinstance(event, dict):
        raise ContractError("Sự kiện canvas phải là object.")
    if event.get("image_id") != metadata["image_id"] or event.get("session_token") != session_token:
        return current
    revision = event.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ContractError("revision phải là số nguyên >= 0.")
    if revision <= current["revision"]:
        return current
    answer = build_player_crater_set(event.get("circles"), metadata)
    return {"revision": revision, "circles": answer["circles"]}


def save_player_answers(output_root: str | Path, metadata: dict[str, Any],
                        circles: list[dict[str, Any]], *, run_id: str | None = None) -> Path:
    """Save an immutable answer run and its metadata without overwriting."""
    answer = build_player_crater_set(circles, metadata)
    ident = run_id if run_id is not None else "player_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:12]
    return save_run(output_root, ident, metadata=metadata, crater_set=answer,
                    params={"interface": "s1-09", "coordinate_space": "processed_image_pixels"},
                    code_version="s3-04-player-ui-v2")
