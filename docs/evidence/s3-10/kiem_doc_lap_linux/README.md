# S3-10 — Kiểm độc lập trên Linux, 31/10/2026

Lượt do trưởng nhóm phối hợp chạy với Codex hỗ trợ trên máy của trưởng nhóm, Intel i5-12450HX, Linux x86_64, Python 3.12.3; mã nền `13394de`. Chạy từ 13:00:56 đến 13:14:24 UTC, mất 807,232 giây; `complete/full`, mặc định `repeats=3`, đủ tám bước. Thời gian ghi theo log lượt chạy, không dùng để so hiệu năng giữa các máy.

- [manifest.json](manifest.json): bản công khai đã ẩn đường dẫn theo [ghi chú 01/11/2026](../README.md#an-duong-dan-20261101); SHA-256 `7052219bf52564048ce51419b5b3972f12bb339d4fb5711dd5116374488150cf`. Bản gốc chưa ẩn cùng SHA được giữ riêng ngoài repo; bản công khai không còn nguyên byte với bản gốc.
- [so_khop_tom_tat.json](so_khop_tom_tat.json): trích từ kết quả đối chiếu Vòng 1, gồm 25 nhóm so sánh (17 nhóm dòng CSV, tám nhóm bản ghi ảnh JSON), số khớp/lệch và 10 file khác hash nguồn kèm giải thích. Không chép dòng kết quả. Hồ sơ đối chiếu là [full](../full/), [S2-15](../../s2-15/), [S2-06/S3-02](../../s2-06-s3-02/), [S2-07](../../s2-07/) và [S2-09](../../s2-09/).

Tất cả dòng/bản ghi trong phạm vi so sánh đều khớp. CSV khác schema so cột chung; bỏ thời gian, timestamp, đường dẫn và tách metadata nhận diện. S2-07 cũ chỉ có một ảnh, đối chiếu được 2/4/2 dòng E1/E2/E3; phần còn lại so với S3-10/full. Tóm tắt này không lưu chi tiết từng giá trị JSON hay toàn bộ 62 artifact; manifest giữ hash của lượt gốc, không khẳng định các artifact đó đều nằm trong thư mục này.

Hash nguồn: 117/127 file trùng byte. Tám file chỉ khác LF/CRLF; hai script khớp bản CLI cuối trong [quick/manifest.json](../quick/manifest.json), Git `7d8a0a9` và ghi nhận ở [verification.json](../verification.json). Manifest full cũ ghi commit nền cùng working tree chưa commit, nên không suy mọi diff từ commit nền là thay đổi sau lượt chạy.

NPZ giả lập có hash cũ `9e6fdea9190bcae45bb59efa0b41a74f18c0ff7ed1e7a7dce8f1dd420dc0c119`, mới `f1a39a3c281c27890b7699baad5a9b3a1d1f72b4a89b432670470e2a181523e7`. Bản NPZ cũ không có trong Git; chưa so được từng mảng hoặc kết luận nguyên nhân khác byte. CSV/JSON giả lập đã so khớp; PNG giả lập trùng byte. Ba PNG density trùng pixel và dữ liệu IDAT sau giải nén, chỉ khác luồng nén.

Ngày 31/10/2026, người kiểm độc lập đối chiếu bằng script riêng: **25/25 nhóm, 9 bảng CSV/102 dòng riêng, 0 giá trị lệch**; xác nhận lượt gốc có đủ **62 artifact**, tất cả đúng hash manifest. Kết quả PASS trong phạm vi S3-10 và nháp S3-16. **Đức quyết định nghiệm thu S3-10; Sheet J49 do Đức cập nhật.**

Nhãn thưa chỉ cho Recall_known; holdout là đánh giá lặp, không dùng chọn tham số. `.gitattributes` áp dụng `docs/evidence/s3-10/** -text` để giữ byte qua checkout Linux/Windows.
