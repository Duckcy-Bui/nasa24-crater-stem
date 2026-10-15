# UI fix R1: các điểm lệch giữa bản thật `3b4a977` và mockup

Nguồn: review hình ảnh ngày 2026-10-15 bằng Playwright + Chromium. Chụp ở 1440×900 và 390 px, với 3 trạng thái: trống, 1 vòng có lỗi nhập, 8 vòng đã lưu.
Bản chuẩn để so: `docs/ui-design/mockup.html#empty|#one|#many` và `SPEC.md`.

Bất biến giữ như SPEC §8: hệ tọa độ 512 px gốc trên-trái, hợp đồng sự kiện cùng `save_nonce`, schema JSON, offline, chữ tiếng Việt. Không push, không merge khi lead chưa duyệt.

## P2 (phải sửa)
1. **Bỏ 2 dòng lặp dưới ảnh.** Chỉ giữ dòng meta "512 × 512 px · Gốc (0, 0) ở góc trên trái · {scale} m/px". Bỏ dòng gợi ý "Nhấn tại tâm hố rồi kéo ra vành…", vì chip chế độ và coach mark đã nói việc này. Bỏ dòng trạng thái "N vòng tròn · Đã chọn … · Tọa độ…", vì badge và tiêu đề ô sửa đã nói việc này. Nếu test JS đang dựa vào `#status`, giữ phần tử đó nhưng ẩn bằng class `sr-only`, không xóa id.
2. **Kiểu nút Hoàn tác / Xóa khi tắt.** Hiện tại lúc tắt nút lại có viền và nền, ngược với lúc bật. Sửa thành: nút tắt vẫn là ghost, không viền, không nền, `opacity: .42`, `cursor: default`.
3. **Thanh công cụ mobile (≤ 720 px) phải nằm trên một hàng.** Segmented control `flex: 1 1 auto`, hai nút trong đó `flex: 1 1 0` với nhãn "Vẽ" / "Chọn / sửa". Hoàn tác và Xóa thành nút icon 44×44, chỉ hiện icon, có `aria-label`. Không được cuộn ngang.
4. **Căn ảnh desktop.** Ảnh đang thu nhỏ để vừa chiều cao (khoảng 620 px) nhưng lại căn giữa cột 768 px, nên mép trái thụt vào khoảng 75 px so với toolbar và meta. Căn ảnh về mép trái của cột, hoặc cho toolbar và meta có cùng chiều rộng với ảnh. Mép trái của toolbar, ảnh và meta phải thẳng hàng.
5. **Ô tọa độ bị cắt số** (desktop hiện "178.30'"). Trong ô hiển thị `Number(v).toFixed(2)`. Khi bấm Áp dụng: nếu chuỗi trong ô vẫn đúng bằng chuỗi đã hiển thị thì giữ giá trị gốc, chỉ dùng giá trị mới cho ô người dùng đã sửa. Ô phải đủ rộng cho "511.00" ở cả 1440 và 390 px.

## P3 (nên sửa)
6. Khi có 0 vòng, ẩn hàng tiêu đề cột (ID / Tâm x / Tâm y / Bán kính).
7. Nhãn chọn ảnh đang cắt mất image id trên mobile. Đổi `format_func` thành `"{id} · {region_group}"` (đưa id lên trước) và giữ ` · {n} vòng` khi ảnh đó có bản nháp.
8. Đường dẫn đã lưu: cắt ở giữa, giữ phần cuối `player_…_<hash>`. Ví dụ `outputs/player_answers/…/player_20261015T003710_bc63…`. Đường dẫn đầy đủ để trong `title`.
9. Nhãn ID trên canvas đang quá nhỏ trên mobile (khoảng 7 px). Cỡ font vẽ trên canvas đổi thành `11 * 512 / rect.width`, nét viền chữ cũng tính theo tỉ lệ đó, để nhãn luôn khoảng 11 px trên màn hình.
10. Số trong danh sách và trong ô sửa dùng cùng số chữ số thập phân (2).

## Không bắt buộc
11. Icon Mặt Trăng ở header, chấm màu trên chip chế độ (cyan khi Vẽ, amber khi Chọn/sửa), vị trí con trỏ trong dòng meta.

## Nghiệm thu
```bash
.venv/bin/python -m unittest discover -s tests -v
for t in tests/test_canvas_*.js; do node "$t"; done
```
- Chụp lại 1440×900 và 390 px ở 3 trạng thái, so với mockup. Các điểm 1–10 phải hết.
- Checklist SPEC §9 vẫn đạt: không cuộn ngang ở 390 px, nút cao ít nhất 44 px, ở 1440×900 không phải cuộn trang, chỉ một nút amber.
