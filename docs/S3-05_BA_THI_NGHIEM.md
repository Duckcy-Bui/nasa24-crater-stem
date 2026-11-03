# S3-05 — Ba thí nghiệm và bảng/ảnh kết quả

Ngày chạy thực tế: **01/11/2026** (sau hạn kế hoạch 23–25/10/2026). Phụ trách theo bảng việc: **Hoàng Quốc Anh**; phối hợp kiểm tra: **Nguyễn Mạnh Tiến**. Căn cứ: [S2-07](S2-07_THI_NGHIEM_VA_THU_GAME.md), [S2-03](S2-03_TAP_DIEU_CHINH.md), [S2-15](S2-15_CHOT_THAM_SO.md).

## 1. Đầu ra và điều kiện chạy

- Script riêng: `scripts/s305_experiments.py`; không sửa thuật toán, app, cấu hình game hoặc split.
- [Hồ sơ kết quả](evidence/s3-05/README.md): ba bảng CSV, JSON vòng máy/cặp ghép/lý do loại vòng, cấu hình và 11 ảnh đối chiếu.
- [Report](evidence/s3-05/report.json): trạng thái lượt chạy, commit nền, SHA-256 mã/dữ liệu/cấu hình, môi trường và phân bố sáng–tối/phân lớp ứng viên.
- [Kiểm chứng](evidence/s3-05/verification.json): đối chiếu hash, bảng/JSON và các điều kiện đánh giá.

Mốc so sánh là `configs/s215_frozen.json`, giống cấu hình game `configs/default.json`: Hough NumPy full-circle, chọn `score`, ngưỡng phiếu 0,35, bước r=1 px, tối đa 100 vòng, dải r kẹp theo metadata; tiền xử lý giữ nguyên S2-15. S1-11 chỉ gắn nhãn; không bật lọc inverted/texture hoặc dedupe trong game. File cấu hình từng biến thể được chụp lại dưới `evidence/s3-05/configs/`.

Lượt chạy dùng `.venv` có **Python 3.14.7**, NumPy 2.5.4, OpenCV 5.0.0, Matplotlib 3.11.2; khác Python 3.12 được khuyến nghị trong README. Report ghi phiên bản thực tế, không coi đây là xác nhận chạy trên Python 3.12. Hough không lấy mẫu ngẫu nhiên; OpenCV đặt một luồng. Thời gian Hough là **một lượt mỗi cấu hình, không warm-up**, chỉ để chẩn đoán, không kết luận xếp hạng tốc độ.

Chỉ số dùng `src/evaluation.py`, ghép một–một theo tâm lệch ≤ 0,5 bán kính tham chiếu. Nhãn thưa đã có xác nhận kiểm chéo tại `data/reference_labels/review_confirmation.json`; chỉ báo **Recall_known**, FP/Precision/F1 để null. Không coi vòng không khớp nhãn là vòng sai và không coi số ứng viên giảm là độ chính xác tăng.

## 2. Phạm vi ảnh

| Ký hiệu trong bảng dưới | image_id | Split | Điều kiện và vai trò |
|---|---|---|---|
| STT 13 | `moon_ap16_m132732855l_c01` | tuning | Bóng mạnh, có hướng nắng dùng được; E1/E2/E3 |
| STT 9 | `moon_ap16_m102064759r_c01` | tuning | Nắng xiên 81,08°, có hướng nắng dùng được; E1/E2/E3 |
| STT 17 | `moon_ap16_m109134835l_c01` | tuning | Nắng gần đứng 7,64°; E2/E3, E1 không đánh giá được |
| Mare | `moon_marefrig_loc_c01` | holdout | Mosaic 20 m/px, thiếu hướng nắng; chỉ mô tả ảnh khó bằng cấu hình đã chốt |

Ba tuning là đúng `DEFAULT_IMAGES` của S2-07; có tổng 30 nhãn chắc chắn. Không gộp số này với bảng 3 ảnh/28 nhãn của phép đối chiếu S2-06 hoặc kết quả 18 ảnh S2-15. Mare đã được xem ở các nhiệm vụ trước; đây là đánh giá mô tả lặp, không phải một tập kiểm tra chưa xem. Không quét tham số hoặc thử chọn bộ lọc trên Mare.

## 3. E1 — Hough cơ bản so với thêm sáng–tối

[Bảng E1 đầy đủ](evidence/s3-05/E1.csv). Hai ảnh phù hợp được chạy ba nhánh trên cùng danh sách ứng viên: thô, gắn nhãn sáng–tối, thử loại `inverted`.

| Ảnh | Hough thô: vòng; TP/nhãn | Gắn sáng–tối: vòng; TP/nhãn | Thử bỏ inverted: vòng; TP/nhãn |
|---|---|---|---|
| STT 13 | 100; 0/9 | 100; 0/9 | 75; 0/9 |
| STT 9 | 100; 1/11 | 100; 1/11 | 76; 0/11 |

Trên STT 13, trạng thái sáng–tối gồm 28 consistent, 25 inverted và 47 unclear. Trên STT 9: 27 consistent, 24 inverted và 49 unclear. Phân bố riêng cho vòng khớp/không khớp nhãn được giữ trong report. Vòng không khớp nhãn thưa chưa phải dương tính giả.

**Kết quả chưa tốt được giữ lại:** ở STT 9, vòng M61 khớp nhãn C9 (tâm lệch 2,828 px, bằng 0,4041 bán kính tham chiếu) nhưng có trạng thái inverted; nhánh thử loại nó làm Recall_known giảm từ 1/11 xuống 0/11. Do đó không bật lọc inverted. Gắn nhãn S1-11 không đổi hình học/số vòng nên không đổi Recall_known, đúng thiết kế hiện tại.

STT 17 và Mare đều có 100/100 vòng `not_checked`, lần lượt do góc tới nhỏ hơn 30° và thiếu hướng nắng. Bộ kết quả vẫn lưu ảnh/vòng thô, ghi E1 không đánh giá được; không tạo một phép so sáng–tối giả trên hai ảnh này.

Ảnh đối chiếu: [STT 13](evidence/s3-05/E1/moon_ap16_m132732855l_c01.png), [STT 9](evidence/s3-05/E1/moon_ap16_m102064759r_c01.png).

## 4. E2 — Ảnh hưởng tham số

[Bảng E2 đầy đủ](evidence/s3-05/E2.csv). Giữ tiền xử lý và các tham số khác; mỗi biến thể chỉ đổi một yếu tố từ cấu hình nền. Chỉ chạy trên ba ảnh tuning.

| Ảnh | Nền (0,35; r bước 1) | Ngưỡng 0,30 | Ngưỡng 0,40 | Bước r=2 px |
|---|---|---|---|---|
| STT 13 | 0/9 | 0/9 | 0/9 | 0/9 |
| STT 9 | 1/11 | 1/11 | 1/11 | 1/11 |
| STT 17 | 0/10 | 0/10 | 0/10 | 0/10 |

Các ô là TP_known/số nhãn chắc chắn. Tất cả 12 dòng đều chạm trần 100 ứng viên; toàn bộ nhãn chắc chắn của các ảnh này nằm trong dải bán kính được cấu hình. Mỗi biến thể đều có Recall_known gộp 1/30 = 3,33% trên ba tuning này; không cải thiện số nhãn tìm lại. Đổi bước bán kính có thể đổi vòng được giữ dù TP không đổi; xem JSON/ảnh thay vì suy danh sách vòng giống nhau từ cùng một điểm Recall.

CSV lưu thời gian Hough thực đo của từng lượt. Bước r=2 quét ít bán kính hơn, nhưng một lần đo chưa đủ kết luận tốc độ. Không dùng E2 để sửa cấu hình đã chốt S2-15 hoặc tuyên bố đã tìm được cấu hình tối ưu.

Ảnh đối chiếu đủ bốn biến thể: [STT 13](evidence/s3-05/E2/moon_ap16_m132732855l_c01.png), [STT 9](evidence/s3-05/E2/moon_ap16_m102064759r_c01.png), [STT 17](evidence/s3-05/E2/moon_ap16_m109134835l_c01.png).

## 5. E3 — Ảnh khó

[Bảng E3 đầy đủ](evidence/s3-05/E3.csv). Trên tuning, nhánh bỏ texture và nhánh dedupe được áp dụng **riêng rẽ** lên cùng baseline đã phân lớp, không nối hai bộ lọc và không bật vào pipeline game.

| Ảnh | Nền: vòng; TP/nhãn | Bỏ texture: vòng; TP/nhãn | Dedupe: vòng; TP/nhãn |
|---|---|---|---|
| STT 13 — bóng mạnh | 100; 0/9 | 48; 0/9 | 96; 0/9 |
| STT 9 — nắng xiên | 100; 1/11 | 46; 1/11 | 91; 1/11 |
| STT 17 — nắng gần đứng | 100; 0/10 | 61; 0/10 | 97; 0/10 |
| Mare — mosaic holdout | 100; 0/6 | Không chạy | Không chạy |

Trên STT 9, bỏ texture giảm 54 vòng và dedupe giảm 9 vòng, vẫn giữ cặp M61–C9: đây là kết quả có ích trong phạm vi nhãn đã biết. Tuy nhiên STT 13/STT 17 vẫn không tìm lại được nhãn nào sau lọc; không được diễn giải việc giảm vòng là khắc phục bỏ sót hoặc chứng minh không mất hố chưa gán nhãn. Các vòng bị bỏ, `filter_reason`/`dedupe_reason`, vòng đại diện `duplicate_of` và cặp ghép trước/sau được lưu trong từng JSON.

Mare có 27 vòng được bộ phân lớp gọi rim, 4 shadow_edge và 69 texture, nhưng Recall_known vẫn 0/6. Đây là nhãn do thuật toán phân lớp, không phải kiểm bằng mắt xác nhận 27 hố thật. Không thử bộ lọc trên Mare để chọn cấu hình. Bộ ca này minh họa bóng mạnh, nắng gần đứng và mosaic; chưa có tập nhãn riêng xác nhận hố chồng nhau nên không tuyên bố đã nghiệm thu phát hiện hố chồng nhau.

Ảnh đối chiếu: [STT 13](evidence/s3-05/E3/moon_ap16_m132732855l_c01.png), [STT 9](evidence/s3-05/E3/moon_ap16_m102064759r_c01.png), [STT 17](evidence/s3-05/E3/moon_ap16_m109134835l_c01.png), [Mare](evidence/s3-05/E3/moon_marefrig_loc_c01.png).

## 6. Tái tạo và kiểm tra bàn giao

Sau khi cài phụ thuộc và chuẩn bị dữ liệu S1-06 theo README, từ gốc repo chạy vào **thư mục mới**:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/s305_experiments.py --output outputs/s305_recheck
```

Script từ chối cấu hình game lệch snapshot, split sai phạm vi và thư mục đầu ra đã tồn tại. Không ghi đè hồ sơ cũ. Report chỉ có `status=complete` khi đủ bảng/ảnh và hash mã/đầu vào không đổi trong lượt chạy; lỗi giữa lượt giữ `status=failed` và nguyên nhân. Các lượt sau có timestamp/thời gian Hough khác; so số vòng/cặp ghép và cấu hình, không yêu cầu hai file report giống byte.

Đã kiểm **17 test** liên quan: 4 test quy trình S3-05, 5 test S2-07, 6 test evaluation, 2 test S2-15. Đối chiếu tự động ba bảng với JSON, cặp ghép một–một, các nhánh lọc và mã băm; kiểm trực quan ảnh đại diện E1/E2/E3. Lượt đầu phát hiện chú thích ảnh đơn bị cắt; đã sửa bố cục và chạy lại toàn bộ hồ sơ. Lượt đầu được giữ riêng dưới `outputs/s305_initial_20261101/`, không dùng làm hồ sơ bàn giao.

**Bàn giao kỹ thuật:** đã có ba bộ kết quả, cấu hình, bảng/ảnh và diễn giải kết quả tốt/chưa tốt. Nguyễn Mạnh Tiến kiểm tra phần phối hợp và xác nhận nghiệm thu; chưa ghi thay xác nhận của Tiến, chưa cập nhật trạng thái chính thức trong bảng giao việc, chưa commit/push. Không triển khai hoặc khôi phục S2-14.

## 7. Ghi chú sau khi merge (02/11/2026)

Lượt chạy trên Windows ghi các file `.json` và `.csv` với kiểu xuống dòng CRLF và băm SHA-256 trên đúng byte đó. Khi commit, Git chuẩn hóa hai loại file này về LF theo `.gitattributes` (blob trên nhánh PR đã là LF), nên 37/49 SHA trong `artifacts_sha256` của [report.json](evidence/s3-05/report.json) không còn khớp file trong repo. Bản sửa khôi phục CRLF cho đúng 37 file đó, không đổi nội dung, và thêm ngoại lệ `docs/evidence/s3-05/** -text` giống hồ sơ S3-10. Sau sửa, 49/49 SHA khớp; không thay số SHA nào đã ghi.

Tương tự, 6/43 SHA trong `source_and_input_sha256` (`src/contracts.py`, `src/__init__.py` và bốn file `requirements*.txt`) được băm trên bản CRLF của working tree Windows. Các file này là mã nguồn chung nên giữ LF; đổi LF sang CRLF thì tái tạo đúng cả 6 SHA đã ghi. Chạy lại script trên Linux, Python 3.12 cho cùng mọi số vòng, cặp ghép và Recall_known.

[validation.log](evidence/s3-05/validation.log) ghi đường dẫn tuyệt đối tới trình thông dịch trên máy chạy. Theo [quy tắc ẩn đường dẫn](evidence/s3-10/README.md#an-duong-dan-20261101), bốn dòng `COMMAND:` thay gốc môi trường Python bằng `<venv>`; lệnh, tham số và kết quả test giữ nguyên. File này không nằm trong `artifacts_sha256`. SHA-256 trước khi sửa: `4ca640a9c77feed55ac537db2012936bf05eb9df937462ece1173ce694d4ca96`; sau khi sửa: `a808f86a82e3ef3d3d036d0eec82096b31e30e67d4fb281345af9e89af02f405`.
