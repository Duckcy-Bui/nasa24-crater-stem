# Tiền xử lý B0–B8 — S1-08

Cài đặt chuỗi theo [S1-04 mục 8](S1-04_Dac_ta_tien_xu_ly.docx). Mã nguồn: `src/preprocessing.py`. Đầu ra theo [DINH_DANG_DU_LIEU.md](DINH_DANG_DU_LIEU.md) mục 3.

## 1. Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows CMD; macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Kết quả mong đợi: mọi kiểm tra đạt. Nếu chưa cài numpy/opencv, các kiểm tra tiền xử lý tự bỏ qua để checker S1-05 vẫn chạy được.

## 2. Chạy và xem ảnh từng bước

```bash
# Hai cảnh giả lập (chưa có ảnh thật từ S1-06): nắng xiên 80° và nắng gần đứng 15°
python scripts/run_preprocessing.py --synthetic oblique
python scripts/run_preprocessing.py --synthetic overhead

# Ảnh thật: metadata JSON theo chuẩn S1-05 (crop_x0, crop_y0, downsample_k...)
python scripts/run_preprocessing.py --input data/raw/<file>.tif --metadata data/processed/<image_id>.json

# Thử tham số khác mà không sửa cấu hình
python scripts/run_preprocessing.py --synthetic oblique --set gauss_sigma=2.0 canny_high_pct=95
```

Mỗi lần chạy tạo một thư mục mới `outputs/<run_id>/`, không ghi đè lần trước:

| File | Nội dung |
|---|---|
| `overview.png` | Ghép 12 ô B1→B8; tiêu đề xanh = tự viết, đỏ = thư viện |
| `steps/B*.png` | Ảnh riêng từng bước (B3 gray, B4 enhanced, B5 smooth, B6 gx/gy/mag/theta, B7 canny, B8 edges, overlay, valid_mask) |
| `params.json` | Toàn bộ tham số đã dùng, kể cả giá trị tính ra: P0,5/P99,5, ngưỡng Canny low/high, số px biên |
| `metadata.json` | Metadata ảnh, trường `preprocess` và `valid_ratio` đã điền; đã qua `validate_metadata` |
| `run.json` | run_id, mã commit (`+working-tree` nếu còn sửa chưa commit), cấu hình, tham số ghi đè |
| `result.npz` | Các mảng đầu ra để Hough (S1-07) đọc: `np.load(...)["edges"]` |
| `truth_craters.json` | Chỉ có với cảnh giả lập: hố đúng do bộ tạo đặt, định dạng danh sách hố chung |

## 3. Tự viết và thư viện

| Bước | Thao tác | Cài đặt | Hàm |
|---|---|---|---|
| B0 | Đọc file, cắt cửa sổ 512·k | **Thư viện** rasterio | `read_window` |
| B1 | Thu nhỏ trung bình khối k×k | **Tự viết** NumPy | `block_mean` |
| B2 | Ảnh xám BT.601 | **Tự viết** NumPy | `to_gray` |
| B3 | Chuẩn hóa phân vị 0,5–99,5 % | **Tự viết** NumPy | `normalize_percentile` |
| B4 | CLAHE | **Thư viện** OpenCV `createCLAHE` | `clahe` |
| B5 | Gaussian tách hai chiều | **Tự viết** NumPy | `gaussian_kernel`, `gaussian_blur`, `correlate_1d` |
| B6 | Sobel 3×3, \|G\|, θ | **Tự viết** NumPy | `sobel` |
| B7 | Canny (NMS + ngưỡng kép) | **Thư viện** OpenCV `Canny`; ngưỡng tự động P90 tự viết | `canny` |
| B8 | Bỏ biên trong lề 6 px từ mép ảnh và nodata | **Tự viết** NumPy | `erode`, `mask_edges` |

"Tự viết" nghĩa là chỉ dùng phép toán mảng NumPy (cộng, nhân, cắt lát, `np.pad`, `np.percentile`); không gọi hàm lọc ảnh dựng sẵn. OpenCV chỉ được gọi trong B4, B7 và trong `tests/` để đối chiếu. Danh sách này cũng được ghi vào `params.json` (khóa `steps`) của mỗi lần chạy.

## 4. Kiểm chứng phần tự viết (S1-04 mục 9)

`tests/test_preprocessing.py`:

| Phần tự viết | Đối chiếu | Kết quả |
|---|---|---|
| Thu nhỏ khối, k = 2, 3, 4 | `cv2.resize(INTER_AREA)` | sai khác < 1e-5 |
| Gaussian σ = 1; 1,5; 2,5 | `cv2.GaussianBlur(BORDER_REFLECT_101)` | sai khác < 1e-5 |
| Sobel gx, gy, \|G\| | `cv2.Sobel(ksize=3, CV_32F)` | sai khác < 1e-5 |
| Chuẩn hóa phân vị | Ma trận 3×3 tính tay; pixel lỗi bị loại | đúng công thức |
| Ảnh xám | R, G, B, trắng → 0,299; 0,587; 0,114; 1 | đúng |
| Dấu gradient | Ảnh sáng dần sang phải/xuống dưới | θ = 0 và π/2 |
| Mặt nạ biên | Lề 6 px quanh mép và quanh pixel nodata | đúng |

## 5. Điểm lệch S1-04 cần Hưng và Tiến xác nhận

**CLAHE dùng uint8 thay vì uint16** (`clahe_bits = 8`). OpenCV đặt ngưỡng cắt mỗi bin là `max(1, clipLimit × số pixel một ô / số bin)`. Với uint16 (65536 bin) và ô 64×64 thì `2 × 4096 / 65536 < 1`, nên ngưỡng luôn bằng 1: `clipLimit` = 1, 2, 4 cho kết quả giống hệt nhau và nhiễu vùng phẳng bị khuếch đại khoảng 9 lần. Với uint8 (256 bin) ngưỡng bằng 32, `clipLimit` có tác dụng đúng như mô tả. Phương án uint16 vẫn chạy được bằng `--set clahe_bits=16` để so sánh; kiểm tra `test_b4_clip_limit_has_effect_in_8bit_only` ghi lại hiện tượng này.

## 6. Hạn chế đã thấy

- **Ngưỡng Canny P90 giả định khoảng 10 % pixel là biên mạnh.** Trên vùng phẳng hoặc kết cấu mịn, ngưỡng rơi vào mức nhiễu nên Canny giữ nhiều biên kết cấu ngoài vành hố (thấy rõ ở B7 của hai cảnh giả lập). `canny_high_pct`, `canny_low_ratio` và `gauss_sigma` cần chỉnh trên tập điều chỉnh (S2-15).
- **Cảnh giả lập không có bóng đổ dài**, nên chưa thể hiện hạn chế nắng rất xiên của S1-04 mục 10. Cần chạy lại trên ảnh thật STT 13/14 (nắng xiên) và STT 17 (nắng đứng) khi S1-06 bàn giao.
- B8 không phát hiện được đường ghép mosaic nằm giữa vùng hợp lệ; S1-06 vẫn phải tránh khi cắt ảnh.
