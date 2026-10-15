# NASA 24 — Nhóm 2

Phát hiện hố va chạm và trò chơi STEM cho học sinh.

Repo chứa khung dùng chung S1-05 và các phần triển khai của Sprint 1: bộ ảnh S1-06, Hough NumPy S1-07, tiền xử lý B0–B8 S1-08 và giao diện khoanh hố S1-09. Chấm điểm, đánh giá và tích hợp phát hiện hố thuộc các đầu việc tiếp theo; những hàm chưa cài đặt báo `NotImplementedError`.

## Mở giao diện khoanh hố S1-09

Sau khi cài môi trường bên dưới, chạy từ thư mục repo:

```bash
python scripts/install_s106_dataset.py
python -m streamlit run app.py --server.address 127.0.0.1
```

Mở địa chỉ local Streamlit in ra (mặc định `http://127.0.0.1:8501`). Chọn một trong 26 ảnh, kéo từ tâm ra vành để vẽ; chọn **Chọn / sửa** để di chuyển tâm, đổi bán kính hoặc xóa. Có thể nhập tọa độ chính xác rồi tải JSON hoặc lưu câu trả lời vào `outputs/player_answers/`. Nếu bộ ảnh chưa được giải nén, giao diện có nút chuẩn bị ảnh ngoại tuyến.

Tọa độ luôn theo ảnh 512×512, kể cả khi cửa sổ hiển thị nhỏ hơn. Bản nháp từng ảnh giữ trong phiên đang mở; cần lưu hoặc tải JSON trước khi đóng trang. Đây là câu trả lời `source=player`, chưa có chấm điểm hoặc danh mục hố tham chiếu. Xem [hướng dẫn S1-09](docs/S1-09_GIAO_DIEN_KHOANH_HO.md).

UI v2 dùng thiết kế Claude Design: ảnh bên trái, bảng vòng/chỉnh/lưu bên phải; trên điện thoại các phần xếp dọc. Nút **Lưu trên máy** màu vàng lưu đúng bản nháp hiện tại và báo đường dẫn tương đối. Xem [mẫu thiết kế](docs/ui-design/mockup.html) và [nghiệm thu UI v2](docs/S1-09_UI_V2_NGHIEM_THU.md).

## Chạy kiểm tra khung repo

Checker và kiểm tra hợp đồng dưới đây chỉ dùng thư viện chuẩn Python 3.10 trở lên:

```bash
python3 scripts/check_contracts.py
python3 -m unittest discover -s tests -p 'test_contracts.py' -v
```

Mẫu trong `data/examples/` là dữ liệu giả lập, chỉ dùng để kiểm tra định dạng. Không dùng các mẫu này để tính độ chính xác trên ảnh NASA.

Khi bắt đầu cài thuật toán hoặc giao diện:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Trên Windows dùng `python` và kích hoạt bằng `.venv\Scripts\activate` trong CMD.

Để tái tạo môi trường kiểm tra của các PR và GitHub Actions, dùng **Python 3.12**:

```bash
python -m pip install -r requirements-test.txt
python scripts/check_contracts.py
python -m unittest discover -s tests -v
node tests/test_canvas_save.js
```

Xem [TIEN_XU_LY.md](docs/TIEN_XU_LY.md) để chạy tiền xử lý và đọc ảnh từng bước. Sau khi merge cả ba PR, xem thêm `docs/S1-06_BANG_ANH_XA_ANH_CAT.md` để lấy bộ ảnh và `docs/HOUGH.md` để chạy Hough. Ảnh thật có nguồn riêng; danh mục hố chỉ được dùng khi đã xác minh, không suy ra đáp án từ vị trí tâm ảnh.

[S1-12](docs/S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md) / [S1-15](docs/S1-15_LY_THUYET_HOUGH.md) / [References](docs/TAI_LIEU_THAM_KHAO_HOUGH.md)

## Cấu trúc thư mục

```text
nasa24-crater-stem/
├── README.md
├── requirements.txt
├── configs/default.json       # Tham số ban đầu theo S1-04
├── data/
│   ├── examples/              # Mẫu JSON giả lập để thống nhất định dạng
│   ├── raw/                   # Ảnh nguồn tải về, không đưa vào Git
│   └── processed/             # .npy/.png và metadata sau chuẩn hóa
├── src/
│   ├── contracts.py           # Định dạng và kiểm tra dữ liệu dùng chung
│   ├── preprocessing.py       # Hưng: chuỗi B0–B8, S1-08
│   ├── hough.py               # Tiến: Hough NumPy, S1-07
│   ├── postprocessing.py      # Hưng: sáng–tối và lọc trùng
│   ├── statistics.py          # Hưng: kích thước và mật độ hố
│   ├── scoring.py             # Đức: chấm với máy và danh mục riêng
│   ├── science_cards.py       # Anh/Đức: nội dung và mở thẻ
│   └── evaluation.py          # Anh/Tiến: Precision/Recall
├── app.py                     # S1-09: mở ảnh, vẽ/sửa/xóa và lưu câu trả lời
├── scripts/
│   ├── check_contracts.py     # Kiểm tra dữ liệu mẫu và lưu một bản chạy mẫu
│   ├── run_preprocessing.py   # S1-08: chạy B0–B8, lưu ảnh từng bước + tham số
│   └── synthetic_scene.py     # Cảnh hố giả lập để thử khi chưa có ảnh thật
├── tests/                     # Kiểm tra hợp đồng dữ liệu và tiền xử lý
├── outputs/                   # Kết quả chạy theo run_id, không đưa vào Git
└── docs/
    ├── DINH_DANG_DU_LIEU.md
    ├── PHAN_CONG.md
    ├── NHAT_KY_NHOM.csv
    ├── TIEN_XU_LY.md          # S1-08: cài đặt, chạy, tự viết/thư viện
    └── HUONG_DAN_GITHUB.md
```

## Chuẩn dữ liệu

- Mỗi ảnh xử lý có `image_id` duy nhất, ảnh 512×512 và file JSON metadata cùng tên.
- `x` là cột, tăng sang phải; `y` là hàng, tăng xuống dưới; gốc ở góc trên trái. Tâm và bán kính dùng pixel của ảnh xử lý.
- Dùng cùng `image_id` cho metadata, kết quả máy, danh mục và câu trả lời người chơi.
- Ảnh xử lý dùng `float32` trong [0, 1]; ảnh biên và mặt nạ hợp lệ dùng `bool`.
- Tâm, bán kính trong danh mục phải được đổi sang hệ tọa độ này trước khi đánh giá.

Xem [định dạng dữ liệu](docs/DINH_DANG_DU_LIEU.md) và các mẫu JSON trong `data/examples/` trước khi viết module.

## Cách làm việc

Một đầu việc dùng một nhánh, ví dụ `s1-07-hough-numpy` hoặc `s1-08-preprocessing`. Mỗi người tự commit phần mình làm, ghi mã việc trong commit, cập nhật nhật ký và mở Pull Request để người phối hợp kiểm tra. Đức tích hợp các phần vào `main`.

Đầu ra S1-05 chỉ được nhóm nghiệm thu khi Hưng và Tiến cùng xác nhận chuẩn metadata, ảnh biên và danh sách hố dùng được cho phần của họ. Sau đó ghi link repo vào `Giao_viec!O12` và cập nhật trạng thái tại `J12`.

## Căn cứ thiết kế

Ba tài liệu nhóm đã bàn giao được lưu trong `docs/`:

- [S1-02 — Bảng 20 nguồn ảnh](<docs/S1-02_Bang_20_anh_nguon (1).docx>)
- [S1-03 — Ghi chú Hough tròn, tiền xử lý và tài liệu](<docs/S1-03 — GHI CHÚ HOUGH TRÒN, TIỀN XỬ LÝ VÀ TÀI LIỆU.docx>)
- [S1-04 — Đặc tả tiền xử lý](docs/S1-04_Dac_ta_tien_xu_ly.docx)

Nhấp vào tên tài liệu rồi tải file DOCX để đọc bằng Word hoặc LibreOffice. S1-04 là căn cứ cho kích thước, kiểu dữ liệu, hướng nắng và quy đổi bán kính.

## Đưa repo lên GitHub

Repo local dùng nhánh `main`. Hướng dẫn từng bước, đúng tài khoản `Duckcy-Bui`, nằm tại [HUONG_DAN_GITHUB.md](docs/HUONG_DAN_GITHUB.md).

## Bộ ảnh S1-06

Repo chứa bundle ngoại tuyến 26 ảnh LROC thật, kèm metadata và mặt nạ. Sau khi cài thư viện, chạy `python scripts/install_s106_dataset.py` để xác minh và giải nén vào `data/processed/`. Xem [hướng dẫn dữ liệu](docs/S1-06_HUONG_DAN_DU_LIEU.md) và [bảng ánh xạ](docs/S1-06_BANG_ANH_XA_ANH_CAT.md).

Bundle là ảnh browse cho demo môn học; chưa có danh mục hố đã xác minh. Không dùng nhãn giả hoặc danh mục thiếu để chấm Precision/Recall hay điểm danh mục. Môi trường kiểm tra cố định dùng Python 3.12 và `requirements-test.txt`; các test dataset tự kiểm tra bundle trong Git, không phụ thuộc file ảnh đã giải nén trên máy.
