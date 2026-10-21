"""S1-14: tạo hình và bảng tham số cho nháp Chương 2/3 (tiền xử lý, sáng–tối).

    python scripts/s114_figures.py
    python scripts/s114_figures.py --processed-dir <thư mục ảnh S1-06>

Ghi vào docs/images/s114/:
  so_do_cac_buoc.png         sơ đồ B0–B8 → Hough → S1-11, tô màu tự viết / thư viện
  truoc_sau_<STT>.png        ảnh đầu vào và đầu ra từng bước (STT 13 nắng xiên, STT 17 nắng đứng)
  histogram_<STT>.png        phân bố độ sáng trước/sau B3 và B4
  sang_toi_nguyen_ly.png     hố lõm, gò nổi: ảnh, t-map, đồ thị độ sáng theo t
  tru_doc_dia_hinh.png       vòng chỗ phẳng trên dốc: trước/sau trừ mặt phẳng
và docs/evidence/s1-14/tham_so_<image_id>.json (tham số thực tế của mỗi ảnh).
Hai hình sáng–tối cần mã S1-11; nếu nhánh hiện tại chưa có thì script bỏ qua hai hình đó.
Ảnh LROC là bản browse 8 bit, chỉ dùng minh họa xử lý ảnh (LROC RDR SIS mục 3.2).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import load_image  # noqa: E402
try:  # Hình sáng–tối cần mã S1-11 (PR #12); khi chưa gộp vào main thì bỏ qua, giữ hình đã tạo.
    from src.postprocessing import _pixels_in_ring, resolve_params, score_one, sun_vector  # noqa: E402
    HAS_S111 = True
except ImportError:
    HAS_S111 = False
from src.preprocessing import preprocess  # noqa: E402

OUT = ROOT / "docs" / "images" / "s114"
EVIDENCE = ROOT / "docs" / "evidence" / "s1-14"
SELF, LIB, OTHER = "#1f6feb", "#d1495b", "#6e7781"
IMAGES = {"stt13": ("moon_ap16_m132732855l_c01", "STT 13 · nắng xiên (góc tới 87,7°)"),
          "stt17": ("moon_ap16_m109134835l_c01", "STT 17 · nắng gần đứng (góc tới 7,64°)")}


def diagram(path: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    steps = [("B0", "Đọc, cắt\n512·k", LIB, "rasterio"), ("B1", "Thu nhỏ\nkhối k×k", SELF, "NumPy"),
             ("B2", "Ảnh xám\nBT.601", SELF, "NumPy"), ("B3", "Chuẩn hóa\nphân vị", SELF, "NumPy"),
             ("B4", "CLAHE", LIB, "OpenCV"), ("B5", "Gauss\nσ=1,5", SELF, "NumPy"),
             ("B6", "Sobel\ngx, gy, |G|, θ", SELF, "NumPy"), ("B7", "Canny", LIB, "OpenCV\n(ngưỡng tự viết)"),
             ("B8", "Mặt nạ\nbiên", SELF, "NumPy")]
    fig, ax = plt.subplots(figsize=(15, 5.4))
    ax.set_xlim(0, 15); ax.set_ylim(-0.9, 4.6); ax.axis("off")
    w, h, y = 1.35, 1.1, 2.9
    for i, (sid, name, color, impl) in enumerate(steps):
        x = 0.3 + i * 1.6
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", fc=color, ec="none", alpha=0.9))
        ax.text(x + w / 2, y + h - 0.22, sid, ha="center", va="center", color="white", fontsize=10, weight="bold")
        ax.text(x + w / 2, y + 0.42, name, ha="center", va="center", color="white", fontsize=8.5)
        ax.text(x + w / 2, y - 0.25, impl, ha="center", va="top", color=color, fontsize=7.5)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 1.6, y + h / 2), xytext=(x + w, y + h / 2), arrowprops=dict(arrowstyle="->", color="#333"))
    outs = [(3, "gray (B3)\n→ S1-11, game"), (6, "theta (B6)\n→ Hough gradient"), (8, "edges (B8)\n→ Hough")]
    for i, label in outs:
        x = 0.3 + i * 1.6 + w / 2
        ax.annotate("", xy=(x, 1.25), xytext=(x, y - 0.75), arrowprops=dict(arrowstyle="->", color=OTHER))
        ax.text(x, 1.15, label, ha="center", va="top", fontsize=8, color=OTHER)
    for x0, sid, name in ((10.6, "S1-07", "Hough tròn"), (12.6, "S1-11", "Chấm sáng–tối")):
        ax.add_patch(FancyBboxPatch((x0, -0.8), 1.6, 0.6, boxstyle="round,pad=0.04", fc="#e9ecef", ec=OTHER))
        ax.text(x0 + 0.8, -0.5, f"{sid}\n{name}", ha="center", va="center", fontsize=8.5)
    ax.annotate("", xy=(12.6, -0.5), xytext=(12.2, -0.5), arrowprops=dict(arrowstyle="->", color="#333"))
    ax.text(0.3, 4.45, "Chuỗi tiền xử lý S1-08 (src/preprocessing.py)", fontsize=11, weight="bold", va="top")
    ax.text(10.2, 4.45, "■ tự viết NumPy", color=SELF, fontsize=10, va="top")
    ax.text(12.5, 4.45, "■ thư viện", color=LIB, fontsize=10, va="top")
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def steps_figure(path: Path, image: np.ndarray, out: dict, title: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import hsv_to_rgb

    mag = out["mag"]
    hue = (out["theta"] + np.pi) / (2 * np.pi)
    val = np.clip(mag / np.percentile(mag, 99), 0, 1)
    theta_rgb = hsv_to_rgb(np.dstack([hue, np.ones_like(hue), val]))
    panels = [("Đầu vào (.npy S1-06)", image, "gray", OTHER), ("B3 chuẩn hóa phân vị", out["gray"], "gray", SELF),
              ("B4 CLAHE", out["enhanced"], "gray", LIB), ("B5 Gauss σ=1,5", out["smooth"], "gray", SELF),
              ("B6 |G|", np.clip(mag / np.percentile(mag, 99), 0, 1), "gray", SELF), ("B6 θ (màu) × |G|", theta_rgb, None, SELF),
              (f"B7 Canny ({int(out['edges_canny'].sum())} px)", out["edges_canny"], "gray", LIB),
              (f"B8 sau mặt nạ ({int(out['edges'].sum())} px)", out["edges"], "gray", SELF)]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.6), constrained_layout=True)
    for ax, (name, data, cmap, color) in zip(axes.ravel(), panels):
        ax.imshow(data, cmap=cmap, vmin=0 if cmap else None, vmax=1 if cmap else None)
        ax.set_title(name, color=color, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(f"{title} — xanh: tự viết, đỏ: thư viện", fontsize=12)
    fig.savefig(path, dpi=80)
    plt.close(fig)


def histogram_figure(path: Path, image: np.ndarray, out: dict, title: str) -> None:
    import matplotlib.pyplot as plt

    v = out["valid_mask"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.2), constrained_layout=True, sharey=True)
    for ax, (name, data) in zip(axes, (("Đầu vào", image), ("Sau B3", out["gray"]), ("Sau B4 CLAHE", out["enhanced"]))):
        ax.hist(np.asarray(data)[v].ravel(), bins=64, range=(0, 1), color=SELF if "B3" in name else (LIB if "B4" in name else OTHER))
        ax.set_title(name, fontsize=10); ax.set_xlabel("độ sáng [0, 1]")
    axes[0].set_ylabel("số pixel")
    fig.suptitle(f"Phân bố độ sáng — {title}", fontsize=11)
    fig.savefig(path, dpi=90)
    plt.close(fig)


def lit(dem: np.ndarray, azimuth: float, incidence: float, seed: int = 0) -> np.ndarray:
    ux, uy = sun_vector(azimuth, 0.0)
    inc = math.radians(incidence)
    fy, fx = np.gradient(dem)
    shade = (-fx * ux * math.sin(inc) - fy * uy * math.sin(inc) + math.cos(inc)) / np.sqrt(fx ** 2 + fy ** 2 + 1)
    img = np.clip(shade, 0, None) * 0.6 + 0.2 + np.random.default_rng(seed).normal(0, 0.02, dem.shape)
    return np.clip(img, 0, 1)


def shading_figure(path: Path) -> dict:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    n, c, r = 160, 80.0, 40.0
    yy, xx = np.mgrid[:n, :n].astype(float)
    d = np.hypot(xx - c, yy - c) / r
    shapes = {"Hố lõm": np.where(d < 1, 0.25 * r * (d ** 2 - 1), 0), "Gò nổi": np.where(d < 1, 0.25 * r * (1 - d ** 2), 0)}
    u = sun_vector(270, 0)
    p = resolve_params({})
    valid = np.ones((n, n), bool)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8.4), constrained_layout=True)
    scores = {}
    for row, (name, dem) in enumerate(shapes.items()):
        img = lit(dem, 270, 70, seed=row)
        xs, ys, _ = _pixels_in_ring(valid, c, c, -1, r)
        t = -((xs - c) * u[0] + (ys - c) * u[1]) / r
        vals = img[ys, xs]
        s = score_one(img.astype(np.float32), valid, {"x": c, "y": c, "r": r}, u, "side_only", p)
        scores[name] = s
        axes[row][0].imshow(img, cmap="gray", vmin=0, vmax=1)
        axes[row][0].add_patch(Circle((c, c), r, fill=False, color="cyan", ls="--"))
        axes[row][0].annotate("", xy=(c - 60, 12), xytext=(c - 10, 12), arrowprops=dict(color="yellow", width=2.5, headwidth=10))
        axes[row][0].text(c - 35, 26, "u: về phía Mặt Trời", color="yellow", ha="center", fontsize=8)
        axes[row][0].set_title(f"{name}, nắng Tây, góc tới 70°", fontsize=10)
        tmap = np.full((n, n), np.nan); tmap[ys, xs] = t
        im = axes[row][1].imshow(tmap, cmap="coolwarm", vmin=-1, vmax=1)
        axes[row][1].set_title("t = −((p − c)·u)/r: âm phía Mặt Trời, dương phía xa", fontsize=9)
        fig.colorbar(im, ax=axes[row][1], shrink=0.7)
        axes[row][2].scatter(t, vals, s=2, alpha=0.3, color=SELF if row == 0 else LIB)
        axes[row][2].set_xlabel("t"); axes[row][2].set_ylabel("độ sáng")
        axes[row][2].set_title(f"score = corr(độ sáng, t) = {s['score']:+.2f} → {s['status']}", fontsize=10)
        for ax in axes[row][:2]:
            ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Nguyên lý chấm sáng–tối (S1-04 mục 6.3): hố lõm sáng dần về phía xa Mặt Trời, gò nổi ngược lại", fontsize=11)
    fig.savefig(path, dpi=85)
    plt.close(fig)
    return {k: {"score": v["score"], "status": v["status"]} for k, v in scores.items()}


def detrend_figure(path: Path) -> dict:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    n, c, r = 200, 100.0, 30.0
    yy, xx = np.mgrid[:n, :n].astype(float)
    img = (lit(np.zeros((n, n)), 270, 70, seed=3) + 0.004 * (xx - c)).astype(np.float32)
    valid = np.ones((n, n), bool)
    u = sun_vector(270, 0)
    p = resolve_params({})
    s = score_one(img, valid, {"x": c, "y": c, "r": r}, u, "side_only", p)
    xs, ys, _ = _pixels_in_ring(valid, c, c, -1, r)
    ax_, ay_, _ = _pixels_in_ring(valid, c, c, 1.3 * r, 2 * r)
    design = np.column_stack([np.ones(len(ax_)), (ax_ - c) / r, (ay_ - c) / r])
    coef, *_ = np.linalg.lstsq(design, img[ay_, ax_].astype(float), rcond=None)
    t = -((xs - c) * u[0] + (ys - c) * u[1]) / r
    raw = img[ys, xs]
    det = raw - (coef[0] + coef[1] * (xs - c) / r + coef[2] * (ys - c) / r)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), constrained_layout=True)
    axes[0].imshow(img, cmap="gray")
    axes[0].add_patch(Circle((c, c), r, fill=False, color="cyan", ls="--"))
    for rr in (1.3 * r, 2 * r):
        axes[0].add_patch(Circle((c, c), rr, fill=False, color="orange", ls=":"))
    axes[0].set_title("Vòng chỗ phẳng trên nền dốc sáng\n(cam: vành ngoài [1,3r; 2r] để khớp mặt phẳng)", fontsize=9)
    axes[0].set_xticks([]); axes[0].set_yticks([])
    axes[1].scatter(t, raw, s=2, alpha=0.3, color=LIB)
    axes[1].set_title(f"Không trừ dốc: score_raw = {s['score_raw']:+.2f}", fontsize=10)
    axes[2].scatter(t, det, s=2, alpha=0.3, color=SELF)
    axes[2].set_title(f"Trừ mặt phẳng: score = {s['score']:+.2f} → {s['status']}", fontsize=10)
    for ax in axes[1:]:
        ax.set_xlabel("t"); ax.set_ylabel("độ sáng")
    fig.savefig(path, dpi=85)
    plt.close(fig)
    return {"score_raw": s["score_raw"], "score": s["score"], "status": s["status"], "reason": s["reason"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    parser.add_argument("--out-dir", default=None,
                        help="ghi hình và tham số vào thư mục này thay vì docs/ (để chạy thử không làm bẩn repo)")
    args = parser.parse_args(argv)
    global OUT, EVIDENCE
    if args.out_dir:
        OUT = Path(args.out_dir) / "images"
        EVIDENCE = Path(args.out_dir) / "evidence"
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    diagram(OUT / "so_do_cac_buoc.png")
    summary = {}
    for key, (image_id, title) in IMAGES.items():
        metadata, image, valid = load_image(image_id, args.processed_dir)
        out = preprocess(image, metadata, None, valid_mask=valid)
        steps_figure(OUT / f"truoc_sau_{key}.png", image, out, title)
        histogram_figure(OUT / f"histogram_{key}.png", image, out, title)
        params = {k: v for k, v in out["params"].items() if k != "steps"}
        (EVIDENCE / f"tham_so_{image_id}.json").write_text(json.dumps(params, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary[image_id] = {k: params[k] for k in ("p_lo_value", "p_hi_value", "normalization_strategy", "canny_low",
                                                    "canny_high", "canny_threshold_strategy", "edge_margin_px",
                                                    "valid_ratio", "edge_px_canny", "edge_px_final")}
    if HAS_S111:
        summary["sang_toi_nguyen_ly"] = shading_figure(OUT / "sang_toi_nguyen_ly.png")
        summary["tru_doc_dia_hinh"] = detrend_figure(OUT / "tru_doc_dia_hinh.png")
    else:
        print("Chưa có mã S1-11 (src/postprocessing.py) trên nhánh này: bỏ qua sang_toi_nguyen_ly.png "
              "và tru_doc_dia_hinh.png, giữ bản đã tạo. Chạy lại sau khi PR #12 được gộp.")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
