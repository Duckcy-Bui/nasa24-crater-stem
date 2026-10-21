# Hồ sơ nguồn dữ liệu — S1-16

> **Bản nháp S1-16** (15/10/2026), chưa qua nhóm duyệt. Phụ trách theo bảng giao việc: Hoàng Quốc Anh; phối hợp: Bùi Hải Đức. Mọi số liệu dưới đây được đọc lại từ `data/s106_bundle/` (`sources.json`, `crops.json`, `manifest.json`, metadata trong ZIP) và từ `src/contracts.py`, không lấy từ trí nhớ. Chỗ chưa có căn cứ trong repo được ghi ở mục 8.

Tài liệu này gom và đối chiếu các tài liệu đã có ([S1-06_HUONG_DAN_DU_LIEU.md](S1-06_HUONG_DAN_DU_LIEU.md), [S1-06_BANG_ANH_XA_ANH_CAT.md](S1-06_BANG_ANH_XA_ANH_CAT.md), [DINH_DANG_DU_LIEU.md](DINH_DANG_DU_LIEU.md), [S1-10_HUONG_DAN_NHAN_HO.md](S1-10_HUONG_DAN_NHAN_HO.md)) thành một hồ sơ: **nguồn ở đâu, cắt thế nào, quy đổi tọa độ ra sao, dùng được đến đâu**.

## 1. Tổng quan

| Mục | Giá trị |
|---|---|
| Bộ dữ liệu | `s106_lroc_browse_v2` (schema bundle `s106-bundle-1`) |
| Số ảnh cắt | 26 ảnh 512×512, `float32` trong [0, 1], kèm `.png`, `.json`, `_valid_mask.npy` (bool) |
| Số ảnh nguồn | 16 TIFF browse LROC (STT 1–6 và 8–11, 13–18 theo S1-02), tổng 503.640.706 byte (≈ 480,3 MiB) |
| Thiên thể | Mặt Trăng (`body = moon`) |
| Tỷ lệ | 15 ảnh 20 m/px (mosaic NAC, STT 1–6) và 11 ảnh 2 m/px (NAC Apollo 16, STT 8–18); mọi ảnh `downsample_k = 1` |
| Mức sản phẩm | `browse` (8 bit, để xem), `radiometrically_calibrated = false` |
| Credit | NASA/GSFC/Arizona State University (LROC) |
| Nhãn hố tham chiếu | `reference_status = "unavailable"` cho cả 26 ảnh; chỉ có 4 nhãn thủ công thưa, chưa kiểm chéo (mục 7) |
| Gói ngoại tuyến | `data/s106_bundle/s106_lroc_browse_v2.zip`, 12.861.130 byte, SHA-256 `5b869f11…ebd95` |
| Tải nguồn | ngày 14/10/2026, từ máy chủ LROC/PDS chính thức |

## 2. Nguồn ảnh

Mỗi ảnh nguồn là file `.PYR.TIF` trong thư mục `EXTRAS/BROWSE` của PDS LROC. URL đầy đủ, URL trang sản phẩm, số byte và SHA-256 đầy đủ của **từng file** nằm trong `data/s106_bundle/sources.json`; script tải từ chối file sai kích thước hoặc sai hash.

- Mẫu URL tải: `https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/EXTRAS/BROWSE/NAC_ROI/<NHÓM>/<product>.PYR.TIF` (mosaic) và `.../BROWSE/NAC_PHO/E090S0155/<product>.PYR.TIF` (Apollo 16).
- Mẫu trang sản phẩm: `https://data.lroc.im-ldi.com/lroc/view_rdr_product/<product>`.

| STT | Vùng | Product | Byte | SHA-256 (12 ký tự đầu) | m/px | Ảnh nguồn (px) | Số ảnh cắt |
|---:|---|---|---:|---|---:|---|---:|
| 1 | Apollo 15, high-Sun | `NAC_ROI_APOLLO15HIA_E259N0036_20M` | 5.049.616 | `6b53520f9444…` | 20 | 1568×1910 | 3 |
| 2 | Apollo 15, low-Sun | `NAC_ROI_APOLLO15LOC_E252N0018_20M` | 9.900.554 | `941817751a88…` | 20 | 1952×3502 | 3 |
| 3 | Van de Graaff, high-Sun | `NAC_ROI_VANDGRAFHIA_E269S1722_20M` | 5.573.968 | `15c938651e19…` | 20 | 1985×1988 | 2 |
| 4 | Lunokhod 1, low-Sun | `NAC_ROI_LUNOKOD1LOA_E381N3246_20M` | 6.492.266 | `2662d281b852…` | 20 | 1790×2476 | 2 |
| 5 | Lunokhod 2, low-Sun | `NAC_ROI_LUNOKOD2LOA_E259N0306_20M` | 3.279.928 | `aad46ee897e9…` | 20 | 1393×1477 | 2 |
| 6 | Mare Frigoris, low-Sun | `NAC_ROI_MAREFRIGLOA_E598N0261_20M` | 9.900.554 | `a93f55c0c3b6…` | 20 | 2025×3572 | 3 |
| 8 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M102057602R` | 46.344.382 | `6903707b5395…` | 2 | 2213×14282 | 1 |
| 9 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M102064759R` | 46.344.382 | `b8dc3ef49cea…` | 2 | 2213×14282 | 1 |
| 10 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M106777343R` | 46.344.382 | `6e8c16094800…` | 2 | 2213×14282 | 1 |
| 11 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M113853974R` | 46.344.382 | `e201bd02ddbd…` | 2 | 2213×14282 | 1 |
| 13 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M132732855L` | 46.344.382 | `b01ffee70cdd…` | 2 | 2213×14282 | 1 |
| 14 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M132732855R` | 46.344.382 | `cfed88e7ba0c…` | 2 | 2213×14282 | 1 |
| 15 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M175179080R` | 46.344.382 | `f3aa7cdbc337…` | 2 | 2213×14282 | 1 |
| 16 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M1108182629L` | 46.344.382 | `9ad46dbb9798…` | 2 | 2213×14282 | 1 |
| 17 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M109134835L` | 46.344.382 | `c7fc798e9704…` | 2 | 2213×14282 | 2 |
| 18 | Apollo 16 (chuỗi E090S0155) | `NAC_PHO_E090S0155_M117392541L` | 46.344.382 | `c66f2af9b5f8…` | 2 | 2213×14282 | 1 |

Số ảnh cắt cộng lại: 15 (mosaic) + 11 (Apollo 16) = 26. STT là mã nguồn trong [S1-02](S1-02_Bang_20_anh_nguon%20(1).docx); thông tin chụp (ngày, góc tới, góc phát) của từng STT xem bảng gốc đó.

**Cách trích dẫn theo yêu cầu của trang sản phẩm LROC** (theo S1-02): mosaic STT 1–6 trích R12 = Robinson et al. (2012); ảnh Apollo 16 STT 8–18 trích M18 = Martin et al. (2018). Chi tiết ở danh mục tham khảo cuối [S1-16_CHUONG_4_NHAP.md](S1-16_CHUONG_4_NHAP.md).

### 2.1. Nguồn đã cân nhắc nhưng không dùng trong bundle

| STT | Nội dung | Tình trạng theo tài liệu nhóm |
|---:|---|---|
| 7 | M111571816R, ảnh NAC Apollo 15 (ALSJ) | Không có trong `sources.json`; **chưa có ghi chép lý do** trong repo |
| 12 | M119747321R, Apollo 16 | Swath hẹp; được thay bằng crop phụ chất lượng cao từ STT 17 (`NHAT_KY_NHOM.csv`, 12/10/2026) |
| 19 | WAC toàn cầu 100 m/px (TIF 1,12 GB) | Không tải để tiết kiệm bộ nhớ (`NHAT_KY_NHOM.csv`) |
| 20 | HiRISE Jezero (Sao Hỏa) | Không tải; bundle chỉ làm Mặt Trăng (Chương 1, mục 1.4) |

## 3. Từ ảnh nguồn đến ảnh cắt

Thực hiện bởi `scripts/generate_s106_crops.py` theo cấu hình `data/s106_bundle/crops.json` (26 mục, mỗi mục có `x0`, `y0`, nhóm vùng, dải đường kính, thông tin nắng).

1. **Đọc ảnh nguồn** bằng `rasterio`; yêu cầu ảnh một băng, CRS chiếu Equirectangular tính bằng mét, mặt cầu Mặt Trăng R = 1.737.400 m, affine không xoay và pixel vuông. Nếu không thỏa, script dừng.
2. **Cắt cửa sổ 512×512** có góc trên-trái `(x0, y0)` theo pixel ảnh nguồn (`crop_x0`, `crop_y0`). Cửa sổ phải nằm trọn trong ảnh nguồn (đã kiểm: cả 26 cửa sổ thỏa). Không thu nhỏ: `downsample_k = 1`.
3. **Mặt nạ hợp lệ** = `rasterio.read_masks()` **và** giá trị hữu hạn. Pixel có giá trị 0 vẫn hợp lệ; không suy mặt nạ từ màu đen. Nguồn TIFF browse không khai báo nodata; cả 26 ảnh có `valid_ratio = 1.0`.
4. **Chuẩn hóa** về [0, 1] bằng phân vị 0,5 % và 99,5 % của các pixel hợp lệ; nếu hai phân vị trùng mà ảnh còn biến thiên thì dùng min/max. Giá trị thực dùng lưu trong `preprocess.percentile_values` và `normalization_bounds`.
5. **Ghi** `.npy` (float32), `.png`, `_valid_mask.npy` (bool) và `.json` đúng hợp đồng [DINH_DANG_DU_LIEU.md](DINH_DANG_DU_LIEU.md); kiểm bằng `validate_metadata`.
6. **Truy vết**: metadata lưu SHA-256 của generator và của `crops.json`, nguồn gốc (`source.*`), CRS dạng WKT và affine của ảnh nguồn.

Cách chọn cửa sổ: nằm trong vùng có ảnh, tránh khoảng trống và đường ghép mosaic (khuyến nghị của S1-02/S1-04); các cặp so sánh dùng cùng cửa sổ hoặc cùng thang đo (mục 6). Khi đổi cửa sổ phải nhìn lại ảnh bằng mắt.

## 4. Quy đổi tọa độ và kích thước

Đây là quy ước **duy nhất** của nhóm, trùng với `src/contracts.py::source_coordinates` và `DINH_DANG_DU_LIEU.md` mục 2.

**Ký hiệu.** `(x, y)` là cột/hàng trong ảnh cắt 512×512, gốc trên-trái, **tâm pixel có tọa độ nguyên**; `(x0, y0) = (crop_x0, crop_y0)`; `k = downsample_k`; `s = scale_m_per_px` của ảnh cắt (đã gồm `k`).

**4.1. Ảnh cắt → ảnh nguồn** (cùng quy ước tâm pixel nguyên):

```text
x_src = x0 + k·x + (k − 1)/2        y_src = y0 + k·y + (k − 1)/2        r_src = k·r
```

Chiều ngược lại: `x = (x_src − x0 − (k − 1)/2) / k`, tương tự cho `y`; `r = r_src / k`. Số hạng `(k − 1)/2` là độ lệch tâm của khối k×k khi thu nhỏ bằng trung bình khối; với `k = 1` (cả 26 ảnh hiện nay) nó bằng 0.

**4.2. Ảnh nguồn → kinh/vĩ độ.** Ma trận affine của `rasterio` (`source_transform = [a, b, c, d, e, f]`) tính theo **góc** pixel, nên phải cộng 0,5 để chuyển từ quy ước tâm-nguyên:

```text
col = x_src + 0,5        row = y_src + 0,5
X = a·col + b·row + c    Y = d·col + e·row + f          (mét; với dữ liệu này b = d = 0, a = s, e = −s)
vĩ độ φ  = Y / R                                         (R = 1.737.400 m, radian)
kinh độ λ = λ0 + X / (R·cos φ1)                          (λ0 = central_meridian, φ1 = standard_parallel_1 trong source_crs_wkt)
```

**4.3. Kinh/vĩ độ → ảnh cắt** (cần khi nhập hố từ danh mục như Robbins): lấy `X = R·(λ − λ0)·cos φ1`, `Y = R·φ` (λ − λ0 chuẩn về (−180°, 180°]); `col = (X − c)/a`, `row = (Y − f)/e`; `x_src = col − 0,5`, `y_src = row − 0,5`; rồi áp công thức ngược ở 4.1.

**4.4. Kích thước.** Đường kính mét `D = 2·r·s`; bán kính pixel `r = D / (2·s)`. Dải tìm kiếm: `r_min = max(5, ⌈D_min/(2s)⌉)`, `r_max = min(128, ⌊D_max/(2s)⌋)`. Ví dụ: 20–500 m ở 2 m/px cho `r` ∈ [5, 125]; 200–4000 m ở 20 m/px cho `r` ∈ [5, 100].

**4.5. Ví dụ kiểm chứng được** (`moon_ap16_m106777343r_c01`, `x0 = 170`, `y0 = 6600`, `k = 1`, `s = 2`, `source_transform = [2, 0, −4929560, 0, −2, −261374]`):

| Bước | Kết quả |
|---|---|
| Tâm ảnh cắt `(x, y)` | (255,5; 255,5) |
| Ảnh nguồn `(x_src, y_src)` | (425,5; 6855,5) |
| `(col, row)` sau khi cộng 0,5 | (426; 6856) |
| `(X, Y)` | (−4.928.708 m; −275.086 m) |
| `(φ, λ)` | (−9,0717548°; 15,4355671°) |
| `center_lat`, `center_lon` trong metadata | −9,071754807836863; 15,435567132509533 → **khớp** |

Script [`scripts/verify_s116_coords.py`](../scripts/verify_s116_coords.py) lặp lại phép tính này cho cả 26 ảnh, so với `center_lat`/`center_lon` đã lưu và kiểm dải bán kính, cửa sổ nằm trong ảnh nguồn. Kết quả ngày 15/10/2026: **26/26 ảnh khớp** (chênh lệch tối đa ≈ 6·10⁻¹⁴ độ, tức sai số làm tròn số thực).

> **Lưu ý đồng nhất.** `S1-10_HUONG_DAN_NHAN_HO.md` mục 3.3 (bước 2–3) từng viết `x_crop = (col_source − crop_x0)/k`, thiếu `(k − 1)/2` và bước trừ 0,5. Với `k = 1` chênh 0,5 pixel (≈ 1 m ở 2 m/px, 10 m ở 20 m/px) — nhỏ so với ngưỡng 0,5·r, nhưng cần một công thức duy nhất. PR #10 đã sửa trực tiếp S1-10 mục 3.3 về đúng quy ước trên.

## 5. Metadata mỗi ảnh

Các trường theo [DINH_DANG_DU_LIEU.md](DINH_DANG_DU_LIEU.md) mục 1: `image_id`, `source_stt`, `product_id`, `crop_x0/y0`, `downsample_k`, `scale_m_per_px`, `center_lat/lon`, `north_up`, `north_angle_deg`, `sun`, `radius`, `valid_ratio`, `preprocess`, `source` (nguồn, CRS, affine), `reference_status`, `reference_note`, `comparison_pair`.

`north_up = true`, `north_angle_deg = 0` do generator ghi sau khi kiểm affine không xoay (`b = d = 0`, `a = −e`) trên CRS Equirectangular. Bản đồ chiếu theo kiểu này có Bắc ở phía trên.

## 6. Hướng nắng và các cặp so sánh

- **Apollo 16** (11 ảnh): góc tới lấy từ trang sản phẩm (7,64°–87,78°). 8 ảnh có `side_only` (nắng phía Tây, `azimuth_deg = 270` là **quy ước, không phải số đo**): STT 8, 9, 10, 13, 14, 17 (2 ảnh), 18. 3 ảnh STT 11, 15, 16 có phía Đông chỉ là **suy từ quy ước dấu**, nên giữ `quality = "none"`, `azimuth_deg = null`.
- **Mosaic STT 1–6**: chỉ có dải góc tới của các ảnh thành phần, lưu ở `incidence_range_deg` (trừ 3 ảnh STT 2 `moon_ap15_loc_c01..03`: nguồn chỉ ghi "Low-Sun" nên `incidence_range_deg = null`); `incidence_deg = null`, không lấy trung điểm làm số đo; không có hướng nắng.
- Với góc tới < 30° (STT 10: 28,38°; STT 17: 7,64°) S1-11 không chấm sáng–tối ([S1-04](S1-04_Dac_ta_tien_xu_ly.docx) đề xuất ngưỡng này; S1-11 dùng làm giá trị ban đầu, chưa chỉnh trên tập điều chỉnh).

Ba kiểu so sánh (chi tiết và giới hạn ở [S1-06_HUONG_DAN_DU_LIEU.md](S1-06_HUONG_DAN_DU_LIEU.md)):

| Kiểu | Ảnh | Có thể nói | Không được nói |
|---|---|---|---|
| Cùng vùng, khác nắng | `moon_ap16_m102064759r_c01` (81,08°) và `moon_ap16_m109134835l_c01` (7,64°); cùng cửa sổ (1190, 2750), cùng CRS/affine, 2 m/px | Minh họa ảnh hưởng chiếu sáng đến số ứng viên/biên | Chênh lệch độ chính xác (chưa có nhãn) |
| Mật độ minh họa | Van de Graaff (cao nguyên) và Mare Frigoris (mare), cùng 20 m/px, D 200–4000 m | Số hố/diện tích hợp lệ với cùng tham số | Tuổi địa chất; điều kiện chiếu sáng khác nhau |
| Apollo 15 high/low-Sun | Hai nhóm ảnh ở tọa độ khác nhau | Hai nhóm điều kiện khác nhau | Thí nghiệm cùng vùng chỉ đổi góc nắng; không cộng diện tích các crop chồng lấp |

## 7. Giới hạn sử dụng

1. Ảnh là **browse 8 bit để xem** (theo LROC RDR SIS, mục 3.2); dùng cho demo xử lý hình học trong môn học, không đo quang học hay trắc địa định lượng.
2. **Chưa có nhãn hố đã xác minh.** Robbins (2019) không đầy đủ cho hố nhỏ hơn 1–2 km, trong khi ảnh 2 m/px có dải 20–500 m. Thiếu nhãn không có nghĩa vùng không có hố.
3. Nhãn thủ công S1-10 hiện là 4 nhãn thưa (C1–C3 và `C4_uncertain`) trên `moon_ap16_m106777343r_c01`, nguồn `unreviewed`, chờ Nguyễn Mạnh Tiến kiểm chéo. **Chưa dùng để tính Precision/Recall hay chấm điểm.** Precision chỉ tính khi một vùng được gán nhãn đầy đủ và đã kiểm chéo.
4. Các cửa sổ cùng mosaic có thể chồng lấp; không coi là mẫu thống kê độc lập (liên quan chia tập ở S2-03).

## 8. Việc còn mở

- [ ] Xác nhận lý do không dùng STT 7 (mục 2.1).
- [ ] [S1-04](S1-04_Dac_ta_tien_xu_ly.docx) mục 5.3 yêu cầu S1-06 kiểm bằng mắt hướng nắng trên một hố rõ ràng (vẽ vector nắng, xem phía tối có nằm về phía +u). S1-11 đã làm bước này cho 8 ảnh Apollo 16 (`data/s111_sun_checks.json`, ảnh phiếu ở `docs/evidence/s1-11/`), do một người kiểm; còn cần người thứ hai kiểm chéo STT 11, 15, 16.
- [x] Đồng nhất công thức quy đổi tọa độ giữa S1-10 và `contracts.py` (PR #10).
- [ ] Đọc toàn văn Robbins (2019) và các nguồn trích dẫn trước khi nộp báo cáo.
- [ ] Điều khoản sử dụng riêng của LROC và của danh mục Robbins chưa tìm thấy (S1-02 mục 5); ghi rõ khi nộp.

## 9. Kiểm tra lại

```bash
python scripts/install_s106_dataset.py          # xác minh SHA-256 và giải nén vào data/processed/
python scripts/verify_s116_coords.py            # kiểm quy đổi tọa độ, dải bán kính, cửa sổ cắt (26 ảnh)
python scripts/download_s106_sources.py         # (tùy chọn) tải lại 16 TIFF từ nguồn, kiểm hash
```
