"""Hưng — S1-11: chấm mức phù hợp sáng–tối của ứng viên hố theo hướng nắng.

Cơ sở vật lý (S1-04 mục 6.3): hố là chỗ lõm. Thành hố phía gần Mặt Trời quay
lưng với nắng nên tối, thành phía xa hướng về nắng nên sáng. Gò nổi cho kết
quả ngược lại; vòng đặt vào chỗ không có hố cho kết quả gần 0.

Cách chấm (tự viết bằng NumPy):
    u = (sin φ, −cos φ), φ = azimuth_deg + north_angle_deg  (S1-04 mục 6.1)
    Với các pixel hợp lệ trong đĩa bán kính r:  t = −((p − c)·u) / r
    Trừ độ dốc địa hình: khớp mặt phẳng độ sáng trên vành khuyên ngoài
    [1,3r; 2r] và trừ khỏi pixel trong đĩa (vòng trên sườn dốc không bị chấm sai).
    score = hệ số tương quan Pearson giữa độ sáng đã trừ dốc và t, trong [−1, 1].
    score > 0: sáng dần về phía xa Mặt Trời → khớp hố lõm.
    Chỉ kết luận khi ảnh gốc và ảnh đã trừ dốc cho cùng nhãn; khác nhãn → "unclear"
    (mặt phẳng không mô tả được mép bóng sắc, nên trừ dốc một mình có thể tạo dấu giả).

S1-11 CHỈ CHẤM, KHÔNG XÓA vòng nào. Ngưỡng loại bỏ để S2-02 quyết định khi
có số liệu. Ảnh không có hướng nắng đủ tin cậy thì mọi vòng ghi
status="not_checked" kèm lý do, và ghi log.

Hướng nắng chỉ được dùng khi có căn cứ:
  1. metadata có sun.quality measured/side_only và azimuth_deg (từ trang nguồn),
     hoặc phía nắng side_candidate đã được xác nhận bằng mắt;
  2. góc tới >= 30° (S1-04 mục 6.2; nắng gần đứng thì bóng quá ngắn);
  3. hướng nắng/hướng Bắc đã được kiểm tra bằng mắt trên hố tham chiếu
     (S1-04 mục 6.3), ghi trong data/s111_sun_checks.json.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
SUN_CHECKS_PATH = ROOT / "data" / "s111_sun_checks.json"
MODULE_VERSION = "s111-2"

DEFAULT_PARAMS = {
    "min_incidence_deg": 30.0,       # S1-04 mục 6.2; đề xuất ban đầu, cần kiểm chứng
    "require_visual_check": True,    # S1-04 mục 6.3: bắt buộc nhìn bằng mắt trước khi dùng ảnh
    "disk_fraction": 1.0,            # lấy pixel trong đĩa bán kính disk_fraction·r
    "min_pixels": 30,                # ít hơn thì không đủ pixel để chấm
    "min_valid_fraction": 0.8,       # phần đĩa nằm trong ảnh và hợp lệ
    "score_threshold": 0.15,         # |score| < ngưỡng → "unclear" (measured)
    "score_threshold_side_only": 0.25,  # nới hơn vì chỉ biết Đông/Tây (S1-04 mục 6.2)
    "detrend": True,                 # trừ độ dốc sáng của địa hình quanh vòng
    "annulus_inner": 1.3,            # vành ngoài bắt đầu từ 1,3r: bỏ qua vành nổi của hố
    "annulus_outer": 2.0,
    "min_annulus_pixels": 30,
    "min_annulus_fraction": 0.5,     # vành ngoài phải còn ít nhất nửa trong ảnh và hợp lệ
}

SIDE_AZIMUTH = {"east": 90.0, "west": 270.0}


# ------------------------------------------------------------ Hướng nắng
def load_sun_checks(path: str | Path | None = None) -> dict[str, dict]:
    """Đọc kết quả kiểm tra hướng nắng bằng mắt; trả {image_id: bản ghi}."""
    path = Path(path) if path is not None else SUN_CHECKS_PATH
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["image_id"]: item for item in data.get("checks", [])}


def resolve_sun(metadata: dict, check: dict | None, params: dict) -> dict:
    """Quyết định ảnh có được chấm không.

    Trả {"usable": bool, "reason": str, "azimuth_deg", "quality", "basis": [...]}.
    """
    sun = metadata.get("sun") or {}
    quality = sun.get("quality")
    azimuth = sun.get("azimuth_deg")
    incidence = sun.get("incidence_deg")
    basis = []
    result = {"usable": False, "azimuth_deg": None, "quality": quality, "basis": basis,
              "incidence_deg": incidence, "visual_check": check.get("verdict") if check else None}

    # 1. Phương vị có nguồn, hoặc phía nắng ứng viên đã xác nhận bằng mắt.
    if quality in ("measured", "side_only") and azimuth is not None:
        basis.append(f"metadata: {quality} {azimuth:g}° ({sun.get('source', 'không ghi nguồn')})")
    elif sun.get("side_candidate") in SIDE_AZIMUTH and check and check.get("verdict") == "consistent":
        side = sun["side_candidate"]
        azimuth, quality = SIDE_AZIMUTH[side], "side_only"
        result["quality"] = quality
        basis.append(f"side_candidate={side} được xác nhận bằng mắt ({check.get('checked_by')}, {check.get('checked_on')})")
    else:
        candidate = sun.get("side_candidate")
        result["reason"] = (f"phía nắng '{candidate}' chưa xác minh bằng mắt" if candidate
                            else "metadata không có hướng nắng (sun.quality=none)")
        return result

    # 2. Nắng gần đứng: bóng quá ngắn.
    if incidence is None:
        result["reason"] = "không có góc tới của cửa sổ"
        return result
    if incidence < params["min_incidence_deg"]:
        result["reason"] = f"góc tới {incidence:g}° < {params['min_incidence_deg']:g}°: nắng gần đứng, bóng quá ngắn"
        return result

    # 3. Kiểm tra hướng nắng / hướng Bắc bằng mắt.
    if metadata.get("north_angle_deg") is None:
        result["reason"] = "chưa biết north_angle_deg"
        return result
    if params["require_visual_check"]:
        verdict = check.get("verdict") if check else None
        if verdict != "consistent":
            result["reason"] = ("chưa kiểm tra hướng nắng bằng mắt (S1-04 mục 6.3)" if verdict in (None, "pending")
                                else f"kiểm tra bằng mắt cho kết quả '{verdict}': không dùng ảnh này")
            return result
        if not any("bằng mắt" in b for b in basis):
            basis.append(f"hướng Bắc/nắng xác nhận bằng mắt ({check.get('checked_by')}, {check.get('checked_on')})")

    result.update(usable=True, azimuth_deg=float(azimuth), reason=None)
    return result


def sun_vector(azimuth_deg: float, north_angle_deg: float) -> tuple[float, float]:
    """Vector đơn vị chỉ về phía Mặt Trời trong hệ ảnh (x phải, y xuống) — S1-04 mục 6.1."""
    phi = math.radians(azimuth_deg + north_angle_deg)
    return math.sin(phi), -math.cos(phi)


# ------------------------------------------------------------ Chấm một vòng
def _pixels_in_ring(valid: np.ndarray, x: float, y: float, r_in: float, r_out: float):
    """Tọa độ pixel hợp lệ trong vành khuyên r_in < d <= r_out (r_in < 0 → cả đĩa); kèm số pixel lý thuyết."""
    x0, x1 = int(math.floor(x - r_out)), int(math.ceil(x + r_out)) + 1
    y0, y1 = int(math.floor(y - r_out)), int(math.ceil(y + r_out)) + 1
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d2 = (xx - x) ** 2 + (yy - y) ** 2
    ring = (d2 <= r_out ** 2) & (d2 > r_in ** 2 if r_in >= 0 else True)
    total = int(ring.sum())
    h, w = valid.shape
    keep = ring & (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
    keep[keep] = valid[yy[keep], xx[keep]]
    return xx[keep], yy[keep], total


def shading_score(image: np.ndarray, valid: np.ndarray, x: float, y: float, r: float,
                  u: tuple[float, float], params: dict) -> tuple[float | None, str | None]:
    """[TỰ VIẾT] Tương quan giữa độ sáng và vị trí dọc hướng ra xa Mặt Trời.

    Nếu params["detrend"]: trước khi tính, khớp mặt phẳng độ sáng a + b·x + c·y
    (bình phương tối thiểu) trên vành khuyên ngoài [annulus_inner·r, annulus_outer·r]
    rồi trừ khỏi pixel trong đĩa. Mặt phẳng đại diện độ dốc sáng của địa hình
    quanh vòng; không trừ thì một vòng đặt trên sườn dốc cũng bị chấm hợp/ngược.

    Trả (score, None) hoặc (None, lý do không chấm được).
    """
    xs, ys, total = _pixels_in_ring(valid, x, y, -1.0, params["disk_fraction"] * r)
    n = len(xs)
    if n < params["min_pixels"] or n < params["min_valid_fraction"] * total:
        return None, f"chỉ {n}/{total} pixel trong đĩa nằm trong ảnh và hợp lệ"
    values = image[ys, xs].astype(np.float64)

    if params["detrend"]:
        ax, ay, a_total = _pixels_in_ring(valid, x, y, params["annulus_inner"] * r, params["annulus_outer"] * r)
        m = len(ax)
        if m < params["min_annulus_pixels"] or m < params["min_annulus_fraction"] * a_total:
            return None, f"chỉ {m}/{a_total} pixel vành ngoài hợp lệ, không ước lượng được độ dốc địa hình"
        design = np.column_stack([np.ones(m), (ax - x) / r, (ay - y) / r])
        coef, *_ = np.linalg.lstsq(design, image[ay, ax].astype(np.float64), rcond=None)
        values = values - (coef[0] + coef[1] * (xs - x) / r + coef[2] * (ys - y) / r)

    t = -((xs - x) * u[0] + (ys - y) * u[1]) / r
    sv, st = values.std(), t.std()
    if sv < 1e-9 or st == 0:
        return None, "độ sáng trong đĩa không đổi"
    score = float(((values - values.mean()) * (t - t.mean())).mean() / (sv * st))
    return score, None


def classify(score: float, quality: str, params: dict) -> str:
    threshold = params["score_threshold_side_only"] if quality == "side_only" else params["score_threshold"]
    if score >= threshold:
        return "consistent"
    if score <= -threshold:
        return "inverted"
    return "unclear"


def score_one(image: np.ndarray, valid: np.ndarray, c: dict, u: tuple[float, float], quality: str, p: dict) -> dict:
    """Chấm một vòng; trả {"status", "score", "score_raw", "reason"}.

    Khi bật detrend, chấm cả trên ảnh gốc lẫn sau khi trừ độ dốc địa hình và chỉ
    kết luận khi hai cách cùng nhãn. Khác nhãn nghĩa là kết quả do độ dốc hoặc mép
    bóng lớn quanh vòng quyết định, không phải do hình dạng hố → "unclear".
    """
    raw, why_raw = shading_score(image, valid, c["x"], c["y"], c["r"], u, {**p, "detrend": False})
    if raw is None:
        return {"status": "not_checked", "score": None, "score_raw": None, "reason": why_raw}
    if not p["detrend"]:
        return {"status": classify(raw, quality, p), "score": round(raw, 4), "score_raw": round(raw, 4), "reason": None}
    score, why = shading_score(image, valid, c["x"], c["y"], c["r"], u, p)
    if score is None:
        return {"status": "not_checked", "score": None, "score_raw": round(raw, 4), "reason": why}
    status, status_raw = classify(score, quality, p), classify(raw, quality, p)
    reason = None
    if status != status_raw:
        reason = (f"độ dốc/mép bóng địa hình làm kết quả không ổn định: ảnh gốc '{status_raw}' "
                  f"({raw:+.2f}), sau trừ dốc '{status}' ({score:+.2f})")
        status = "unclear"
    return {"status": status, "score": round(score, 4), "score_raw": round(raw, 4), "reason": reason}


# ------------------------------------------------------------ API cho pipeline
def resolve_params(params: dict | None) -> dict:
    params = dict(params or {})
    params.pop("sun_checks", None)
    params.pop("valid_mask", None)
    unknown = set(params) - set(DEFAULT_PARAMS)
    if unknown:
        raise ValueError("Tham số S1-11 không biết: " + ", ".join(sorted(unknown)))
    return {**DEFAULT_PARAMS, **params}


def score_candidates(circles: list[dict], image: Any, metadata: dict, params: dict | None = None,
                     valid_mask: Any = None) -> tuple[list[dict], dict]:
    """Thêm trường "shading" vào bản sao từng vòng; trả (vòng, báo cáo cấp ảnh).

    shading = {"status": consistent|inverted|unclear|not_checked, "score": float|None (sau trừ dốc),
               "score_raw": float|None (ảnh gốc), "reason": str|None}
    """
    sun_checks = (params or {}).get("sun_checks")
    if valid_mask is None:
        valid_mask = (params or {}).get("valid_mask")
    p = resolve_params(params)
    image = np.asarray(image, dtype=np.float32)
    valid = np.ones(image.shape, dtype=bool) if valid_mask is None else np.asarray(valid_mask, dtype=bool)
    # NaN/inf pixels are nodata: exclude them, otherwise a score becomes NaN and breaks JSON output.
    valid = valid & np.isfinite(image)
    image = np.where(valid, image, 0.0).astype(np.float32)
    checks = sun_checks if isinstance(sun_checks, dict) else load_sun_checks(sun_checks)
    image_id = metadata.get("image_id")
    sun = resolve_sun(metadata, checks.get(image_id), p)

    out = []
    counts = {"consistent": 0, "inverted": 0, "unclear": 0, "not_checked": 0}
    if not sun["usable"]:
        log.warning("S1-11 bỏ qua kiểm tra sáng–tối cho %s: %s", image_id, sun["reason"])
        for c in circles:
            out.append({**c, "shading": {"status": "not_checked", "score": None, "score_raw": None, "reason": sun["reason"]}})
        counts["not_checked"] = len(circles)
    else:
        u = sun_vector(sun["azimuth_deg"], metadata["north_angle_deg"])
        for c in circles:
            shading = score_one(image, valid, c, u, sun["quality"], p)
            counts[shading["status"]] += 1
            out.append({**c, "shading": shading})

    report = {
        "module_version": MODULE_VERSION,
        "image_id": image_id,
        "checked": sun["usable"],
        "reason": sun["reason"],
        "sun_basis": sun["basis"],
        "azimuth_deg": sun["azimuth_deg"],
        "quality": sun["quality"],
        "incidence_deg": sun["incidence_deg"],
        "visual_check": sun["visual_check"],
        "sun_vector_xy": list(sun_vector(sun["azimuth_deg"], metadata["north_angle_deg"])) if sun["usable"] else None,
        "counts": counts,
        "params": p,
        "removed": 0,
    }
    return out, report


def filter_candidates(circles: list[dict], image, metadata: dict, params: dict) -> list[dict]:
    """Giữ nguyên hệ tọa độ và số vòng; chỉ thêm trường "shading" (S1-11 không lọc).

    Thiếu hướng nắng đủ tin cậy thì mọi vòng ghi not_checked kèm lý do và ghi log.
    params có thể chứa "valid_mask" (mặt nạ bool cùng kích thước ảnh) để bỏ pixel nodata.
    """
    scored, _ = score_candidates(circles, image, metadata, params)
    return scored


# ============================================================ S2-02: rà ứng viên
# Phân biệt vành hố với ranh giới bóng đổ và biên kết cấu. Mặc định CHỈ GẮN NHÃN;
# apply_filter chỉ loại khi người gọi bật rõ ràng các lớp cần loại, và mỗi vòng bị
# loại ghi lý do. Ngưỡng là giá trị ban đầu, phải đối chiếu trên nhãn đã kiểm chéo.

REVIEW_DEFAULTS = {
    "dark_level": 0.06,            # gray (B3) dưới mức này coi là bóng
    "shadow_min_area_px": 1500,    # vùng tối liền khối lớn hơn → bóng địa hình, không phải bóng trong hố nhỏ
    "shadow_edge_dist_px": 2,      # điểm biên cách vùng bóng lớn <= 2 px → ranh giới bóng
    "rim_band_px": 1.5,            # điểm biên trong |d − r| <= 1,5 px thuộc vòng
    "radial_tol_deg": 30.0,        # gradient lệch hướng xuyên tâm <= 30° → hợp vành tròn
    "angle_bins": 36,
    "min_radial_coverage": 0.5,    # vành hố: >= 50% số cung 10° có điểm biên xuyên tâm
    "min_rim_contrast": 1.5,       # |G| trên vành / trung vị |G| vành ngoài
    "max_shadow_edge_fraction": 0.5,
}
REVIEW_CLASSES = ("rim", "shadow_edge", "texture", "unclear")
SHADING_STATUSES = ("consistent", "inverted", "unclear", "not_checked")


def resolve_review_params(params: dict | None) -> dict:
    params = dict(params or {})
    unknown = set(params) - set(REVIEW_DEFAULTS)
    if unknown:
        raise ValueError("Tham số S2-02 không biết: " + ", ".join(sorted(unknown)))
    return {**REVIEW_DEFAULTS, **params}


def shadow_regions(gray: np.ndarray, edges: np.ndarray, valid: np.ndarray, p: dict) -> tuple[np.ndarray, np.ndarray]:
    """Vùng bóng lớn và các điểm biên nằm trên ranh giới của nó.

    Tìm vùng liền khối: THƯ VIỆN OpenCV connectedComponentsWithStats. Giãn vùng
    bằng phép co phần bù (erode tự viết của S1-08).
    """
    import cv2
    from src.preprocessing import erode

    dark = (np.asarray(gray) < p["dark_level"]) & valid
    _, labels, stats, _ = cv2.connectedComponentsWithStats(dark.astype(np.uint8), connectivity=8)
    big_ids = np.where(stats[:, cv2.CC_STAT_AREA] >= p["shadow_min_area_px"])[0]
    big = np.isin(labels, big_ids[big_ids != 0])
    near = ~erode(~big, int(p["shadow_edge_dist_px"]))
    return big, np.asarray(edges, dtype=bool) & near


def candidate_features(c: dict, mag: np.ndarray, theta: np.ndarray, edges: np.ndarray, shadow_edges: np.ndarray,
                       valid: np.ndarray, p: dict) -> dict:
    """[TỰ VIẾT] Đặc trưng một vòng: độ phủ biên xuyên tâm, tỉ lệ biên là ranh giới bóng, độ nổi của vành."""
    x, y, r = c["x"], c["y"], c["r"]
    xs, ys, _ = _pixels_in_ring(valid, x, y, r - p["rim_band_px"], r + p["rim_band_px"])
    on = edges[ys, xs]
    if not on.any():
        return {"edge_px": 0, "radial_coverage": 0.0, "shadow_edge_fraction": 0.0, "rim_contrast": 0.0}
    ang = np.arctan2(ys - y, xs - x)
    radial = np.abs(np.cos(theta[ys, xs] - ang)) >= math.cos(math.radians(p["radial_tol_deg"]))
    bins = ((ang + np.pi) / (2 * np.pi) * p["angle_bins"]).astype(int) % p["angle_bins"]
    rim = on & radial
    coverage = len(np.unique(bins[rim])) / p["angle_bins"]
    shadow_fraction = float(shadow_edges[ys, xs][on].mean())
    ax, ay, _ = _pixels_in_ring(valid, x, y, 1.3 * r, 2.0 * r)
    background = float(np.median(mag[ay, ax])) if len(ax) else 0.0
    rim_mag = float(mag[ys, xs][rim].mean()) if rim.any() else 0.0
    contrast = rim_mag / background if background > 1e-9 else (99.0 if rim_mag > 0 else 0.0)
    return {"edge_px": int(on.sum()), "radial_coverage": round(coverage, 3),
            "shadow_edge_fraction": round(shadow_fraction, 3), "rim_contrast": round(min(contrast, 99.0), 3)}


def classify_candidate(f: dict, p: dict) -> tuple[str, str]:
    """Lớp của một vòng theo đặc trưng hình học, kèm lý do. Không dùng điểm sáng–tối."""
    if f["edge_px"] == 0:
        return "unclear", "không có điểm biên trên vòng"
    if f["shadow_edge_fraction"] >= p["max_shadow_edge_fraction"]:
        return "shadow_edge", f"{f['shadow_edge_fraction']:.0%} điểm biên trên vòng là ranh giới vùng bóng lớn"
    if f["radial_coverage"] < p["min_radial_coverage"]:
        return "texture", f"biên xuyên tâm chỉ phủ {f['radial_coverage']:.0%} chu vi"
    if f["rim_contrast"] < p["min_rim_contrast"]:
        return "texture", f"vành không nổi hơn nền (|G| vành / nền = {f['rim_contrast']:.2f})"
    return "rim", f"biên xuyên tâm phủ {f['radial_coverage']:.0%} chu vi, vành nổi {f['rim_contrast']:.1f}× nền"


def review_candidates(circles: list[dict], pre: dict, params: dict | None = None) -> tuple[list[dict], dict]:
    """Thêm trường "review" = {class, reason, features} vào bản sao từng vòng. Không loại vòng nào.

    pre: kết quả preprocess() (cần gray, mag, theta, edges, valid_mask).
    """
    p = resolve_review_params(params)
    valid = np.asarray(pre["valid_mask"], dtype=bool)
    big, shadow_edges = shadow_regions(pre["gray"], pre["edges"], valid, p)
    out, counts = [], {k: 0 for k in REVIEW_CLASSES}
    for c in circles:
        f = candidate_features(c, pre["mag"], pre["theta"], pre["edges"], shadow_edges, valid, p)
        cls, reason = classify_candidate(f, p)
        counts[cls] += 1
        out.append({**c, "review": {"class": cls, "reason": reason, "features": f}})
    edges = int(np.asarray(pre["edges"]).sum())
    report = {"params": p, "counts": counts, "removed": 0,
              "shadow_area_fraction": round(float(big.mean()), 4),
              "edge_px": edges, "shadow_edge_px": int(shadow_edges.sum()),
              "shadow_edge_fraction_of_edges": round(int(shadow_edges.sum()) / edges, 4) if edges else 0.0}
    return out, report


def apply_filter(circles: list[dict], remove_classes=(), remove_shading=()) -> tuple[list[dict], list[dict]]:
    """LỌC THẬT: loại vòng có review.class thuộc remove_classes hoặc shading.status thuộc remove_shading.

    Trả (giữ lại, bị loại); mỗi vòng bị loại có "filter_reason". Gọi không tham số thì không loại gì.
    """
    if isinstance(remove_classes, str) or isinstance(remove_shading, str):
        raise ValueError("remove_classes / remove_shading phải là tuple hoặc list, không phải chuỗi.")
    bad = set(remove_classes) - set(REVIEW_CLASSES)
    if bad:
        raise ValueError("Lớp không biết: " + ", ".join(sorted(bad)))
    bad = set(remove_shading) - set(SHADING_STATUSES)
    if bad:
        raise ValueError("Nhãn sáng–tối không biết: " + ", ".join(sorted(bad)) + f" (hợp lệ: {', '.join(SHADING_STATUSES)})")
    kept, removed = [], []
    for c in circles:
        cls = (c.get("review") or {}).get("class")
        st = (c.get("shading") or {}).get("status")
        why = []
        if cls in remove_classes:
            why.append(f"review={cls}")
        if st in remove_shading:
            why.append(f"shading={st}")
        if why:
            removed.append({**c, "filter_reason": "; ".join(why)})
        else:
            kept.append(c)
    return kept, removed


# ============================================================ S2-05: lọc vòng trùng
# Hough có thể tìm cùng một hố nhiều lần mà NMS của S1-07 (tâm <= 4 px VÀ bán kính
# lệch <= 2 px) không gộp được. Hai dạng đã thấy trên ảnh thật:
#   - vòng nhỏ lồng trong vành thật: mép bóng lòng hố (STT 13: M8 r=6 trong M32 r=9;
#     M19 r=6 trong M15 r=10);
#   - hai vòng cùng cỡ, tâm lệch nhau (STT 17: M66/M67, r=7, tâm cách 5 px).
# Quy tắc (tự viết):
#   Cặp (A, B), R = max(rA, rB), r = min:  trùng nếu  d(tâm) <= max_center_frac·R  VÀ  r/R >= min_radius_ratio.
#   - Hai hố cạnh nhau/chồng mép có d >= khoảng R + r > 0,75R → không bị gộp.
#   - Hố nhỏ nằm trong hố lớn có r/R < 0,5 → không bị gộp.
#   Giữ vòng theo thứ tự ưu tiên: (1) vòng đủ tin (tỉ lệ phiếu >= min_outer_vote_ratio
#   và không bị S2-02 xếp lớp không tin cậy); (2) vòng lớn hơn — vòng trong thường là
#   mép bóng lòng hố; (3) tỉ lệ phiếu cao hơn; (4) số phiếu; (5) crater_id.
#   Duyệt tham lam theo thứ tự đó; vòng trùng với một vòng đã giữ thì bị loại, ghi duplicate_of.

DEDUPE_DEFAULTS = {
    "max_center_frac": 0.75,
    "min_radius_ratio": 0.5,
    "min_outer_vote_ratio": 0.35,          # cùng ý nghĩa min_vote_ratio của Hough
    "unreliable_classes": ("texture",),    # lớp S2-02 không đủ tin để làm vòng giữ lại
    "angle_step_deg": 1.0,                 # phải khớp Hough để tính đúng số điểm trên chu vi
}


def resolve_dedupe_params(params: dict | None) -> dict:
    params = dict(params or {})
    unknown = set(params) - set(DEDUPE_DEFAULTS)
    if unknown:
        raise ValueError("Tham số S2-05 không biết: " + ", ".join(sorted(unknown)))
    p = {**DEDUPE_DEFAULTS, **params}
    if not 0 < p["max_center_frac"] <= 2 or not 0 < p["min_radius_ratio"] <= 1:
        raise ValueError("Cần 0 < max_center_frac <= 2 và 0 < min_radius_ratio <= 1.")
    bad = set(p["unreliable_classes"]) - set(REVIEW_CLASSES)
    if isinstance(p["unreliable_classes"], str) or bad:
        raise ValueError("unreliable_classes phải là tuple các lớp S2-02.")
    return p


def vote_ratio(c: dict, angle_step_deg: float = 1.0) -> float | None:
    """Số phiếu / số điểm pixel khác nhau trên chu vi bán kính r (đúng mẫu số Hough dùng)."""
    from src.hough import _circle_offsets

    if c.get("votes") is None:
        return None
    angles = np.deg2rad(np.arange(0.0, 360.0, angle_step_deg))
    return c["votes"] / len(_circle_offsets(int(round(c["r"])), angles))


def duplicate_pair(a: dict, b: dict, p: dict) -> tuple[bool, float, float]:
    """(trùng?, d/R, r/R) cho một cặp vòng."""
    big, small = (a, b) if a["r"] >= b["r"] else (b, a)
    d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
    center, ratio = d / big["r"], small["r"] / big["r"]
    return center <= p["max_center_frac"] and ratio >= p["min_radius_ratio"], round(center, 3), round(ratio, 3)


def dedupe_circles(circles: list[dict], params: dict | None = None) -> tuple[list[dict], list[dict], dict]:
    """LỌC TRÙNG: trả (giữ lại theo thứ tự gốc, bị loại, báo cáo).

    Mỗi vòng bị loại có "duplicate_of" (crater_id vòng giữ) và "dedupe_reason".
    Không đổi trường nào của vòng giữ lại.
    """
    p = resolve_dedupe_params(params)

    def reliable(c):
        vr = vote_ratio(c, p["angle_step_deg"])
        cls = (c.get("review") or {}).get("class")
        return (vr is None or vr >= p["min_outer_vote_ratio"]) and cls not in p["unreliable_classes"]

    def key(c):
        vr = vote_ratio(c, p["angle_step_deg"]) or 0.0
        return (not reliable(c), -c["r"], -vr, -(c.get("votes") or 0), str(c["crater_id"]))

    kept_ids, removed, pairs = [], [], []
    by_id = {c["crater_id"]: c for c in circles}
    for c in sorted(circles, key=key):
        hit = None
        for kid in kept_ids:
            same, center, ratio = duplicate_pair(c, by_id[kid], p)
            if same:
                hit = (kid, center, ratio)
                break
        if hit is None:
            kept_ids.append(c["crater_id"])
            continue
        kid, center, ratio = hit
        why = (f"trùng {kid}: tâm lệch {center:.2f}R, r/R = {ratio:.2f}; giữ {kid} vì "
               + ("vòng kia đủ tin còn vòng này không" if reliable(by_id[kid]) and not reliable(c)
                  else "vòng kia lớn hơn" if by_id[kid]["r"] > c["r"] else "cùng cỡ, tỉ lệ phiếu không thấp hơn"))
        removed.append({**c, "duplicate_of": kid, "dedupe_reason": why})
        pairs.append({"kept": kid, "removed": c["crater_id"], "center_over_R": center, "r_over_R": ratio})
    keep = set(kept_ids)
    kept = [c for c in circles if c["crater_id"] in keep]
    report = {"params": {**p, "unreliable_classes": list(p["unreliable_classes"])},
              "n_in": len(circles), "n_kept": len(kept), "n_removed": len(removed), "pairs": pairs}
    return kept, removed, report
