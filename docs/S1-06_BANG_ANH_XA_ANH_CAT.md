# Bảng ánh xạ ảnh cắt và hai vùng so sánh — S1-06

Đầu ra chính thức của đầu việc **S1-06** (Phụ trách: Hoàng Quốc Anh; Phối hợp/Nghiệm thu: Đinh Quang Hưng).
Tổng số ảnh cắt: **26** ảnh (kích thước chuẩn 512×512, tỷ lệ pixel [0, 1] `float32`).

## 1. Hai vùng so sánh chính thức

### Cặp so sánh 1: Chiếu sáng High-Sun vs Low-Sun (Khu vực Apollo 15)
- **Thang đo dùng chung**: `scale_m_per_px = 20.0 m/px`.
- **Khoảng bán kính vật lý**: Đường kính $D = [200\text{ m}, 4000\text{ m}] \implies r = [5\text{ px}, 100\text{ px}]$.
- **Vùng 1A (High-Sun)**: `moon_ap15_hia_c01`, `moon_ap15_hia_c02`, `moon_ap15_hia_c03` (STT 1, góc tới 28°–53°).
- **Vùng 1B (Low-Sun)**: `moon_ap15_loc_c01`, `moon_ap15_loc_c02`, `moon_ap15_loc_c03` (STT 2, góc tới cao đổ bóng dài).
- **Mục đích khoa học**: Đánh giá sự suy giảm độ chính xác của thuật toán Hough và bộ lọc sáng-tối khi góc nắng thay đổi từ chiếu đỉnh đầu sang xiên tạo bóng.

### Cặp so sánh 2: Địa chất Biển Basalt (Mare) vs Cao nguyên mặt xa (Highlands)
- **Thang đo dùng chung**: `scale_m_per_px = 20.0 m/px`.
- **Khoảng bán kính vật lý**: Đường kính $D = [200\text{ m}, 4000\text{ m}] \implies r = [5\text{ px}, 100\text{ px}]$.
- **Vùng 2A (Cao nguyên mặt xa)**: `moon_vandegraff_hia_c01`, `moon_vandegraff_hia_c02` (STT 3 - Miệng hố Van de Graaff).
- **Vùng 2B (Biển phẳng)**: `moon_marefrig_loc_c01`, `moon_marefrig_loc_c02`, `moon_marefrig_loc_c03` (STT 6 - Mare Frigoris).
- **Mục đích khoa học**: Phục vụ phân tích thống kê mật độ hố ở tuần 2 (so sánh độ tuổi địa chất giữa bề mặt biển trẻ và cao nguyên cổ).

### Nhóm mở rộng: Chuỗi góc tới Apollo 16 ở độ phân giải siêu cao (2.0 m/px)
- 11 ảnh cắt từ STT 8 đến 18 với thang đo $2.0\text{ m/px}$, đường kính $D = [20\text{ m}, 500\text{ m}] \implies r = [5\text{ px}, 125\text{ px}]$.
- Khảo sát góc tới từ cực thấp ($7.64^\circ$ ở STT 17) đến cực cao ($87.78^\circ$ ở STT 14), có cả nắng từ Tây lẫn Đông.

## 2. Bảng chi tiết 26 ảnh cắt

| STT | Image ID | Mã nguồn (STT) | Vùng phân loại | Tọa độ cắt (x0, y0) | Scale (m/px) | Tâm Lat/Lon | Góc tới | Dải D (m) | Dải r (px) | Hợp lệ |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `moon_ap15_hia_c01` | NAC_ROI_APOLLO15HIA_E259N0036_20M (1) | Apollo 15 High-Sun (Vùng so sánh 1A) | (630, 1152) | 20.0 | 25.627°N, 3.718°E | 40.5° | 200–4000 | 5–100 | 100.0% |
| 2 | `moon_ap15_hia_c02` | NAC_ROI_APOLLO15HIA_E259N0036_20M (1) | Apollo 15 High-Sun (Vùng so sánh 1A) | (630, 896) | 20.0 | 25.796°N, 3.718°E | 40.5° | 200–4000 | 5–100 | 100.0% |
| 3 | `moon_ap15_hia_c03` | NAC_ROI_APOLLO15HIA_E259N0036_20M (1) | Apollo 15 High-Sun (Vùng so sánh 1A) | (735, 64) | 20.0 | 26.345°N, 3.795°E | 40.5° | 200–4000 | 5–100 | 100.0% |
| 4 | `moon_ap15_loc_c01` | NAC_ROI_APOLLO15LOC_E252N0018_20M (2) | Apollo 15 Low-Sun (Vùng so sánh 1B) | (1296, 2380) | 20.0 | 24.655°N, 2.242°E | 75.0° | 200–4000 | 5–100 | 100.0% |
| 5 | `moon_ap15_loc_c02` | NAC_ROI_APOLLO15LOC_E252N0018_20M (2) | Apollo 15 Low-Sun (Vùng so sánh 1B) | (1296, 2737) | 20.0 | 24.419°N, 2.242°E | 75.0° | 200–4000 | 5–100 | 100.0% |
| 6 | `moon_ap15_loc_c03` | NAC_ROI_APOLLO15LOC_E252N0018_20M (2) | Apollo 15 Low-Sun (Vùng so sánh 1B) | (432, 2142) | 20.0 | 24.812°N, 1.612°E | 75.0° | 200–4000 | 5–100 | 100.0% |
| 7 | `moon_vandegraff_hia_c01` | NAC_ROI_VANDGRAFHIA_E269S1722_20M (3) | Van de Graaff Highlands (Vùng so sánh 2A) | (588, 512) | 20.0 | -26.782°N, 172.078°E | 36.0° | 200–4000 | 5–100 | 100.0% |
| 8 | `moon_vandegraff_hia_c02` | NAC_ROI_VANDGRAFHIA_E269S1722_20M (3) | Van de Graaff Highlands (Vùng so sánh 2A) | (600, 900) | 20.0 | -27.038°N, 172.087°E | 36.0° | 200–4000 | 5–100 | 100.0% |
| 9 | `moon_lunokhod1_loc_c01` | NAC_ROI_LUNOKOD1LOA_E381N3246_20M (4) | Lunokhod 1 Low-Sun | (127, 1560) | 20.0 | 37.735°N, -35.805°E | 70.0° | 200–4000 | 5–100 | 100.0% |
| 10 | `moon_lunokhod1_loc_c02` | NAC_ROI_LUNOKOD1LOA_E381N3246_20M (4) | Lunokhod 1 Low-Sun | (127, 1950) | 20.0 | 37.478°N, -35.805°E | 70.0° | 200–4000 | 5–100 | 100.0% |
| 11 | `moon_lunokhod2_loc_c01` | NAC_ROI_LUNOKOD2LOA_E259N0306_20M (5) | Lunokhod 2 Low-Sun | (352, 960) | 20.0 | 25.551°N, 30.485°E | 69.5° | 200–4000 | 5–100 | 100.0% |
| 12 | `moon_lunokhod2_loc_c02` | NAC_ROI_LUNOKOD2LOA_E259N0306_20M (5) | Lunokhod 2 Low-Sun | (88, 896) | 20.0 | 25.593°N, 30.289°E | 69.5° | 200–4000 | 5–100 | 100.0% |
| 13 | `moon_marefrig_loc_c01` | NAC_ROI_MAREFRIGLOA_E598N0261_20M (6) | Mare Frigoris Basalt (Vùng so sánh 2B) | (151, 2318) | 20.0 | 59.236°N, 25.316°E | 72.5° | 200–4000 | 5–100 | 100.0% |
| 14 | `moon_marefrig_loc_c02` | NAC_ROI_MAREFRIGLOA_E598N0261_20M (6) | Mare Frigoris Basalt (Vùng so sánh 2B) | (453, 2318) | 20.0 | 59.236°N, 25.714°E | 72.5° | 200–4000 | 5–100 | 100.0% |
| 15 | `moon_marefrig_loc_c03` | NAC_ROI_MAREFRIGLOA_E598N0261_20M (6) | Mare Frigoris Basalt (Vùng so sánh 2B) | (755, 2100) | 20.0 | 59.380°N, 26.113°E | 72.5° | 200–4000 | 5–100 | 100.0% |
| 16 | `moon_ap16_m102057602r_c01` | M102057602R (8) | Apollo 16 Highlands 2m | (340, 2750) | 2.0 | -8.818°N, 15.447°E | 79.94° | 20–500 | 5–125 | 100.0% |
| 17 | `moon_ap16_m102064759r_c01` | M102064759R (9) | Apollo 16 Highlands 2m | (1190, 2750) | 2.0 | -8.818°N, 15.504°E | 81.08° | 20–500 | 5–125 | 100.0% |
| 18 | `moon_ap16_m106777343r_c01` | M106777343R (10) | Apollo 16 Highlands 2m | (170, 6600) | 2.0 | -9.072°N, 15.436°E | 28.38° | 20–500 | 5–125 | 100.0% |
| 19 | `moon_ap16_m113853974r_c01` | M113853974R (11) | Apollo 16 Highlands 2m (Đông) | (1190, 2750) | 2.0 | -8.818°N, 15.504°E | 54.72° | 20–500 | 5–125 | 100.0% |
| 20 | `moon_ap16_m132732855l_c01` | M132732855L (13) | Apollo 16 Highlands 2m | (680, 2750) | 2.0 | -8.818°N, 15.470°E | 87.7° | 20–500 | 5–125 | 100.0% |
| 21 | `moon_ap16_m132732855r_c01` | M132732855R (14) | Apollo 16 Highlands 2m | (1360, 2750) | 2.0 | -8.818°N, 15.515°E | 87.78° | 20–500 | 5–125 | 100.0% |
| 22 | `moon_ap16_m175179080r_c01` | M175179080R (15) | Apollo 16 Highlands 2m (Đông) | (700, 3000) | 2.0 | -8.834°N, 15.471°E | 41.95° | 20–500 | 5–125 | 100.0% |
| 23 | `moon_ap16_m1108182629l_c01` | M1108182629L (16) | Apollo 16 Highlands 2m (Đông) | (1020, 2750) | 2.0 | -8.818°N, 15.492°E | 65.27° | 20–500 | 5–125 | 100.0% |
| 24 | `moon_ap16_m109134835l_c01` | M109134835L (17) | Apollo 16 Highlands 2m | (1020, 2750) | 2.0 | -8.818°N, 15.492°E | 7.64° | 20–500 | 5–125 | 100.0% |
| 25 | `moon_ap16_m109134835l_c02` | M109134835L (17) | Apollo 16 Highlands 2m | (1020, 4200) | 2.0 | -8.914°N, 15.492°E | 7.64° | 20–500 | 5–125 | 100.0% |
| 26 | `moon_ap16_m117392541l_c01` | M117392541L (18) | Apollo 16 Highlands 2m | (1190, 2750) | 2.0 | -8.818°N, 15.504°E | 83.3° | 20–500 | 5–125 | 100.0% |
