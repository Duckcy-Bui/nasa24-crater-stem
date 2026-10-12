import sys
import numpy as np
# pyrefly: ignore [missing-import]
import rasterio
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt

with rasterio.open(sys.argv[1]) as f:
    img = f.read(1)
    print("transform:", f.transform)

print("min / max:", img.min(), img.max())
print("pixel = 0:", np.count_nonzero(img == 0), "/", img.size)

plt.imshow(img, cmap="gray")
plt.title("Trục = tọa độ pixel (cột x, hàng y)")
plt.show()