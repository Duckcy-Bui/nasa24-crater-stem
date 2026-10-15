# UI R2: bản đồ to hơn, có phóng to / thu nhỏ / kéo ảnh

Yêu cầu của user ngày 2026-10-15, đưa ra sau khi xem bản R1 trên trình duyệt.

Bản chuẩn để so là `docs/ui-design/mockup.html#many`. Mockup đã có zoom chạy thật: cuộn chuột trên ảnh, các nút − / + / Vừa khung, chế độ Kéo ảnh.

Bất biến giữ như SPEC §8:
- hệ tọa độ 512 px gốc trên-trái
- hợp đồng sự kiện và `save_nonce`
- schema JSON
- chạy offline, chữ trên giao diện bằng tiếng Việt

Các hàm hiện có trong `geometry.js` giữ nguyên chữ ký. Nếu cần thì thêm hàm mới.

Không push, không merge khi user chưa duyệt.

## 1. Nguyên nhân của khoảng đen bên phải ảnh

`src/crater_canvas/styles.css:61` đặt `.image-stage { max-width: 620px }`, trong khi cột ảnh là `.workspace { grid-template-columns: minmax(0,1fr) 340px }` (dòng 53) và rộng 768 px ở màn 1440. Ảnh bị giới hạn 620 px rồi căn trái, nên còn khoảng 148 px nền trống. Khung `section.observation` vẫn rộng 768 px.

## 2. Bố cục mới
- Bỏ giới hạn 620 px. Khung ảnh rộng hết cột, giữ tỉ lệ vuông, tối đa `--stage-max: 840px`.
- Nội dung tối đa `--content-max: 1248px`, gồm 840 cho ảnh, 28 khoảng cách và 380 cho bảng. Ở màn 1440 ảnh rộng khoảng 840 px.
- Toolbar và dòng meta rộng đúng bằng khung ảnh. Không còn khoảng trống giữa ảnh và bảng.
- Màn thấp (900 px) được phép cuộn nhẹ để thấy đáy ảnh. Thay mục "không cuộn ở 1440×900" trong SPEC §9 bằng hai điều kiện:
  - Toolbar, bảng và nút Lưu thấy ngay khi mở trang.
  - Ảnh không bị cắt ngang.
- Gọn header để bù chiều cao: giảm padding trên của Streamlit, đưa tiêu đề và ô chọn ảnh về một hàng thấp khoảng 64 px.
- Mobile ≤ 720 px giữ bố cục R1. Ảnh rộng hết bề ngang (358 px).

## 3. Phóng to / thu nhỏ / kéo ảnh
**Trạng thái xem**: `view = {z, x, y}`.
- `z` nằm trong [1, 8]. 1 là "Vừa khung", tức thấy toàn ảnh.
- `x, y` là góc trên-trái của vùng đang thấy, tính bằng px ảnh. Kẹp cả hai trong `[0, 512 − 512/z]`.
- `view` **không** vào lịch sử Hoàn tác, **không** lưu, **không** gửi về Python.
- Khi đổi ảnh thì đặt lại `z = 1`.

**Điều khiển**:

| Thao tác | Hành vi |
|---|---|
| Cuộn chuột trên ảnh | Mỗi nấc ×1.25 hoặc ÷1.25, neo tại vị trí con trỏ. Gọi `preventDefault` (listener `passive: false`). |
| Nút − / + | ×1.25 hoặc ÷1.25, neo tại tâm khung. Nút tắt khi chạm giới hạn. |
| Ô `NNN%` | `<output aria-live="polite">`. |
| Nút Vừa khung | `z = 1, x = y = 0`. Tắt khi đang ở 1×. |
| Chế độ mới "Kéo ảnh" | Nút thứ 3 trong segmented control (icon bàn tay; nhãn mobile là "Kéo"). Kéo để di chuyển. Con trỏ `grab` / `grabbing`. Ở 1× không kéo được. |
| Giữ Space, hoặc kéo bằng chuột giữa | Kéo ảnh tạm thời ở bất kỳ chế độ nào. |
| Cảm ứng | Chụm hai ngón để zoom, neo tại tâm hai ngón. Kéo hai ngón để di chuyển ảnh. Một ngón giữ nguyên hành vi vẽ / sửa. |
| Bàn phím (khi khung ảnh có focus, `tabIndex = 0`) | `+` / `=` phóng to, `-` thu nhỏ, `0` vừa khung. Không đăng ký phím tắt toàn cục. |

**Cụm nút zoom**: đặt **dưới ảnh**, cùng hàng với dòng meta và căn phải (bản triển khai ngày 2026-10-15 đổi chỗ vì nếu nằm đè góc trên-phải ảnh thì ở 100% không vẽ được hố dưới cụm nút). Mobile: hàng zoom rộng hết bề ngang, nằm trên dòng meta.
- Nền `rgba(10,12,15,.82)`, bo góc 10, nút 32 px.
- Mobile: nút 40 px, ẩn ô `%`.
- CSS lấy từ `.zoom` trong `mockup.html`.

**Vẽ trên canvas** (khác mockup: mockup phóng SVG nên nhãn cũng to lên):
- Backing store bằng `rect.width × devicePixelRatio`.
- `drawImage(image, x, y, 512/z, 512/z, 0, 0, W, H)`.
- Vòng tròn: biến đổi tọa độ ảnh sang màn hình bằng `(p − view) × z × W/512`.
- Độ dày nét, cỡ nhãn (11 px), dấu tâm và núm vành **giữ nguyên kích thước trên màn hình** ở mọi mức zoom.
- Khi `z ≥ 3`: `imageSmoothingEnabled = false` để thấy rõ từng pixel thật.

**Đổi tọa độ khi bấm / kéo**:
- `imageX = view.x + (clientX − rect.left) / rect.width × 512 / z`, tương tự cho y.
- Dung sai bắt vòng 9 px màn hình, tức `9 × 512 / (rect.width × z)` px ảnh.
- Kẹp tâm vòng trong 0–511 và bán kính lớn hơn 0 như cũ.
- Bán kính khi vẽ tính trong hệ px ảnh.

## 4. Test bắt buộc thêm
- Hàm đổi tọa độ chiều xuôi và chiều ngược ở z = 1, 2.5, 8 với x, y khác 0. Sai số dưới 1e-9.
- Vẽ một vòng ở z = 4 đã kéo lệch: lưu ra đúng tọa độ ảnh. Bắt vòng nhỏ (r = 3) ở z = 8.
- Zoom và kéo ảnh không đổi `revision`, không thêm vào lịch sử, không có trong value gửi Streamlit hay trong JSON tải về.
- Kẹp `view` ở các biên; đổi ảnh thì `z` về 1.
- Nghiệm thu bằng ảnh chụp ở 1440×900 và 390 px: 1×, 400% đã kéo lệch, và trạng thái trống. Không còn khoảng đen giữa ảnh và bảng.
