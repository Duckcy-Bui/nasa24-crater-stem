"""S1-11: tạo phiếu kiểm tra hướng nắng bằng mắt (S1-04 mục 6.3).

Với mỗi ảnh có hướng nắng (side_only) hoặc phía nắng ứng viên (side_candidate):
  1. chạy tiền xử lý + Hough, lấy các ứng viên nhiều phiếu nhất nằm trọn trong ảnh
     (số phiếu Hough không dùng độ sáng hai nửa hố nên không gây lập luận vòng tròn);
  2. phóng to từng hố, vẽ mũi tên chỉ về phía Mặt Trời theo metadata;
  3. ghi các hố tham chiếu vào data/s111_sun_checks.json với verdict="pending".

Người kiểm tra mở ảnh trong docs/evidence/s1-11/, trả lời cho mỗi hố:
"phía tối của thành hố có nằm về phía mũi tên không?", rồi sửa verdict của ảnh
thành consistent / inverted / unclear và điền checked_by, checked_on.
Hố tham chiếu không được dùng làm ví dụ đánh giá S1-11.
Nếu không ứng viên nào là hố rõ, ghi manual_craters (x, y, r tự chọn) cho ảnh đó
rồi chạy lại: phiếu được vẽ lại với đúng các hố đó.

    python scripts/s111_sun_check_sheet.py
    python scripts/s111_sun_check_sheet.py --processed-dir <thư mục ảnh S1-06>
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

from src.hough import detect_circles, resolve_hough_params  # noqa: E402
from src.pipeline import load_image, radius_range  # noqa: E402
from src.postprocessing import DEFAULT_PARAMS, SIDE_AZIMUTH, SUN_CHECKS_PATH, sun_vector  # noqa: E402
from src.preprocessing import preprocess  # noqa: E402

EVIDENCE = ROOT / "docs" / "evidence" / "s1-11"
QUESTION = "Phía tối của thành hố có nằm về phía mũi tên (phía Mặt Trời) không?"


def stated_side(metadata: dict) -> tuple[str, float, str] | None:
    """Phía nắng cần kiểm tra: (tên, phương vị, nguồn) hoặc None nếu không có gì để kiểm."""
    sun = metadata["sun"]
    if sun.get("quality") in ("measured", "side_only") and sun.get("azimuth_deg") is not None:
        return sun.get("side") or sun["quality"], float(sun["azimuth_deg"]), "metadata"
    if sun.get("side_candidate") in SIDE_AZIMUTH:
        side = sun["side_candidate"]
        return side, SIDE_AZIMUTH[side], "side_candidate (chưa xác minh)"
    return None


def reference_craters(image_id: str, processed: Path, count: int) -> tuple[np.ndarray, list[dict]]:
    metadata, image, valid = load_image(image_id, processed)
    pre = preprocess(image, metadata, None, valid_mask=valid)
    hough = resolve_hough_params({})
    r_min, r_max = radius_range(metadata, hough)
    circles = detect_circles(pre["edges"], r_min, r_max, hough, theta=pre["theta"])
    inside = [c for c in circles if c["r"] >= 8 and c["r"] <= c["x"] <= 511 - c["r"] and c["r"] <= c["y"] <= 511 - c["r"]]
    inside.sort(key=lambda c: -(c["votes"] or 0) / c["r"])  # phiếu trên chu vi: vòng rõ, không thiên vị hố to
    chosen = []
    for c in inside:
        if all(np.hypot(c["x"] - d["x"], c["y"] - d["y"]) > c["r"] + d["r"] for d in chosen):
            chosen.append(c)
        if len(chosen) == count:
            break
    return pre["gray"], chosen


def render(path: Path, gray: np.ndarray, metadata: dict, side: tuple, craters: list[dict]) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    ux, uy = sun_vector(side[1], metadata["north_angle_deg"])
    cols = max(1, math.ceil(len(craters) / 2))
    layout = [["all"] * 2 + [str(i) for i in range(1, cols + 1)],
              ["all"] * 2 + [str(i) for i in range(cols + 1, 2 * cols + 1)]]
    fig, grid = plt.subplot_mosaic(layout, figsize=(3.2 * (cols + 2), 7), constrained_layout=True)
    axes = [grid["all"]] + [grid[str(i)] for i in range(1, 2 * cols + 1)]
    for ax in axes[len(craters) + 1:]:
        ax.axis("off")
    axes[0].imshow(gray, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title(f"{metadata['image_id']}\nnắng {side[0]} ({side[1]:g}°), góc tới {metadata['sun']['incidence_deg']}°", fontsize=9)
    axes[0].annotate("", xy=(256 + 150 * ux, 256 + 150 * uy), xytext=(256, 256),
                     arrowprops=dict(color="yellow", width=3, headwidth=12))
    axes[0].text(256 + 170 * ux, 256 + 170 * uy, "Mặt Trời", color="yellow", ha="center", fontsize=9)
    for i, c in enumerate(craters, 1):
        axes[0].add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color="cyan", lw=1))
        axes[0].text(c["x"], c["y"] - c["r"] - 4, str(i), color="cyan", ha="center", fontsize=10, weight="bold")
        pad = max(32, int(c["r"] * 2.5))
        x0, x1 = max(0, int(c["x"]) - pad), min(512, int(c["x"]) + pad)
        y0, y1 = max(0, int(c["y"]) - pad), min(512, int(c["y"]) + pad)
        ax = axes[i]
        ax.imshow(gray[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=1, interpolation="bilinear", extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5))
        ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color="cyan", lw=0.8, ls="--"))
        L = c["r"] * 1.4
        ax.annotate("", xy=(c["x"] + L * ux, c["y"] + L * uy), xytext=(c["x"], c["y"]),
                    arrowprops=dict(color="yellow", width=2, headwidth=9))
        ax.set_title(f"Hố {i}: x={c['x']:.0f}, y={c['y']:.0f}, r={c['r']:.0f}", fontsize=9)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(QUESTION + "  Mũi tên vàng chỉ về phía Mặt Trời theo metadata.", fontsize=10)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    parser.add_argument("--count", type=int, default=6, help="số hố tham chiếu mỗi ảnh")
    args = parser.parse_args(argv)
    processed = Path(args.processed_dir)

    existing = json.loads(SUN_CHECKS_PATH.read_text(encoding="utf-8")) if SUN_CHECKS_PATH.exists() else {}
    old = {c["image_id"]: c for c in existing.get("checks", [])}
    checks = []
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for meta_path in sorted(processed.glob("*.json")):
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if "sun" not in metadata or not (processed / f"{metadata['image_id']}.npy").exists():
            continue
        side = stated_side(metadata)
        image_id = metadata["image_id"]
        incidence = metadata["sun"].get("incidence_deg")
        if side is None or incidence is None or incidence < DEFAULT_PARAMS["min_incidence_deg"]:
            continue  # S1-11 không chấm các ảnh này, không cần nhìn
        prev = old.get(image_id, {})
        if prev.get("verdict") not in (None, "pending"):  # không ghi đè kết quả người kiểm tra đã điền
            checks.append(prev)
            print(f"giữ nguyên   {image_id}: {prev['verdict']}")
            continue
        manual = prev.get("manual_craters") or []
        if manual:  # người kiểm tra tự chọn hố: vẽ đúng các hố đó, không dùng Hough
            gray = load_image(image_id, processed)[1]
            craters = [{"x": float(c["x"]), "y": float(c["y"]), "r": float(c["r"])} for c in manual]
        else:
            gray, craters = reference_craters(image_id, processed, args.count)
        evidence = EVIDENCE / f"sun_check_{image_id}.png"
        render(evidence, gray, metadata, side, craters)
        checks.append({
            "image_id": image_id,
            "stated_side": side[0], "stated_azimuth_deg": side[1], "stated_from": side[2],
            "incidence_deg": metadata["sun"]["incidence_deg"],
            "reference_craters": [{"n": i, "x": c["x"], "y": c["y"], "r": c["r"], "dark_side": None}
                                  for i, c in enumerate(craters, 1)],
            "manual_craters": manual,
            "verdict": "pending", "checked_by": None, "checked_on": None, "note": None,
            "evidence": evidence.relative_to(ROOT).as_posix(),
        })
        print(f"đã tạo phiếu {image_id}: {len(craters)} hố → {evidence.relative_to(ROOT)}")

    record = {
        "schema": "s111_sun_checks/1",
        "question": QUESTION,
        "how_to_fill": ("Với mỗi hố: dark_side = 'toward_sun' nếu phía tối nằm về phía mũi tên, 'away' nếu ngược lại, "
                        "'unclear' nếu không nhìn rõ. verdict của ảnh: 'consistent' khi các hố nhìn rõ đều toward_sun; "
                        "'inverted' khi các hố nhìn rõ đều away; 'unclear' khi không đủ hố nhìn rõ hoặc mâu thuẫn. "
                        "Nếu không ứng viên nào là hố rõ: ghi manual_craters = [{\"x\":..,\"y\":..,\"r\":..}] rồi chạy lại script để vẽ phiếu mới. "
                        "Điền checked_by, checked_on (YYYY-MM-DD). Hố tham chiếu không dùng làm ví dụ đánh giá S1-11."),
        "checks": checks,
    }
    SUN_CHECKS_PATH.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Đã ghi {SUN_CHECKS_PATH.relative_to(ROOT)} ({len(checks)} ảnh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
