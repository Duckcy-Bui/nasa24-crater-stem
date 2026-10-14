# S1-09 — Hồ sơ bàn giao để nghiệm thu

Người lập: nasa24-dev. Nhánh: `s1-09-interface`. Đây là tổng hợp bằng chứng hiện có, chưa phải quyết định nghiệm thu; nasa24-qa rà độc lập trước khi lead xác nhận.

## Phạm vi

Mở/chọn bộ 26 ảnh LROC S1-06; vẽ, sửa tâm/bán kính, xóa vòng tròn; quy đổi thao tác trên ảnh hiển thị về tọa độ ảnh 512×512; tải JSON hoặc lưu câu trả lời trên máy. `x` tăng sang phải, `y` tăng xuống dưới, gốc góc trên trái; `r` tính bằng pixel ảnh 512×512. Căn cứ: [README](../README.md) và [hướng dẫn S1-09](S1-09_GIAO_DIEN_KHOANH_HO.md).

## Lệnh chạy và kiểm

Từ thư mục repo, dùng Python 3.12 và Node cho kiểm tra hình học:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python scripts/install_s106_dataset.py
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Mở `http://127.0.0.1:8501`. Các lệnh kiểm dưới đây chạy ở terminal riêng với cùng môi trường:

```bash
python scripts/check_contracts.py
python -m unittest discover -s tests -v
node tests/test_canvas_geometry.js
```

## Kết quả trong bằng chứng hiện có

| Nội dung | Kết quả được ghi nhận | Bằng chứng |
| --- | --- | --- |
| Toàn bộ unittest repo | 107 tests, 0 skip; `OK`, 4.977 giây | [unittest.log](evidence/s1-09/unittest.log) |
| Vẽ desktop, tọa độ gốc, tải JSON | PASS | [browser_checks.json](evidence/s1-09/browser_checks.json) |
| Viewport 390px, vẽ vòng thứ hai độc lập | PASS | Cùng báo cáo trình duyệt |
| Sửa bằng số, giá trị lưu chính xác | PASS | Cùng báo cáo trình duyệt |
| Kéo tâm, đổi bán kính sau đổi viewport | PASS | Cùng báo cáo trình duyệt |
| Xóa vòng đã chọn, giữ ID vòng còn lại | PASS | Cùng báo cáo trình duyệt |
| A → B → A; sửa rồi đổi ảnh ngay, khôi phục draft đúng ảnh | PASS | Cùng báo cáo trình duyệt |
| Lưu trên máy, đọc lại khớp JSON tải xuống | PASS | Cùng báo cáo trình duyệt |

Báo cáo browser có `status=PASS`, 7 checks, `errors=[]`. Agent lập tài liệu chỉ đọc bằng chứng; lead đã trực tiếp chạy unittest và thử trên Chromium. Hai file này không có kết quả chạy riêng của checker/Node để ghi PASS riêng. Các phép thử browser dùng vòng tròn thao tác thử, không tạo danh mục hố tham chiếu.

## Hạn chế và bàn giao S1-13

Chưa chấm điểm, chưa chạy Hough trong giao diện; bộ ảnh chưa có danh mục hố xác minh (`reference_status=unavailable`). Vòng người chơi và danh sách rỗng không được dùng làm đáp án tham chiếu. Draft chỉ giữ trong phiên Streamlit; phải lưu/tải JSON trước khi đóng tab, tải lại trang hoặc khởi động lại server. Chưa có nút nhập lại JSON; lịch sử hoàn tác làm mới khi đổi ảnh.

Bàn giao JSON schema 1.0, `source=player`, `reference_source=null`, giữ đúng `image_id` và `data_kind` từ metadata. Lưu trên máy tạo từng run tại `outputs/player_answers/player_<UTC>_<id_ngẫu_nhiên>/`, gồm `craters.json`, `metadata.json`, `params.json`, `run.json`; kết quả không đưa vào Git. S1-13 dùng lại `build_player_crater_set`, `apply_canvas_event`, `save_player_answers` trong `src/player_annotations.py`, ghép với phát hiện hố theo cùng image_id và hệ tọa độ; chỉ tích hợp chấm điểm khi nhóm thống nhất dữ liệu tham chiếu. Hồ sơ và các tệp bằng chứng đã được đưa vào repo để người phối hợp xem và nghiệm thu trước khi merge.

## Ảnh giao diện

[Máy tính](evidence/s1-09/final_desktop.png) · [Màn hình rộng 390px](evidence/s1-09/final_mobile.png). Ảnh chụp trang mới mở, chưa có câu trả lời người chơi.
