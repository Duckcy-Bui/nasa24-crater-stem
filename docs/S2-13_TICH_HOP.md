# S2-13 — Tích hợp bốn chức năng và kiểm tra luồng sử dụng (khung)

Phụ trách: Bùi Hải Đức; phối hợp: cả nhóm. Mã: `src/integration.py`, `app.py` (`show_statistics`, `show_cards`). Test: `tests/test_integration.py`.

Trạng thái 28/10/2026: **đã ghép đủ bốn chức năng** trên main `958b589` và trên VPS. Phát hiện (S1-07/08/11), trò chơi (S1-09, S2-04, S2-08) và thẻ khoa học S2-10 chạy từ 27/10. S2-10 trả thẻ vùng có nguồn cho Apollo 15/16 và Lunokhod 1/2, với `position=null` khi thiết bị nằm ngoài crop; app tự hiện thẻ mà không vẽ pin giả. Thống kê S2-09 đã merge (PR #30): app hiện số ứng viên máy, diện tích, mật độ và histogram đúng hợp đồng mục 1.

Cập nhật 31/10/2026 trên nhánh `s2-13-app-fixes`, gốc `13394de`: **đã sửa lỗi #8, #9, #10, #11** (mục 3.2). Khi máy chạm giới hạn ứng viên thô, app ẩn giá trị mật độ và giải thích giới hạn. Ảnh thuộc Lunokhod 1 hoặc Mare Frigoris hiện so sánh đếm tay từ bằng chứng S2-09 ngay khi mở ảnh. Đây là kết quả sửa và kiểm cục bộ; chưa phải nghiệm thu độc lập, merge hay deploy.

Vòng r1 đã commit thành `4ee5a86`; kiểm độc lập trả **FAIL A-01** do caption cũ từ `summarize` vẫn báo chạm trần vô điều kiện. Vòng r2 sửa tiếp trên commit đó: thống nhất lời giới hạn ở lớp integration/hiển thị, xử lý số cực hạn và bổ sung kiểm biên. Kết quả r2 cần người kiểm đánh giá lại, không thay verdict r1 thành PASS.

## 1. Hợp đồng cho S2-09 và S2-10 (đề xuất, Hưng và Quốc Anh xác nhận)

### `statistics.summarize(crater_set, metadata, valid_pixel_count) -> dict` (S2-09)

App gọi với ứng viên máy của lượt chấm gần nhất và số pixel hợp lệ của ảnh (`valid_mask`).

| Khóa | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `count` | int ≥ 0 | có | số hố trong `crater_set` được đếm |
| `valid_area_km2` | số ≥ 0 hoặc null | không | `valid_pixel_count × scale² / 1e6` |
| `density_per_km2` | số ≥ 0 hoặc null | không | null khi diện tích bằng 0 |
| `histogram` | `{bin_edges_m: [n+1 số tăng dần], counts: [n số nguyên ≥ 0]}` | không | đường kính `2 × r × scale` (m) |
| `limitations` | list chuỗi | không | app giữ nguyên lời các ghi chú; riêng câu chạm trần vô điều kiện cũ được thay ở lớp integration bằng warning theo số thô (mục 3.2), không sửa dữ liệu `summarize` |

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

### 2.1. Kiểm lại sau khi merge S2-10 và S3-04 (Chromium, 27/10/2026)

Chạy trên main `3cff367` (đã có PR #25 thẻ khoa học và PR #27 tọa độ tâm pixel), cùng mã đang chạy trên VPS. Mỗi ảnh: mở ảnh, bấm Chấm bài, đọc mục Thống kê và Thẻ khoa học.

| Ảnh | Vùng | Chấm bài lần đầu | Thẻ khoa học | Thống kê |
|---|---|---|---|---|
| `moon_ap15_hia_c01` | Apollo 15 | 6,8 s | Apollo 15 — vùng Hadley–Apennine, có link nguồn | "Chưa có thống kê" kèm mã S2-09 |
| `moon_ap16_m109134835l_c01` | Apollo 16 | (lượt chụp Hình 5.2) | Apollo 16 — vùng cao nguyên Descartes | như trên |
| `moon_ap16_m132732855l_c01` | Apollo 16 | 7,3 s | Apollo 16 — vùng cao nguyên Descartes | như trên |
| `moon_lunokhod1_loc_c01` | Lunokhod 1 | 6,8 s | Lunokhod 1 — vùng Mare Imbrium | như trên |
| `moon_lunokhod2_loc_c02` | Lunokhod 2 | 6,3 s | Lunokhod 2 — vùng Le Monnier | như trên |
| `moon_marefrig_loc_c02` | Mare Frigoris | 6,8 s | "Ảnh này chưa có thẻ khoa học." | như trên |
| `moon_vandegraff_hia_c01` | Van de Graaff | 6,8 s | "Ảnh này chưa có thẻ khoa học." | như trên |

Lỗi trang và lỗi Streamlit: 0 / 0. Gọi `cards_view` trên cả 26 ảnh: 21 ảnh có đúng một thẻ hợp lệ (Apollo 15: 6, Apollo 16: 11, Lunokhod 1: 2, Lunokhod 2: 2), 5 ảnh không có thẻ (Mare Frigoris: 3, Van de Graaff: 2), không thẻ nào bị loại vì sai hợp đồng. Không thẻ nào có `position`, nên app không vẽ ghim, đúng với S2-10.

Trên `moon_ap16_m109134835l_c01`, khoanh lại đúng bảy vòng của Hình 5.1 cho điểm 60/100 như trước; bảng vòng tròn ghi tâm nguyên (370, 360…), đúng quy ước sau S3-04. Ảnh chụp lại của Hình 5.1 và 5.3 trùng từng byte với ảnh trong `docs/evidence/s3-08/`.

Lỗi phát hiện trong lượt kiểm ngày 27/10: ở bề rộng 1440 px, nhãn "Điểm theo nhãn đã kiểm chéo" của ô điểm bị cắt chữ cuối (lỗi #9). Đã sửa ngày 31/10, xem mục 3.2.

Ngoài ra `tests/test_integration.py` chạy app với `summarize` và `cards_for_image` giả đúng hợp đồng: số liệu, biểu đồ và thẻ có nguồn hiện đúng.

### 2.2. Kiểm lại với thống kê thật (Chromium cục bộ, 31/10/2026)

Chạy `scripts/check_s213_app.py` trên nhánh `s2-13-app-fixes`, gốc `13394de`. Mỗi ảnh dùng một lượt mở trang mới, chọn ảnh rồi chấm câu trả lời trống; đây là kiểm kỹ thuật, không phải thử người chơi. Đổi ảnh trong cùng phiên được kiểm thêm bằng AppTest ở `tests/test_integration.py`.

| Ảnh | Số ứng viên | Diện tích hợp lệ (km²) | Mật độ máy | So sánh đếm tay | Thẻ khoa học |
|---|---|---|---|---|---|
| `moon_ap15_hia_c01` | 100 | 104,86 | Ẩn, có cảnh báo giới hạn | Không hiện | Apollo 15 |
| `moon_ap16_m109134835l_c01` | 100 | 1,05 | Ẩn, có cảnh báo giới hạn | Không hiện | Apollo 16 |
| `moon_ap16_m132732855l_c01` | 100 | 1,05 | Ẩn, có cảnh báo giới hạn | Không hiện | Apollo 16 |
| `moon_lunokhod1_loc_c01` | 100 | 104,86 | Ẩn, có cảnh báo giới hạn | Có | Lunokhod 1 |
| `moon_lunokhod2_loc_c02` | 100 | 104,86 | Ẩn, có cảnh báo giới hạn | Không hiện | Lunokhod 2 |
| `moon_marefrig_loc_c02` | 100 | 104,86 | Ẩn, có cảnh báo giới hạn | Có | Chưa có thẻ |
| `moon_vandegraff_hia_c01` | 100 | 104,86 | Ẩn, có cảnh báo giới hạn | Không hiện | Chưa có thẻ |

Số trên bảng là số hiển thị của `statistics.summarize` thật, không phải số hố đếm tay. Tất cả lượt chấm có điểm theo nhãn và không có lỗi trang. Script ghi ảnh chụp và `browser_results.json` (số hiển thị và nội dung trang của từng ảnh) vào thư mục `--out`, còn log in ra terminal; kết quả lượt này không đưa vào repo. Chưa kiểm trên VPS.

## 3. Danh sách lỗi cần sửa

| # | Lỗi | Mức | Người | Đề xuất |
|---|---|---|---|---|
| 1 | Canvas đặt mép trái pixel ở tọa độ 0, nên bấm vào giữa pixel 200 ghi x = 200,5. Hợp đồng S1-05 (`DINH_DANG_DU_LIEU.md`: "tâm pixel có tọa độ nguyên") và Hough dùng tâm pixel = 200. Vòng người chơi lệch +0,5 px so với máy và nhãn. | Thấp: nhỏ hơn nhiều ngưỡng ghép 0,5 r ≥ 2,5 px, nhưng sai hợp đồng | Đức | **Đã sửa (S3-04, 27/10).** Xem mục 3.1 |
| 2 | Máy chạm trần 100 ứng viên trên cả 26 ảnh, nên "Chỉ máy có" luôn khoảng 100 và thống kê sẽ đếm ứng viên thô | Cao cho thống kê và thí nghiệm | Tiến, Hưng | Còn mở. S2-07 đã đo: trên `moon_ap16_m109134835l_c01` cả 10 nhãn nằm trong dải tìm 5–125 px nhưng máy dừng ở 100 vòng r 5–10 px, Recall_known 0/10. Nếu không sửa kịp thì ghi là hạn chế trong báo cáo. PR #26 (28/10) thêm chế độ `radius_balanced` để thử, nhưng game vẫn dùng `score` (tập kiểm tra 4/66 so với 5/66); chọn cấu hình game thuộc S2-15 |
| 3 | Chưa ảnh nào có nhãn đã kiểm chéo, nên trò chơi chưa ra điểm | Cao cho khảo sát | Tiến (S1-10), Quốc Anh (S2-03) | **Đã có nhãn (PR #20, 26/10):** 26/26 file ghi `reviewed by Nguyen Manh Tien`, game ra điểm thật trên VPS. **Đã xác nhận (28/10):** Tiến ghi trên PR #20 là đã kiểm đủ 26 overlay |
| 4 | Thống kê chưa có; thẻ S2-10 không có pin vì thiết bị ngoài crop | Cao cho thống kê; giới hạn minh bạch cho thẻ | Hưng (S2-09), Quốc Anh (S2-10) | Thẻ đã merge (PR #25) và hiện trên VPS. **Thống kê đã merge (PR #30, 28/10)** và chạy trên VPS; xem lỗi #10, #11. Pin: nhóm chốt cắt crop mới hay ghi hạn chế |
| 5 | Đổi ảnh rồi quay lại thì mất lịch sử hoàn tác (vòng vẫn còn) | Thấp | Đức | Chưa sửa, có chủ đích. Mỗi ảnh là một component riêng (`key=player_canvas_<image_id>`), nên iframe của ảnh cũ bị hủy khi đổi ảnh. Muốn giữ lịch sử phải lưu ra ngoài iframe (sessionStorage hoặc Python), thêm rủi ro ngay trước khảo sát cho một lỗi mức thấp |
| 6 | Chấm bài lần đầu mỗi ảnh mất 6–8 s trên máy dev; VPS giới hạn 1 CPU có thể chậm hơn | Trung bình khi khảo sát nhiều người cùng lúc | Đức | Đã đo trên VPS (26/10): 9,4 s cho lượt chấm đầu trên `moon_ap15_hia_c01`. Ứng viên máy được cache trong tiến trình (`machine_for_image`, tối đa 8 ảnh) đến khi khởi động lại service. Cách xử lý khi khảo sát: sau khi deploy, người điều phối bấm Chấm bài một lần trên mỗi ảnh dùng khảo sát (≤ 8 ảnh) để làm nóng cache |
| 7 | Link nguồn trong thẻ khoa học màu xanh đậm mặc định của Streamlit, gần như không đọc được trên nền tối | Thấp | Đức | **Đã sửa (S3-04, 27/10):** `app.css` đặt link trong khối văn bản thành `#8cc8ff`, tương phản 9,7–11:1 |
| 8 | Nút đổi bán kính của vòng đang chọn vẽ tại `min(511, x + r)`: khi vành vượt mép phải, nút không nằm trên vành, bấm vào đó sẽ dời vòng thay vì đổi bán kính | Thấp | Đức | **Đã sửa (S2-13/S3-04, 31/10)**. Nút chọn điểm trên vành trong ảnh. Test Node kiểm vị trí và kéo nút; Chromium kiểm tâm giữ nguyên, bán kính bằng khoảng cách tới con trỏ |
| 9 | Nhãn ô điểm "Điểm theo nhãn đã kiểm chéo" bị cắt chữ cuối ở bề rộng 1440 px (cột hẹp của `st.metric`) | Thấp | Đức | **Đã sửa (S2-13/S3-04, 31/10)**. CSS cho nhãn xuống dòng. Chromium kiểm đủ chữ ở 1440 px, 390 px và cột thử hẹp; ca cột hẹp thất bại khi trả CSS cũ |
| 10 | Mục Thống kê tính mật độ trên ứng viên máy, mà máy luôn trả đủ 100 vòng (lỗi #2). Vì vậy mọi ảnh 20 m/px hiện 0,954 hố/km² và mọi ảnh 2 m/px hiện 95,4 hố/km², dù bề mặt khác nhau | Cao: học sinh có thể đọc thành "các vùng cùng tuổi" | Đức | **Đã sửa (S2-13/S3-04, 31/10)**, bổ sung r2 theo A-01. Integration bỏ đúng caption chạm trần vô điều kiện cũ; chưa chạm trần không có lời chạm trần, chạm trần chỉ có một warning và ẩn mật độ. Test dùng `summarize` thật ở số thô 0/99/100/101, kiểm toàn bộ caption/warning. Không sửa API hoặc dữ liệu `summarize`; chờ kiểm độc lập r2 |
| 11 | So sánh mật độ hai vùng (yêu cầu 2 của đề) mới có trong `scripts/s209_density.py` và `docs/S2-09_MAT_DO_HO.md`, chưa có trong app | Cao cho đủ chức năng | Đức | **Đã sửa (S2-13/S3-04, 31/10)**. Đọc, kiểm JSON lúc chạy; nhận vùng bằng vùng đếm và metadata. Test Python kiểm dữ liệu, file lỗi và đổi ảnh; Chromium kiểm bảng trên cả hai vùng, ô cùng nguồn không được đếm và ảnh ngoài vùng |
| 12 | A-06: picker quay về ảnh đầu khi xóa/hoàn tác/lưu nhanh trên ảnh khác; yêu cầu lưu có thể chưa được xử lý | Thấp (A-06) | Đức | **Đã sửa cục bộ (S3-04 r4, 01/11)**. Giữ nhãn lựa chọn độc lập với số vòng; bỏ đoạn tự gán state cho nhãn động. Main `c466c2d` tái hiện 13/20 lượt, bản sửa 0/20 lượt cùng kịch bản. Test AppTest phát lại nhãn wire cũ fail trên main, pass trên bản sửa; xem mục 3.4. Chưa nghiệm thu độc lập hoặc deploy |

### 3.1. Lỗi #1: quy ước tâm pixel trên canvas và ảnh đối chiếu

Trước khi sửa, canvas và ảnh đối chiếu kết quả dùng **mép** pixel làm tọa độ: pixel i phủ đoạn [i, i + 1), nên bấm vào giữa pixel 200 ghi x = 200,5. Hough, công cụ gán nhãn (`scripts/label_craters.py`, `extent=[-0.5, 511.5, 511.5, -0.5]`) và các hình của pipeline đều dùng **tâm** pixel: tâm pixel i là số nguyên i.

Cách sửa:

- `geometry.js` thêm `PIXEL_CENTER = 0.5` và hai hàm `screenToPixel` / `pixelToScreen`: đổi giữa tọa độ màn hình và tọa độ tâm pixel bằng cách lệch đúng nửa pixel. `canvasToImage` cũng trừ 0,5 rồi mới kẹp vào 0–511.
- `canvas.js` đọc con trỏ bằng `screenToPixel` và vẽ vòng tại `x + 0,5`. Thu phóng và kéo ảnh (`view`) vẫn tính theo mép pixel, vì đó là đơn vị của `drawImage`.
- `render_overlay` (`src/game_results.py`) phóng ảnh đối chiếu 3 lần và vẽ vòng tại $3x + 1$, tức tâm của khối 3 × 3 pixel ứng với pixel $x$ (công thức đổi tỷ lệ $k x + (k-1)/2$ của hợp đồng). PIL vẽ theo chỉ số pixel nguyên và bỏ phần lẻ, nên ảnh phóng 2 lần không thể đặt đúng tâm: trước đây vòng lệch −0,25 px ảnh gốc, và cách cộng 0,5 trước khi nhân 2 chỉ đổi thành +0,25 px. Phóng 3 lần thì tâm nguyên rơi đúng một pixel; ảnh lớn hơn (khoảng 1,4 MB thay vì 0,8 MB, thêm khoảng 0,15 s).
- Nhãn hiển thị dưới bản đồ đổi thành "(0, 0) là tâm điểm ảnh góc trên-trái".

Kiểm chứng: test JS mới khóa ba điểm. Bấm giữa pixel 200 ghi 200, bấm mép trái của nó ghi 199,5, và vòng (256, 200) được vẽ quanh 256,5 / 200,5 ở mức 1× cũng như 4×. Test Python khóa vòng (100, 100, r 20) trên ảnh phóng 3 lần cắt hàng 301 tại 241 và 361, đối xứng đúng quanh pixel 301. Test JS còn kiểm vị trí nút đổi bán kính của vòng đang chọn ở mức 4×. Khi đặt lại mã cũ, 5/6 bộ test JS và 2 test Python thất bại, nên các test khóa được quy ước. Thao tác dời và đổi bán kính không đổi vì độ lệch triệt tiêu.

Ảnh hưởng: câu trả lời lưu trước ngày sửa lệch +0,5 px mỗi trục so với hợp đồng. Các lượt chấm cũ giữ nguyên kết quả vì file đã lưu không bị đổi. Không nên trộn câu trả lời cũ và mới khi phân tích sai số tâm: hai bản lệch nhau khoảng 0,71 px, và cặp nằm sát ngưỡng ghép có thể đổi kết quả. Từ bản này, câu trả lời lưu ghi `code_version = "s3-04-player-ui-v2"` (trước là `s1-09-player-ui-v1`) để phân biệt. Nhãn tham chiếu không bị ảnh hưởng vì được tạo bằng công cụ gán nhãn đã dùng đúng quy ước từ 14/10 (commit `c967623`).

### 3.2. Sửa lỗi #8–#11 và cách kiểm lại (31/10/2026)

- `density_limit_view` dùng `raw_count`, không dùng số còn lại sau lọc. `statistics_presentation_view` bỏ đúng câu cũ `Hough hiện chỉ trả vòng nhỏ (chạm trần 100 ứng viên), nên hố lớn bị thiếu.` trong danh sách caption để hiển thị; các ghi chú khác giữ nguyên và dict/list gốc không bị sửa. Nếu số thô < `max_circles`, không có thông báo chạm trần. Nếu số thô ≥ `max_circles`, chỉ có một warning ở Thống kê, ô Mật độ hiện `—`. Bỏ caption phụ dưới ô mật độ và caption cũ ở Chấm bài để không lặp. Số ứng viên, diện tích và histogram vẫn theo hợp đồng mục 1.
- **Đề xuất cho Hưng, chưa phải thay đổi đã thực hiện:** câu chạm trần trong `statistics.summarize` nên có điều kiện dựa trên số ứng viên thô và ngưỡng thực tế do lớp gọi cung cấp; số sau lọc không đủ để suy ra đã chạm trần. Nếu chưa có thông tin này thì không khẳng định chạm trần. Cần thống nhất cách truyền ngữ cảnh trong phần của Hưng trước khi đổi API. R2 giữ nguyên API và toàn bộ dữ liệu gốc của `summarize`; integration tạm xử lý đúng chuỗi cũ nêu trên, không lọc rộng mọi câu có từ "giới hạn".
- `density_comparison_view` đọc `so_sanh.json` và `regions.json` mỗi lần hiển thị. Validator kiểm tên vùng không rỗng; số đếm nguyên không âm; diện tích và tỷ lệ ảnh hữu hạn, dương; mật độ hữu hạn, không âm và khớp `n / area_km2` với sai số tương đối `1e-9`. CI cần hai số hữu hạn thỏa `0 ≤ thấp ≤ mật độ ≤ cao`; tỷ lệ phải khớp thương hai mật độ với sai số tương đối `1e-9`; p-value chỉ được kiểm là số hữu hạn trong [0, 1]. Dải D gồm hai số hữu hạn tăng dần, dương và trùng giữa bằng chứng/vùng đếm; hai vùng cùng tỷ lệ và khác `product_id`. Danh sách tên ô cắt phải không trùng và khớp các khóa trong vùng đếm. Nếu `image_id` là khóa ô đếm thì `product_id` phải khớp vùng đó; các ảnh khác được nhận vùng bằng `product_id`. Chỉ hiện bảng khi metadata có `body=moon` và tỷ lệ trùng vùng đã nhận.
- Validator **không tính lại** CI Garwood hoặc p-value, không kiểm nội dung hình chữ nhật `keep/exclude`, diện tích hợp pixel hoặc đếm lại hố. Vì vậy p = 0,01, CI [0, 999] hay một crop definition bằng `null` vẫn có thể qua nếu các điều kiện miền giá trị/tên khóa nói trên đạt. Đây là giới hạn của kiểm đầu vào, không phải kết quả thẩm định số học. File thiếu, JSON không đọc được, vi phạm điều kiện đang kiểm hoặc gây `OverflowError` được đổi thành thông báo lỗi nhẹ. Mọi số trên bảng vẫn lấy từ JSON.
- Bảng đếm tay hiện độc lập với lượt chấm, chỉ trên ảnh thuộc hai ảnh nguồn đã đối chiếu bằng metadata. Mare Frigoris `c01` có cùng ảnh nguồn nhưng không thuộc các ô đếm: app nói rõ bảng dùng các ô khác. Ảnh ngoài hai vùng không hiện bảng để tránh gắn kết quả đếm tay với một vùng khác. Dùng bảng, không thêm hình tích lũy để giữ phần so sánh ngắn.
- `radiusHandle` thử phải, trái, dưới, trên; nếu chỉ vành gần góc lọt vào ảnh thì tìm giao với mép ảnh. Kiểm biên cho phép sai số `1e-9` px để giữ điểm tiếp xúc đúng góc do dấu phẩy động; giữ nguyên điểm tính trên vành, không kẹp lại tọa độ. Khi cả vành nằm ngoài ảnh vượt sai số này, không vẽ nút giả. Node kiểm cả tiếp xúc góc và kéo theo khoảng cách tới tâm; Chromium kiểm vòng thử chạm mép phải.
- CSS giữ nguyên nhãn điểm và cho xuống dòng, gồm cả khối Markdown chứa nhãn. Kiểm chữ nằm trong vùng hiển thị bằng hình học DOM, kèm ảnh ở 1440 px và 390 px. Bộ font hiện tại không tái hiện lỗi ở chiều rộng mặc định; ca cột thử 128 px ở viewport 1440 px tái hiện cắt chữ với CSS cũ và qua với CSS mới. Kích thước này chỉ là dữ liệu thử bố cục.

Test hồi quy: `tests/test_integration.py`, `tests/test_integration_density.py`, `tests/test_canvas_geometry.js`, `tests/test_canvas_zoom.js`, `tests/test_browser_tool.py` và `scripts/check_s213_app.py`. R2 bổ sung kiểm lời giới hạn với `summarize` thật ở 0/99/100/101, JSON có số cực hạn và điểm tiếp xúc góc. Các ca này đã tái hiện lỗi trên `4ee5a86` trước khi sửa; đối chứng r1 với mã gốc `13394de` vẫn được giữ trong hồ sơ vòng trước. Kiểm độc lập và quyết định tích hợp thuộc người điều phối.

### 3.3. Môi trường và phạm vi công cụ browser tùy chọn

`requirements-browser.txt` dùng bộ phụ thuộc kiểm thử đã ghim trong `requirements-test.txt` và `playwright==1.64.1`. Không thêm Playwright vào phụ thuộc runtime. Ví dụ tạo môi trường trên Linux/macOS, chạy từ gốc repo:

```sh
python3.12 -B -m venv .venv
.venv/bin/python -B -m pip install -r requirements-browser.txt
.venv/bin/python -B -m playwright install chromium
.venv/bin/python -X utf8 -B scripts/install_s106_dataset.py
.venv/bin/python -B -m streamlit run app.py --server.port 8621 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

Trong terminal thứ hai:

```sh
.venv/bin/python -B scripts/check_s213_app.py --url http://127.0.0.1:8621 --out /tmp/s213-browser-check
```

`--out` phải chưa tồn tại, kể cả khi chạy lại sau một lượt lỗi; script từ chối ghi đè. Dừng Streamlit bằng Ctrl+C sau khi chụp. `--help` không cần mở browser; `--layout-only` chỉ kiểm nhãn điểm. Đường dẫn Python trên Windows là `.venv\Scripts\python.exe`.

`run_identity.json` và `browser_results.json` ghi HEAD, URL yêu cầu, hash source/cấu hình/bằng chứng từ checkout; file kết quả còn ghi URL đã mở. HEAD là danh tính checkout cung cấp kỳ vọng, **không chứng minh** server tại `--url` chạy đúng source đó (`server_source_verified=false`); khi kiểm cục bộ phải tự khởi động server từ checkout cần kiểm. PASS chỉ nói các assertion đã chạy: biên chữ; chuỗi tên/số đếm/diện tích/mật độ và câu kết luận trong bảng; số ứng viên, ô mật độ, một lời chạm trần và không có exception ở từng ảnh; tâm và bán kính hiển thị sau kéo nút. Script chỉ lưu, không assert CI, tỷ lệ, p-value hoặc thẻ khoa học trong vòng bảy ảnh. Mỗi ảnh được mở lại trên trang mới, nên lượt này không chứng minh giữ draft/score khi đổi ảnh trong cùng phiên.

### 3.4. A-06 — nguyên nhân và sửa picker (r4, 01/11/2026)

Ghi nhận trước r4: người kiểm thấy picker về ảnh đầu khi thao tác nhanh sau xóa/hoàn tác/lưu; lượt chậm hơn đi qua được. R1/r2 chưa có đối chứng cùng nhịp để quy hiện tượng này cho commit `4ee5a86`, nên giữ mở. Bằng chứng các vòng đó vẫn nằm trong hồ sơ người kiểm, không được coi là bằng chứng đã sửa.

R4 tái hiện trên main `c466c2d`, Streamlit cục bộ cổng 8624, Chromium trong `venv-verify`. Sau khi mở Lunokhod 1 và nhận phản hồi revision của vòng đầu, harness bấm xóa → hoàn tác → lưu bằng click Playwright, không thêm khoảng đợi hoặc chờ ACK giữa ba thao tác. Mỗi lượt là một phiên mới; chỉ chụp ảnh sau cả chuỗi. Main có **13/20 lượt reset (65 %)**; bản sửa có **0/20 reset, 20/20 lưu thành công** với cùng harness và tham số. Nhịp thông điệp trung vị xóa→hoàn tác / hoàn tác→lưu lần lượt khoảng 62/40 ms trên main và 61/49 ms trên bản sửa. Đây là tỷ lệ của các lượt đã chạy, không phải cam kết cho mọi thiết bị hoặc mọi nhịp thao tác.

Nguyên nhân đã có log hai phía: nhãn picker trước đây chứa số vòng, nên đổi giữa chuỗi không có số vòng và chuỗi thêm `· 1 vòng`. Khi trình duyệt gửi lại nhãn cũ trong yêu cầu lưu, `SelectboxSerde.deserialize` của Streamlit không tìm thấy nó trong map nhãn hiện tại và trả chính chuỗi nhãn đó thay vì `image_id`. `image_label` tiếp tục định dạng chuỗi này như một mã ảnh; `resolve_value_against_options` nhận giá trị không thuộc options và reset về ảnh đầu. Log còn ghi yêu cầu canvas có đúng ảnh/revision/nonce, nhưng ảnh đang mở đã đổi trước khi xử lý lưu. Đây là cuộc đua giữa nhãn lựa chọn và rerun, không phải bằng chứng canvas gửi nhầm ảnh.

Cách sửa tối thiểu trong `app.py`: nhãn chỉ gồm mã ảnh và tên vùng cố định; số vòng vẫn xem ở panel canvas. Bỏ đoạn tự gán `player_image_picker` từng dùng để cập nhật nhãn động. Không đổi key, hợp đồng revision/nonce, lưu câu trả lời, chấm bài hoặc thuật toán máy. Không chữa bằng chờ cố định hay tự chọn lại ảnh sau reset.

`tests/test_app_state.py::PlayerRerunStateTests.test_fast_delete_undo_save_keeps_image_with_delayed_picker_wire_value` phát lại giá trị string của widget đúng như browser sau xóa/hoàn tác, rồi gửi Save với nhãn cũ. Test thất bại trên main vì lựa chọn thành Apollo 15; bản sửa giữ Lunokhod, revision và nonce đúng, có một file câu trả lời đúng hình học. Test dùng `install_dataset` vào thư mục tạm; đã chạy đối chứng trong bản sao không có ảnh tại `data/processed`.

Chi tiết nhịp, source hash, log deserialize/resolve và ảnh mỗi lượt nằm trong hồ sơ `n24-team/runs/app/r4/`; báo cáo `n24-app-r4.md` chỉ rõ lệnh và giới hạn. Bộ ghi log chỉ quan sát lời gọi thật và chuyển thư mục lưu sang vùng minh chứng. Kết quả r4 là kiểm cục bộ, chờ kiểm độc lập. Harness vẫn chờ revision do Python phản hồi và nonce lưu khớp **sau** chuỗi nhanh; không dùng số vòng cục bộ hoặc riêng `notRunning` làm xác nhận đã lưu.

## 4. Việc còn lại để đóng S2-13

- S2-09 đã merge (PR #30) và chạy trên VPS. Lỗi #8–#11 đã sửa và kiểm cục bộ ngày 31/10; còn người kiểm độc lập đánh giá trước khi người điều phối tích hợp và Đức đồng ý deploy. Không coi kiểm cục bộ là bản đã chạy trên VPS.
- Thẻ S2-10 đã kiểm xong (mục 2.1). Muốn kiểm ghim vị trí thì cần crop mới bao phủ thiết bị; nếu nhóm không cắt thêm thì giữ hạn chế đã ghi trong báo cáo (mục 5.5, 5.8).
- PR #26 đã merge mà không đổi game: trên hai ảnh thử, danh sách ứng viên giống hệt main trước đó. Nếu S2-15 chốt đổi cấu hình game thì chụp lại Hình 5.2 và chạy lại mục 2.1.
- Theo quyết định của trưởng nhóm ngày 31/10, không thử người chơi thật hoặc khảo sát. Yêu cầu khảo sát ít nhất 10 học sinh chưa đạt và phải ghi là hạn chế; không có số liệu khảo sát mới trong vòng sửa này.
