# S3-10 — README, script tái tạo và kiểm tra thực thi

Ngày thực hiện: 30/10/2026. Phụ trách theo phân công: Nguyễn Mạnh Tiến; phối hợp: Bùi Hải Đức. Căn cứ `Giao_viec!A49:N49` trong `Nhom_2_NASA24_Phan_cong_3_tuan.xlsx`: README, danh sách phụ thuộc, dữ liệu/cấu hình rõ ràng, seed cố định, ví dụ nhỏ và một lệnh tái tạo các bảng kết quả.

## Phạm vi và bảo toàn S2-15

Nhánh `s3-10-reproduction` bắt đầu từ `NMTien` tại `210e68d`, đã bao gồm main `cc31a8f` qua merge `3159cb4`. Không bỏ các file S2-15: snapshot, cấu hình game, code app, script, test, biên bản và bằng chứng đều được giữ. Không tự chốt tham số mới hoặc sửa số liệu lịch sử.

- README hướng dẫn Python 3.12, Windows/Linux, demo, bộ ảnh ngoại tuyến, cấu hình, chỉ số và kiểm hồi quy.
- `requirements-test.txt` đã cố định sáu phụ thuộc trực tiếp; giữ nguyên danh sách đã kiểm chứng. Báo cáo dùng phụ thuộc riêng `requirements-report.txt`.
- `scripts/reproduce_s310.py` là lệnh tổng hợp. Mỗi lần chạy tạo thư mục mới, ghi `running/complete/failed`, lệnh và log từng bước, cấu hình, phiên bản thư viện, commit nền và SHA-256 byte mã/dữ liệu/đầu ra. Có kiểm tra mã/dữ liệu không thay đổi giữa lượt.
- `s207_experiments.py` nhận cấu hình nền cho cả E1/E2/E3; cấu hình holdout được áp dụng cho baseline sáng–tối/ảnh khó và nhánh E2. Trước đây `--chosen-config` chỉ đi tới E2. E2 trên tuning vẫn đổi một tham số mỗi lần; không quét biến thể trên holdout.
- `s209_density.py --output` cho phép ghi bảng/hình vào thư mục lượt chạy thay vì ghi đè bằng chứng S2-09.
- Phụ lục C dùng cùng lệnh và mô tả đầu ra với README.

## Cách chạy và diễn giải

Cài môi trường theo README, chạy từ gốc repo:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/reproduce_s310.py
```

Mặc định full giữ toàn bộ bước/đầu ra cũ: ví dụ tính tay/giả lập; 18 tuning S2-15; đối chiếu Hough 3 tuning/8 holdout; E1/E2/E3 S2-07 trên 3 tuning/2 holdout; đếm/mật độ hai vùng. Sau đó thêm ba bước: chạy `s305_experiments.py --output <lượt>/s305`, chụp hồ sơ lọc nhãn mù vào `blind_filter/`, xuất `chapter4_tables/`. Không ghi đè `E1.csv`–`E3.csv` cũ bằng CSV S3-05.

Linux/macOS sau khi kích hoạt venv dùng cùng entry point:

```sh
python -X utf8 -B scripts/reproduce_s310.py --output outputs/s310_full
```

Thư mục output phải mới. Trong `chapter4_tables/`:

| CSV | Bảng hiện tại | Dữ liệu và cách tổng hợp |
|---|---|---|
| `table_4_4.csv` | S3-05 gộp | 11 dòng nhánh cho bốn nhóm; E1 hai ảnh đủ nắng, E2/E3 ba tuning, Mare E3 nền. Gộp TP/nhãn, không tạo SD thời gian từ một lượt |
| `table_4_5.csv` | Lọc nhãn mù | Tám tổ hợp ảnh/cách lọc, dùng đúng hai report S2-02 lịch sử; tỷ lệ hố thật trên nhãn rõ, không phải Precision toàn ảnh |
| `table_4_6.csv` | Tổng hợp so Hough | Sáu dòng: trung bình ± SD mẫu theo 3/8 ảnh qua logic `ch4_mean_sd.summarize`, TP/FN và Recall_known gộp; tách bộ 28 nhãn khỏi S3-05 30 nhãn |
| `table_4_7.csv` | Từng ảnh holdout | Tám ảnh và hàng tổng; TP/FN ba phương pháp, số vòng OpenCV từ `evaluation_holdout/summary.json` |
| `table_4_8.csv` | Mật độ hai vùng | Tái tính từ đếm tay; diện tích một chữ số thập phân, mật độ/CI95 ba chữ số từ JSON chưa làm tròn |

`index.json` ghi nguồn/SHA đầu vào, SHA từng CSV, số dòng, quy tắc làm tròn và hash nguồn Chương 4 tại lúc xuất. Bảng 4.1–4.2 là kiểm kê dữ liệu/nhãn, 4.3 là thiết kế; năm bảng kết quả là 4.4–4.8 theo bản đã ghép S3-05.

**Lựa chọn cho nhãn mù:** `s202_review.py` tạo đánh giá từ nhãn người gắn với ứng viên lịch sử, CLI hiện ghi cứng vào hồ sơ S2-02 và có thể tạo mẫu nhãn. Runner không gọi CLI đó. Bước `blind_filter` chỉ đọc và sao đúng byte hai `docs/evidence/s2-02/<image_id>/report.json`, ghi SHA nguồn/bản sao và `filters.csv`; đánh dấu `historical_blind_labels`. Đây là tái kết xuất kết quả lịch sử, không phải người kiểm chấm lại. STT 17 thiếu nắng nên ô loại/mất hố của lọc sáng–tối trống; tỷ lệ hố thật giữ mức nền.

Kiểm nhanh: thêm `--quick --repeats 1`; giữ sáu bước cũ, bỏ hai bước đánh giá/thí nghiệm holdout và ba bước mới. Bước mật độ vẫn đọc các ô hai vùng như trước; không gọi quick là bộ bảng đầy đủ.

Game dùng score S2-15. Phép đối chiếu S2-06 ghi riêng ba phương pháp score/balanced/OpenCV với cấu hình S2-01. Chỉ số trên nhãn thưa là Recall_known; Precision/F1 để null hoặc ô CSV trống. E1 không đánh giá được khi thiếu hướng nắng và trên holdout mosaic. Mật độ máy S2-09 có lọc texture và dedupe; đây là nhánh đối chiếu riêng, không thay game. Holdout đã được xem trước đó, mọi lần chạy ở đây là đánh giá lặp, không dùng chọn tham số.

Seed cố định 0 cho hash Python trước khi chạy từng tiến trình con; ảnh giả lập dựng cố định, Hough không lấy mẫu ngẫu nhiên. Manifest giữ `seed=0`, thêm `seed_policy`; producer dùng OpenCV đặt một luồng, bổ sung ở S2-07/S2-09. Tốc độ phụ thuộc CPU/thư viện/điều kiện đo; không so byte timestamp, log thời gian, PNG/NPZ giữa các máy. Lượt `--repeats 1` chỉ kiểm thực thi/số đếm, không dùng kết luận tốc độ.

## Kiểm chứng và bàn giao

Kết quả chạy thực tế tại [docs/evidence/s3-10/](evidence/s3-10/README.md). Lượt đầy đủ `--repeats 1` hoàn tất tám bước; lượt quick chạy từ thư mục cha repo cũng complete. **303/303 test Python, 6/6 bộ test canvas và kiểm hợp đồng đạt**. Đối chiếu 31 file S2-15 giữ nguyên nội dung; vòng máy/metrics trên cả 18 ảnh giống hồ sơ cũ. Số liệu holdout score 4/66, balanced 5/66, OpenCV 65/66; bảng đếm hai vùng 47/32. Sau lượt full chỉ sửa chuỗi trợ giúp CLI và cách in đường dẫn output; hash hai phiên bản được ghi rõ, lượt quick và bộ test xác nhận bản cuối. Không suy kết luận tốc độ từ lượt một lần đo. Bộ Python/canvas kiểm tra logic và luồng Streamlit bằng test; không thay kiểm thao tác trực quan trên trình duyệt hay lượt chạy của người phối hợp. Chưa có xác nhận của Bùi Hải Đức trên máy khác; không ghi thay xác nhận này.

Chỉ nhận bộ bảng mới có manifest `status=complete, mode=full` và `chapter4_tables/index.json` complete. Các kết quả kiểm tám bước/303 test ở đoạn trên là lượt lịch sử ngày 30/10, không phải số kiểm của bản mở rộng. Dữ liệu khảo sát, duyệt diễn giải S3-05 và nghiệm thu vẫn thuộc chủ phần; runner không xác nhận thay thành viên.

## Kiểm độc lập trên Linux (31/10/2026)

Lượt do trưởng nhóm Bùi Hải Đức phối hợp chạy với Codex hỗ trợ trên máy của trưởng nhóm (Intel i5-12450HX, Linux x86_64, Python 3.12.3), commit `13394de`. Lệnh full giữ mặc định ba lượt đo, một warm-up trong phép đối chiếu Hough; chạy 13:00:56–13:14:24 UTC, mất 807,232 giây, đủ tám bước `complete/full`.

[Hồ sơ Linux gọn](evidence/s3-10/kiem_doc_lap_linux/README.md) lưu manifest công khai đã ẩn đường dẫn và số dòng khớp/lệch: frozen tuning 18/18, đối chiếu tuning 9/9, holdout 24/24; E1/E2/E3 lần lượt 15/15, 14/14, 10/10; hai bảng density mỗi bảng 2/2, giả lập 8/8. Không có dòng chung nào lệch; tổng S2-15 vẫn 10/174, holdout score/balanced/OpenCV vẫn 4/66, 5/66, 65/66. Phạm vi riêng của S2-07 cũ được ghi trong hồ sơ.

Hash nguồn có 117/127 file trùng byte, tám file chỉ khác LF/CRLF và hai script là bản CLI cuối đã ghi trong verification/quick. NPZ giả lập khác hash byte; thiếu bản NPZ cũ để so từng mảng, chưa kết luận nguyên nhân. Không dùng thời gian để so tốc độ giữa máy; nhãn thưa và đánh giá lặp giữ nguyên giới hạn.

Ngày 31/10/2026, người kiểm độc lập đối chiếu bằng script riêng: **25/25 nhóm, 9 bảng CSV/102 dòng riêng, 0 giá trị lệch**; xác nhận lượt gốc có đủ **62 artifact**, tất cả đúng hash manifest. Kết quả PASS trong phạm vi S3-10 và nháp S3-16. **Đức quyết định nghiệm thu S3-10; Sheet J49 do Đức cập nhật.**

Bản công khai cập nhật ngày 01/11/2026 chỉ ẩn đường dẫn và cập nhật SHA phụ thuộc; SHA-256 manifest Linux công khai: `7052219bf52564048ce51419b5b3972f12bb339d4fb5711dd5116374488150cf`. Xem [quy tắc và bảng SHA cũ → mới](evidence/s3-10/README.md#an-duong-dan-20261101); bản gốc cùng hash được lưu riêng, không thay số liệu hoặc kết luận kiểm độc lập.
