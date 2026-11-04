# NASA 24 — Nhóm 2

Phát hiện ứng viên hố va chạm bằng Hough tròn NumPy và trò chơi STEM: khoanh hố, chấm bài, xem thống kê kích thước/mật độ và thẻ khoa học. Tiền xử lý B0–B8, Hough, sáng–tối, ghép một–một và chấm điểm đã được triển khai.

Game dùng `configs/default.json`, giống `configs/s215_frozen.json`: chính sách `score`, sáng–tối chỉ gắn nhãn, không bật lọc trùng. S2-15 trên 18 ảnh tuning đạt Recall_known 10/174 = 5,75%; chất lượng phát hiện còn thấp. Vòng máy là ứng viên. Nhãn thưa đã kiểm chéo chỉ cho phép báo Recall trên nhãn đã biết; FP/Precision/F1 toàn ảnh chưa xác định.

## Cài môi trường và mở demo

Chạy từ gốc repo với **Python 3.12** và Git; Node.js 24 nếu kiểm canvas. `requirements-test.txt` cố định phiên bản phụ thuộc trực tiếp đã kiểm chứng; `requirements.txt` dùng cài thông thường. Repo chứa bundle ảnh ngoại tuyến, không cần tải ảnh NASA qua mạng.

Windows PowerShell (gọi Python trong venv, không cần đổi ExecutionPolicy):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -X utf8 -B scripts/install_s106_dataset.py
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python -X utf8 -B scripts/install_s106_dataset.py
python -m streamlit run app.py --server.address 127.0.0.1
```

Mở `http://127.0.0.1:8501`, chọn ảnh, kéo từ tâm ra vành; chọn/sửa/xóa vòng rồi **Chấm bài**. Lưu hoặc tải JSON trước khi đóng phiên. Tọa độ theo ảnh 512×512, không phụ thuộc kích thước hiển thị. Xem [giao diện](docs/S1-09_GIAO_DIEN_KHOANH_HO.md), [chấm bài](docs/S2-08_MAN_HINH_KET_QUA.md) và [giới hạn tích hợp](docs/S2-13_TICH_HOP.md).

## Một lệnh tái tạo bảng kết quả (S3-10)

Sau khi cài môi trường:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/reproduce_s310.py
```

Linux/macOS sau khi kích hoạt venv:

```bash
python -X utf8 -B scripts/reproduce_s310.py
```

Chế độ full mặc định tạo đủ năm CSV cho các bảng kết quả Chương 4 hiện tại (4.4–4.8). Script giữ các bước cũ: xác minh/giải nén 26 ảnh, kiểm ví dụ tính tay/giả lập, S2-15 trên 18 tuning, đối chiếu Hough 3 tuning/8 holdout, S2-07 trên 3 tuning/2 holdout và thống kê hai vùng. Sau đó chạy riêng S3-05, chụp hồ sơ lọc nhãn mù lịch sử và kết xuất bảng. Đầu ra mới tại `outputs/s310_<UTC>/`; dùng `--output outputs/s310_full` để đặt tên, thư mục phải chưa tồn tại. Chạy đầy đủ có thể mất nhiều phút tùy CPU. Đối chiếu Hough warm-up một lượt, đo ba lượt; `--repeats 1` không dùng kết luận tốc độ.

| Đầu ra trong thư mục lượt chạy | Nội dung |
|---|---|
| `manifest.json`, `*.log` | Trạng thái, lệnh từng bước, môi trường, seed, commit nền và hash byte thực tế của mã/dữ liệu/kết quả |
| `game_config.json`, `comparison_config.json` | Snapshot game S2-15 và phép đối chiếu S2-06, ghi riêng trước khi chạy |
| `synthetic/` | Ví dụ 5×5, đối chiếu NumPy/OpenCV trên ảnh giả lập, JSON/CSV/PNG |
| `frozen_tuning.csv`, `frozen_tuning/report.json` | TP/FN/Recall_known từng ảnh và tổng hợp 18 tuning S2-15 |
| `evaluation_tuning/results.csv`, `evaluation_holdout/results.csv` | Bảng đánh giá S2-06/S3-02; JSON `summary.json` cung cấp cả số vòng, dùng cho Bảng 4.6–4.7 |
| `E1.csv`, `E2.csv`, `E3.csv`, `experiments_*.json` | Đầu ra S2-07 cũ, giữ nguyên namespace và ý nghĩa; không tráo với S3-05 |
| `density/` | Bảng đếm, máy so với tay, mật độ và hình histogram/tích lũy/vùng đếm S2-09 |
| `s305/` | S3-05 chạy mới: CSV/JSON/ảnh E1/E2/E3, cấu hình và report; chỉ quét tham số trên tuning, Mare chỉ mô tả nền |
| `blind_filter/` | Bản sao đúng byte hai `docs/evidence/s2-02/<image_id>/report.json`, SHA nguồn và `filters.csv`; nhãn mù lịch sử, không phải đánh giá mới của người |
| `chapter4_tables/` | Năm CSV dưới đây và `index.json`: số bảng, nguồn/SHA, cách làm tròn, nguồn lịch sử hay lượt mới |

| CSV trong `chapter4_tables/` | Bảng báo cáo và phạm vi |
|---|---|
| `table_4_4.csv` | S3-05 gộp: 11 dòng nhánh, tương ứng bốn nhóm trình bày; E1 chỉ hai ảnh đủ nắng, E2/E3 ba tuning, Mare E3 nền |
| `table_4_5.csv` | Lọc nhãn mù: bốn cách × hai ảnh, đọc hồ sơ S2-02. STT 17 không chấm lọc sáng–tối, ô loại/mất hố để trống |
| `table_4_6.csv` | Sáu nhóm so Hough, 3 tuning/8 holdout; trung bình ± SD mẫu theo ảnh dùng `scripts/ch4_mean_sd.py`, không phải SD thời gian |
| `table_4_7.csv` | Tám ảnh holdout và tổng TP/FN; số vòng OpenCV lấy từ JSON |
| `table_4_8.csv` | Hai vùng đếm tay: diện tích, N, mật độ và CI95; làm tròn từ JSON chính xác |

Chỉ dùng lượt `manifest.json: status=complete, mode=full` và `chapter4_tables/index.json: status=complete` cho bộ bảng đầy đủ. Bảng 4.1–4.2 là kiểm kê đầu vào, 4.3 là thiết kế thí nghiệm. Bảng 4.5 tái kết xuất đánh giá người đã lưu; không gọi CLI S2-02 vì CLI đó ghi vào hồ sơ/nhãn lịch sử. Lỗi dừng pipeline và ghi `failed`. Kiểm nhanh giữ phạm vi cũ, bỏ hai bước đánh giá/thí nghiệm holdout và ba bước mới; bước mật độ vẫn dùng các ô hai vùng như trước:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/reproduce_s310.py --quick --repeats 1
```

Seed cố định 0 (`PYTHONHASHSEED`) trước khi khởi động từng Python con; cảnh giả lập dựng cố định và Hough không lấy mẫu ngẫu nhiên. Các producer dùng OpenCV đặt `cv2.setNumThreads(1)`, gồm S2-07/S2-09/S3-05. Thời gian, timestamp và đường dẫn thay đổi theo máy; so số vòng/TP/FN/cặp ghép và cấu hình, không đòi PNG/NPZ trùng hash giữa môi trường. Holdout đã xem nên đây là **đánh giá lặp**; không chọn lại tham số. Balanced và các bộ lọc là nhánh thí nghiệm; giảm vòng chưa chứng minh giảm FP. Mật độ máy S2-09 có lọc texture/dedupe, khác game S2-15.

S3-05 đã được ghép thành dự thảo Chương 4–5, chờ Quốc Anh duyệt; chạy lệnh không xác nhận thay chủ phần. Không tạo số liệu khảo sát hoặc chốt tham số mới. Hồ sơ lịch sử trong `docs/evidence/` được giữ nguyên; mọi CSV bảng và bản sao nhãn mù mới nằm trong thư mục lượt chạy.

Biên bản [S3-14 — kiểm chạy lại và đủ bộ sản phẩm](docs/S3-14_KIEM_TRA_BAN_GIAO.md) ngày 04/11/2026: 370 test Python, 6 bộ canvas, Chromium local và 5 bảng Chương 4 đạt; đã sửa lỗi chọn Python đóng gói Windows. Bộ nộp cuối còn chờ PDF/slide/video và xác nhận thành viên.

## Dữ liệu và cấu hình

- `data/s106_bundle/`: 26 ảnh LROC browse thật, manifest/SHA-256. Installer từ chối dữ liệu khác bundle thay vì tự ghi đè. Xem [cách cài và nguồn](docs/S1-06_HUONG_DAN_DU_LIEU.md).
- `data/processed/`: ảnh float32 [0,1], metadata JSON và mask bool cùng `image_id`. `data/examples/` là mẫu giả lập, chỉ dùng kiểm hợp đồng.
- `data/reference_labels/`: nhãn thưa đã kiểm chéo; uncertain không tính vào Recall_known. `data/s203_split/manifest_split.json`: 18 tuning/8 holdout. Xem [quy tắc chia tập](docs/S2-03_TAP_DIEU_CHINH.md).
- `configs/s215_frozen.json` và `configs/default.json`: snapshot/game S2-15. `configs/s201_large_craters.json` dùng đối chiếu S2-06; script đo riêng score/balanced/OpenCV. Xem [S2-15](docs/S2-15_CHOT_THAM_SO.md), [S2-06/S3-02](docs/S2-06_S3-02_KIEM_CHUNG.md).
- x là cột sang phải, y là hàng xuống dưới; tâm pixel nguyên, gốc trên trái; bán kính theo pixel ảnh xử lý. Ghép một–một, lệch tâm ≤0,5 r_ref. Xem [hợp đồng dữ liệu](docs/DINH_DANG_DU_LIEU.md).

## Ví dụ nhỏ và kiểm tra độc lập

Ví dụ tính tay không cần ảnh NASA, không ghi file; ví dụ ảnh giả lập có ảnh kết quả:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_hough_examples.py --tiny-only
.\.venv\Scripts\python.exe -X utf8 -B scripts/demo_hough.py
```

Kiểm hợp đồng và hồi quy (Windows PowerShell):

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_contracts.py
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
Get-ChildItem tests/test_canvas_*.js | ForEach-Object { node $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Canvas test failed" } }
```

Linux/macOS dùng `python` thay đường dẫn venv; canvas chạy bằng:

```bash
for f in tests/test_canvas_*.js; do node "$f" || exit 1; done
```

[Hồ sơ S3-10](docs/S3-10_TAI_TAO_KET_QUA.md) ghi phạm vi và kết quả thực chạy. Kiểm tra tự động không thay cho Bùi Hải Đức chạy độc lập trên máy của mình.

## Mã nguồn và báo cáo

`src/` chứa thuật toán, chấm điểm, thống kê và canvas; `app.py` là giao diện Streamlit; `scripts/` là các lệnh chạy; `tests/` là kiểm hồi quy; `outputs/` chứa kết quả local không đưa vào Git. Xem [Hough](docs/HOUGH.md), [tiền xử lý](docs/TIEN_XU_LY.md), [phân công](docs/PHAN_CONG.md), [hướng dẫn GitHub](docs/HUONG_DAN_GITHUB.md).

[Báo cáo](docs/bao_cao/README.md): cài thêm `requirements-report.txt`, chạy `python scripts/build_report.py --no-pdf` để dựng DOCX. PDF cần LibreOffice/UNO theo hướng dẫn báo cáo.

Căn cứ thiết kế: [S1-02 — nguồn ảnh](<docs/S1-02_Bang_20_anh_nguon (1).docx>), [S1-03 — Hough và tài liệu](<docs/S1-03 — GHI CHÚ HOUGH TRÒN, TIỀN XỬ LÝ VÀ TÀI LIỆU.docx>), [S1-04 — đặc tả](docs/S1-04_Dac_ta_tien_xu_ly.docx).
