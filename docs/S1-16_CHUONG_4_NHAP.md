# Chương 4 — Khung và nháp mục Dữ liệu (S1-16)

> **Bản nháp S1-16** (15/10/2026), chưa qua nhóm duyệt. Khung theo bảng giao việc: Chương 4 gồm **dữ liệu, Precision/Recall, ba thí nghiệm, khảo sát** (S2-14, S3-09); báo cáo 5 chương. Mục 1.8 của [CHUONG_1_NHAP.md](CHUONG_1_NHAP.md) đã được sửa theo cùng cấu trúc 5 chương này.

## Khung Chương 4

| Mục | Nội dung | Người/việc | Trạng thái |
|---|---|---|---|
| 4.1 | Dữ liệu: nguồn, cắt ảnh, metadata, quy đổi tọa độ, nhãn tham chiếu | Hoàng Quốc Anh, S1-16 | **Nháp bên dưới** |
| 4.2 | Phương pháp đánh giá: đối sánh một–một, tâm lệch ≤ 0,5 bán kính tham chiếu, Precision/Recall, tập điều chỉnh và tập kiểm tra | S2-03, S2-14 | Có giới hạn split cần giữ lại bên dưới |
| 4.3 | Ba thí nghiệm: (1) Hough cơ bản so với thêm sáng–tối; (2) ảnh hưởng tham số; (3) ảnh khó (bóng mạnh, hố chồng nhau) | S2-07, S3-05 | Thí nghiệm 1 chưa có số holdout S1-11 |
| 4.4 | Khảo sát người chơi: đối tượng, quy trình, phiếu, kết quả hứng thú và hiểu bài | S1-16 (khung), S3-01, S3-09 | Khung tại [S1-16_KHAO_SAT.md](S1-16_KHAO_SAT.md) |
| 4.5 | Thống kê hố và so sánh mật độ hai vùng | Đinh Quang Hưng, S3-03 | Chưa viết (vị trí do nhóm chốt) |
| 4.6 | Thảo luận và hạn chế | S3-09 | Chưa viết |

---

## 4.1. Dữ liệu

### 4.1.1. Nguồn ảnh

Nhóm dùng ảnh Mặt Trăng do camera góc hẹp NAC của tàu LRO chụp, phát hành bởi LROC (NASA/GSFC/Arizona State University) trên Kho dữ liệu PDS [1]. Bộ dữ liệu `s106_lroc_browse_v2` gồm **26 ảnh cắt kích thước 512 × 512 pixel**, lấy từ **16 ảnh nguồn** dạng browse (TIFF 8 bit): sáu mosaic NAC ở 20 m/px quanh Apollo 15 (hai điều kiện high-Sun và low-Sun), miệng hố Van de Graaff, Lunokhod 1, Lunokhod 2 và Mare Frigoris [2], cùng mười ảnh NAC đơn lẻ ở 2 m/px của chuỗi Apollo 16 chụp dưới các góc tới từ 7,64° đến 87,78° [3]. Bảng 4.1 tóm tắt; số byte và mã băm SHA-256 của từng file nguồn được lưu để kiểm tra và tải lại.

**Bảng 4.1.** Nguồn ảnh và số ảnh cắt.

| STT | Vùng | Tỷ lệ | Số ảnh nguồn | Số ảnh cắt |
|---:|---|---:|---:|---:|
| 1 | Apollo 15, high-Sun | 20 m/px | 1 | 3 |
| 2 | Apollo 15, low-Sun | 20 m/px | 1 | 3 |
| 3 | Van de Graaff, high-Sun | 20 m/px | 1 | 2 |
| 4 | Lunokhod 1, low-Sun | 20 m/px | 1 | 2 |
| 5 | Lunokhod 2, low-Sun | 20 m/px | 1 | 2 |
| 6 | Mare Frigoris, low-Sun | 20 m/px | 1 | 3 |
| 8–11, 13–18 | Apollo 16, chuỗi E090S0155 | 2 m/px | 10 | 11 |
| | **Tổng** | | **16** | **26** |

Ảnh browse chỉ phục vụ quan sát; theo đặc tả sản phẩm LROC, loại ảnh này không dùng cho đo đạc định lượng [4]. Vì vậy dữ liệu của đề tài dùng để minh họa xử lý hình học ảnh, không để rút ra số đo quang học hay trắc địa.

### 4.1.2. Cách cắt và chuẩn hóa

Từ mỗi ảnh nguồn, nhóm cắt một hoặc vài cửa sổ vuông 512 × 512 pixel (26 cửa sổ từ 16 ảnh nguồn) nằm hoàn toàn trong vùng có ảnh, tránh khoảng trống và đường ghép mosaic. Không thu nhỏ ảnh (hệ số thu nhỏ bằng 1). Mặt nạ hợp lệ được lấy từ mặt nạ raster của nguồn và kiểm tra giá trị hữu hạn; pixel bằng 0 không bị coi là thiếu dữ liệu. Giá trị pixel được chuẩn hóa về đoạn [0, 1] bằng phân vị 0,5 % và 99,5 % của các pixel hợp lệ để mọi tham số xử lý phía sau có cùng ý nghĩa trên mọi ảnh. Toàn bộ quá trình được tái tạo bằng một script cố định, và mã băm của script, của cấu hình cửa sổ và của từng file nguồn được ghi vào metadata để truy vết `[Hình 4.1: sơ đồ nguồn → cắt → chuẩn hóa → metadata]`.

### 4.1.3. Metadata và quy đổi tọa độ

Mỗi ảnh có một file metadata ghi mã nguồn, vị trí cửa sổ cắt `(x₀, y₀)`, tỷ lệ `s` (m/px), tọa độ tâm, hướng Bắc, thông tin chiếu sáng và dải bán kính tìm kiếm. Tâm và bán kính hố luôn tính theo pixel của ảnh 512 × 512, với `x` là cột tăng sang phải, `y` là hàng tăng xuống dưới, gốc ở góc trên-trái và tâm pixel có tọa độ nguyên.

Từ tọa độ ảnh cắt `(x, y)` sang ảnh nguồn:

$$x_{src} = x_0 + kx + \frac{k-1}{2},\qquad y_{src} = y_0 + ky + \frac{k-1}{2},\qquad r_{src} = kr, \tag{4.1}$$

trong đó `k` là hệ số thu nhỏ (`k = 1` với bộ ảnh hiện tại). Đường kính tính theo mét là `D = 2rs`, và dải tìm kiếm được đổi từ dải đường kính `[D_min, D_max]` theo

$$r_{min} = \max\!\left(5,\ \left\lceil \frac{D_{min}}{2s} \right\rceil\right),\qquad r_{max} = \min\!\left(128,\ \left\lfloor \frac{D_{max}}{2s} \right\rfloor\right). \tag{4.2}$$

Để đổi sang kinh/vĩ độ, ma trận affine của ảnh nguồn (tính theo góc pixel) được áp lên cặp (x_src + 0,5; y_src + 0,5), sau đó dùng phép chiếu Equirectangular trên mặt cầu Mặt Trăng bán kính 1.737.400 m. Nhóm kiểm tra phép đổi này trên cả 26 ảnh bằng cách đổi tâm ảnh cắt rồi so với tọa độ tâm đã lưu: cả 26 ảnh khớp ở mức sai số làm tròn số thực `[Bảng 4.2: kết quả kiểm tra, lấy từ scripts/verify_s116_coords.py]`.

### 4.1.4. Chiếu sáng và các cặp so sánh

Hướng nắng chỉ có ở mức thô: với một số ảnh Apollo 16, trang sản phẩm cho biết nắng từ phía Tây; phía Đông của ba ảnh còn lại chỉ được suy từ quy ước dấu và chưa xác minh; mosaic chỉ có dải góc tới của các ảnh thành phần. Nhóm vì vậy ghi mức tin cậy (`measured`, `side_only`, `none`) thay vì suy đoán, S1-11 ([S1-11_SANG_TOI.md](S1-11_SANG_TOI.md)) bỏ qua kiểm tra sáng–tối khi góc tới nhỏ hơn 30° hoặc thiếu căn cứ về hướng nắng; ngưỡng 30° là giá trị ban đầu theo đề xuất của S1-04, chưa chỉnh trên tập điều chỉnh.

Dữ liệu cho ba kiểu so sánh: (i) hai ảnh Apollo 16 cùng cửa sổ, góc tới 81,08° và 7,64°, dùng để minh họa ảnh hưởng của chiếu sáng; (ii) Van de Graaff (cao nguyên) và Mare Frigoris (mare) cùng 20 m/px, dải D 200–4000 m, dùng để minh họa so sánh mật độ hố; (iii) hai nhóm ảnh Apollo 15 high-Sun và low-Sun ở các tọa độ khác nhau, chỉ là hai nhóm điều kiện, không phải thí nghiệm cùng vùng chỉ đổi góc nắng. Các cửa sổ cùng mosaic có thể chồng lấp, nên không coi là mẫu độc lập và không cộng diện tích.

### 4.1.5. Nhãn tham chiếu và giới hạn

Danh mục hố toàn cầu của Robbins [5] đầy đủ cho hố lớn hơn khoảng 1–2 km, trong khi ảnh 2 m/px của nhóm chủ yếu chứa hố có đường kính 20–500 m, nên danh mục này không bao phủ phần lớn hố cần đánh giá. Nhóm đã có file nhãn thủ công thưa cho 26/26 crops; theo xác nhận cập nhật ngày 26/10/2026, chúng đã được Nguyễn Mạnh Tiến kiểm chéo và ghi nguồn `reviewed by Nguyen Manh Tien`. Vì nhãn vẫn thưa nên không tính Precision/F1 trên các nhãn này; chỉ báo Recall trên tập hố đã gán nhãn, kèm số hố và phạm vi; các hố chưa chắc chắn được tách thành tập bỏ qua. Thiếu nhãn không có nghĩa vùng ảnh không có hố.

### 4.2. Giới hạn của tập kiểm tra hiện tại

Split S2-03 giữ toàn bộ 11 crops Apollo 16 2 m/px trong tuning vì chúng chồng lấp mặt đất và một crop đã được dùng chọn lọc ở S2-02. Do đó toàn bộ 8 crops holdout là mosaic 20 m/px và `sun.quality = none`. Hệ quả là S1-11 không thể được đo trên holdout: mọi ứng viên đều `not_checked`; thí nghiệm “Hough cơ bản so với thêm sáng–tối” không có kết quả ngoài mẫu để kết luận tác động của bước này. Holdout cũng không đánh giá độc lập cho Apollo 16 2 m/px, dù nhãn và các khảo sát S2-02/S2-05 có dùng ảnh này.

Khi báo cáo, kết quả Apollo 16 tuning chỉ được trình bày là phát triển/chẩn đoán; kết quả holdout chỉ áp dụng cho mosaic 20 m/px. Nhóm cần chốt một trong hai phương án: giữ split này và nêu rõ giới hạn, hoặc bổ sung một cụm Apollo 16 2 m/px mới, không chồng lấp và chưa dùng để chọn tham số, làm holdout riêng.

## Tài liệu tham khảo của chương

[1] NASA/GSFC/Arizona State University, "Lunar Reconnaissance Orbiter Camera (LROC) Planetary Data System archive," https://pds.lroc.im-ldi.com/ (truy cập 14/10/2026).
[2] M. S. Robinson, E. J. Speyerer, A. Boyd, D. Waller, R. V. Wagner and K. N. Burns, "Exploring the Moon with the Lunar Reconnaissance Orbiter Camera," *Int. Arch. Photogramm. Remote Sens. Spat. Inf. Sci.*, vol. 39, part B4, 2012, doi:10.5194/isprsarchives-XXXIX-B4-501-2012.
[3] A. C. Martin, A. K. Boyd, M. S. Robinson and the LROC Team, "Controlling LROC NAC Photometric Images," *Lunar and Planetary Science Conference 49*, abstract #1621, 2018.
[4] LROC RDR Software Interface Specification, mục 3.2, https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DOCUMENT/RDRSIS.PDF.
[5] S. J. Robbins, "A new global database of lunar impact craters >1–2 km: 1. Crater locations and sizes, comparisons with published databases, and global analysis," *J. Geophys. Res. Planets*, vol. 124, no. 4, pp. 871–892, 2019, doi:10.1029/2018JE005592.

> Trước khi nộp: đọc toàn văn [2], [3], [5] để ghi đúng tập/trang (S1-02 chỉ ghi theo yêu cầu trích dẫn của trang sản phẩm); số thứ tự trích dẫn sẽ đổi khi ghép vào báo cáo cuối.
