# Bằng chứng S3-10 — 30/10/2026

- `full/manifest.json`: lượt đầy đủ `--repeats 1`, tám bước complete; nguồn tại `outputs/s310_full_validation/` (62 artifact). Chỉ dùng xác nhận số đếm/khả năng chạy, không kết luận tốc độ.
- `full/`: bản sao CSV/JSON bảng, cấu hình, log và ví dụ giả lập. Các NPZ và JSON máy từng ảnh vẫn ở thư mục outputs của lượt chạy, không sao chép lặp vào Git. Manifest giữ hash của toàn bộ artifact gốc.
- `quick/manifest.json`: bản cuối chạy từ thư mục cha repo bằng đường dẫn tuyệt đối; một ảnh tuning, không đọc ảnh holdout. Nguồn tại `outputs/s310_quick_validation/`.
- `checks/`: 303 test Python, sáu bộ test canvas, kiểm hợp đồng và đối chiếu bảo toàn S2-15.
- `verification.json`: kiểm hash toàn bộ artifact của hai lượt, hash nguồn bản cuối, và xác nhận holdout không quét E2. Sau lượt full chỉ sửa mã hóa hai chuỗi trợ giúp CLI và cách in đường dẫn output; không sửa thuật toán/cấu hình. Hai hash script khác được liệt kê tường minh; lượt quick và test xác nhận bản cuối.

S2-15 vẫn TP=10, FN=164 trên 18 tuning (5,75%); toàn bộ vòng máy và metrics khớp hồ sơ cũ. Đối chiếu Hough trên holdout: score 4/66, balanced 5/66, OpenCV 65/66. Đây là Recall_known trên nhãn thưa, Precision/F1 không xác định. Bảng mật độ giữ 47 hố Lunokhod 1 và 32 hố Mare Frigoris, p=0,3451.

E1/E2/E3 lần đầy đủ có 15/14/10 dòng tương ứng (3 tuning + 2 holdout); E2 holdout chỉ chạy chosen_on_tuning. Bộ thí nghiệm này xác nhận thực thi, không tự thay kết quả cuối S3-05 hoặc đóng dấu nghiệm thu của chủ task. Holdout đã được xem từ trước; đây là đánh giá lặp.

So với Git `210e68d`, 31 file S2-15 giữ nguyên nội dung. Bốn file Markdown/log có thể khác LF/CRLF do checkout; CSV S2-15 còn bị Git báo diff vì quy tắc `*.csv text eol=lf` dù byte file hiện tại giống chính xác blob cũ. Không ghi đè bằng chứng S2-15. Hồ sơ không thay cho Bùi Hải Đức xác nhận chạy trên máy khác.
