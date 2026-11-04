# S3-14 — Kiểm tra chạy lại và đủ bộ sản phẩm

Ngày kiểm thực tế: **04/11/2026 (UTC+7)**. Phụ trách theo phân công: **Nguyễn Mạnh Tiến**, phối hợp cả nhóm; Codex hỗ trợ chạy kiểm và lập hồ sơ. Căn cứ `Giao_viec!A53:N53` trong `Nhom_2_NASA24_Phan_cong_3_tuan.xlsx`: phụ thuộc S3-10, S3-12, S3-13; cần biên bản, kết quả chạy lại, danh sách lỗi có người xử lý và kiểm đủ/khớp phiên bản repo, README/script, dữ liệu, PDF, slide, video, bảng đánh giá. Lịch gốc là sáng ngày 20 trước tổng duyệt buổi chiều; hồ sơ này ghi đúng ngày kiểm thực tế, chưa chứng minh đáp ứng lịch gốc.

## 1. Kết luận và phiên bản

**Kiểm kỹ thuật đạt sau sửa lỗi đóng gói Windows; chưa đủ điều kiện nghiệm thu bộ sản phẩm cuối.** Chưa nhận PDF cuối được duyệt, slide cuối, video, bảng đánh giá hoàn thiện và bản phân công có chữ ký. Không tự đánh dấu S3-14 hoàn thành trên bảng giao việc.

Nguồn full/Chromium: `a50c145ecdb2c521298ad1a4d44a794465ced956`; nhánh `s3-14-kiem-tra-ban-giao`. Hash mọi file tracked giữ nguyên suốt lượt chạy. Sau khi full kết thúc, chỉ sửa mã `scripts/package_s316.py`: tìm tên Python qua PATH trước khi tạo tiến trình con. Windows có thể ưu tiên Python cha khi chỉ truyền `python.exe`; dùng `shutil.which` rồi `abspath` khắc phục lỗi và giữ symlink venv.

Đã đối chiếu nguồn runtime cuối với archive dùng chạy kiểm trên venv mới: cùng nội dung, sáu khác biệt CRLF/LF có sẵn được ghi rõ và giữ nguyên. Chạy thêm đủ 370 test trên chính repo sau sửa để xác minh byte nguồn cuối. Thuật toán, cấu hình, nhãn và nguồn báo cáo không đổi. Chưa chốt commit nộp cuối hoặc kiểm VPS. [Tóm tắt/hash](evidence/s3-14/summary.json), [chỉ mục bằng chứng](evidence/s3-14/README.md).

## 2. Kết quả chạy lại

| Hạng mục | Kết quả | Bằng chứng/phạm vi |
|---|---|---|
| Môi trường mới | Đạt | Git archive, venv mới, cài requirements-test; checker, toàn bộ Python và kiểm số học đạt |
| Hợp đồng | Đạt | Repo nền và nguồn sạch; checker kiểm mẫu dữ liệu giả lập |
| Python | **370/370 đạt**, không skip | Cả venv mới trên archive có bản sửa và repo cuối; giữ log lượt đầu có 1 lỗi Windows |
| Đóng gói sau sửa | **15/15 đạt** | Chạy lại riêng trên repo cuối, gồm tên Python qua PATH và đường dẫn venv tương đối; dùng fixture, chưa phải gói nộp thật |
| Canvas | **6/6 bộ đạt** | Sự kiện, hình học, tọa độ vùng xem, sửa chính xác, lưu và phóng; nguồn không đổi |
| Dữ liệu | **26 ảnh**, mọi payload khớp SHA-256 bundle | Cài riêng từ bundle trong archive; local còn ảnh cũ ngoài bundle, giữ nguyên |
| Kiểm số học | **78 phép so/26 ảnh và Hough tính tay đạt** | Summary và hash ảnh bằng hồ sơ S3-12; chạy nguồn sạch vì script từ chối 27 ảnh local |
| S3-10 full | **complete/full, 11 bước**, seed 0, repeats 3 | Kiểm mọi hash artifact; đủ Bảng 4.4–4.8 và index complete |
| So hồ sơ Hough S3-10 | Khớp TP/FN, Recall và số ứng viên từng ảnh/phương pháp | 3 tuning + 8 holdout; không yêu cầu trùng thời gian |
| Game S2-15 | **10/174**, FN 164, Recall_known 5,75 % | 18 tuning, không chọn lại tham số trên holdout |
| Chromium local | **PASS** | 7 ảnh; nhãn điểm 1440/390 px, cột giả lập 128 px; bảng mật độ, cảnh báo trần và kéo bán kính; không lỗi trang/Streamlit trong phạm vi assertion |
| Kiểm ảnh bằng mắt | Đã xem | Ảnh điểm desktop/mobile và bảng Lunokhod 1; không suy ra kiểm toàn bộ giao diện |
| Dựng báo cáo | DOCX dựng được, ZIP/CRC hợp lệ | `outputs/s314_20261104/report/`; chưa kiểm hết nội dung/dàn trang. Thiếu LibreOffice/UNO; Word chạy ẩn quá 10 phút chưa có PDF nên dừng tiến trình do lượt kiểm tạo |

Holdout: score **4/66**, balanced **5/66**, OpenCV **65/66**. Nhãn thưa chỉ hỗ trợ Recall_known; chưa có FP/Precision/F1 toàn ảnh. Holdout đã được xem, đây là đánh giá lặp. Bảng 4.5 tái xuất nhãn người lịch sử, không phải đánh giá người/khảo sát mới. Mật độ tay vẫn là 47/184,7 = 0,254 và 32/99,2 = 0,322 hố/km², chưa khác biệt có ý nghĩa. CSV Bảng 4.4/4.5/4.6/4.7/4.8 lần lượt có 11/8/6/9/2 dòng; không thay số đo thời gian lịch sử bằng lượt này.

## 3. Kiểm đủ bộ và người xử lý

“Chưa nhận” áp dụng đầu vào cung cấp/tìm thấy trong lượt này, không khẳng định thành viên chưa làm ở nơi khác. Người xử lý theo phân công hiện có, chưa phải xác nhận nhận việc hoặc chữ ký thay thành viên.

| Sản phẩm | Trạng thái | Người xử lý/điều kiện chốt |
|---|---|---|
| Repo/README/requirements/script | Có, kỹ thuật đạt | Tiến kiểm hash sau tích hợp; Đức chốt commit |
| Dữ liệu/cấu hình/nhãn | Có bundle ngoại tuyến, hash đạt | Tiến dùng nguồn sạch, tránh ảnh cũ local; giữ tham số đã chốt |
| PDF cuối | **Chưa kiểm được**; chỉ dựng DOCX thử | Đức/S3-12 nhận PDF, kiểm mở được, 5 chương, 25–40 trang chính, tổng 30–60 trang và dàn trang đúng nguồn cuối |
| Nội dung báo cáo | **14 dấu chờ**: mở đầu 1, Chương 4: 2, Chương 5: 1, phụ lục 10 | Chủ phần/cả nhóm hoàn thiện, tự xác nhận AI, tỷ lệ và chữ ký |
| Slide cuối 15–20 trang | **Chưa nhận** | Hưng/S3-11; file giới thiệu ở thư mục cha có 10 slide, ZIP/CRC hợp lệ nhưng là ý tưởng/dự kiến, không coi là bản cuối |
| Video 5–7 phút | **Chưa nhận** | Quốc Anh/S3-13 giao tệp, kiểm thời lượng/nội dung/phiên bản |
| Đánh giá chéo | Khung còn **17 dấu chờ**, chưa có bản xác nhận | Mỗi người hoàn thiện dòng của mình; Đức nhận bản cuối |
| Phân công/tỷ lệ/chữ ký | Chưa nhận bản ký, mở đầu còn ô chờ | Bốn thành viên tự xác nhận, tổng tỷ lệ 100 % và ký thật |
| Bộ cuối/triển khai/dự phòng | **Chưa xác minh** | Đức/S3-16 ghép cùng commit, nhận file bổ sung, đối chiếu manifest/checksum và mở bản sao |

Giữ các hạn chế học phần theo [S3-12](bao_cao/README.md) và [S3-16](S3-16_BAN_GIAO.md); kiểm kỹ thuật không thay khảo sát hoặc xác nhận thành viên.

## 4. Danh sách lỗi và việc còn lại

| Mã | Mức/Trạng thái | Mô tả và xử lý | Người xử lý theo phân công |
|---|---|---|---|
| R14-01 | Cao — **đã sửa, kiểm lại đạt** | Tên `python.exe` trên PATH gọi nhầm Python cha trên Windows; dùng `shutil.which`/`abspath`, giữ symlink venv. 15 test đóng gói và 370 test đạt | Tiến; Đức đọc lại khi tích hợp |
| R14-02 | Local — **đã có cách chạy sạch** | Script số học từ chối 27 ảnh do `moon_ap15_hia_crop01.npy` cũ ngoài bundle. Cài đúng 26 ảnh vào nguồn sạch và kiểm lại đạt; không xóa/đổi ảnh cũ của người dùng | Tiến |
| R14-03 | Chặn nghiệm thu — **mở** | Thiếu PDF cuối được duyệt; Word quá thời gian. Dựng trong môi trường LibreOffice chuẩn hoặc nhận bản Word đã cập nhật mục lục/xuất PDF, kiểm trang/dàn trang | Đức |
| R14-04 | Chặn nghiệm thu — **mở** | Slide tìm thấy chỉ là giới thiệu 10 trang; cần bản cuối 15–20 trang đúng kết quả/giới hạn | Hưng |
| R14-05 | Chặn nghiệm thu — **mở** | Chưa có video 5–7 phút để kiểm mở được, thời lượng, chức năng và phiên bản | Quốc Anh |
| R14-06 | Chặn nghiệm thu — **mở** | Dấu chờ báo cáo/đánh giá, tỷ lệ/chữ ký và khai AI còn thiếu; từng tác giả tự hoàn thiện | Cả nhóm; Đức điều phối |
| R14-07 | Chặn nghiệm thu — **mở** | Chưa đối chiếu phiên bản bộ cuối/triển khai/dự phòng. Nhận đủ, chốt SHA, đóng gói S3-16, kiểm hash và mở tệp | Đức; Tiến kiểm lại |

## 5. Bàn giao và kiểm lại

Có thể dùng demo local và bằng chứng kỹ thuật để chuẩn bị S3-15; chưa đủ căn cứ ghi bộ nộp cuối sẵn sàng. Người điều phối nhận R14-03–R14-07, bổ sung file và cho Tiến kiểm lại phiên bản trước nghiệm thu. Không tạo số liệu, chữ ký hoặc xác nhận thay thành viên. Không sửa Excel, push, tạo PR, merge hay deploy trong lượt này.

Từ nguồn sạch và venv Python 3.12 theo [README](../README.md), dùng đầu ra mới:

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -X utf8 -B scripts/reproduce_s310.py --output outputs/s314_recheck --repeats 3
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_contracts.py
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
Get-ChildItem tests/test_canvas_*.js | ForEach-Object { node $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Canvas test failed" } }
```

Kiểm `manifest.json: complete/full`, `chapter4_tables/index.json: complete`, hash, đầu vào/cấu hình và số đếm/TP/FN. Không yêu cầu trùng thời gian/PNG giữa môi trường. Script số học cần riêng đúng 26 ảnh bundle; log lỗi local và nguồn sạch được giữ trong [bằng chứng](evidence/s3-14/README.md). Kiểm Chromium bằng `scripts/check_s213_app.py`, Streamlit cổng 8621 và `--out` mới; script có thể lưu lượt chấm trong `outputs/`.
