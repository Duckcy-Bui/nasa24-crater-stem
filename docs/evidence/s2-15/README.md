# Minh chứng S2-15 — 29/10/2026

- report.json: cấu hình, commit nền, trạng thái working tree, SHA-256 mã/config/manifest, môi trường và kết quả từng ảnh.
- results.csv: bảng 18 tuning, TP_known=10/FN_known=164/Recall_known=5,75%.
- Các JSON theo image_id: vòng máy, cặp ghép, nhãn bỏ sót và hash ảnh/metadata/mask/nhãn.
- validation.log: kết quả kiểm thử toàn repo với PYTHONUTF8=1.

Chỉ chạy tuning. Thời gian một lượt/ảnh không dùng làm benchmark. Hash tính trên byte local (có thể CRLF trên Windows). code_version là commit nền; nhận diện working tree bằng source_sha256. Nhãn thưa không có FP/Precision/F1 toàn ảnh.

Kiểm lại sau merge main `cc31a8f` vào `NMTien` tại `3159cb4`:

- `report_post_merge.json`: lần chạy lại hoàn chỉnh 18 tuning, hash nguồn sau tích hợp thống kê S2-09; vẫn 10/174.
- `post_merge_verification.json`: đối chiếu 18/18 danh sách máy, metrics, hash đầu vào, dải r và hậu xử lý với hồ sơ ban đầu; tất cả giống nhau. JSON vòng máy ban đầu được giữ làm bằng chứng đầu ra chung; JSON lần chạy mới nằm ở thư mục local được ghi trong file đối chiếu.
- `validation_post_merge.log`: 298 test Python, 6 bộ JavaScript và checker hợp đồng đều đạt.
