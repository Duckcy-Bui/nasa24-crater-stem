# S2-13 — Tích hợp bốn chức năng và kiểm tra luồng sử dụng (khung)

Phụ trách: Bùi Hải Đức; phối hợp: cả nhóm. Mã: `src/integration.py`, `app.py` (`show_statistics`, `show_cards`). Test: `tests/test_integration.py`.

Trạng thái 27/10/2026: **khung đã ghép một phần.** Phát hiện (S1-07/08/11), trò chơi (S1-09, S2-04, S2-08) và thẻ khoa học S2-10 đã chạy. S2-10 trả thẻ vùng có nguồn cho Apollo 15/16 và Lunokhod 1/2, với `position=null` khi thiết bị nằm ngoài crop; app tự hiện thẻ mà không vẽ pin giả. Thống kê S2-09 đã cài (`statistics.summarize`, nhánh s2-09-mat-do): app hiện số ứng viên máy, diện tích, mật độ và histogram đúng hợp đồng mục 1.

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
| 1 | Canvas đặt mép trái pixel ở tọa độ 0, nên bấm vào giữa pixel 200 ghi x = 200,5. Hợp đồng S1-05 (`DINH_DANG_DU_LIEU.md`: "tâm pixel có tọa độ nguyên") và Hough dùng tâm pixel = 200. Vòng người chơi lệch +0,5 px so với máy và nhãn. | Thấp: nhỏ hơn nhiều ngưỡng ghép 0,5 r ≥ 2,5 px, nhưng sai hợp đồng | Đức | **Đã sửa (S3-04, 27/10).** Xem mục 3.1 |
| 2 | Máy chạm trần 100 ứng viên trên cả 26 ảnh, nên "Chỉ máy có" luôn khoảng 100 và thống kê sẽ đếm ứng viên thô | Cao cho thống kê và thí nghiệm | Tiến, Hưng | Còn mở. S2-07 đã đo: trên `moon_ap16_m109134835l_c01` cả 10 nhãn nằm trong dải tìm 5–125 px nhưng máy dừng ở 100 vòng r 5–10 px, Recall_known 0/10. Nếu không sửa kịp thì ghi là hạn chế trong báo cáo |
| 3 | Chưa ảnh nào có nhãn đã kiểm chéo, nên trò chơi chưa ra điểm | Cao cho khảo sát | Tiến (S1-10), Quốc Anh (S2-03) | **Đã có nhãn (PR #20, 26/10):** 26/26 file ghi `reviewed by Nguyen Manh Tien`, game ra điểm thật trên VPS. Còn chờ Tiến tự xác nhận trên PR #20 |
| 4 | Thống kê chưa có; thẻ S2-10 không có pin vì thiết bị ngoài crop | Cao cho thống kê; giới hạn minh bạch cho thẻ | Hưng (S2-09), Quốc Anh (S2-10) | Thẻ đã merge (PR #25) và hiện trên VPS. Thống kê S2-09 còn mở. Pin: nhóm chốt cắt crop mới hay ghi hạn chế |
| 5 | Đổi ảnh rồi quay lại thì mất lịch sử hoàn tác (vòng vẫn còn) | Thấp | Đức | Chưa sửa, có chủ đích. Mỗi ảnh là một component riêng (`key=player_canvas_<image_id>`), nên iframe của ảnh cũ bị hủy khi đổi ảnh. Muốn giữ lịch sử phải lưu ra ngoài iframe (sessionStorage hoặc Python), thêm rủi ro ngay trước khảo sát cho một lỗi mức thấp |
| 6 | Chấm bài lần đầu mỗi ảnh mất 6–8 s trên máy dev; VPS giới hạn 1 CPU có thể chậm hơn | Trung bình khi khảo sát nhiều người cùng lúc | Đức | Đã đo trên VPS (26/10): 9,4 s cho lượt chấm đầu trên `moon_ap15_hia_c01`. Ứng viên máy được cache trong tiến trình (`machine_for_image`, tối đa 8 ảnh) đến khi khởi động lại service. Cách xử lý khi khảo sát: sau khi deploy, người điều phối bấm Chấm bài một lần trên mỗi ảnh dùng khảo sát (≤ 8 ảnh) để làm nóng cache |
| 7 | Link nguồn trong thẻ khoa học màu xanh đậm mặc định của Streamlit, gần như không đọc được trên nền tối | Thấp | Đức | **Đã sửa (S3-04, 27/10):** `app.css` đặt link trong khối văn bản thành `#8cc8ff`, tương phản 9,7–11:1 |
| 8 | Nút đổi bán kính của vòng đang chọn vẽ tại `min(511, x + r)`: khi vành vượt mép phải, nút không nằm trên vành, bấm vào đó sẽ dời vòng thay vì đổi bán kính | Thấp | Đức | Chưa sửa; đổi bán kính bằng ô nhập số hoặc kéo vành ở phía khác |

### 3.1. Lỗi #1: quy ước tâm pixel trên canvas và ảnh đối chiếu

Trước khi sửa, canvas và ảnh đối chiếu kết quả dùng **mép** pixel làm tọa độ: pixel i phủ đoạn [i, i + 1), nên bấm vào giữa pixel 200 ghi x = 200,5. Hough, công cụ gán nhãn (`scripts/label_craters.py`, `extent=[-0.5, 511.5, 511.5, -0.5]`) và các hình của pipeline đều dùng **tâm** pixel: tâm pixel i là số nguyên i.

Cách sửa:

- `geometry.js` thêm `PIXEL_CENTER = 0.5` và hai hàm `screenToPixel` / `pixelToScreen`: đổi giữa tọa độ màn hình và tọa độ tâm pixel bằng cách lệch đúng nửa pixel. `canvasToImage` cũng trừ 0,5 rồi mới kẹp vào 0–511.
- `canvas.js` đọc con trỏ bằng `screenToPixel` và vẽ vòng tại `x + 0,5`. Thu phóng và kéo ảnh (`view`) vẫn tính theo mép pixel, vì đó là đơn vị của `drawImage`.
- `render_overlay` (`src/game_results.py`) phóng ảnh đối chiếu 3 lần và vẽ vòng tại $3x + 1$, tức tâm của khối 3 × 3 pixel ứng với pixel $x$ (công thức đổi tỷ lệ $k x + (k-1)/2$ của hợp đồng). PIL vẽ theo chỉ số pixel nguyên và bỏ phần lẻ, nên ảnh phóng 2 lần không thể đặt đúng tâm: trước đây vòng lệch −0,25 px ảnh gốc, và cách cộng 0,5 trước khi nhân 2 chỉ đổi thành +0,25 px. Phóng 3 lần thì tâm nguyên rơi đúng một pixel; ảnh lớn hơn (khoảng 1,4 MB thay vì 0,8 MB, thêm khoảng 0,15 s).
- Nhãn hiển thị dưới bản đồ đổi thành "(0, 0) là tâm điểm ảnh góc trên-trái".

Kiểm chứng: test JS mới khóa ba điểm. Bấm giữa pixel 200 ghi 200, bấm mép trái của nó ghi 199,5, và vòng (256, 200) được vẽ quanh 256,5 / 200,5 ở mức 1× cũng như 4×. Test Python khóa vòng (100, 100, r 20) trên ảnh phóng 3 lần cắt hàng 301 tại 241 và 361, đối xứng đúng quanh pixel 301. Test JS còn kiểm vị trí nút đổi bán kính của vòng đang chọn ở mức 4×. Khi đặt lại mã cũ, 5/6 bộ test JS và 2 test Python thất bại, nên các test khóa được quy ước. Thao tác dời và đổi bán kính không đổi vì độ lệch triệt tiêu.

Ảnh hưởng: câu trả lời lưu trước ngày sửa lệch +0,5 px mỗi trục so với hợp đồng. Các lượt chấm cũ giữ nguyên kết quả vì file đã lưu không bị đổi. Không nên trộn câu trả lời cũ và mới khi phân tích sai số tâm: hai bản lệch nhau khoảng 0,71 px, và cặp nằm sát ngưỡng ghép có thể đổi kết quả. Từ bản này, câu trả lời lưu ghi `code_version = "s3-04-player-ui-v2"` (trước là `s1-09-player-ui-v1`) để phân biệt. Nhãn tham chiếu không bị ảnh hưởng vì được tạo bằng công cụ gán nhãn đã dùng đúng quy ước từ 14/10 (commit `c967623`).

## 4. Việc còn lại để đóng S2-13

- Merge S2-09, chạy lại bảng mục 2 với số liệu; muốn kiểm pin S2-10 thì cần crop mới bao phủ thiết bị.
- Trước buổi khảo sát: deploy bản cuối, làm nóng cache cho các ảnh khảo sát (lỗi #6).
