"""S2-03: Tao manifest phan chia tap dieu chinh (tuning) / kiem tra (holdout).

Quy tac phan tap (v3 - group_by_ground_region):
- Nhom theo vung mat dat thuc te (ground region):
  + Toan bo 11 anh Apollo 16 deu chup tai khu vuc Apollo 16 (NAC_PHO_E090S0155)
    va co tam cach nhau < 1.5 km (trong khi moi crop rong ~1 km -> tat ca chong lap
    mat dat voi nhau). Vi STT 13 (moon_ap16_m132732855l_c01) da dung chon filter o S2-02
    nen TOAN BO 11 anh Apollo 16 bat buoc phai vao tap tuning de tranh ro ri mat dat.
  + Tap holdout gom 3 vung mat dat hoan toan tach biet (cach tap tuning >= 50 km):
    * Apollo 15 Low-Sun (NAC_ROI_APOLLO15LOC_E252N0018_20M - 3 crops, cach Ap15 HIA ~50 km)
    * Lunokhod 2 Low-Sun (NAC_ROI_LUNOKOD2LOA_E259N0306_20M - 2 crops, cach > 700 km)
    * Mare Frigoris Basalt (NAC_ROI_MAREFRIGLOA_E598N0261_20M - 3 crops, cach > 1000 km)
- Khong co bat ky anh holdout nao cach anh tuning duoi 50 km (0% ground overlap).
- Holdout KHONG duoc dung de chinh tham so Hough hoac nguong shading.
- Nhan tham chieu thua (sparse) chi do recall tren nhan da biet.
  Khong suy Precision/F1 toan anh tu nhan thua.
- Ghep ho mot-mot, tam lech <= 0.5 x r_ref (CENTER_TOLERANCE = 0.5,
  khop src/matching.py).
- Nhan hien tai la 'sparse_unreviewed'; Tien kiem cheo overlay truoc khi
  dung lam ground truth chinh thuc.

Chay:
    python scripts/build_s203_split.py
    # --> data/s203_split/manifest_split.json
    # --> data/s203_split/label_index.json
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROPS_JSON = ROOT / "data" / "s106_bundle" / "crops.json"
REF_LABEL_DIR = ROOT / "data" / "reference_labels"
OUT_DIR = ROOT / "data" / "s203_split"

# ---------------------------------------------------------------------------
# Holdout ground regions (doc lap hoan toan ve dia ly, cach tuning >= 50 km):
#   - AP15LOC      : Apollo 15 LOC mosaic (3 crops, cach Ap15 HIA ~50 km)
#   - LUNOKOD2     : Lunokhod 2 Low-Sun (2 crops, cach xa > 700 km)
#   - MAREFRIG     : Mare Frigoris Basalt (3 crops, cach xa > 1000 km)
# Tong holdout: 8 crops (~30.8%), 3 vung mat dat doc lap.
#
# Tap tuning (18 crops, ~69.2%):
#   - Toan bo 11 anh Apollo 16 (NAC_PHO_E090S0155) - tap trung trong ban kinh 1.5 km
#   - Apollo 15 HIA (3 crops)
#   - Lunokhod 1 Low-Sun (2 crops)
#   - Van de Graaff High-Sun (2 crops)
# ---------------------------------------------------------------------------
HOLDOUT_PRODUCT_IDS: set[str] = {
    "NAC_ROI_APOLLO15LOC_E252N0018_20M",
    "NAC_ROI_LUNOKOD2LOA_E259N0306_20M",
    "NAC_ROI_MAREFRIGLOA_E598N0261_20M",
}

# Ảnh đã dùng tại S2-02 (#19) để lựa chọn cách lọc -> bắt buộc tuning
FORCED_TUNING_IMAGE_IDS: set[str] = {
    "moon_ap16_m132732855l_c01",  # STT 13 - đã dùng chọn filter S2-02
}

CENTER_TOLERANCE = 0.5  # fraction of ref radius, khop matching.py


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_ref(image_id: str) -> dict | None:
    """Tim file nhan tham chieu cho image_id; tra None neu chua co."""
    fp = REF_LABEL_DIR / f"{image_id}_craters_catalogue.json"
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None


def _label_status(ref: dict | None) -> str:
    """Tra trang thai nhan tu nguon thuc te, khong ghi cung trong manifest."""
    if ref is None:
        return "unlabeled"
    source = str(ref.get("reference_source") or "").lower()
    if "reviewed by" in source and "unreviewed" not in source:
        return "reviewed"
    return "sparse_unreviewed"


def _ground_patch_key(crop: dict) -> str:
    """Key xac dinh vung mat dat:
    - Voi NAC_PHO (Apollo 16): tat ca anh deu chup tren footprint NAC_PHO_E090S0155
      (cac tam cach nhau < 1.5 km, crop rong ~1 km -> chong lap dia ly tren mat dat)
      -> phai vao cung mot key vung mat dat.
    - Voi NAC_ROI (mosaics): moi product_id dai dien cho mot khu vuc mat dat rieng.
    """
    file = crop["file"]
    if file.startswith("NAC_PHO_"):
        basename = file.split(".")[0]
        parts = basename.rsplit("_", 1)
        return parts[0] if len(parts) == 2 else basename
    return crop["product_id"]


def build_split() -> None:
    crops: list[dict] = json.loads(CROPS_JSON.read_text(encoding="utf-8"))

    # Bước 1: Gom theo ground_patch (file + x0 + y0)
    patch_groups: dict[str, list[dict]] = {}
    for c in crops:
        key = _ground_patch_key(c)
        patch_groups.setdefault(key, []).append(c)

    # Bước 2: Xác định tap cho mỗi patch
    # Một patch vào holdout KHI TẤT CẢ product_id của nó đều trong
    # HOLDOUT_PRODUCT_IDS VÀ không có image_id nào trong FORCED_TUNING_IMAGE_IDS.
    tuning_patches: list[str] = []
    holdout_patches: list[str] = []

    for patch_key in sorted(patch_groups):
        patch_crops = patch_groups[patch_key]
        # Kiểm tra forced tuning
        has_forced_tuning = any(
            c["image_id"] in FORCED_TUNING_IMAGE_IDS for c in patch_crops
        )
        # Kiểm tra tất cả product_id đều là holdout
        all_holdout = all(c["product_id"] in HOLDOUT_PRODUCT_IDS for c in patch_crops)

        if all_holdout and not has_forced_tuning:
            holdout_patches.append(patch_key)
        else:
            tuning_patches.append(patch_key)

    def _make_entries(plist: list[str], split: str) -> list[dict]:
        out = []
        for pk in plist:
            for crop in patch_groups[pk]:
                iid = crop["image_id"]
                ref = _find_ref(iid)
                has = ref is not None
                label_status = _label_status(ref)
                circles = ref.get("circles", []) if ref else []
                n_unc = sum(
                    1 for c in circles if "uncertain" in c.get("crater_id", "")
                )
                forced_note = (
                    " Da dung tai S2-02 de chon filter -> buoc vao tuning."
                    if iid in FORCED_TUNING_IMAGE_IDS
                    else ""
                )
                out.append(
                    {
                        "image_id": iid,
                        "split": split,
                        "product_id": crop["product_id"],
                        "ground_patch": pk,
                        "region_group": crop["region_group"],
                        "sun_quality": (
                            "measured" if crop.get("sun_inc") is not None else "none"
                        ),
                        "sun_inc_deg": crop.get("sun_inc"),
                        "sun_side": (
                            crop.get("sun_side") or crop.get("sun_side_candidate")
                        ),
                        "d_min_m": crop["d_min_m"],
                        "d_max_m": crop["d_max_m"],
                        "has_reference_label": has,
                        "reference_label_file": (
                            f"{iid}_craters_catalogue.json" if has else None
                        ),
                        "label_status": label_status,
                        "n_labels": len(circles),
                        "n_uncertain": n_unc,
                        "label_note": (
                            (
                                "Nhan thua thu cong S1-10; da kiem cheo. "
                                if label_status == "reviewed"
                                else "Nhan thua thu cong S1-10; chua kiem cheo. "
                            )
                            + "Recall do tren nhan da biet, khong suy F1 toan anh."
                            + forced_note
                            if has
                            else "Chua co nhan tham chieu."
                        ),
                    }
                )
        return out

    tuning = _make_entries(tuning_patches, "tuning")
    holdout = _make_entries(holdout_patches, "holdout")
    all_entries = tuning + holdout

    # Đếm số lượng ground patches duy nhất
    tuning_patch_count = len(tuning_patches)
    holdout_patch_count = len(holdout_patches)

    stats = {
        "total_images": len(all_entries),
        "tuning_images": len(tuning),
        "holdout_images": len(holdout),
        "tuning_ground_patches": tuning_patch_count,
        "holdout_ground_patches": holdout_patch_count,
        "labeled_tuning": sum(1 for e in tuning if e["has_reference_label"]),
        "labeled_holdout": sum(1 for e in holdout if e["has_reference_label"]),
    }

    manifest = {
        "schema_version": "s203-split-1",
        "task_id": "S2-03",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "crops_source": "data/s106_bundle/crops.json",
        "crops_sha256": _sha256_file(CROPS_JSON),
        "split_strategy": "group_by_ground_patch",
        "split_note": (
            "Anh cung vung mat dat (cung file goc + cung offset crop x0,y0) "
            "luon vao cung mot tap, bat ke product_id khac nhau. "
            "Tieu chi nay dam bao crops chong lap hoac cung dia diem duoi goc "
            "nang khac nhau khong bi tach vao 2 tap. "
            "Anh da dung chon filter o S2-02 (m132732855l_c01) buoc vao tuning."
        ),
        "matching_rules": {
            "algorithm": "one_to_one_hungarian",
            "center_tolerance": CENTER_TOLERANCE,
            "center_tolerance_unit": "fraction_of_reference_radius",
            "description": (
                "Moi vong du doan khop toi da mot nhan tham chieu khi "
                "khoang cach tam <= 0.5 x r_ref. "
                "Trong cac phuong an nhieu cap nhat, chon tong khoang cach "
                "(chuan hoa) nho nhat. Khop voi src/matching.py CENTER_TOLERANCE."
            ),
            "recall_note": (
                "Nhan thua: recall tinh tren nhan da biet. "
                "Precision va F1 toan anh KHONG duoc suy tu nhan thua."
            ),
            "cross_review_required": True,
            "cross_review_assignee": "Nguyen Manh Tien",
        },
        "statistics": stats,
        "images": all_entries,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "manifest_split.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Label index (tien tra cuu khi danh gia)
    label_index: dict[str, dict] = {}
    for e in all_entries:
        if e["has_reference_label"]:
            ref = _find_ref(e["image_id"])
            circles = ref.get("circles", []) if ref else []
            n_unc = sum(
                1 for c in circles if "uncertain" in c.get("crater_id", "")
            )
            label_index[e["image_id"]] = {
                "split": e["split"],
                "ground_patch": e["ground_patch"],
                "label_file": e["reference_label_file"],
                "n_circles": len(circles),
                "n_certain": len(circles) - n_unc,
                "n_uncertain": n_unc,
                "label_status": e["label_status"],
                "radius_range_px": (
                    [min(c["r"] for c in circles), max(c["r"] for c in circles)]
                    if circles
                    else [None, None]
                ),
            }
    label_index_path = OUT_DIR / "label_index.json"
    label_index_path.write_text(
        json.dumps(label_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Tuning : {len(tuning)} crops ({tuning_patch_count} ground patches),"
        f" {stats['labeled_tuning']} co nhan"
    )
    print(
        f"Holdout: {len(holdout)} crops ({holdout_patch_count} ground patches),"
        f" {stats['labeled_holdout']} co nhan"
    )
    print(f"Manifest : {manifest_path}")
    print(f"LabelIdx : {label_index_path}")

    # Kiểm tra: không có ground_patch nào vừa tuning vừa holdout
    tuning_patches_set = set(tuning_patches)
    holdout_patches_set = set(holdout_patches)
    overlap = tuning_patches_set & holdout_patches_set
    if overlap:
        raise RuntimeError(f"BUG: ground patches bi tach 2 tap: {overlap}")
    print("OK: Khong co ground patch nao bi tach giua tuning va holdout.")


if __name__ == "__main__":
    build_split()
