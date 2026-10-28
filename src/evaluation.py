"""S3-02: one-to-one detection evaluation; sparse labels never imply FP/P/F1."""

from __future__ import annotations

from src.contracts import ContractError, validate_crater_set
from src.matching import CENTER_TOLERANCE, match_one_to_one
from src.scoring import reference_is_reviewed


def evaluate(machine: dict, catalogue: dict, params: dict) -> dict:
    """Evaluate known labels; complete coverage must be declared in catalogue."""
    if not isinstance(params, dict):
        raise ContractError("params phải là một dict.")
    if params.get("matching", "one_to_one") != "one_to_one":
        raise ContractError("Chỉ hỗ trợ ghép cặp one_to_one.")
    if machine.get("source") != "machine" or catalogue.get("source") != "catalogue":
        raise ContractError("Nguồn đầu vào phải là machine và catalogue.")
    # Validate through the same contract as the application, including unique IDs.
    metadata = params.get("metadata")
    if metadata is None:
        raise ContractError("Đánh giá cần params['metadata'].")
    validate_crater_set(machine, metadata)
    validate_crater_set(catalogue, metadata)
    tolerance = params.get("center_tolerance_fraction", CENTER_TOLERANCE)
    # Validate even empty inputs.
    match_one_to_one([], [], tolerance)
    coverage = catalogue.get("catalogue_coverage", "sparse")
    if coverage not in ("sparse", "complete"):
        raise ContractError("catalogue_coverage phải là sparse hoặc complete.")
    result = dict(
        image_id=machine["image_id"],
        status="unavailable",
        coverage=coverage,
        tp=None,
        fp=None,
        fn=None,
        precision=None,
        recall=None,
        f1=None,
        pairs=[],
        ignored_prediction_ids=[],
        missed_reference_ids=[],
        unmatched_prediction_ids=[],
        reference_source=catalogue["reference_source"],
        rule=dict(matching="one_to_one", center_tolerance_fraction=tolerance),
    )
    if not reference_is_reviewed(catalogue):
        result["reason"] = "Nhãn tham chiếu chưa được kiểm chéo."
        return result
    certain = [
        c for c in catalogue["circles"] if "uncertain" not in c["crater_id"].lower()
    ]
    uncertain = [
        c for c in catalogue["circles"] if "uncertain" in c["crater_id"].lower()
    ]
    pairs = match_one_to_one(machine["circles"], certain, tolerance)
    used = {p["prediction_id"] for p in pairs}
    found = {p["reference_id"] for p in pairs}
    remaining = [c for c in machine["circles"] if c["crater_id"] not in used]
    # Ignore every prediction inside any uncertain region, after matching certain
    # labels first. Multiple guesses in one uncertain region are all ignored.
    ignored = {
        c["crater_id"]
        for c in remaining
        if any(
            (c["x"] - u["x"]) ** 2 + (c["y"] - u["y"]) ** 2 <= (tolerance * u["r"]) ** 2
            for u in uncertain
        )
    }
    unmatched = [c["crater_id"] for c in remaining if c["crater_id"] not in ignored]
    tp, fn = len(pairs), len(certain) - len(pairs)
    recall = tp / len(certain) if certain else None
    fp = len(unmatched) if coverage == "complete" else None
    precision = tp / (tp + fp) if fp is not None and tp + fp else None
    f1 = 2 * tp / (2 * tp + fp + fn) if fp is not None and 2 * tp + fp + fn else None
    result.update(
        status="evaluated",
        tp=tp,
        fp=fp,
        fn=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        pairs=pairs,
        ignored_prediction_ids=sorted(ignored),
        missed_reference_ids=[
            c["crater_id"] for c in certain if c["crater_id"] not in found
        ],
        unmatched_prediction_ids=unmatched,
        known_references=len(certain),
        reason=(
            "Chỉ tính Recall trên nhãn đã biết."
            if coverage == "sparse"
            else "Vùng đã được gán nhãn đầy đủ."
        ),
    )
    return result
