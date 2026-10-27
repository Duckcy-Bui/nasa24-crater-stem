# S2-08 — Màn hình kết quả và lưu lượt chấm

Phụ trách: Bùi Hải Đức; phối hợp: Hoàng Quốc Anh. Mã: `app.py` (`render_results`, `show_result`), `src/game_results.py`, `src/pipeline.py` (`detect_machine`). Test: `tests/test_game_results.py`. Dựa trên S2-04 (`docs/S2-04_CHAM_DIEM.md`).

## 1. Luồng

1. Người chơi khoanh hố trên canvas như S1-09.
2. Bấm **Chấm bài** dưới bản đồ. Máy chạy tiền xử lý, Hough NumPy và chấm sáng–tối S1-11 trên ảnh đang mở (5–10 giây; kết quả máy được giữ trong cache theo ảnh).
3. Câu trả lời hiện tại được chấm bằng `score_player` (S2-04) và lưu thành một lượt mới.
4. Nếu người chơi sửa vòng sau khi chấm, màn hình báo kết quả đã cũ và nhắc chấm lại.

## 2. Màn hình hiện gì

| Phần | Nội dung |
|---|---|
| Ảnh đối chiếu | Ảnh 512×512 phóng 3 lần (từ S3-04, để vòng nằm đúng tâm pixel): vòng người chơi (xanh, cùng màu canvas), ứng viên máy (tím, nét mảnh), nhãn tham chiếu (cam) |
| Điểm | Chỉ khi ảnh có nhãn đã kiểm chéo: điểm, số hố tìm đúng, bỏ sót (và khoanh sai nếu nhãn đầy đủ). Không có thì ghi rõ lý do, không hiện số giả |
| So với máy | Trùng máy, chỉ bạn khoanh, chỉ máy có; ghi rõ máy không phải đáp án |
| Phạm vi chấm | Dải bán kính máy thật sự tìm (metadata kẹp trong giới hạn Hough), đổi ra đường kính mét, bước lưới và số bán kính; cảnh báo khi bước > 2 px; báo khi máy chạm trần `max_circles` |
| Lưu/xuất | Đường dẫn lượt đã lưu và nút tải `score.json` |

Màn hình không dùng bảng dữ liệu (dataframe), nên không có lỗi Arrow khi trộn số với ô trống.

## 3. Một lượt lưu gồm gì

`outputs/player_scores/score_<image_id>_<UTC>_<id>/`, không ghi đè lượt cũ; lỗi giữa chừng thì xóa thư mục dở:

- `metadata.json`, `run.json` (image_id, thời gian UTC, phiên bản mã), `craters.json` (vòng người chơi, `source=player`);
- `params.json`: tham số Hough, quy tắc ghép, trạng thái S1-11 và `radius_scope` (dải bán kính, bước lưới);
- `machine.json` (ứng viên máy), `score.json` (kết quả S2-04), `reference.json` nếu ảnh có nhãn.

## 4. Kiểm tra

- `tests/test_game_results.py`: dải bán kính và cảnh báo lưới thưa, lượt chấm không sửa vòng máy, lưu hai lượt thành hai thư mục, ảnh đối chiếu; màn hình trong app (AppTest, thay Hough bằng ứng viên cố định) hiện đúng số và lưu đúng một lượt, báo kết quả cũ khi sửa vòng.
- Trình duyệt thật (Chromium, 22/10/2026) trên `moon_ap15_hia_c01` với 2 vòng vẽ bằng chuột: không lỗi, máy 100 ứng viên (chạm trần), 0 trùng. Ảnh: `docs/evidence/s2-08/ket_qua_desktop.png`, `docs/evidence/s2-08/ket_qua_mobile_390.png`. Các vòng trong ảnh chỉ để thử giao diện, không phải nhãn hố.

## 5. Hạn chế

- Hiện chưa ảnh nào có nhãn đã kiểm chéo, nên màn hình chỉ hiện phần so với máy cho tới khi S1-10 được kiểm chéo.
- Máy chạm trần 100 ứng viên trên mọi ảnh (S1-13), nên số "chỉ máy có" lớn; việc giảm ứng viên thuộc S2-01/S2-02/S2-05.
