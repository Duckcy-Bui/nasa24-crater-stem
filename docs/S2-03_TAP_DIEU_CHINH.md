# S2-03 — Chốt tập điều chỉnh, tập kiểm tra và nhãn tham chiếu

**Phụ trách:** Hoàng Quốc Anh  
**Nghiệm thu:** Nguyễn Mạnh Tiến  
**Ngày:** 25/10/2026  
**Đầu ra:** `data/s203_split/manifest_split.json`, `data/s203_split/label_index.json`

---

## 1. Mục tiêu

Tách 26 crops thành **tập điều chỉnh (tuning)** và **tập kiểm tra (holdout)** để:

- Tuning: điều chỉnh tham số Hough, ngưỡng shading, ngưỡng confidence.
- Holdout: chỉ báo cáo kết quả cuối. **Tuyệt đối không dùng holdout để chỉnh tham số.**

---

## 2. Nguyên tắc phân tập (v3 — nhóm theo vùng mặt đất địa lý)

### 2.1 Nhóm theo vùng mặt đất — triệt tiêu rò rỉ địa lý

> **Đính chính v3 (25/10/2026):** 
> - Toàn bộ 11 ảnh Apollo 16 (`NAC_PHO_E090S0155_*`) đều chụp quanh bãi đáp Apollo 16, tâm cách nhau dưới $1,5\text{ km}$, trong khi mỗi crop phủ bề rộng $1,024\text{ km}$. Khoảng cách tâm $340\text{ m}$ đến $680\text{ m}$ đồng nghĩa với việc các ảnh Apollo 16 chồng lấp mặt đất từ 33% đến 67% với nhau.
> - Do `moon_ap16_m132732855l_c01` (STT 13) đã dùng để chọn cách lọc tại S2-02 ([#19](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/19)), nên theo nguyên tắc *"crop chồng lấp hoặc cùng địa điểm phải cùng nhóm"*, **toàn bộ 11 ảnh Apollo 16 bắt buộc vào tập tuning**.
> - Tập **holdout** gồm 3 vùng địa lý độc lập hoàn toàn, cách tập tuning tối thiểu **$50\text{ km}$** (đảm bảo 0% chồng lấp mặt đất):
>   1. **Apollo 15 Low-Sun** (`NAC_ROI_APOLLO15LOC`): 3 crops, cách Apollo 15 High-Sun ~50 km.
>   2. **Lunokhod 2 Low-Sun** (`NAC_ROI_LUNOKOD2LOA`): 2 crops, cách Lunokhod 1 > 700 km.
>   3. **Mare Frigoris Basalt** (`NAC_ROI_MAREFRIGLOA`): 3 crops, biển bazan phía bắc, cách > 1000 km.

### 2.2 Phân bố (v3)

| Tập | Vùng mặt đất | Crops | Có nhãn | Tỉ lệ | Khoảng cách tới tập kia |
|-----|-------------|-------|---------|--------|--------------------------|
| **Tuning** | 4 | 18 | **18** | ~69,2 % | Đối chứng học tham số |
| **Holdout** | 3 | 8 | **8** | ~30,8 % | **$\ge 50\text{ km}$** (0% rò rỉ) |
| **Tổng** | 7 | 26 | **26 (100%)** | 100 % | Độc lập tuyệt đối |

### 2.3 Holdout (3 vùng mặt đất độc lập)

| Vùng mặt đất (Product ID) | image_id | Đặc trưng | sun_inc | Lý do holdout |
|--------------------------|----------|-----------|---------|---------------|
| `NAC_ROI_APOLLO15LOC_...` | `moon_ap15_loc_c0{1,2,3}` | Ap15 Low-Sun (Rille/Mare) | null | Cách Ap15 HIA ~50 km; góc chiếu xiên kiểm chứng độ nhạy bóng |
| `NAC_ROI_LUNOKOD2LOA_...` | `moon_lunokhod2_loc_c0{1,2}` | Lunokhod 2 Low-Sun | null | Cách các vùng khác > 700 km; địa hình gồ ghề ven biển |
| `NAC_ROI_MAREFRIGLOA_...` | `moon_marefrig_loc_c0{1,2,3}` | Mare Frigoris Basalt | null | Biển bazan phẳng, bóng sắc nét; cách > 1000 km |

### 2.4 Hạn chế đại diện của holdout — cần nêu khi báo cáo kết quả

Toàn bộ 8 crops holdout hiện là **mosaic 20 m/px** và có `sun.quality = none`. Đây là hệ quả của quyết định v3: giữ toàn bộ 11 crops Apollo 16 2 m/px trong tuning để tránh rò rỉ mặt đất, vì chúng chồng lấp nhau và một crop đã được dùng ở S2-02.

- **Thí nghiệm 1 (Hough cơ bản so với thêm S1-11):** không có số đo holdout cho tác động của S1-11. Khi chạy holdout, mọi ứng viên phải được ghi `not_checked` vì thiếu hướng nắng đủ tin cậy; không được diễn giải đây là bằng chứng S1-11 có hoặc không có hiệu quả.
- **Độ phân giải và nhãn:** holdout không có ảnh Apollo 16 2 m/px, trong khi nhãn thủ công và việc khảo sát S2-02/S2-05 tập trung đáng kể ở ảnh 2 m/px. Kết quả holdout chỉ đại diện cho mosaic 20 m/px, không đại diện độc lập cho hiệu năng trên Apollo 16 2 m/px.
- **Cách báo cáo bắt buộc:** tách rõ (a) kết quả tuning Apollo 16 — chỉ là kết quả phát triển/chẩn đoán, và (b) kết quả holdout mosaic — kết quả ngoài mẫu cho 20 m/px. Không gộp hai phần thành một Precision/Recall hay một kết luận chung về S1-11.

**Lựa chọn cần nhóm chốt trước báo cáo cuối:** (1) giữ split v3 và ghi rõ hai giới hạn trên; hoặc (2) bổ sung một cụm Apollo 16 2 m/px mới, không chồng lấp với mọi crop tuning và chưa từng dùng để chọn tham số, làm holdout riêng. Chỉ chuyển ảnh Apollo 16 hiện có sang holdout khi chứng minh được không chồng lấp và không đã dùng cho tuning; với 11 crop hiện tại, điều kiện này không đạt.

---

## 3. Nhãn tham chiếu (reference labels)

### 3.1 Trạng thái hiện tại

✅ **Toàn bộ 26/26 ảnh** đã có file nhãn tham chiếu (25/10/2026) — file coverage 100%; đây không phải coverage đầy đủ của mọi hố trong ảnh. Theo xác nhận cập nhật ngày 26/10/2026, toàn bộ nhãn đã được Nguyễn Mạnh Tiến kiểm chéo.

> ⚠️ **Quan trọng:** Tất cả nhãn hiện tại là `reviewed` và vẫn là nhãn **thưa**. Game và **Recall trên nhãn đã biết** được dùng; Precision/F1 vẫn chỉ được báo cáo nếu có nhãn đầy đủ.

**Tập Tuning (18 ảnh):**

| Ảnh | Số hố | Uncertain | Trạng thái | Ghi chú |
|-----|-------|-----------|-----------|---------|
| `moon_ap16_m102057602r_c01` | 10 | 0 | `sparse_unreviewed` | Ap16 Standard West (chuyển tuning v3 để tránh trùng mặt đất) |
| `moon_ap16_m102064759r_c01` | 11 | 0 | `sparse_unreviewed` | Ap16 Standard West 81.08° |
| `moon_ap16_m106777343r_c01` | 4 | 1 | `sparse_unreviewed` | Ap16 West 28.38° |
| `moon_ap16_m113853974r_c01` | 10 | 0 | `sparse_unreviewed` | Ap16 East 54.72° (cùng tâm m102064759r) |
| `moon_ap16_m132732855l_c01` | 9 | 0 | `sparse_unreviewed` | Ép tuning (đã dùng chọn filter S2-02) |
| `moon_ap16_m132732855r_c01` | 10 | 0 | `sparse_unreviewed` ⚠ | Ap16 Grazing West 87.78° (chuyển tuning v3 để tránh trùng m102064759r) |
| `moon_ap16_m175179080r_c01` | 13 | 0 | `sparse_unreviewed` | Ap16 East 41.95° |
| `moon_ap16_m1108182629l_c01` | 11 | 0 | `sparse_unreviewed` | Ap16 East 65.27° |
| `moon_ap16_m109134835l_c01` | 10 | 0 | `sparse_unreviewed` ⚠ | Ap16 High-Sun 7.64° |
| `moon_ap16_m109134835l_c02` | 11 | 0 | `sparse_unreviewed` ⚠ | Ap16 High-Sun 7.64° |
| `moon_ap16_m117392541l_c01` | 12 | 0 | `sparse_unreviewed` | Ap16 West 83.30° |
| `moon_ap15_hia_c01` | 9 | 0 | `sparse_unreviewed` | Ap15 High-Sun |
| `moon_ap15_hia_c02` | 8 | 0 | `sparse_unreviewed` | Ap15 High-Sun |
| `moon_ap15_hia_c03` | 7 | 0 | `sparse_unreviewed` | Ap15 High-Sun |
| `moon_vandegraff_hia_c01` | 10 | 0 | `sparse_unreviewed` | Van de Graaff Far Side High-Sun |
| `moon_vandegraff_hia_c02` | 11 | 0 | `sparse_unreviewed` | Van de Graaff Far Side High-Sun |
| `moon_lunokhod1_loc_c01` | 10 | 0 | `sparse_unreviewed` | Lunokhod 1 Low-Sun |
| `moon_lunokhod1_loc_c02` | 9 | 0 | `sparse_unreviewed` | Lunokhod 1 Low-Sun |

**Tập Holdout (8 ảnh):**

| Ảnh | Số hố | Uncertain | Trạng thái | Vùng |
|-----|-------|-----------|-----------|------|
| `moon_ap15_loc_c01` | 8 | 0 | `sparse_unreviewed` | Apollo 15 Low-Sun (cách tuning 50,1 km) |
| `moon_ap15_loc_c02` | 9 | 0 | `sparse_unreviewed` | Apollo 15 Low-Sun (cách tuning 54,7 km) |
| `moon_ap15_loc_c03` | 9 | 0 | `sparse_unreviewed` | Apollo 15 Low-Sun (cách tuning 62,8 km) |
| `moon_lunokhod2_loc_c01` | 9 | 0 | `sparse_unreviewed` | Lunokhod 2 Low-Sun (cách tuning 726,9 km) |
| `moon_lunokhod2_loc_c02` | 9 | 0 | `sparse_unreviewed` | Lunokhod 2 Low-Sun (cách tuning 721,4 km) |
| `moon_marefrig_loc_c01` | 6 | 0 | `sparse_unreviewed` | Mare Frigoris Basalt (cách tuning 1095 km) |
| `moon_marefrig_loc_c02` | 7 | 0 | `sparse_unreviewed` | Mare Frigoris Basalt (cách tuning 1098 km) |
| `moon_marefrig_loc_c03` | 9 | 0 | `sparse_unreviewed` | Mare Frigoris Basalt (cách tuning 1106 km) |

> ⚠ **Lưu ý (đính chính 19/10/2026):** Ảnh kiểm hướng nắng của Hưng có vòng chọn thủ công `x249,y180,r120` trong `data/s111_sun_checks.json`. Vòng này **không phải** nhãn đầy đủ để đánh giá.  
> Tiến cần kiểm chéo overlay trước khi dùng nhãn cho báo cáo chính thức.

> 📌 **Ghi chú nhãn (25/10/2026):** Toàn bộ nhãn là `sparse_unreviewed` — ghi nhãn thủ công dựa trên phân tích thị giác. Nhãn Ap15 High-Sun và ảnh High-Sun Ap16 (7.64°) khó nhất — ưu tiên kiểm chéo trước.

### 3.2 Quy trình đổi trạng thái nhãn sau kiểm chéo

Sau khi Tiến kiểm chéo mỗi ảnh, cập nhật trực tiếp trong JSON label file:

```json
"reference_source": "reviewed by Nguyen Manh Tien; sparse manual labels"
```

Sau đó chạy lại `build_s203_split.py` để cập nhật `label_index.json`.  
Nhãn `reviewed` mới dùng được để tính Precision/Recall trong game.

### 3.3 Giải thích về nhãn thưa

Nhãn hiện tại là **sparse** (thưa):

- **Recall** đo trên nhãn đã biết: TP / (TP + FN\_known).
- **KHÔNG** suy Precision hay F1 toàn ảnh từ nhãn thưa (FP không đo được vì chưa gán nhãn toàn bộ hố).
- Nhãn `C4_uncertain` không tính vào TP khi tính recall chính thức.

### 3.4 Quy trình thêm nhãn mới

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

### 6.1 Kiểm chéo nhãn — hoàn tất ngày 26/10/2026

- [x] **Tiến** kiểm chéo toàn bộ **26 overlay PNG** trong `data/reference_labels/`, gồm **8 holdout** và các ảnh dùng để khảo sát.
- [x] Cập nhật `reference_source` thành `manual_label_s110; sparse manual labels, reviewed by Nguyen Manh Tien`.
- [x] Chạy lại `build_s203_split.py` để tái sinh manifest và label index.

### 6.2 Quy trình sau kiểm chéo
- [ ] Không dùng holdout để chỉnh tham số cho đến khi báo cáo cuối.
- [ ] Commit lại manifest + label_index sau mỗi lần thêm nhãn đã kiểm chéo.
- [ ] Chạy `python scripts/build_s203_split.py` sau mỗi lần thêm/sửa nhãn.

---

## 7. Phụ lục — Danh sách ảnh đầy đủ

### 7.1 Tập điều chỉnh (Tuning, 18 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn | Số hố |
|----------|-------------|-------------|-------------|------|-------|
| **moon_ap16_m102057602r_c01** | Ap16 Highlands 2m | measured | 79.94° W | ✅ sparse_unreviewed | **10** |
| **moon_ap16_m102064759r_c01** | Ap16 Highlands 2m | measured | 81.08° W | ✅ sparse_unreviewed | **11** |
| **moon_ap16_m106777343r_c01** | Ap16 Highlands 2m | measured | 28.38° W | ✅ sparse_unreviewed | **4 (1 unc.)** |
| **moon_ap16_m113853974r_c01** | Ap16 Highlands 2m (Đông) | measured | 54.72° E | ✅ sparse_unreviewed | **10** |
| **moon_ap16_m132732855l_c01** | Ap16 Highlands 2m | measured | 87.70° W | ✅ sparse_unreviewed | **9** |
| **moon_ap16_m132732855r_c01** | Ap16 Highlands 2m | measured | 87.78° W | ✅ sparse_unreviewed ⚠ | **10** |
| **moon_ap16_m175179080r_c01** | Ap16 Highlands 2m (Đông) | measured | 41.95° E | ✅ sparse_unreviewed | **13** |
| **moon_ap16_m1108182629l_c01** | Ap16 Highlands 2m (Đông) | measured | 65.27° E | ✅ sparse_unreviewed | **11** |
| **moon_ap16_m109134835l_c01** | Ap16 Highlands 2m | measured | 7.64° W | ✅ sparse_unreviewed ⚠ | **10** |
| **moon_ap16_m109134835l_c02** | Ap16 Highlands 2m | measured | 7.64° W | ✅ sparse_unreviewed ⚠ | **11** |
| **moon_ap16_m117392541l_c01** | Ap16 Highlands 2m | measured | 83.30° W | ✅ sparse_unreviewed | **12** |
| **moon_ap15_hia_c01** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **9** |
| **moon_ap15_hia_c02** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **8** |
| **moon_ap15_hia_c03** | Ap15 High-Sun | none | — | ✅ sparse_unreviewed | **7** |
| **moon_vandegraff_hia_c01** | Van de Graaff | none | — | ✅ sparse_unreviewed | **10** |
| **moon_vandegraff_hia_c02** | Van de Graaff | none | — | ✅ sparse_unreviewed | **11** |
| **moon_lunokhod1_loc_c01** | Lunokhod 1 Low-Sun | none | — | ✅ sparse_unreviewed | **10** |
| **moon_lunokhod1_loc_c02** | Lunokhod 1 Low-Sun | none | — | ✅ sparse_unreviewed | **9** |

> ⚠ = Ảnh High-Sun hoặc Grazing cực hạn, nhãn khó — ưu tiên kiểm chéo.

### 7.2 Tập kiểm tra (Holdout, 8 crops)

| image_id | region_group | sun_quality | sun_inc_deg | Nhãn | Số hố | Vùng mặt đất |
|----------|-------------|-------------|-------------|------|-------|--------------|
| **moon_ap15_loc_c01** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **8** | Apollo 15 LOC (cách tuning 50,1 km) |
| **moon_ap15_loc_c02** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **9** | Apollo 15 LOC (cách tuning 54,7 km) |
| **moon_ap15_loc_c03** | Ap15 Low-Sun | none | — | ✅ sparse_unreviewed | **9** | Apollo 15 LOC (cách tuning 62,8 km) |
| **moon_lunokhod2_loc_c01** | Lunokhod 2 Low-Sun | none | — | ✅ sparse_unreviewed | **9** | Lunokhod 2 (cách tuning 726,9 km) |
| **moon_lunokhod2_loc_c02** | Lunokhod 2 Low-Sun | none | — | ✅ sparse_unreviewed | **9** | Lunokhod 2 (cách tuning 721,4 km) |
| **moon_marefrig_loc_c01** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **6** | Mare Frigoris (cách tuning 1095 km) |
| **moon_marefrig_loc_c02** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **7** | Mare Frigoris (cách tuning 1098 km) |
| **moon_marefrig_loc_c03** | Mare Frigoris | none | — | ✅ sparse_unreviewed | **9** | Mare Frigoris (cách tuning 1106 km) |

---

## 8. Nhật ký thay đổi

| Ngày | Phiên bản | Thay đổi |
|------|----------|---------|
| 23/10/2026 | v1 | Chia lần đầu: group_by_product_id, 18 tuning / 8 holdout |
| 25/10/2026 | v2 | Đổi sang group_by_ground_patch theo tọa độ offset; m113853974r_c01 → tuning; m132732855l_c01 → tuning (S2-02); m102057602r_c01 → holdout. Kết quả: 19 tuning / 7 holdout |
| 25/10/2026 | v3 | Chuyển toàn bộ 11 ảnh Apollo 16 sang tuning (do các ảnh cách nhau < 1.5 km và chồng lấp mặt đất). Holdout gồm 3 vùng độc lập cách tuning $\ge 50\text{ km}$ (Apollo 15 LOC, Lunokhod 2, Mare Frigoris). Kết quả: 18 tuning / 8 holdout, 0% rò rỉ mặt đất. |
