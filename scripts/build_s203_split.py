"""S2-03: Tao manifest phan chia tap dieu chinh (tuning) / kiem tra (holdout).

Quy tac phan tap:
- Cac crops cung product_id (cung TIF goc) luon vao cung mot tap.
  Dam bao crops chong lap hoac cung dia diem khac goc nang KHONG bi tach
  vao 2 tap khac nhau.
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
# Holdout groups (theo product_id):
# - M132732855L/R: Ap16 grazing West ~87.7-87.78 deg (extreme shadow)
# - M113853974R  : Ap16 East candidate 54.72 deg (phan biet huong nang)
# - AP15LOC      : Apollo 15 LOC mosaic (quality=none, khong co sun_inc)
# - LUNOKOD2     : Lunokhod 2 Low-Sun (quality=none, da dang vung)
# ---------------------------------------------------------------------------
HOLDOUT_PRODUCT_IDS: set[str] = {
    "M132732855L",
    "M132732855R",
    "M113853974R",
    "NAC_ROI_APOLLO15LOC_E252N0018_20M",
    "NAC_ROI_LUNOKOD2LOA_E259N0306_20M",
}

CENTER_TOLERANCE = 0.5  # fraction of ref radius, khop matching.py


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_ref(image_id: str) -> dict | None:
    """Tim file nhan tham chieu cho image_id; tra None neu chua co."""
    fp = REF_LABEL_DIR / f"{image_id}_craters_catalogue.json"
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None


def build_split() -> None:
    crops: list[dict] = json.loads(CROPS_JSON.read_text(encoding="utf-8"))

    # Gom crops theo product_id
    groups: dict[str, list[dict]] = {}
    for c in crops:
        groups.setdefault(c["product_id"], []).append(c)

    tuning_groups: list[str] = []
    holdout_groups: list[str] = []
    for pid in sorted(groups):
        if pid in HOLDOUT_PRODUCT_IDS:
            holdout_groups.append(pid)
        else:
            tuning_groups.append(pid)

    def _make_entries(glist: list[str], split: str) -> list[dict]:
        out = []
        for pid in glist:
            for crop in groups[pid]:
                iid = crop["image_id"]
                ref = _find_ref(iid)
                has = ref is not None
                circles = ref.get("circles", []) if ref else []
                n_unc = sum(
                    1 for c in circles if "uncertain" in c.get("crater_id", "")
                )
                out.append(
                    {
                        "image_id": iid,
                        "split": split,
                        "product_id": pid,
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
                        "label_status": "sparse_unreviewed" if has else "unlabeled",
                        "n_labels": len(circles),
                        "n_uncertain": n_unc,
                        "label_note": (
                            "Nhan thua thu cong S1-10; chua kiem cheo. "
                            "Recall do tren nhan da biet, khong suy F1 toan anh."
                            if has
                            else "Chua co nhan tham chieu."
                        ),
                    }
                )
        return out

    tuning = _make_entries(tuning_groups, "tuning")
    holdout = _make_entries(holdout_groups, "holdout")
    all_entries = tuning + holdout

    stats = {
        "total_images": len(all_entries),
        "tuning_images": len(tuning),
        "holdout_images": len(holdout),
        "tuning_groups": len(tuning_groups),
        "holdout_groups": len(holdout_groups),
        "labeled_tuning": sum(1 for e in tuning if e["has_reference_label"]),
        "labeled_holdout": sum(1 for e in holdout if e["has_reference_label"]),
    }

    manifest = {
        "schema_version": "s203-split-1",
        "task_id": "S2-03",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "crops_source": "data/s106_bundle/crops.json",
        "crops_sha256": _sha256_file(CROPS_JSON),
        "split_strategy": "group_by_product_id",
        "split_note": (
            "Crops tu cung TIF goc (product_id) luon vao cung tap. "
            "Khong co crop chong lap hoac cung dia diem o khac nhom."
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
        f"Tuning : {len(tuning)} crops ({len(tuning_groups)} groups),"
        f" {stats['labeled_tuning']} co nhan"
    )
    print(
        f"Holdout: {len(holdout)} crops ({len(holdout_groups)} groups),"
        f" {stats['labeled_holdout']} co nhan"
    )
    print(f"Manifest : {manifest_path}")
    print(f"LabelIdx : {label_index_path}")


if __name__ == "__main__":
    build_split()
