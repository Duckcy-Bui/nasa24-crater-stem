import sys
# pyrefly: ignore [missing-import]
import rasterio

with rasterio.open(sys.argv[1]) as f:
    print("Rộng x cao:", f.width, f.height)
    print("Số kênh, kiểu dữ liệu:", f.count, f.dtypes)
    print("Kích thước pixel:", f.res)
    print("Hệ tọa độ:", f.crs)
    print("Giá trị nodata:", f.nodata)
    print("Phạm vi:", f.bounds)