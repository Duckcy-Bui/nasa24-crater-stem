# UI R1 — Bản local chờ duyệt

Ngày kiểm tra: 15/10/2026. Worktree `nasa24-crater-stem-s1-09`, nhánh `s1-09-interface`, nền `3b4a977`. Yêu cầu gốc: [UI_FIX_R1.md](ui-design/UI_FIX_R1.md). Các thay đổi chưa commit, push hoặc merge.

Đã làm nhóm P2 trước, sau đó P3. [SPEC §8](ui-design/SPEC.md) và hợp đồng `save_nonce` giữ nguyên. `geometry.js`, `contracts.py`, `player_annotations.py`, `player_ui.py` không đổi; không thêm vòng mặc định hay dùng vòng minh họa làm ground truth.

## Đối chiếu 10 điểm

| Điểm | Thay đổi | Kiểm chứng |
| --- | --- | --- |
| 1 · P2 | Bỏ gợi ý lặp dưới ảnh; giữ `#status` dạng `sr-only`. Chỉ dòng meta còn hiển thị | 6 ảnh, kiểm phần tử được cắt khỏi bố cục |
| 2 · P2 | Hoàn tác/Xóa tắt vẫn có nền và viền trong suốt, opacity .42 | Trạng thái trống, computed style |
| 3 · P2 | Toolbar mobile một hàng; nhãn Vẽ ngắn, Hoàn tác/Xóa chỉ icon 44×44 và có aria-label | 3 ảnh 390 px, đo vị trí và kích thước, không tràn ngang |
| 4 · P2 | Mép trái toolbar, ảnh và meta thẳng hàng | 3 ảnh 1440×900, chênh lệch không quá viền ảnh 1 px |
| 5 · P2 | Input hiện 2 chữ số; ô không sửa giữ số gốc, chỉ parse ô đã đổi chuỗi | 18 test hồi quy, download và lưu/đọc lại trên Chromium |
| 6 · P3 | Ẩn hàng ID/Tâm x/Tâm y/Bán kính khi trống | Hai ảnh trống và kiểm visibility |
| 7 · P3 | Image id lên trước, kèm số vòng của bản nháp | Kiểm đổi nhãn sau sửa/lưu, chọn ảnh khác rồi quay lại đúng bản nháp |
| 8 · P3 | Đường dẫn rút gọn ở giữa, giữ prefix thư mục và đuôi hash; title và nút sao chép giữ nguyên đường dẫn đầy đủ | Hai ảnh nhiều vòng đã lưu, kiểm text/title và file thật |
| 9 · P3 | Font ID và viền chữ tính theo 512/chiều rộng hiển thị; vẽ lại khi resize | Đo gần 11 CSS px cả hai chiều đổi viewport |
| 10 · P3 | Input và bảng vòng cùng hiển thị 2 chữ số | Ảnh, test JS và dữ liệu tải/lưu giữ nguyên độ chính xác |

Để cả thông báo đã lưu và phần cuối bảng vừa desktop 900 px, danh sách cuộn giới hạn 200 px, khoảng cách trong bảng được thu gọn và padding cuối trang giảm. Ảnh vẫn rộng tối đa 620 px. Mobile giữ thứ tự ảnh → sửa → lưu → danh sách.

Nhãn ảnh có số vòng làm chuỗi option thay đổi theo bản nháp. Ứng dụng giữ key ổn định và đồng bộ lại giá trị đang chọn trước khi dựng selectbox, tránh frontend tự chuyển về ảnh đầu khi nhãn đổi. Bộ thử kiểm cả lưu đúng ảnh và đổi ảnh A → B → A.

## Log kiểm thử

- [unittest.log](evidence/s1-09-ui-r1/unittest.log): **131 test PASS**, không skip.
- [canvas.log](evidence/s1-09-ui-r1/canvas.log): chạy đủ `tests/test_canvas_*.js`, gồm event, geometry, precision **18 kịch bản** và save **9 kịch bản**, tất cả PASS.
- [browser_checks.json](evidence/s1-09-ui-r1/browser_checks.json): **8 nhóm PASS**, không lỗi JavaScript, không request HTTP ra ngoài origin local. Có kiểm 511.00 vừa các ô nhập, desktop không cuộn, mobile không tràn ngang, nút cao tối thiểu 44 px và lưu/đọc lại JSON.
- [runtime.log](evidence/s1-09-ui-r1/runtime.log) và [contracts_readback.json](evidence/s1-09-ui-r1/contracts_readback.json): kết quả chạy và kiểm lại hợp đồng của các JSON tải về.
- [source_hashes.json](evidence/s1-09-ui-r1/source_hashes.json): fingerprint source khi nghiệm thu, kèm xác nhận bốn helper không đổi so với nền.

Kiểm số thực dùng vòng tạo bằng thao tác chuột: Apply không sửa giữ nguyên cả JSON; sửa x giữ nguyên y và r đầy đủ; input sai không làm đổi bản nháp; file ghi bởi `save_nonce` khớp JSON tải. Test riêng còn kiểm bán kính 0.004 hiển thị 0.00 vẫn hợp lệ khi không sửa. Các vòng trong kiểm thử chỉ là dữ liệu thao tác UI.

## Sáu ảnh chụp cuối

| Trạng thái | Desktop 1440×900 | Mobile rộng 390 px |
| --- | --- | --- |
| Trống | [1440_empty.png](evidence/s1-09-ui-r1/1440_empty.png) | [390_empty.png](evidence/s1-09-ui-r1/390_empty.png) |
| 1 vòng, lỗi nhập | [1440_one_error.png](evidence/s1-09-ui-r1/1440_one_error.png) | [390_one_error.png](evidence/s1-09-ui-r1/390_one_error.png) |
| 8 vòng, đã lưu | [1440_many_saved.png](evidence/s1-09-ui-r1/1440_many_saved.png) | [390_many_saved.png](evidence/s1-09-ui-r1/390_many_saved.png) |

Ảnh mobile chụp toàn nội dung bằng cách tăng chiều cao viewport, giữ nguyên rộng 390 px; các chiều cao lần lượt 1269, 1332 và 1694 px. Layout/overflow được kiểm cả trước chụp. Thử nghiệm dùng Chromium headless; chưa kiểm Safari/Firefox hoặc thiết bị cảm ứng thật.

## Chạy lại

```bash
.venv/bin/python -m unittest discover -s tests -v
for test_file in tests/test_canvas_*.js; do
  node "$test_file" || exit "$?"
done
```

Sau khi Streamlit sẵn sàng tại 127.0.0.1:8501, chạy bộ chụp bằng Node có Playwright và Chromium đã cài:

```bash
node scripts/check_ui_r1.cjs
```

Nếu Playwright nằm ngoài module path thông thường, đặt `NASA24_PLAYWRIGHT_MODULE` thành đường dẫn package có sẵn. `NASA24_UI_R1_URL` và `NASA24_UI_R1_OUTPUT` cho phép đổi địa chỉ/thư mục bằng chứng; mặc định kết quả vào `outputs/s109_ui_r1/`. Script có tạo các lần lưu thử riêng trong `outputs/player_answers/`; không ghi đè câu trả lời cũ. CI đã đổi thành chạy toàn bộ `test_canvas_*.js`, nhưng bản R1 này chưa được push nên chưa có lượt CI mới.

Agent kiểm thử chỉ thêm test precision; agent review khác đối chiếu nguồn, report và ảnh riêng. Xem [review độc lập](evidence/s1-09-ui-r1/independent_review.md) để phân biệt bằng chứng runtime do root chạy với kiểm định nguồn/ảnh của reviewer.
