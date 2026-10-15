"""S1-10 — Vẽ lại ảnh overlay từ file nhãn trong data/reference_labels/.

Cách dùng:
  python scripts/render_demo_overlay.py [image_id] [--processed-dir DIR]

Ảnh overlay chỉ để kiểm tra chéo bằng mắt. Tiêu đề ghi đúng nguồn và trạng thái nhãn,
không gọi nhãn chưa kiểm chéo là ground truth.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COLOR_CERTAIN = "#00e5ff"
COLOR_UNCERTAIN = "#ff9800"


def render(image_id: str, processed_dir: Path, ref_dir: Path) -> Path:
    data = json.loads((ref_dir / f"{image_id}_craters_catalogue.json").read_text(encoding="utf-8"))
    meta = json.loads((processed_dir / f"{image_id}.json").read_text(encoding="utf-8"))
    img = np.load(processed_dir / f"{image_id}.npy")
    out_path = ref_dir / f"{image_id}_overlay.png"

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#0f0f23")
    ax.imshow(img, cmap="gray", vmin=0, vmax=1, extent=[-0.5, 511.5, 511.5, -0.5], origin="upper")

    source = data["reference_source"]
    status = "chưa kiểm chéo" if "unreviewed" in source else "xem nguồn"
    ax.set_title(
        f"S1-10 nhãn thủ công ({status}): {image_id} · {meta['scale_m_per_px']} m/px\nNguồn: {source}",
        color="#e0e0e0", fontsize=9.5, pad=10,
    )
    ax.set_xlabel("x (pixel [0, 511])", color="#90caf9")
    ax.set_ylabel("y (pixel [0, 511])", color="#90caf9")
    ax.tick_params(colors="#90caf9")
    for spine in ax.spines.values():
        spine.set_edgecolor("#37474f")

    certain = uncertain = 0
    for c in data["circles"]:
        unc = "_uncertain" in c["crater_id"]
        certain += not unc
        uncertain += unc
        color = COLOR_UNCERTAIN if unc else COLOR_CERTAIN
        ax.add_patch(plt.Circle((c["x"], c["y"]), c["r"], fill=False, color=color, linewidth=1.5))
        ax.annotate(c["crater_id"], (c["x"], c["y"] - c["r"] - 4), color=color, fontsize=8, ha="center", fontweight="bold")

    ax.legend(handles=[
        mpatches.Patch(facecolor="none", edgecolor=COLOR_CERTAIN, label=f"Nhãn chắc chắn ({certain})"),
        mpatches.Patch(facecolor="none", edgecolor=COLOR_UNCERTAIN, label=f"Nhãn uncertain ({uncertain})"),
    ], loc="upper right", facecolor="#263238", edgecolor="#455a64", labelcolor="#e0e0e0", fontsize=8)
    fig.text(0.5, 0.015, "Nhãn thưa: còn nhiều hố chưa gán nhãn. Không dùng để tính Precision.",
             color="#ffeb3b", fontsize=8, ha="center")

    plt.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Vẽ lại ảnh overlay nhãn S1-10")
    parser.add_argument("image_id", nargs="?", default="moon_ap16_m106777343r_c01")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--ref-dir", type=Path, default=ROOT / "data" / "reference_labels")
    args = parser.parse_args()
    print(f"Đã vẽ overlay: {render(args.image_id, args.processed_dir, args.ref_dir)}")


if __name__ == "__main__":
    main()
