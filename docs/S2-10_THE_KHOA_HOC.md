# S2-10 — Thẻ Apollo/rover theo vùng ảnh đã xác minh

**Phụ trách:** Hoàng Quốc Anh · **Phối hợp kiểm tra:** Bùi Hải Đức  
**Mã:** `src/science_cards.py` · **Tích hợp:** `src/integration.py`, `app.py`

## 1. Quy tắc vị trí

Chỉ dùng `position` khi đối tượng nằm trong crop 512×512 và tọa độ pixel được xác minh. Không suy vị trí từ tên vùng, không đặt ghim đại diện cho một địa điểm cách xa, và không nói rover/thiết bị “nhìn thấy được” nếu ảnh browse không chứng minh điều đó.

Các crop hiện tại đều không chứa thiết bị. Vì vậy thẻ trong phiên bản này là thẻ **vùng ảnh** với `position: null`, đúng hợp đồng S2-13. Nội dung thẻ nêu rõ thiết bị ở ngoài khung; app không vẽ pin.

## 2. Đối chiếu vị trí

Tọa độ tâm crop lấy từ `docs/S1-06_BANG_ANH_XA.csv`; tọa độ thiết bị lấy từ nguồn trong bảng. Khoảng cách xấp xỉ trên mặt cầu Mặt Trăng, chỉ dùng để quyết định nằm ngoài crop, không phải phép đo trắc địa của ảnh browse.

| Vùng thẻ | Thiết bị/bãi đáp chuẩn | Crop gần nhất | Khoảng cách xấp xỉ | Kết luận |
|---|---|---:|---:|---|
| Apollo 15 Hadley–Apennine | LM Falcon: 26,13239°N, 3,63330°E | `moon_ap15_hia_c02` | 10,3 km | ngoài crop (nửa bề rộng crop 20 m/px chỉ 5,12 km) |
| Apollo 16 Descartes | LM Orion: 8,9734°S, 15,5011°E | `moon_ap16_m109134835l_c02` | 1,8 km | ngoài crop (nửa bề rộng crop 2 m/px chỉ 0,512 km) |
| Lunokhod 1 Mare Imbrium | rover: 38,3152°N, 35,0080°W | `moon_lunokhod1_loc_c01` | 26,0 km | ngoài crop |
| Lunokhod 2 Le Monnier | rover: 25,8323°N, 30,9222°E | `moon_lunokhod2_loc_c01` | 14,7 km | ngoài crop |

## 3. Thẻ được hiện

| Nhóm image_id | Thẻ | Nguồn |
|---|---|---|
| `moon_ap15_*` | Apollo 15 — vùng Hadley–Apennine | NASA, Apollo 15 Mission Details |
| `moon_ap16_*` | Apollo 16 — vùng cao nguyên Descartes | NASA, Apollo 16 Mission Details |
| `moon_lunokhod1_*` | Lunokhod 1 — vùng Mare Imbrium | LROC, *Lunokhod 1 Revisited* |
| `moon_lunokhod2_*` | Lunokhod 2 — vùng Le Monnier | NASA/NSSDC, bảng tọa độ hiện vật nhân tạo trên Mặt Trăng |

Các ảnh Van de Graaff và Mare Frigoris trả `[]`: không gắn câu chuyện Apollo/rover tùy ý vào ảnh.

## 4. Hướng phát triển

Muốn có pin tương tác, cần bổ sung crop mới thực sự bao phủ vị trí thiết bị, lưu metadata/affine và xác minh phép đổi tọa độ sang pixel. Không dùng crop hiện tại để suy hoặc nội suy pin đó.
