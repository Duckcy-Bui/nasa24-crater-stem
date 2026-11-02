<!-- Đức chốt kết luận; Quốc Anh duyệt bản ghép S3-05. -->

# Chương 5. Kết luận và hướng phát triển

## 5.1. Đối chiếu mục tiêu

Bảng 5.1 đối chiếu các mã ở Bảng 1.1. Kiểm thử đạt xác nhận cài đặt theo thiết kế, không thay độ chính xác phát hiện hoặc hiệu quả giáo dục.

| Mục tiêu | Mức đạt | Kết quả có bằng chứng |
|---|---|---|
| M1 — Hai thiên thể | Đạt một phần | 26 ô từ 16 sản phẩm LROC; có Mặt Trăng, chưa có CTX/HiRISE Sao Hỏa |
| M2 — Hough tự viết, tiền xử lý/sáng–tối | Đạt | Chạy 26 ảnh; ví dụ 5×5 khớp NumPy; sai số tiền xử lý lớn nhất $3,58\cdot10^{-7}$; sáng–tối chỉ chấm 8/26 ảnh đủ điều kiện |
| M3 — Đếm và so hai vùng | Đạt một phần | Đếm tay 47 và 32 hố; 0,254 và 0,322 hố/km², p = 0,35: chưa kết luận vùng già hơn. Mật độ máy chưa dùng được |
| M4 — Khoanh, sửa, lưu, chấm | Đạt một phần | Có thao tác và đối chiếu máy/nhãn tay, chưa ghép danh mục. Bộ có 240 nhãn chắc chắn; minh họa 6/10 cho 60/100, trùng máy 0 |
| M5 — Thẻ khi tìm thấy thiết bị | Đạt một phần | Có thẻ theo vùng trên 21/26 ảnh; không có ghim vì thiết bị ngoài ô cắt, chưa có kích hoạt khi tìm thấy |
| M6 — Độ đo theo danh mục | Đạt một phần | Tỷ lệ tìm lại nhãn đã biết (Recall_known), tập kiểm tra (holdout): score 4/66 (6,06 %), balanced 5/66 (7,58 %); OpenCV 65/66, hơn 8.000 vòng/ảnh. Chưa đo độ chính xác dự đoán (Precision)/F1 toàn ảnh |
| M7 — Khảo sát ≥10 học sinh | Chưa đạt | Chưa có lượt thử/phiếu thật; bỏ khảo sát theo quyết định 31/10, chưa có số liệu hứng thú hay hiểu bài |

: Bảng 5.1. Mức đáp ứng các mục tiêu Chương 1.

S3-05 (Bảng 4.4) cho thấy gắn sáng–tối giữ 1/20, lọc ngược làm mất cặp đúng; đổi tham số vẫn 1/30. Bỏ kết cấu/lọc trùng giảm 300 còn 155/284 vòng nhưng giữ 1/30, chưa khắc phục bỏ sót hay chứng minh giảm dương tính giả (false positive — FP). [CHỜ Quốc Anh duyệt kết luận S3-05.] Tham số trò chơi chốt theo tập điều chỉnh (tuning) 10/174; holdout sau lần đầu là đánh giá lặp. Lệnh tái tạo ở Phụ lục A–B.

## 5.2. Hạn chế

Phạm vi **chỉ Mặt Trăng, chưa Sao Hỏa**; dùng nhãn thưa thay danh mục nên **chưa có Precision**. Thẻ theo vùng chưa đạt hành vi tìm thấy thiết bị; **khảo sát học sinh chưa đạt**. Nhóm có **4 thay vì 5 thành viên** theo quy định, chưa có căn cứ coi là ngoại lệ được duyệt; tỷ lệ và chữ ký còn chờ chính thành viên xác nhận.

Hough chạm trần 100 vòng, thiên về hố nhỏ; bộ lọc chưa bật vì có nguy cơ mất hố đúng. Ảnh xem nhanh (browse) 8 bit, góc nắng không đều và holdout toàn 20 m/px, thiếu hướng nắng, đã được xem trước giới hạn suy luận. Đếm tay hai vùng có ít hố, sai số r khoảng ±2 px; không suy tuổi tuyệt đối. Lượt chấm đầu còn chậm. Phép đo phụ về lượng tử 8 bit trong tài liệu bổ sung chưa có mã tái tạo riêng.

## 5.3. Ba hướng phát triển

1. **Giảm bỏ sót và đo đúng chất lượng:** Hough nhiều tầng phân giải, hạn ngạch ứng viên (quota) theo dải r; gán nhãn đầy đủ tập ảnh độc lập, đối chiếu Robbins ở hố ≥1–2 km, chọn ngưỡng/lọc trên tuning rồi đo Precision/F1.
2. **Bổ sung dữ liệu và thẻ có vị trí:** thêm ô chứa bãi đáp/xe tự hành và ảnh CTX/HiRISE; kiểm đổi tọa độ thiết bị sang pixel, chỉ mở thẻ khi người chơi chọn đúng vùng đã xác minh.
3. **Đánh giá giáo dục có dữ liệu thật:** thử thao tác 1–2 người, sau đó ít nhất 10 học sinh với bốn câu hứng thú 1–5, năm câu hiểu bài trước/sau và phản hồi mở. Báo riêng hai mặt; mẫu nhỏ, không nhóm đối chứng thì không kết luận nhân quả. Kiểm bản ngoại tuyến ở lớp học có mạng yếu.
