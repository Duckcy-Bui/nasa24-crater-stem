<!-- S3-12, 01/11/2026: rút theo giao việc của Đức trên main c466c2d (đã gồm PR #26, #31, #33–#36).
Bảng mọi chỗ cắt, kèm lý do và chủ phần, ở mô tả PR S3-12. Chủ phần chưa xác nhận bản rút gọn; bản trước rút là main c466c2d.
-->

# Chương 4. Dữ liệu, đánh giá và khảo sát

Chương này trình bày dữ liệu, nhãn tham chiếu, cách chia tập, phương pháp đánh giá, ba thí nghiệm và khảo sát người chơi. Chuỗi phát hiện ở Chương 3; quy tắc ghép hố và các độ đo ở mục 2.4; trò chơi và cách chấm điểm người chơi ở Chương 5.

## 4.1. Nguồn ảnh và bộ dữ liệu

Nhóm dùng ảnh Mặt Trăng của camera góc hẹp (NAC) trên tàu Lunar Reconnaissance Orbiter, lấy từ kho PDS của LROC [@lroc_pds] ngày 14/10/2026, ghi công NASA/GSFC/Arizona State University. Có hai loại sản phẩm: mosaic `NAC_ROI` ở 20 m/px [@robinson2012] và ảnh NAC đơn `NAC_PHO` ở 2 m/px thuộc chuỗi E090S0155 quanh bãi đáp Apollo 16 [@martin2018]. Cả hai đều là TIFF browse 8 bit, loại ảnh dùng để xem chứ không dùng cho đo đạc định lượng [@lroc_rdrsis]. Vì vậy dữ liệu chỉ phục vụ bài toán hình học ảnh: tìm vòng tròn, đếm và so sánh.

Bộ dữ liệu `s106_lroc_browse_v2` gồm 26 ảnh cắt 512 × 512 px lấy từ 16 ảnh nguồn: 15 ảnh cắt 20 m/px từ 6 mosaic và 11 ảnh cắt 2 m/px từ 10 ảnh Apollo 16 (Bảng 4.1). STT là mã ảnh nguồn trong danh sách của nhóm.

| STT | Vùng | Tỷ lệ | Góc tới (°) | Ảnh nguồn | Ảnh cắt |
|:---------:|:----------------------------|:---------:|:------------:|:--------:|:--------:|
| 1 | Apollo 15, Mặt Trời cao | 20 m/px | 28–53 (\*) | 1 | 3 |
| 2 | Apollo 15, Mặt Trời thấp | 20 m/px | không ghi | 1 | 3 |
| 3 | Van de Graaff, Mặt Trời cao | 20 m/px | 27–45 (\*) | 1 | 2 |
| 4 | Lunokhod 1, Mặt Trời thấp | 20 m/px | 60–79 (\*) | 1 | 2 |
| 5 | Lunokhod 2, Mặt Trời thấp | 20 m/px | 56–83 (\*) | 1 | 2 |
| 6 | Mare Frigoris, Mặt Trời thấp | 20 m/px | 61–84 (\*) | 1 | 3 |
| 8–11, 13–18 | Apollo 16, chuỗi E090S0155 | 2 m/px | 7,64–87,78 | 10 | 11 |
| | **Tổng** | | | **16** | **26** |

: Bảng 4.1. Nhóm ảnh nguồn và số ảnh cắt. (\*) Dải góc tới của các ảnh thành phần trong mosaic, không phải số đo tại cửa sổ cắt.

Script `scripts/generate_s106_crops.py` cắt mỗi cửa sổ theo góc trên-trái $(x_0, y_0)$, nằm trọn trong ảnh nguồn và tránh đường ghép mosaic; ảnh không bị thu nhỏ ($k = 1$). Mặt nạ hợp lệ là giao của mặt nạ raster và điều kiện giá trị hữu hạn; pixel bằng 0 vẫn hợp lệ, và cả 26 ảnh có tỷ lệ pixel hợp lệ bằng 1,0. Giá trị pixel được chuẩn hóa về [0, 1] theo phân vị 0,5 % và 99,5 %. Metadata của mỗi ảnh ghi mã nguồn, vị trí cắt, tỷ lệ, tọa độ tâm, hướng Bắc, chiếu sáng, dải bán kính, CRS và affine của ảnh nguồn, cùng mã băm SHA-256 của script và cấu hình. Chiếu sáng có mức tin cậy `measured`, `side_only` hoặc `none`, và không ảnh nào có phương vị đo được. Tám ảnh Apollo 16 ghi `side_only` (nắng phía Tây, phương vị 270° chỉ là quy ước); STT 11, 15, 16 và 15 ảnh mosaic ghi `none`.

Toàn bộ ảnh được đóng thành một gói ngoại tuyến 12.861.130 byte, có kiểm tra SHA-256 khi cài. File `sources.json` lưu URL, kích thước và SHA-256 của 16 TIFF nguồn (503.640.706 byte), nên có thể tải lại và tái tạo ảnh cắt.

Dữ liệu phục vụ ba kiểu so sánh. Vùng 1 gồm Apollo 15 khi Mặt Trời cao (1A) và thấp (1B), ở hai tọa độ khác nhau, nên chỉ là hai nhóm điều kiện chụp. Cặp so mật độ gồm Lunokhod 1 và Mare Frigoris, cùng là biển bazan, cùng 20 m/px, cùng Mặt Trời thấp và cùng dải đường kính 300–2.000 m (mục 3.6). Cặp dự kiến ban đầu Van de Graaff – Mare Frigoris không dùng vì hai ảnh chụp ở góc nắng rất khác nhau; mật độ hố chỉ gợi ý tuổi tương đối [@neukum2001]. Cặp STT 9 (góc tới 81,08°) và STT 17 (7,64°) có cùng cửa sổ (1190, 2750), dùng để minh họa ảnh hưởng của chiếu sáng. Các ảnh cắt cùng mosaic có thể chồng lấp, nên không phải mẫu độc lập.

## 4.2. Quy đổi tọa độ ảnh cắt và ảnh nguồn

Tâm pixel ảnh cắt có tọa độ nguyên, x là cột, y là hàng, gốc ở góc trên-trái. `source_coordinates` trong `src/contracts.py` đổi sang ảnh nguồn bằng vị trí cửa sổ và hệ số thu nhỏ, có bù tâm pixel khi k khác 1. Khi áp dụng affine của rasterio phải cộng 0,5 vì affine dùng góc pixel. Công thức và ví dụ tọa độ địa lý ở Phụ lục E.7.

Đường kính $D = 2rs$ và dải bán kính theo (2.14): D = 20–500 m ở 2 m/px cho r = 5–125 px; D = 200–4.000 m ở 20 m/px cho r = 5–100 px. `scripts/verify_s116_coords.py` kiểm cả 26 ảnh: 26/26 khớp metadata, sai khác lớn nhất khoảng $6 \cdot 10^{-14}$ độ.

## 4.3. Nhãn tham chiếu

### 4.3.1. Gán nhãn và kiểm chéo

Nhãn tham chiếu được gán bằng `scripts/label_craters.py`: người gán nhấp vào tâm hố rồi vào một điểm trên vành, công cụ tính bán kính, kiểm tra cấu trúc dữ liệu và ghi kèm một ảnh overlay để kiểm chéo. Hố chưa chắc chắn, chẳng hạn vành xói mòn không khép kín hay nằm trong bóng sâu, có hậu tố `_uncertain` trong mã. Nhãn của nhóm là nhãn thưa: mỗi ảnh chỉ có một số hố được gán, và thiếu nhãn không có nghĩa là không có hố.

Cả 26 ảnh cắt có file nhãn, tổng cộng 241 nhãn, mỗi ảnh từ 4 đến 13 nhãn. Chỉ có 1 nhãn chưa chắc chắn (`C4_uncertain` trên `moon_ap16_m106777343r_c01`), nên 240 nhãn được dùng khi tính độ đo. Mọi nhãn nằm trong dải bán kính tìm kiếm (Bảng 4.2).

| Vùng mặt đất | Tập | Ảnh cắt | Nhãn | Chưa chắc | $r$ (px) | $D$ (m) |
|:------------------------|:-----------|:-------:|:------:|:-------:|:----------:|:-----------:|
| Apollo 16 (2 m/px) | điều chỉnh | 11 | 111 | 1 | 5,15–26 | 21–104 |
| Apollo 15, Mặt Trời cao | điều chỉnh | 3 | 24 | 0 | 7–30 | 280–1.200 |
| Van de Graaff | điều chỉnh | 2 | 21 | 0 | 7–20 | 280–800 |
| Lunokhod 1 | điều chỉnh | 2 | 19 | 0 | 7,5–55 | 300–2.200 |
| Apollo 15, Mặt Trời thấp | kiểm tra | 3 | 26 | 0 | 8–32 | 320–1.280 |
| Lunokhod 2 | kiểm tra | 2 | 18 | 0 | 8–50 | 320–2.000 |
| Mare Frigoris | kiểm tra | 3 | 22 | 0 | 7,5–24 | 300–960 |
| **Tổng** | | **26** | **241** | **1** | 5,15–55 | |

: Bảng 4.2. Nhãn tham chiếu theo vùng mặt đất. Các vùng ngoài Apollo 16 có tỷ lệ 20 m/px.

Cả 26 file ghi nguồn `manual_label_s110; sparse manual labels, reviewed by Nguyen Manh Tien`. Theo xác nhận của người kiểm ngày 27/10/2026, Nguyễn Mạnh Tiến đã đối chiếu bằng mắt từng vòng trên đủ 26 ảnh overlay. Kiểm tra tự động cho thấy 26/26 file khớp với manifest, chỉ mục nhãn và ảnh overlay, nhưng kiểm tra này chỉ xác nhận định dạng, không xác nhận vị trí hố.

### 4.3.2. Danh mục Robbins và nhãn mù

Danh mục hố của Robbins chỉ đầy đủ cho hố từ khoảng 1–2 km trở lên [@robbins2019]. Dải 20–500 m của ảnh 2 m/px nằm hoàn toàn dưới ngưỡng này; với ảnh 20 m/px, chỉ phần trên của dải 200–4.000 m nằm trong phạm vi đầy đủ. Nhóm chưa chiếu danh mục lên ảnh 20 m/px, vì việc đó cần quy đổi ngược theo mục 4.2, đối chiếu bằng mắt từng hố và chỉ cho một tập con hố lớn. Mọi nhãn tham chiếu hiện có đều là nhãn tay.

Bước rà biên ở Chương 3 dùng thêm nhãn mù gán trực tiếp cho ứng viên máy. Trên STT 13 (`moon_ap16_m132732855l_c01`, góc tới 87,7°), 100 ứng viên của cấu hình mặc định được đưa lên một phiếu không hiện lớp do máy xếp. Kết quả: 8 vành hố thật, 7 ranh giới bóng, 79 biên kết cấu, 6 không chắc (Đinh Quang Hưng gán, Hoàng Quốc Anh kiểm chéo, 23/10/2026). Trên STT 17, kết quả là 17 vành hố thật, 66 biên kết cấu và 17 không chắc (25/10/2026). Nhãn mù không chứa các hố máy bỏ sót, nên không dùng để tính Recall_known.

## 4.4. Tập điều chỉnh và tập kiểm tra

Tập điều chỉnh dùng để chọn tham số; tập kiểm tra chỉ dùng để báo cáo kết quả cuối. Cách chia hiện hành (phiên bản 3, `data/s203_split/manifest_split.json`) theo quy tắc: các ảnh cắt chồng lấp nhau, hoặc cùng mặt đất chụp dưới điều kiện nắng khác nhau, phải nằm cùng một tập. Vì vậy cả 11 ảnh Apollo 16 thuộc tập điều chỉnh. Các ảnh này thuộc cùng chuỗi ảnh quanh bãi đáp Apollo 16, tâm cách nhau từ 0 đến 8,06 km, trong khi mỗi ảnh cắt rộng 1.024 m: 24 trong 55 cặp chồng lấp mặt đất, với khoảng cách tâm 340–680 m tương ứng mức chồng lấp 33–67 %. Bốn ảnh STT 9, 11, 17 và 18 còn dùng chung cửa sổ (1190, 2750), và STT 13 đã được dùng để chọn cách lọc ở bước rà biên. Tập kiểm tra gồm ba vùng độc lập: Apollo 15 khi Mặt Trời thấp (cách tập điều chỉnh 50,1–62,8 km), Lunokhod 2 (721,4–726,9 km) và Mare Frigoris (1.095–1.106 km).

Tập điều chỉnh gồm 18 ảnh cắt từ bốn vùng: 11 ảnh Apollo 16 ở 2 m/px, cùng Apollo 15 khi Mặt Trời cao, Van de Graaff và Lunokhod 1 ở 20 m/px; có 174 nhãn được tính. Tập kiểm tra gồm 8 ảnh cắt 20 m/px từ ba vùng, với 66 nhãn được tính (Bảng 4.2). Chỉ 8 ảnh Apollo 16 của tập điều chỉnh thỏa điều kiện của bước sáng–tối (Chương 3): có phía nắng đã biết và góc tới từ 30° trở lên. STT 10 (28,38°) và hai ảnh cắt của STT 17 (7,64°) bị loại vì nắng gần đứng.

Cách chia có hai giới hạn. Thứ nhất, cả 8 ảnh kiểm tra đều là mosaic 20 m/px với `sun.quality = none`, nên bước sáng–tối luôn ghi `not_checked` và thí nghiệm E1 không có phép đo ngoài mẫu. Thứ hai, tập kiểm tra không có ảnh 2 m/px, nên kết quả trên Apollo 16 chỉ là kết quả chẩn đoán và được báo riêng. Khắc phục cần một cụm ảnh Apollo 16 mới, không chồng lấp với tập điều chỉnh; bộ dữ liệu hiện chưa có. Ngoài ra, hai vùng so sánh 2A và 2B nằm ở hai tập khác nhau, nên khi so mật độ cần nêu sai số phát hiện của từng vùng. Ảnh `moon_marefrig_loc_c01` của tập kiểm tra đã được dùng làm ảnh đối chứng trong thử nghiệm tiền xử lý trước khi chốt cách chia; thử nghiệm đó giữ nguyên tham số mặc định, nhưng đây vẫn là điểm cần lưu ý.

## 4.5. Phương pháp đánh giá

**Ghép và độ đo.** Dùng quy tắc một–một và Recall_known ở mục 2.4: tâm lệch không quá 0,5 bán kính nhãn, tối đa số cặp rồi tối thiểu tổng khoảng cách bằng Hungary tự viết. Máy chỉ so với nhãn tham chiếu; so người chơi với máy không sinh điểm. Nhãn thưa không cho Precision/F1 toàn ảnh; nhãn chưa chắc chắn thuộc tập bỏ qua. Chỉ tính Precision/F1 khi `catalogue_coverage = "complete"`, hiện chưa file nào đạt. Recall_known luôn đi kèm số nhãn, số ứng viên và trạng thái chạm trần.

**Chạy tập kiểm tra.** Tham số chỉ được chọn trên tập điều chỉnh; tập kiểm tra chạy một lần với cấu hình đã đóng băng. Lần đánh giá ở mục 4.7 đã dùng tập kiểm tra một lần cho hai chế độ chọn ứng viên được cố định từ trước, trước khi S2-15 chốt tham số ngày 29/10/2026; cấu hình cuối `configs/s215_frozen.json` giữ `score` dựa trên 18 ảnh điều chỉnh; mọi lần chạy lại trên tập kiểm tra sau đó phải được ghi rõ trong báo cáo. Script `scripts/s207_experiments.py` từ chối ảnh kiểm tra nếu thiếu cờ `--holdout`, cờ này bắt buộc kèm `--chosen-config` (file tham số đã chốt), và ở chế độ đó script chỉ chạy đúng cấu hình đã chốt, không quét biến thể.

## 4.6. Thiết kế ba thí nghiệm

Ba thí nghiệm dùng chung quy tắc ở mục 4.5 và được tái tạo bằng `scripts/s207_experiments.py` (Bảng 4.3).

| Thí nghiệm và câu hỏi | Ảnh | Biến thể |
|:--------------------|:--------------------|:----------------------|
| E1. Bước sáng–tối thay đổi gì so với Hough cơ bản? | Apollo 16, tập điều chỉnh, có hướng nắng dùng được | Hough cơ bản; thêm nhãn sáng–tối; thử bỏ vòng "ngược" |
| E2. Tham số Hough ảnh hưởng thế nào? | Ảnh đại diện của tập điều chỉnh | `min_vote_ratio` 0,30 / 0,35 / 0,40; `radius_step` 1 / 2 px; mỗi lượt đổi một tham số |
| E3. Ảnh khó được xử lý ra sao? | STT 13 (bóng mạnh), STT 17 (nắng gần đứng), Mare Frigoris | Phân lớp vành / bóng / kết cấu; bỏ lớp kết cấu; lọc vòng trùng |

: Bảng 4.3. Thiết kế ba thí nghiệm.

Ở E1, bước sáng–tối chỉ gắn nhãn mà không xóa vòng, nên hai nhánh đầu có cùng Recall_known; phần đáng so là phân bố nhãn sáng–tối của vòng khớp và không khớp nhãn. Nhánh bỏ vòng "ngược" đo rủi ro mất hố; trên STT 13, lọc này đã loại nhầm 2 trong 8 hố thật (Chương 3). Ở E2, mặc định là `min_vote_ratio = 0,35`, `radius_step = 1` px, tối đa 100 vòng; tiêu chí chọn là không làm giảm Recall_known, rồi ưu tiên ít vòng hoặc nhanh hơn. Ở E3, bỏ lớp kết cấu và lọc vòng trùng được báo riêng, không tự bật trong chuỗi chính; Mare Frigoris thuộc tập kiểm tra nên chỉ được mô tả.

Ngày 26/10/2026, nhóm chạy kiểm tra luồng trên `moon_ap16_m109134835l_c01` (STT 17, 10 nhãn bán kính 8–22 px). Đây là kiểm tra kỹ thuật, không phải kết quả thí nghiệm. Với E1, góc tới 7,64° nhỏ hơn 30° nên 100/100 ứng viên ghi `not_checked`, đúng quy tắc. Với E2, cả bốn biến thể chạm trần 100 ứng viên và cho Recall_known 0/10 (Bảng 4.4), nên chưa đủ căn cứ chọn tham số. Với E3, bước phân lớp cho 61 vành hố và 39 biên kết cấu, lọc vòng trùng bỏ 3 vòng, Recall_known vẫn 0/10. Trong khi đó, nhãn mù trên ứng viên của cấu hình mặc định ở cùng ảnh ghi 17/100 vành hố thật: máy có tìm được hố, nhưng không tìm lại được 10 hố đã gán nhãn.

| Biến thể | Ứng viên | Thời gian Hough (s) | Recall_known |
|:----------------------------------|:---:|:---:|:---:|
| Mặc định | 100 | 9,136 | 0/10 |
| `min_vote_ratio` = 0,30 | 100 | 8,437 | 0/10 |
| `min_vote_ratio` = 0,40 | 100 | 8,375 | 0/10 |
| `radius_step` = 2 px | 100 | 4,325 | 0/10 |

: Bảng 4.4. Chạy kiểm tra luồng E2 trên STT 17 (một lần đo, không phải kết quả cuối).

[CHỜ S3-05: kết quả ba thí nghiệm trên tập điều chỉnh và tập kiểm tra]

## 4.7. Kết quả phát hiện

Đánh giá phát hiện được chạy ngày 27/10/2026 bằng `scripts/evaluate_hough.py` trên ba ảnh của tập điều chỉnh (STT 13, STT 17, `moon_ap15_hia_c01`) và đủ 8 ảnh của tập kiểm tra. Hough tròn tự cài đặt bằng NumPy được đối chiếu với `HoughCircles` của OpenCV [@opencv_hough_tutorial].

**Điều kiện đánh giá.** Cấu hình Hough được cố định trong `configs/s201_large_craters.json` trước khi đánh giá: bỏ phiếu toàn vòng, bán kính 5–128 px kẹp theo metadata, bước bán kính 1 px, bước góc 1°, `min_votes = 12`, `min_vote_ratio = 0,35`, NMS 4 px cho tâm và 2 px cho bán kính, tối đa 100 vòng. Hough NumPy có hai chế độ chọn đỉnh: `numpy_score` chọn theo số phiếu, `numpy_balanced` chọn luân phiên giữa các nhóm bán kính để vòng nhỏ không chiếm hết 100 chỗ (Chương 3). Hai chế độ được xác định trước khi đọc kết quả tập kiểm tra, và không tham số nào được chỉnh theo kết quả đó. OpenCV dùng `HOUGH_GRADIENT` với `dp = 1`, `minDist = 4`, `param1 = 100`, `param2 = 12`, cùng tiền xử lý và dải bán kính, nhưng tự trích biên và không giới hạn 100 vòng; hai cài đặt vì vậy không tương đương. Thời gian là trung vị của 3 lần đo; với NumPy chỉ gồm bước Hough, với OpenCV gồm cả trích biên.

Bảng 4.5 tóm tắt kết quả. Cột gộp cộng số hố của mọi ảnh; cột theo ảnh là trung bình Recall_known từng ảnh kèm độ lệch chuẩn mẫu, không phải khoảng tin cậy.

| Tập | Phương pháp | TP | FN | Recall_known gộp (%) | Trung bình theo ảnh ± SD (%) |
|:------------|:----------------|:----------:|:----------:|:-----------:|:--------------:|
| Điều chỉnh | numpy_score | 0 | 28 | 0,00 | 0,00 ± 0,00 |
| Điều chỉnh | numpy_balanced | 2 | 26 | 7,14 | 7,41 ± 6,42 |
| Điều chỉnh | opencv | 27 | 1 | 96,43 | 96,67 ± 5,77 |
| Kiểm tra | numpy_score | 4 | 62 | 6,06 | 5,95 ± 8,77 |
| Kiểm tra | numpy_balanced | 5 | 61 | 7,58 | 7,64 ± 8,88 |
| Kiểm tra | opencv | 65 | 1 | 98,48 | 98,21 ± 5,05 |

: Bảng 4.5. Recall trên nhãn đã biết theo tập (điều chỉnh: 3 ảnh; kiểm tra: 8 ảnh) và phương pháp. TP và FN đếm trên nhãn đã biết (TP_known, FN_known); không tính Precision và F1.

Bảng 4.6 cho kết quả từng ảnh của tập kiểm tra. Trên tập kiểm tra, thời gian trung vị mỗi ảnh là 6,056–22,250 s với `numpy_score`, 6,332–25,497 s với `numpy_balanced` và 3,153–6,970 s với `opencv`. Trên ba ảnh của tập điều chỉnh, `numpy_score` cho 0/9, 0/10, 0/9 và `numpy_balanced` cho 1/9, 0/10, 1/9.

| Ảnh | Nhãn | score | balanced | opencv | Số vòng opencv |
|:--------------------------|:-------:|:--------:|:----------:|:--------:|:----------:|
| moon_ap15_loc_c01 | 8 | 0/8 | 0/8 | 8/0 | 8.195 |
| moon_ap15_loc_c02 | 9 | 0/9 | 0/9 | 9/0 | 8.323 |
| moon_ap15_loc_c03 | 9 | 0/9 | 0/9 | 9/0 | 8.438 |
| moon_lunokhod2_loc_c01 | 9 | 1/8 | 1/8 | 9/0 | 9.040 |
| moon_lunokhod2_loc_c02 | 9 | 0/9 | 1/8 | 9/0 | 9.086 |
| moon_marefrig_loc_c01 | 6 | 0/6 | 1/5 | 6/0 | 8.259 |
| moon_marefrig_loc_c02 | 7 | 1/6 | 0/7 | 6/1 | 8.521 |
| moon_marefrig_loc_c03 | 9 | 2/7 | 2/7 | 9/0 | 8.866 |
| **Tổng** | **66** | **4/62** | **5/61** | **65/1** |  |

: Bảng 4.6. Kết quả từng ảnh trên tập kiểm tra, ghi TP/FN cho từng phương pháp. Hai chế độ NumPy trả đúng 100 vòng trên mọi ảnh.

**Diễn giải.** Recall_known của Hough NumPy rất thấp: 6,06 % (`numpy_score`) và 7,58 % (`numpy_balanced`) trên tập kiểm tra. Chế độ cân bằng chỉ gỡ được một nguyên nhân bỏ sót: trên STT 13, `numpy_score` giữ 100 vòng đều có bán kính không quá 10 px, còn `numpy_balanced` giữ 29 vòng có bán kính trên 16 px, lớn nhất 31 px. Trên `moon_marefrig_loc_c02`, kết quả còn giảm từ 1/7 xuống 0/7, và cấu hình không được chỉnh lại sau đó. Vành lớn hơn 128 px, vành đứt hoặc không tròn, và đỉnh chưa đủ ngưỡng phiếu vẫn có thể bị bỏ sót.

OpenCV đạt 98,48 % nhưng tạo 8.195–9.086 vòng mỗi ảnh kiểm tra (7.112–8.984 trên tập điều chỉnh), so với 100 vòng của NumPy. Vì không đếm được dương tính giả, Recall cao này không nói gì về Precision, và nhãn hiện có không đủ để kết luận phương pháp nào chính xác hơn. Các số thời gian này cũng không dùng để xếp hạng tốc độ, vì hai bên đo phạm vi khác nhau. Lọc vòng trùng, đo riêng và không bật trong trò chơi, làm mất cặp ghép đúng duy nhất của `numpy_balanced` trên STT 13.

## 4.8. Khảo sát người chơi

Đề bài yêu cầu khảo sát ít nhất 10 học sinh về hứng thú và hiểu bài [@debai_nasa]. Ngày 31/10/2026, trưởng nhóm quyết định bỏ thử người chơi thật và khảo sát để ưu tiên hoàn thành dự án. Nhóm chưa thực hiện thử nhỏ S2-07 hay khảo sát S3-01; chưa có dữ liệu để kết luận sản phẩm làm tăng hứng thú hoặc hiểu bài. Đây là yêu cầu chưa đạt.

Thiết kế dự kiến được giữ trong `docs/S1-16_KHAO_SAT.md` và `docs/S2-07_THI_NGHIEM_VA_THU_GAME.md`: thử thao tác với 1–2 người; khảo sát 10–15 sinh viên chọn thuận tiện, mục tiêu ít nhất 10 phiếu hoàn chỉnh, với bốn câu hứng thú Likert 1–5, năm câu hiểu bài trước/sau và phản hồi mở. Khảo sát tự nguyện, ẩn danh. Đối tượng sinh viên khác học sinh mà đề bài yêu cầu; mẫu nhỏ, hỏi lại cùng câu và không có nhóm đối chứng nên chỉ dùng thống kê mô tả, không suy ra quan hệ nhân quả. Đây là kế hoạch chưa thực hiện.

## 4.9. Thảo luận và hạn chế

**Nhãn thưa.** Recall_known chỉ đo khả năng tìm lại 4–13 hố đã gán mỗi ảnh và không cho phép tính Precision. Trên STT 17, Recall_known bằng 0/10 trong khi nhãn mù ghi 17/100 vành hố thật; còn Recall_known gần 100 % của OpenCV đi kèm hàng nghìn vòng mỗi ảnh. Vì vậy Recall_known cần được đọc cùng số ứng viên và nhãn mù.

**Dữ liệu browse 8 bit.** Ảnh chưa hiệu chỉnh bức xạ, được chuẩn hóa riêng từng ảnh cắt, và hướng nắng chỉ có ở mức Đông/Tây. Dữ liệu phù hợp cho bài toán hình học, không cho kết luận định lượng.

**Tập kiểm tra không có thông tin nắng.** Tác động của bước sáng–tối chỉ đo được trên tập điều chỉnh, và kết quả kiểm tra chỉ đại diện cho mosaic 20 m/px.

**Trần 100 ứng viên.** Chế độ `numpy_balanced` đưa được vòng lớn hơn vào danh sách, nhưng Recall_known trên tập kiểm tra chỉ tăng từ 6,06 % lên 7,58 %. Giới hạn 100 vòng là một nguyên nhân bỏ sót, không phải nguyên nhân duy nhất.

**Mẫu nhỏ.** Bộ dữ liệu có 26 ảnh cắt từ 7 vùng mặt đất, và các ảnh cùng vùng không độc lập. Khảo sát chưa thực hiện, nên chưa có bằng chứng về hiệu quả giáo dục.
