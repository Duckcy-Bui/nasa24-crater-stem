"""S1-12: verify a hand-worked 5x5 example and compare NumPy with OpenCV.

OpenCV is used only as the reference in this script; src/hough.py stays NumPy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.hough import (
    _accumulate, _accumulate_gradient, _circle_offsets, _local_peaks,
    detect_circles, resolve_hough_params,
)
from src.preprocessing import gaussian_blur


def tiny_example() -> dict:
    """Use real internal helpers; radius=1 is deliberately outside the public API."""
    edges = np.zeros((5, 5), dtype=bool)
    points = [(2, 1), (1, 2), (3, 2), (2, 3)]  # (x,y), np.nonzero row order
    for x, y in points:
        edges[y, x] = True
    angles = np.deg2rad(np.arange(0.0, 360.0, 1.0))
    offsets = _circle_offsets(1, angles)
    manual_offsets = np.array([
        [-1, -1], [-1, 0], [-1, 1], [0, -1],
        [0, 1], [1, -1], [1, 0], [1, 1],
    ], dtype=np.int32)
    np.testing.assert_array_equal(offsets, manual_offsets)

    running = np.zeros((5, 5), dtype=np.int32)
    trace = []
    for x, y in points:
        votes = []
        for dx, dy in manual_offsets:
            a, b = int(x - dx), int(y - dy)
            inside = 0 <= a < 5 and 0 <= b < 5
            votes.append({"offset": [int(dx), int(dy)], "center": [a, b],
                          "inside": inside, "flat_index": b * 5 + a if inside else None})
            if inside:
                running[b, a] += 1
        trace.append({"point_xy": [x, y], "votes": votes,
                      "cumulative_accumulator": running.tolist()})

    expected = np.array([
        [0, 1, 1, 1, 0],
        [1, 2, 2, 2, 1],
        [1, 2, 4, 2, 1],
        [1, 2, 2, 2, 1],
        [0, 1, 1, 1, 0],
    ], dtype=np.int32)
    ys, xs = (a.astype(np.int32) for a in np.nonzero(edges))
    for batch_size in (1, 2, 256):
        actual = _accumulate(ys, xs, edges.shape, offsets, batch_size)
        np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(running, expected)
    threshold = max(3, int(np.ceil(0.35 * len(offsets))))
    peaks = _local_peaks(actual, threshold)
    np.testing.assert_array_equal(peaks, [[2, 2]])
    np.testing.assert_array_equal(_local_peaks(actual, 12), np.empty((0, 2), int))

    theta = np.zeros((5, 5), dtype=np.float64)
    for x, y in points:
        theta[y, x] = np.arctan2(y - 2, x - 2)
    gradient = _accumulate_gradient(ys, xs, edges.shape, theta, 1)
    expected_gradient = np.array([
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 0, 4, 0, 1],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
    ], dtype=np.int32)
    np.testing.assert_array_equal(gradient, expected_gradient)
    return {"shape": [5, 5], "radius": 1, "angle_step_deg": 1.0,
            "edges": edges.astype(int).tolist(), "offsets": offsets.tolist(),
            "trace": trace, "accumulator": actual.tolist(),
            "toy_min_votes": 3, "threshold": threshold,
            "peaks_yx": peaks.tolist(), "score": 4 / 8,
            "gradient_accumulator": gradient.tolist(),
            "gradient_support_size": 7, "gradient_score": 4 / 7,
            "note": "Internal helpers only; detect_circles requires 512x512 and r>=5."}


def nearest_truth(circles: list[dict], truth: list[dict]) -> list[dict]:
    """Descriptive nearest neighbour, WITHOUT acceptance threshold or unique matching.

    Several detections can point to the same truth. A row is not a TP or FP.
    """
    rows = []
    for circle in circles:
        row = dict(circle)
        if truth:
            known = min(truth, key=lambda t: (circle["x"] - t["x"]) ** 2
                        + (circle["y"] - t["y"]) ** 2)
            row.update({"nearest_truth_id": known["crater_id"],
                        "dx_px": circle["x"] - known["x"],
                        "dy_px": circle["y"] - known["y"],
                        "center_distance_px": float(np.hypot(circle["x"] - known["x"],
                                                            circle["y"] - known["y"])),
                        "dr_px": circle["r"] - known["r"]})
        rows.append(row)
    return rows


def comparison() -> tuple[dict, dict[str, np.ndarray]]:
    import cv2
    from scripts.demo_hough import synthetic_scene

    cv2.setNumThreads(1)
    image, _, _, truth = synthetic_scene()
    # Common image for all methods. These are comparison settings, not B0-B8.
    smooth = gaussian_blur(image, sigma=1.5, size=11)
    gray_u8 = np.rint(np.clip(smooth, 0, 1) * 255).astype(np.uint8)
    cv_params = {"dp": 1.0, "minDist": 4.0, "param1": 100.0, "param2": 12.0,
                 "minRadius": 18, "maxRadius": 36}
    # Reproduce Sobel/Canny in OpenCV 4.14.0 HoughCirclesGradient.
    gx = cv2.Sobel(gray_u8, cv2.CV_16S, 1, 0, ksize=3,
                   borderType=cv2.BORDER_REPLICATE)
    gy = cv2.Sobel(gray_u8, cv2.CV_16S, 0, 1, ksize=3,
                   borderType=cv2.BORDER_REPLICATE)
    edges = cv2.Canny(gx, gy, 50, 100, L2gradient=False) > 0
    theta = np.arctan2(gy.astype(np.float32), gx.astype(np.float32))
    results = {}
    for method in ("full_circle", "gradient"):
        params = resolve_hough_params({"voting_method": method})
        start = time.perf_counter()
        circles = detect_circles(edges, 18, 36, params, theta=theta)
        seconds = time.perf_counter() - start
        results[method] = {"params": params, "seconds": seconds,
                           "detections": nearest_truth(circles, truth)}
    start = time.perf_counter()
    raw = cv2.HoughCircles(gray_u8, cv2.HOUGH_GRADIENT, **cv_params)
    seconds = time.perf_counter() - start
    circles = [] if raw is None else [
        {"crater_id": f"CV{i}", "x": float(x), "y": float(y), "r": float(r),
         "confidence": None, "votes": None}
        for i, (x, y, r) in enumerate(raw[0], start=1)
    ]
    results["opencv"] = {"params": {"method": "HOUGH_GRADIENT", **cv_params},
                         "seconds": seconds, "detections": nearest_truth(circles, truth)}
    # A negative control checks the public APIs, independently of noisy detections.
    blank = np.zeros_like(edges)
    for method in ("full_circle", "gradient"):
        if detect_circles(blank, 18, 36, {"voting_method": method}, theta=theta):
            raise AssertionError("Blank image produced NumPy circles.")
    if cv2.HoughCircles(np.zeros_like(gray_u8), cv2.HOUGH_GRADIENT, **cv_params) is not None:
        raise AssertionError("Blank image produced OpenCV circles.")
    report = {"data_kind": "synthetic", "truth": truth,
              "radius_range_px": [18, 36], "edge_count": int(edges.sum()),
              "common_preprocessing": {"gaussian_sigma": 1.5, "gaussian_size": 11,
                  "gaussian_border": "reflect_101", "quantization": "rint(255*smooth)",
                  "sobel_size": 3, "sobel_border": "replicate",
                  "canny_low": 50, "canny_high": 100, "canny_L2gradient": False},
              "results": results, "blank_control": "all three methods returned no circles",
              "comparison_limits": [
                  "Same gray_u8 and radius range; NumPy receives reconstructed Canny edges.",
                  "Internal Canny reconstruction verified against OpenCV 4.14.0 source; "
                  "other versions must be checked separately.",
                  "NumPy per-radius NMS/ratio and OpenCV center/radius stages differ.",
                  "Nearest-truth differences are descriptive, not TP/FP or Precision/Recall.",
                  "NumPy timings exclude Sobel/Canny; OpenCV timing includes them.",
                  "Parameters illustrate differences; no accuracy acceptance threshold.",
              ]}
    arrays = {"image": image, "gray_u8": gray_u8, "edges": edges,
              "theta": theta, "gx": gx, "gy": gy}
    return report, arrays


def render_comparison(gray_u8: np.ndarray, report: dict) -> np.ndarray:
    import cv2
    panels = []
    for method in ("input", "full_circle", "gradient", "opencv"):
        panel = np.full((570, 512, 3), 255, dtype=np.uint8)
        panel[58:570] = cv2.cvtColor(gray_u8, cv2.COLOR_GRAY2BGR)
        cv2.putText(panel, method, (12, 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(panel, "Green: truth; red: detection", (12, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        for c in report["truth"]:
            cv2.circle(panel, (round(c["x"]), round(c["y"]) + 58),
                       round(c["r"]), (0, 255, 0), 1)
        if method != "input":
            for c in report["results"][method]["detections"]:
                cv2.circle(panel, (round(c["x"]), round(c["y"]) + 58),
                           round(c["r"]), (0, 0, 255), 1)
        panels.append(panel)
    return np.hstack(panels)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tiny-only", action="store_true",
                        help="Print verified 5x5 trace without writing files or importing cv2.")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    tiny = tiny_example()
    if args.tiny_only:
        print(json.dumps(tiny, indent=2, allow_nan=False))
        return

    import cv2
    report, arrays = comparison()
    # Outside a git checkout (zip/archive) record "unknown" instead of crashing after the run.
    git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    head = git_head.stdout.strip() if git_head.returncode == 0 else "unknown"
    git_dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    dirty = git_dirty.stdout.strip() if git_dirty.returncode == 0 else ""
    source_paths = ("src/hough.py", "src/preprocessing.py", "scripts/demo_hough.py",
                    "scripts/verify_hough_examples.py")
    report.update({"tiny_example": tiny,
                   "environment": {"python": platform.python_version(),
                       "numpy": np.__version__, "opencv": cv2.__version__,
                       "opencv_threads": cv2.getNumThreads(), "platform": platform.platform()},
                   "code_version": head + ("+working-tree" if dirty else ""),
                   "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                     for p in source_paths},
                   # Same hash on Windows (CRLF) and Linux (LF) checkouts of one commit.
                   "source_sha256_lf": {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                                        for p in source_paths},
                   "created_at_utc": datetime.now(timezone.utc).isoformat()})
    # Render before writing, then reserve a new directory; never overwrite a run.
    png = render_comparison(arrays["gray_u8"], report)
    run_id = "s112_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = args.output_root / run_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8")
    np.savez_compressed(directory / "inputs.npz", **arrays)
    encoded_ok, encoded_png = cv2.imencode(".png", png)
    if not encoded_ok:
        raise RuntimeError("Could not encode comparison image.")
    (directory / "comparison.png").write_bytes(encoded_png.tobytes())
    fields = ("method", "crater_id", "x", "y", "r", "votes", "nearest_truth_id",
              "dx_px", "dy_px", "center_distance_px", "dr_px")
    with (directory / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for method, result in report["results"].items():
            writer.writerows({"method": method, **row} for row in result["detections"])
    print("5x5 scalar calculation, NumPy batches, peaks and gradient: PASS")
    for method, result in report["results"].items():
        print(f"{method}: {len(result['detections'])} circles; {result['seconds']:.6f} s")
    print(f"Saved: {directory}")
    print("Synthetic comparison only; no NASA accuracy or speed ranking.")


if __name__ == "__main__":
    main()
