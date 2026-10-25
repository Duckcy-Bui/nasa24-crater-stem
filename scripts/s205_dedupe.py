"""S2-05: chạy lọc vòng trùng trên ảnh thật và đối chiếu với nhãn S2-02.

    python scripts/s205_dedupe.py
    python scripts/s205_dedupe.py --images moon_ap16_m132732855l_c01 --processed-dir <thư mục>

Ghi vào docs/evidence/s2-05/:
  <image_id>_cap_trung.png   từng cặp trùng: vòng giữ (xanh) và vòng bị loại (đỏ), phóng to
  <image_id>.csv             vòng bị loại: duplicate_of, d/R, r/R, lý do, nhãn người hai vòng
  tong_hop.json / .csv       mỗi ảnh: số vòng vào/ra, số cặp, đối chiếu nhãn (gộp đúng / mất hố)
Đối chiếu dùng data/s202_labels/<image_id>.json nếu có.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from s202_review import human_labels, load_labels, run  # noqa: E402
from src.postprocessing import dedupe_circles, vote_ratio  # noqa: E402

OUT = ROOT / "docs" / "evidence" / "s2-05"
IMAGES = ["moon_ap16_m132732855l_c01", "moon_ap16_m109134835l_c01", "moon_marefrig_loc_c01"]


def pairs_figure(path: Path, gray: np.ndarray, kept: list[dict], removed: list[dict], human: dict, image_id: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    by_id = {c["crater_id"]: c for c in kept}
    n = max(1, len(removed))
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3.4 * cols, 3.6 * rows), squeeze=False)
    for ax in axes.ravel():
        ax.set_xticks([]); ax.set_yticks([])
    if not removed:
        axes[0][0].text(0.5, 0.5, "không có cặp trùng", ha="center", va="center")
    for ax, c in zip(axes.ravel(), removed):
        k = by_id[c["duplicate_of"]]
        pad = int(max(k["r"], c["r"]) * 2.5) + 8
        x0, x1 = max(0, int(k["x"]) - pad), min(512, int(k["x"]) + pad)
        y0, y1 = max(0, int(k["y"]) - pad), min(512, int(k["y"]) + pad)
        ax.imshow(gray[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=1, extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5))
        ax.add_patch(Circle((k["x"], k["y"]), k["r"], fill=False, color="#2ecc71", lw=1.6))
        ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color="#ff4d4d", lw=1.2, ls="--"))
        ax.set_title(f"giữ {k['crater_id']} r={k['r']:.0f} ({human.get(k['crater_id'], '–')})\n"
                     f"loại {c['crater_id']} r={c['r']:.0f} ({human.get(c['crater_id'], '–')})", fontsize=8)
    fig.suptitle(f"S2-05 · {image_id} · xanh = giữ, đỏ nét đứt = loại (trong ngoặc: nhãn người)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=70)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S2-05: lọc vòng trùng trên ảnh thật")
    parser.add_argument("--images", nargs="*", default=IMAGES)
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for image_id in args.images:
        r = run(image_id, Path(args.processed_dir))
        labels = load_labels(image_id)
        if labels and not any(c.get("label") for c in labels["candidates"]):
            labels = None  # mẫu nhãn trống (toàn null) = chưa có nhãn
        human = human_labels(labels, r["circles"])
        kept, removed, report = dedupe_circles(r["circles"])
        by_id = {c["crater_id"]: c for c in kept}
        merged_ok = sum(human.get(c["crater_id"]) == "rim" and human.get(c["duplicate_of"]) == "rim" for c in removed)
        lost = [c["crater_id"] for c in removed if human.get(c["crater_id"]) == "rim" and human.get(c["duplicate_of"]) != "rim"]
        rims_before = sum(v == "rim" for v in human.values())
        rims_after = sum(human.get(c["crater_id"]) == "rim" for c in kept)
        pairs_figure(OUT / f"{image_id}_cap_trung.png", r["pre"]["gray"], kept, removed, human, image_id)
        with (OUT / f"{image_id}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["loai", "r_loai", "ty_le_phieu_loai", "nhan_loai", "giu", "r_giu", "ty_le_phieu_giu", "nhan_giu",
                        "lop_may_giu", "d_chia_R", "r_chia_R", "ly_do"])
            for c, pr in zip(removed, report["pairs"]):
                k = by_id[c["duplicate_of"]]
                w.writerow([c["crater_id"], c["r"], round(vote_ratio(c), 3), human.get(c["crater_id"], ""), k["crater_id"], k["r"],
                            round(vote_ratio(k), 3), human.get(k["crater_id"], ""), k["review"]["class"],
                            pr["center_over_R"], pr["r_over_R"], c["dedupe_reason"]])
        row = {"image_id": image_id, "co_nhan": bool(labels), "nhan_da_kiem_cheo": bool((labels or {}).get("reviewed_by")),
               "vong_vao": report["n_in"], "vong_ra": report["n_kept"], "loai_trung": report["n_removed"],
               "ho_that_truoc": rims_before if labels else "", "vong_ho_that_sau": rims_after if labels else "",
               "gop_dung_cung_ho": merged_ok if labels else "", "mat_ho_that": len(lost) if labels else "",
               "mat_ho_that_id": " ".join(lost), "giay_hough": r["seconds"]["hough"]}
        summary.append(row)
        print(f"{image_id:28s} vào {row['vong_vao']} → ra {row['vong_ra']} (loại {row['loai_trung']}) | "
              f"gộp đúng {row['gop_dung_cung_ho']} | mất hố thật {row['mat_ho_that']} {row['mat_ho_that_id']}")
    (OUT / "tong_hop.json").write_text(json.dumps({"params": report["params"], "rows": summary}, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    with (OUT / "tong_hop.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]), lineterminator="\n")
        w.writeheader(); w.writerows(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
