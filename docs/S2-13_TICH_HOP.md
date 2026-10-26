# S2-13 — Tích hợp bốn chức năng và kiểm tra luồng sử dụng (khung)

Phụ trách: Bùi Hải Đức; phối hợp: cả nhóm. Mã: `src/integration.py`, `app.py` (`show_statistics`, `show_cards`). Test: `tests/test_integration.py`.

Trạng thái 26/10/2026: **khung đã ghép một phần.** Phát hiện (S1-07/08/11), trò chơi (S1-09, S2-04, S2-08) và thẻ khoa học S2-10 đã chạy. S2-10 trả thẻ vùng có nguồn cho Apollo 15/16 và Lunokhod 1/2, với `position=null` khi thiết bị nằm ngoài crop; app tự hiện thẻ mà không vẽ pin giả. Thống kê S2-09 vẫn báo `NotImplementedError` và app ghi "chưa có" thay vì tự tạo số liệu.

## 1. Hợp đồng cho S2-09 và S2-10 (đề xuất, Hưng và Quốc Anh xác nhận)

### `statistics.summarize(crater_set, metadata, valid_pixel_count) -> dict` (S2-09)

App gọi với ứng viên máy của lượt chấm gần nhất và số pixel hợp lệ của ảnh (`valid_mask`).

| Khóa | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `count` | int ≥ 0 | có | số hố trong `crater_set` được đếm |
| `valid_area_km2` | số ≥ 0 hoặc null | không | `valid_pixel_count × scale² / 1e6` |
| `density_per_km2` | số ≥ 0 hoặc null | không | null khi diện tích bằng 0 |
| `histogram` | `{bin_edges_m: [n+1 số tăng dần], counts: [n số nguyên ≥ 0]}` | không | đường kính `2 × r × scale` (m) |
| `limitations` | list chuỗi | không | app hiện nguyên văn dưới biểu đồ |

Có thể thêm khóa khác (ví dụ so hai vùng); app bỏ qua khóa lạ. Sai hợp đồng thì app báo lỗi đỏ, không hiện số.

### `science_cards.cards_for_image(image_id) -> list[dict]` (S2-10)

| Khóa | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `card_id`, `title`, `body`, `source_title` | chuỗi không rỗng | có | |
| `source_url` | link `http(s)` | có | thẻ không có nguồn không được hiện |
| `position` | `{x, y}` trong 0–511 hoặc null | không | vị trí thật trên ảnh 512×512 (hệ tọa độ S1-05); null nếu thẻ nói về cả vùng |

Ảnh không có thẻ thì trả `[]`. Thẻ sai hợp đồng bị ẩn và liệt kê lý do trong một cảnh báo.

## 2. Kiểm tra luồng sử dụng (Chromium, 22/10/2026)

| Bước | Kết quả |
|---|---|
| Mở `moon_ap15_hia_c01`, vẽ 2 vòng bằng chuột, lưu trên máy | Lưu 2 vòng vào `outputs/player_answers/` |
| Chấm bài lần đầu | 6,4 s; 100 ứng viên máy; "Chưa có điểm" vì ảnh không có nhãn |
| Đổi sang `moon_ap16_m106777343r_c01` (2 m/px) | Canvas mở đúng ảnh và tỉ lệ; không lẫn kết quả của ảnh trước |
| Vẽ 1 vòng, chấm bài | 7,8 s; nhãn S1-10 có nhưng `unreviewed` nên không chấm, có ghi lý do |
| Quay lại ảnh đầu | Còn đủ 2 vòng và kết quả chấm cũ |
| Thống kê, thẻ khoa học | Hiện "chưa có" kèm mã việc S2-09, S2-10 |
| Lỗi trang / lỗi Streamlit | 0 / 0 |

Ngoài ra `tests/test_integration.py` chạy app với `summarize` và `cards_for_image` giả đúng hợp đồng: số liệu, biểu đồ và thẻ có nguồn hiện đúng.

## 3. Danh sách lỗi cần sửa

| # | Lỗi | Mức | Người | Đề xuất |
|---|---|---|---|---|
| 1 | Canvas đặt mép trái pixel ở tọa độ 0, nên bấm vào giữa pixel 200 ghi x = 200,5. Hợp đồng S1-05 (`DINH_DANG_DU_LIEU.md`: "tâm pixel có tọa độ nguyên") và Hough dùng tâm pixel = 200. Vòng người chơi lệch +0,5 px so với máy và nhãn. | Thấp: nhỏ hơn nhiều ngưỡng ghép 0,5 r ≥ 2,5 px, nhưng sai hợp đồng | Đức | Sửa `canvasToImage`/`imageToScreen` trong `geometry.js` (trừ/cộng 0,5) kèm test JS; PR riêng |
| 2 | Máy chạm trần 100 ứng viên trên cả 26 ảnh, nên "Chỉ máy có" luôn khoảng 100 và thống kê sẽ đếm ứng viên thô | Cao cho thống kê và thí nghiệm | Tiến, Hưng | S2-01, S2-02, S2-05 |
| 3 | Chưa ảnh nào có nhãn đã kiểm chéo, nên trò chơi chưa ra điểm | Cao cho khảo sát | Tiến (S1-10), Quốc Anh (S2-03) | Kiểm chéo 4 nhãn S1-10, bổ sung nhãn cho ảnh dùng khi khảo sát |
| 4 | Thống kê chưa có; thẻ S2-10 không có pin vì thiết bị ngoài crop | Cao cho thống kê; giới hạn minh bạch cho thẻ | Hưng (S2-09), Quốc Anh (S2-10) | Cài S2-09; muốn pin cần crop mới bao phủ thiết bị |
| 5 | Đổi ảnh rồi quay lại thì mất lịch sử hoàn tác (vòng vẫn còn) | Thấp | Đức | Ghi vào S3-04 |
| 6 | Chấm bài lần đầu mỗi ảnh mất 6–8 s trên máy dev; VPS giới hạn 1 CPU có thể chậm hơn | Trung bình khi khảo sát nhiều người cùng lúc | Đức | Đo trên VPS sau khi deploy; nếu chậm thì tính sẵn ứng viên máy cho các ảnh dùng khi khảo sát |

## 4. Việc còn lại để đóng S2-13

- Merge S2-09, chạy lại bảng mục 2 với số liệu; muốn kiểm pin S2-10 thì cần crop mới bao phủ thiết bị.
- Sửa lỗi #1; đo lỗi #6 trên VPS.
