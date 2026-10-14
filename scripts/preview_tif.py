"""Preview a source TIFF while masking raster nodata and nonfinite pixels."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    with rasterio.open(args.source) as src:
        pixels = src.read(1)
        mask = (src.read_masks(1) != 0) & np.isfinite(pixels)
        print("transform:", src.transform)
    if not mask.any():
        raise ValueError("Không có pixel hợp lệ để xem.")
    print("min / max hợp lệ:", pixels[mask].min(), pixels[mask].max())
    print("pixel 0 hợp lệ:", np.count_nonzero(mask & (pixels == 0)))
    print("valid_ratio:", float(mask.mean()))
    plt.imshow(np.ma.array(pixels, mask=~mask), cmap="gray")
    plt.title("Trục = tọa độ pixel (cột x, hàng y); nodata bị che")
    plt.show()
