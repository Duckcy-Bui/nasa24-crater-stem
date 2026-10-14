"""Process explicit canvas save requests without changing the player contract."""
from __future__ import annotations

import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.contracts import ContractError
from src.player_annotations import build_player_crater_set, save_player_answers


def handle_save_request(draft: dict[str, Any], event: dict[str, Any] | None,
                        metadata: dict[str, Any], session_token: str,
                        save_state: dict[str, Any], output_root: str | Path, *,
                        before_save: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Save only the current, validated snapshot; consume each nonce once.

    The caller passes metadata for the image currently open, after applying
    its canvas event. Old image/token/revision requests are ignored. Failed
    writes are consumed too, so a rerun cannot retry them without a new click.
    """
    updated = copy.deepcopy(save_state)
    if not isinstance(event, dict):
        return updated
    nonce = event.get("save_nonce")
    if (event.get("image_id") != metadata["image_id"]
            or event.get("session_token") != session_token
            or not isinstance(nonce, str) or not 1 <= len(nonce) <= 64):
        return updated
    revision = event.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision != draft["revision"]:
        return updated
    handled = updated.get("handled_nonces", [])
    if nonce in handled:
        return updated
    # Equal-revision save commands must contain the same normalized snapshot.
    # A forged or delayed value must never save the wrong coordinates.
    answer = build_player_crater_set(draft["circles"], metadata)
    request_answer = build_player_crater_set(event.get("circles"), metadata)
    if request_answer != answer:
        return updated
    handled.append(nonce)
    updated["handled_nonces"] = handled
    if before_save is not None:
        before_save(copy.deepcopy(updated))
    result = {"nonce": nonce, "revision": revision, "image_id": metadata["image_id"]}
    try:
        directory = save_player_answers(output_root, metadata, draft["circles"])
        # Show paths relative to the project, never the user's home directory.
        directory = Path(directory)
        output = Path(output_root)
        result.update(ok=True, count=len(answer["circles"]),
                      time=datetime.now().strftime("%H:%M"),
                      path=str(Path("outputs") / "player_answers" / directory.relative_to(output)))
    except (OSError, ValueError, ContractError) as error:
        result.update(ok=False, error=str(error))
    updated["result"] = result
    return updated
