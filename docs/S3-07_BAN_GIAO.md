# S3-07 — Chốt phần tiền xử lý, sáng–tối, lọc trùng và thống kê

Phụ trách: Đinh Quang Hưng · Phụ thuộc: S3-03 (PR #46), S3-05, S2-12 · Ngày 04/11/2026, nền `main` `0e5b49f`.

Tài liệu này bàn giao cho người ghép báo cáo (S3-12): những gì đã sửa trong Chương 3, kết quả đối chiếu với lần chạy cuối, và đoạn văn/hình **sẵn để ghép** cho mục 4.8 và Bảng 5.1 khi bản đếm S3-03 được kiểm chéo.

## 1. Đối chiếu với phiên bản chạy cuối

Mọi con số trong các mục của Hưng ở Chương 3 được chạy lại ngày 04/11/2026 bằng mã trên `main` `0e5b49f` và cấu hình chốt `configs/s215_frozen.json`. Mục tiền xử lý của `configs/default.json` khớp `s215_frozen.json`.

| Nội dung trong Chương 3 | Cách kiểm | Kết quả |
|---|---|---|
| Tham số Bảng 3.2, Thuật toán 3.4–3.7 | So với `DEFAULT_PARAMS`, `REVIEW_DEFAULTS`, `DEDUPE_DEFAULTS` trong mã | Khớp; sửa công thức lề B8 cho đúng mã (mục 2) |
| Bảng 3.4 (sai số tự viết so với OpenCV) | Chạy lại `scripts/verify_report_numerics.py` trên bộ ảnh cài sạch | Trùng từng số với `docs/evidence/s3-12/report_numerics.json`; 78 phép so trên 26 ảnh và ví dụ Hough 5×5 đạt |
| Mục 3.4: 8/26 ảnh được chấm; 17–31 hợp, 18–27 ngược, 44–56 không rõ | Chạy lại `score_candidates` trên 8 ảnh với Hough S2-15 | Không đổi |
| Mục 3.5: STT 13 100→96, STT 17 100→97, các cặp M8→M32, M19→M15, M67→M66 | Chạy lại `review_candidates` rồi `dedupe_circles` | Không đổi |
| Mục 3.6: kiểm tra diện tích, đơn vị, dải | `scripts/s303_kiem_tra.py` | 13/13 đạt |
| Số test mục 3.8 | `python -m unittest discover -s tests` | 380 OK (trước ghi 370) |

Ghi chú khi chạy lại:
- `scripts/verify_report_numerics.py` từ chối chạy nếu `data/processed/` có khác 26 ảnh. Trên máy của Hưng còn sót ảnh mẫu cũ `moon_ap15_hia_crop01`, nên lần kiểm dùng bộ ảnh cài sạch bằng `scripts/install_s106_dataset.py` trong một worktree riêng.
- Hash nguồn trong JSON chạy lại khác bản trên `main` chỉ do xuống dòng CRLF trên Windows; mọi giá trị số trùng.

## 2. Đã sửa trong `docs/bao_cao/03_chuong_3_phuong_phap_cai_dat.md`

| Mục | Sửa | Lý do |
|---|---|---|
| 3.2, Bảng 3.2 | Lề B8 thành $\ell=\max(6,\lfloor h/2\rfloor+1)$ = 6 px với h = 11 | Mã tính theo kích thước kernel h; công thức cũ $\lceil 3\sigma\rceil+1$ chỉ trùng khi h lấy mặc định |
| 3.2 | Thêm một câu về đơn vị: ảnh [0, 1], ngưỡng Canny trên \|G\|·255, σ/h/lề theo pixel | Tiêu chí "đơn vị" |
| 3.4 | Nêu τ ở Bảng 2.1 và đơn vị pixel; ngưỡng bóng 0,06 là độ sáng chuẩn hóa; 1.500 px = 0,6 km² ở 20 m/px | Tiêu chí "tham số, đơn vị" |
| 3.4 | Ghi số đã chạy lại 04/11 bằng mã cuối; 26 bài test sáng–tối, 10 bài phân lớp/lọc | Tiêu chí "kết quả kiểm tra" |
| 3.5 | Đơn vị d, R, r; ghi đã chạy lại 04/11 | Như trên |
| 3.6 | Thêm đoạn "Kiểm tra số đếm và diện tích (S3-03)": 13 phép kiểm, diện tích tính lại, quy tắc loại vùng chung, ngưỡng 424 m là thăm dò; một dấu `[CHỜ]` cho số liệu mới | Tiêu chí "kết quả kiểm tra"; ghi chú review PR #30 |
| 3.8 | 370 → 380 test Python | Số đo ngày 04/11 |

Không sửa mục 3.1, 3.3, 3.7 (của Đức và Tiến). Mục 3.6 tăng khoảng một đoạn; nếu cần giữ ngân sách trang, có thể rút đoạn cuối mục 3.4 (so với vòng ngẫu nhiên).

## 3. Phần chờ kiểm chéo bản đếm S3-03

Bốn file `data/s303_counts/*_count.json` còn `reviewed_by = null`. Theo review PR #30 và PR #46, **chưa thay số trong báo cáo hay app** trước khi Quốc Anh tự xác nhận trên PR. Khi có xác nhận, người ghép làm như sau:

1. Điền `reviewed_by`, `reviewed_on` vào bốn file đếm; chuyển chúng thành số chính thức và chạy lại `scripts/s209_density.py` để cập nhật `docs/evidence/s2-09/so_sanh.json` (app và `tests/test_integration_density.py` đọc file này).
2. Thay mục 4.8 bằng đoạn ở mục 3.1 dưới đây, và thay Bảng 5.1 hàng M3 bằng dòng ở mục 3.2.
3. Xóa dấu `[CHỜ kiểm chéo bản đếm S3-03…]` ở mục 3.6 Chương 3.
4. Chạy lượt tái tạo mới cho bảng S2-09 của S3-10.

### 3.1. Đoạn thay cho mục 4.8 (Chương 4)

> **4.8. So sánh mật độ hai vùng**
>
> Chọn Lunokhod 1 (Mare Imbrium) và Mare Frigoris: cùng biển bazan, 20 m/px, nắng thấp (góc tới ảnh thành phần 60–79° và 61–84°), D = 300–2.000 m. Van de Graaff nắng cao 27–45° khó thấy hố nhỏ nên không dùng. Hai vùng dùng chung một quy tắc loại vùng: chỉ bỏ phần trùng giữa hai ô, dải ghép, vùng bóng lớn và phần trong vành, sườn ngoài của hố có D > 2 km. Hưng đếm đủ hố trên bốn ô, Quốc Anh kiểm chéo; không dùng nhãn thưa. Bảng 4.8 và Hình 4.4 cho kết quả.
>
> | Vùng | Diện tích (km²) | N | ρ (hố/km²) | Khoảng tin cậy 95 % |
> |---|---:|---:|---:|---|
> | Lunokhod 1 | 184,7 | 73 | 0,395 | 0,310–0,497 |
> | Mare Frigoris | 123,0 | 43 | 0,350 | 0,253–0,471 |
>
> : Bảng 4.8. Mật độ đếm tay đầy đủ, cùng 20 m/px, D = 300–2.000 m.
>
> Theo khoảng lớp kích thước 300–424; 424–600; 600–849; 849–1.200; 1.200–2.000 m, Lunokhod 1 có 42;18;8;3;2 hố, Mare Frigoris có 33;6;3;1;0. Tỷ số tổng mật độ 1,13, p = 0,57: **chưa đủ bằng chứng có khác biệt**, không kết luận vùng nào già hơn. Ở lớp nhỏ nhất, Mare Frigoris hơi cao hơn (0,268 so với 0,227 hố/km², p = 0,48). Từ 424 m trở lên, tỷ số 2,06 và p = 0,054; đây là phân tích thăm dò trong bốn ngưỡng, sau hiệu chỉnh Bonferroni p = 0,22, và chỉ thêm một hố đã đổi được kết luận ở mức 0,05. Hai đường tích lũy không cắt nhau: Lunokhod 1 cao hơn ở mọi ngưỡng đã xét.
>
> ![Hình 4.4. Tần suất tích lũy N(≥D)/km²; trục D theo mét, dải tô là khoảng tin cậy Poisson 95 %; nét chấm là bản đếm trước.](../evidence/s3-03/tich_luy.png){width=65%}
>
> Bất định lớn do ít hố, vùng nhỏ không phải mẫu ngẫu nhiên, thiếu phương vị nắng và có thể có cụm hố thứ cấp; sai số r đếm tay khoảng ±2 px. Đối chiếu với nhãn thưa S2-03 trong cùng vùng và dải, chỉ 4/30 nhãn khớp một hố đã đếm (tâm lệch ≤ 0,5 $r_{\text{nhãn}}$, không xét bán kính); đây là mức đồng thuận giữa hai bộ chú thích, không phải Recall của máy. Máy (Hough cấu hình S2-15, bỏ texture rồi lọc trùng) tìm lại 12 % và 0 % số hố; với `radius_balanced`, tỷ số máy 1,13 trùng đếm tay nhưng ở Mare Frigoris không vòng nào khớp, nên có thể chỉ là trùng hợp do bỏ sót và vòng không khớp bù trừ nhau. Mật độ ứng viên chưa dùng được; ứng dụng hiện bảng đếm tay riêng và ẩn mật độ máy khi chạm trần.

### 3.2. Dòng thay cho Bảng 5.1, hàng M3 (Chương 5)

> | M3 — Đếm và so hai vùng | Đạt một phần | Đếm tay 73 và 43 hố theo quy tắc loại vùng chung; 0,395 và 0,350 hố/km², p = 0,57: chưa kết luận vùng già hơn. Mật độ máy chưa dùng được |

### 3.3. Hình bàn giao

| Hình | File | Dùng ở |
|---|---|---|
| Tần suất tích lũy, bản mới và bản trước | `docs/evidence/s3-03/tich_luy.png` | Hình 4.4 |
| Histogram theo khoảng lớp √2 | `docs/evidence/s3-03/histogram.png` | Tùy chọn, phụ lục |
| Vùng đếm và hố đã đếm | `docs/evidence/s3-03/vung_dem.png` | Tùy chọn, phụ lục |

Tất cả tạo lại bằng `python scripts/s303_kiem_tra.py`.

## 4. Hạn chế còn lại

- Bản đếm S3-03 chưa được kiểm chéo; bản đầu do Claude lập, Hưng duyệt. Cần khai ở Phụ lục D.
- Phân lớp `texture` và lọc trùng vẫn chưa bật trong chuỗi mặc định; kết quả mới đo trên hai ảnh Apollo 16 có nhãn ứng viên.
- Chấm sáng–tối chỉ áp dụng được cho 8/26 ảnh; phiếu hướng nắng do một người kiểm.
- Chuỗi phiên bản `MODULE_VERSION` trong `src/postprocessing.py` vẫn là `s111-2` dù mô-đun đã có thêm phân lớp (S2-02) và lọc trùng (S2-05). Không ảnh hưởng kết quả; có thể đổi khi bật các bước này.
