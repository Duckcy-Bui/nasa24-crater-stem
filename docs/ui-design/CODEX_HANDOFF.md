# Giao việc cho Codex: triển khai UI mới S1-09 (cách A)

Dán nguyên tệp này cho Codex. Làm trên nhánh `s1-09-interface`. Không push và không merge khi lead chưa duyệt.

## Mục tiêu
Dựng lại giao diện khoanh hố theo `docs/ui-design/SPEC.md`. Bản chuẩn để so là `docs/ui-design/mockup.html`: mở `#empty`, `#one`, `#many`, ở chiều rộng 1440 px và 390 px. Màu và kích thước lấy từ `docs/ui-design/tokens.css`. Nút **Lưu trên máy** nằm trong component và dùng **cách A** (`save_nonce`).

## Bất biến (không được đổi)
- Hệ tọa độ ảnh gốc 512 × 512, gốc (0, 0) ở góc trên-trái. `CraterGeometry` giữ nguyên. x và y kẹp trong 0–511, bán kính lớn hơn 0. *(Cập nhật S3-04, 27/10/2026: tọa độ vòng theo tâm pixel nguyên, xem `docs/S2-13_TICH_HOP.md` mục 3.1.)*
- ID vòng `U{n}`, lịch sử hoàn tác 50 bước, tối đa 500 vòng mỗi ảnh. Schema JSON tải về và tên tệp `{image_id}_player.json` giữ nguyên.
- `apply_canvas_event`, `build_player_crater_set`, `save_player_answers` không đổi chữ ký và không đổi hành vi.
- Chạy offline hoàn toàn: không CDN, không font tải qua mạng. Chữ giao diện bằng tiếng Việt, dùng đúng bảng chữ ở SPEC §7.
- Không có điểm số, độ chính xác hay thẻ khoa học.
- Giữ các id DOM `drawMode`, `editMode`, `deleteCircle`, `undo`, `centerX`, `centerY`, `radius`, `applyEdit`, `error`, `circles`, `editor`, `downloadAnswer`, `craterCanvas`.

## Việc cần làm

### 1. Theme và khung trang
- Tạo `.streamlit/config.toml` theo SPEC §6.1 (theme dark, `primaryColor = "#F3B23C"`, `toolbarMode = "minimal"`).
- Trong `app.py`:
  - Gọi `st.set_page_config(layout="wide")`.
  - Thêm một khối `<style>`: `.block-container { max-width: 1192px; padding-top: 1.25rem }` và font serif hệ thống cho `h1`.
- Header dùng `st.columns([1, 1.25])`:
  - Cột trái: tiêu đề và dòng phụ.
  - Cột phải: selectbox với nhãn `Ảnh {i} / 26 · {region_group}`. `format_func` thêm ` · {n} vòng` khi bản nháp của ảnh đó có vòng.
  - Nút ‹ › là tùy chọn, chỉ làm sau khi xong mọi việc khác.

### 2. Component (`src/crater_canvas/index.html` và `canvas.js`)
- Dựng DOM và CSS theo `mockup.html`:
  - Toolbar dạng segmented control, ảnh vuông, chip chế độ và coach mark (đều `pointer-events: none`).
  - Bảng bên phải gồm danh sách `.row` dạng lưới, form sửa tọa độ (ẩn khi chưa chọn vòng), khu lưu.
  - Chuyển sang bố cục mobile bằng `@media (max-width: 720px)`.
  - Nền `body` là `var(--bg)`, `color-scheme: dark`.
- Sửa `paint()` theo bảng ở SPEC §5.3:
  - Viền tối dưới mọi nét.
  - Vòng thường cyan 1.6, vòng đang chọn amber 2.5, vẽ vòng đang chọn sau cùng.
  - Nhãn ID có viền chữ, núm vành, nét đứt kèm nhãn `r … px` khi đang kéo.
  - Nên làm thêm: vẽ HiDPI bằng `setTransform`.
- Danh sách vòng:
  - Hiện 1 chữ số thập phân.
  - Đổi kiểu dòng đang chọn theo `aria-pressed`.
  - Gọi `scrollIntoView({block: "nearest"})` cho dòng đang chọn.
- Thêm các element mới, mỗi cái một id cố định:
  - `saveAnswer` (nút primary)
  - `saveStatus` (`role="status"`)
  - `saveError` (`role="alert"`)
  - `count`
  - `modeChip`
  - `coach`
  - `emptyState`
  - `noSelection`
  - `cursor`
- Thông báo `[hidden]` phải có `display: none !important`. Lỗi này đã gặp trong mockup.

### 3. Nút Lưu theo cách A
**Phía component (canvas.js):**
- Khi bấm `saveAnswer`, gửi `streamlit:setComponentValue` với value:
  `{image_id, session_token, revision: state.revision, circles: clone(circles), save_nonce}`
  - `save_nonce` là chuỗi ngẫu nhiên tối đa 64 ký tự.
  - **Không** tăng `revision`.
- Tắt `saveAnswer` khi chưa có `state`, ảnh chưa tải xong, hoặc đang kéo (cùng điều kiện với `downloadAnswer`). Lưu 0 vòng là hợp lệ.
- Ở mỗi `streamlit:render`, đọc `args.save_result` trước nhánh so `revision`, để kết quả lưu được cập nhật kể cả khi `revision` không đổi.
  - Hiện `saveStatus` khi `save_result.ok && save_result.revision === state.revision`. Nội dung:
    - “Đã lưu {count} vòng · {time}”
    - Đường dẫn tương đối, rút gọn ở giữa, có `title` chứa đầy đủ
    - Nút sao chép (`navigator.clipboard` bọc try/catch)
  - Ẩn `saveStatus` ngay khi `revision` thay đổi.
  - Khi `save_result.ok === false`, hiện `saveError` với “Chưa lưu được câu trả lời” và `error`.

**Phía `app.py`:**
- Sau khi gọi `apply_canvas_event` thành công cho ảnh **đang mở**, chỉ xét `save_nonce` khi đủ cả ba điều kiện:
  - `event["image_id"] == image_id`
  - `event["session_token"] == token`
  - nonce là `str`, độ dài 1–64
- Nếu nonce khác `st.session_state[f"player_saved_nonce_{image_id}"]`:
  - **Ghi nonce vào session_state trước**, rồi mới gọi `save_player_answers(ROOT / "outputs" / "player_answers", metadata, draft["circles"])`.
  - Thành công: `save_result = {"ok": True, "count": n, "time": datetime.now().strftime("%H:%M"), "path": directory.relative_to(ROOT).as_posix(), "revision": draft["revision"]}`.
  - Lỗi (`OSError`, `ValueError`, `ContractError`): `{"ok": False, "error": str(error), "revision": draft["revision"]}`.
  - Lưu kết quả vào `st.session_state["player_save_results"][image_id]` và truyền vào component qua arg `save_result`.
- Khối “xả sự kiện của ảnh trước” (`previous_event`) **không bao giờ** được gọi lưu.
- Bỏ khỏi `app.py`:
  - `st.button("Lưu câu trả lời trên máy")`
  - `st.success` có đường dẫn tuyệt đối
  - `st.markdown` đếm vòng
  - `st.caption` cuối trang
  - `st.info` “chưa chấm điểm”

  Các nội dung này đã chuyển vào component.
- Thay `st.info` và `st.stop` ở màn hình thiếu bộ ảnh bằng card ở SPEC §5.7, tức artboard “Token & trạng thái”. Vẫn giữ nút `st.button("Chuẩn bị bộ ảnh ngoại tuyến", type="primary")`.

### 4. Test
- `tests/test_canvas_events.js`: thêm các id mới vào `boot()`. Thêm test:
  - Bấm Lưu gửi đúng `revision` hiện tại, đúng `circles` và có `save_nonce`.
  - Nút Lưu bị tắt khi đang kéo hoặc ảnh chưa tải xong.
  - `save_result` có `revision` khớp thì hiện trạng thái đã lưu. Lệch `revision` hoặc `ok: false` thì không hiện.
- `tests/test_app_smoke.py` và `tests/test_app_state.py`: cập nhật các assertion đang tìm nút “Lưu câu trả lời trên máy”. Thêm test, với `outputs` trỏ sang thư mục tạm:
  - Nonce mới thì lưu đúng 1 lần.
  - Chạy lại với cùng nonce thì không lưu thêm.
  - Nonce mới hơn thì lưu thêm 1 lần.
  - Nonce kèm `session_token` sai hoặc `image_id` khác thì bị bỏ qua.
  - Nonce còn nằm trong sự kiện của ảnh trước khi đổi ảnh thì không lưu.
  - Lưu lỗi thì trả `ok: False` và không dừng app.
  - `save_result["path"]` không bắt đầu bằng `/`.

## Nghiệm thu
```bash
python -m unittest discover -s tests -v
node tests/test_canvas_geometry.js
node tests/test_canvas_events.js
streamlit run app.py   # kiểm tra bằng tay trên browser
```
- Ở 1440 × 900: thấy toolbar, ảnh, danh sách, ô sửa và nút Lưu mà không cuộn trang. Không còn khối trắng.
- Ở 390 px: không cuộn ngang, nút cao ít nhất 44 px, thứ tự là ảnh → sửa → lưu → danh sách.
- Cả 3 trạng thái giống `mockup.html#empty`, `#one`, `#many`.
- Lưu xong thì `outputs/player_answers/player_*` có dữ liệu. Thông báo chỉ hiện đường dẫn tương đối.
- Chạy hết checklist ở SPEC §9.

Báo lại cho lead: danh sách tệp đã đổi, log test, ảnh chụp 1440 và 390 px. Không commit, push hay merge khi lead chưa duyệt.
