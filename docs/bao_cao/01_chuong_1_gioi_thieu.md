<!--
Người chốt: Bùi Hải Đức (S3-08). Nguồn: docs/CHUONG_1_NHAP.md (S1-13), bảng giao việc, README.
Việc còn lại: cập nhật mục 1.6 khi có kết quả S2-09, S3-01, S3-02, S3-05; điền tên chính thức của tài liệu đề bài.
-->

# Chương 1. Giới thiệu

## 1.1. Bối cảnh và vấn đề

Đề tài xuất phát từ một vấn đề giáo dục ở Việt Nam: học sinh ở vùng xa ít có cơ hội tiếp cận nội dung STEM về không gian. Đề bài đặt ra yêu cầu xây dựng một trò chơi học tập dùng ảnh thật của NASA về Mặt Trăng và Sao Hỏa, cùng các thiết bị con người đã để lại ở đó, để học sinh học qua trải nghiệm [@debai_nasa].

Hố va chạm là dạng địa hình phổ biến trên bề mặt Mặt Trăng [@nasa_moon]. Trên ảnh chụp từ quỹ đạo, một hố thường hiện thành một vành gần tròn: nửa hướng về Mặt Trời sáng, nửa còn lại tối do bóng đổ. Đếm hố theo kích thước cho phép so sánh hai vùng. Trong cùng điều kiện quan sát và cùng dải đường kính, bề mặt có mật độ hố cao hơn thường đã phơi ra trước va chạm lâu hơn, tức là già hơn về **tuổi tương đối** [@neukum2001]. Cách so sánh này không cho ra tuổi tuyệt đối.

Việc tìm và khoanh hố trên ảnh vừa là một hoạt động học tập trực quan, vừa là một bài toán xử lý ảnh rõ ràng. Máy có thể đề xuất vị trí hố bằng biến đổi Hough tròn [@duda1972; @yuen1990]. Học sinh có thể tự khoanh rồi so sánh với kết quả của máy và với nhãn hố đã được kiểm tra. Đề tài nối hai việc này trong cùng một sản phẩm.

## 1.2. Đề tài NASA 24 và yêu cầu

Nhóm thực hiện Đề 24, "Phát hiện hố va chạm và trò chơi STEM cho học sinh", gắn với các thử thách NASA số 1, 3 và 11 [@debai_nasa]. Đề bài nêu các yêu cầu sau.

- **Dữ liệu:** ảnh LRO của Mặt Trăng và ảnh CTX/HiRISE của Sao Hỏa công khai; ảnh khu vực hạ cánh Apollo và rover; danh mục hố va chạm đã công bố để đối chiếu.
- **Bốn chức năng bắt buộc:**
  1. Tiền xử lý ảnh (tăng tương phản, làm trơn) và phát hiện hố bằng biến đổi Hough tròn **tự cài đặt**, kết hợp kiểm tra cặp vùng sáng–tối theo hướng nắng.
  2. Đếm hố, vẽ phân bố kích thước và so sánh mật độ hố giữa hai vùng để giải thích "bề mặt nào già hơn".
  3. Chế độ chơi: học sinh khoanh hố trên ảnh, hệ thống chấm điểm so với kết quả máy và danh mục.
  4. Thẻ khoa học kể về thiết bị NASA đã để lại tại vùng ảnh (Apollo, rover), hiện ra khi học sinh tìm thấy.
- **Đánh giá:** Precision và Recall của phát hiện hố so với danh mục, coi là trùng khi tâm lệch không quá 0,5 bán kính; khảo sát ít nhất 10 học sinh về mức hứng thú và mức hiểu bài.
- **Hướng mở rộng gợi ý:** chọn điểm hạ cánh an toàn, quản lý tiền đồn theo thử thách số 3, bản tiếng Việt chạy ngoại tuyến.

## 1.3. Mục tiêu của nhóm

1. Xây dựng chuỗi xử lý từ ảnh LROC thật đến danh sách hố có tâm và bán kính. Phần biến đổi Hough được tự viết bằng NumPy và đối chiếu với thư viện OpenCV.
2. Thống nhất một định dạng dữ liệu chung cho ảnh, metadata và danh sách hố của máy, của nhãn tham chiếu và của người chơi, trên cùng hệ tọa độ 512 × 512 px.
3. Làm giao diện tiếng Việt để học sinh mở ảnh, khoanh, sửa và lưu câu trả lời, rồi xem kết quả chấm.
4. Chỉ chấm điểm và báo độ đo khi có nhãn tham chiếu đã được kiểm chéo cho đúng vùng ảnh. Kết quả của máy chỉ là ứng viên, không được dùng thay đáp án.
5. Đo hiệu quả theo đúng yêu cầu đề: độ đo phát hiện trên nhãn tham chiếu và khảo sát ít nhất 10 người chơi.

## 1.4. Phạm vi và giới hạn

**Thiên thể.** Nhóm làm Mặt Trăng trước. Bộ dữ liệu gồm 26 ảnh cắt 512 × 512 px từ 16 sản phẩm ảnh LROC tải từ kho dữ liệu chính thức [@lroc_pds; @robinson2012; @martin2018]. 15 ảnh có tỷ lệ 20 m/px (mosaic các vùng Apollo 15, Van de Graaff, Lunokhod 1, Lunokhod 2, Mare Frigoris) và 11 ảnh có tỷ lệ 2 m/px (vùng Apollo 16). Sao Hỏa nằm ngoài phạm vi của báo cáo này.

**Kích thước hố.** Dải đường kính đặt theo tỷ lệ ảnh: ảnh 2 m/px xét hố đường kính 20–500 m (bán kính 5–125 px), ảnh 20 m/px xét hố 200 m–4 km (bán kính 5–100 px). Bán kính tìm kiếm được kẹp trong [5, 128] px để Hough chạy được trên máy cá nhân.

**Nhãn tham chiếu.** Danh mục toàn cầu của Robbins chỉ đầy đủ cho hố từ khoảng 1–2 km trở lên [@robbins2019], nên không dùng được cho phần lớn hố trong ảnh 2 m/px. Nhóm tự gán nhãn thủ công **thưa**: mỗi ảnh có 4–13 hố được khoanh (tổng cộng 241 hố trên 26 ảnh), không phải toàn bộ hố trong ảnh. Vì vậy chỉ đo được tỉ lệ hố đã gán nhãn mà máy hoặc người chơi tìm thấy (Recall trên nhãn đã biết). Không đo được Precision và F1 trên toàn ảnh (mục 2.4).

**Dữ liệu ảnh.** Ảnh dùng là bản *browse* 8 bit của LROC, phù hợp để xem và minh họa, không phải dữ liệu để đo đạc khoa học định lượng [@lroc_rdrsis]. So sánh mật độ hố chỉ gợi ý tuổi tương đối giữa hai vùng có điều kiện phù hợp. Kết luận bị ảnh hưởng nếu máy bỏ sót hoặc khoanh nhầm.

**Thời gian và nhân lực.** Bốn thành viên thực hiện trong ba tuần, từ 09/10 đến 29/10/2026 (mục 1.7).

## 1.5. Cách tiếp cận tổng quát

Hình dưới đây tóm tắt luồng xử lý của sản phẩm. Mỗi khối ứng với một module trong mã nguồn và một phần của báo cáo.

```text
Ảnh LROC thật ─► cắt 512 × 512 + metadata + mặt nạ hợp lệ        (Chương 4)
                   │
                   ▼
   Tiền xử lý: thu nhỏ, ảnh xám, chuẩn hóa, CLAHE, Gauss,
   Sobel, Canny, mặt nạ biên                                     (2.1, 3.2)
                   │ ảnh biên, hướng gradient
                   ▼
   Hough tròn tự viết bằng NumPy: bỏ phiếu, chọn đỉnh, NMS      (2.2, 3.3)
                   │ ứng viên (x, y, r, số phiếu)
                   ▼
   Kiểm tra sáng–tối theo hướng nắng; phân lớp, lọc trùng       (2.3, 3.4, 3.5)
                   │ ứng viên máy
      ┌────────────┼──────────────────────────┐
      ▼            ▼                          ▼
  Thống kê,     Trò chơi: người chơi khoanh,  Thẻ khoa học
  mật độ (3.6)  chấm với máy và nhãn (5.2–5.4) theo vùng ảnh (5.5)
```

Mọi bước trao đổi dữ liệu qua cùng một định dạng (mục 5.1). Ảnh xử lý luôn là 512 × 512 px. Tâm và bán kính hố tính theo pixel của ảnh xử lý, với quy ước tâm pixel có tọa độ nguyên, và đổi được về ảnh nguồn và tọa độ địa lý qua metadata (mục 4.2). Danh sách hố của máy, của nhãn tham chiếu và của người chơi dùng chung cấu trúc nhưng lưu riêng. Mỗi lần chạy được lưu vào một thư mục riêng kèm tham số và mã phiên bản để tái tạo được.

## 1.6. Kết quả chính

Bảng 1.1 tóm tắt mức độ hoàn thành bốn chức năng bắt buộc và hai yêu cầu đánh giá tại thời điểm viết báo cáo.

| Yêu cầu | Kết quả | Mục |
|---|---|---|
| Tiền xử lý và Hough tự cài đặt | Chạy trên cả 26 ảnh; Hough NumPy có ví dụ tính tay và đối chiếu OpenCV; kiểm tra sáng–tối, phân lớp và lọc trùng có thể bật thêm | 3.2–3.5 |
| Thống kê và so sánh mật độ | [CHỜ S2-09: cài đặt thống kê và so sánh hai vùng] | 3.6 |
| Trò chơi khoanh hố và chấm điểm | Giao diện tiếng Việt chạy trên trình duyệt; chấm riêng so với máy và so với nhãn đã kiểm chéo, ghép hố một–một | 5.2–5.4 |
| Thẻ khoa học | Thẻ có nguồn cho các vùng Apollo 15, Apollo 16, Lunokhod 1 và Lunokhod 2; chưa gắn vị trí trên ảnh | 5.5 |
| Độ đo phát hiện | Recall trên nhãn đã biết của tập kiểm tra (8 ảnh, 66 nhãn): 6,06 % với Hough NumPy chọn theo điểm, 7,58 % khi chọn cân bằng theo bán kính; OpenCV đạt 98,48 % nhưng sinh hơn 8.000 vòng mỗi ảnh [CHỜ PR #26 được merge] | 4.7 |
| Khảo sát ít nhất 10 người chơi | [CHỜ S3-01: kết quả khảo sát] | 4.8 |

: Bảng 1.1. Mức độ hoàn thành các yêu cầu của đề.

Hạn chế lớn nhất của phần phát hiện là Hough trả đủ trần 100 ứng viên trên mọi ảnh, phần lớn là vòng nhỏ, nên bỏ sót các hố lớn dù chúng nằm trong dải bán kính tìm kiếm (mục 3.7). Vì vậy Recall trên nhãn đã biết của Hough tự cài đặt còn rất thấp (mục 4.7). Chương 5 tổng kết các hạn chế và hướng khắc phục.

## 1.7. Tổ chức nhóm và kế hoạch

Bảng 1.2 trình bày phân công chính. Phân công chi tiết theo từng đầu việc và phần đóng góp của mỗi người nằm ở Phụ lục A.

| Thành viên | Phụ trách chính |
|---|---|
| Bùi Hải Đức (nhóm trưởng) | Khung mã nguồn, định dạng dữ liệu, giao diện trò chơi, chấm điểm, tích hợp, ghép báo cáo |
| Nguyễn Mạnh Tiến | Hough tròn bằng NumPy, lý thuyết và kiểm chứng, đánh giá Precision/Recall |
| Đinh Quang Hưng | Tiền xử lý, kiểm tra sáng–tối, lọc trùng, thống kê hố |
| Hoàng Quốc Anh | Dữ liệu và metadata, nhãn tham chiếu, thẻ khoa học, thí nghiệm, khảo sát |

: Bảng 1.2. Phân công chính trong nhóm.

Kế hoạch chia ba sprint bảy ngày: sprint 1 (09–15/10) có bộ dữ liệu khớp nguồn, bản chạy đầu tiên và giao diện khoanh hố; sprint 2 (16–22/10) đủ bốn chức năng, chia tập và chấm điểm người chơi; sprint 3 (23–29/10) đánh giá, khảo sát, hoàn thiện báo cáo, slide và video. Mỗi phần việc vào kho mã qua pull request có kiểm thử tự động và người phối hợp duyệt (Phụ lục B).

## 1.8. Cấu trúc báo cáo

Ngoài chương này, báo cáo gồm bốn chương:

- **Chương 2 — Cơ sở lý thuyết:** tiền xử lý và trích biên, biến đổi Hough tròn, kiểm tra sáng–tối, đối sánh một–một và các độ đo, mật độ hố.
- **Chương 3 — Phương pháp và cài đặt:** chuỗi phát hiện, cài đặt tiền xử lý, Hough, kiểm tra sáng–tối, lọc trùng và thống kê.
- **Chương 4 — Dữ liệu, đánh giá và khảo sát:** nguồn ảnh, quy đổi tọa độ, nhãn tham chiếu, tập điều chỉnh và tập kiểm tra, ba thí nghiệm, kết quả phát hiện và khảo sát người chơi.
- **Chương 5 — Hệ thống, trò chơi và kết luận:** kiến trúc và định dạng dữ liệu, giao diện, chấm điểm, thẻ khoa học, kiểm thử và triển khai; kết luận, hạn chế và hướng phát triển.
