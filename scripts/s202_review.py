"""S2-02: rà tiền xử lý/biên và kiểm tra ứng viên theo sáng–tối trên một ảnh.

    python scripts/s202_review.py moon_ap16_m132732855l_c01
    python scripts/s202_review.py moon_ap16_m132732855l_c01 --processed-dir <thư mục ảnh S1-06>

Ghi vào docs/evidence/s2-02/<image_id>/:
  buoc_bien.png      ảnh gốc → B3 → B4 → B5 → |G| → B7 → B8 → loại biên (bóng / còn lại)
  ung_vien.png       ứng viên Hough tô theo lớp máy (rim / shadow_edge / texture) và nhãn sáng–tối
  phieu_nhan.png     phiếu gán nhãn MÙ: ứng viên phóng to, đánh số, KHÔNG hiện lớp máy
  candidates.csv     từng vòng: đặc trưng, lớp máy, sáng–tối, nhãn người (nếu có)
  report.json        tham số, thời gian, số đếm; nếu đã có nhãn: ma trận nhầm lẫn và bảng thử lọc
Mẫu nhãn: data/s202_labels/<image_id>.json (tạo nếu chưa có; không ghi đè nhãn đã điền).
Nhãn hợp lệ: rim (vành hố thật) / shadow_edge (ranh giới bóng đổ) /
texture (biên kết cấu, không phải hố) / unclear.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np  # noqa: E402 - đặt backend trước các thư viện ảnh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.hough import detect_circles, resolve_hough_params  # noqa: E402 - cần ROOT
from src.pipeline import load_image, radius_range  # noqa: E402 - cần ROOT
from src.postprocessing import (  # noqa: E402 - cần ROOT
    REVIEW_CLASSES,
    apply_filter,
    resolve_review_params,
    review_candidates,
    score_candidates,
    shadow_regions,
    sun_vector,
)
from src.preprocessing import preprocess  # noqa: E402 - cần ROOT

EVIDENCE = ROOT / "docs" / "evidence" / "s2-02"
LABELS = ROOT / "data" / "s202_labels"
COLORS = {"rim": "#2ecc71", "shadow_edge": "#ff4d4d", "texture": "#f1c40f", "unclear": "#9aa0a6"}
FILTERS = [
    ("bỏ shadow_edge", ("shadow_edge",), ()),
    ("bỏ texture", ("texture",), ()),
    ("bỏ shadow_edge + texture", ("shadow_edge", "texture"), ()),
    ("bỏ sáng–tối ngược", (), ("inverted",)),
    ("bỏ shadow_edge + texture + ngược", ("shadow_edge", "texture"), ("inverted",)),
]


def run(
    image_id: str,
    processed: Path,
    preprocess_params: dict | None = None,
    review_params: dict | None = None,
) -> dict:
    """Chạy chuỗi xử lý cho image_id từ processed (Path), trả dict kết quả.

    preprocess_params/review_params là dict ghi đè hoặc None; trả ảnh,
    vòng theo px, lớp máy/sáng–tối và thời gian theo giây. Chỉ đọc dữ liệu,
    không ghi kết quả; các khối theo mục 3.2–3.4 báo cáo.
    """
    metadata, image, valid = load_image(image_id, processed)
    t = time.perf_counter()
    pre = preprocess(image, metadata, preprocess_params, valid_mask=valid)
    t_pre = time.perf_counter() - t
    hough = resolve_hough_params({})
    t = time.perf_counter()
    raw = detect_circles(pre["edges"], *radius_range(metadata, hough), hough, theta=pre["theta"])
    t_hough = time.perf_counter() - t
    t = time.perf_counter()
    scored, shading = score_candidates(
        raw, pre["gray"], metadata, {}, valid_mask=pre["valid_mask"]
    )
    reviewed, review = review_candidates(scored, pre, review_params)
    t_post = time.perf_counter() - t
    return {
        "metadata": metadata,
        "image": image,
        "pre": pre,
        "circles": reviewed,
        "shading": shading,
        "review": review,
        "seconds": {
            "preprocess": round(t_pre, 2),
            "hough": round(t_hough, 2),
            "shading_review": round(t_post, 2),
        },
    }


def match(c: dict, ref: dict) -> bool:
    """Nhận c/ref (dict x, y, r theo px); trả bool theo hai điều kiện cục bộ.

    Đòi lệch tâm và lệch r đều <=0,5*r_ref. Có thêm điều kiện r, nên không
    đồng nhất với quy tắc ghép chỉ xét tâm ở (2.20); không sửa vòng.
    """
    return (
        math.hypot(c["x"] - ref["x"], c["y"] - ref["y"]) <= 0.5 * ref["r"]
        and abs(c["r"] - ref["r"]) <= 0.5 * ref["r"]
    )


def load_labels(image_id: str) -> dict | None:
    """Đọc LABELS/<image_id>.json; trả giá trị JSON hoặc None nếu file chưa có.

    image_id là str; không tạo file hay tự xác nhận nhãn người.
    """
    path = LABELS / f"{image_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_label_template(image_id: str, circles: list[dict]) -> Path:
    """Nhận image_id (str), circles (list vòng px); trả Path file nhãn mẫu.

    Chỉ tạo LABELS/<image_id>.json khi chưa có, không ghi đè nhãn đã điền;
    tạo các ô người gán/kiểm trống, không tự xác nhận theo mục 4.3.
    """
    path = LABELS / f"{image_id}.json"
    if path.exists():
        return path
    LABELS.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "s202_labels/1",
        "image_id": image_id,
        "how_to_fill": (
            "Nhìn phieu_nhan.png. label: rim = vành hố thật; "
            "shadow_edge = ranh giới bóng đổ địa hình; "
            "texture = biên kết cấu/đốm, không phải hố; unclear = không chắc. "
            "Ghi labeled_by, labeled_on; "
            "người thứ hai kiểm chéo ghi reviewed_by, reviewed_on và sửa label nếu không đồng ý."
        ),
        "labeled_by": None,
        "labeled_on": None,
        "reviewed_by": None,
        "reviewed_on": None,
        "candidates": [
            {
                "n": i,
                "crater_id": c["crater_id"],
                "x": c["x"],
                "y": c["y"],
                "r": c["r"],
                "label": None,
            }
            for i, c in enumerate(circles, 1)
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def human_labels(labels: dict | None, circles: list[dict]) -> dict:
    """Ghép labels (dict hoặc None) với circles, trả dict mã vòng → nhãn người.

    Đòi từng lệch x/y/r tuyệt đối <0,5 px; không dựa vào mã vòng cũ.
    Chỉ nhận tên lớp hợp lệ, chưa kiểm người ký/kiểm chéo; không ghi file,
    phục vụ nhãn mù mục 4.3, khác ghép tâm chuẩn hóa ở (2.20).
    """
    if not labels:
        return {}
    out = {}
    for c in circles:
        for label in labels["candidates"]:
            if (
                label.get("label") in REVIEW_CLASSES
                and abs(label["x"] - c["x"]) < 0.5
                and abs(label["y"] - c["y"]) < 0.5
                and abs(label["r"] - c["r"]) < 0.5
            ):
                out[c["crater_id"]] = label["label"]
    return out


def evaluate(circles: list[dict], human: dict) -> dict:
    """Nhận circles có review/shading và human (dict mã → nhãn), trả dict đánh giá.

    Chỉ tính vòng nhãn rõ: ma trận lớp máy × nhãn người, số loại/mất rim
    và tỷ lệ rim còn giữ. Không ghi file hay suy Precision toàn ảnh;
    đây là bảng nhãn mù mục 4.6, không phải Recall_known trên nhãn thưa.
    """
    labeled = [
        c for c in circles if human.get(c["crater_id"]) in ("rim", "shadow_edge", "texture")
    ]
    confusion = {m: {h: 0 for h in ("rim", "shadow_edge", "texture")} for m in REVIEW_CLASSES}
    for c in labeled:
        confusion[c["review"]["class"]][human[c["crater_id"]]] += 1
    n_rim = sum(human[c["crater_id"]] == "rim" for c in labeled)
    rows = [
        {
            "cach_loc": "không lọc",
            "loai": 0,
            "loai_nham_ho_that": 0,
            "con_lai": len(labeled),
            "ho_that_con_lai": n_rim,
            "ty_le_ho_that_trong_con_lai": round(n_rim / len(labeled), 3) if labeled else None,
        }
    ]
    for name, classes, shading in FILTERS:
        kept, removed = apply_filter(labeled, classes, shading)
        kr = sum(human[c["crater_id"]] == "rim" for c in kept)
        rows.append(
            {
                "cach_loc": name,
                "loai": len(removed),
                "loai_nham_ho_that": sum(human[c["crater_id"]] == "rim" for c in removed),
                "con_lai": len(kept),
                "ho_that_con_lai": kr,
                "ty_le_ho_that_trong_con_lai": round(kr / len(kept), 3) if kept else None,
            }
        )
    return {
        "n_labeled": len(labeled),
        "n_rim": n_rim,
        "confusion_machine_x_human": confusion,
        "filters": rows,
    }


def steps_figure(path: Path, r: dict) -> None:
    """Nhận path (Path) và r từ run; ghi PNG các bước biên rồi đóng hình, trả None.

    Hiển thị B3–B8 và biên bóng/còn lại theo mục 3.2–3.4, không đổi số liệu.
    """
    import matplotlib.pyplot as plt

    pre = r["pre"]
    big, sh = shadow_regions(pre["gray"], pre["edges"], pre["valid_mask"], r["review"]["params"])
    types = np.dstack([pre["gray"]] * 3) * 0.45
    types[pre["edges"] & ~sh] = (0.2, 1, 1)
    types[sh] = (1, 0.2, 0.2)
    mag = np.clip(pre["mag"] / np.percentile(pre["mag"], 99), 0, 1)
    p = pre["params"]
    panels = [
        ("Ảnh gốc (.npy S1-06)", r["image"]),
        ("B3 chuẩn hóa", pre["gray"]),
        (
            f"B4 CLAHE clip={p['clahe_clip']:g}",
            pre["enhanced"],
        ),
        (
            f"B5 Gauss σ={p['gauss_sigma']:g}",
            pre["smooth"],
        ),
        ("B6 |G|", mag),
        (
            f"B7 Canny P{p['canny_high_pct']:g} ({int(pre['edges_canny'].sum())} px)",
            pre["edges_canny"],
        ),
        (
            f"B8 sau mặt nạ ({int(pre['edges'].sum())} px)",
            pre["edges"],
        ),
        (
            f"Loại biên: đỏ = ranh giới bóng "
            f"({r['review']['shadow_edge_fraction_of_edges']:.0%}), xanh = còn lại",
            types,
        ),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.6), constrained_layout=True)
    for ax, (name, data) in zip(axes.ravel(), panels):
        ax.imshow(data, cmap=None if np.ndim(data) == 3 else "gray", vmin=0, vmax=1)
        ax.set_title(name, fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(f"S2-02 · {r['metadata']['image_id']} · biên từng bước", fontsize=11)
    fig.savefig(path, dpi=60)
    plt.close(fig)


def candidates_figure(path: Path, r: dict) -> None:
    """Nhận path (Path), r từ run; ghi PNG vòng có lớp máy/sáng–tối, trả None.

    Vòng theo px; mũi tên từ vector nắng nếu đủ căn cứ (2.17), mục 3.4;
    đóng figure sau ghi, màu lớp máy không thay nhãn người.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle

    fig, ax = plt.subplots(figsize=(8.5, 9), constrained_layout=True)
    ax.imshow(r["pre"]["gray"], cmap="gray", vmin=0, vmax=1, extent=(-0.5, 511.5, 511.5, -0.5))
    styles = {"consistent": "-", "inverted": "--", "unclear": ":", "not_checked": "-"}
    for c in r["circles"]:
        ax.add_patch(
            Circle(
                (c["x"], c["y"]),
                max(c["r"], 3),
                fill=False,
                color=COLORS[c["review"]["class"]],
                ls=styles[c["shading"]["status"]],
                lw=1.3,
            )
        )
    if r["shading"]["checked"]:
        ux, uy = r["shading"]["sun_vector_xy"]
        ax.annotate(
            "",
            xy=(256 + 110 * ux, 256 + 110 * uy),
            xytext=(256, 256),
            arrowprops=dict(color="yellow", width=3, headwidth=11),
        )
    k = r["review"]["counts"]
    h = [Line2D([], [], color=COLORS[c], label=f"{c} ({k[c]})") for c in REVIEW_CLASSES]
    h += [
        Line2D([], [], color="white", ls=s, label=f"sáng–tối {n}")
        for n, s in (("hợp", "-"), ("ngược", "--"), ("không rõ", ":"))
    ]
    ax.legend(handles=h, loc="lower right", fontsize=7, facecolor="#222", labelcolor="white")
    sh = r["shading"]
    head = (
        f"hướng nắng {sh['azimuth_deg']:g}° ({sh['quality']}) — mũi tên về phía Mặt Trời"
        if sh["checked"]
        else f"sáng–tối BỎ QUA: {sh['reason']}"
    )
    ax.set_title(
        f"S2-02 · {r['metadata']['image_id']} · màu = lớp máy, nét = sáng–tối\n{head}", fontsize=9
    )
    ax.set_xticks([])
    ax.set_yticks([])
    fig.savefig(path, dpi=65)
    plt.close(fig)


def label_sheet(path: Path, r: dict) -> None:
    """Nhận path (Path), r từ run; ghi phiếu PNG ứng viên phóng to, trả None.

    Chỉ hiện ảnh/vòng/số thứ tự, không hiện lớp máy hay điểm; đóng hình.
    Không ghi nhãn người, theo quy tắc nhãn mù ở mục 4.3.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    circles, gray = r["circles"], r["pre"]["gray"]
    cols = 10
    rows = math.ceil(len(circles) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(2.0 * cols, 2.15 * rows), squeeze=False)
    for i, ax in enumerate(axes.ravel()):
        ax.set_xticks([])
        ax.set_yticks([])
        if i >= len(circles):
            ax.axis("off")
            continue
        c = circles[i]
        pad = max(16, int(c["r"] * 3))
        x0, x1 = max(0, int(c["x"]) - pad), min(512, int(c["x"]) + pad)
        y0, y1 = max(0, int(c["y"]) - pad), min(512, int(c["y"]) + pad)
        ax.imshow(
            gray[y0:y1, x0:x1],
            cmap="gray",
            vmin=0,
            vmax=1,
            interpolation="bilinear",
            extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5),
        )
        ax.add_patch(Circle((c["x"], c["y"]), c["r"], fill=False, color="cyan", lw=0.8, ls="--"))
        ax.set_title(f"{i + 1}", fontsize=9)
    if r["shading"]["checked"]:
        ux, uy = r["shading"]["sun_vector_xy"]
        side = "trái" if ux < -0.5 else "phải" if ux > 0.5 else "lên" if uy < 0 else "xuống"
        sun = f"Mặt Trời ở phía {side} ảnh."
    else:
        sun = "Ảnh không có hướng nắng đủ căn cứ."
    fig.suptitle(
        f"{r['metadata']['image_id']} — phiếu gán nhãn (không hiện kết quả máy). {sun} "
        "Ghi rim / shadow_edge / texture / unclear cho từng số.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=48)
    plt.close(fig)


HUMAN_COLORS = {
    "rim": "#2ecc71",
    "shadow_edge": "#ff4d4d",
    "texture": "#f1c40f",
    "unclear": "#9aa0a6",
}


def filter_figure(path: Path, r: dict, human: dict, classes=("shadow_edge", "texture")) -> None:
    """Nhận path, r, human (dict mã → nhãn) và classes (tên lớp cần bỏ).

    Trả None; ghi PNG trước/sau lọc, tâm/r theo px, màu theo nhãn người
    rồi đóng hình. Không sửa nhãn hoặc tự xác nhận kiểm chéo; mục 4.6.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle

    kept, removed = apply_filter(r["circles"], classes)
    fig, axes = plt.subplots(1, 2, figsize=(15, 8), constrained_layout=True)
    for ax, (title, items) in zip(
        axes,
        (
            (f"Trước: {len(r['circles'])} ứng viên Hough", r["circles"]),
            (f"Sau khi bỏ {' + '.join(classes)}: còn {len(kept)}, loại {len(removed)}", kept),
        ),
    ):
        ax.imshow(r["pre"]["gray"], cmap="gray", vmin=0, vmax=1, extent=(-0.5, 511.5, 511.5, -0.5))
        for c in items:
            lab = human.get(c["crater_id"], "unclear")
            ax.add_patch(
                Circle(
                    (c["x"], c["y"]),
                    max(c["r"], 3),
                    fill=False,
                    color=HUMAN_COLORS[lab],
                    lw=2.2 if lab == "rim" else 1.0,
                )
            )
        ax.set_title(title, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    lost = [c for c in removed if human.get(c["crater_id"]) == "rim"]
    for c in lost:
        axes[0].annotate(
            "hố thật bị loại",
            xy=(c["x"], c["y"]),
            xytext=(c["x"] + 40, c["y"] - 40),
            color="white",
            fontsize=8,
            arrowprops=dict(color="white", width=1, headwidth=6),
        )
    h = [Line2D([], [], color=v, label=f"nhãn người: {k}") for k, v in HUMAN_COLORS.items()]
    axes[1].legend(handles=h, loc="lower right", fontsize=8, facecolor="#222", labelcolor="white")
    fig.suptitle(
        f"S2-02 · {r['metadata']['image_id']} · "
        "lọc theo lớp máy, tô màu theo nhãn người (đã kiểm chéo)",
        fontsize=11,
    )
    fig.savefig(path, dpi=60)
    plt.close(fig)


def examples_figure(path: Path, r: dict, human: dict) -> None:
    """Nhận path (Path), r từ run và human; ghi PNG ví dụ theo nhãn, trả None.

    Hiện rim/bóng/kết cấu, lớp máy và sáng–tối; tọa độ theo px, đóng hình.
    Không thay nhãn người hoặc tính độ đo mới, theo mục 4.6.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    by = {
        k: [c for c in r["circles"] if human.get(c["crater_id"]) == k]
        for k in ("rim", "shadow_edge", "texture")
    }
    by["texture"] = sorted(by["texture"], key=lambda c: -c["votes"])
    names = {"rim": "Hố đúng", "shadow_edge": "Ranh giới bóng", "texture": "Biên kết cấu"}
    fig, axes = plt.subplots(3, 5, figsize=(17, 11), constrained_layout=True)
    for row, k in enumerate(("rim", "shadow_edge", "texture")):
        for col in range(5):
            ax = axes[row][col]
            ax.set_xticks([])
            ax.set_yticks([])
            if col >= len(by[k]):
                ax.axis("off")
                continue
            c = by[k][col]
            pad = 36
            x0, x1 = max(0, int(c["x"]) - pad), min(512, int(c["x"]) + pad)
            y0, y1 = max(0, int(c["y"]) - pad), min(512, int(c["y"]) + pad)
            ax.imshow(
                r["pre"]["gray"][y0:y1, x0:x1],
                cmap="gray",
                vmin=0,
                vmax=1,
                extent=(x0 - 0.5, x1 - 0.5, y1 - 0.5, y0 - 0.5),
            )
            ax.add_patch(
                Circle((c["x"], c["y"]), c["r"], fill=False, color=HUMAN_COLORS[k], lw=1.4)
            )
            ok = "✓" if c["review"]["class"] == k else "✗"
            ax.set_title(
                f"{names[k]} · {c['crater_id']} r={c['r']:.0f}\n"
                f"máy: {c['review']['class']} {ok} · sáng–tối: {c['shading']['status']}",
                fontsize=8,
            )
    fig.suptitle(
        f"S2-02 · {r['metadata']['image_id']} · ví dụ theo nhãn người; ✓/✗ = lớp máy đúng/sai",
        fontsize=11,
    )
    fig.savefig(path, dpi=60)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """Nhận argv (list str hoặc None); chạy một ảnh và trả 0 khi hoàn tất.

    Ghi PNG, candidates.csv, report.json trong EVIDENCE/<image_id>, có thể
    ghi đè; tạo mẫu LABELS nếu thiếu. Đọc nhãn sẵn có, không tự gán nhãn
    hoặc xác nhận người kiểm; mục 4.3/4.6, không chạy CLI này chỉ để xuất bảng.
    """
    parser = argparse.ArgumentParser(description="S2-02: rà biên và ứng viên trên một ảnh")
    parser.add_argument("image_id")
    parser.add_argument("--processed-dir", default=str(ROOT / "data" / "processed"))
    args = parser.parse_args(argv)
    r = run(args.image_id, Path(args.processed_dir))
    out = EVIDENCE / args.image_id
    out.mkdir(parents=True, exist_ok=True)
    steps_figure(out / "buoc_bien.png", r)
    candidates_figure(out / "ung_vien.png", r)
    label_sheet(out / "phieu_nhan.png", r)
    label_path = write_label_template(args.image_id, r["circles"])
    human = human_labels(load_labels(args.image_id), r["circles"])
    if human:
        filter_figure(out / "loc_truoc_sau.png", r, human)
        examples_figure(out / "vi_du.png", r, human)
    with (out / "candidates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            [
                "n",
                "crater_id",
                "x",
                "y",
                "r",
                "votes",
                "radial_coverage",
                "shadow_edge_fraction",
                "rim_contrast",
                "lop_may",
                "sang_toi",
                "score",
                "nhan_nguoi",
            ]
        )
        for i, c in enumerate(r["circles"], 1):
            fe = c["review"]["features"]
            w.writerow(
                [
                    i,
                    c["crater_id"],
                    c["x"],
                    c["y"],
                    c["r"],
                    c["votes"],
                    fe["radial_coverage"],
                    fe["shadow_edge_fraction"],
                    fe["rim_contrast"],
                    c["review"]["class"],
                    c["shading"]["status"],
                    c["shading"]["score"],
                    human.get(c["crater_id"], ""),
                ]
            )
    report = {
        "image_id": args.image_id,
        "seconds": r["seconds"],
        "preprocess_params": {k: v for k, v in r["pre"]["params"].items() if k != "steps"},
        "review": r["review"],
        "shading": {
            k: r["shading"][k]
            for k in ("checked", "reason", "sun_basis", "azimuth_deg", "quality", "counts")
        },
        "hough_circles": len(r["circles"]),
        "labels": str(label_path.relative_to(ROOT)),
        "evaluation": (
            evaluate(r["circles"], human)
            if human
            else "chưa có nhãn người: chưa đối chiếu, chưa gọi là lọc"
        ),
    }
    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Đã lưu {out.relative_to(ROOT)} | lớp máy {r['review']['counts']} | sáng–tối "
        f"{(
            r['shading']['counts']
            if r['shading']['checked']
            else 'bỏ qua: ' + r['shading']['reason']
        )}"
        f" | {r['seconds']}"
    )
    print(f"Mẫu nhãn: {label_path.relative_to(ROOT)} ({len(human)} vòng đã có nhãn)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
