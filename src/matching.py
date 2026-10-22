"""Đức — S2-04: ghép hố một–một, dùng chung cho chấm điểm và đánh giá.

Quy tắc của nhóm (configs/default.json, mục "evaluation"): một vòng dự đoán
khớp một hố tham chiếu khi khoảng cách hai tâm ≤ 0,5 × bán kính hố tham chiếu.
Mỗi vòng và mỗi hố được dùng tối đa một lần, nên không đếm một hố nhiều lần.
Trong các cách ghép có nhiều cặp nhất, chọn cách có tổng khoảng cách tâm
(chia bán kính) nhỏ nhất; kết quả không phụ thuộc thứ tự các vòng.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.contracts import ContractError

CENTER_TOLERANCE = 0.5


def _assignment(cost: np.ndarray) -> list[tuple[int, int]]:
    """Gán chi phí nhỏ nhất (thuật toán Hungary, thế vị u/v) cho ma trận n×m."""
    transposed = cost.shape[0] > cost.shape[1]
    if transposed:
        cost = cost.T
    n, m = cost.shape
    u, v = np.zeros(n + 1), np.zeros(m + 1)
    owner = np.zeros(m + 1, dtype=int)  # owner[j] = hàng (1..n) đang giữ cột j, 0 nếu trống
    way = np.zeros(m + 1, dtype=int)
    for row in range(1, n + 1):
        owner[0], col = row, 0
        best = np.full(m + 1, np.inf)
        used = np.zeros(m + 1, dtype=bool)
        while True:
            used[col] = True
            i = owner[col]
            free = np.flatnonzero(~used[1:]) + 1
            reduced = cost[i - 1, free - 1] - u[i] - v[free]
            better = reduced < best[free]
            best[free[better]] = reduced[better]
            way[free[better]] = col
            nxt = free[np.argmin(best[free])]
            delta = best[nxt]
            u[owner[used]] += delta
            v[used] -= delta
            best[~used] -= delta
            col = nxt
            if owner[col] == 0:
                break
        while col:
            prev = way[col]
            owner[col] = owner[prev]
            col = prev
    pairs = [(int(owner[j]) - 1, j - 1) for j in range(1, m + 1) if owner[j]]
    return [(j, i) for i, j in pairs] if transposed else pairs


def match_one_to_one(predictions: list[dict[str, Any]], references: list[dict[str, Any]],
                     tolerance: float = CENTER_TOLERANCE) -> list[dict[str, Any]]:
    """Trả các cặp khớp, sắp theo thứ tự vòng dự đoán.

    Mỗi cặp gồm prediction_id, reference_id, center_distance_px,
    normalized_center_distance (chia bán kính tham chiếu) và radius_error_px.
    """
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not 0 < tolerance < math.inf:
        raise ContractError("Ngưỡng tâm phải là số dương.")
    if not predictions or not references:
        return []
    p = np.array([[c["x"], c["y"]] for c in predictions], dtype=float)
    q = np.array([[c["x"], c["y"], c["r"]] for c in references], dtype=float)
    distance = np.hypot(p[:, None, 0] - q[None, :, 0], p[:, None, 1] - q[None, :, 1])
    normalized = distance / q[None, :, 2]
    eligible = normalized <= tolerance + 1e-12
    rows, cols = np.flatnonzero(eligible.any(axis=1)), np.flatnonzero(eligible.any(axis=0))
    if not len(rows):
        return []
    sub = eligible[np.ix_(rows, cols)]
    # Một cặp không đủ điều kiện đắt hơn mọi cách ghép hợp lệ cộng lại,
    # nên lời giải luôn lấy nhiều cặp hợp lệ nhất trước, rồi mới xét khoảng cách.
    penalty = (min(sub.shape) + 1) * (tolerance + 1)
    cost = np.where(sub, normalized[np.ix_(rows, cols)], penalty)
    result = []
    for i, j in sorted(_assignment(cost)):
        if not sub[i, j]:
            continue
        a, b = rows[i], cols[j]
        result.append({"prediction_id": predictions[a]["crater_id"], "reference_id": references[b]["crater_id"],
                       "center_distance_px": round(float(distance[a, b]), 3),
                       "normalized_center_distance": round(float(normalized[a, b]), 4),
                       "radius_error_px": round(float(predictions[a]["r"] - references[b]["r"]), 3)})
    return result
