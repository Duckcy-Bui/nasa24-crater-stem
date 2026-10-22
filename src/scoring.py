"""Đức — S2-04/S2-08: chấm người chơi theo hai nguồn riêng.

1. So với máy: chỉ là mức trùng với ứng viên Hough. Máy không phải đáp án,
   nên phần này không sinh điểm, chỉ đếm vòng trùng và vòng lệch.
2. So với danh mục: chỉ chấm khi nhãn đã được kiểm chéo ("reviewed by <tên>").
   - Nhãn thưa (mặc định): chỉ biết hố đã gán nhãn, nên điểm = tỉ lệ hố
     đã gán nhãn mà người chơi tìm được (recall). Vòng không khớp nhãn nào
     không bị tính là khoanh sai, vì vùng chưa gán nhãn vẫn có thể có hố.
   - Nhãn đầy đủ (catalogue_coverage="complete", do S2-03 xác nhận): có thêm
     khoanh sai và precision; điểm = F1.
Hố có "uncertain" trong crater_id (quy ước S1-10) bị loại khỏi phần chấm.
"""
from __future__ import annotations

from typing import Any

from src.contracts import ContractError, validate_crater_set
from src.matching import CENTER_TOLERANCE, match_one_to_one

COVERAGES = ("sparse", "complete")


def reference_is_reviewed(reference: dict[str, Any] | None) -> bool:
    """Nhãn thủ công chỉ được coi là đã kiểm chéo khi nguồn ghi "reviewed by"."""
    source = (reference or {}).get("reference_source") or ""
    return "reviewed by" in source.lower() and "unreviewed" not in source.lower()


def _check(data: dict[str, Any] | None, source: str, metadata: dict[str, Any]) -> None:
    if data is None:
        return
    validate_crater_set(data, metadata)
    if data["source"] != source:
        raise ContractError(f"Cần danh sách hố source={source}, nhận {data['source']}.")


def _ids(circles: list[dict[str, Any]], used: set[str]) -> list[str]:
    return [c["crater_id"] for c in circles if c["crater_id"] not in used]


def compare_with_machine(player: dict[str, Any], machine: dict[str, Any], tolerance: float) -> dict[str, Any]:
    pairs = match_one_to_one(player["circles"], machine["circles"], tolerance)
    return {"kind": "agreement_with_machine", "matched": len(pairs),
            "player_only_ids": _ids(player["circles"], {p["prediction_id"] for p in pairs}),
            "machine_only_ids": _ids(machine["circles"], {p["reference_id"] for p in pairs}),
            "pairs": pairs,
            "note": "Mức trùng với ứng viên của máy, không phải độ chính xác: máy không phải đáp án."}


def compare_with_catalogue(player: dict[str, Any], catalogue: dict[str, Any] | None,
                           tolerance: float, coverage: str) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": "catalogue", "status": "unavailable", "reason": None,
                              "coverage": coverage, "reviewed": reference_is_reviewed(catalogue),
                              "reference_source": catalogue["reference_source"] if catalogue else None,
                              "excluded_ids": [], "correct": None, "missed_ids": [], "wrong_ids": None,
                              "unmatched_player_ids": [], "recall": None, "precision": None, "score": None,
                              "pairs": []}
    if catalogue is None:
        result["reason"] = "Ảnh chưa có danh mục hoặc nhãn tham chiếu."
        return result
    if not result["reviewed"]:
        result["reason"] = "Nhãn chưa được kiểm chéo (cần \"reviewed by <tên>\"); chưa chấm."
        return result
    excluded = {c["crater_id"] for c in catalogue["circles"] if "uncertain" in c["crater_id"].lower()}
    references = [c for c in catalogue["circles"] if c["crater_id"] not in excluded]
    result["excluded_ids"] = sorted(excluded)
    if not references:
        result["reason"] = "Không còn hố tham chiếu chắc chắn để chấm."
        return result
    pairs = match_one_to_one(player["circles"], references, tolerance)
    found = {p["reference_id"] for p in pairs}
    unmatched = _ids(player["circles"], {p["prediction_id"] for p in pairs})
    tp, n_ref, n_player = len(pairs), len(references), len(player["circles"])
    recall = tp / n_ref
    result.update(status="scored", correct=tp, pairs=pairs, missed_ids=_ids(references, found),
                  unmatched_player_ids=unmatched, recall=round(recall, 4))
    if coverage == "complete":
        result.update(wrong_ids=unmatched, precision=round(tp / n_player, 4) if n_player else None,
                      score=round(100 * 2 * tp / (n_player + n_ref), 1),
                      reason="Nhãn đầy đủ: điểm = F1 × 100.")
    else:
        result.update(score=round(100 * recall, 1),
                      reason="Nhãn thưa: điểm = tỉ lệ hố đã gán nhãn được tìm thấy; "
                             "vòng ngoài nhãn không bị tính là khoanh sai.")
    return result


def score_player(player: dict, machine: dict | None, catalogue: dict | None, params: dict, *,
                 metadata: dict) -> dict:
    """Cùng image_id; trả riêng so máy và so danh mục, ghép hố một-một."""
    if not isinstance(params, dict):
        raise ContractError("params phải là dict.")
    tolerance = params.get("center_tolerance_fraction", CENTER_TOLERANCE)
    if params.get("matching", "one_to_one") != "one_to_one":
        raise ContractError("Chỉ hỗ trợ ghép one_to_one.")
    coverage = params.get("catalogue_coverage", "sparse")
    if coverage not in COVERAGES:
        raise ContractError("catalogue_coverage phải là sparse hoặc complete.")
    _check(player, "player", metadata)
    _check(machine, "machine", metadata)
    _check(catalogue, "catalogue", metadata)
    vs_catalogue = compare_with_catalogue(player, catalogue, tolerance, coverage)
    return {"image_id": player["image_id"], "data_kind": player["data_kind"],
            "rule": {"matching": "one_to_one", "center_tolerance_fraction": tolerance},
            "player_circles": len(player["circles"]),
            "vs_machine": compare_with_machine(player, machine, tolerance) if machine is not None else None,
            "vs_catalogue": vs_catalogue,
            "score": vs_catalogue["score"]}
