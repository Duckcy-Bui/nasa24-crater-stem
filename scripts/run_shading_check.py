"""S1-11: chấm sáng–tối các ứng viên Hough trên ảnh thật.

Một ảnh (ví dụ hố đúng / ứng viên sai):
    python scripts/run_shading_check.py moon_ap16_m132732855l_c01
Cả bộ (ảnh nào được chấm, ảnh nào không và vì sao):
    python scripts/run_shading_check.py --all
Xem trước khi chưa điền phiếu kiểm tra bằng mắt (KHÔNG dùng làm kết quả):
    python scripts/run_shading_check.py moon_ap16_m132732855l_c01 --preview

Mỗi ảnh lưu outputs/s111_<image_id>_<UTC>/: craters.json (vòng + trường shading),
report.json (căn cứ hướng nắng, số vòng mỗi nhãn, tham số), candidates.csv,
overlay.png và examples.png (các vòng điểm cao nhất/thấp nhất phóng to để người
kiểm tra xác nhận bằng mắt). Hố tham chiếu trong data/s111_sun_checks.json
được đánh dấu và không đưa vào examples.png.
--all ghi docs/evidence/s1-11/s111_tong_hop.csv (đổi bằng --summary-csv; --preview ghi vào --output-root).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.hough import detect_circles, resolve_hough_params  # noqa: E402
from src.pipeline import load_image, radius_range  # noqa: E402
from src.postprocessing import load_sun_checks, score_candidates, sun_vector  # noqa: E402
from src.preprocessing import preprocess  # noqa: E402

COLORS = {"consistent": "#2ecc71", "inverted": "#ff4d4d", "unclear": "#f1c40f", "not_checked": "#9aa0a6"}
LABELS = {"consistent": "hợp sáng–tối", "inverted": "ngược sáng–tối", "unclear": "không rõ", "not_checked": "không kiểm tra"}
SUMMARY_CSV = ROOT / "docs" / "evidence" / "s1-11" / "s111_tong_hop.csv"


def code_version() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return (head.stdout.strip() or "unknown") + ("+working-tree" if dirty.stdout.strip() else "")


def near_reference(c: dict, refs: list[dict]) -> bool:
    return any(np.hypot(c["x"] - r["x"], c["y"] - r["y"]) <= max(r["r"], c["r"]) for r in refs)


def run_one(image_id: str, processed: Path, checks: dict, preview: bool) -> tuple[list[dict], dict, np.ndarray, dict]:
    metadata, image, valid = load_image(image_id, processed)
    pre = preprocess(image, metadata, None, valid_mask=valid)
    hough = resolve_hough_params({})
    r_min, r_max = radius_range(metadata, hough)
    raw = detect_circles(pre["edges"], r_min, r_max, hough, theta=pre["theta"])
    params = {"sun_checks": checks}
    if preview:
        params["require_visual_check"] = False
    scored, report = score_candidates(raw, pre["gray"], metadata, params, valid_mask=pre["valid_mask"])
    refs = (checks.get(image_id) or {}).get("reference_craters", []) + (checks.get(image_id) or {}).get("manual_craters", [])
    for c in scored:
        c["shading"]["reference_crater"] = near_reference(c, refs)
    report.update(preview=preview, hough_circles=len(raw), radius_px=[r_min, r_max],
                  reference_craters_excluded=sum(c["shading"]["reference_crater"] for c in scored))
    return scored, report, pre["gray"], metadata


def render_overlay(path: Path, gray: np.ndarray, metadata: dict, scored: list[dict], report: dict) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(8, 8.4), constrained_layout=True)
    ax.imshow(gray, cmap="gray", vmin=0, vmax=1, extent=(-0.5, 511.5, 511.5, -0.5))
    for c in scored:
        s = c["shading"]
        ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color=COLORS[s["status"]],
                            lw=1.4, ls=":" if s["reference_crater"] else "-"))
    if report["checked"]:
        ux, uy = report["sun_vector_xy"]
        ax.annotate("", xy=(256 + 120 * ux, 256 + 120 * uy), xytext=(256, 256),
                    arrowprops=dict(color="yellow", width=3, headwidth=12))
    counts = report["counts"]
    handles = [Line2D([], [], color=COLORS[k], label=f"{LABELS[k]} ({counts[k]})") for k in COLORS]
    handles.append(Line2D([], [], color="white", ls=":", label="hố tham chiếu (không tính ví dụ)"))
    ax.legend(handles=handles, loc="lower right", fontsize=8, facecolor="#222", labelcolor="white")
    note = "XEM TRƯỚC — chưa kiểm tra hướng nắng bằng mắt, không dùng làm kết quả" if report["preview"] else ""
    head = (f"nắng {report['azimuth_deg']:g}° ({report['quality']}), góc tới {report['incidence_deg']}° — mũi tên chỉ về phía Mặt Trời"
            if report["checked"] else f"KHÔNG CHẤM: {report['reason']}")
    ax.set_title(f"S1-11 · {metadata['image_id']}\n{head}\n{note}", fontsize=9, color="red" if note else "black")
    ax.set_xticks([]); ax.set_yticks([])
    fig.savefig(path, dpi=100)
    plt.close(fig)


def render_examples(path: Path, gray: np.ndarray, scored: list[dict], report: dict, per_group: int = 4) -> list[dict]:
    """Phóng to các vòng điểm cao nhất (ứng viên 'hợp') và thấp nhất (ứng viên 'ngược')."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    pool = [c for c in scored if c["shading"]["score"] is not None and not c["shading"]["reference_crater"]]
    pool.sort(key=lambda c: -c["shading"]["score"])
    top = pool[:per_group]
    bottom = [c for c in pool[::-1][:per_group] if c not in top]
    rows = [("Điểm cao nhất", top), ("Điểm thấp nhất", bottom)]
    fig, axes = plt.subplots(2, per_group, figsize=(3.2 * per_group, 7), constrained_layout=True, squeeze=False)
    ux, uy = report["sun_vector_xy"]
    chosen = []
    for row, (name, group) in enumerate(rows):
        for col in range(per_group):
            ax = axes[row][col]
            ax.set_xticks([]); ax.set_yticks([])
            if col >= len(group):
                ax.axis("off")
                continue
            c = group[col]
            pad = max(32, int(c["r"] * 2.5))
            x0, x1 = max(0, int(c["x"]) - pad), min(512, int(c["x"]) + pad)
            y0, y1 = max(0, int(c["y"]) - pad), min(512, int(c["y"]) + pad)
            ax.imshow(gray[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=1, interpolation="bilinear",
                      extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5))
            s = c["shading"]
            ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color=COLORS[s["status"]], lw=1.2))
            L = c["r"] * 1.4
            ax.annotate("", xy=(c["x"] + L * ux, c["y"] + L * uy), xytext=(c["x"], c["y"]),
                        arrowprops=dict(color="yellow", width=2, headwidth=9))
            ax.set_title(f"{name}: {c['crater_id']}\nscore={s['score']:+.2f} (gốc {s['score_raw']:+.2f}) · {LABELS[s['status']]}",
                         fontsize=8)
            chosen.append({"group": name, "crater_id": c["crater_id"], "x": c["x"], "y": c["y"], "r": c["r"],
                           "score": s["score"], "status": s["status"], "visual_verdict": None})
    fig.suptitle("Mũi tên vàng chỉ về phía Mặt Trời. Hố lõm thật: phía tối nằm về phía mũi tên. "
                 "Người kiểm tra ghi visual_verdict cho từng vòng trong report.json.", fontsize=9)
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return chosen


def save(image_id: str, scored: list[dict], report: dict, gray: np.ndarray, metadata: dict, output_root: Path,
         render: bool) -> Path:
    directory = output_root / f"s111_{image_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    directory.mkdir(parents=True, exist_ok=False)
    report["code_version"] = code_version()
    machine = {"schema_version": "1.0", "data_kind": metadata["data_kind"], "image_id": image_id,
               "source": "machine", "reference_source": None, "circles": scored}
    (directory / "craters.json").write_text(json.dumps(machine, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (directory / "candidates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["crater_id", "x", "y", "r", "votes", "score", "score_raw", "status", "reference_crater", "reason"])
        for c in scored:
            s = c["shading"]
            w.writerow([c["crater_id"], c["x"], c["y"], c["r"], c["votes"], s["score"], s["score_raw"], s["status"],
                        s["reference_crater"], s["reason"]])
    if render:
        render_overlay(directory / "overlay.png", gray, metadata, scored, report)
        if report["checked"]:
            report["examples"] = render_examples(directory / "examples.png", gray, scored, report)
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S1-11: chấm sáng–tối ứng viên Hough")
    parser.add_argument("image_id", nargs="?")
    parser.add_argument("--all", action="store_true", help="chạy cả bộ, ghi bảng tổng hợp")
    parser.add_argument("--preview", action="store_true", help="bỏ yêu cầu kiểm tra bằng mắt (chỉ để xem trước)")
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    parser.add_argument("--output-root", default=str(ROOT / "outputs"))
    parser.add_argument("--summary-csv", default=None,
                        help="bảng tổng hợp của --all (mặc định docs/evidence/s1-11/s111_tong_hop.csv; "
                             "với --preview mặc định ghi vào --output-root để không ghi đè minh chứng)")
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args(argv)
    if bool(args.image_id) == args.all:
        parser.error("cần đúng một trong: image_id hoặc --all")
    processed = Path(args.processed_dir)
    checks = load_sun_checks()

    if args.image_id:
        scored, report, gray, metadata = run_one(args.image_id, processed, checks, args.preview)
        directory = save(args.image_id, scored, report, gray, metadata, Path(args.output_root), not args.no_render)
        print(f"Đã lưu: {directory}")
        print("  " + (f"chấm: {report['counts']}" if report["checked"] else f"không chấm: {report['reason']}"))
        return 0

    ids = sorted(p.stem for p in processed.glob("*.json")
                 if (processed / f"{p.stem}.npy").exists() and "sun" in json.loads(p.read_text(encoding="utf-8")))
    rows = []
    for image_id in ids:
        scored, report, gray, metadata = run_one(image_id, processed, checks, args.preview)
        directory = save(image_id, scored, report, gray, metadata, Path(args.output_root), not args.no_render)
        k = report["counts"]
        rows.append([image_id, metadata["source_stt"], metadata["sun"].get("quality"), metadata["sun"].get("incidence_deg"),
                     report["visual_check"], "có" if report["checked"] else "không", report["reason"] or "",
                     " | ".join(report["sun_basis"]), report["hough_circles"], k["consistent"], k["inverted"],
                     k["unclear"], k["not_checked"], report["preview"], directory.name])
        print(f"{image_id:30s} {'chấm' if report['checked'] else 'bỏ qua'}: {report['reason'] or k}")
    summary_csv = Path(args.summary_csv) if args.summary_csv else (
        Path(args.output_root) / "s111_tong_hop_xem_truoc.csv" if args.preview else SUMMARY_CSV)
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "stt", "sun_quality", "incidence_deg", "kiem_tra_bang_mat", "duoc_cham", "ly_do_khong_cham",
                    "can_cu_huong_nang", "ung_vien_hough", "hop", "nguoc", "khong_ro", "khong_kiem_tra", "xem_truoc", "run_dir"])
        w.writerows(rows)
    print(f"Đã ghi {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
