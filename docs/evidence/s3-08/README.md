# Hình 5.1–5.3 — chụp lại ngày 01/11/2026

App trên VPS được mở qua SSH tunnel tới cổng Streamlit của VPS, tại `http://127.0.0.1:18601` trên máy chụp. Trưởng nhóm cung cấp mốc `main c466c2d`; lượt chụp không SSH hay đọc hash mã trên VPS. Không dùng app dựng từ worktree báo cáo để thay bằng chứng này.

Dùng Chromium/Playwright trong `venv-verify`. Lệnh tái hiện, chạy ở gốc repo với Python có Playwright và Chromium:

```bash
python -B scripts/capture_report_figures.py \
  --url http://127.0.0.1:18601 --server-commit c466c2d \
  --out /tmp/s308-capture
```

Thư mục đầu ra phải chưa tồn tại. Lệnh tạo một lượt chấm minh họa trên app; lưu ảnh, JSON tải từ giao diện và biên bản kiểm vào thư mục đó. Khi kiểm xong, ba JPEG thay các file cùng tên tại đây.

- Viewport 1440 × 900 CSS px, device scale factor 10/9, ảnh gốc 512 × 512, zoom canvas 100%. Khung giao diện giữ cùng bố cục ảnh cũ; JPEG chất lượng 92. Không sửa pixel, số điểm hay vòng máy trong ảnh chụp.
- Mở `moon_ap16_m109134835l_c01`. Vẽ bằng chuột rồi dùng ô số để nhập bảy vòng của Hình 5.1 cũ, theo thứ tự `(x,y,r)`: `(370,360,21)`, `(320,446,15)`, `(434,410,12)`, `(276,200,17)`, `(195,211,11)`, `(251,390,14)`, `(90,120,16)`. Chọn U4 ở chế độ sửa.
- Hình 5.1 chụp đầu trang; Hình 5.2 cuộn tới “Chấm bài”, cắt khung 1440 × 829 CSS px; Hình 5.3 cắt 1440 × 230,4 CSS px từ trước tiêu đề thẻ 16 px. Riêng thẻ tạm tăng khoảng trống cuối trang lên 60 px để khung cắt nằm trọn trong viewport, rồi khôi phục; không đổi nội dung hay chiều rộng bố cục.
- Kích thước ba file giữ như ảnh cũ: 1600 × 1000, 1600 × 921, 1600 × 256 px. Chờ Streamlit hết chạy trước khi chụp.

Lượt chấm minh họa cho **60/100, đúng 6/10 nhãn, bỏ sót 4; trùng máy 0, chỉ người chơi 7, chỉ máy 100**. Chú thích Hình 5.2 vẫn đúng. Đây là các vòng nhập bằng kịch bản để chụp hình, không phải lượt khảo sát người học. Có cảnh báo chạm trần và mật độ “—” trong phần thống kê, bên dưới khung Hình 5.2.

`r3_player_answer.json` và `r3_score.json` được tải qua nút trên app; `r3_capture.json` ghi cấu hình, kết quả assertion, trạng thái kiểm commit và SHA-256 ảnh. Script chỉ kiểm giao diện/điểm của lượt minh họa, không xác nhận độc lập commit máy chủ hoặc độ chính xác phát hiện trên toàn bộ dữ liệu.
