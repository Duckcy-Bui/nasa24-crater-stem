import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

root = Path(__file__).resolve().parents[1]
ref_dir = root / "data" / "reference_labels"
json_path = ref_dir / "moon_ap16_m106777343r_c01_craters_catalogue.json"
meta_path = root / "data" / "processed" / "moon_ap16_m106777343r_c01.json"
npy_path = root / "data" / "processed" / "moon_ap16_m106777343r_c01.npy"
out_path = ref_dir / "moon_ap16_m106777343r_c01_overlay.png"

data = json.loads(json_path.read_text(encoding="utf-8"))
meta = json.loads(meta_path.read_text(encoding="utf-8"))
img = np.load(npy_path)

fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#0f0f23")
ax.imshow(img, cmap="gray", vmin=0, vmax=1, extent=[-0.5, 511.5, 511.5, -0.5], origin="upper")

title = (
    f"S1-10 Ground Truth: moon_ap16_m106777343r_c01 (Scale: {meta['scale_m_per_px']} m/px)\n"
    f"Nguồn: {data['reference_source']}"
)
ax.set_title(title, color="#e0e0e0", fontsize=9.5, pad=10)
ax.set_xlabel("x (pixel [0, 511])", color="#90caf9")
ax.set_ylabel("y (pixel [0, 511])", color="#90caf9")
ax.tick_params(colors="#90caf9")
for spine in ax.spines.values():
    spine.set_edgecolor("#37474f")

for c in data["circles"]:
    unc = "_uncertain" in c["crater_id"]
    color = "#ff9800" if unc else "#00e5ff"
    circle = plt.Circle((c["x"], c["y"]), c["r"], fill=False, color=color, linewidth=1.5)
    ax.add_patch(circle)
    ax.annotate(c["crater_id"], (c["x"], c["y"] - c["r"] - 4), color=color, fontsize=8, ha="center", fontweight="bold")

legend_elements = [
    mpatches.Patch(facecolor="none", edgecolor="#00e5ff", label="Chắc chắn (C1, C2, C3)"),
    mpatches.Patch(facecolor="none", edgecolor="#ff9800", label="Uncertain (C4_uncertain)"),
]
ax.legend(handles=legend_elements, loc="upper right", facecolor="#263238", edgecolor="#455a64", labelcolor="#e0e0e0", fontsize=8)

plt.tight_layout()
fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
print(f"Rendered overlay: {out_path}")
