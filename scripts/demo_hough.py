"""Demo S1-07 trên đường biên giả lập; không phải bộ ảnh NASA hay Robbins."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json, save_run, validate_crater_set
from src.hough import (
    _accumulate, _accumulate_gradient, _circle_offsets,
    detect_circles, resolve_hough_params,
)


def synthetic_scene() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    """Tạo ba vòng tròn đã biết; vòng thứ ba bị cắt tại mép trái ảnh."""
    yy, xx = np.indices((512, 512))
    image = np.zeros((512, 512), dtype=np.float32)
    edges = np.zeros_like(image, dtype=bool)
    theta = np.zeros_like(image)
    truth = []
    for index, (x, y, radius) in enumerate(
        ((160, 180, 32), (350, 310, 20), (8, 420, 24)), start=1,
    ):
        distance = np.hypot(xx - x, yy - y)
        image[distance <= radius] = 1
        contour = np.abs(distance - radius) <= 0.5
        edges |= contour
        theta[contour] = np.arctan2(yy[contour] - y, xx[contour] - x)
        truth.append({"crater_id": f"T{index}", "x": float(x), "y": float(y),
                      "r": float(radius), "confidence": None, "votes": None})
    return image, edges, theta, truth


def code_version() -> str:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          text=True, capture_output=True, check=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           text=True, capture_output=True, check=True)
    return head.stdout.strip() + ("+working-tree" if dirty.stdout.strip() else "")


def render_demo(directory, image, edges, theta, circles, truth, params, seconds):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    radius = 32
    ys, xs = np.nonzero(edges)
    ys, xs = ys.astype(np.int32), xs.astype(np.int32)
    if params["voting_method"] == "gradient":
        accumulator = _accumulate_gradient(ys, xs, edges.shape, theta, radius)
    else:
        offsets = _circle_offsets(radius, np.deg2rad(
            np.arange(0, 360, params["angle_step_deg"]),
        ))
        accumulator = _accumulate(ys, xs, edges.shape, offsets,
                                  params["edge_batch_size"])
    figure, axes = plt.subplots(1, 3, figsize=(14, 5), constrained_layout=True)
    axes[0].imshow(image, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Synthetic input: 3 known circles")
    axes[1].imshow(edges, cmap="gray")
    axes[1].set_title("Input edges and detections")
    for circle in truth:
        axes[1].add_patch(Circle((circle["x"], circle["y"]), circle["r"],
                                fill=False, edgecolor="lime", linestyle="--"))
    for circle in circles:
        axes[1].add_patch(Circle((circle["x"], circle["y"]), circle["r"],
                                fill=False, edgecolor="red", linewidth=1))
    heat = axes[2].imshow(accumulator, cmap="magma")
    axes[2].set_title("NumPy accumulator at radius = 32 px")
    figure.colorbar(heat, ax=axes[2], label="Votes")
    for axis in axes:
        axis.set_xlim(0, 511)
        axis.set_ylim(511, 0)
        axis.set_xlabel("x (px)")
        axis.set_ylabel("y (px)")
    figure.suptitle(
        f"S1-07 | {params['voting_method']} | {seconds:.3f} s | "
        "Green: synthetic truth; red: detected circles. NOT NASA validation."
    )
    figure.savefig(directory / "demo.png", dpi=130)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=("full_circle", "gradient"),
                        default="full_circle")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    image, edges, theta, truth = synthetic_scene()
    version = code_version()
    params = resolve_hough_params({"voting_method": args.method})
    r_min, r_max = 18, 36
    start = time.perf_counter()
    circles = detect_circles(edges, r_min, r_max, params, theta=theta)
    elapsed = time.perf_counter() - start
    hits = sum(any(abs(found["x"] - known["x"]) <= 1
                   and abs(found["y"] - known["y"]) <= 1
                   and abs(found["r"] - known["r"]) <= 1
                   for found in circles) for known in truth)
    if hits != len(truth):
        raise RuntimeError(f"Demo regression: detected {hits}/{len(truth)} known circles.")

    metadata = copy.deepcopy(read_json(ROOT / "data/examples/s105_synthetic_512.json"))
    metadata.update({
        "image_id": "s107_hough_synthetic", "valid_ratio": 1.0,
        "radius": {"d_min_m": r_min * 4, "d_max_m": r_max * 4,
                   "r_min_px": r_min, "r_max_px": r_max},
        "preprocess": {"version": version, "method": "analytic_synthetic_edges"},
        "note": "Synthetic disks and analytic gradients from demo_hough.py; "
                "scale 2 m/px is hypothetical. No NASA/Robbins data.",
    })
    crater_set = {"schema_version": "1.0", "data_kind": "synthetic",
                  "image_id": metadata["image_id"], "source": "machine",
                  "reference_source": None, "circles": circles}
    truth_set = {**crater_set, "source": "catalogue", "circles": truth,
                 "reference_source": "Known synthetic construction in demo_hough.py; "
                                     "NOT NASA or Robbins catalogue."}
    validate_crater_set(truth_set, metadata)
    run_id = args.run_id or ("s107_" + args.method + "_" +
                             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    directory = save_run(args.output_root, run_id, metadata=metadata,
                         crater_set=crater_set,
                         params={"hough": params, "r_min_px": r_min,
                                 "r_max_px": r_max}, code_version=version)
    np.save(directory / "image.npy", image)
    np.save(directory / "edges.npy", edges)
    np.save(directory / "theta.npy", theta)
    for filename, value in (
        ("synthetic_truth.json", truth_set),
        ("demo_check.json", {"data_kind": "synthetic", "expected_circles": len(truth),
                             "found_within_1px": hits, "detections": len(circles),
                             "elapsed_seconds": elapsed}),
    ):
        (directory / filename).write_text(json.dumps(value, indent=2,
                                                       allow_nan=False) + "\n")
    render_demo(directory, image, edges, theta, circles, truth, params, elapsed)
    print(f"Found {hits}/{len(truth)} synthetic circles in {elapsed:.3f} s.")
    print(f"Saved effective parameters, version, JSON, arrays and demo.png: {directory}")
    print("This demonstrates the NumPy algorithm, not accuracy on NASA imagery.")


if __name__ == "__main__":
    main()
