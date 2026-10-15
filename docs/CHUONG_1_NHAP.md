# Chương 1. Giới thiệu

> **Bản nháp S1-13** (Bùi Hải Đức, 15/10/2026), chưa qua nhóm duyệt. Hiện trạng ghi theo repo tại nhánh `main` sau khi merge PR #4–#6. Mục 1.8 là cấu trúc báo cáo đề xuất; nhóm cần chốt.

## 1.1. Bối cảnh và vấn đề

Đề tài xuất phát từ một vấn đề ở Việt Nam: học sinh vùng xa ít có cơ hội tiếp cận nội dung STEM về không gian. Nhóm hướng tới một trò chơi dùng ảnh thật của NASA về Mặt Trăng, Sao Hỏa và các thiết bị NASA để lại ở đó, để các em học qua trải nghiệm [1].

Hố va chạm là dấu vết dễ nhận ra nhất trên bề mặt Mặt Trăng. Trên ảnh chụp từ quỹ đạo, một hố thường hiện thành một vành gần tròn, với một nửa sáng và một nửa tối tùy hướng nắng. Đếm hố theo kích thước giúp so sánh hai vùng: trong cùng điều kiện quan sát và cùng dải kích thước, vùng có mật độ hố cao hơn thường đã chịu va chạm lâu hơn. Đây chỉ là so sánh **tuổi tương đối**, không cho ra tuổi tuyệt đối.

Việc khoanh và đếm hố bằng tay vừa là một hoạt động học tập tốt, vừa là bài toán xử lý ảnh rõ ràng. Máy có thể đề xuất vị trí hố bằng biến đổi Hough tròn. Học sinh có thể tự khoanh rồi so sánh với máy và với danh mục hố đã công bố. Đề tài nối hai việc này trong cùng một sản phẩm.

## 1.2. Đề tài NASA 24 và yêu cầu

Nhóm thực hiện **Đề 24 — Phát hiện hố va chạm và trò chơi STEM cho học sinh**, gắn với các thử thách NASA #1, #3, #11 [1].

- **Dữ liệu:** ảnh LRO (Mặt Trăng) và CTX/HiRISE (Sao Hỏa) công khai; ảnh bãi hạ cánh Apollo và rover; danh mục hố va chạm đã công bố để đối chiếu.
- **Bốn chức năng bắt buộc:**
  1. Tiền xử lý ảnh (cân bằng tương phản, làm trơn) và phát hiện hố bằng biến đổi Hough tròn **tự cài đặt**, kết hợp cặp vùng sáng–tối theo hướng nắng.
  2. Đếm hố, vẽ phân bố kích thước, so sánh mật độ hố giữa hai vùng để giải thích "bề mặt nào già hơn".
  3. Chế độ chơi: học sinh khoanh hố trên ảnh, hệ thống chấm điểm so với kết quả máy và danh mục.
  4. Thẻ "khoa học" kể chuyện về thiết bị NASA để lại tại vùng ảnh (Apollo, rover), hiển thị khi học sinh tìm thấy.
- **Đánh giá:** Precision và Recall phát hiện hố so với danh mục, coi là trúng khi sai lệch tâm ≤ 0,5 bán kính; khảo sát thử với ít nhất 10 học sinh về mức độ hứng thú và hiểu bài.
- **Hướng phát triển gợi ý:** chọn điểm hạ cánh an toàn, quản lý tiền đồn theo thử thách #3, bản tiếng Việt chạy ngoại tuyến.

## 1.3. Mục tiêu của nhóm

1. Xây chuỗi xử lý ảnh từ ảnh LROC thật tới danh sách hố có tâm và bán kính, phần Hough tự viết bằng NumPy và có đối chiếu với thư viện.
2. Thống nhất một hợp đồng dữ liệu chung cho ảnh, metadata và danh sách hố (máy, danh mục, người chơi), cùng hệ tọa độ 512 × 512 px gốc trên-trái [2].
3. Làm giao diện tiếng Việt chạy ngoại tuyến để học sinh mở ảnh, khoanh, sửa và lưu câu trả lời.
4. Chỉ chấm điểm và báo độ đo khi đã có danh mục tham chiếu đã xác minh cho đúng vùng ảnh. Không dùng kết quả máy hoặc số liệu đặt sẵn để thay đáp án.
5. Đo hiệu quả theo đúng yêu cầu đề: Precision/Recall trên danh mục và khảo sát ít nhất 10 học sinh.

## 1.4. Phạm vi và giới hạn

- **Thiên thể:** làm Mặt Trăng trước. Bộ ảnh hiện có **26 ảnh cắt 512 × 512** từ **16 ảnh LROC** tải từ máy chủ LROC/PDS chính thức, mỗi ảnh có metadata về tỷ lệ (2 hoặc 20 m/px), góc tới và dải bán kính tìm kiếm [3]. Sao Hỏa (CTX/HiRISE) để sau.
- **Kích thước hố:** mỗi ảnh có dải đường kính riêng, đổi ra bán kính pixel và kẹp trong [5, 128] px để Hough chạy được trên máy cá nhân.
- **Danh mục tham chiếu:** danh mục Robbins [4] không đủ cho hố nhỏ hơn 1 km ở ảnh 2 m/px. Bộ ảnh vì vậy ghi `reference_status="unavailable"`. Nhãn thủ công S1-10 hiện mới có 4 hố thưa trên một ảnh và chưa kiểm chéo [5]. **Chưa có Precision/Recall hay điểm trò chơi nào được tính.**
- **Diễn giải khoa học:** so sánh mật độ chỉ gợi ý tuổi tương đối giữa hai vùng có điều kiện phù hợp. Kết luận bị ảnh hưởng nếu máy bỏ sót hoặc khoanh nhầm.
- **Thời gian:** ba tuần, bốn thành viên (mục 1.7).

## 1.5. Cách tiếp cận tổng quát

```text
Ảnh LROC thật ──► cắt 512×512 + metadata (S1-06)
                     │
                     ▼
        Tiền xử lý B1–B8 (S1-08): thu nhỏ, xám, chuẩn hóa phân vị,
        CLAHE, Gauss, Sobel, Canny, mặt nạ biên
                     │  edges, theta
                     ▼
        Hough tròn NumPy (S1-07): bỏ phiếu theo vòng tròn hoặc theo
        hướng gradient, chọn đỉnh, loại trùng (NMS)
                     │  ứng viên (x, y, r, votes)
                     ▼
        Kiểm tra sáng–tối theo hướng nắng, lọc trùng (S1-11)      [đang làm]
                     │
       ┌─────────────┼──────────────────────────┐
       ▼             ▼                          ▼
  Thống kê,     Trò chơi: người chơi khoanh  Thẻ khoa học
  mật độ (S2)   (S1-09), chấm với máy và     tại địa điểm
                danh mục (S2)                Apollo/rover (S2)
```

Mọi bước trao đổi dữ liệu qua cùng một hợp đồng [2]. Ảnh xử lý luôn là 512 × 512 px, tâm và bán kính tính theo pixel ảnh xử lý, và đổi được về ảnh nguồn qua metadata. Danh sách hố của máy, danh mục và người chơi dùng chung cấu trúc nhưng **lưu riêng** (`source` = `machine`, `catalogue`, `player`). Mỗi lần chạy lưu thư mục riêng kèm tham số và mã commit để tái tạo được.

Lý thuyết Hough và ví dụ tính tay được trình bày ở chương lý thuyết (S1-12, S1-15) [6][7].

## 1.6. Hiện trạng sau tuần 1

| Phần | Đã có trong repo | Bằng chứng | Còn lại |
|---|---|---|---|
| Dữ liệu (S1-06) | 26 ảnh LROC thật, metadata, mặt nạ hợp lệ, bundle ngoại tuyến có SHA256 | `docs/S1-06_*` | Nhãn tham chiếu đã xác minh |
| Tiền xử lý (S1-08) | Chuỗi B1–B8 tự viết, lưu ảnh từng bước | `docs/TIEN_XU_LY.md` | — |
| Hough (S1-07, S1-12, S1-15) | Hough NumPy hai cách bỏ phiếu; ví dụ 5×5 tính tay khớp code; đối chiếu OpenCV trên cảnh giả lập | `docs/HOUGH.md`, `docs/S1-12_*`, `docs/S1-15_*` | Chọn tham số trên ảnh thật |
| Nhãn tham chiếu (S1-10) | Công cụ ghi nhãn; 4 nhãn thưa trên ảnh demo, chưa kiểm chéo | `docs/S1-10_HUONG_DAN_NHAN_HO.md` | Kiểm chéo; nhiều ảnh hơn |
| Giao diện khoanh hố (S1-09) | Giao diện tiếng Việt ngoại tuyến: vẽ, sửa, xóa, hoàn tác, phóng to, lưu và tải JSON | `docs/S1-09_*`, `docs/ui-design/` | Nối với kết quả máy |
| Chạy từ đầu đến cuối (S1-13) | Chạy được cả 26 ảnh, lưu run và overlay | `docs/S1-13_CHAY_TU_DAU_DEN_CUOI.md` | Lọc S1-11; chấm điểm |
| Sáng–tối, lọc trùng (S1-11) | Chưa cài | — | Tuần 1–2 |
| Thống kê, chấm điểm, thẻ khoa học | Chưa cài (khung hàm báo `NotImplementedError`) | — | Tuần 2 |

Lần chạy cả bộ cho thấy vấn đề chính của tuần 2. Không có bước lọc, Hough trên ảnh thật trả đủ trần **100 ứng viên ở cả 26 ảnh**, phần lớn là vòng nhỏ trên vệt tia và đá. Kết quả máy hiện chỉ là ứng viên thô, chưa phải số hố [8].

## 1.7. Tổ chức nhóm và kế hoạch

| Thành viên | Phụ trách | Đầu việc tuần 1 |
|---|---|---|
| Bùi Hải Đức | Khung repo, hợp đồng dữ liệu, giao diện, tích hợp, chấm điểm, ghép báo cáo | S1-05, S1-09, S1-13 |
| Nguyễn Mạnh Tiến | Hough NumPy, lý thuyết, kiểm chứng | S1-07, S1-12, S1-15 |
| Đinh Quang Hưng | Tiền xử lý, sáng–tối, lọc trùng, thống kê | S1-08, S1-11, S1-14 |
| Hoàng Quốc Anh | Dữ liệu, metadata, nhãn tham chiếu, thẻ khoa học, thực nghiệm, khảo sát | S1-06, S1-10, S1-16 |

- **Tuần 1:** có bản chạy đầu tiên và dữ liệu khớp nguồn.
- **Tuần 2:** đủ bốn chức năng, chốt tham số.
- **Tuần 3:** đánh giá, khảo sát học sinh, hoàn thiện bộ nộp.

Mỗi phần đi qua pull request có kiểm thử tự động (GitHub Actions). Mỗi thành viên ghi nhật ký vào `docs/NHAT_KY_NHOM.csv`.

## 1.8. Cấu trúc báo cáo (đề xuất)

1. **Chương 1 — Giới thiệu:** bối cảnh, yêu cầu đề, mục tiêu, phạm vi, cách tiếp cận.
2. **Chương 2 — Cơ sở lý thuyết:** tiền xử lý, biên Canny, biến đổi Hough tròn, kiểm tra sáng–tối (S1-14, S1-15).
3. **Chương 3 — Thiết kế và cài đặt hệ thống:** hợp đồng dữ liệu, chuỗi xử lý, giao diện và trò chơi.
4. **Chương 4 — Dữ liệu:** nguồn ảnh, cách cắt, metadata, nhãn tham chiếu và giới hạn (S1-16).
5. **Chương 5 — Thực nghiệm và đánh giá:** Precision/Recall trên danh mục đã xác minh, ba thí nghiệm, khảo sát học sinh.
6. **Chương 6 — Kết luận và hướng phát triển.**

## Tài liệu tham khảo của chương

[1] Danh sách đề tài liên quan NASA, Đề 24 "Phát hiện hố va chạm và trò chơi STEM cho học sinh" (tài liệu môn học).
[2] Nhóm 2, *Định dạng dữ liệu*, `docs/DINH_DANG_DU_LIEU.md`.
[3] Nhóm 2, *Bàn giao bộ ảnh S1-06*, `docs/S1-06_HUONG_DAN_DU_LIEU.md`; nguồn ảnh: LROC/PDS (https://data.lroc.im-ldi.com/).
[4] Robbins, S. J. (2019). A New Global Database of Lunar Impact Craters >1–2 km: 1. Crater Locations and Sizes, Comparisons With Published Databases, and Global Analysis. *Journal of Geophysical Research: Planets*, 124(4), 871–892. DOI 10.1029/2018JE005592.
[5] Nhóm 2, *Hướng dẫn ghi nhãn hố tham chiếu S1-10*, `docs/S1-10_HUONG_DAN_NHAN_HO.md`.
[6] Nhóm 2, *Ví dụ và đối chiếu Hough S1-12*; *Lý thuyết Hough S1-15*; danh mục nguồn `docs/TAI_LIEU_THAM_KHAO_HOUGH.md` (Duda & Hart 1972; Yuen và cộng sự 1990; Canny 1986).
[7] NASA Science, *Earth's Moon*, https://science.nasa.gov/moon/.
[8] Nhóm 2, *Chạy từ đầu đến cuối S1-13*, `docs/S1-13_CHAY_TU_DAU_DEN_CUOI.md` và `docs/evidence/s1-13/`.

> Trước khi nộp cần: đọc toàn văn [4] để ghi đúng tập/trang; thay [1] bằng tên chính thức của tài liệu môn học; cập nhật mục 1.6 theo hiện trạng cuối tuần 3.
