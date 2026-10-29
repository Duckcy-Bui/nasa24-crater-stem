# Minh chứng S2-15 — 29/10/2026

- report.json: cấu hình, commit nền, trạng thái working tree, SHA-256 mã/config/manifest, môi trường và kết quả từng ảnh.
- results.csv: bảng 18 tuning, TP_known=10/FN_known=164/Recall_known=5,75%.
- Các JSON theo image_id: vòng máy, cặp ghép, nhãn bỏ sót và hash ảnh/metadata/mask/nhãn.
- validation.log: kết quả kiểm thử toàn repo với PYTHONUTF8=1.

Chỉ chạy tuning. Thời gian một lượt/ảnh không dùng làm benchmark. Hash tính trên byte local (có thể CRLF trên Windows). code_version là commit nền; nhận diện working tree bằng source_sha256. Nhãn thưa không có FP/Precision/F1 toàn ảnh.
