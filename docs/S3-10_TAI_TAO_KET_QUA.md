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

Mặc định chạy toàn bộ phạm vi đã có mã/dữ liệu: ví dụ tính tay/ảnh giả lập; 18 tuning S2-15; đối chiếu Hough 3 tuning/8 holdout; E1/E2/E3 trên 3 tuning và 2 holdout; bảng đếm/mật độ hai vùng. Bộ kết quả có `frozen_tuning.csv`, hai `evaluation_*/results.csv`, `E1.csv`–`E3.csv`, `density/`, JSON chi tiết và `manifest.json`. Kiểm nhanh: thêm `--quick --repeats 1`; không đọc ảnh holdout và không tạo đủ bộ bảng.

Game dùng score S2-15. Phép đối chiếu S2-06 ghi riêng ba phương pháp score/balanced/OpenCV với cấu hình S2-01. Chỉ số trên nhãn thưa là Recall_known; Precision/F1 để null hoặc ô CSV trống. E1 không đánh giá được khi thiếu hướng nắng và trên holdout mosaic. Mật độ máy S2-09 có lọc texture và dedupe; đây là nhánh đối chiếu riêng, không thay game. Holdout đã được xem trước đó, mọi lần chạy ở đây là đánh giá lặp, không dùng chọn tham số.

Seed cố định 0 cho hash Python; ảnh giả lập dựng cố định, Hough không lấy mẫu ngẫu nhiên. Tốc độ phụ thuộc CPU, thư viện và điều kiện đo; không so byte timestamp/log thời gian giữa các máy. Lượt `--repeats 1` chỉ kiểm thực thi và các số đếm, không dùng kết luận tốc độ.

## Kiểm chứng và bàn giao

Kết quả chạy thực tế tại [docs/evidence/s3-10/](evidence/s3-10/README.md). Lượt đầy đủ `--repeats 1` hoàn tất tám bước; lượt quick chạy từ thư mục cha repo cũng complete. **303/303 test Python, 6/6 bộ test canvas và kiểm hợp đồng đạt**. Đối chiếu 31 file S2-15 giữ nguyên nội dung; vòng máy/metrics trên cả 18 ảnh giống hồ sơ cũ. Số liệu holdout score 4/66, balanced 5/66, OpenCV 65/66; bảng đếm hai vùng 47/32. Sau lượt full chỉ sửa chuỗi trợ giúp CLI và cách in đường dẫn output; hash hai phiên bản được ghi rõ, lượt quick và bộ test xác nhận bản cuối. Không suy kết luận tốc độ từ lượt một lần đo. Bộ Python/canvas kiểm tra logic và luồng Streamlit bằng test; không thay kiểm thao tác trực quan trên trình duyệt hay lượt chạy của người phối hợp. Chưa có xác nhận của Bùi Hải Đức trên máy khác; không ghi thay xác nhận này.

Chỉ nhận bộ bảng có manifest `status=complete, mode=full`. Dữ liệu khảo sát người dùng S3-01, quyết định S3-03/S3-05 và nghiệm thu giao diện vẫn thuộc chủ task tương ứng. Không cập nhật Excel, gửi thông báo, commit/push hay triển khai dịch vụ trong lượt này.
