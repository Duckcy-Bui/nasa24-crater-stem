# S2-03 — Chốt tập điều chỉnh, tập kiểm tra và nhãn tham chiếu

**Phụ trách:** Hoàng Quốc Anh  
**Nghiệm thu:** Nguyễn Mạnh Tiến  
**Ngày:** 23/10/2026  
**Đầu ra:** `data/s203_split/manifest_split.json`, `data/s203_split/label_index.json`

---

## 1. Mục tiêu

Tách 26 crops thành **tập điều chỉnh (tuning)** và **tập kiểm tra (holdout)** để:

- Tuning: điều chỉnh tham số Hough, ngưỡng shading, ngưỡng confidence.
- Holdout: chỉ báo cáo kết quả cuối. **Tuyệt đối không dùng holdout để chỉnh tham số.**

---

## 2. Nguyên tắc phân tập

### 2.1 Nhóm theo product_id (không tách crops cùng địa điểm)

Crops từ cùng file TIF gốc (`product_id`) **luôn vào cùng một tập**.  
Điều này đảm bảo:
- Crops chồng lấp (overlapping crops) không bị tách vào 2 tập khác nhau.
- Crops cùng địa điểm dưới góc nắng khác nhau không bị tách tập (mỗi product_id là một góc nắng riêng).

Đơn vị phân tập = **product_id group** (không phải ảnh riêng lẻ).

### 2.2 Phân bố

| Tập | Groups | Crops | Có nhãn | Tỉ lệ |
|-----|--------|-------|---------|--------|
| **Tuning** | 11 | 18 | 1 | ~69 % |
| **Holdout** | 5 | 8 | 0 | ~31 % |
| **Tổng** | 16 | 26 | 1 | 100 % |

### 2.3 Holdout groups (product_id)

| Product ID | STT | Vùng | sun_inc | Lý do holdout |
|-----------|-----|------|---------|---------------|
| `M132732855L` | 13 | Ap16 Highlands | 87.70° W | Grazing extreme — shadow test |
| `M132732855R` | 14 | Ap16 Highlands | 87.78° W | Cặp L/R cùng pass — giữ cùng tập |
| `M113853974R` | 11 | Ap16 Highlands (Đông) | 54.72° E | East-side candidate — kiểm chéo hướng nắng |
| `NAC_ROI_APOLLO15LOC_...` | 2 | Ap15 Low-Sun | null | Mosaic quality=none; đa dạng region |
| `NAC_ROI_LUNOKOD2LOA_...` | 5 | Lunokhod 2 Low-Sun | null | quality=none; khác địa hình |

---

## 3. Nhãn tham chiếu (reference labels)

### 3.1 Trạng thái hiện tại

Chỉ có **1 ảnh** có nhãn tham chiếu: `moon_ap16_m106777343r_c01` (tập **tuning**).

| Ảnh | Tập | File nhãn | Số hố | Uncertain | Trạng thái |
|-----|-----|-----------|-------|-----------|-----------|
| `moon_ap16_m106777343r_c01` | tuning | `moon_ap16_m106777343r_c01_craters_catalogue.json` | 4 | 1 | `sparse_unreviewed` |

> ⚠ **Lưu ý (đính chính 19/10/2026):** Ảnh kiểm hướng nắng của Hưng có vòng chọn thủ công `x249,y180,r120` trong `data/s111_sun_checks.json`. Vòng này **không phải** nhãn đầy đủ để đánh giá.  
> Tiến cần kiểm chéo overlay trước khi dùng nhãn cho báo cáo chính thức.

### 3.2 Giải thích về nhãn thưa

Nhãn hiện tại là **sparse** (thưa):

- **Recall** đo trên nhãn đã biết: TP / (TP + FN\_known).
- **KHÔNG** suy Precision hay F1 toàn ảnh từ nhãn thưa (FP không đo được vì chưa gán nhãn toàn bộ hố).
- Nhãn `C4_uncertain` không tính vào TP khi tính recall chính thức.

### 3.3 Quy trình thêm nhãn mới

1. Dùng `scripts/label_craters.py` để ghi nhãn.
2. Lưu file vào `data/reference_labels/<image_id>_craters_catalogue.json`.
3. Chạy lại `python scripts/build_s203_split.py` để cập nhật `label_index.json`.
4. Ghi nhận người ghi nhãn, nguồn (manual / Robbins) vào trường `reference_source`.
5. Tiến kiểm chéo overlay (xem `docs/S1-10_HUONG_DAN_NHAN_HO.md`).

---

## 4. Quy tắc ghép hố (matching rules)

Từ `src/matching.py` (S2-04):

```
Thuật toán : one_to_one_hungarian
Ngưỡng tâm : khoảng cách tâm ≤ 0.5 × r_ref  (CENTER_TOLERANCE = 0.5)
Đơn vị     : fraction of reference radius
Tối ưu     : nhiều cặp nhất → tổng khoảng cách (chuẩn hoá) nhỏ nhất
```

**Lưu ý:**
- Mỗi hố tham chiếu và mỗi vòng dự đoán chỉ được dùng **một lần**.
- Recall = TP / n\_labels\_known (chỉ trên nhãn đã có, không toàn ảnh).
- Khi nhãn có `uncertain` trong `crater_id` → loại khỏi recall chính thức.

---

## 5. Đầu ra

| File | Mô tả |
|------|-------|
| `data/s203_split/manifest_split.json` | Split manifest đầy đủ (schema `s203-split-1`) |
| `data/s203_split/label_index.json` | Index nhãn tham chiếu theo ảnh và tập |

### Tái sinh manifest

```bash
python scripts/build_s203_split.py
```

Manifest được sinh tự động từ `data/s106_bundle/crops.json` — không sửa tay.

---

## 6. Việc cần làm tiếp

- [ ] **Tiến** kiểm chéo nhãn `moon_ap16_m106777343r_c01` (4 hố, 1 uncertain).
- [ ] Bổ sung nhãn cho các ảnh Apollo 16 còn lại (ưu tiên ảnh tuning trước).
- [ ] Sau khi có nhãn kiểm chéo → đổi `label_status` từ `sparse_unreviewed` sang `reviewed`.
- [ ] Khi có nhãn holdout → chạy lại script để cập nhật `label_index.json`.
- [ ] Không dùng holdout để chỉnh tham số cho đến khi báo cáo cuối.

---

## 7. Phụ lục — Danh sách ảnh đầy đủ

### 7.1 Tập điều chỉnh (Tuning, 18 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn |
|----------|-------------|-------------|-------------|------|
| moon_ap15_hia_c01 | Ap15 High-Sun | none | — | Chưa có |
| moon_ap15_hia_c02 | Ap15 High-Sun | none | — | Chưa có |
| moon_ap15_hia_c03 | Ap15 High-Sun | none | — | Chưa có |
| moon_vandegraff_hia_c01 | Van de Graaff | none | — | Chưa có |
| moon_vandegraff_hia_c02 | Van de Graaff | none | — | Chưa có |
| moon_lunokhod1_loc_c01 | Lunokhod 1 Low-Sun | none | — | Chưa có |
| moon_lunokhod1_loc_c02 | Lunokhod 1 Low-Sun | none | — | Chưa có |
| moon_marefrig_loc_c01 | Mare Frigoris | none | — | Chưa có |
| moon_marefrig_loc_c02 | Mare Frigoris | none | — | Chưa có |
| moon_marefrig_loc_c03 | Mare Frigoris | none | — | Chưa có |
| moon_ap16_m102057602r_c01 | Ap16 Highlands 2m | measured | 79.94° W | Chưa có |
| moon_ap16_m102064759r_c01 | Ap16 Highlands 2m | measured | 81.08° W | Chưa có |
| **moon_ap16_m106777343r_c01** | Ap16 Highlands 2m | measured | 28.38° W | **4 nhãn (1 uncertain)** |
| moon_ap16_m175179080r_c01 | Ap16 Highlands 2m (Đông) | measured | 41.95° E | Chưa có |
| moon_ap16_m1108182629l_c01 | Ap16 Highlands 2m (Đông) | measured | 65.27° E | Chưa có |
| moon_ap16_m109134835l_c01 | Ap16 Highlands 2m | measured | 7.64° W | Chưa có |
| moon_ap16_m109134835l_c02 | Ap16 Highlands 2m | measured | 7.64° W | Chưa có |
| moon_ap16_m117392541l_c01 | Ap16 Highlands 2m | measured | 83.30° W | Chưa có |

### 7.2 Tập kiểm tra (Holdout, 8 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn |
|----------|-------------|-------------|-------------|------|
| moon_ap16_m113853974r_c01 | Ap16 Highlands (Đông) | measured | 54.72° E | Chưa có |
| moon_ap16_m132732855l_c01 | Ap16 Highlands 2m | measured | 87.70° W | Chưa có |
| moon_ap16_m132732855r_c01 | Ap16 Highlands 2m | measured | 87.78° W | Chưa có |
| moon_ap15_loc_c01 | Ap15 Low-Sun | none | — | Chưa có |
| moon_ap15_loc_c02 | Ap15 Low-Sun | none | — | Chưa có |
| moon_ap15_loc_c03 | Ap15 Low-Sun | none | — | Chưa có |
| moon_lunokhod2_loc_c01 | Lunokhod 2 Low-Sun | none | — | Chưa có |
| moon_lunokhod2_loc_c02 | Lunokhod 2 Low-Sun | none | — | Chưa có |
