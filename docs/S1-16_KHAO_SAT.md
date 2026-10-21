# Khung khảo sát người chơi và lịch tiếp cận — S1-16

> **Bản nháp S1-16** (15/10/2026), chưa qua nhóm duyệt. **Lịch chưa chốt** nên S1-16 chưa đạt tiêu chí "lịch tiếp cận ít nhất 10 học sinh đã được thu xếp" (mục 3). Câu hỏi hiểu bài (mục 6) bám nội dung đã có trong repo; câu liên quan thẻ khoa học và phần nội dung game chưa cài phải được nhóm chốt lại khi game hoàn thiện (S2-07, S2-14).

## 1. Mục tiêu và yêu cầu

Theo đề và `Nghiem_thu` (hạng mục 6): khảo sát **ít nhất 10 học sinh**, dùng cùng hướng dẫn và cùng câu hỏi, **hỏi và tổng hợp riêng mức hứng thú và mức hiểu bài**; lưu kết quả và phản hồi để phân tích (S3-01, S3-09). Khảo sát đo hiệu quả trải nghiệm của sản phẩm, không đo độ chính xác của thuật toán.

## 2. Đối tượng

Dự kiến: sinh viên lớp cử nhân Công nghệ thông tin 2, Trường Đại học Giao thông Vận tải, khoảng 10–15 bạn.

Cần ghi rõ trong báo cáo (giới hạn mẫu): đây là **sinh viên đại học chuyên ngành CNTT**, khác với nhóm học sinh phổ thông ở vùng xa mà Chương 1 nêu làm đối tượng hướng tới; mẫu nhỏ, chọn thuận tiện; kết quả chỉ mô tả nhóm này, không khái quát cho học sinh. Việc đề cho phép dùng sinh viên thay "học sinh" cần được xác nhận với giảng viên hướng dẫn.

## 3. Lịch tiếp cận

Ràng buộc từ bảng giao việc (ngày 1 = 09/10/2026): S2-14 xác nhận lịch khảo sát (20–21/10); **S3-01 tổ chức khảo sát (23–24/10)**; S3-09 phân tích và viết Chương 4 (26–27/10); hạn cuối dự án 29/10/2026. Do đó khảo sát nên diễn ra trong **23–24/10/2026 (thứ Sáu–thứ Bảy)** hoặc sớm hơn; nếu trượt quá 24/10, thời gian phân tích bị ép.

| Hạng mục | Thông tin | Trạng thái |
|---|---|---|
| Đối tượng | Sinh viên lớp cử nhân CNTT 2, Trường Đại học GTVT | Đã nêu |
| Số người dự kiến | 10–15 (mục tiêu **≥ 10 người hoàn thành đủ phiếu**) | Đã nêu; cần dự phòng vì có thể có người vắng |
| Người liên hệ/tổ chức | Người nhận việc S1-16 (liên hệ lớp/giảng viên); hỗ trợ: Bùi Hải Đức | Đã nêu |
| Ngày giờ | `[chưa chốt]` | **Còn trống** |
| Địa điểm/phòng | `[chưa chốt]` | **Còn trống** |
| Giảng viên/đại diện lớp đồng ý | `[chưa có]` | **Còn trống** |
| Thiết bị | Máy tính cá nhân của người tổ chức hoặc máy của từng bạn | Cần chốt cách chạy (mục 3.1) |
| Bằng chứng xác nhận | Ảnh chụp tin nhắn/email xác nhận ngày giờ | `[chưa có]` |

**Điều kiện đánh dấu S1-16 là Hoàn thành:** các ô "Ngày giờ", "Địa điểm", "đồng ý" và "Bằng chứng xác nhận" đã điền và có minh chứng. Trước đó nên để trạng thái **Đang làm**.

### 3.1. Cách chạy trên máy (cần nhóm chốt, nhất là Bùi Hải Đức)

Giao diện chạy bằng Streamlit sau khi cài môi trường và giải nén bộ ảnh (README). Hai hướng, mỗi hướng có đánh đổi:

- **Một máy của người tổ chức, từng bạn chơi lần lượt.** Cài một lần; nhưng nếu mỗi lượt ≈ 20–25 phút (mục 4, thời lượng tạm) thì 10 bạn mất hơn 3 giờ.
- **Máy của từng bạn.** Chơi song song, nhanh hơn; nhưng mỗi máy phải cài Python 3.12 và repo (`requirements.txt`, `install_s106_dataset.py`). Cần kiểm tra trước trên ít nhất một máy lạ.

Số lượt chơi, thời lượng mỗi lượt và cách chạy chỉ chốt được sau thử nhỏ (S2-07).

## 4. Quy trình mỗi lượt (đề xuất, thời lượng tạm)

Mọi người nhận **cùng một hướng dẫn nói**, đọc đúng văn bản đã soạn trước (không giải thích thêm kiến thức ngoài văn bản, để không làm lệch mức hiểu bài).

| Bước | Nội dung | Thời lượng tạm |
|---|---|---|
| 1 | Giới thiệu mục đích, quyền tự nguyện, ẩn danh; cấp mã tham gia (SV01, SV02, …) | 3 phút |
| 2 | **Hiểu bài – trước** (5 câu, mục 6) | 3 phút |
| 3 | Chơi: khoanh hố trên ảnh được giao; lưu câu trả lời (`outputs/player_answers/`) | 10 phút |
| 4 | **Hứng thú** (mục 5.2) và **Hiểu bài – sau** (cùng 5 câu, đổi thứ tự lựa chọn) | 5 phút |
| 5 | Phản hồi mở (mục 5.3) | 2–3 phút |

## 5. Phiếu khảo sát

### 5.1. Thông tin chung (không ghi tên)

Mã tham gia; lớp; đã từng xem/chơi nội dung về hố va chạm hoặc Mặt Trăng chưa (Có/Không); mức quan tâm đến không gian trước khi chơi (1–5).

### 5.2. Mức hứng thú — thang 1–5

1 = hoàn toàn không đồng ý, 2 = không đồng ý, 3 = bình thường, 4 = đồng ý, 5 = hoàn toàn đồng ý.

| Mã | Phát biểu |
|---|---|
| H1 | Tôi thấy việc khoanh hố trên ảnh Mặt Trăng thú vị. |
| H2 | Tôi muốn chơi thêm với những ảnh khác. |
| H3 | Trải nghiệm này làm tôi tò mò hơn về Mặt Trăng và không gian. |
| H4 | Tôi sẵn lòng giới thiệu trò chơi này cho bạn bè. |

### 5.3. Phản hồi mở

1. Điều gì khiến bạn thấy khó khăn nhất khi khoanh hố? 2. Điều gì làm bạn thích nhất? 3. Bạn muốn thay đổi điều gì? (Phần này giúp sửa giao diện; không dùng để tính điểm hứng thú hay hiểu bài.)

## 6. Mức hiểu bài — 5 câu trắc nghiệm, một đáp án đúng

Cùng 5 câu trước và sau khi chơi. Hiểu bài = số câu đúng (0–5), so sánh trước/sau của từng người.

| Mã | Câu hỏi | Lựa chọn (đáp án đúng đánh dấu ✓) | Căn cứ trong repo | Trạng thái |
|---|---|---|---|---|
| U1 | Trên ảnh chụp từ quỹ đạo, một hố va chạm thường hiện ra như thế nào? | A. Một vành gần tròn, một phía sáng và phía đối diện tối tùy hướng nắng ✓<br>B. Một đường thẳng dài rất sáng<br>C. Một chấm sáng nhỏ, không có bóng<br>D. Một vùng phẳng đồng màu, không có vành | `CHUONG_1_NHAP.md` 1.1 | Cần nhóm xác nhận |
| U2 | Vì sao cùng một vùng, ảnh chụp lúc Mặt Trời thấp và lúc Mặt Trời gần đỉnh đầu trông khác nhau? | A. Hố thay đổi hình dạng giữa hai lần chụp<br>B. Mặt Trời thấp cho bóng dài và rõ; Mặt Trời gần đỉnh đầu gần như không tạo bóng ✓<br>C. Camera tự đổi màu theo mỗi lần chụp<br>D. Mặt Trăng quay quanh hố | `S1-06_HUONG_DAN_DU_LIEU.md` (cặp 81,08° và 7,64°); S1-04 mục 6 | Cần nhóm xác nhận |
| U3 | Hố là chỗ lõm. Phần thành hố nằm trong bóng thường ở phía nào so với Mặt Trời? | A. Phía gần Mặt Trời ✓<br>B. Phía xa Mặt Trời<br>C. Cả hai phía bằng nhau<br>D. Không phụ thuộc vào hướng Mặt Trời | `S1-04` mục 6 (thành hố gần Mặt Trời quay lưng với nắng nên tối) | **Nhờ Hưng (S1-11) xác nhận cách diễn đạt** |
| U4 | Vùng A có mật độ hố (số hố trên cùng diện tích, cùng thang đo, cùng khoảng kích thước) cao hơn vùng B. Kết luận hợp lý nhất? | A. A nhiều khả năng đã chịu va chạm lâu hơn B (tuổi tương đối già hơn) ✓<br>B. A đúng bằng một số triệu năm tuổi xác định<br>C. B chắc chắn không có hố<br>D. Không thể rút ra điều gì | `CHUONG_1_NHAP.md` 1.1 (chỉ là tuổi tương đối) | Cần nhóm xác nhận |
| U5 | Máy tự động đánh dấu 100 vòng tròn trên một ảnh. Điều nào đúng? | A. Chắc chắn có đúng 100 hố<br>B. Đó là các ứng viên cần kiểm tra, không phải số hố đã xác nhận ✓<br>C. Máy không thể sai<br>D. Số vòng càng nhiều càng chính xác | `S1-13` (cả 26 ảnh chạm trần 100 ứng viên, phần lớn là vòng nhỏ trên vệt tia và đá) | Cần nhóm xác nhận; có thể đổi khi bộ lọc S1-11 hoàn thiện |

**Chờ thẻ khoa học (S2-10):** khi thẻ Apollo/rover được cài, thêm 1–2 câu về thiết bị và địa điểm có trong thẻ; chỉ hỏi những gì thẻ thật sự nói và đã có nguồn. Chưa soạn vì thẻ chưa tồn tại.

Lưu ý thiết kế: dùng cùng 5 câu trước và sau nên người làm có thể nhớ câu; ghi vào giới hạn. Không có nhóm đối chứng (không chơi) nên mức tăng điểm không chứng minh game là nguyên nhân.

## 7. Kế hoạch phân tích

- Báo số người tham gia `n` và số người hoàn thành đủ phiếu.
- **Hứng thú:** trung bình ± độ lệch chuẩn từng câu H1–H4 và tổng; phân bố điểm từng câu.
- **Hiểu bài:** điểm trước và sau (0–5) của từng người; trung bình ± độ lệch chuẩn; số người tăng/không đổi/giảm; tỷ lệ đúng từng câu U1–U5.
- Với `n` ≈ 10–15, **không suy diễn ý nghĩa thống kê** và không kết luận vượt dữ liệu; trình bày số liệu mô tả, phản hồi mở và các trường hợp gặp khó.
- Lưu: file câu trả lời khoanh hố (JSON) và phiếu đã điền theo mã tham gia; nhóm tổng hợp ở S3-09.

## 8. Quyền riêng tư

Ẩn danh: chỉ dùng mã tham gia; không thu tên, mã sinh viên hay ảnh người tham gia; nói rõ tự nguyện, được dừng bất cứ lúc nào, dữ liệu chỉ dùng cho báo cáo môn học.

Nếu người tham gia là học sinh phổ thông (dưới 18 tuổi) thay vì sinh viên: cần sự đồng ý của nhà trường và thông báo/đồng ý của phụ huynh trước buổi khảo sát, có mẫu thông báo ngắn và lưu bằng chứng đồng ý (không lưu thông tin cá nhân của học sinh).

## 9. Việc còn mở

- [ ] Chốt ngày giờ, địa điểm; xin đồng ý của giảng viên/đại diện lớp; lưu ảnh chụp xác nhận.
- [ ] Xác nhận với giảng viên hướng dẫn: dùng sinh viên thay học sinh có chấp nhận được không.
- [ ] Chốt cách chạy trên máy (một máy luân phiên hay nhiều máy) cùng Bùi Hải Đức.
- [ ] Nhóm duyệt bộ 5 câu U1–U5 (đặc biệt U3 với Hưng); thêm câu về thẻ khoa học khi S2-10 xong.
- [ ] Thử nhỏ 1–2 người để chỉnh câu chữ và thời lượng (S2-07).
- [ ] Soạn văn bản hướng dẫn nói chung cho mọi lượt.
