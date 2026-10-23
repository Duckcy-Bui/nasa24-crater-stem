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
| **Tuning** | 11 | 18 | **18** | ~69 % |
| **Holdout** | 5 | 8 | **8** | ~31 % |
| **Tổng** | 16 | 26 | **26 (100%)** | 100 % |

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

✅ **Toàn bộ 26/26 ảnh** đã có nhãn tham chiếu (23/10/2026) — coverage 100%.

**Tập Tuning (18 ảnh):**

| Ảnh | Tập | Số hố | Uncertain | Trạng thái |
|-----|-----|-------|-----------|-----------|
| `moon_ap16_m106777343r_c01` | tuning | 4 | 1 | `sparse_unreviewed` |
| `moon_ap16_m102057602r_c01` | tuning | 10 | 0 | `sparse_unreviewed` |
| `moon_ap16_m102064759r_c01` | tuning | 11 | 0 | `sparse_unreviewed` |
| `moon_ap16_m175179080r_c01` | tuning | 13 | 0 | `sparse_unreviewed` |
| `moon_ap16_m1108182629l_c01` | tuning | 11 | 0 | `sparse_unreviewed` |
| `moon_ap16_m109134835l_c01` | tuning | 10 | 0 | `sparse_unreviewed` ⚠ |
| `moon_ap16_m109134835l_c02` | tuning | 11 | 0 | `sparse_unreviewed` ⚠ |
| `moon_ap16_m117392541l_c01` | tuning | 12 | 0 | `sparse_unreviewed` |
| `moon_ap15_hia_c01` | tuning | 9 | 0 | `sparse_unreviewed` |
| `moon_ap15_hia_c02` | tuning | 8 | 0 | `sparse_unreviewed` |
| `moon_ap15_hia_c03` | tuning | 7 | 0 | `sparse_unreviewed` |
| `moon_vandegraff_hia_c01` | tuning | 10 | 0 | `sparse_unreviewed` |
| `moon_vandegraff_hia_c02` | tuning | 11 | 0 | `sparse_unreviewed` |
| `moon_lunokhod1_loc_c01` | tuning | 10 | 0 | `sparse_unreviewed` |
| `moon_lunokhod1_loc_c02` | tuning | 9 | 0 | `sparse_unreviewed` |
| `moon_marefrig_loc_c01` | tuning | 6 | 0 | `sparse_unreviewed` |
| `moon_marefrig_loc_c02` | tuning | 7 | 0 | `sparse_unreviewed` |
| `moon_marefrig_loc_c03` | tuning | 9 | 0 | `sparse_unreviewed` |

**Tập Holdout (8 ảnh):**

| Ảnh | Tập | Số hố | Uncertain | Trạng thái |
|-----|-----|-------|-----------|-----------|
| `moon_ap16_m113853974r_c01` | holdout | 10 | 0 | `sparse_unreviewed` |
| `moon_ap16_m132732855l_c01` | holdout | 9 | 0 | `sparse_unreviewed` |
| `moon_ap16_m132732855r_c01` | holdout | 10 | 0 | `sparse_unreviewed` |
| `moon_ap15_loc_c01` | holdout | 8 | 0 | `sparse_unreviewed` |
| `moon_ap15_loc_c02` | holdout | 9 | 0 | `sparse_unreviewed` |
| `moon_ap15_loc_c03` | holdout | 9 | 0 | `sparse_unreviewed` |
| `moon_lunokhod2_loc_c01` | holdout | 9 | 0 | `sparse_unreviewed` |
| `moon_lunokhod2_loc_c02` | holdout | 9 | 0 | `sparse_unreviewed` |

> ⚠ **Lưu ý (đính chính 19/10/2026):** Ảnh kiểm hướng nắng của Hưng có vòng chọn thủ công `x249,y180,r120` trong `data/s111_sun_checks.json`. Vòng này **không phải** nhãn đầy đủ để đánh giá.  
> Tiến cần kiểm chéo overlay trước khi dùng nhãn cho báo cáo chính thức.

> 📌 **Ghi chú nhãn (23/10/2026):** Toàn bộ nhãn là `sparse_unreviewed` — ghi nhãn thủ công dựa trên phân tích thị giác. Nhãn Ap15 High-Sun và ảnh High-Sun Ap16 (7.64°) khó nhất — ưu tiên kiểm chéo trước.

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

### 6.1 Kiểm chéo nhãn (ưu tiên cao)
- [ ] **Tiến** kiểm chéo toàn bộ **26 overlay PNG** trong `data/reference_labels/`.
- [ ] Ưu tiên 1 — Ap16 High-Sun (7.64°): `moon_ap16_m109134835l_c01`, `moon_ap16_m109134835l_c02`.
- [ ] Ưu tiên 2 — Ap15 High-Sun: `moon_ap15_hia_c01/02/03` (scale 20m/px, ejecta ray nhiều).
- [ ] Ưu tiên 3 — Holdout Grazing: `moon_ap16_m132732855l/r_c01` (87°, bóng dài che phủ nhiều).
- [ ] Sau khi kiểm chéo xong → đổi `label_status` từ `sparse_unreviewed` sang `reviewed`.

### 6.2 Quy trình sau kiểm chéo
- [ ] Không dùng holdout để chỉnh tham số cho đến khi báo cáo cuối.
- [ ] Commit lại manifest + label_index sau mỗi lần thêm nhãn đã kiểm chéo.
- [ ] Chạy `python scripts/build_s203_split.py` sau mỗi lần thêm/sửa nhãn.

---

## 7. Phụ lục — Danh sách ảnh đầy đủ

### 7.1 Tập điều chỉnh (Tuning, 18 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn | Số hố |
|----------|-------------|-------------|-------------|------|-------|
| **moon_ap15_hia_c01** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_ap15_hia_c02** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **8** |
| **moon_ap15_hia_c03** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **7** |
| **moon_vandegraff_hia_c01** | Van de Graaff | none | — | ✅ sparse_unreviewed | **10** |
| **moon_vandegraff_hia_c02** | Van de Graaff | none | — | ✅ sparse_unreviewed | **11** |
| **moon_lunokhod1_loc_c01** | Lunokhod 1 Low-Sun | none | — | ✅ sparse_unreviewed | **10** |
| **moon_lunokhod1_loc_c02** | Lunokhod 1 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_marefrig_loc_c01** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **6** |
| **moon_marefrig_loc_c02** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **7** |
| **moon_marefrig_loc_c03** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **9** |
| **moon_ap16_m102057602r_c01** | Ap16 Highlands 2m | measured | 79.94° W | ✅ sparse_unreviewed | **10** |
| **moon_ap16_m102064759r_c01** | Ap16 Highlands 2m | measured | 81.08° W | ✅ sparse_unreviewed | **11** |
| **moon_ap16_m106777343r_c01** | Ap16 Highlands 2m | measured | 28.38° W | ✅ sparse_unreviewed | **4 (1 unc.)** |
| **moon_ap16_m175179080r_c01** | Ap16 Highlands 2m (Đông) | measured | 41.95° E | ✅ sparse_unreviewed | **13** |
| **moon_ap16_m1108182629l_c01** | Ap16 Highlands 2m (Đông) | measured | 65.27° E | ✅ sparse_unreviewed | **11** |
| **moon_ap16_m109134835l_c01** | Ap16 Highlands 2m | measured | 7.64° W | ✅ sparse_unreviewed ⚠ | **10** |
| **moon_ap16_m109134835l_c02** | Ap16 Highlands 2m | measured | 7.64° W | ✅ sparse_unreviewed ⚠ | **11** |
| **moon_ap16_m117392541l_c01** | Ap16 Highlands 2m | measured | 83.30° W | ✅ sparse_unreviewed | **12** |

> ⚠ = Ảnh High-Sun (sun_inc 7.64°), nhãn khó — ưu tiên kiểm chéo.

### 7.2 Tập kiểm tra (Holdout, 8 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn | Số hố |
|----------|-------------|-------------|-------------|------|-------|
| **moon_ap16_m113853974r_c01** | Ap16 Highlands (Đông) | measured | 54.72° E | ✅ sparse_unreviewed | **10** |
| **moon_ap16_m132732855l_c01** | Ap16 Highlands 2m | measured | 87.70° W | ✅ sparse_unreviewed ⚠ | **9** |
| **moon_ap16_m132732855r_c01** | Ap16 Highlands 2m | measured | 87.78° W | ✅ sparse_unreviewed ⚠ | **10** |
| **moon_ap15_loc_c01** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **8** |
| **moon_ap15_loc_c02** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_ap15_loc_c03** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_lunokhod2_loc_c01** | Lunokhod 2 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_lunokhod2_loc_c02** | Lunokhod 2 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |

> ⚠ = Ảnh Grazing (87°), bóng che phủ nhiều — ưu tiên kiểm chéo.
