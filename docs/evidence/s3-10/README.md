# Bằng chứng S3-10 — 30/10/2026

- `full/manifest.json`: lượt đầy đủ `--repeats 1`, tám bước complete; nguồn tại `outputs/s310_full_validation/` (62 artifact). Chỉ dùng xác nhận số đếm/khả năng chạy, không kết luận tốc độ.
- `full/`: bản sao CSV/JSON bảng, cấu hình, log và ví dụ giả lập. Các NPZ và JSON máy từng ảnh vẫn ở thư mục outputs của lượt chạy, không sao chép lặp vào Git. Manifest giữ hash của toàn bộ artifact gốc.
- `quick/manifest.json`: bản cuối chạy từ thư mục cha repo bằng đường dẫn tuyệt đối; một ảnh tuning, không đọc ảnh holdout. Nguồn tại `outputs/s310_quick_validation/`.
- `checks/`: 303 test Python, sáu bộ test canvas, kiểm hợp đồng và đối chiếu bảo toàn S2-15.
- `verification.json`: kiểm hash toàn bộ artifact của hai lượt, hash nguồn bản cuối, và xác nhận holdout không quét E2. Sau lượt full chỉ sửa mã hóa hai chuỗi trợ giúp CLI và cách in đường dẫn output; không sửa thuật toán/cấu hình. Hai hash script khác được liệt kê tường minh; lượt quick và test xác nhận bản cuối.

S2-15 vẫn TP=10, FN=164 trên 18 tuning (5,75%); toàn bộ vòng máy và metrics khớp hồ sơ cũ. Đối chiếu Hough trên holdout: score 4/66, balanced 5/66, OpenCV 65/66. Đây là Recall_known trên nhãn thưa, Precision/F1 không xác định. Bảng mật độ giữ 47 hố Lunokhod 1 và 32 hố Mare Frigoris, p=0,3451.

E1/E2/E3 lần đầy đủ có 15/14/10 dòng tương ứng (3 tuning + 2 holdout); E2 holdout chỉ chạy chosen_on_tuning. Bộ thí nghiệm này xác nhận thực thi, không tự thay kết quả cuối S3-05 hoặc đóng dấu nghiệm thu của chủ task. Holdout đã được xem từ trước; đây là đánh giá lặp.

So với Git `210e68d`, 31 file S2-15 giữ nguyên nội dung. Bốn file Markdown/log có thể khác LF/CRLF do checkout; CSV S2-15 còn bị Git báo diff vì quy tắc `*.csv text eol=lf` dù byte file hiện tại giống chính xác blob cũ. Không ghi đè bằng chứng S2-15. Hồ sơ không thay cho Bùi Hải Đức xác nhận chạy trên máy khác.

<a id="an-duong-dan-20261101"></a>
## Ẩn đường dẫn công khai — 01/11/2026

Repo công khai chỉ giữ vị trí theo vai trò, không công bố thư mục cá nhân hoặc tên agent trong đường dẫn. Ghi chú chung này cũng áp dụng cho log S2-01/S2-15, tham chiếu hồ sơ S2-13 và hướng dẫn GitHub trong bảng dưới. Phần hồ sơ phía trên mô tả lượt gốc trước khi ẩn.

| Placeholder | Quy tắc |
|---|---|
| `<repo>` | Gốc checkout trên máy chạy; giữ nguyên đường dẫn con và dấu phân cách của hệ điều hành gốc |
| `<venv>` | Gốc môi trường Python; ưu tiên thay trước gốc checkout để không lộ vị trí môi trường |
| `<run-dir>` | Gốc lượt full Linux nằm ngoài checkout; mọi đường dẫn con dùng cùng gốc này |
| `<tmp-dir>` | Gốc thư mục tạm cá nhân của Windows; giữ tên thư mục con/tệp log gốc |
| `<app-run-dir>` | Thư mục hồ sơ kiểm ứng dụng vòng 4 nằm ngoài repo |
| `<app-report>` | Tên gốc báo cáo kiểm ứng dụng vòng 4; giữ đuôi `.md` |

Chỉ thay tiền tố dài nhất, giữ nguyên số liệu, khóa/thứ tự JSON và các nội dung khác; sau đó cập nhật SHA theo chuỗi phụ thuộc. Tên nội bộ trong gốc đường dẫn bị ẩn cùng gốc. Placeholder là metadata, cần thay bằng thư mục thật trước khi dùng lại lệnh lịch sử. URL loopback, thư mục tạm chung và đường dẫn hệ thống chung không bị đổi.

Bản gốc chưa ẩn và bảng ánh xạ chi tiết được lưu riêng ngoài repo, tại kho `privacy_raw/374ce36e3260`, kèm `SHA256SUMS` và chỉ mục SHA. Không đưa bản raw hoặc bảng có tiền tố cá nhân vào Git. Các byte cũ cũng còn trong lịch sử Git; cập nhật này làm sạch cây hiện tại, không viết lại lịch sử.

Các mục manifest trỏ tới tệp công khai đã đổi dùng SHA mới của tệp đó. Mục không có bản trong Git tiếp tục nhận diện artifact gốc; không tuyên bố đã ẩn các byte ngoài repo. Các cờ trong `verification.json` là kết quả kiểm lượt gốc, không phải một lần chạy lại sau ẩn. `source_input_sha256`, seed, cấu hình và số liệu không đổi.

Bảng SHA dưới gồm các tệp chứng cứ và chỗ dẫn hash được cập nhật, trước README/chỉ mục tổng. SHA của README này được kiểm qua `archive_sha256.json`; không tự ghi SHA của README hoặc của chỉ mục vào bảng để tránh vòng phụ thuộc. Bảng đầy đủ, gồm cả hai tệp tổng, lưu trong hồ sơ riêng ngoài repo.

| Tệp | SHA-256 trước ẩn | SHA-256 công khai |
|---|---|---|
| `docs/HUONG_DAN_GITHUB.md` | `78bf43aa374c813aac4bdcaece4376bddb10c686e828af28987ee067c21b315a` | `bdb390830d1df0d9a1c8ac759fc2fd1a35450719b081878c067ca0d766c63fc9` |
| `docs/S2-13_TICH_HOP.md` | `c33b0c6d552d22b82270f1caa029773de11c34841225cb7296800cbe9c4998c5` | `4de8e672073cc9ada9d4614e6ceecbd3894c374a6b38fa7ca703956c7a0fef6b` |
| `docs/S3-10_TAI_TAO_KET_QUA.md` | `04438f081d6d2924547dd458deec0b6563cf6a5eca9207b15ab12b8bfa0f7ca4` | `b37064aa328c66f53f40340b2c6f9ff71a1b531908ef820b68b8522a8f0dedfc` |
| `docs/evidence/s2-01/regression.log` | `f207e3d4343bf8045345c965919e3674da5a0fca662f0fb53968a012af302865` | `70cba462951cbacab6c82946ecb3e7af7a9afbaaabe08362238dcc2ab8da4299` |
| `docs/evidence/s2-15/validation.log` | `f4b9610d4513de6af3e227666377ad02e26ec99fc90139c8ce9bdfa5256795a7` | `467001630f8bf545f2e9b888996e3679d43d636b037eaa59673e0fb5351e5634` |
| `docs/evidence/s2-15/validation_post_merge.log` | `5a96a4eae1e4b273807c446bdd80d8ea33bb8dcf85347c0323d957601c2c608e` | `31a31cb4f9b4e01b4190895fbf2ce37bd4e9fab6f68ca3f9430918231b2a42f2` |
| `docs/evidence/s3-10/checks/python.log` | `571262d13605006e725ddc937c4766f56e7c70d2584f10b70a8972f304eb1339` | `7edab20c44c5fded8438cdaee1361ecaec687b03896666a16f52774fafa43596` |
| `docs/evidence/s3-10/full/experiments_holdout.json` | `b53d5c62bd6b293fdb882e060babeb48c3e0632309da92ebb3f434666eceb8ff` | `d57670d0bfaf57ff71a75479a087f8ac5844a5786cdfbdd52ab411c5bdc3de49` |
| `docs/evidence/s3-10/full/manifest.json` | `20ffe4c689a2838aa1fcf8237f9508741365bb4505ec9b83e5c108fb19458fb5` | `359fea6748acb8237a9a210b917a07a7fe86478aba5d88bcdae70b1749a43d75` |
| `docs/evidence/s3-10/full/synthetic.log` | `b0c9644b060cd8bba19507b3d946dc97f3aedd050dd2427df5062559c32f1ee6` | `f227e007886e2f32e6a8ddd17d1c41a144428838deb158f189a01d7864b6e9d0` |
| `docs/evidence/s3-10/kiem_doc_lap_linux/README.md` | `387a010138266fad7fa51a9f6ac56fceb8b8c9c0428de76c52539a0357692b15` | `bda43782464e62d1c16f7df5ed1349642b40951d5abd5887ac4bad0d0c7c65aa` |
| `docs/evidence/s3-10/kiem_doc_lap_linux/manifest.json` | `e8cce73f24c180b01f32af407ddbd00de6e6cc66f32b71880b051dbbc92f68ef` | `7052219bf52564048ce51419b5b3972f12bb339d4fb5711dd5116374488150cf` |
| `docs/evidence/s3-10/quick/experiments_tuning.log` | `725e29b825f5e30621fe1b193acb6c91716a937f055887f4e2501892c9adf11e` | `bcc07046b62dee55ff2b3af624ea90b5703c56407281e0a87a546c3cc28f859d` |
| `docs/evidence/s3-10/quick/manifest.json` | `f0d1298c5c4de5a695cf2dd1cbf90340ccb7adccc30ff368202881db95c786a2` | `8085d6f6764cd9f5ebe549e03047c7fa1ab2525b26340d833320a6c091c0ea03` |
| `docs/evidence/s3-10/quick/synthetic.log` | `f22d68de66b859798becb6b93b03cccf03e9cb03001205972ed4d1173cbb7510` | `3326fb918d30986e9c1234cbde823e1c77af54157e9864b63859d9f7a5b4b0f9` |
