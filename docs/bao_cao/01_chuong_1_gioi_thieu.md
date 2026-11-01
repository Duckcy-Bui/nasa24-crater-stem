<!--
Người chốt: Bùi Hải Đức (S3-08). Nguồn: docs/CHUONG_1_NHAP.md (S1-13), bảng giao việc, README.
Ngày 31/10/2026: ghi quyết định bỏ khảo sát; đối chiếu PR #26 và S2-15 trên main 13394de.
Việc còn lại: đối chiếu bản cuối S3-02, S3-05 và kết quả thống kê do người chốt cập nhật.
-->

# Chương 1. Giới thiệu

## 1.1. Bối cảnh và vấn đề

Đề tài xây dựng trò chơi dùng ảnh NASA để học sinh, nhất là ở vùng xa, tiếp cận STEM về không gian qua việc tìm hố va chạm và tìm hiểu thiết bị trên Mặt Trăng, Sao Hỏa [@debai_nasa].

Hố va chạm phổ biến trên Mặt Trăng [@nasa_moon], thường có vành gần tròn và cặp vùng sáng–tối tùy hướng nắng. Trong cùng điều kiện quan sát và dải đường kính, mật độ hố cao hơn thường gợi ý bề mặt già hơn về **tuổi tương đối**, không cho tuổi tuyệt đối [@neukum2001].

Máy đề xuất vị trí hố bằng Hough tròn [@duda1972; @yuen1990]. Học sinh tự khoanh rồi đối chiếu riêng với ứng viên máy và nhãn đã kiểm tra.

## 1.2. Yêu cầu của đề và mục tiêu của nhóm

Nhóm thực hiện Đề 24, "Phát hiện hố va chạm và trò chơi STEM cho học sinh", gắn với các thử thách NASA số 1, 3 và 11 [@debai_nasa]. Đề bài dùng ảnh LRO của Mặt Trăng, ảnh CTX/HiRISE của Sao Hỏa, ảnh khu vực hạ cánh Apollo và rover, cùng danh mục hố đã công bố để đối chiếu. Sản phẩm phải có bốn chức năng:

1. Tiền xử lý ảnh (tăng tương phản, làm trơn) và phát hiện hố bằng biến đổi Hough tròn **tự cài đặt**, kết hợp kiểm tra cặp vùng sáng–tối theo hướng nắng.
2. Đếm hố, vẽ phân bố kích thước và so sánh mật độ hố giữa hai vùng để giải thích "bề mặt nào già hơn".
3. Chế độ chơi: học sinh khoanh hố trên ảnh, hệ thống chấm điểm so với kết quả máy và danh mục.
4. Thẻ khoa học kể về thiết bị NASA đã để lại tại vùng ảnh (Apollo, rover), hiện ra khi học sinh tìm thấy.

Đề yêu cầu đánh giá bằng Precision và Recall so với danh mục, coi là trùng khi tâm lệch không quá 0,5 bán kính, và bằng khảo sát ít nhất 10 học sinh về mức hứng thú và mức hiểu bài. Đề còn gợi ý các hướng mở rộng: chọn điểm hạ cánh an toàn, quản lý tiền đồn theo thử thách số 3, bản tiếng Việt chạy ngoại tuyến.

Nhóm đặt mục tiêu cài Hough bằng NumPy và đối chiếu OpenCV; thống nhất tọa độ, định dạng vòng máy, nhãn và vòng người chơi; xây giao diện tiếng Việt để khoanh, sửa, lưu và chấm theo nhãn đã kiểm chéo. Phần đánh giá trải nghiệm người chơi chưa thực hiện (mục 1.5).

## 1.3. Phạm vi và giới hạn

**Thiên thể.** Bộ dữ liệu gồm 26 ảnh cắt 512 × 512 px từ 16 sản phẩm LROC chính thức: 15 ảnh mosaic 20 m/px và 11 ảnh Apollo 16 ở 2 m/px [@lroc_pds; @robinson2012; @martin2018]. Danh sách vùng ở mục 4.1; Sao Hỏa ngoài phạm vi báo cáo.

**Kích thước hố.** Ảnh 2 m/px xét đường kính 20–500 m, ảnh 20 m/px xét 200 m–4 km. Bán kính tương ứng là 5–125 và 5–100 px, trong giới hạn tìm kiếm [5, 128] px.

**Nhãn tham chiếu.** Danh mục Robbins chỉ đầy đủ cho hố từ khoảng 1–2 km [@robbins2019]. Nhóm gán nhãn tay **thưa**: 4–13 hố mỗi ảnh, tổng 241 nhãn, gồm 240 nhãn chắc chắn và 1 nhãn chưa chắc chắn (mục 4.3). Nhãn chỉ cho phép đo Recall trên nhãn đã biết, chưa đủ để đo Precision/F1 toàn ảnh (mục 2.4).

**Dữ liệu ảnh.** Bản *browse* 8 bit dùng để minh họa, không phải dữ liệu đo đạc khoa học định lượng [@lroc_rdrsis]. Bỏ sót hoặc khoanh nhầm hố làm lệch so sánh mật độ.

## 1.4. Cách tiếp cận tổng quát

Hình 1.1 tóm tắt luồng xử lý và các mục tương ứng.

```text
Ảnh LROC → cắt 512 × 512, metadata, mặt nạ    (4.1, 4.2)
  ▼
Tiền xử lý: thu nhỏ, ảnh xám, chuẩn hóa,
CLAHE, Gauss, Sobel, Canny, mặt nạ biên       (2.1, 3.2)
  ▼ ảnh biên, hướng gradient
Hough tròn NumPy tự viết: phiếu, đỉnh, NMS    (2.2, 3.3)
  ▼ ứng viên (x, y, r, số phiếu)
Kiểm tra sáng–tối, phân lớp, lọc trùng        (2.3–3.5)
  ▼ ứng viên máy
  ├─► Thống kê và mật độ hố                   (3.6)
  ├─► Trò chơi: khoanh, chấm với máy và nhãn  (5.2–5.4)
  └─► Thẻ khoa học theo vùng ảnh              (5.5)
```

::: {custom-style="Image Caption"}
Hình 1.1. Luồng xử lý của sản phẩm; số trong ngoặc là mục trình bày trong báo cáo.
:::

Các mô-đun dùng chung định dạng nhưng lưu riêng vòng máy, nhãn và vòng người chơi (mục 5.1). Tâm pixel có tọa độ nguyên; metadata cho phép đổi về ảnh nguồn (mục 4.2). Mỗi lần chạy lưu riêng tham số và mã phiên bản.

## 1.5. Kết quả chính

Bảng 1.1 tóm tắt mức đáp ứng yêu cầu của đề.

| Yêu cầu | Kết quả | Mục |
|---|---|---|
| Tiền xử lý và Hough tự cài đặt | Chạy trên 26 ảnh; có kiểm chứng. Sáng–tối chỉ gắn nhãn, phân lớp và lọc trùng chưa bật | 3.2–3.5 |
| Thống kê và so sánh mật độ | Đếm tay hai vùng; chưa khác biệt có ý nghĩa (p = 0,35) | 3.6, 5.7 |
| Trò chơi khoanh hố và chấm điểm | Giao diện tiếng Việt; điểm theo nhãn kiểm chéo, so máy chỉ báo mức trùng | 5.2–5.4 |
| Thẻ khoa học | Có nguồn cho 21/26 ảnh; mới theo vùng, chưa có ghim vị trí | 5.5 |
| Độ đo phát hiện | Recall trên nhãn đã biết, tập kiểm tra 8 ảnh, 66 nhãn: NumPy 6,06 % (`score`) và 7,58 % (cân bằng); OpenCV 98,48 % nhưng hơn 8.000 vòng mỗi ảnh | 4.7 |
| Khảo sát ít nhất 10 người chơi | Chưa thực hiện, chưa đạt yêu cầu. Trưởng nhóm bỏ thử và khảo sát ngày 31/10/2026 để ưu tiên hoàn thành dự án | 5.8 |

: Bảng 1.1. Mức độ hoàn thành các yêu cầu của đề.

Game giữ cách chọn `score` đã chốt. Hough chạm trần 100 ứng viên, phần lớn là vòng nhỏ, nên Recall còn thấp (mục 3.7, 4.7).

## 1.6. Tổ chức nhóm và kế hoạch

Bùi Hải Đức phụ trách khung mã, trò chơi, tích hợp và ghép báo cáo; Nguyễn Mạnh Tiến phụ trách Hough và kiểm chứng; Đinh Quang Hưng phụ trách tiền xử lý, sáng–tối và thống kê; Hoàng Quốc Anh phụ trách dữ liệu, nhãn, thẻ khoa học và thí nghiệm. Kế hoạch gồm ba sprint: xây bản đầu, tích hợp chức năng, rồi đánh giá và hoàn thiện. Phân công và quy trình ở Phụ lục A–B; phần thử người chơi và khảo sát đã bỏ theo quyết định nêu ở Bảng 1.1.

## 1.7. Cấu trúc báo cáo

Chương 2 đến 5 lần lượt trình bày lý thuyết, cài đặt, dữ liệu và đánh giá, hệ thống và kết luận.
