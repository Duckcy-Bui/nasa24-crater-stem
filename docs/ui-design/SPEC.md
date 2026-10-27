# S1-09 · Thiết kế UI mới “Khoanh hố Mặt Trăng”

Bản thiết kế để lead/Codex tự triển khai. Tài liệu này không sửa `app.py`, `src/` hay `tests/`.

| Tệp | Dùng để |
|---|---|
| `mockup.html` | Mockup offline chạy được, mở thẳng bằng trình duyệt. Thêm `#empty`, `#one` hoặc `#many` vào URL để xem từng trạng thái. Thu cửa sổ ≤ 720 px để xem bản mobile. CSS trong tệp này có thể chép gần như nguyên văn vào component. |
| `tokens.css` | Toàn bộ màu, chữ, khoảng cách, bo góc và kích thước. |
| Canvas Claude Design (private) | https://claude.ai/artifact/E9sMU8tAmqwVqFBwh2tY7v có 6 artboard: Desktop (nhiều vòng, có tương tác), Desktop (1 vòng + lỗi nhập), Desktop (trống), Mobile 390 (nhiều vòng), Mobile 390 (trống), Token & trạng thái. Chủ sở hữu phải chia sẻ link thì người khác mới mở được. |

Ảnh trong mockup lấy từ `../../data/processed/moon_ap16_m113853974r_c01.png`. Thư mục này nằm trong gitignore, nên cần chạy `python scripts/install_s106_dataset.py` trước. Nếu thiếu ảnh, khung ảnh hiện nền tối.

---

## 1. Phản hồi của người dùng và cách giải quyết

| Vấn đề trên bản hiện tại | Cách giải quyết |
|---|---|
| Iframe nền trắng, lệch với theme tối của Streamlit | Toàn app dùng một theme tối (`tokens.css` cộng `.streamlit/config.toml` ở mục 6). Component đặt `color-scheme: dark` và `body { background: var(--bg) }`. |
| Controls xếp dọc nên phải cuộn | Desktop chia 2 cột: ảnh 720 px bên trái, bảng 380 px bên phải. Thanh công cụ nằm ngay trên ảnh. Danh sách vòng cuộn bên trong bảng, tối đa 300 px. Ô sửa tọa độ và nút lưu luôn nằm trong tầm nhìn. |
| Mọi nút trông như nhau | Chia 4 cấp. Primary amber chỉ có một nút: **Lưu trên máy**. Secondary: Tải JSON, Áp dụng tọa độ. Ghost: Hoàn tác. Ghost đỏ cam: Xóa. Chế độ Vẽ / Chọn-sửa là segmented control, không dùng nút rời. |
| Thiếu empty state | Khi chưa có vòng: coach mark trên ảnh, minh họa và 3 bước trong bảng, gợi ý trong ô sửa tọa độ (mục 4). |
| Đường dẫn lưu quá dài | Hiện thông báo “Đã lưu N vòng · HH:MM”. Đường dẫn là tương đối từ gốc repo, rút gọn ở giữa bằng `…`. Đường dẫn đầy đủ nằm ở `title` và nút sao chép. Không in đường dẫn tuyệt đối `/home/...`. |
| Ô thông tin xanh to cho “chưa chấm điểm” | Gộp thành một dòng chú thích nhỏ ở cuối khu lưu. Không có điểm, độ chính xác giả hay thẻ khoa học. |

## 2. Hướng thiết kế

**Bàn quan sát Mặt Trăng.** Nền gần đen ánh lam để ảnh xám của LROC nổi lên như trên màn hình quan sát. Giao diện tự lùi lại phía sau, còn ảnh là trọng tâm.

- **Hai màu chú thích, cả hai mượn từ canvas.js hiện tại.** Vòng thường màu cyan `#5FE3F5`, vòng đang chọn màu vàng amber `#FFD84D`. Mọi nét vẽ có viền tối bên dưới để vẫn đọc được trên vùng regolith sáng. Vòng đang chọn còn khác ở độ dày nét (2.5 so với 1.6) và có núm vành, nên phân biệt được không chỉ nhờ màu.
- **Một accent duy nhất**: amber `#F3B23C`, dùng cho nút Lưu trên máy, viền focus và dòng đang chọn. Cyan chỉ dùng cho dữ liệu trên ảnh.
- **Chữ** dùng font hệ thống, không tải qua mạng:
  - Tiêu đề dùng serif kiểu atlas: Iowan / Palatino / Noto Serif / DejaVu Serif.
  - Giao diện dùng `system-ui`.
  - Mọi con số dùng mono với `font-variant-numeric: tabular-nums` để các cột x, y, r thẳng hàng.
  - Cả ba stack đều có glyph tiếng Việt trên Linux, macOS và Windows.
- Không gradient trang trí, không emoji, không card có viền trái. Icon là SVG nét 1.8, kích thước 18 px, viết inline.

## 3. Token

Xem `tokens.css`. Tóm tắt các token chính:

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--bg` | `#0A0C0F` | Nền trang, nền iframe |
| `--surface-0 / 1 / 2 / 3` | `#0E1115 / #111419 / #171B21 / #1E232B` | Ô nhập và rãnh · bảng · nút phụ và hover · hover mạnh và badge |
| `--line / -2 / -3 / -4` | `#222831 / #262C35 / #303743 / #3D4552` | Viền bảng · khung ảnh · viền control · viền khi hover |
| `--text / -2 / -3` | `#ECEAE4 / #A7ADB6 / #7D848E` | Tương phản trên surface-1 lần lượt 15.3 / 8.2 / 4.9 : 1 |
| `--accent`, `--on-accent` | `#F3B23C`, `#1A1205` | CTA, focus. Chữ trên nền amber đạt 9.9 : 1 |
| `--circle`, `--circle-selected` | `#5FE3F5`, `#FFD84D` | Vòng thường, vòng đang chọn |
| `--danger`, `--success` | `#FF8A7A`, `#6FD69B` | Lỗi, đã lưu |
| Chữ | display 26 (mobile 22) · heading 15/650 · body 14 (mobile 15) · small 12 · label 11 in hoa, giãn 0.06em · mono 13 | |
| Khoảng cách | Bậc 4 px: 4 8 12 16 20 24 28 32 | |
| Bo góc | Control 8 (mobile 9) · chip 6 · ảnh 12 · bảng 14 | |
| Chiều cao | Control 40 (mobile 44) · CTA 44 (mobile 48) | Mục tiêu chạm trên mobile ≥ 44 px |

Focus: `outline: 2px solid var(--focus); outline-offset: 2px` cho mọi phần tử bấm được, chỉ áp dụng với `:focus-visible`.

## 4. Bố cục

### Desktop (iframe rộng hơn 720 px)

```
┌ Header (Streamlit) ─────────────────────────────────────────────────────┐
│ ◎ Khoanh hố Mặt Trăng                  Ảnh 19 / 26 · <nhóm vùng>         │
│   NASA 24 · Nhóm 2 · Mở ảnh, …     [‹] [ moon_ap16_…_c01            ▾ ] [›]│
├──────────────────────────────────────────── max-width 1128 ─────────────┤
│ [◎ Vẽ vòng tròn | ➤ Chọn / sửa]   ↶ Hoàn tác  🗑 Xóa │ Vòng tròn (8)  đv px │
│ ┌──────────────────────────────────────────────┐ │ ID  Tâm x Tâm y  B.kính│
│ │ ● Chọn / sửa: kéo tâm để dời, …              │ │ U1  105.4 200.2  108.6 │
│ │                                              │ │ U2  178.3 211.8   31.5 │← đang chọn
│ │            ẢNH 512×512, vuông                 │ │ …  (cuộn, tối đa 300 px)│
│ │            tối đa 720 × 720                   │ ├────────────────────────┤
│ │                                              │ │ Sửa tọa độ U2  x,y 0–511│
│ │                                              │ │ [x px] [y px] [r px]   │
│ └──────────────────────────────────────────────┘ │ [  Áp dụng tọa độ    ] │
│ 512 × 512 px · gốc (0,0) góc trên-trái · 2 m/px  ├────────────────────────┤
│                         con trỏ  x 231.4 · y 104.0│ Câu trả lời hiện tại  8│
│                                                  │ [■ Lưu trên máy][Tải JSON]
│                                                  │ ✓ Đã lưu 8 vòng · 19:47│
│                                                  │   outputs/…/player_…   │
│                                                  │ chú thích nhỏ           │
└──────────────────────────────────────────────────┴────────────────────────┘
```

- Cột ảnh: `flex: 999 1 560px; max-width: 720px`. Cột bảng: `flex: 1 1 340px; max-width: 400px`. Khoảng cách giữa hai cột 28 px. Hai cột cao bằng nhau (`align-items: stretch`). Phần danh sách chiếm chỗ còn trống.
- Ảnh luôn vuông (`aspect-ratio: 1`), bo 12, viền `--line-2`, nền `#000`.
- Dòng meta dưới ảnh gồm kích thước, gốc tọa độ, `scale_m_per_px` lấy từ metadata, và vị trí con trỏ.

### Mobile (iframe ≤ 720 px; kiểm thử ở 390 px)

Thứ tự từ trên xuống:

1. Header (tiêu đề 22 px, ẩn phần mô tả dài)
2. Hàng chọn ảnh `[‹] [select] [›]`
3. Thanh công cụ: segmented control “Vẽ | Chọn / sửa” chiếm hết chiều rộng còn lại, cạnh đó 2 nút icon 44 × 44 cho Hoàn tác và Xóa (có `aria-label`)
4. Ảnh rộng toàn bộ, 358 px
5. Dòng meta (bỏ vị trí con trỏ)
6. Card **Sửa tọa độ**
7. Card **Lưu**: Lưu trên máy (48 px) rồi Tải JSON, xếp dọc, rộng toàn bộ
8. Card **Vòng tròn** chứa danh sách đầy đủ, không cuộn trong card

Bảng desktop tách thành các card riêng bằng `order` (edsec 1, savesec 2, listsec 3). Ẩn chip chế độ trên ảnh. Coach mark trải rộng từ cạnh trái tới cạnh phải ảnh. Lề hai bên 16 px. Trang không được cuộn ngang.

Thanh lưu không dính đáy màn hình (no sticky) vì iframe Streamlit tự giãn chiều cao, nên `position: sticky` bên trong iframe không hoạt động. Vì vậy đặt khu lưu ngay sau ô sửa và trước danh sách dài.

## 5. Thành phần và trạng thái

### 5.1 Chọn ảnh (Streamlit)
- `st.selectbox` với nhãn “Ảnh {i} / 26 · {region_group}”. Hiện `format_func` là `"{id} · {region_group}"`. Thêm ` · {n} vòng` khi ảnh đó đã có bản nháp (`drafts[id]["circles"]`), để người chơi thấy ảnh nào đã làm.
- Nút ‹ › để chuyển ảnh là **tùy chọn**: `st.button` đổi chỉ số trong `session_state`. Tắt nút ở ảnh đầu và ảnh cuối.

### 5.2 Thanh công cụ
- Segmented control: hai `<button aria-pressed>` trong cùng một rãnh. Nút đang bật có nền `#232934` và viền trong `#3A4250`.
- Hoàn tác: ghost, tắt khi `history` rỗng. Xóa vòng đã chọn: ghost đỏ cam, tắt khi chưa chọn vòng nào.
- Giữ nguyên các id `drawMode`, `editMode`, `undo`, `deleteCircle` để canvas.js chỉ phải đổi tối thiểu.

### 5.3 Khung ảnh và cách vẽ trong canvas.js
Hệ tọa độ **giữ nguyên**: ảnh gốc 512 × 512, gốc (0, 0) ở góc trên-trái, `CraterGeometry.canvasToImage` dùng như cũ. *(Cập nhật S3-04, 27/10/2026: tọa độ vòng theo tâm pixel nguyên, xem `docs/S2-13_TICH_HOP.md` mục 3.1.)*

Các thông số vẽ trong `paint()`:

| Phần tử | Thông số |
|---|---|
| Thứ tự vẽ | Vòng thường trước, vòng đang chọn sau cùng để nằm trên |
| Viền tối | Mỗi vòng vẽ một nét `rgba(0,0,0,.55)` dày `w + 2` trước, rồi mới vẽ nét màu |
| Vòng thường | `#5FE3F5`, `w = 1.6` |
| Vòng đang chọn | `#FFD84D`, `w = 2.5` |
| Dấu tâm | Dấu cộng ±4, nét 1.5, cùng màu với vòng |
| Nhãn ID | `600 11px` font mono, tô màu `#8DEFFB` (đang chọn: `#FFD84D`). Viền chữ `rgba(10,12,15,.85)` dày 3 (`strokeText` trước `fillText`). Đặt tại `(x + 0.72r + 3, y − 0.72r − 3)`, giới hạn trong `[0, 482] × [13, 512]` |
| Núm vành | Ô vuông 8 × 8 màu `#FFD84D`, viền `#0A0C0F` 1.5, tại `(min(511, x + r), y)`. Chỉ hiện ở vòng đang chọn |
| Đang kéo để vẽ | Nét đứt `setLineDash([4, 4])` màu cyan, cộng nhãn “r 19.0 px” trên nền `rgba(10,12,15,.86)` cạnh con trỏ |

- **Nên làm (không bắt buộc), để nét sắc trên màn hình lớn và HiDPI**: đặt `canvas.width = rect.width * devicePixelRatio` rồi `ctx.setTransform(scale, 0, 0, scale, 0, 0)` với `scale = canvas.width / 512`. Như vậy vẫn vẽ theo tọa độ ảnh, còn độ dày nét tính theo CSS px (chia `w` cho `rect.width / 512`). Hit-test hiện dùng `getBoundingClientRect`, nên không bị ảnh hưởng.
- Lớp HTML phủ trên canvas, đều có `pointer-events: none`:
  - **Chip chế độ** ở góc trên-trái, có chấm cyan hoặc amber. Nội dung: “Vẽ: nhấn tâm hố, kéo ra vành” / “Chọn / sửa: kéo tâm để dời, kéo vành để đổi bán kính”. Chip này thay đoạn `.hint` hiện tại.
  - **Coach mark** ở giữa đáy ảnh, chỉ hiện khi chưa có vòng nào.
- Vị trí con trỏ (tùy chọn): khi `pointermove` mà không kéo, ghi “con trỏ  x 231.4 · y 104.0” vào dòng meta. Khi `pointerleave` thì ghi “—”.

### 5.4 Danh sách vòng
- Mỗi dòng là một `<button aria-pressed>` dạng lưới `56px repeat(3, 1fr)`, căn phải, font mono, hiện 1 chữ số thập phân. Chip ID màu `#10303A` / `#8DEFFB`.
- Hover: nền `--surface-2`. Đang chọn: nền `#2A2414`, chữ `#FFE3A3`, chip ID nền amber.
- Bấm vào dòng thì chọn vòng đó và chuyển sang chế độ Chọn / sửa (giữ hành vi cũ).
- Hàng tiêu đề cột: ID · Tâm x · Tâm y · Bán kính. Badge số lượng nằm cạnh chữ “Vòng tròn”.

### 5.5 Sửa tọa độ
- 3 ô nhập (`id` giữ nguyên: `centerX`, `centerY`, `radius`), có hậu tố “px”, font mono. Giá trị hiển thị là giá trị gốc như hiện tại.
- Khi chưa chọn vòng, ẩn form và hiện một dòng gợi ý (xem bảng chữ ở mục 7). Không hiện 3 ô trống bị tắt.
- Lỗi:
  - Ô sai có viền `--danger` và quầng `rgba(255,138,122,.14)`, cộng `aria-invalid="true"`.
  - Dòng `role="alert"` có icon, nội dung giữ như thông báo hiện tại.
  - Trong mockup chỉ tô đỏ ô bán kính. Khi triển khai, tô đúng ô bị sai.

### 5.6 Khu lưu
- Dòng tóm tắt “Câu trả lời hiện tại · **N vòng tròn**” thay cho `st.markdown` hiện tại.
- Nút **Lưu trên máy** là primary amber, chiếm phần rộng còn lại. Nút **Tải JSON** là secondary. Lưu 0 vòng vẫn hợp lệ, nên cả hai nút luôn bật khi ảnh đã tải xong và không đang kéo.
- Sau khi lưu thành công, hiện hộp `role="status"` gồm:
  - ✓ “Đã lưu N vòng · HH:MM” (giờ địa phương)
  - Nút icon sao chép
  - Đường dẫn `Path.relative_to(ROOT)`, rút gọn giữa thành `outputs/player_answers/…/player_2026…_e6f7…`, có `title` chứa đường dẫn đầy đủ

  Ẩn hộp này ngay khi `circles` thay đổi sau lần lưu. Như vậy người chơi luôn biết bản đang thấy đã được lưu hay chưa.
- Lưu thất bại: hộp `role="alert"` nền `--danger-bg` với nội dung “Chưa lưu được câu trả lời” và lý do ngắn.
- Chú thích cuối: “Bản nháp giữ trong phiên này. Lưu hoặc tải JSON trước khi đóng trang. Chưa chấm điểm vì bộ ảnh chưa có đáp án đã xác minh.”

### 5.7 Danh sách trạng thái

| Trạng thái | Hiển thị |
|---|---|
| Chưa có bộ ảnh | Một card ở giữa: icon Mặt Trăng, “Chuẩn bị 26 ảnh Mặt Trăng”, CTA amber “Chuẩn bị bộ ảnh ngoại tuyến”, lệnh dự phòng dạng mono. Xem artboard Token & trạng thái. |
| Đang mở ảnh | Khung ảnh `--surface-1`, vòng xoay cyan, chữ “Đang mở ảnh…”. Tắt Lưu và Tải. |
| Lỗi ảnh | Khung viền đứt đỏ, “Không mở được ảnh”, “Chọn lại ảnh hoặc kiểm tra bộ dữ liệu.” |
| Trống (0 vòng) | Chế độ mặc định là Vẽ, có coach mark trên ảnh. Bảng hiện minh họa và 3 bước. Ô sửa tọa độ hiện gợi ý. Badge “0”. |
| 1 vòng | Như nhiều vòng nhưng danh sách chỉ 1 dòng, không có khoảng trống thừa. Vòng vừa vẽ được chọn tự động (giữ hành vi cũ). |
| Nhiều vòng | Danh sách cuộn bên trong (desktop). Cuộn để thấy dòng đang chọn (`scrollIntoView({block: "nearest"})`). |
| Đang kéo | Nét đứt và nhãn bán kính. Tắt Tải JSON (giữ như cũ). |
| Đã đủ 500 vòng | Dòng lỗi “Mỗi ảnh hỗ trợ tối đa 500 vòng tròn.” ở vị trí của lỗi nhập |
| Lỗi hợp đồng dữ liệu (`ContractError`) | Hộp trung tính hoặc lỗi trong Streamlit với cùng token màu. Giữ nguyên nội dung hiện tại. |

## 6. Gợi ý triển khai trong Streamlit

1. **Theme**: tạo `.streamlit/config.toml`:
   ```toml
   [theme]
   base = "dark"
   primaryColor = "#F3B23C"
   backgroundColor = "#0A0C0F"
   secondaryBackgroundColor = "#111419"
   textColor = "#ECEAE4"
   font = "sans serif"

   [client]
   toolbarMode = "minimal"
   ```
2. **Trang**: `st.set_page_config(layout="wide")`. Chèn một khối `<style>` nhỏ qua `st.markdown(..., unsafe_allow_html=True)`:
   - `.block-container { max-width: 1192px; padding-top: 1.25rem; }`
   - Font serif cho tiêu đề `h1`
   - Không chèn font từ mạng
3. **Header**: `st.columns([1, 1.25])`. Cột trái là tiêu đề và dòng phụ. Cột phải là selectbox, có thể thêm nút ‹ ›. Trên mobile Streamlit tự xếp dọc các cột.
4. **Component** (`index.html` + `canvas.js`): chứa toolbar, ảnh, bảng, ô sửa và khu lưu, dựng theo DOM của `mockup.html`. Đổi trong `index.html`:
   - Đặt `color-scheme: dark`
   - Thêm tokens
   - Cột ảnh và cột bảng dùng flex-wrap
   - Thêm `@media (max-width: 720px)`
   - Bỏ `.hint`
   - Danh sách vòng dùng `.row`
5. **Nút Lưu trên máy**. Lead đã chọn **cách A** (2026-10-14). Cách B chỉ giữ lại để tham khảo.
   - **A (đã chọn, không phải đổi hợp đồng dữ liệu)**:
     - Component gửi thêm khóa `save_nonce` (chuỗi ngẫu nhiên) trong cùng value: `{image_id, session_token, revision, circles, save_nonce}`. `apply_canvas_event` chỉ đọc 4 khóa đầu nên bỏ qua khóa mới.
     - `app.py` so `event.get("save_nonce")` với `st.session_state[f"player_saved_nonce_{image_id}"]`. Nếu mới thì gọi `save_player_answers`, rồi truyền kết quả về component qua arg `save_result={"ok": True, "count": n, "time": "19:47", "path": rel, "revision": rev}` (hoặc `{"ok": False, "error": msg}`).
     - canvas.js hiện hộp đã lưu khi `save_result.revision === state.revision`.
     - Cần thêm test: nonce trùng không được lưu hai lần.
   - **B (không dùng; ít đổi nhất)**: giữ `st.button("Lưu trên máy", type="primary", use_container_width=True)` ngay dưới component. `primaryColor` sẽ tô nút màu amber. Thay `st.success(đường dẫn dài)` bằng `st.toast("Đã lưu N vòng")` cộng `st.caption` chứa đường dẫn tương đối. Cách này làm Lưu và Tải JSON nằm tách xa nhau, nên chỉ là phương án dự phòng.
6. Bỏ `st.info` “chưa chấm điểm” và `st.caption` cuối trang. Nội dung đó đã chuyển vào chú thích của khu lưu.

## 7. Chữ trên giao diện (tiếng Việt)

| Vị trí | Chữ |
|---|---|
| Tiêu đề / dòng phụ | Khoanh hố Mặt Trăng · NASA 24 · Nhóm 2 · Mở ảnh, khoanh hố và lưu câu trả lời |
| Chọn ảnh | Ảnh {i} / 26 · {region_group} · aria: Chọn ảnh để mở · Ảnh trước · Ảnh tiếp theo |
| Chế độ | Vẽ vòng tròn (mobile: Vẽ) · Chọn / sửa |
| Thao tác | Hoàn tác · Xóa vòng đã chọn · Áp dụng tọa độ · Lưu trên máy · Tải JSON |
| Chip chế độ | Vẽ: nhấn tâm hố, kéo ra vành · Chọn / sửa: kéo tâm để dời, kéo vành để đổi bán kính |
| Coach mark | Nhấn vào tâm một hố, kéo ra tới vành rồi thả tay (mobile: Chạm vào …) |
| Trống | Chưa có vòng tròn nào · 1. Nhấn vào tâm một hố trên ảnh. · 2. Giữ và kéo ra tới vành hố. · 3. Thả tay. Vòng mới hiện ở danh sách này. |
| Bảng | Vòng tròn · đơn vị px, ảnh gốc · ID · Tâm x · Tâm y · Bán kính · Sửa tọa độ U2 · x, y: 0–511 |
| Chưa chọn vòng | Chọn một vòng trong danh sách hoặc trên ảnh để sửa tọa độ. / (0 vòng) Vẽ vòng đầu tiên, sau đó có thể sửa tọa độ chính xác ở đây. |
| Meta | 512 × 512 px · gốc (0, 0) ở góc trên-trái · {scale} m/px · con trỏ x … · y … |
| Lưu | Câu trả lời hiện tại · N vòng tròn · Đã lưu N vòng · HH:MM · Sao chép đường dẫn · Chưa lưu được câu trả lời |
| Chú thích | Bản nháp giữ trong phiên này. Lưu hoặc tải JSON trước khi đóng trang. Chưa chấm điểm vì bộ ảnh chưa có đáp án đã xác minh. |

## 8. Những gì không được đổi
- Hệ tọa độ 512 px với gốc ở góc trên-trái, kẹp x và y trong 0–511, bán kính lớn hơn 0.
- ID vòng dạng `U{n}`, lịch sử hoàn tác 50 bước, tối đa 500 vòng mỗi ảnh.
- Schema JSON tải về, tên tệp `{image_id}_player.json`, và cấu trúc `save_player_answers`.
- Hợp đồng sự kiện `streamlit:setComponentValue` (chỉ được thêm khóa, như cách A).
- Chạy hoàn toàn offline: không CDN, không font tải từ mạng, không ảnh từ bên ngoài.

## 8a. Cập nhật R2 (2026-10-15): bản đồ to hơn và zoom
Phần này thay §4 ở 3 điểm:
- Khung ảnh tối đa 840 px (`--stage-max`), nội dung rộng 1248 px.
- Có chế độ thứ 3 "Kéo ảnh", cộng cụm nút zoom ở góc trên-phải của ảnh.
- Màn 900 px được phép cuộn nhẹ.

Chi tiết và test: `UI_FIX_R2.md`.

## 8b. Ghi chú phạm vi và dữ liệu mẫu
- **Vòng trong mockup là vòng minh họa, không phải ground truth.** Các vòng U1–U8 trong `mockup.html` và trên canvas Claude Design được đặt bằng mắt lên `moon_ap16_m113853974r_c01`, chỉ để thể hiện bố cục và các trạng thái.
  - Đây không phải danh mục hố tham chiếu hay đáp án. Không dùng để chấm điểm, đánh giá Hough, hay làm fixture "đúng".
  - Không đưa chúng vào app thành vòng mặc định hoặc vòng gợi ý. Ảnh luôn mở với danh sách vòng của người chơi, bắt đầu trống.
  - Nếu test cần dữ liệu vòng, đặt tên rõ là vòng thao tác thử (ví dụ `demo_circles`), giống cách bằng chứng S1-09 đang làm.
- **Phạm vi dạy học:** đây là công cụ để học sinh tự khoanh hố. Chữ trên giao diện không được hàm ý đúng hay sai: không "chính xác", không "khớp", không điểm số, không màu xanh/đỏ theo độ đúng. Màu xanh chỉ dùng cho trạng thái "đã lưu", màu đỏ cam chỉ dùng cho lỗi nhập hoặc lỗi hệ thống. Dòng "Chưa chấm điểm vì bộ ảnh chưa có đáp án đã xác minh" giữ nguyên tới khi có đáp án đã xác minh.

## 9. Checklist nghiệm thu UI
- [ ] Không còn khối trắng: iframe và trang cùng nền `#0A0C0F` ở cả desktop và 390 px.
- [ ] Ở 1440 × 900, thấy được ảnh, toolbar, danh sách, ô sửa và nút Lưu mà không phải cuộn trang (Streamlit chrome đã ở chế độ minimal).
- [ ] Ở 390 px, không cuộn ngang. Mọi nút cao ít nhất 44 px. Thứ tự là ảnh → sửa → lưu → danh sách.
- [ ] Chỉ có một nút amber trên màn hình.
- [ ] Trạng thái trống có coach mark trên ảnh và hướng dẫn trong bảng.
- [ ] Thông báo đã lưu không chứa đường dẫn tuyệt đối và không làm vỡ bố cục.
- [ ] Vòng đang chọn phân biệt được bằng cả độ dày nét lẫn núm vành, không chỉ bằng màu.
- [ ] Mọi thao tác dùng được bằng bàn phím. Focus ring amber hiện rõ.
- [ ] Các test hiện có của canvas, geometry và player_annotations vẫn qua.
