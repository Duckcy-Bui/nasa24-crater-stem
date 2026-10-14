# Hướng dẫn ghi nhãn hố tham chiếu — S1-10

Phụ trách: **Hoàng Quốc Anh**. Phối hợp/nghiệm thu: **Nguyễn Mạnh Tiến**.
Hạn ưu tiên: nhãn thật cho **ảnh demo trước trưa 15/10/2026**; Tiến kiểm tra chéo sau đó.

> [!IMPORTANT]
> Nhãn thủ công và nhãn Robbins phải ghi nguồn **rõ ràng và riêng biệt**. Không gán nhãn Robbins cho hố chưa đối chiếu tọa độ pixel thực tế. Hố chưa chắc chắn phải đánh dấu `_uncertain` trong `crater_id`.

## 1. Ảnh demo và thứ tự ưu tiên

| Ưu tiên | image_id | Scale | Góc tới | Lý do chọn demo |
|---|---|---|---|---|
| **1 (Demo)** | `moon_ap16_m106777343r_c01` | 2.0 m/px | 28.38° (Tây) | Hố rõ nhất, không bóng đổ cực đoan |
| 2 | `moon_ap16_m109134835l_c01` | 2.0 m/px | 7.64° (gần đỉnh đầu) | Cùng vùng Apollo 16, ít bóng, Tiến kiểm tra chéo cặp này |
| 3–5 | `moon_ap15_hia_c01..c03` | 20.0 m/px | 28°–53° | Hố lớn hơn, dễ đối chiếu Robbins |

## 2. Cách chạy script ghi nhãn

```bash
# Ảnh demo mặc định (moon_ap16_m106777343r_c01)
python scripts/label_craters.py

# Chỉ định ảnh khác
python scripts/label_craters.py moon_ap15_hia_c01

# Ghi nhãn từ Robbins (thêm note nguồn)
python scripts/label_craters.py moon_ap15_hia_c01 --source "Robbins 2019 DOI:10.1029/2018JE005592 crater_id=XXXXX"

# Ghi nhãn uncertain hàng loạt (toàn phiên đều uncertain)
python scripts/label_craters.py moon_ap16_m106777343r_c01 --uncertain
```

> [!NOTE]
> Script dùng backend `TkAgg`. Nếu gặp lỗi cửa sổ không mở, đảm bảo đã kích hoạt `.venv` trước khi chạy.

## 3. Thao tác trong cửa sổ

| Thao tác | Tác dụng |
|---|---|
| **Click chuột trái lần 1** | Đặt **TÂM** hố (dấu `+` trắng) |
| **Click chuột trái lần 2** | Đặt điểm trên **VÀNH** miệng hố → bán kính `r` tự tính bằng khoảng cách Euclid |
| **Phím `U`** | Đánh dấu hố vừa ghi là **uncertain** (màu cam) |
| **Phím `Z`** | **Hoàn tác** hố cuối, hoặc hủy click tâm đang chờ |
| **Phím `S`** | **Lưu** và thoát → file `_craters_catalogue.json` |
| **Phím `Q`** | Thoát **không lưu** |

Hố chắc chắn hiển thị **màu xanh cyan**. Hố uncertain hiển thị **màu cam**. Góc dưới ảnh có 2 vòng tham chiếu kích thước `r_min` và `r_max` để so sánh mắt thường.

## 4. Quy tắc ghi nhãn

### 4a. Nhãn thủ công (hố nhỏ < 1 km, thiếu Robbins)

- `reference_source`: `"manual_label_s110; <mô tả ngắn>"`
- `crater_id`: `C1`, `C2`... (hố chắc chắn) hoặc `C1_uncertain` (hố còn ngờ)
- `confidence`: `null` — chưa hiệu chuẩn theo chuẩn nào

**Không ghi:** phương vị nắng, độ chính xác phát hiện hoặc bất kỳ số đo phái sinh nào chưa có.

### 4b. Nhãn từ danh mục Robbins 2019 (hố > 1 km)

1. Tra tọa độ địa lý của hố trong file CSV Robbins.
2. Quy đổi sang tọa độ pixel ảnh 512×512 bằng công thức:
   - `x_px = (lon_crater - lon_topleft) / (lon_bottomright - lon_topleft) * 512`
   - `y_px = (lat_topleft - lat_crater) / (lat_topleft - lat_bottomright) * 512`
   - `r_px = D_km * 1000 / 2 / scale_m_per_px`
3. Dùng file JSON metadata của ảnh để lấy `center_lat`, `center_lon`, `scale_m_per_px`.
4. **Bắt buộc** mở ảnh `.png` và kiểm tra bằng mắt xem hố Robbins có xuất hiện đúng vị trí không.
5. Nếu khớp: ghi vào script với `--source "Robbins 2019 DOI:10.1029/2018JE005592 crater_id=<id_Robbins>"`.
6. Nếu không khớp hoặc còn ngờ: thêm `--uncertain` hoặc bấm `U` sau khi ghi.

> [!WARNING]
> Robbins 2019 chỉ đầy đủ thống kê cho hố **D ≥ 1–2 km**. Các ảnh Apollo 16 ở 2 m/px có dải `D = [20 m, 500 m]` — Robbins **không đủ** cho các ảnh này, dùng nhãn thủ công.

### 4c. Hố đánh dấu uncertain — khi nào dùng

Dùng `uncertain` khi:
- Không thể phân biệt rõ là hố va chạm hay địa hình đá.
- Hố bị bóng đổ che một phần lớn (thường gặp ở Low-Sun).
- Tọa độ Robbins chiếu vào ảnh nhưng không thấy rõ hình tròn.

Tiến kiểm tra chéo sẽ quyết định giữ hoặc bỏ nhãn uncertain.

## 5. Format file đầu ra

File lưu tại `data/processed/<image_id>_craters_catalogue.json`, đạt 100% hợp đồng dữ liệu `validate_crater_set` của [contracts.py](../src/contracts.py):

```json
{
  "schema_version": "1.0",
  "data_kind": "real",
  "image_id": "moon_ap16_m106777343r_c01",
  "source": "catalogue",
  "reference_source": "manual_label_s110; visual inspection on 512x512 PNG",
  "circles": [
    {
      "crater_id": "C1",
      "x": 183.4,
      "y": 256.7,
      "r": 18.2,
      "confidence": null,
      "votes": null
    },
    {
      "crater_id": "C2_uncertain",
      "x": 390.1,
      "y": 110.5,
      "r": 9.5,
      "confidence": null,
      "votes": null
    }
  ]
}
```

## 6. Checklist bàn giao cho Tiến kiểm tra chéo

- [ ] Đã chạy `label_craters.py` cho ảnh demo và lưu file `_craters_catalogue.json`.
- [ ] Tọa độ `(x, y)` nằm trong `[0, 511]`; `r > 0`.
- [ ] Nhãn Robbins đã đối chiếu bằng mắt trên ảnh PNG.
- [ ] Nhãn thủ công có ghi `reference_source = "manual_label_s110; ..."`.
- [ ] Hố không chắc chắn có hậu tố `_uncertain` trong `crater_id`.
- [ ] `validate_crater_set` chạy không báo lỗi (script tự gọi trước khi lưu).
- [ ] Đã commit lên nhánh `s1-10-reference-labels` và tạo PR gán Tiến làm reviewer.
