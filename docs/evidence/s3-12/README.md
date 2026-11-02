# Kiểm số học cho báo cáo S3-12 — 01/11/2026

`report_numerics.json` ghi 78 đối chiếu trên đủ 26 ảnh đã cài, cùng hash đầu vào/mã và môi trường đúng lượt này. Không dùng cấu hình máy ở đây để bổ sung cho phép đo Windows 27/10 hoặc lượt Linux S3-10 31/10. Đây là kiểm sai số số học, không phải đo chất lượng phát hiện hố hay kết quả S3-05.

```bash
python -B scripts/verify_report_numerics.py --out outputs/report_numerics.json
```

Đầu ra phải là file mới. Script yêu cầu đủ 26 ảnh 512 × 512 có toàn bộ pixel hợp lệ; dùng dữ liệu float32, đối chiếu trung bình khối k=2 với OpenCV `INTER_AREA`, Gauss σ=1,5/kernel 11 và Sobel với biên `REFLECT_101`. Sai số tính bằng float64; MSE gộp theo số phần tử. Ngưỡng kiểm sai số lớn nhất là 1e-5. Mọi phép tính xác định, không dùng lấy mẫu ngẫu nhiên. Script gọi lại `tiny_example()` của `verify_hough_examples.py` để so từng ma trận tính tay 5 × 5 với NumPy.

Kết quả: 78/78 đối chiếu có sai số lớn nhất dưới ngưỡng, ví dụ Hough khớp; bảng tổng hợp ở mục 3.8 của báo cáo, mã kiểm được dẫn từ Phụ lục B. Các khác biệt cỡ 1e-7 phát sinh từ thứ tự cộng và làm tròn float32/float64. Không so MSE của danh sách vòng Hough với OpenCV vì hai thuật toán/ngưỡng không tương đương.
