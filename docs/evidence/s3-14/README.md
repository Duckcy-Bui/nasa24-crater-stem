# Bằng chứng S3-14 · 04/11/2026

[Biên bản, phạm vi và người xử lý lỗi](../../S3-14_KIEM_TRA_BAN_GIAO.md). `summary.json` ghi kết luận, phiên bản, hash nguồn runtime cuối, sản phẩm còn thiếu và giới hạn.

- `initial_checks.json`, `logs/python.log`, `logs/report_numerics.log`: giữ cả hai lỗi lượt đầu, không thay lịch sử bằng kết quả sau sửa.
- `fresh_checks.json`, `logs/fresh_install.log`, `logs/fresh_python.log`: venv mới, requirements-test, 370 test đạt trên archive cộng bản sửa đóng gói.
- `logs/python_final.log`: 370 test đạt trên repo cuối sau sửa; `logs/packaging_final.log`: 15 test đóng gói đạt. Log `logs/python_final_encoding_failed.log` giữ lượt kiểm bổ sung thiếu PYTHONUTF8=1 theo README; đặt đúng biến môi trường và chạy lại, không sửa nguồn. Sáu file checkout khác archive chỉ ở CRLF/LF, ghi rõ trong summary; không sửa các file đó.
- `logs/test_canvas_*.log`: 6 bộ JavaScript đạt, nguồn canvas không đổi.
- `fresh_report_numerics.json`: 78 phép so/26 ảnh và Hough tính tay; khớp sai số hồ sơ S3-12.
- `browser/results.json`, `logs/browser.log`: Chromium kiểm 7 ảnh, nhãn điểm 1440/390 px và cột giả lập 128 px, bảng đếm tay, cảnh báo trần và kéo bán kính. Bốn PNG chọn từ 17 ảnh local; đã xem trực tiếp ảnh điểm desktop/mobile và bảng Lunokhod 1. Công cụ không assert đầy đủ CI/p; không kiểm VPS.
- `reproduction/`: manifest full/11 bước, log, 5 CSV Bảng 4.4–4.8 và index; kiểm mọi hash artifact local trước khi chọn bằng chứng. Bảng 4.5 là nhãn người lịch sử.
- `report/word_export_failure.json`: dựng DOCX được; Word quá thời gian chưa có PDF, chưa xác nhận số trang.

`archive_manifest.json` ánh xạ hash byte gốc local sang byte công bố đã ẩn đường dẫn máy. Hash bên trong manifest/index/JSON vẫn dẫn byte gốc; dùng `published_sha256` để kiểm bản công bố. CSV bảng và PNG giữ nguyên byte. Log/ảnh đầy đủ, nguồn cách ly, venv mới và DOCX thử ở `outputs/s314_20261104/`, không đưa vào Git; manifest full còn liệt kê artifact không chép vào hồ sơ chọn này.

Nguồn full/browser là `a50c145ecdb2c521298ad1a4d44a794465ced956`, giữ nguyên suốt lượt đo. Sau đó chỉ sửa mã đóng gói `scripts/package_s316.py`. Đây là kiểm hỗ trợ bằng Codex, không phải chữ ký/xác nhận cá nhân hoặc nghiệm thu của trưởng nhóm.
