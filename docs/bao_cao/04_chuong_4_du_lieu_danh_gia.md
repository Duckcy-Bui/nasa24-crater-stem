<!--
Chương 4. Người chốt: Hoàng Quốc Anh (S3-09); Nguyễn Mạnh Tiến (S3-02) cho phần Precision/Recall (mục 4.5 và 4.7).
Bản ghép đầu tiên lấy từ: docs/S1-16_HO_SO_DU_LIEU.md, docs/S1-16_CHUONG_4_NHAP.md, docs/S1-16_KHAO_SAT.md, docs/S1-06_HUONG_DAN_DU_LIEU.md, docs/S1-06_BANG_ANH_XA_ANH_CAT.md, docs/DINH_DANG_DU_LIEU.md, docs/S1-10_HUONG_DAN_NHAN_HO.md, docs/S2-02_RA_SOAT_SANG_TOI.md, docs/S2-03_TAP_DIEU_CHINH.md, docs/S2-04_CHAM_DIEM.md, docs/S2-05_LOC_TRUNG.md, docs/S2-07_THI_NGHIEM_VA_THU_GAME.md, docs/evidence/s2-07/results.json; dữ liệu data/s106_bundle/, data/processed/*.json, data/reference_labels/*.json, data/s202_labels/, data/s203_split/manifest_split.json, data/s111_sun_checks.json; mã src/contracts.py, src/matching.py, src/hough.py, src/postprocessing.py, scripts/s207_experiments.py, scripts/verify_s116_coords.py (chạy lại ngày 27/10/2026: 26 ảnh, 0 lỗi).
Số nhãn ở mục 4.3 và 4.4 đếm trực tiếp từ 26 file data/reference_labels/*_craters_catalogue.json ngày 27/10/2026.
Hình phiếu nhãn mù (docs/evidence/s2-02/moon_ap16_m132732855l_c01/phieu_nhan.png) chưa đưa vào để giữ số trang; có thể thêm ở mục 4.3.2 nếu còn chỗ.

Cập nhật từ PR #26 (chưa merge, CI xanh; đọc qua git ref pr26 theo chỉ dẫn của người ghép, ngày 27/10/2026):
– Mục 4.7 lấy số liệu từ pr26:docs/S2-06_S3-02_KIEM_CHUNG.md, pr26:docs/evidence/s2-06-s3-02/holdout/results.csv và tuning_v2/results.csv. Bảng 4.5 chép nguyên bảng tóm tắt của tài liệu (chỉ đổi dấu thập phân sang dấu phẩy, đưa ký hiệu % lên tiêu đề cột và ghi TP_known/FN_known thành TP/FN có chú thích, để bảng không vỡ cột khi build_report.py tự chia độ rộng); Bảng 4.6 lấy TP/FN và số vòng OpenCV từ bảng từng ảnh; khoảng thời gian trung vị trong đoạn văn tính từ cột median_seconds của holdout/results.csv. Các số khớp hai file CSV.
– Mục 4.3.1 dựa trên pr26:docs/evidence/s2-06-s3-02/review_confirmation.json: reviewer Nguyen Manh Tien, date 2026-10-27, scope 26 overlay, status confirmed_by_user. File ghi rằng đây là lời xác nhận của người kiểm, không phải kiểm tra độc lập; bình luận trên PR #20 còn "pending". pr26:docs/S2-03_TAP_DIEU_CHINH.md chỉ thêm mục "Xác nhận của Tiến ngày 27/10/2026".
– Cấu hình đánh giá ở PR #26 là configs/s201_large_craters.json với hai chế độ score/balanced, cố định trước khi đánh giá; nó không phải cấu hình chọn qua E2 ở mục 4.6. Người chốt cần làm khớp mô tả E2 với cách chọn này.
– Sau khi PR #26 được merge: kiểm lại mọi số ở mục 4.7, rồi xóa hai dấu [CHỜ PR #26 ...].

Việc còn mở cho người chốt:
1. Đăng xác nhận kiểm chéo lên PR #20 (S2-07 mục 1 yêu cầu xác nhận này trước khi đưa Recall_known vào báo cáo chính thức).
2. S3-05 chạy ba thí nghiệm (mục 4.6); src/evaluation.py ở nhánh main hiện còn NotImplementedError, bản cài nằm trong PR #26.
3. Chốt mục tiêu định lượng của E2 ("giảm vòng/thời gian theo mục tiêu nêu trước", S2-07) trước khi chạy.
4. Nhóm chốt phương án tập kiểm tra (giữ split v3 hay thêm cụm Apollo 16 mới, S2-03 mục 2.4). Văn bản hiện mô tả split v3 và giới hạn của nó.
5. moon_marefrig_loc_c01 (tập kiểm tra) đã dùng trong thử nghiệm có kiểm soát của S2-02 mục 4 trước khi có split v3; manifest chỉ ghi STT 13. Xác nhận cách nêu ở mục 4.4.
6. Lần chạy kiểm tra ngày 26/10 (results.json, commit dc43eac) do bản script cũ tạo: thiếu các trường remove_inverted_experiment, shading_by_label_match, machine_radius_px, hit_max_circles. Chạy lại khi làm S3-05.
7. Khảo sát: chốt ngày giờ, địa điểm, đồng ý của giảng viên; xác nhận dùng sinh viên thay học sinh; S2-10 đã có thẻ khoa học nên cân nhắc thêm 1–2 câu hiểu bài về thẻ (S1-16_KHAO_SAT mục 6); thử nhỏ S2-07 chưa có lượt nào.
8. Sửa tài liệu nguồn lệch dữ liệu: S2-03 các bảng mục 3.1 và 7 còn ghi sparse_unreviewed; manifest_split.json ghi sun_quality "measured" cho 11 ảnh Apollo 16, trong khi metadata ghi side_only (8 ảnh) và none (3 ảnh); S1-16_HO_SO_DU_LIEU mục 1 và 7 còn ghi "4 nhãn chưa kiểm chéo"; data/reference_labels/README.md còn ghi "chưa kiểm chéo"; S1-10_HUONG_DAN_NHAN_HO mục 1 ghi STT 9 nắng "Đông" trong khi metadata ghi side_only phía Tây.
9. Chưa có ghi chép lý do không dùng ảnh nguồn STT 7; chưa đọc toàn văn Robbins (2019), Robinson et al. (2012), Martin et al. (2018); chưa tìm thấy điều khoản sử dụng riêng của LROC và danh mục Robbins (S1-16 mục 8).
10. Thống kê mật độ hai vùng (S3-03, Hưng) không có mục trong chương này; nhóm chốt đặt ở Chương 3 hay Chương 5.
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

Dữ liệu phục vụ ba kiểu so sánh. Vùng 1 gồm Apollo 15 khi Mặt Trời cao (1A) và thấp (1B), ở hai tọa độ khác nhau, nên chỉ là hai nhóm điều kiện chụp. Vùng 2 gồm Van de Graaff (2A, cao nguyên) và Mare Frigoris (2B, biển bazan), cùng 20 m/px và dải đường kính 200–4.000 m, để minh họa so sánh mật độ hố; mật độ hố chỉ gợi ý tuổi tương đối [@neukum2001]. Cặp STT 9 (góc tới 81,08°) và STT 17 (7,64°) có cùng cửa sổ (1190, 2750), dùng để minh họa ảnh hưởng của chiếu sáng. Các ảnh cắt cùng mosaic có thể chồng lấp, nên không phải mẫu độc lập.

## 4.2. Quy đổi tọa độ ảnh cắt và ảnh nguồn

Tâm và bán kính hố được lưu theo pixel ảnh cắt: $x$ là cột, $y$ là hàng, gốc ở góc trên-trái, tâm pixel có tọa độ nguyên. Gọi $s$ là tỷ lệ m/px của ảnh cắt. Công thức (4.1), cài trong hàm `source_coordinates` của `src/contracts.py`, đổi một vòng tròn sang ảnh nguồn:

$$ x_{\mathrm{src}} = x_0 + k\,x + \frac{k-1}{2}, \qquad y_{\mathrm{src}} = y_0 + k\,y + \frac{k-1}{2}, \qquad r_{\mathrm{src}} = k\,r \qquad (4.1) $$

Số hạng $(k-1)/2$ là độ lệch tâm khi thu nhỏ bằng trung bình khối; với $k = 1$ nó bằng 0. Ma trận affine $(a, b, c, d, e, f)$ của rasterio tính theo góc pixel, nên phải cộng 0,5 trước khi đổi sang tọa độ phẳng $(X, Y)$ tính bằng mét:

$$ \mathrm{col} = x_{\mathrm{src}} + \text{0,5}, \quad \mathrm{row} = y_{\mathrm{src}} + \text{0,5}, \quad X = a\,\mathrm{col} + b\,\mathrm{row} + c, \quad Y = d\,\mathrm{col} + e\,\mathrm{row} + f \qquad (4.2) $$

Với dữ liệu này $b = d = 0$, $a = s$, $e = -s$. Vĩ độ và kinh độ theo phép chiếu Equirectangular là

$$ \varphi = \frac{Y}{R}, \qquad \lambda = \lambda_0 + \frac{X}{R\cos\varphi_1} \qquad (4.3) $$

với bán kính Mặt Trăng $R$ = 1.737.400 m, góc tính bằng radian, $\lambda_0$ và $\varphi_1$ đọc từ CRS của ảnh nguồn. Đường kính và dải bán kính tìm kiếm được đổi theo công thức (4.4):

$$ D = 2\,r\,s, \qquad r_{\min} = \max\bigl(5,\ \lceil D_{\min}/(2s) \rceil\bigr), \qquad r_{\max} = \min\bigl(128,\ \lfloor D_{\max}/(2s) \rfloor\bigr) \qquad (4.4) $$

Dải 20–500 m ở 2 m/px cho $r \in [5, 125]$ px; dải 200–4.000 m ở 20 m/px cho $r \in [5, 100]$ px. Ví dụ, tâm (255,5; 255,5) của ảnh `moon_ap16_m106777343r_c01` ($x_0 = 170$, $y_0 = 6600$, $s = 2$ m/px) đổi thành (425,5; 6855,5) trong ảnh nguồn và (−9,0717548°; 15,4355671°), khớp tọa độ tâm trong metadata. Script `scripts/verify_s116_coords.py` lặp lại phép tính cho cả 26 ảnh: 26/26 ảnh khớp, chênh lệch lớn nhất cỡ $6 \cdot 10^{-14}$ độ.

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

Cả 26 file ghi nguồn `manual_label_s110; sparse manual labels, reviewed by Nguyen Manh Tien`. Theo xác nhận của người kiểm ngày 27/10/2026, Nguyễn Mạnh Tiến đã đối chiếu bằng mắt từng vòng trên đủ 26 ảnh overlay. Kiểm tra tự động cho thấy 26/26 file khớp với manifest, chỉ mục nhãn và ảnh overlay, nhưng kiểm tra này chỉ xác nhận định dạng, không xác nhận vị trí hố. [CHỜ PR #26 được merge]

### 4.3.2. Danh mục Robbins và nhãn mù

Danh mục hố của Robbins chỉ đầy đủ cho hố từ khoảng 1–2 km trở lên [@robbins2019]. Dải 20–500 m của ảnh 2 m/px nằm hoàn toàn dưới ngưỡng này; với ảnh 20 m/px, chỉ phần trên của dải 200–4.000 m nằm trong phạm vi đầy đủ. Nhóm chưa chiếu danh mục lên ảnh 20 m/px, vì việc đó cần quy đổi ngược theo mục 4.2, đối chiếu bằng mắt từng hố và chỉ cho một tập con hố lớn. Mọi nhãn tham chiếu hiện có đều là nhãn tay.

Bước rà biên ở Chương 3 dùng thêm nhãn mù gán trực tiếp cho ứng viên máy. Trên STT 13 (`moon_ap16_m132732855l_c01`, góc tới 87,7°), 100 ứng viên của cấu hình mặc định được đưa lên một phiếu không hiện lớp do máy xếp. Kết quả: 8 vành hố thật, 7 ranh giới bóng, 79 biên kết cấu, 6 không chắc (Đinh Quang Hưng gán, Hoàng Quốc Anh kiểm chéo, 23/10/2026). Trên STT 17, kết quả là 17 vành hố thật, 66 biên kết cấu và 17 không chắc (25/10/2026). Nhãn mù không chứa các hố máy bỏ sót, nên không dùng để tính Recall_known.

## 4.4. Tập điều chỉnh và tập kiểm tra

Tập điều chỉnh dùng để chọn tham số; tập kiểm tra chỉ dùng để báo cáo kết quả cuối. Cách chia hiện hành (phiên bản 3, `data/s203_split/manifest_split.json`) theo quy tắc: các ảnh cắt chồng lấp nhau, hoặc cùng mặt đất chụp dưới điều kiện nắng khác nhau, phải nằm cùng một tập. Vì vậy cả 11 ảnh Apollo 16 thuộc tập điều chỉnh. Các ảnh này thuộc cùng chuỗi ảnh quanh bãi đáp Apollo 16, tâm cách nhau từ 0 đến 8,06 km, trong khi mỗi ảnh cắt rộng 1.024 m: 24 trong 55 cặp chồng lấp mặt đất, với khoảng cách tâm 340–680 m tương ứng mức chồng lấp 33–67 %. Bốn ảnh STT 9, 11, 17 và 18 còn dùng chung cửa sổ (1190, 2750), và STT 13 đã được dùng để chọn cách lọc ở bước rà biên. Tập kiểm tra gồm ba vùng độc lập: Apollo 15 khi Mặt Trời thấp (cách tập điều chỉnh 50,1–62,8 km), Lunokhod 2 (721,4–726,9 km) và Mare Frigoris (1.095–1.106 km).

Tập điều chỉnh gồm 18 ảnh cắt từ bốn vùng: 11 ảnh Apollo 16 ở 2 m/px, cùng Apollo 15 khi Mặt Trời cao, Van de Graaff và Lunokhod 1 ở 20 m/px; có 174 nhãn được tính. Tập kiểm tra gồm 8 ảnh cắt 20 m/px từ ba vùng, với 66 nhãn được tính (Bảng 4.2). Chỉ 8 ảnh Apollo 16 của tập điều chỉnh thỏa điều kiện của bước sáng–tối (Chương 3): có phía nắng đã biết và góc tới từ 30° trở lên. STT 10 (28,38°) và hai ảnh cắt của STT 17 (7,64°) bị loại vì nắng gần đứng.

Cách chia có hai giới hạn. Thứ nhất, cả 8 ảnh kiểm tra đều là mosaic 20 m/px với `sun.quality = none`, nên bước sáng–tối luôn ghi `not_checked` và thí nghiệm E1 không có phép đo ngoài mẫu. Thứ hai, tập kiểm tra không có ảnh 2 m/px, nên kết quả trên Apollo 16 chỉ là kết quả chẩn đoán và được báo riêng. Khắc phục cần một cụm ảnh Apollo 16 mới, không chồng lấp với tập điều chỉnh; bộ dữ liệu hiện chưa có. Ngoài ra, hai vùng so sánh 2A và 2B nằm ở hai tập khác nhau, nên khi so mật độ cần nêu sai số phát hiện của từng vùng. Ảnh `moon_marefrig_loc_c01` của tập kiểm tra đã được dùng làm ảnh đối chứng trong thử nghiệm tiền xử lý trước khi chốt cách chia; thử nghiệm đó giữ nguyên tham số mặc định, nhưng đây vẫn là điểm cần lưu ý.

## 4.5. Phương pháp đánh giá

**Quy tắc ghép.** Theo mục 2.4, một ứng viên máy khớp một nhãn khi khoảng cách hai tâm không vượt quá 0,5 $r_{\mathrm{ref}}$; mỗi ứng viên và mỗi nhãn chỉ dùng một lần. Cách ghép có nhiều cặp nhất, rồi có tổng khoảng cách chuẩn hóa nhỏ nhất, được tìm bằng thuật toán Hungary [@kuhn1955], tự viết bằng NumPy trong `src/matching.py`. Ngưỡng 0,5 dùng chung cho đánh giá máy và chấm điểm người chơi.

**Máy không phải đáp án.** Đánh giá phát hiện chỉ so ứng viên máy với nhãn tham chiếu. Khi trò chơi so người chơi với máy, kết quả chỉ là mức trùng và không cho điểm (Chương 5).

**Nhãn thưa.** Một ứng viên không khớp nhãn nào vẫn có thể là hố thật chưa được gán, nên nhóm không đếm dương tính giả và không tính Precision hay F1. Độ đo chính là Recall trên nhãn đã biết (Recall_known, mục 2.4). Nhãn chưa chắc chắn thuộc tập bỏ qua. Precision và F1 chỉ được tính khi file nhãn được đánh dấu đầy đủ (`catalogue_coverage = "complete"`); hiện chưa file nào như vậy. Mỗi giá trị Recall_known đi kèm số nhãn, số ứng viên và trạng thái chạm trần 100 vòng.

**Chạy tập kiểm tra.** Tham số chỉ được chọn trên tập điều chỉnh; tập kiểm tra chạy một lần với cấu hình đã đóng băng. Lần đánh giá ở mục 4.7 đã dùng tập kiểm tra một lần cho hai chế độ chọn ứng viên được cố định từ trước, khi bộ tham số chính thức chưa được chốt [CHỜ S2-15]; mọi lần chạy lại trên tập kiểm tra sau đó phải được ghi rõ trong báo cáo. Script `scripts/s207_experiments.py` từ chối ảnh kiểm tra nếu thiếu cờ `--holdout`, cờ này bắt buộc kèm `--chosen-config` (file tham số đã chốt), và ở chế độ đó script chỉ chạy đúng cấu hình đã chốt, không quét biến thể.

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

[CHỜ PR #26 được merge: kiểm lại số liệu]

## 4.8. Khảo sát người chơi

### 4.8.1. Mục tiêu, người tham gia và quy trình

Đề bài yêu cầu khảo sát ít nhất 10 học sinh về mức hứng thú và mức hiểu bài [@debai_nasa]. Nhóm đo hai mặt này riêng biệt, với cùng hướng dẫn và cùng câu hỏi cho mọi người; khảo sát đánh giá trải nghiệm sản phẩm, không đo độ chính xác thuật toán. Người tham gia dự kiến là 10–15 sinh viên một lớp cử nhân Công nghệ thông tin, chọn thuận tiện, với mục tiêu ít nhất 10 người hoàn thành đủ phiếu. Đối tượng này khác với học sinh phổ thông vùng xa mà sản phẩm hướng tới (Chương 1), nên kết quả chỉ mô tả nhóm tham gia. Nếu người tham gia là học sinh dưới 18 tuổi, cần sự đồng ý của nhà trường và phụ huynh.

Mỗi lượt gồm năm bước với thời lượng tạm tính: giới thiệu và cấp mã tham gia (3 phút); 5 câu hiểu bài lần trước (3 phút); chơi khoanh hố và lưu câu trả lời (10 phút); 4 câu hứng thú và 5 câu hiểu bài lần sau, đổi thứ tự lựa chọn (5 phút); phản hồi mở (2–3 phút). Mọi người nghe cùng một hướng dẫn được đọc nguyên văn. Khảo sát ẩn danh: nhóm chỉ dùng mã tham gia, không thu tên, mã sinh viên hay ảnh; người tham gia được biết việc tham gia là tự nguyện, có thể dừng bất cứ lúc nào, và dữ liệu chỉ dùng cho báo cáo học phần.

### 4.8.2. Phiếu khảo sát

Phiếu có bốn phần: thông tin chung không ghi tên (lớp, đã từng xem nội dung về Mặt Trăng chưa, mức quan tâm đến không gian 1–5); bốn phát biểu hứng thú theo thang Likert 1–5; năm câu hiểu bài trắc nghiệm, điểm là số câu đúng (0–5); và ba câu phản hồi mở chỉ dùng để sửa giao diện (Bảng 4.7).

| Mã | Nội dung | Thang hoặc đáp án đúng |
|:---:|:---------------------------------------------------|:-----------------------------|
| H1 | Tôi thấy việc khoanh hố trên ảnh Mặt Trăng thú vị. | 1–5 |
| H2 | Tôi muốn chơi thêm với những ảnh khác. | 1–5 |
| H3 | Trải nghiệm này làm tôi tò mò hơn về Mặt Trăng và không gian. | 1–5 |
| H4 | Tôi sẵn lòng giới thiệu trò chơi này cho bạn bè. | 1–5 |
| U1 | Hố va chạm thường hiện ra thế nào trên ảnh chụp từ quỹ đạo? | Vành gần tròn, một phía sáng, phía kia tối tùy hướng nắng |
| U2 | Vì sao cùng một vùng trông khác nhau khi Mặt Trời thấp và gần đỉnh đầu? | Mặt Trời thấp cho bóng dài; gần đỉnh đầu gần như không có bóng |
| U3 | Phần thành hố nằm trong bóng thường ở phía nào so với Mặt Trời? | Phía gần Mặt Trời |
| U4 | Vùng A có mật độ hố cao hơn vùng B. Kết luận hợp lý nhất? | A nhiều khả năng già hơn B về tuổi tương đối |
| U5 | Máy đánh dấu 100 vòng trên một ảnh. Điều nào đúng? | Đó là ứng viên cần kiểm tra, không phải số hố đã xác nhận |

: Bảng 4.7. Câu hỏi hứng thú (thang Likert 1–5) và câu hỏi hiểu bài.

### 4.8.3. Thử nhỏ và kế hoạch phân tích

Trước khảo sát, nhóm thiết kế một lượt thử với 1–2 người (mã P01, P02) trên ảnh `moon_ap16_m106777343r_c01` để sửa thao tác và câu chữ, không để đo hiệu quả. Người điều phối đọc nguyên văn kịch bản, nói rõ vòng của máy chỉ là ứng viên, không phải đáp án. Phiếu thử ghi thiết bị, thời lượng, việc lưu JSON và hiện điểm, cùng các lỗi gặp phải; sau lượt chơi, người thử trả lời bốn câu ngắn về thao tác, về cách hiểu vòng máy, về việc điểm có gây hiểu nhầm rằng vòng ngoài nhãn là sai, và về thời gian chờ.

[CHỜ S2-07: kết quả thử nhỏ 1–2 người và danh sách lỗi đã xác nhận]

Nhóm sẽ báo số người tham gia và số người hoàn thành đủ phiếu; trung bình, độ lệch chuẩn và phân bố điểm của từng câu hứng thú và của tổng; điểm hiểu bài trước và sau của từng người, số người tăng, không đổi, giảm điểm và tỷ lệ đúng từng câu. Với 10–15 người, nhóm chỉ trình bày số liệu mô tả. Cùng năm câu được hỏi hai lần và không có nhóm đối chứng, nên mức tăng điểm không chứng minh trò chơi là nguyên nhân.

[CHỜ S3-01: kết quả khảo sát (số người tham gia, thời gian và địa điểm, điểm hứng thú H1–H4, điểm hiểu bài trước và sau, phản hồi mở)]

## 4.9. Thảo luận và hạn chế

**Nhãn thưa.** Recall_known chỉ đo khả năng tìm lại 4–13 hố đã gán mỗi ảnh và không cho phép tính Precision. Trên STT 17, Recall_known bằng 0/10 trong khi nhãn mù ghi 17/100 vành hố thật; còn Recall_known gần 100 % của OpenCV đi kèm hàng nghìn vòng mỗi ảnh. Vì vậy Recall_known cần được đọc cùng số ứng viên và nhãn mù.

**Dữ liệu browse 8 bit.** Ảnh chưa hiệu chỉnh bức xạ, được chuẩn hóa riêng từng ảnh cắt, và hướng nắng chỉ có ở mức Đông/Tây. Dữ liệu phù hợp cho bài toán hình học, không cho kết luận định lượng.

**Tập kiểm tra không có thông tin nắng.** Tác động của bước sáng–tối chỉ đo được trên tập điều chỉnh, và kết quả kiểm tra chỉ đại diện cho mosaic 20 m/px.

**Trần 100 ứng viên.** Chế độ `numpy_balanced` đưa được vòng lớn hơn vào danh sách, nhưng Recall_known trên tập kiểm tra chỉ tăng từ 6,06 % lên 7,58 %. Giới hạn 100 vòng là một nguyên nhân bỏ sót, không phải nguyên nhân duy nhất.

**Mẫu nhỏ.** Bộ dữ liệu có 26 ảnh cắt từ 7 vùng mặt đất, và các ảnh cùng vùng không độc lập. Khảo sát dự kiến 10–15 sinh viên chọn thuận tiện, nên kết quả chỉ mang tính mô tả.
