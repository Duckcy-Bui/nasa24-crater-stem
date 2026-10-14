# NASA 24 — Nhóm 2

Phát hiện hố va chạm và trò chơi STEM cho học sinh.

Repo này là đầu ra S1-05: cấu trúc mã nguồn, định dạng dữ liệu dùng chung, mẫu lưu tham số/kết quả và quy tắc phối hợp. Thuật toán Hough, chuỗi tiền xử lý và ứng dụng giao diện sẽ được các thành viên cài đặt ở các đầu việc tiếp theo. Những hàm chưa cài đặt báo `NotImplementedError`, không trả kết quả đặt sẵn.

## Chạy kiểm tra khung repo

Từ thư mục repo, chạy hai lệnh dưới đây với Python 3.10 trở lên. Hai lệnh này chỉ dùng thư viện chuẩn Python, chưa cần cài thư viện xử lý ảnh:

```bash
python3 scripts/check_contracts.py
python3 -m unittest discover -s tests -v
```

Kết quả mong đợi: các mẫu metadata/danh sách hố hợp lệ và các kiểm tra đạt. Mẫu trong `data/examples/` là dữ liệu giả lập; repo chưa có bộ ảnh thật đã khớp danh mục.

Khi bắt đầu cài thuật toán hoặc giao diện:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Trên Windows dùng `python` và kích hoạt bằng `.venv\Scripts\activate` trong CMD.

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
├── app.py                     # Điểm vào giao diện, sẽ cài ở S1-09
├── scripts/check_contracts.py # Kiểm tra dữ liệu mẫu và lưu một bản chạy mẫu
├── tests/                     # Kiểm tra hợp đồng dữ liệu
├── outputs/                   # Kết quả chạy theo run_id, không đưa vào Git
└── docs/
    ├── DINH_DANG_DU_LIEU.md
    ├── PHAN_CONG.md
    ├── NHAT_KY_NHOM.csv
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
