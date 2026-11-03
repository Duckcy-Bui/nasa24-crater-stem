"""S3-03: kiểm tra đếm, kích thước và mật độ hai vùng.

    python scripts/s303_kiem_tra.py              # đủ phép kiểm tra, gồm đối chiếu máy
    python scripts/s303_kiem_tra.py --no-machine # bỏ phần chạy Hough

Đọc bản đếm và vùng đếm ở data/s303_counts/, so với bản S2-09 ở data/s209_counts/.
Ghi docs/evidence/s3-03/: kiem_tra.json, bang_dem.csv, do_nhay.csv, doi_chieu_nhan.csv,
may_so_voi_dem.csv, tich_luy.png, histogram.png, vung_dem.png.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import logging
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import radius_range_px, read_json  # noqa: E402
from src.matching import match_one_to_one  # noqa: E402
from src.statistics import (binomial_two_sided_p, compare_regions, count_mask, region_count,  # noqa: E402
                            size_frequency, sqrt2_bins)

NEW = ROOT / "data" / "s303_counts"
OLD = ROOT / "data" / "s209_counts"
LABELS = ROOT / "data" / "reference_labels"
OUT = ROOT / "docs" / "evidence" / "s3-03"
COLORS = {"lunokhod1": "#1f6feb", "marefrig": "#d1495b"}
THRESHOLDS = [300.0, 300.0 * 2 ** 0.5, 600.0, 600.0 * 2 ** 0.5]
LUNOKHOD, MARE = "lunokhod1", "marefrig"
CORNER = [0, 0, 184, 244]   # góc trưởng nhóm thử ở review PR #30


def load(folder: Path, processed: Path, exclude_extra: dict | None = None, regions: dict | None = None) -> dict:
    R = regions or read_json(folder / "regions.json")
    out = {}
    for key, reg in R["regions"].items():
        crops = []
        for iid, cfg in reg["crops"].items():
            vpath = processed / f"{iid}_valid_mask.npy"
            extra = (exclude_extra or {}).get(iid, [])
            crops.append({"metadata": read_json(processed / f"{iid}.json"),
                          "crater_set": read_json(folder / f"{iid}_count.json"),
                          "mask": count_mask(cfg["keep"], list(cfg["exclude"]) + extra),
                          "valid": np.load(vpath).astype(bool) if vpath.exists() else None})
        out[key] = crops
    return out


def compare(crops: dict, d0: float, d1: float) -> dict:
    a, b = region_count(crops[LUNOKHOD], d0, d1), region_count(crops[MARE], d0, d1)
    c = compare_regions(a, b)
    return {"n_a": a["n"], "n_b": b["n"], "area_a": a["area_km2"], "area_b": b["area_km2"],
            "density_a": c["density_a"], "density_b": c["density_b"], "ratio": c["ratio_a_over_b"],
            "p": c["binomial_p_two_sided"]}


def scenario(name: str, crops: dict, d1: float) -> dict:
    tot, big = compare(crops, 300.0, d1), compare(crops, THRESHOLDS[1], d1)
    return {"kich_ban": name, "ty_so_tong": round(tot["ratio"], 2), "p_tong": round(tot["p"], 3),
            "ty_so_424": round(big["ratio"], 2), "p_424": round(big["p"], 3), "n_L": tot["n_a"], "n_M": tot["n_b"],
            "A_L": round(tot["area_a"], 1), "A_M": round(tot["area_b"], 1)}


def shifted(crops: dict, dr: float) -> dict:
    """Mọi bán kính lệch dr px: sai số hệ thống của người đếm."""
    out = copy.deepcopy(crops)
    for group in out.values():
        for c in group:
            for q in c["crater_set"]["circles"]:
                q["r"] = max(1.0, q["r"] + dr)
    return out


def checks(R: dict, crops: dict, regions: dict, sfd: dict) -> list[dict]:
    """Kiểm tra thang đo, dải bán kính, diện tích và đơn vị; mỗi dòng ghi đạt hay không."""
    rows = []
    d0, d1 = R["d_range_m"]
    scales = {c["metadata"]["scale_m_per_px"] for g in crops.values() for c in g}
    rows.append({"muc": "Cùng tỷ lệ ảnh", "gia_tri": sorted(scales), "dat": scales == {20.0}})
    rows.append({"muc": "Cùng dải D (m)", "gia_tri": [d0, d1],
                 "dat": regions[LUNOKHOD]["d_range_m"] == regions[MARE]["d_range_m"] == [d0, d1]})
    rows.append({"muc": "Dải r tương ứng (px)", "gia_tri": [d0 / 40, d1 / 40], "dat": d0 / 40 == 7.5 and d1 / 40 == 50})
    meta_rr = {tuple(radius_range_px(c["metadata"]["radius"]["d_min_m"], c["metadata"]["radius"]["d_max_m"], 20.0))
               for g in crops.values() for c in g}
    rows.append({"muc": "Dải tìm Hough theo metadata (px)", "gia_tri": sorted(meta_rr), "dat": len(meta_rr) == 1})
    for key, group in crops.items():
        px = 0
        spans = []
        for c in group:
            m = np.asarray(c["mask"], dtype=bool)
            if c.get("valid") is not None:
                m = m & c["valid"]
            px += int(m.sum())
            spans.append((c["metadata"]["crop_x0"], c["metadata"]["crop_y0"], m))
        (x1, y1, a), (x2, y2, b) = spans
        dx, dy = x2 - x1, y2 - y1
        xa, xb = max(0, dx), min(512, 512 + dx)
        ya, yb = max(0, dy), min(512, 512 + dy)
        overlap = int((a[ya:yb, xa:xb] & b[ya - dy:yb - dy, xa - dx:xb - dx]).sum()) if xb > xa and yb > ya else 0
        km2 = px * 20.0 ** 2 / 1e6
        rows.append({"muc": f"{key}: diện tích tính lại (km²)", "gia_tri": round(km2, 3),
                     "dat": math.isclose(km2, regions[key]["area_km2"]) and overlap == 0})
        rows.append({"muc": f"{key}: phần chồng giữa hai ô (px)", "gia_tri": overlap, "dat": overlap == 0})
        rows.append({"muc": f"{key}: tổng bin = N", "gia_tri": [sum(sfd[key]["counts"]), regions[key]["n"]],
                     "dat": sum(sfd[key]["counts"]) == regions[key]["n"]})
        ds = [c["d_m"] for c in regions[key]["craters"]]
        rows.append({"muc": f"{key}: D nằm trong dải", "gia_tri": [min(ds), max(ds)], "dat": d0 <= min(ds) and max(ds) < d1})
    rows.append({"muc": "Đơn vị: 1 px ở 20 m/px (km²)", "gia_tri": 4e-4, "dat": math.isclose(20 ** 2 / 1e6, 4e-4)})
    return rows


def labels_vs_counts(crops: dict, d0: float, d1: float) -> tuple[list[list], dict]:
    """Nhãn S2-03 trong vùng đếm và dải D có khớp một hố đã đếm không (tâm ≤ 0,5 r nhãn)."""
    rows, sums = [], {}
    for key, group in crops.items():
        hit = total = n_count = n_count_hit = 0
        for c in group:
            iid = c["metadata"]["image_id"]
            mask = np.asarray(c["mask"], dtype=bool)
            inside = lambda q: mask[int(round(q["y"])), int(round(q["x"]))] and d0 <= 40 * q["r"] < d1  # noqa: E731
            counted = [q for q in c["crater_set"]["circles"] if inside(q)]
            labels = [q for q in read_json(LABELS / f"{iid}_craters_catalogue.json")["circles"] if inside(q)]
            result = match_one_to_one(counted, labels, 0.5)
            pairs = {m["reference_id"] for m in result}
            for q in labels:
                rows.append([key, iid, q["crater_id"], q["x"], q["y"], q["r"], 40 * q["r"], q["crater_id"] in pairs])
            hit += len(pairs)
            total += len(labels)
            n_count += len(counted)
            n_count_hit += len(result)
        sums[key] = {"nhan_trong_vung": total, "nhan_khop_ban_dem": hit, "ban_dem": n_count, "ban_dem_khop_nhan": n_count_hit}
    return rows, sums


def machine_rows(crops: dict, d0: float, d1: float, processed: Path) -> tuple[list[list], dict]:
    """Ứng viên máy (cấu hình S2-15 và radius_balanced) so với bản đếm: bỏ sót, phát hiện sai, mật độ."""
    from src.hough import detect_circles, resolve_hough_params
    from src.pipeline import load_image, radius_range
    from src.postprocessing import apply_filter, dedupe_circles, review_candidates
    from src.preprocessing import preprocess

    logging.disable(logging.WARNING)
    frozen = read_json(ROOT / "configs" / "s215_frozen.json")["hough"]
    configs = {"S2-15 (score)": frozen, "radius_balanced": {**frozen, "candidate_selection": "radius_balanced"}}
    rows, out = [], {}
    for cname, cfg in configs.items():
        h = resolve_hough_params(cfg)
        for key, group in crops.items():
            tp = fn = fp = 0
            sets = []
            for c in group:
                iid = c["metadata"]["image_id"]
                meta, image, valid = load_image(iid, processed)
                pre = preprocess(image, meta, None, valid_mask=valid)
                raw = detect_circles(pre["edges"], *radius_range(meta, h), h, theta=pre["theta"])
                kept, _ = apply_filter(review_candidates(raw, pre)[0], remove_classes=("texture",))
                kept = dedupe_circles(kept)[0]
                mask = np.asarray(c["mask"], dtype=bool)
                inside = lambda q: mask[int(round(q["y"])), int(round(q["x"]))] and d0 <= 40 * q["r"] < d1  # noqa: E731
                pred = [q for q in kept if inside(q)]
                ref = [q for q in c["crater_set"]["circles"] if inside(q)]
                n = len(match_one_to_one(pred, ref, 0.5))
                tp += n
                fn += len(ref) - n
                fp += len(pred) - n
                keep = ("crater_id", "x", "y", "r", "confidence", "votes")
                sets.append({**c, "crater_set": {**c["crater_set"], "source": "machine", "reference_source": None,
                                                  "circles": [{k: q[k] for k in keep} for q in kept]}})
            reg = region_count(sets, d0, d1)
            n_true = tp + fn
            rows.append([cname, key, n_true, tp + fp, tp, fn, fp, round(tp / n_true, 3) if n_true else None,
                         round(tp / (tp + fp), 3) if tp + fp else None, round(reg["density_per_km2"], 4)])
            out.setdefault(cname, {})[key] = {"tp": tp, "fn": fn, "fp": fp, "density": reg["density_per_km2"]}
    return rows, out


def impact(a: dict, b: dict) -> dict:
    """Bỏ sót và phát hiện sai đổi tỉ số mật độ bao nhiêu, và cần lệch bao nhiêu để đổi kết luận."""
    frac = a["area_a"] / (a["area_a"] + a["area_b"])
    n1, n2 = a["n_a"], a["n_b"]

    def need(k1: int, k2: int) -> dict:
        add_a = next((x for x in range(0, 400) if binomial_two_sided_p(k1 + x, k1 + x + k2, frac) < 0.05), None)
        add_b = next((x for x in range(0, 400) if binomial_two_sided_p(k1, k1 + k2 + x, frac) < 0.05), None)
        return {"them_vao_L_de_p_nho_hon_0_05": add_a, "them_vao_M_de_p_nho_hon_0_05": add_b}

    grid = []
    for c_a in (1.0, 0.9, 0.8, 0.7):
        for c_b in (1.0, 0.9, 0.8, 0.7):
            grid.append({"do_day_du_L": c_a, "do_day_du_M": c_b, "ty_so_tong": round(a["ratio"] * c_b / c_a, 2),
                         "ty_so_424": round(b["ratio"] * c_b / c_a, 2)})
    return {"tong": need(n1, n2), "tu_424": need(b["n_a"], b["n_b"]), "luoi_do_day_du": grid}


def figures(regions: dict, sfd: dict, old: dict, old_sfd: dict, R: dict, processed: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    d0, d1 = R["d_range_m"]
    fig, ax = plt.subplots(figsize=(7.4, 5), constrained_layout=True)
    for k, reg in regions.items():
        cum = [c for c in sfd[k]["cumulative"] if c["n"] > 0]
        x = [c["d_m"] for c in cum]
        ax.plot(x, [c["per_km2"] for c in cum], "o-", color=COLORS[k], label=f"{reg['name']}: S3-03")
        ax.fill_between(x, [c["ci95"][0] for c in cum], [c["ci95"][1] for c in cum], color=COLORS[k], alpha=0.15)
        prev = [c for c in old_sfd[k]["cumulative"] if c["n"] > 0]
        ax.plot([c["d_m"] for c in prev], [c["per_km2"] for c in prev], ":", color=COLORS[k], label=f"{reg['name']}: bản S2-09")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("D (m)"); ax.set_ylabel("N(≥ D) / km²")
    ax.set_title("Tần suất tích lũy; dải tô = khoảng tin cậy Poisson 95 %", fontsize=11)
    ax.legend(fontsize=8)
    fig.savefig(OUT / "tich_luy.png", dpi=90); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.4), constrained_layout=True)
    edges = sfd[LUNOKHOD]["edges_m"]
    pos = np.arange(len(edges) - 1)
    for i, (k, reg) in enumerate(regions.items()):
        dens = np.array(sfd[k]["counts"]) / reg["area_km2"] * 100
        ax.bar(pos + (i - 0.5) * 0.36, dens, 0.36, color=COLORS[k], label=f"{reg['name']} (N = {reg['n']}, A = {reg['area_km2']:.1f} km²)")
    ax.set_xticks(pos, [f"{a:.0f}–{b:.0f}" for a, b in zip(edges[:-1], edges[1:])])
    ax.set_xlabel("Đường kính D (m), bin √2"); ax.set_ylabel("Số hố / 100 km²")
    ax.set_title(f"Phân bố kích thước, cùng 20 m/px, D {d0:.0f}–{d1:.0f} m", fontsize=11)
    ax.legend(fontsize=8)
    fig.savefig(OUT / "histogram.png", dpi=90); plt.close(fig)

    tiles = [(k, i) for k, reg in R["regions"].items() for i in reg["crops"]]
    fig, axes = plt.subplots(1, len(tiles), figsize=(4.6 * len(tiles), 5), constrained_layout=True)
    for ax, (k, iid) in zip(axes, tiles):
        cfg = R["regions"][k]["crops"][iid]
        g = np.load(processed / f"{iid}.npy")
        m = count_mask(cfg["keep"], cfg["exclude"])
        ax.imshow(g, cmap="gray", vmin=0, vmax=1)
        ax.imshow(np.ma.masked_where(m, np.ones_like(g)), cmap="Reds", alpha=0.4, vmin=0, vmax=1)
        for c in read_json(NEW / f"{iid}_count.json")["circles"]:
            if d0 <= 40 * c["r"] < d1 and m[int(round(c["y"])), int(round(c["x"]))]:
                ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color=COLORS[k], lw=1.1))
        ax.set_title(iid, fontsize=9); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Vùng đếm (đỏ = loại) và hố đã đếm", fontsize=11)
    fig.savefig(OUT / "vung_dem.png", dpi=70); plt.close(fig)


def write_csv(name: str, header: list, rows: list) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    ap.add_argument("--no-machine", action="store_true")
    args = ap.parse_args(argv)
    processed = Path(args.processed_dir)
    OUT.mkdir(parents=True, exist_ok=True)

    R = read_json(NEW / "regions.json")
    d0, d1 = R["d_range_m"]
    crops = load(NEW, processed)
    old_crops = load(OLD, processed)
    regions = {k: {**region_count(v, d0, d1), "name": R["regions"][k]["name"]} for k, v in crops.items()}
    old_regions = {k: {**region_count(v, d0, d1), "name": R["regions"][k]["name"]} for k, v in old_crops.items()}
    edges = sqrt2_bins(d0, d1)
    sfd = {k: size_frequency(r, edges) for k, r in regions.items()}
    old_sfd = {k: size_frequency(r, edges) for k, r in old_regions.items()}

    check_rows = checks(R, crops, regions, sfd)
    write_csv("bang_dem.csv", ["ban", "vung", "dien_tich_km2", "so_ho", "mat_do_km2", "ci95_thap", "ci95_cao",
                               *[f"bin_{a:.0f}_{b:.0f}" for a, b in zip(edges[:-1], edges[1:])]],
              [[tag, r["name"], round(r["area_km2"], 2), r["n"], round(r["density_per_km2"], 4),
                round(r["density_ci95_per_km2"][0], 4), round(r["density_ci95_per_km2"][1], 4), *s[k]["counts"]]
               for tag, reg, s in (("S3-03", regions, sfd), ("S2-09", old_regions, old_sfd)) for k, r in reg.items()])

    # Ngưỡng là phân tích thăm dò: báo p thô và p đã nhân số ngưỡng thử (Bonferroni).
    thresholds = []
    for d in THRESHOLDS:
        c = compare(crops, d, d1)
        thresholds.append({"tu_D_m": round(d), "n_L": c["n_a"], "n_M": c["n_b"], "mat_do_L": round(c["density_a"], 3),
                           "mat_do_M": round(c["density_b"], 3), "ty_so": round(c["ratio"], 2) if c["n_b"] else None,
                           "p": round(c["p"], 3), "p_bonferroni_4": round(min(1.0, c["p"] * len(THRESHOLDS)), 3)})

    scen = [scenario("Bản S3-03", crops, d1), scenario("Bản S2-09 (cũ)", old_crops, d1)]
    scen.append(scenario("S3-03, cùng bỏ góc [0,0,184,244) ở c01 và c03",
                         load(NEW, processed, {"moon_lunokhod1_loc_c01": [CORNER], "moon_marefrig_loc_c03": [CORNER]}), d1))
    scen.append(scenario("S3-03, chỉ Lunokhod c01", {**crops, LUNOKHOD: crops[LUNOKHOD][:1]}, d1))
    scen.append(scenario("S3-03, chỉ Mare Frigoris c03", {**crops, MARE: crops[MARE][1:]}, d1))
    scen.append(scenario("S3-03, r đếm +1 px", shifted(crops, 1.0), d1))
    scen.append(scenario("S3-03, r đếm −1 px", shifted(crops, -1.0), d1))
    write_csv("do_nhay.csv", list(scen[0]), [list(s.values()) for s in scen])

    label_rows, label_sum = labels_vs_counts(crops, d0, d1)
    _, old_label_sum = labels_vs_counts(old_crops, d0, d1)
    write_csv("doi_chieu_nhan.csv", ["vung", "image_id", "nhan", "x", "y", "r", "D_m", "khop_ban_dem"], label_rows)

    machine, machine_rows_out = {}, []
    if not args.no_machine:
        machine_rows_out, machine = machine_rows(crops, d0, d1, processed)
        write_csv("may_so_voi_dem.csv", ["cau_hinh", "vung", "ban_dem", "may_trong_dai", "dung", "bo_sot", "phat_hien_sai",
                                         "ty_le_tim_lai", "ty_le_dung", "mat_do_may_km2"], machine_rows_out)

    tot, big = compare(crops, d0, d1), compare(crops, THRESHOLDS[1], d1)
    result = {"rule": R["rule"], "status": "bản nháp: chờ người đếm duyệt và người thứ hai kiểm chéo",
              "checks": check_rows, "thresholds": thresholds, "sensitivity": scen,
              "labels": label_sum, "labels_old": old_label_sum, "impact": impact(tot, big), "machine": machine,
              "regions": {k: {kk: vv for kk, vv in r.items() if kk != "craters"} for k, r in regions.items()},
              "size_frequency": sfd}
    (OUT / "kiem_tra.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    figures(regions, sfd, old_regions, old_sfd, R, processed)

    print("KIỂM TRA:", sum(r["dat"] for r in check_rows), "/", len(check_rows), "đạt")
    for r in check_rows:
        if not r["dat"]:
            print("  KHÔNG ĐẠT", r)
    for k, r in regions.items():
        lo, hi = r["density_ci95_per_km2"]
        print(f"{r['name']:28s} A={r['area_km2']:6.1f} N={r['n']:3d} ρ={r['density_per_km2']:.3f} ({lo:.3f}–{hi:.3f}) bin={sfd[k]['counts']}")
    for t in thresholds:
        print(t)
    for s in scen:
        print(s)
    print("nhãn:", label_sum, "| cũ:", old_label_sum)
    print("tác động:", result["impact"]["tong"], result["impact"]["tu_424"])
    for row in machine_rows_out:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
