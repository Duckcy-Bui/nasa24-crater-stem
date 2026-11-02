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
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ch4_mean_sd import summarize  # noqa: E402

BLIND_IMAGES = (
    "moon_ap16_m132732855l_c01",
    "moon_ap16_m109134835l_c01",
)
S305_TUNING = (
    BLIND_IMAGES[0], "moon_ap16_m102064759r_c01", BLIND_IMAGES[1],
)
MARE = "moon_marefrig_loc_c01"
METHODS = ("numpy_score", "numpy_balanced", "opencv")
FILTERS = (
    "không lọc", "bỏ texture", "bỏ shadow_edge + texture",
    "bỏ sáng–tối ngược",
)
REPORT = "docs/bao_cao/04_chuong_4_du_lieu_danh_gia.md"


def read_json(path):
    """Read a JSON file at path and return its decoded value; no writes."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    """Return SHA-256 of exact file bytes at path, including line endings."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    """Write value as finite JSON at path, creating its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def read_csv(path):
    """Return CSV records from path as string-valued dictionaries."""
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    """Write records to path; None becomes an unavailable blank cell."""
    if not rows:
        raise ValueError(f"Empty table: {path.name}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def blind_filter_rows(reports):
    """Return eight image/filter rows from archived S202 reports (Table 4.5).

    Purity = retained rim / retained clearly labelled candidates, section 4.5.
    Unusable shading leaves counts unavailable and keeps baseline purity.
    No human label is generated and no full-image FP/Precision is inferred.
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
            rows.append({
                "image_id": image_id, "filter": name,
                "status": "evaluated" if available else "not_evaluable_no_sun",
                "labeled_candidates": baseline["con_lai"],
                "removed": row["loai"] if available else None,
                "rim_removed": row["loai_nham_ho_that"] if available else None,
                "rim_fraction_pct": round(
                    100 * row["ty_le_ho_that_trong_con_lai"], 1),
            })
    return rows


def snapshot_blind_labels(source_root, output):
    """Copy historical reports and export filters.csv under new output.

    Input is the repo root. Output must not exist. Record exact source hashes;
    do not call S202's CLI, create labels or overwrite historical evidence.
    """
    sources = {i: source_root / f"docs/evidence/s2-02/{i}/report.json"
               for i in BLIND_IMAGES}
    rows = blind_filter_rows({i: read_json(p) for i, p in sources.items()})
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for image_id, source in sources.items():
        name = image_id + ".json"
        digest = sha(source)
        shutil.copyfile(source, output / name)
        if sha(output / name) != digest or sha(source) != digest:
            raise ValueError("Blind-label source changed during snapshot")
        files[name] = {"source": source.relative_to(source_root).as_posix(),
                       "sha256": digest}
    write_csv(output / "filters.csv", rows)
    save_json(output / "manifest.json", {
        "status": "complete", "mode": "historical_blind_labels",
        "reason": "Historical human judgements; not rerun.",
        "reports": files, "filters_sha256": sha(output / "filters.csv"),
    })


def s305_rows(directory):
    """Pool new S305 CSVs into eleven branch rows for four Table 4.4 groups.

    Sum TP and known labels on identical image sets, never across variants.
    E1 excludes unusable sun, E2 uses tuning only, Mare is E3 baseline-only.
    """
    report = read_json(directory / "report.json")
    if report["status"] != "complete":
        raise ValueError("Incomplete S3-05 run")
    specs = {
        "E1": ("raw", "shading_annotation", "remove_inverted"),
        "E2": ("baseline", "min_vote_ratio_030", "min_vote_ratio_040",
               "radius_step_2"),
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
            tp, fn, known = (int(row[k]) for k in
                             ("tp_known", "fn_known", "known_labels"))
            if (row["split"] != split or row["precision"] or row["f1"]
                    or min(tp, fn, known, int(row["candidates"])) < 0
                    or tp + fn != known):
                raise ValueError("Invalid sparse-label S3-05 row")
        for variant in variants:
            selected = [r for r in rows if r["variant"] == variant
                        and r["split"] == "tuning"
                        and (experiment != "E1" or
                             r["scope"] == "diagnostic_tuning_only")]
            wanted = 2 if experiment == "E1" else 3
            if len(selected) != wanted:
                raise ValueError("S3-05 image group changed")
            out.append(pool_s305(experiment, "tuning", variant, selected))
        if experiment == "E3":
            out.append(pool_s305(experiment, "holdout_descriptive", "baseline",
                                 [r for r in rows if r["image_id"] == MARE]))
    return out


def pool_s305(experiment, scope, variant, rows):
    """Return pooled TP/labels for a branch; Precision/F1 stay unavailable."""
    tp = sum(int(r["tp_known"]) for r in rows)
    labels = sum(int(r["known_labels"]) for r in rows)
    return {"experiment": experiment, "scope": scope, "variant": variant,
            "n_images": len(rows),
            "candidates": sum(int(r["candidates"]) for r in rows),
            "tp_known": tp, "known_labels": labels,
            "recall_known": tp / labels if labels else None,
            "precision": None, "f1": None}


def hough_tables(summaries):
    """Return Tables 4.6 and 4.7 from complete new-run evaluation summaries.

    Reuse ch4_mean_sd.summarize for sample SD over images, not over timing
    repeats. Read OpenCV candidate counts from JSON, absent in results.csv.
    """
    aggregate, per_image = [], []
    for split, n_images in (("tuning", 3), ("holdout", 8)):
        report = summaries[split]
        images = report["images"]
        if (report["status"] != "complete" or report["split"] != split
                or len(images) != n_images
                or len({i["image_id"] for i in images}) != n_images):
            raise ValueError(f"Incomplete evaluation: {split}")
        for method in METHODS:
            rows = [i["methods"][method] for i in images]
            if any(r["precision"] is not None or r["f1"] is not None
                   for r in rows):
                raise ValueError("Sparse-label Precision/F1 must be null")
            summary = summarize(rows, f"evaluation_{split}", split, method,
                                "recall", "tp", "fn", "median_seconds")
            aggregate.append({
                "split": split, "method": method, "n_images": n_images,
                "tp_known": summary["tp"],
                "fn_known": summary["labels"] - summary["tp"],
                "known_labels": summary["labels"],
                "recall_pooled_pct": round(100 * summary["recall_pooled"], 2),
                "recall_mean_pct": round(100 * summary["recall_mean"], 2),
                "recall_sd_pct": round(100 * summary["recall_sd"], 2),
                "precision": None, "f1": None,
            })
        if split == "holdout":
            for image in images:
                methods = image["methods"]
                labels = {m["tp"] + m["fn"] for m in
                          (methods[k] for k in METHODS)}
                if len(labels) != 1:
                    raise ValueError("Methods disagree on known-label count")
                row = {"image_id": image["image_id"],
                       "known_labels": labels.pop()}
                for method in METHODS:
                    row[method + "_tp"] = methods[method]["tp"]
                    row[method + "_fn"] = methods[method]["fn"]
                row["opencv_candidates"] = methods["opencv"]["candidate_count"]
                per_image.append(row)
    total = {key: ("TOTAL" if key == "image_id" else
                   None if key == "opencv_candidates" else
                   sum(r[key] for r in per_image)) for key in per_image[0]}
    return aggregate, [*per_image, total]


def density_rows(report):
    """Return Table 4.8 rows, rounding precise JSON instead of rounded CSV.

    Areas use one decimal; density and Poisson 95% limits use three decimals.
    Counts remain manual complete counts, not Hough or sparse-label totals.
    """
    rows = []
    for key in ("lunokhod1", "marefrig"):
        region = report["regions"][key]
        low, high = region["density_ci95_per_km2"]
        rows.append({"region": region["name"],
                     "area_km2": round(region["area_km2"], 1),
                     "n": region["n"],
                     "density_per_km2": round(region["density_per_km2"], 3),
                     "ci95_low": round(low, 3), "ci95_high": round(high, 3)})
    return rows


def export_tables(run, report_root=ROOT):
    """Export five CSVs plus an index with source/output SHA under run.

    Require a full run and complete producers. Table 4.5 is explicitly marked
    historical; no archived timing is substituted for new measurements.
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
    summaries = {s: read_json(run / f"evaluation_{s}/summary.json")
                 for s in ("tuning", "holdout")}
    hough, holdout = hough_tables(summaries)
    filters = read_csv(run / "blind_filter/filters.csv")
    if len(filters) != 8:
        raise ValueError("Incomplete blind-label filters")
    tables = {
        "4.4": (s305_rows(run / "s305"), "computed_current_run",
                [f"s305/{e}.csv" for e in ("E1", "E2", "E3")]
                + ["s305/report.json"]),
        "4.5": (filters, "historical_blind_labels",
                ["blind_filter/manifest.json", "blind_filter/filters.csv"]
                + [f"blind_filter/{i}.json" for i in BLIND_IMAGES]),
        "4.6": (hough, "computed_current_run",
                [f"evaluation_{s}/summary.json" for s in summaries]),
        "4.7": (holdout, "computed_current_run",
                ["evaluation_holdout/summary.json"]),
        "4.8": (density_rows(read_json(run / "density/so_sanh.json")),
                "computed_from_manual_counts", ["density/so_sanh.json"]),
    }
    output = run / "chapter4_tables"
    output.mkdir(exist_ok=False)
    registry = []
    for number, (rows, mode, inputs) in tables.items():
        name = "table_" + number.replace(".", "_") + ".csv"
        write_csv(output / name, rows)
        registry.append({"table_id": number, "file": name, "rows": len(rows),
                         "mode": mode, "sha256": sha(output / name),
                         "inputs_sha256": {p: sha(run / p) for p in inputs}})
    index = {
        "status": "complete", "tables": registry,
        "report_source": {"path": REPORT, "sha256": sha(report_root / REPORT)},
        "base_commit": parent["base_commit"], "seed": parent["seed"],
        "rounding": {"4.5": "purity percent: 1 decimal",
                     "4.6": "ch4_mean_sd.summarize: ratios 4 dp; percent 2 dp",
                     "4.8": "area: 1 decimal; density and CI95: 3"},
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
    """Read CLI paths and write a new snapshot or result table directory."""
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
        print("Chapter 4 tables complete:",
              ", ".join(r["table_id"] for r in index["tables"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
