<!-- S3-12 r5: đối chiếu tài liệu học phần; Đức chốt, các chủ phần xác nhận nội dung của mình. -->

# Chương 1. Tổng quan bài toán

## 1.1. Bối cảnh và ý nghĩa

Một giờ học STEM ở trường vùng xa có thể cho học sinh tìm hố trên ảnh NASA, tự khoanh và giải thích vì sao máy bỏ sót hoặc khoanh nhầm. Đề tài dùng tình huống này để gắn xử lý ảnh với khoa học, công nghệ, kỹ thuật và toán học (Science, Technology, Engineering, Mathematics — STEM). Danh sách đề tài NASA, Đề 24 yêu cầu ảnh Mặt Trăng, Sao Hỏa và câu chuyện về thiết bị được để lại tại vùng ảnh [@debai_nasa].

Hố có vành gần tròn và cặp vùng sáng–tối tùy hướng nắng. Biến đổi Hough tròn (circular Hough transform) đề xuất vị trí hình học; học sinh khoanh độc lập rồi đối chiếu với máy và nhãn đã kiểm. Trong cùng điều kiện quan sát và dải đường kính, mật độ hố giúp bàn về tuổi tương đối (relative age), không cho tuổi tuyệt đối [@neukum2001].

## 1.2. Đầu vào, đầu ra và ràng buộc

**Đầu vào.** Ảnh LROC một kênh, bản xem nhanh (browse) TIFF 8 bit; sau cắt là mảng 512 × 512 phần tử số thực 32 bit (float32) trong [0, 1], PNG để hiển thị, mặt nạ hợp lệ và siêu dữ liệu (metadata) về nguồn, tỷ lệ, tọa độ, hướng nắng. Trò chơi nhận thêm vòng người chơi và nhãn tham chiếu. Ảnh 2 m/px xét hố 20–500 m; ảnh 20 m/px xét 200 m–4 km, tương ứng bán kính 5–125 và 5–100 px.

**Đầu ra.** Danh sách tâm, bán kính và số phiếu của ứng viên máy; nhãn sáng–tối; số đếm, phân bố kích thước, mật độ khi đủ điều kiện; điểm theo nhãn chắc chắn, ảnh đối chiếu, file lưu lượt chơi và thẻ khoa học có nguồn. Ứng viên máy, nhãn và vòng người chơi được lưu riêng.

**Ràng buộc.** Hough cốt lõi phải tự viết bằng NumPy; thư viện dùng đọc ảnh, cân bằng tương phản thích nghi có giới hạn (contrast limited adaptive histogram equalization — CLAHE), Canny và đối chiếu. Dải bán kính bị kẹp trong [5, 128] px; đầu ra tối đa 100 ứng viên/ảnh. Cài đặt giữ một mặt phẳng tích lũy int32 512 × 512 (1 MiB), thay vì khối 124 MiB cho 124 bán kính; bộ nhớ toàn chương trình còn gồm ảnh, đỉnh và lô phiếu. Giao diện giữ bộ nhớ đệm (cache) tối đa 8 ảnh. Đề không đặt trần thời gian/RAM bằng số; nhóm chưa cam kết xử lý thời gian thực. Lượt chấm đầu trên máy chủ từng mất 9,4 s; phép đo hiệu năng (benchmark) Hough theo máy và ảnh được báo ở Chương 4, không dùng làm cam kết tốc độ.

## 1.3. Yêu cầu và mục tiêu đo được

Bảng 1.1 diễn giải yêu cầu Đề 24 bằng các tiêu chí của nhóm [@debai_nasa]; không đặt thêm ngưỡng chất lượng tùy ý sau khi xem kết quả. Chương 5 trả lời từng mục tiêu theo cùng mã M1–M7.

| Mã | Mục tiêu và tiêu chí kiểm |
|---|---|
| M1 | Có dữ liệu của hai thiên thể: LRO/Mặt Trăng và CTX hoặc HiRISE/Sao Hỏa; ghi nguồn, tỷ lệ, nhãn và phạm vi sử dụng |
| M2 | Bằng mã NumPy của nhóm, định vị vòng tròn sau tăng tương phản và làm trơn; dùng hướng nắng kiểm cặp sáng–tối. Kiểm 26 ảnh, ví dụ tính tay và sai số so thư viện |
| M3 | Với hai miền ảnh cùng tỷ lệ và dải đường kính, lập bảng số hố, biểu đồ kích thước và đối chiếu mật độ; giải thích tuổi tương đối kèm bất định |
| M4 | Cho học sinh tự đánh dấu hố; phản hồi mức khớp với máy và danh mục tham chiếu, có thao tác sửa/lưu bài |
| M5 | Gắn chuyện Apollo/rover với vị trí thiết bị đã biết; người chơi nhận thẻ có nguồn sau khi xác định đúng vị trí ấy |
| M6 | Báo độ chính xác dương tính (Precision) và độ bao phủ (Recall) so với danh mục; ghép một–một với sai lệch tâm ≤0,5 bán kính nhãn |
| M7 | Khảo sát ít nhất 10 học sinh về hứng thú và hiểu bài |

: Bảng 1.1. Mục tiêu và tiêu chí đối chiếu Đề 24.

Các hướng chọn điểm hạ cánh, quản lý tiền đồn và bản tiếng Việt ngoại tuyến là gợi ý mở rộng của đề; không dùng chúng thay cho các tiêu chí bắt buộc chưa đạt.

## 1.4. Công trình liên quan và lựa chọn của nhóm

Ba công trình sau định hướng phương pháp; nhận xét về giới hạn khi áp dụng là phân tích của nhóm, không phải kết quả thực nghiệm của các tác giả trên bộ ảnh này.

- **Duda và Hart (1972)** [@duda1972] đưa phát hiện đường cong về tìm đỉnh trong không gian tham số. Ưu điểm là mô hình hình học rõ, dễ kiểm từng phiếu; hạn chế là phải lượng tử hóa và lưu/tính trên không gian tham số. Nhóm quét từng bán kính để giảm bộ nhớ.
- **Yuen và cộng sự (1990)** [@yuen1990] đối chiếu năm biến thể Hough tìm đường tròn, xét độ đúng, độ tin cậy, thời gian và bộ nhớ trên ảnh giả lập và ảnh luyện kim. Công trình cho cách nhìn các đánh đổi; kết quả không chuyển trực tiếp sang hố có bóng trên Mặt Trăng. Nhóm thử bỏ phiếu toàn vòng và theo hướng biến thiên độ sáng (gradient).
- **Robbins (2019)** [@robbins2019] cung cấp danh mục hố toàn Mặt Trăng, ước đầy đủ từ đường kính khoảng 1–2 km. Đây là nguồn đối chiếu cho hố lớn; không phủ đầy đủ hố 20–500 m của ảnh Apollo 16. Nhóm hiện dùng nhãn tay thưa và báo đúng giới hạn đó.

Hệ thống chọn giải pháp hình học có thể kiểm chứng bằng ma trận nhỏ, kèm bằng chứng sáng–tối và trò chơi. Không dùng kết quả Recall cao với hàng nghìn vòng để kết luận máy chính xác hơn khi chưa đo được dương tính giả.

## 1.5. Phạm vi thực hiện và phần không làm

Bộ hiện tại gồm **26 ảnh cắt từ 16 sản phẩm LROC**, 15 ảnh 20 m/px và 11 ảnh Apollo 16 ở 2 m/px. Tổng 241 nhãn gồm **240 nhãn chắc chắn và 1 nhãn chưa chắc chắn**. Đây là nhãn thưa (sparse labels): chỉ đo tỷ lệ tìm lại nhãn đã biết (Recall_known), chưa đo Precision/F1 toàn ảnh và chưa chiếu danh mục Robbins lên ảnh. Bản browse 8 bit phục vụ minh họa hình học, không phải phép đo quang học định lượng [@lroc_rdrsis].

Các lệch so với đề được giữ rõ: chỉ có Mặt Trăng, **chưa có Sao Hỏa**; chưa có Precision theo danh mục; thẻ phủ 21/26 ảnh theo vùng, **chưa hiện khi tìm thấy thiết bị** vì vị trí nằm ngoài ô cắt. Nhóm có **4 người thay vì 5** theo Quy định BTL Xử lý ảnh [@quydinh_btl]; phân công gộp vai trò ở Bảng M.1, chưa có căn cứ coi đây là ngoại lệ đã được giảng viên chấp thuận.

Ngày 31/10/2026, trưởng nhóm quyết định bỏ thử người chơi thật và khảo sát để ưu tiên hoàn thành dự án. Tiêu chí ít nhất 10 học sinh **chưa đạt**; nhóm không có số liệu về hứng thú hay hiểu bài. Ngoài ra, không xác định tuổi địa chất tuyệt đối, không tự nhận ứng viên máy là hố thật, chưa bật phân lớp/lọc trùng mặc định và chưa làm chế độ chọn bãi đáp hay quản lý tiền đồn.

## 1.6. Tổ chức báo cáo

Theo cấu trúc tài liệu học phần [@quydinh_btl], Chương 2 nêu lý thuyết và ví dụ số; Chương 3 trình bày thiết kế, giả mã, kiểm chứng và ứng dụng; Chương 4 báo dữ liệu, môi trường và đánh giá; Chương 5 đối chiếu mục tiêu và hướng phát triển. Mã kiểm ví dụ nằm ở Phụ lục B; hướng dẫn chạy, nhật ký tuần và khai báo AI ở các phụ lục còn lại. Phân công theo bốn thành viên nằm ở phần mở đầu, không điền tỷ lệ hoặc ký thay người thật.
