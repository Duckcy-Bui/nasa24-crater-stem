"""Đức — S1-13: nối bản chạy từ đầu đến cuối trên một ảnh.

Ảnh đã cắt (S1-06) → tiền xử lý B1–B8 (S1-08) → Hough NumPy (S1-07)
→ danh sách hố của máy (source="machine") → lưu run, ảnh overlay và tóm tắt.

Cùng run có thể đặt cạnh vòng của người chơi (S1-09) và nhãn thủ công (S1-10)
để nhìn bằng mắt. Khi có câu trả lời người chơi, S2-04 chấm riêng so với máy
(chỉ mức trùng) và so với danh mục (chỉ khi nhãn đã kiểm chéo), lưu score.json.
Không tính Precision/Recall của máy: việc đó thuộc evaluation.py (S3-02).
"""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from src.contracts import ContractError, read_json, save_run, validate_crater_set, validate_metadata
from src.hough import DEFAULT_PARAMS as HOUGH_DEFAULTS, detect_circles, resolve_hough_params
from src.postprocessing import filter_candidates
from src.preprocessing import preprocess
from src.scoring import reference_is_reviewed, score_player

PIPELINE_VERSION = "s113-e2e-v1"


def load_image(image_id: str, processed_dir: str | Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray | None]:
    """Đọc metadata, ảnh .npy 512×512 và mặt nạ hợp lệ (nếu có) của một ảnh cắt."""
    processed_dir = Path(processed_dir)
    metadata = read_json(processed_dir / f"{image_id}.json")
    validate_metadata(metadata)
    if metadata["image_id"] != image_id:
        raise ContractError("Tên file và image_id trong metadata không khớp.")
    image = np.load(processed_dir / f"{image_id}.npy")
    mask_path = processed_dir / f"{image_id}_valid_mask.npy"
    valid = np.load(mask_path).astype(bool) if mask_path.exists() else None
    return metadata, image, valid


def find_player_answer(image_id: str, player_root: str | Path) -> Path | None:
    """Lần lưu mới nhất của người chơi cho đúng image_id.

    Xếp theo created_at_utc trong run.json (đủ độ chính xác dưới giây), rồi theo tên thư mục.
    File hỏng hoặc không phải object JSON thì bỏ qua.
    """
    root = Path(player_root)
    if not root.is_dir():
        return None
    matches = []
    for path in root.glob("*/craters.json"):
        try:
            data = read_json(path)
            if not isinstance(data, dict) or data.get("image_id") != image_id:
                continue
            run = read_json(path.parent / "run.json") if (path.parent / "run.json").exists() else {}
            created = run.get("created_at_utc", "") if isinstance(run, dict) else ""
        except (OSError, ValueError):
            continue
        matches.append((str(created), path.parent.name, path))
    return max(matches)[2] if matches else None


def load_overlay_set(path: str | Path | None, metadata: dict[str, Any], expected_source: str) -> dict[str, Any] | None:
    """Đọc một danh sách hố để vẽ cạnh; sai hợp đồng hoặc sai nguồn thì báo lỗi."""
    if path is None:
        return None
    data = read_json(path)
    validate_crater_set(data, metadata)
    if data["source"] != expected_source:
        raise ContractError(f"{path} có source={data['source']}, cần {expected_source}.")
    return data


def radius_range(metadata: dict[str, Any], hough: dict[str, Any]) -> tuple[int, int]:
    """Dải bán kính của ảnh, kẹp trong giới hạn Hough [5, 128]."""
    r_min = max(int(metadata["radius"]["r_min_px"]), hough["r_min_limit_px"])
    r_max = min(int(metadata["radius"]["r_max_px"]), hough["r_max_limit_px"])
    if r_min > r_max:
        raise ContractError(f"Dải bán kính ảnh [{r_min}, {r_max}] nằm ngoài giới hạn Hough.")
    return r_min, r_max


def render_overlay(path: Path, gray: np.ndarray, edges: np.ndarray, metadata: dict[str, Any],
                   machine: dict[str, Any], player: dict[str, Any] | None,
                   reference: dict[str, Any] | None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle

    figure, axes = plt.subplots(1, 2, figsize=(13, 6.8), constrained_layout=True)
    figure.patch.set_facecolor("#0a0c0f")
    extent = [-0.5, 511.5, 511.5, -0.5]
    axes[0].imshow(gray, cmap="gray", vmin=0, vmax=1, extent=extent)
    axes[0].set_title("Ảnh + vòng tròn (tọa độ 512 px, gốc trên-trái)", color="#ecEAE4", fontsize=10)
    axes[1].imshow(edges, cmap="gray", extent=extent)
    axes[1].set_title(f"Biên B8 đưa vào Hough ({int(edges.sum())} pixel)", color="#ecEAE4", fontsize=10)
    layers = [(machine, "#5FE3F5", "--", 1.1), (player, "#FFD84D", "-", 1.6), (reference, "#FF8A7A", ":", 2.0)]
    for data, color, style, width in layers:
        if not data:
            continue
        for c in data["circles"]:
            for axis in axes:
                axis.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, edgecolor=color, linestyle=style, linewidth=width))
    for axis in axes:
        axis.set_xlim(-0.5, 511.5); axis.set_ylim(511.5, -0.5)
        axis.tick_params(colors="#A7ADB6", labelsize=7)
    handles = [Line2D([], [], color="#5FE3F5", linestyle="--", label=f"Máy, ứng viên thô ({len(machine['circles'])})")]
    if player:
        handles.append(Line2D([], [], color="#FFD84D", label=f"Người chơi ({len(player['circles'])})"))
    if reference:
        status = "đã kiểm chéo" if reference_is_reviewed(reference) else "chưa kiểm chéo"
        handles.append(Line2D([], [], color="#FF8A7A", linestyle=":", label=f"Nhãn tham chiếu, {status} ({len(reference['circles'])})"))
    axes[0].legend(handles=handles, loc="upper right", fontsize=7, facecolor="#111419", edgecolor="#303743", labelcolor="#ECEAE4")
    figure.suptitle(f"S1-13 · {metadata['image_id']} · {metadata['scale_m_per_px']} m/px · không chấm điểm: chưa có danh mục đã xác minh",
                    color="#A7ADB6", fontsize=9)
    figure.savefig(path, dpi=110, facecolor=figure.get_facecolor())
    plt.close(figure)


def detect_machine(metadata: dict[str, Any], image: np.ndarray, valid: np.ndarray | None, *,
                   hough_params: dict[str, Any] | None = None,
                   preprocess_params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tiền xử lý → Hough → chấm sáng–tối S1-11 cho một ảnh đã nạp.

    Trả danh sách hố của máy (source="machine") cùng tham số và thời gian từng
    bước; dùng chung cho run_end_to_end và màn hình chấm bài (S2-08).
    """
    t0 = time.perf_counter()
    pre = preprocess(image, metadata, preprocess_params, valid_mask=valid)
    t_pre = time.perf_counter() - t0

    hough = resolve_hough_params(hough_params or {})
    r_min, r_max = radius_range(metadata, hough)
    t0 = time.perf_counter()
    raw_circles = detect_circles(pre["edges"], r_min, r_max, hough, theta=pre["theta"])
    t_hough = time.perf_counter() - t0

    try:
        circles = filter_candidates(raw_circles, pre["gray"], metadata, {"valid_mask": pre["valid_mask"]})
        shading_counts: dict[str, int] = {}
        for c in circles:
            status = (c.get("shading") or {}).get("status", "none")
            shading_counts[status] = shading_counts.get(status, 0) + 1
        postprocess = {"status": "applied", "circles_in": len(raw_circles), "circles_out": len(circles),
                       "shading_counts": shading_counts}
    except NotImplementedError as error:
        circles = raw_circles
        postprocess = {"status": "skipped", "reason": f"S1-11 chưa cài: {error}"}

    machine = {"schema_version": "1.0", "data_kind": metadata["data_kind"], "image_id": metadata["image_id"],
               "source": "machine", "reference_source": None, "circles": circles}
    validate_crater_set(machine, metadata)
    return {"pre": pre, "hough": hough, "r_min": r_min, "r_max": r_max, "raw_circles": raw_circles,
            "machine": machine, "postprocess": postprocess,
            "seconds_preprocess": t_pre, "seconds_hough": t_hough}


def run_end_to_end(image_id: str, *, processed_dir: str | Path, output_root: str | Path, code_version: str,
                   player_path: str | Path | None = None, reference_path: str | Path | None = None,
                   hough_params: dict[str, Any] | None = None, preprocess_params: dict[str, Any] | None = None,
                   scoring_params: dict[str, Any] | None = None, render: bool = True) -> tuple[Path, dict[str, Any]]:
    """Chạy một ảnh từ đầu đến cuối; trả (thư mục run, tóm tắt)."""
    started = time.perf_counter()
    metadata, image, valid = load_image(image_id, processed_dir)
    player = load_overlay_set(player_path, metadata, "player")
    reference = load_overlay_set(reference_path, metadata, "catalogue")

    detected = detect_machine(metadata, image, valid, hough_params=hough_params, preprocess_params=preprocess_params)
    pre, hough, machine = detected["pre"], detected["hough"], detected["machine"]
    r_min, r_max, raw_circles = detected["r_min"], detected["r_max"], detected["raw_circles"]
    t_pre, t_hough, postprocess = detected["seconds_preprocess"], detected["seconds_hough"], detected["postprocess"]

    score = None
    if player:
        score = score_player(player, machine, reference, scoring_params or {}, metadata=metadata)
        catalogue = score["vs_catalogue"]
        scoring = {"status": "scored" if catalogue["status"] == "scored" else "machine_agreement_only",
                   "score": score["score"], "reason": catalogue["reason"],
                   "matched_machine": score["vs_machine"]["matched"], "catalogue_correct": catalogue["correct"]}
    else:
        scoring = {"status": "skipped",
                   "reason": "Chưa có câu trả lời người chơi để chấm. Vòng của máy không phải đáp án."}
    summary = {
        "pipeline_version": PIPELINE_VERSION,
        "image_id": image_id,
        "data_kind": metadata["data_kind"],
        "steps": {
            "load": {"status": "ok", "valid_mask": valid is not None},
            "preprocess": {"status": "ok", "seconds": round(t_pre, 3), "edge_px": int(pre["edges"].sum()),
                           "valid_ratio": pre["params"]["valid_ratio"]},
            "hough": {"status": "ok", "seconds": round(t_hough, 3), "voting_method": hough["voting_method"],
                      "r_min_px": r_min, "r_max_px": r_max, "circles": len(raw_circles),
                      "hit_max_circles": len(raw_circles) >= hough["max_circles"]},
            "postprocess": postprocess,
            "player": {"status": "loaded" if player else "none", "circles": len(player["circles"]) if player else 0,
                       "path": str(player_path) if player else None},
            "reference": {"status": "loaded" if reference else "none", "circles": len(reference["circles"]) if reference else 0,
                          "reference_source": reference["reference_source"] if reference else None,
                          "reviewed": reference_is_reviewed(reference)},
            "scoring": scoring,
        },
    }
    params = {"pipeline_version": PIPELINE_VERSION, "preprocess": pre["params"], "hough": hough,
              "hough_defaults": HOUGH_DEFAULTS, "radius_px": [r_min, r_max]}
    radii = range(r_min, r_max + 1, hough["radius_step_px"])
    radius_search = {"metadata_px": [metadata["radius"]["r_min_px"], metadata["radius"]["r_max_px"]],
                     "bounds_px": [r_min, r_max], "step_px": radii.step,
                     "count": len(radii), "last_radius_px": radii[-1]}
    params["radius_search"] = radius_search
    summary["steps"]["hough"]["radius_search"] = radius_search
    run_id = f"e2e_{image_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid4().hex[:8]}"
    directory = save_run(output_root, run_id, metadata=metadata, crater_set=machine, params=params, code_version=code_version)
    # A run directory is either complete or removed: never leave craters.json without summary/overlay.
    try:
        summary["seconds_total"] = round(time.perf_counter() - started, 3)
        if player:
            (directory / "player.json").write_text(json.dumps(player, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if score:
            (directory / "score.json").write_text(json.dumps(score, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if reference:
            (directory / "reference.json").write_text(json.dumps(reference, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        np.savez_compressed(directory / "arrays.npz", gray=pre["gray"], edges=pre["edges"], theta=pre["theta"])
        if render:
            render_overlay(directory / "overlay.png", pre["gray"], pre["edges"], metadata, machine, player, reference)
        (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except BaseException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return directory, summary
