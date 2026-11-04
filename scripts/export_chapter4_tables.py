"""Export result Tables 4.4–4.8 from a full S3-10 run, without running Hough.

Table 4.5 reuses archived human judgements; the other tables use the new run.
Recall_known and sample SD follow report sections 2.4 and 4.5. Candidate purity
on blind labels is separate and cannot establish full-image Precision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import dưới đây đặt sau cấu hình backend/sys.path ở trên; giữ thứ tự (E402).
from scripts.ch4_mean_sd import summarize  # noqa: E402

BLIND_IMAGES = (
    "moon_ap16_m132732855l_c01",
    "moon_ap16_m109134835l_c01",
)
S305_TUNING = (
    BLIND_IMAGES[0],
    "moon_ap16_m102064759r_c01",
    BLIND_IMAGES[1],
)
MARE = "moon_marefrig_loc_c01"
METHODS = ("numpy_score", "numpy_balanced", "opencv")
FILTERS = (
    "không lọc",
    "bỏ texture",
    "bỏ shadow_edge + texture",
    "bỏ sáng–tối ngược",
)
REPORT = "docs/bao_cao/04_chuong_4_du_lieu_danh_gia.md"


def read_json(path):
    """Đọc path (Path) JSON UTF-8; trả giá trị giải mã, không ghi hay kiểm schema."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    """Nhận path (Path); trả SHA-256 trên byte file gồm cả xuống dòng, không ghi file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    """Ghi value JSON hữu hạn vào path (Path), tạo thư mục cha; trả None.

    Có thể ghi đè file; đây là tiện ích I/O, không có công thức riêng.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def read_csv(path):
    """Đọc path (Path) CSV UTF-8; trả list dict giá trị str, không ghi file."""
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    """Ghi rows (list dict không rỗng) vào path (Path); trả None, có thể ghi đè.

    None thành ô trống; danh sách rỗng gây ValueError, không tạo thư mục cha.
    """
    if not rows:
        raise ValueError(f"Empty table: {path.name}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def blind_filter_rows(reports):
    """Nhận reports (dict mã ảnh → report S2-02), trả tám dòng nhãn mù Bảng 4.5.

    Tỷ lệ = rim giữ / vòng nhãn rõ giữ, đổi % một chữ số (mục 4.5).
    Thiếu nắng để số loại/mất hố None và giữ tỷ lệ nền; không ghi file,
    không tạo nhãn người hoặc suy Precision toàn ảnh.
    """
    rows = []
    for image_id in BLIND_IMAGES:
        report = reports[image_id]
        if report["image_id"] != image_id:
            raise ValueError("Blind-label image identity differs")
        filters = {r["cach_loc"]: r for r in report["evaluation"]["filters"]}
        baseline = filters["không lọc"]
        for name in FILTERS:
            row = filters[name]
            available = name != FILTERS[-1] or report["shading"]["checked"]
            if not available:
                row = baseline
            rows.append(
                {
                    "image_id": image_id,
                    "filter": name,
                    "status": "evaluated" if available else "not_evaluable_no_sun",
                    "labeled_candidates": baseline["con_lai"],
                    "removed": row["loai"] if available else None,
                    "rim_removed": row["loai_nham_ho_that"] if available else None,
                    "rim_fraction_pct": round(100 * row["ty_le_ho_that_trong_con_lai"], 1),
                }
            )
    return rows


def snapshot_blind_labels(source_root, output):
    """Sao hồ sơ từ source_root (Path repo) vào output (Path mới); trả None.

    Ghi hai JSON lịch sử, filters.csv và manifest nguồn/SHA; không gọi
    S2-02, không tạo nhãn người hay ghi đè thư mục, theo Bảng 4.5.
    """
    sources = {i: source_root / f"docs/evidence/s2-02/{i}/report.json" for i in BLIND_IMAGES}
    rows = blind_filter_rows({i: read_json(p) for i, p in sources.items()})
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for image_id, source in sources.items():
        name = image_id + ".json"
        digest = sha(source)
        shutil.copyfile(source, output / name)
        if sha(output / name) != digest or sha(source) != digest:
            raise ValueError("Blind-label source changed during snapshot")
        files[name] = {"source": source.relative_to(source_root).as_posix(), "sha256": digest}
    write_csv(output / "filters.csv", rows)
    save_json(
        output / "manifest.json",
        {
            "status": "complete",
            "mode": "historical_blind_labels",
            "reason": "Historical human judgements; not rerun.",
            "reports": files,
            "filters_sha256": sha(output / "filters.csv"),
        },
    )


def s305_rows(directory):
    """Đọc directory (Path lượt S3-05); trả 11 dòng nhánh cho bốn nhóm Bảng 4.4.

    Gộp TP/nhãn trên cùng ảnh theo từng biến thể (2.23); E1 chỉ hai ảnh đủ
    nắng, E2 chỉ tuning, Mare E3 nền. Không ghi file; sai scope bị từ chối.
    """
    report = read_json(directory / "report.json")
    if report["status"] != "complete":
        raise ValueError("Incomplete S3-05 run")
    specs = {
        "E1": ("raw", "shading_annotation", "remove_inverted"),
        "E2": ("baseline", "min_vote_ratio_030", "min_vote_ratio_040", "radius_step_2"),
        "E3": ("baseline", "remove_texture", "dedupe"),
    }
    out = []
    for experiment, variants in specs.items():
        rows = read_csv(directory / f"{experiment}.csv")
        expected = {(i, v) for i in S305_TUNING for v in variants}
        if experiment == "E1":
            expected = {(i, v) for i in S305_TUNING[:2] for v in variants}
            expected |= {(S305_TUNING[2], "raw"), (MARE, "raw")}
        elif experiment == "E3":
            expected.add((MARE, "baseline"))
        pairs = [(r["image_id"], r["variant"]) for r in rows]
        if len(set(pairs)) != len(pairs) or set(pairs) != expected:
            raise ValueError(f"Incomplete/duplicate S3-05 scope: {experiment}")
        for row in rows:
            split = "holdout" if row["image_id"] == MARE else "tuning"
            tp, fn, known = (int(row[k]) for k in ("tp_known", "fn_known", "known_labels"))
            if (
                row["split"] != split
                or row["precision"]
                or row["f1"]
                or min(tp, fn, known, int(row["candidates"])) < 0
                or tp + fn != known
            ):
                raise ValueError("Invalid sparse-label S3-05 row")
        for variant in variants:
            selected = [
                r
                for r in rows
                if r["variant"] == variant
                and r["split"] == "tuning"
                and (experiment != "E1" or r["scope"] == "diagnostic_tuning_only")
            ]
            wanted = 2 if experiment == "E1" else 3
            if len(selected) != wanted:
                raise ValueError("S3-05 image group changed")
            out.append(pool_s305(experiment, "tuning", variant, selected))
        if experiment == "E3":
            out.append(
                pool_s305(
                    experiment,
                    "holdout_descriptive",
                    "baseline",
                    [r for r in rows if r["image_id"] == MARE],
                )
            )
    return out


def pool_s305(experiment, scope, variant, rows):
    """Gộp rows (list dòng CSV) cho experiment/scope/variant (str), trả dict.

    Cộng vòng, TP và nhãn; Recall_known=TP/nhãn theo (2.23), mẫu số 0
    cho None. Precision/F1 để None; không ghi file hay sửa các dòng vào.
    """
    tp = sum(int(r["tp_known"]) for r in rows)
    labels = sum(int(r["known_labels"]) for r in rows)
    return {
        "experiment": experiment,
        "scope": scope,
        "variant": variant,
        "n_images": len(rows),
        "candidates": sum(int(r["candidates"]) for r in rows),
        "tp_known": tp,
        "known_labels": labels,
        "recall_known": tp / labels if labels else None,
        "precision": None,
        "f1": None,
    }


def validate_hough_recall(rows):
    """Kiểm các dòng TP/FN/recall trước khi tổng hợp theo (2.23), mục 4.5.

    Vào: rows là list dict; TP/FN phải là int không âm, không nhận bool;
    recall là số hữu hạn và lệch TP/(TP+FN) không quá 1e-9.
    Ra: None hoặc ValueError; TP+FN=0 bị từ chối vì Recall_known không
    xác định, không gán 0 hay đưa vào trung bình/SD. Không sửa rows.
    """
    for row in rows:
        tp, fn = row.get("tp"), row.get("fn")
        if any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in (tp, fn)):
            raise ValueError("TP/FN must be nonnegative integers")
        labels = tp + fn
        if labels == 0:
            raise ValueError("Recall_known undefined when TP+FN=0")
        recall = row.get("recall")
        if isinstance(recall, bool) or not isinstance(recall, (int, float)):
            raise ValueError("Recall_known must be a finite number")
        try:
            consistent = math.isfinite(recall) and abs(recall - tp / labels) <= 1e-9
        except OverflowError:
            consistent = False
        if not consistent:
            raise ValueError("Recall_known inconsistent with TP/FN or nonfinite")


def hough_tables(summaries):
    """Nhận summaries (dict tuning/holdout); trả cặp list Bảng 4.6 và 4.7.

    Kiểm TP/FN/recall trước summarize; dùng ch4_mean_sd cho SD mẫu theo
    ảnh (mục 4.5), không phải SD thời gian. Đọc số vòng OpenCV từ JSON;
    không ghi file, bảng holdout có hàng tổng và để trống tổng số vòng.
    """
    aggregate, per_image = [], []
    for split, n_images in (("tuning", 3), ("holdout", 8)):
        report = summaries[split]
        images = report["images"]
        if (
            report["status"] != "complete"
            or report["split"] != split
            or len(images) != n_images
            or len({i["image_id"] for i in images}) != n_images
        ):
            raise ValueError(f"Incomplete evaluation: {split}")
        for method in METHODS:
            rows = [i["methods"][method] for i in images]
            validate_hough_recall(rows)
            if any(r["precision"] is not None or r["f1"] is not None for r in rows):
                raise ValueError("Sparse-label Precision/F1 must be null")
            summary = summarize(
                rows, f"evaluation_{split}", split, method, "recall", "tp", "fn", "median_seconds"
            )
            aggregate.append(
                {
                    "split": split,
                    "method": method,
                    "n_images": n_images,
                    "tp_known": summary["tp"],
                    "fn_known": summary["labels"] - summary["tp"],
                    "known_labels": summary["labels"],
                    "recall_pooled_pct": round(100 * summary["recall_pooled"], 2),
                    "recall_mean_pct": round(100 * summary["recall_mean"], 2),
                    "recall_sd_pct": round(100 * summary["recall_sd"], 2),
                    "precision": None,
                    "f1": None,
                }
            )
        if split == "holdout":
            for image in images:
                methods = image["methods"]
                labels = {m["tp"] + m["fn"] for m in (methods[k] for k in METHODS)}
                if len(labels) != 1:
                    raise ValueError("Methods disagree on known-label count")
                row = {"image_id": image["image_id"], "known_labels": labels.pop()}
                for method in METHODS:
                    row[method + "_tp"] = methods[method]["tp"]
                    row[method + "_fn"] = methods[method]["fn"]
                row["opencv_candidates"] = methods["opencv"]["candidate_count"]
                per_image.append(row)
    total = {
        key: (
            "TOTAL"
            if key == "image_id"
            else None if key == "opencv_candidates" else sum(r[key] for r in per_image)
        )
        for key in per_image[0]
    }
    return aggregate, [*per_image, total]


def density_rows(report):
    """Nhận report (dict mật độ JSON); trả hai dòng Bảng 4.8, không ghi file.

    Diện tích km² làm tròn một chữ số, mật độ/CI hố/km² ba chữ số từ
    số chính xác, ghi dạng chuỗi giữ số 0 cuối (0.310, không phải 0.31) cho khớp
    bảng báo cáo; đếm tay, không phải Hough. Theo (2.24)–(2.25).
    """
    rows = []
    for key in ("lunokhod1", "marefrig"):
        region = report["regions"][key]
        low, high = region["density_ci95_per_km2"]
        rows.append(
            {
                "region": region["name"],
                "area_km2": f"{region['area_km2']:.1f}",
                "n": region["n"],
                "density_per_km2": f"{region['density_per_km2']:.3f}",
                "ci95_low": f"{low:.3f}",
                "ci95_high": f"{high:.3f}",
            }
        )
    return rows


def export_tables(run, report_root=ROOT):
    """Đọc run (Path lượt full), report_root (Path repo); trả dict registry.

    Kiểm các nguồn cần thiết rồi tạo chapter4_tables mới, ghi năm CSV và
    index.json nguồn/SHA/làm tròn/hash Chương 4; không ghi đè thư mục.
    Bảng 4.5 dùng nhãn người lịch sử; bảng còn lại từ lượt mới, mục 4.6–4.8.
    """
    parent = read_json(run / "manifest.json")
    if parent["mode"] != "full":
        raise ValueError("Chapter 4 tables require a full run")
    blind = read_json(run / "blind_filter/manifest.json")
    if blind["status"] != "complete":
        raise ValueError("Incomplete blind-label snapshot")
    for name, source in blind["reports"].items():
        if sha(run / "blind_filter" / name) != source["sha256"]:
            raise ValueError("Blind-label snapshot hash differs")
    if sha(run / "blind_filter/filters.csv") != blind["filters_sha256"]:
        raise ValueError("Blind-label filter hash differs")
    summaries = {s: read_json(run / f"evaluation_{s}/summary.json") for s in ("tuning", "holdout")}
    hough, holdout = hough_tables(summaries)
    filters = read_csv(run / "blind_filter/filters.csv")
    if len(filters) != 8:
        raise ValueError("Incomplete blind-label filters")
    tables = {
        "4.4": (
            s305_rows(run / "s305"),
            "computed_current_run",
            [f"s305/{e}.csv" for e in ("E1", "E2", "E3")] + ["s305/report.json"],
        ),
        "4.5": (
            filters,
            "historical_blind_labels",
            ["blind_filter/manifest.json", "blind_filter/filters.csv"]
            + [f"blind_filter/{i}.json" for i in BLIND_IMAGES],
        ),
        "4.6": (
            hough,
            "computed_current_run",
            [f"evaluation_{s}/summary.json" for s in summaries],
        ),
        "4.7": (holdout, "computed_current_run", ["evaluation_holdout/summary.json"]),
        "4.8": (
            density_rows(read_json(run / "density/so_sanh.json")),
            "computed_from_manual_counts",
            ["density/so_sanh.json"],
        ),
    }
    output = run / "chapter4_tables"
    output.mkdir(exist_ok=False)
    registry = []
    for number, (rows, mode, inputs) in tables.items():
        name = "table_" + number.replace(".", "_") + ".csv"
        write_csv(output / name, rows)
        registry.append(
            {
                "table_id": number,
                "file": name,
                "rows": len(rows),
                "mode": mode,
                "sha256": sha(output / name),
                "inputs_sha256": {p: sha(run / p) for p in inputs},
            }
        )
    index = {
        "status": "complete",
        "tables": registry,
        "report_source": {"path": REPORT, "sha256": sha(report_root / REPORT)},
        "base_commit": parent["base_commit"],
        "seed": parent["seed"],
        "rounding": {
            "4.5": "purity percent: 1 decimal",
            "4.6": "ch4_mean_sd.summarize: ratios 4 dp; percent 2 dp",
            "4.8": "area: 1 decimal; density and CI95: 3",
        },
        "limitations": [
            "4.4 has 11 branch rows representing the report's four groups.",
            "4.5 reuses archived human judgements, not a new human review.",
            "4.6 sample SD is across images; it is not a timing SD.",
            "4.7 includes a total row; total candidate count is not reported.",
            "4.1/4.2 are input inventories; 4.3 is experiment design.",
            "Sparse labels do not establish full-image FP/Precision/F1.",
        ],
    }
    save_json(output / "index.json", index)
    return index


def main(argv=None):
    """Nhận argv (list str hoặc None), chạy subcommand và trả 0 khi xong.

    blind-labels ghi bản sao/CSV/manifest vào --output mới; tables đọc
    --run-dir, ghi chapter4_tables với Bảng 4.4–4.8; không chạy Hough.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    blind = sub.add_parser("blind-labels")
    blind.add_argument("--output", type=Path, required=True)
    tables = sub.add_parser("tables")
    tables.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "blind-labels":
        snapshot_blind_labels(ROOT, args.output)
        print("Historical blind-label snapshot complete")
    else:
        index = export_tables(args.run_dir)
        print("Chapter 4 tables complete:", ", ".join(r["table_id"] for r in index["tables"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
