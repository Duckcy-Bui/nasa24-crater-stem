# S1-09 — Giao diện mở ảnh và khoanh vòng tròn

Phụ trách: **Bùi Hải Đức**. Đầu ra là giao diện local để người chơi mở ảnh, vẽ/sửa/xóa vòng tròn và lưu câu trả lời. Giao diện dùng bộ 26 ảnh LROC thật đã bàn giao ở S1-06; chưa chấm điểm và chưa chạy Hough trong giao diện.

## Cài và chạy

Chạy các lệnh từ thư mục repo, dùng Python 3.12 để khớp môi trường kiểm tra:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python scripts/install_s106_dataset.py
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Trên Windows dùng `python -m venv .venv`, rồi `.venv\Scripts\activate` trong CMD; các lệnh còn lại giống nhau. Mở `http://127.0.0.1:8501`. Lần cài thư viện cần Internet; sau khi cài, bộ ảnh và thành phần vẽ đều nằm trong repo, không tải thư viện frontend từ CDN. Nếu chưa giải nén ảnh, nút **Chuẩn bị bộ ảnh ngoại tuyến** trong giao diện sẽ kiểm tra và cài bundle. Không dùng `--overwrite` để xử lý dữ liệu bị khác; kiểm tra nguyên nhân hoặc dùng thư mục mới.

## Dùng trong buổi họp

1. Chọn một ảnh ở **Chọn ảnh để mở**. Ảnh và khu vực chụp hiển thị ngay trong danh sách.
2. Chọn **Vẽ vòng tròn**, nhấn tại tâm một hố và kéo ra vành. Bỏ chuột để ghi nhận vòng tròn. Một cú nhấn không kéo sẽ không tạo vòng tròn.
3. Chọn **Chọn / sửa**. Nhấn vào vòng tròn rồi kéo phần trong vòng để chuyển tâm, hoặc kéo vành để đổi bán kính. Khi các vòng chồng nhau, chọn vòng cần sửa trong danh sách bên dưới ảnh.
4. Có thể sửa chính xác tại **Tâm x**, **Tâm y**, **Bán kính**, rồi bấm **Áp dụng tọa độ**. Tâm thuộc 0–511, bán kính lớn hơn 0; vành có thể vượt ra ngoài mép ảnh.
5. Bấm **Xóa vòng đã chọn** để xóa một vòng. **Hoàn tác** quay lại thay đổi trước đó, tối đa 50 thay đổi trong lượt mở ảnh hiện tại.
6. Bấm **Tải câu trả lời JSON** để lấy file nhỏ gửi cho người tích hợp, hoặc **Lưu câu trả lời trên máy** để lưu một lần chạy riêng. Sau đó đổi sang ảnh khác và quay lại để thấy bản nháp vẫn giữ đúng ảnh.

Bản nháp giữ trong phiên Streamlit hiện tại, không tự lưu bền vững khi đóng tab, tải lại trang hoặc khởi động lại server. Lưu hoặc tải JSON trước khi kết thúc. Lịch sử hoàn tác làm mới khi đổi ảnh; các vòng tròn đã vẽ vẫn giữ trong bản nháp. Giao diện hiện chưa có nút nhập lại JSON đã tải.

## Dữ liệu bàn giao cho S1-13

JSON câu trả lời dùng đúng schema 1.0 đã thống nhất, lấy `image_id` và `data_kind` từ metadata ảnh đang mở:

```json
{
  "schema_version": "1.0",
  "data_kind": "real",
  "image_id": "moon_ap15_hia_c01",
  "source": "player",
  "reference_source": null,
  "circles": [
    {"crater_id": "U1", "x": 128.5, "y": 224.25, "r": 35.0,
     "confidence": null, "votes": null}
  ]
}
```

Đây là ví dụ định dạng, **không phải nhãn hố thật**. `x` tăng sang phải, `y` tăng xuống dưới; gốc góc trên trái; `r` là bán kính pixel của ảnh gốc 512×512. Thay đổi kích thước hiển thị không đổi tọa độ đã lưu. Canvas đổi tọa độ chuột theo vị trí thực tế và chiều rộng/cao phần ảnh hiển thị, không dùng trực tiếp pixel màn hình.

Nút lưu tạo thư mục riêng tại `outputs/player_answers/player_<UTC>_<id_ngẫu_nhiên>/` gồm:

- `craters.json`: câu trả lời người chơi theo schema dùng chung.
- `metadata.json`: metadata của đúng ảnh để truy nguồn và quy đổi về ảnh nguồn.
- `params.json`: phiên bản giao diện và hệ tọa độ.
- `run.json`: thời gian UTC, `run_id`, `image_id` và phiên bản mã giao diện.

Kết quả không đưa vào Git; các lần lưu có tên riêng, không ghi đè lần trước. `src/player_annotations.py` cung cấp `build_player_crater_set`, `apply_canvas_event` và `save_player_answers` để S1-13 dùng lại. Sự kiện canvas có `image_id`, khóa phiên và revision tăng dần; sự kiện cũ hoặc của ảnh khác không thay thế bản nháp hiện tại. Payload sai tâm/bán kính/ID bị từ chối trước khi lưu. Khi chuyển ảnh, ứng dụng nhận sự kiện mới nhất của ảnh trước từ trạng thái widget trước khi mở ảnh tiếp theo.

Nút tải JSON đọc trực tiếp các vòng tròn hiện tại trong canvas, gồm thay đổi vừa sửa, nên không lấy bản JSON cũ đang chờ Python chạy lại. Nút lưu trên máy vẫn nhận và kiểm tra sự kiện qua hợp đồng Python trước khi ghi dữ liệu.

## Kiểm tra khi nghiệm thu

```bash
python scripts/check_contracts.py
python -m unittest discover -s tests -v
node tests/test_canvas_geometry.js
```

Đối chiếu thêm thao tác thật trong trình duyệt: vẽ/sửa/xóa, chuyển ảnh rồi quay lại, lưu và mở `craters.json`, thu nhỏ cửa sổ rồi vẽ lại tại cùng vị trí tương đối. Ví dụ tâm tại 1/4 chiều rộng và 3/4 chiều cao phải ra `(128, 384)` trên ảnh 512×512; không lấy kích thước màn hình làm tọa độ ảnh.

Các bài kiểm tra Python/Node xác nhận hợp đồng và hình học; nghiệm thu giao diện cần cả thao tác trình duyệt. Bộ ảnh có `reference_status=unavailable`, nên không lấy các vòng tròn người chơi hay danh sách rỗng làm đáp án để chấm điểm. S1-13 sẽ ghép giao diện này với phần phát hiện hố sau khi nhóm thống nhất dữ liệu tham chiếu.
