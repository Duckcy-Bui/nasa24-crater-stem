<!-- S3-12 r5: Đức chốt kết luận; Quốc Anh bổ sung kết quả S3-05 sau tích hợp PR #38. -->

# Chương 5. Kết luận và hướng phát triển

## 5.1. Đối chiếu mục tiêu

Bảng 5.1 đối chiếu đúng các mã ở Bảng 1.1. Test đạt xác nhận cài đặt theo thiết kế, không thay độ chính xác phát hiện hoặc hiệu quả giáo dục.

| Mục tiêu | Mức đạt | Kết quả có bằng chứng |
|---|---|---|
| M1 — Hai thiên thể | Đạt một phần | 26 ô từ 16 sản phẩm LROC; có Mặt Trăng, chưa có CTX/HiRISE Sao Hỏa |
| M2 — Hough tự viết, tiền xử lý/sáng–tối | Đạt | Chạy 26 ảnh; ví dụ 5×5 khớp NumPy; sai số tiền xử lý lớn nhất $3,58\cdot10^{-7}$; sáng–tối chỉ chấm 8/26 ảnh đủ điều kiện |
| M3 — Đếm và so hai vùng | Đạt một phần | Đếm tay 47 và 32 hố; 0,254 và 0,322 hố/km², p = 0,35: chưa kết luận vùng già hơn. Mật độ máy chưa dùng được |
| M4 — Khoanh, sửa, lưu, chấm | Đạt một phần | Có thao tác và đối chiếu máy/nhãn tay, chưa ghép danh mục. Bộ có 240 nhãn chắc chắn; minh họa 6/10 cho 60/100, trùng máy 0 |
| M5 — Thẻ khi tìm thấy thiết bị | Đạt một phần | Có thẻ theo vùng trên 21/26 ảnh; không có ghim vì thiết bị ngoài ô cắt, chưa có kích hoạt khi tìm thấy |
| M6 — Precision/Recall theo danh mục | Đạt một phần | Chỉ Recall_known từ nhãn tay: holdout score 4/66 (6,06 %), balanced 5/66 (7,58 %); OpenCV 65/66 nhưng hơn 8.000 vòng/ảnh. Chưa có Precision/F1 toàn ảnh |
| M7 — Khảo sát ≥10 học sinh | Chưa đạt | Chưa có lượt thử/phiếu thật; bỏ khảo sát theo quyết định 31/10, chưa có số liệu hứng thú hay hiểu bài |

: Bảng 5.1. Mức đáp ứng các mục tiêu Chương 1.

[CHỜ S3-05 — Quốc Anh: bổ sung kết luận ba thí nghiệm sau khi kết quả được tích hợp ở mục 4.6]. Tham số game đã chốt theo tuning 10/174; các lượt holdout sau lần đầu là đánh giá lặp. Lệnh tái tạo và phạm vi số đo ở Phụ lục A–B.

## 5.2. Hạn chế

Phạm vi **chỉ Mặt Trăng, chưa Sao Hỏa**; dùng nhãn thưa thay danh mục nên **chưa có Precision**. Thẻ theo vùng chưa đạt hành vi tìm thấy thiết bị; **khảo sát học sinh chưa đạt**. Nhóm có **4 thay vì 5 thành viên** theo quy định, chưa có căn cứ coi là ngoại lệ được duyệt; tỷ lệ và chữ ký còn chờ chính thành viên xác nhận.

Hough chạm trần 100 vòng, thiên về hố nhỏ; phân lớp/lọc trùng chưa bật vì có nguy cơ mất hố đúng. Browse 8 bit và góc nắng không đồng đều giới hạn suy luận; holdout toàn 20 m/px, thiếu hướng nắng, một phần đã được xem trước. Đếm tay hai vùng có ít hố và sai số r khoảng ±2 px; không suy tuổi tuyệt đối. Lượt chấm đầu còn chậm. Các phép đo phụ về lượng tử 8 bit trong tài liệu bổ sung chưa có script riêng.

## 5.3. Ba hướng phát triển

1. **Giảm bỏ sót và đo đúng chất lượng:** Hough nhiều tầng phân giải, quota theo dải r; bổ sung nhãn đầy đủ cho một tập ảnh độc lập, đối chiếu Robbins ở hố ≥1–2 km, rồi chọn ngưỡng/lọc trên tuning và đo Precision/F1.
2. **Bổ sung dữ liệu và thẻ có vị trí:** thêm ô chứa bãi đáp/rover và ảnh CTX/HiRISE; kiểm phép đổi tọa độ thiết bị sang pixel, chỉ mở thẻ khi người chơi chọn đúng vùng đã xác minh.
3. **Đánh giá giáo dục có dữ liệu thật:** thử thao tác 1–2 người, sau đó ít nhất 10 học sinh với bốn câu hứng thú 1–5, năm câu hiểu bài trước/sau và phản hồi mở. Báo riêng hai mặt; mẫu nhỏ, không nhóm đối chứng thì không kết luận nhân quả. Kiểm bản ngoại tuyến ở lớp học có mạng yếu.
