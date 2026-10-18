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
    p = resolve_params(params)
    image = np.asarray(image, dtype=np.float32)
    valid = np.ones(image.shape, dtype=bool) if valid_mask is None else np.asarray(valid_mask, dtype=bool)
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
    """
    scored, _ = score_candidates(circles, image, metadata, params)
    return scored
