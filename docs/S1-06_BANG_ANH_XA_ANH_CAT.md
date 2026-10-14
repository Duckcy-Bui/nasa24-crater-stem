# Bảng ánh xạ ảnh cắt S1-06

26 ảnh browse LROC thật, 512×512 float32 [0,1], mặt nạ bool đi kèm. Không sinh nhãn hố giả.

Đọc [hướng dẫn bàn giao](S1-06_HUONG_DAN_DU_LIEU.md) để giải nén, tái tạo và hiểu giới hạn.

- Apollo 16: `moon_ap16_m102064759r_c01` (81,08°) và `moon_ap16_m109134835l_c01` (7,64°) cùng cửa sổ (1190,2750), cùng CRS/affine và 2 m/px. Đây là cặp cùng vùng để minh họa điều kiện chiếu sáng.
- Apollo 15 High-Sun/Low-Sun cắt các tọa độ khác nhau, không phải cặp cùng mặt đất. Không quy mọi khác biệt phát hiện hố cho góc nắng.
- Van de Graaff/Mare Frigoris cùng 20 m/px và dải D 200–4000 m: so sánh mật độ minh họa, chưa chứng minh tuổi địa chất; điều kiện chiếu sáng khác nhau.
- Mọi ảnh có reference_status=unavailable: chưa dùng để đánh giá P/R hoặc chấm game theo catalogue.

| Image ID | STT | Crop (x0,y0) | m/px | Tâm lat/lon | Góc tới | Hướng nắng | Dải r (px) | Hợp lệ |
|---|---:|---|---:|---|---|---|---|---:|
| `moon_ap15_hia_c01` | 1 | (630,1152) | 20.0 | 25.627775, 3.717558 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap15_hia_c02` | 1 | (630,896) | 20.0 | 25.796622, 3.717558 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap15_hia_c03` | 1 | (735,64) | 20.0 | 26.345374, 3.794610 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap15_loc_c01` | 2 | (1296,2380) | 20.0 | 24.654927, 2.241733 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap15_loc_c02` | 2 | (1296,2737) | 20.0 | 24.419465, 2.241733 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap15_loc_c03` | 2 | (432,2142) | 20.0 | 24.811902, 1.611935 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_vandegraff_hia_c01` | 3 | (588,512) | 20.0 | -26.782001, 172.077424 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_vandegraff_hia_c02` | 3 | (600,900) | 20.0 | -27.037909, 172.086307 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_lunokhod1_loc_c01` | 4 | (127,1560) | 20.0 | 37.735276, -35.805390 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_lunokhod1_loc_c02` | 4 | (127,1950) | 20.0 | 37.478049, -35.805390 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_lunokhod2_loc_c01` | 5 | (352,960) | 20.0 | 25.551266, 30.485025 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_lunokhod2_loc_c02` | 5 | (88,896) | 20.0 | 25.593478, 30.288722 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_marefrig_loc_c01` | 6 | (151,2318) | 20.0 | 59.236198, 25.315145 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_marefrig_loc_c02` | 6 | (453,2318) | 20.0 | 59.236198, 25.713517 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_marefrig_loc_c03` | 6 | (755,2100) | 20.0 | 59.379982, 26.111890 | không có số đo cửa sổ | none | 5–100 | 1.000000 |
| `moon_ap16_m102057602r_c01` | 8 | (340,2750) | 2.0 | -8.817825, 15.446919 | 79.94 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m102064759r_c01` | 9 | (1190,2750) | 2.0 | -8.817825, 15.503681 | 81.08 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m106777343r_c01` | 10 | (170,6600) | 2.0 | -9.071755, 15.435567 | 28.38 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m113853974r_c01` | 11 | (1190,2750) | 2.0 | -8.817825, 15.503681 | 54.72 | none | 5–125 | 1.000000 |
| `moon_ap16_m132732855l_c01` | 13 | (680,2750) | 2.0 | -8.817825, 15.469624 | 87.7 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m132732855r_c01` | 14 | (1360,2750) | 2.0 | -8.817825, 15.515033 | 87.78 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m175179080r_c01` | 15 | (700,3000) | 2.0 | -8.834314, 15.470959 | 41.95 | none | 5–125 | 1.000000 |
| `moon_ap16_m1108182629l_c01` | 16 | (1020,2750) | 2.0 | -8.817825, 15.492328 | 65.27 | none | 5–125 | 1.000000 |
| `moon_ap16_m109134835l_c01` | 17 | (1190,2750) | 2.0 | -8.817825, 15.503681 | 7.64 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m109134835l_c02` | 17 | (1020,4200) | 2.0 | -8.913461, 15.492328 | 7.64 | side_only | 5–125 | 1.000000 |
| `moon_ap16_m117392541l_c01` | 18 | (1190,2750) | 2.0 | -8.817825, 15.503681 | 83.3 | side_only | 5–125 | 1.000000 |
