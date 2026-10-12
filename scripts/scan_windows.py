import sys
# pyrefly: ignore [missing-import]
import rasterio

SIZE = 512
STEP = 64

with rasterio.open(sys.argv[1]) as f:
    img = f.read(1)

valid = img > 0
h, w = valid.shape
for y0 in range(0, h - SIZE + 1, STEP):
    for x0 in range(0, w - SIZE + 1, STEP):
        ratio = valid[y0:y0 + SIZE, x0:x0 + SIZE].mean()
        if ratio >= 0.95:
            print(f"x0={x0:5d} y0={y0:5d} valid_ratio={ratio:.3f}")