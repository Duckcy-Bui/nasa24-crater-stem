# Minh chứng S2-01 — 24/10/2026

Đo NumPy bản gốc và bản tối ưu trên cùng máy, cùng cấu hình `configs/s201_hough.json`, cùng edges/theta và toàn dải bán kính metadata. Mỗi bản warm-up 1 lần, đo 5 lần; đảo thứ tự giữa các lần. Chỉ tính thời gian Hough.

| Ảnh | Pixel biên | r thực quét | Median gốc (s) | Median tối ưu (s) | Tăng tốc | Đầu ra |
|---|---:|---|---:|---:|---:|---|
| moon_ap16_m106777343r_c01 | 26 883 | 5–125, bước 1 | 21,765116 | 9,064821 | 2,40× | Giống hệt ở mọi lần đo |
| moon_ap16_m132732855l_c01 | 24 291 | 5–125, bước 1 | 58,981975 | 26,106811 | 2,26× | Giống hệt ở mọi lần đo |
| moon_ap15_hia_c01 | 27 996 | 5–100, bước 1 | 51,520850 | 24,514279 | 2,10× | Giống hệt ở mọi lần đo |

## Căn cứ và tái chạy

Baseline: `eb8278cc82901cc28dbbc6509b0ff0b6bfefa0cc`. Bản tối ưu là working tree trên nhánh `s2-01-hough-performance`; hash từng file có trong [report.json](report.json). Không tự tạo commit thay người phụ trách.

[timings.csv](timings.csv) có median/min/max và số vòng. Report có tất cả mẫu đo, môi trường, cấu hình đã resolve, hash đầu vào/metadata/mask, danh sách r, vòng phát hiện và cờ tương đương/ổn định. [regression.log](regression.log) là log kiểm tra toàn bộ Python.

```powershell
.\.venv\Scripts\python.exe -B scripts/benchmark_s201.py --images moon_ap16_m106777343r_c01 moon_ap16_m132732855l_c01 moon_ap15_hia_c01 --repeats 5 --warmups 1
```

Run đầy đủ ở `outputs/s201/s201_20261024T111329332160Z_fc8287f7/` trên máy này, gồm nguồn baseline và arrays đầu vào. Outputs không theo dõi bằng Git; report/CSV trong thư mục này là bản minh chứng được giữ trong dự án. Muốn tái chạy cần baseline commit và bộ ảnh đã giải nén.

## Nhận xét và giới hạn

Điểm nghẽn thực tế: cấp phát histogram H×W cho mỗi lỗ, kể cả khi chỉ có phiếu trong một đoạn nhỏ. Thay bằng histogram trên đoạn chỉ số có phiếu giữ nguyên mọi quyết định phát hiện. Cấu hình tìm kiếm không bị thu hẹp để tạo chênh lệch thời gian.

Cả ba ảnh vẫn chậm trên 100 ứng viên. Số vòng, phiếu, tọa độ, bán kính và thứ tự đều giống baseline; chưa giải quyết vòng giả hoặc vòng trùng. Nhãn thật hiện thừa/chưa kiểm chéo nên không báo Precision/Recall. Kết quả này là minh chứng tăng tốc trên ba ảnh đo, không bảo đảm hệ số tương tự cho mọi ảnh/máy.

Không thực hiện S2-05 hoặc S2-06. Giữ nguyên `scripts/verify_hough_examples.py`, mô sáng–tối, matching, scoring và giao diện.

## Kiểm tra hồi quy

209/209 test Python đạt (60,145 giây), gồm 5 test S2-01 và 18 test Hough/ví dụ hiện có. Chạy với Python 3.12, dependency theo `requirements-test.txt` và `PYTHONUTF8=1`. Đã cài các dependency còn thiếu trong .venv, không đổi requirements hoặc mã các task khác.
