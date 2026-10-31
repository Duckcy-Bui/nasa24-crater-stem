"""S3-10: one command to recompute the implemented result tables, offline."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SEED = 0
TUNING = ["moon_ap16_m132732855l_c01", "moon_ap16_m109134835l_c01", "moon_ap15_hia_c01"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities():
    paths = [ROOT / "app.py"] + list(ROOT.glob("requirements*.txt"))
    for folder in ("src", "scripts", "configs", "data/s106_bundle", "data/s203_split",
                   "data/reference_labels", "data/s209_counts"):
        paths += [p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += list((ROOT / "data").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"Empty result table: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_experiments(report, directory):
    """Flatten computed JSON; preserve unavailable precision/F1 as empty CSV cells."""
    e1, e2, e3 = [], [], []
    for image in report["results"]:
        common = {"image_id": image["image_id"], "split": image["split"]}
        first = image["experiment_1_s111"]
        for name in ("baseline", "with_s111_annotation", "remove_inverted_experiment"):
            branch = first[name]
            metric = branch.get("recall", branch)
            e1.append({**common, "variant": name, "status": first["status"],
                       "tp_known": metric["true_positive_known"], "known_labels": metric["known_labels"],
                       "recall_known": metric["recall_known"], "precision": None, "f1": None})
        for branch in image["experiment_2_parameters"]:
            metric = branch["recall"]
            e2.append({**common, "variant": branch["variant"], "candidates": branch["candidates"],
                       "seconds_hough": branch["seconds_hough"], "tp_known": metric["true_positive_known"],
                       "known_labels": metric["known_labels"], "recall_known": metric["recall_known"],
                       "hit_max_circles": metric["hit_max_circles"], "precision": None, "f1": None})
        for name in ("remove_texture", "dedupe"):
            branch = image["experiment_3_hard_cases"][name]
            metric = branch["recall"]
            e3.append({**common, "variant": name, "kept": branch["candidates_kept"],
                       "removed": branch["candidates_removed"], "tp_known": metric["true_positive_known"],
                       "known_labels": metric["known_labels"], "recall_known": metric["recall_known"],
                       "precision": None, "f1": None})
    for name, rows in (("E1.csv", e1), ("E2.csv", e2), ("E3.csv", e3)):
        write_csv(directory / name, rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quick", action="store_true", help="One tuning image; no holdout; not the full tables")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    out = (args.output or ROOT / "outputs" / ("s310_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))).resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONHASHSEED": str(SEED),
           "MPLBACKEND": "Agg", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    report = {"task": "S3-10", "status": "running", "mode": "quick" if args.quick else "full",
              "created_at_utc": datetime.now(timezone.utc).isoformat(), "base_commit": git("rev-parse", "HEAD"),
              "git_status": git("status", "--short"), "python": platform.python_version(),
              "platform": platform.platform(), "seed": SEED, "repeats": args.repeats, "stages": [],
              "limitations": ["Sparse labels: only Recall_known; FP/Precision/F1 unavailable.",
                              "Holdout was previously inspected; this is repeated evaluation, not model selection.",
                              "Timing is machine dependent; experiments use single diagnostic timings.",
                              "Density machine branch uses texture removal and dedupe, unlike the game.",
                              "Survey data and unimplemented future tasks cannot be regenerated."]}
    save(out / "manifest.json", report)

    def run(name, script, *arguments):
        command = [sys.executable, "-X", "utf8", "-B", str(ROOT / "scripts" / script), *map(str, arguments)]
        stage = {"name": name, "command": command, "status": "running"}
        report["stages"].append(stage)
        save(out / "manifest.json", report)
        print(f"[{name}] {out}", flush=True)
        with (out / f"{name}.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        stage.update(returncode=completed.returncode, status="complete" if completed.returncode == 0 else "failed")
        save(out / "manifest.json", report)
        if completed.returncode:
            raise RuntimeError(f"{name} failed: see {out / (name + '.log')}")

    try:
        report["packages"] = {p: importlib.metadata.version(p) for p in
                              ("numpy", "opencv-python-headless", "rasterio", "Pillow", "matplotlib", "streamlit")}
        report["source_input_sha256"] = identities()
        sys.path.insert(0, str(ROOT))
        from src.hough import resolve_hough_params
        from src.preprocessing import DEFAULT_PARAMS
        config = read(ROOT / "configs/s215_frozen.json")
        if config != read(ROOT / "configs/default.json"):
            raise ValueError("Game configuration differs from S2-15; evaluate/freeze a new version first")
        save(out / "game_config.json", config)
        comparison = read(ROOT / "configs/s201_large_craters.json")
        comparison["hough"] = resolve_hough_params(comparison)
        comparison["preprocess"] = DEFAULT_PARAMS
        save(out / "comparison_config.json", comparison)
        run("dataset", "install_s106_dataset.py")
        run("synthetic", "verify_hough_examples.py", "--output-root", out / "synthetic")
        tuning = ["moon_ap16_m109134835l_c01"] if args.quick else TUNING
        run("frozen_tuning", "freeze_s215.py", "--output", out / "frozen_tuning",
            *(["--images", *tuning] if args.quick else []))
        run("evaluation_tuning", "evaluate_hough.py", "--config", out / "comparison_config.json",
            "--images", *tuning, "--output", out / "evaluation_tuning", "--repeats", args.repeats)
        run("experiments_tuning", "s207_experiments.py", "--config", out / "game_config.json",
            "--output", out / "experiments_tuning.json", "--write",
            *(["--images", *tuning] if args.quick else []))
        export_experiments(read(out / "experiments_tuning.json"), out)
        if not args.quick:
            run("evaluation_holdout", "evaluate_hough.py", "--config", out / "comparison_config.json",
                "--holdout", "--output", out / "evaluation_holdout", "--repeats", args.repeats)
            run("experiments_holdout", "s207_experiments.py", "--holdout", "--config", out / "game_config.json",
                "--chosen-config", out / "game_config.json", "--output", out / "experiments_holdout.json", "--write")
            combined = {"results": read(out / "experiments_tuning.json")["results"] + read(out / "experiments_holdout.json")["results"]}
            export_experiments(combined, out)
        run("density", "s209_density.py", "--output", out / "density")
        frozen = read(out / "frozen_tuning/report.json")
        if frozen["status"] != "complete":
            raise ValueError("Incomplete frozen tuning results")
        write_csv(out / "frozen_tuning.csv", [
            {"image_id": row["image_id"], "tp_known": row["metrics"]["tp"], "fn_known": row["metrics"]["fn"],
             "recall_known": row["metrics"]["recall"], "precision": None, "f1": None}
            for row in frozen["images"]])
        if identities() != report["source_input_sha256"]:
            raise ValueError("Code/config/input changed during reproduction")
        report["artifacts_sha256"] = {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob("*"))
                                     if p.is_file() and p.name != "manifest.json"}
        report["status"] = "complete"
    except BaseException as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        save(out / "manifest.json", report)
    print(f"Complete ({report['mode']}): {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
