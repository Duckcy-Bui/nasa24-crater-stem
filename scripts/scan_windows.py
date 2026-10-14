"""List candidate crop windows using the raster mask, not brightness as validity."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window


def scan_windows(path: str | Path, size: int = 512, step: int = 64, min_valid: float = 0.95):
    if size < 1 or step < 1 or not 0 <= min_valid <= 1:
        raise ValueError("size/step phải dương và min_valid trong [0,1].")
    with rasterio.open(path) as src:
        for y0 in range(0, src.height - size + 1, step):
            for x0 in range(0, src.width - size + 1, step):
                window = Window(x0, y0, size, size)
                pixels = src.read(1, window=window)
                valid = (src.read_masks(1, window=window) != 0) & np.isfinite(pixels)
                ratio = float(valid.mean())
                if ratio >= min_valid:
                    # This is diagnostic brightness coverage, never the validity mask.
                    nonzero_ratio = float(np.count_nonzero(valid & (pixels != 0)) / valid.size)
                    yield {"x0": x0, "y0": y0, "valid_ratio": ratio,
                           "nonzero_brightness_ratio": nonzero_ratio}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--step", type=int, default=64)
    parser.add_argument("--min-valid", type=float, default=0.95)
    args = parser.parse_args()
    for result in scan_windows(args.source, step=args.step, min_valid=args.min_valid):
        print(f"x0={result['x0']:5d} y0={result['y0']:5d} valid_ratio={result['valid_ratio']:.6f} "
              f"nonzero_brightness_ratio={result['nonzero_brightness_ratio']:.6f}")
