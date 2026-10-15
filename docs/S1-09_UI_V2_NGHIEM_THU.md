# S1-09 — Nghiệm thu UI v2 theo Claude Design

Ngày kiểm tra: 14/10/2026. Nhánh: `s1-09-interface`. Bản này tiếp nối S1-09 đã có ở commit `45c1e9b`; bằng chứng phiên bản trước giữ nguyên trong `docs/evidence/s1-09/`.

## Thiết kế và phân vai

Claude chạy trong pane `nasa24-design` của Herdr, dùng Claude Design để dựng các trạng thái desktop/mobile và xuất bàn giao. Mở [canvas thiết kế](https://claude.ai/artifact/E9sMU8tAmqwVqFBwh2tY7v) bằng tài khoản được cấp quyền, hoặc xem [mẫu HTML ngoại tuyến](ui-design/mockup.html) sau khi chuẩn bị bộ ảnh. Các hash `#empty`, `#one`, `#many` đổi trạng thái mẫu; đây là mẫu bố cục, không phải ứng dụng lưu dữ liệu.

Codex triển khai ứng dụng thật; agent `nasa24-qa` viết riêng và kiểm định 16 test backend, 8 AppTest và 9 kịch bản JS về nút lưu. Root chạy bộ Python cùng thử nghiệm trình duyệt trên server local mới khởi động. Agent QA kiểm nguồn và đọc bằng chứng sau đó; [review cuối](evidence/s1-09-ui-v2/independent_review.md) không còn finding cần sửa trong phạm vi nghiệm thu.

Người dùng đã chọn cách A: nút lưu nằm trong component, gửi `save_nonce`. `SPEC.md`, `tokens.css` và `CODEX_HANDOFF.md` giữ vai trò tài liệu thiết kế. Những khác biệt triển khai có chủ ý: theme trang được áp dụng bằng CSS cục bộ; ảnh desktop giới hạn 620 px để nút lưu vừa màn hình 1440×900; nhãn chọn ảnh giữ **Chọn ảnh để mở**; bảng vòng hiển thị 2 chữ số thập phân. Chưa thêm điều hướng ảnh bằng nút trước/sau, tọa độ con trỏ, nhãn bán kính trong lúc kéo hoặc canvas HiDPI; các phần này không ảnh hưởng hợp đồng S1-09.

## Hành vi đã triển khai

- Nền tối đồng nhất giữa Streamlit và component; font giao diện dễ đọc, font số tách riêng; không tải font hay script từ CDN.
- Toolbar vẽ/sửa/hoàn tác/xóa; ảnh vuông; bảng chọn vòng, form chỉnh chính xác chỉ hiện khi có vòng được chọn.
- Nhập tọa độ không hợp lệ đánh dấu đúng ô lỗi bằng viền và `aria-invalid`; thông báo lỗi liên kết với từng ô, bộ vòng hiện tại không bị thay đổi.
- Vòng thường xanh lam, vòng được chọn vàng và vẽ sau cùng; nét/nhãn có viền tối để đọc trên ảnh sáng.
- Mobile 390 px không tràn ngang, thứ tự ảnh → chỉnh → lưu → danh sách; các nút thao tác và dòng chọn vòng cao ít nhất 44 px. Danh sách desktop tự cuộn đến vòng đang chọn, giữ nguyên vị trí trang.
- Lưu có trạng thái chờ, thành công hoặc lỗi; hiển thị đường dẫn tương đối. Sửa bản nháp sẽ ẩn xác nhận lần lưu cũ. Mỗi lần lưu mới tạo thư mục riêng.
- Yêu cầu lưu chỉ hợp lệ với ảnh/phiên/revision và bộ vòng hiện tại; ghi nhận nonce trước thao tác ghi file và bỏ qua yêu cầu đã xử lý. Chuyển ảnh không tự lưu sự kiện của ảnh trước.

`geometry.js`, `player_annotations.py` và `contracts.py` giữ nguyên so với bản trước. Schema 1.0, hệ tọa độ ảnh gốc 512×512, giới hạn 500 vòng và hoàn tác 50 bước giữ nguyên. Bản nháp vẫn chỉ tồn tại trong phiên; chưa nhập lại JSON và chưa chấm điểm.

## Kết quả kiểm tra

| Phạm vi | Kết quả | Bằng chứng |
| --- | --- | --- |
| Python: dữ liệu, tiền xử lý, Hough, hợp đồng, UI state và lưu | 131/131 PASS, không skip | [Log unittest](evidence/s1-09-ui-v2/unittest.log) |
| JS mock: nonce, khóa thao tác chờ lưu, ACK, lỗi/thử lại, cách ly ảnh/phiên | 9/9 PASS | [Log JS](evidence/s1-09-ui-v2/canvas_save.log) |
| Chromium thật: vẽ, đổi kích thước, nhập số, kéo tâm/vành, xóa, chuyển ảnh, lưu/đọc lại | 7 nhóm PASS, không lỗi JavaScript | [Browser report](evidence/s1-09-ui-v2/browser_checks.json) |
| Chromium thật: 0/1/8 vòng, hai lần lưu, desktop 1440×900, mobile 390 px, trạng thái đã sửa, vòng chọn hiện trong danh sách, kích thước vùng nhấn và nhập số sai | 10 nhóm PASS | [Visual report](evidence/s1-09-ui-v2/visual_checks.json) |

10 JSON tải về được [kiểm định lại bằng hợp đồng nguồn](evidence/s1-09-ui-v2/contracts_readback.json); file lưu trên đĩa khớp bản JSON tải ngay sau chỉnh. Các báo cáo và ảnh chụp thuộc phiên UI v2; kết quả mock/source không được dùng thay cho thử nghiệm trình duyệt. Thử nghiệm dùng Chromium headless; chưa kiểm trình duyệt khác hoặc thiết bị cảm ứng thật.

Xem [desktop 8 vòng](evidence/s1-09-ui-v2/desktop.png), [mobile 8 vòng](evidence/s1-09-ui-v2/mobile.png) và [desktop trống](evidence/s1-09-ui-v2/empty.png). Các vòng này là thao tác kiểm thử bố cục và lưu, không phải nhãn NASA hay ground truth. Bộ ảnh vẫn có `reference_status=unavailable`.

## Chạy lại

```bash
python scripts/check_contracts.py
python -m unittest discover -s tests -v
node tests/test_canvas_save.js
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Mở `http://127.0.0.1:8501`, tải lại trang để nhận UI mới. Thử vẽ, sửa, lưu, đổi ảnh rồi quay lại; mở `craters.json` trong đường dẫn đã lưu và đối chiếu `image_id`, tọa độ. Lưu hoặc tải JSON trước khi đóng/tải lại trang vì bản nháp trong phiên sẽ mất; các thư mục kết quả đã lưu vẫn còn.
