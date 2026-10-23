"""S2-02: thử có kiểm soát làm trơn / Canny / tương phản trên ảnh lỗi và ảnh khác.

    python scripts/s202_experiments.py
    python scripts/s202_experiments.py --images moon_ap16_m132732855l_c01 --processed-dir <thư mục>

Mỗi cấu hình chỉ đổi MỘT tham số so với mặc định S1-04 (src/preprocessing.py DEFAULT_PARAMS).
Hough và tham số rà ứng viên giữ nguyên. Ghi docs/evidence/s2-02/thu_nghiem.csv và thu_nghiem.json:
tham số, thời gian từng phần, số pixel biên, tỉ lệ biên là ranh giới bóng, số ứng viên theo lớp máy,
bán kính, và — nếu data/s202_labels/<image_id>.json đã có nhãn — số hố thật (nhãn rim) mà cấu hình
vẫn tìm lại được. Cột xau_di liệt kê các tiêu chí xấu hơn mặc định.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import logging
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s202_review import EVIDENCE, load_labels, match, run  # noqa: E402

IMAGES = {"moon_ap16_m132732855l_c01": "ảnh lỗi: STT 13, nắng xiên 87,7°",
          "moon_ap16_m109134835l_c01": "ảnh khác: STT 17, nắng gần đứng 7,64°",
          "moon_marefrig_loc_c01": "ảnh khác: mosaic Mare Frigoris 20 m/px"}
CONFIGS = [("mac_dinh", {}),
           ("gauss_1.0", {"gauss_sigma": 1.0}), ("gauss_2.0", {"gauss_sigma": 2.0}), ("gauss_2.5", {"gauss_sigma": 2.5}),
           ("canny_85", {"canny_high_pct": 85}), ("canny_95", {"canny_high_pct": 95}),
           ("clahe_1", {"clahe_clip": 1.0}), ("clahe_4", {"clahe_clip": 4.0})]


def rims_found(circles: list[dict], refs: list[dict]) -> int:
    return sum(any(match(c, ref) for c in circles) for ref in refs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S2-02: thử có kiểm soát tiền xử lý")
    parser.add_argument("--images", nargs="*", default=list(IMAGES))
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    rows = []
    for image_id in args.images:
        labels = load_labels(image_id)
        refs = [l for l in (labels or {}).get("candidates", []) if l.get("label") == "rim"]
        base = None
        for name, params in CONFIGS:
            r = run(image_id, Path(args.processed_dir), params)
            k = r["review"]["counts"]
            radii = np.array([c["r"] for c in r["circles"]]) if r["circles"] else np.zeros(1)
            row = {"image_id": image_id, "anh": IMAGES.get(image_id, ""), "cau_hinh": name,
                   "tham_so_doi": json.dumps(params, ensure_ascii=False),
                   "giay_tien_xu_ly": r["seconds"]["preprocess"], "giay_hough": r["seconds"]["hough"],
                   "giay_ra_soat": r["seconds"]["shading_review"],
                   "canny_low": round(r["pre"]["params"]["canny_low"], 1), "canny_high": round(r["pre"]["params"]["canny_high"], 1),
                   "bien_px": r["review"]["edge_px"], "ty_le_bien_bong": r["review"]["shadow_edge_fraction_of_edges"],
                   "ung_vien": len(r["circles"]), "rim": k["rim"], "shadow_edge": k["shadow_edge"], "texture": k["texture"],
                   "r_trung_vi": float(np.median(radii)), "r_lon_nhat": float(radii.max()),
                   "ho_that_co_nhan": len(refs) if labels else "",
                   "ho_that_tim_lai": rims_found(r["circles"], refs) if refs else ""}
            if base is None:
                base, row["xau_di"] = row, ""
            else:
                worse = []
                if refs and row["ho_that_tim_lai"] < base["ho_that_tim_lai"]:
                    worse.append(f"mất hố thật có nhãn ({row['ho_that_tim_lai']}/{len(refs)} so với {base['ho_that_tim_lai']})")
                if row["rim"] < 0.8 * base["rim"]:
                    worse.append(f"ứng viên lớp rim giảm {base['rim']}→{row['rim']}")
                if row["shadow_edge"] > base["shadow_edge"]:
                    worse.append(f"ứng viên bám bóng tăng {base['shadow_edge']}→{row['shadow_edge']}")
                if row["ty_le_bien_bong"] > base["ty_le_bien_bong"] + 0.02:
                    worse.append("tỉ lệ biên là ranh giới bóng tăng")
                if row["giay_hough"] > 1.5 * base["giay_hough"]:
                    worse.append(f"Hough chậm hơn {row['giay_hough'] / base['giay_hough']:.1f}×")
                row["xau_di"] = "; ".join(worse)
            rows.append(row)
            print(f"{image_id[:22]:22s} {name:10s} biên {row['bien_px']:6d} bóng {row['ty_le_bien_bong']:.2f} "
                  f"rim/bóng/kết cấu {row['rim']:3d}/{row['shadow_edge']:3d}/{row['texture']:3d} r_max {row['r_lon_nhat']:5.1f} "
                  f"hố thật {row['ho_that_tim_lai']}/{row['ho_that_co_nhan']} hough {row['giay_hough']:5.1f}s | {row['xau_di']}")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    # Chạy một phần ảnh thì giữ lại dòng của các ảnh khác từ lần chạy trước.
    previous = EVIDENCE / "thu_nghiem.json"
    if previous.exists():
        done = {r["image_id"] for r in rows}
        old = [r for r in json.loads(previous.read_text(encoding="utf-8"))["rows"] if r["image_id"] not in done]
        rows = sorted(old + rows, key=lambda r: (list(IMAGES).index(r["image_id"]) if r["image_id"] in IMAGES else 99,
                                                 [n for n, _ in CONFIGS].index(r["cau_hinh"])))
    with (EVIDENCE / "thu_nghiem.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    (EVIDENCE / "thu_nghiem.json").write_text(json.dumps({"configs": CONFIGS, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    print(f"Đã ghi {(EVIDENCE / 'thu_nghiem.csv').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
