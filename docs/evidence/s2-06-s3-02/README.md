# Minh chứng S2-06 / S3-02

[Báo cáo và lệnh tái tạo](../../S2-06_S3-02_KIEM_CHUNG.md).

Chỉ giữ dữ liệu gọn trong Git:

- [results.csv](results.csv): 33 dòng ảnh/phương pháp, cột `split` phân biệt 3 tuning và 8 holdout; FP/P/F1 trống vì nhãn thưa.
- [summary.json](summary.json): tham số, hash cấu hình/mã/đầu vào gốc, môi trường, median thời gian, số ứng viên, TP/FN/Recall trước/sau lọc trùng; kèm tóm tắt kiểm thử/giả lập cũ. Hash và code_version là của lần đo ngày 27/10/2026, không phải mã sau review.
- [input_hashes.json](input_hashes.json): SHA-256 ảnh, metadata, mask và cấu hình.
- [archive_manifest.json](archive_manifest.json): SHA-256/size mọi file chi tiết trong `outputs/s2-06-s3-02/` và SHA-256 từng entry của `details.zip`.

Chi tiết đã chuyển sang `outputs/s2-06-s3-02/` (bị Git bỏ qua): ZIP đầy đủ mọi vòng dự đoán/cặp lọc trùng, report từng tập, log test và ảnh PNG gốc. Manifest ghi `availability=local_only`, `shared_url=null`: chưa có bản sao Drive cho nhóm. Có thể tái chạy theo hướng dẫn để sinh bộ mới; timing/hash phụ thuộc môi trường và mã lúc chạy. Lượt lỗi `tuning/report.json` không thuộc kết quả/summary.

Ảnh đã thu nhỏ: [so sánh ứng viên JPEG](../../images/s206/large_craters.jpg).
Hồ sơ kiểm nhãn: [review_confirmation.json](../../../data/reference_labels/review_confirmation.json).

Game vẫn dùng `score`. `radius_balanced` chỉ bật trong cấu hình thử nghiệm; S2-15 chưa chốt cấu hình game. Nhãn thưa không chứng minh Precision toàn ảnh. OpenCV có ngân sách đầu ra khác NumPy.
