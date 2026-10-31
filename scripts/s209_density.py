"""S2-09: đếm hố và so mật độ hai vùng (Lunokhod 1 và Mare Frigoris, cùng 20 m/px).

    python scripts/s209_density.py              # số liệu từ đếm tay + máy để đối chiếu
    python scripts/s209_density.py --no-machine # bỏ phần chạy Hough (nhanh)

Đầu vào: data/s209_counts/regions.json (vùng đếm, dải D) và <image_id>_count.json
(đếm tay đầy đủ trong vùng đếm, định dạng S1-05 source="catalogue").
Ghi docs/evidence/s2-09/: bang_dem.csv, so_sanh.json, histogram.png, tich_luy.png,
vung_dem.png, may_so_voi_tay.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json  # noqa: E402
from src.statistics import compare_regions, count_mask, region_count, size_frequency  # noqa: E402

COUNTS = ROOT / "data" / "s209_counts"
OUT = ROOT / "docs" / "evidence" / "s2-09"
COLORS = {"lunokhod1": "#1f6feb", "marefrig": "#d1495b"}


def load_region(key: str, cfg: dict, processed: Path) -> list[dict]:
    crops = []
    for iid, m in cfg["crops"].items():
        meta = read_json(processed / f"{iid}.json")
        vpath = processed / f"{iid}_valid_mask.npy"
        crops.append({"metadata": meta, "crater_set": read_json(COUNTS / f"{iid}_count.json"),
                      "mask": count_mask(m["keep"], m["exclude"]),
                      "valid": np.load(vpath).astype(bool) if vpath.exists() else None})
    return crops


def machine_sets(crops: list[dict], processed: Path) -> list[dict]:
    """Hough mặc định + lọc texture (S2-02) + lọc trùng (S2-05) trên từng ô; trả crater_set máy."""
    from src.hough import detect_circles, resolve_hough_params
    from src.pipeline import load_image, radius_range
    from src.postprocessing import apply_filter, dedupe_circles, review_candidates
    from src.preprocessing import preprocess

    logging.disable(logging.WARNING)
    out = []
    for c in crops:
        iid = c["metadata"]["image_id"]
        meta, image, valid = load_image(iid, processed)
        t = time.perf_counter()
        pre = preprocess(image, meta, None, valid_mask=valid)
        h = resolve_hough_params({})
        raw = detect_circles(pre["edges"], *radius_range(meta, h), h, theta=pre["theta"])
        reviewed, _ = review_candidates(raw, pre)
        kept, _ = apply_filter(reviewed, remove_classes=("texture",))
        kept, _, _ = dedupe_circles(kept)
        circles = [{k: v for k, v in x.items() if k in ("crater_id", "x", "y", "r", "confidence", "votes")} for x in kept]
        out.append({**c, "crater_set": {"schema_version": "1.0", "data_kind": meta["data_kind"], "image_id": iid,
                                         "source": "machine", "reference_source": None, "circles": circles},
                    "seconds": round(time.perf_counter() - t, 1), "n_raw": len(raw), "n_after_filters": len(circles),
                    "r_max_raw": max((x["r"] for x in raw), default=0)})
    return out


def figures(regions: dict, sfd: dict, R: dict, processed: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    d0, d1 = R["d_range_m"]
    # Histogram theo bin √2 (mật độ trên mỗi bin)
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    edges = sfd["lunokhod1"]["edges_m"]
    centers = np.sqrt(np.array(edges[:-1]) * np.array(edges[1:]))
    w = 0.35
    for i, (k, reg) in enumerate(regions.items()):
        dens = np.array(sfd[k]["counts"]) / reg["area_km2"] * 100
        ax.bar(np.arange(len(centers)) + (i - 0.5) * w, dens, w, color=COLORS[k],
               label=f"{reg['name']} (N = {reg['n']}, A = {reg['area_km2']:.1f} km²)")
    ax.set_xticks(np.arange(len(centers)), [f"{a:.0f}–{b:.0f}" for a, b in zip(edges[:-1], edges[1:])])
    ax.set_xlabel("Đường kính D (m), bin √2"); ax.set_ylabel("Số hố / 100 km²")
    ax.set_title(f"Phân bố kích thước, cùng 20 m/px, D {d0:.0f}–{d1:.0f} m (đếm tay)")
    ax.legend(fontsize=8)
    fig.savefig(OUT / "histogram.png", dpi=90); plt.close(fig)

    # Tích lũy N(≥D)/km² có khoảng tin cậy 95 %
    fig, ax = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    for k, reg in regions.items():
        cum = [c for c in sfd[k]["cumulative"] if c["n"] > 0]   # log: bỏ điểm N = 0
        x = [c["d_m"] for c in cum]; y = [c["per_km2"] for c in cum]
        lo = [c["ci95"][0] for c in cum]; hi = [c["ci95"][1] for c in cum]
        ax.plot(x, y, "o-", color=COLORS[k], label=reg["name"])
        ax.fill_between(x, lo, hi, color=COLORS[k], alpha=0.15)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("D (m)"); ax.set_ylabel("N(≥ D) / km²")
    ax.set_title("Tần suất tích lũy, dải tô = khoảng tin cậy Poisson 95 %")
    ax.legend(fontsize=8)
    fig.savefig(OUT / "tich_luy.png", dpi=90); plt.close(fig)

    # Vùng đếm và hố đã đếm
    tiles = [(k, c) for k, reg in R["regions"].items() for c in reg["crops"]]
    fig, axes = plt.subplots(1, len(tiles), figsize=(4.6 * len(tiles), 5), constrained_layout=True)
    for ax, (k, iid) in zip(axes, tiles):
        cfg = R["regions"][k]["crops"][iid]
        g = np.load(processed / f"{iid}.npy"); m = count_mask(cfg["keep"], cfg["exclude"])
        ax.imshow(g, cmap="gray", vmin=0, vmax=1)
        ax.imshow(np.ma.masked_where(m, np.ones_like(g)), cmap="Reds", alpha=0.4, vmin=0, vmax=1)
        for c in read_json(COUNTS / f"{iid}_count.json")["circles"]:
            d = 2 * c["r"] * 20.0
            if d0 <= d < d1 and m[int(round(c["y"])), int(round(c["x"]))]:
                ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color=COLORS[k], lw=1.2))
        ax.set_title(iid, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Vùng đếm (đỏ = loại khỏi vùng) và hố đã đếm", fontsize=11)
    fig.savefig(OUT / "vung_dem.png", dpi=70); plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    global OUT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    ap.add_argument("--output", type=Path, default=OUT, help="Thư mục kết quả")
    ap.add_argument("--no-machine", action="store_true")
    args = ap.parse_args(argv)
    OUT = args.output
    processed = Path(args.processed_dir)
    R = read_json(COUNTS / "regions.json")
    d0, d1 = R["d_range_m"]
    OUT.mkdir(parents=True, exist_ok=True)

    crops = {k: load_region(k, cfg, processed) for k, cfg in R["regions"].items()}
    regions = {k: {**region_count(v, d0, d1), "name": R["regions"][k]["name"]} for k, v in crops.items()}
    sfd = {k: size_frequency(r) for k, r in regions.items()}
    cmp = compare_regions(regions["lunokhod1"], regions["marefrig"])
    # So tích lũy N(≥ D) tại từng biên bin: cùng diện tích, cùng D.
    from src.statistics import binomial_two_sided_p
    a, b = regions["lunokhod1"], regions["marefrig"]
    cmp["cumulative"] = []
    for ca, cb in zip(sfd["lunokhod1"]["cumulative"], sfd["marefrig"]["cumulative"]):
        n1, n2 = ca["n"], cb["n"]
        cmp["cumulative"].append({"d_min_m": ca["d_m"], "n_a": n1, "n_b": n2,
                                  "ratio_a_over_b": (n1 / a["area_km2"]) / (n2 / b["area_km2"]) if n2 else None,
                                  "binomial_p_two_sided": binomial_two_sided_p(n1, n1 + n2, a["area_km2"] / (a["area_km2"] + b["area_km2"]))})

    with (OUT / "bang_dem.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vung", "o_cat", "ty_le_m_px", "dai_D_m", "dien_tich_km2", "so_ho", "mat_do_km2",
                    "ci95_thap", "ci95_cao", *[f"bin_{a:.0f}_{b:.0f}" for a, b in zip(sfd["lunokhod1"]["edges_m"][:-1], sfd["lunokhod1"]["edges_m"][1:])]])
        for k, r in regions.items():
            w.writerow([r["name"], " + ".join(r["crops"]), r["scale_m_per_px"], f"{d0:.0f}-{d1:.0f}", round(r["area_km2"], 2),
                        r["n"], round(r["density_per_km2"], 4), round(r["density_ci95_per_km2"][0], 4),
                        round(r["density_ci95_per_km2"][1], 4), *sfd[k]["counts"]])

    result = {"d_range_m": [d0, d1], "regions": {k: {kk: vv for kk, vv in r.items() if kk != "craters"} for k, r in regions.items()},
              "size_frequency": sfd, "comparison_lunokhod1_over_marefrig": cmp}

    if not args.no_machine:
        rows = []
        for k, cs in crops.items():
            ms = machine_sets(cs, processed)
            mreg = region_count(ms, d0, d1)
            rows.append([R["regions"][k]["name"], regions[k]["n"], mreg["n"], round(mreg["density_per_km2"], 4),
                         sum(m["n_raw"] for m in ms), sum(m["n_after_filters"] for m in ms),
                         max(m["r_max_raw"] for m in ms), sum(m["seconds"] for m in ms)])
            result.setdefault("machine", {})[k] = {"n_in_range": mreg["n"], "density_per_km2": mreg["density_per_km2"],
                                                    "n_raw": rows[-1][4], "n_after_filters": rows[-1][5], "r_max_raw_px": rows[-1][6]}
        with (OUT / "may_so_voi_tay.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["vung", "dem_tay", "may_trong_dai", "may_mat_do_km2", "may_ung_vien_tho", "may_sau_loc", "may_r_lon_nhat_px", "giay"])
            w.writerows(rows)

    (OUT / "so_sanh.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figures(regions, sfd, R, processed)

    for k, r in regions.items():
        lo, hi = r["density_ci95_per_km2"]
        print(f"{r['name']:28s} A={r['area_km2']:6.1f} km²  N={r['n']:3d}  mật độ={r['density_per_km2']:.3f}/km² "
              f"(95%: {lo:.3f}–{hi:.3f})  bin={sfd[k]['counts']}")
    print(f"Tỉ số mật độ Lunokhod 1 / Mare Frigoris = {cmp['ratio_a_over_b']:.2f}; p (nhị thức hai phía) = {cmp['binomial_p_two_sided']:.3f}")
    for k, m in result.get("machine", {}).items():
        print(f"máy {k:10s}: thô {m['n_raw']}, sau lọc {m['n_after_filters']}, trong dải D {m['n_in_range']}, r lớn nhất {m['r_max_raw_px']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
