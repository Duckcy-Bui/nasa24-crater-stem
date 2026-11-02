# Hồ sơ S3-05 — kết quả chạy trên ảnh thật

Chạy ngày 01/11/2026 bằng `scripts/s305_experiments.py`, lấy S2-15 làm baseline. Diễn giải đầy đủ tại [S3-05_BA_THI_NGHIEM.md](../../S3-05_BA_THI_NGHIEM.md). Không có dữ liệu khảo sát hoặc dữ liệu giả lập trong hồ sơ này.

| Bộ | Bảng | Nội dung | Ảnh |
|---|---|---|---:|
| E1 | [E1.csv](E1.csv) | 6 dòng so sánh trên 2 ảnh đủ điều kiện nắng; 2 dòng thô ghi không đánh giá được sáng–tối trên STT 17/Mare | 4 |
| E2 | [E2.csv](E2.csv) | 4 cấu hình × 3 ảnh tuning; mỗi lần chỉ đổi một tham số | 3 |
| E3 | [E3.csv](E3.csv) | 3 nhánh × 3 ảnh tuning; 1 baseline Mare chỉ mô tả | 4 |

- `E1/`, `E2/`, `E3/`: ảnh PNG theo image_id và JSON chi tiết từng nhánh. JSON giữ vòng máy, nhãn tham chiếu, cặp ghép, nhãn bỏ sót, dải/lưới bán kính thực quét, tiền xử lý, tham số Hough và vòng bị loại kèm lý do.
- `configs/`: snapshot cấu hình nền S2-15 và ba cấu hình E2 thay đúng một yếu tố; các nhánh lọc E1/E3 là thí nghiệm riêng, không sửa cấu hình game.
- [report.json](report.json): phải có `status=complete`; ghi commit nền và hash byte working tree thực tế, nguồn nhãn/ảnh/mask/split/cấu hình, môi trường, phân bố shading theo vòng khớp/không khớp và thông số phân lớp/dedupe. Commit nền chưa chứa script S3-05 mới; SHA-256 nhận diện mã đã chạy.
- [verification.json](verification.json): đối chiếu bảng/JSON/mã băm và kiểm tra điều kiện đánh giá sau lượt chạy. Danh sách `artifacts_sha256` trong report xác định chính xác các file được băm; biên bản kiểm tra và log test được thêm sau chạy. Bản sửa tài liệu sau chạy, nếu có, được ghi riêng tại `post_run_documentation`, không thay số liệu thực nghiệm.

Màu cam là nhãn chắc chắn. Ở E2/E3, xanh lá là vòng khớp nhãn, xanh lam là vòng chưa khớp (không đồng nghĩa sai). Ở E1, màu vòng biểu diễn trạng thái sáng–tối theo chú thích. Vòng đỏ nét đứt là vòng bị loại thử nghiệm.

FP/Precision/F1 là null (ô CSV trống), vì nhãn thưa. Các cột `seconds_hough` ở E1/E3 lặp thời gian Hough nền được dùng chung, **không phải thời gian bộ lọc hoặc tổng nhánh**. `input_hit_max_circles` báo việc đầu vào Hough chạm trần, kể cả khi số vòng sau lọc giảm. Holdout đã được xem trước, không dùng để chọn tham số; E1 trên holdout không đánh giá được. Mọi kết luận giới hạn trong ảnh/nhãn đã chạy, không suy ra hiệu quả khảo sát người dùng.
