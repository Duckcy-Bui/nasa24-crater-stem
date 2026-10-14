# Hướng dẫn ghi nhãn hố tham chiếu — S1-10

Phụ trách: **Hoàng Quốc Anh**. Phối hợp/nghiệm thu: **Nguyễn Mạnh Tiến**.  
Hạn ưu tiên: Nhãn thật cho **ảnh demo trước trưa 15/10/2026**; Tiến kiểm tra chéo và nghiệm thu sau đó.

> [!IMPORTANT]
> Nhãn thủ công và nhãn Robbins phải ghi nguồn **rõ ràng, tách biệt**. Không gán nhãn Robbins cho hố chưa đối chiếu tọa độ pixel thực tế. Hố chưa chắc chắn phải đánh dấu `_uncertain` trong `crater_id`. Toàn bộ nhãn tham chiếu bàn giao được lưu trong thư mục `data/reference_labels/` để Git theo dõi.

---

## 1. Thứ tự ưu tiên ảnh và cặp so sánh

| Ưu tiên | image_id | Scale | Góc tới | Mục đích sử dụng |
|---|---|---|---|---|
| **1 (Demo)** | `moon_ap16_m106777343r_c01` | 2.0 m/px | 28.38° (Tây) | **Ảnh demo chính S1-10**: Địa hình cao nguyên Apollo 16 rõ nét, tương phản tốt, không bóng đổ cực đoan. |
| **2a (Cặp so sánh)** | `moon_ap16_m102064759r_c01` | 2.0 m/px | 81.08° (Đông) | Cùng cửa sổ mặt đất `(1190, 2750)`, cùng CRS/affine với 2b. Bóng đổ rất dài (Low-Sun). |
| **2b (Cặp so sánh)** | `moon_ap16_m109134835l_c01` | 2.0 m/px | 7.64° (gần đỉnh đầu) | Cùng cửa sổ mặt đất `(1190, 2750)` với 2a. Chiếu sáng thẳng đứng, gần như không bóng (High-Sun). |
| **3–5** | `moon_ap15_hia_c01..c03` | 20.0 m/px | 28°–53° | Khu vực Apollo 15, hố lớn hơn, phù hợp đối chiếu danh mục Robbins (D > 1–2 km). |

> [!NOTE]
> Cặp ảnh so sánh ánh sáng trên cùng một vùng địa hình đã được nhóm chốt tại [S1-06_BANG_ANH_XA_ANH_CAT.md](S1-06_BANG_ANH_XA_ANH_CAT.md) (dòng 7) là `moon_ap16_m102064759r_c01` và `moon_ap16_m109134835l_c01`.

---

## 2. Công cụ ghi nhãn `scripts/label_craters.py`

### 2.1. Cách chạy script

```bash
# Ảnh demo mặc định (moon_ap16_m106777343r_c01)
.venv\Scripts\python.exe scripts/label_craters.py

# Chỉ định ảnh khác
.venv\Scripts\python.exe scripts/label_craters.py moon_ap15_hia_c01

# Ghi nhãn từ danh mục Robbins 2019
.venv\Scripts\python.exe scripts/label_craters.py moon_ap15_hia_c01 --source "Robbins 2019 DOI:10.1029/2018JE005592 crater_id=XXXXX"

# Chế độ toàn bộ nhãn mới là uncertain
.venv\Scripts\python.exe scripts/label_craters.py moon_ap16_m106777343r_c01 --uncertain
```

### 2.2. Thao tác tương tác trong cửa sổ

| Thao tác | Tác dụng | Chi tiết kỹ thuật |
|---|---|---|
| **Click 1 (chuột trái)** | Chọn **TÂM** hố $(x, y)$ | Tọa độ phải thuộc phạm vi $[0, 511]$; hiển thị dấu `+` màu trắng. |
| **Click 2 (chuột trái)** | Chọn điểm trên **VÀNH** | Tự tính bán kính $r = \sqrt{(x - x_c)^2 + (y - y_c)^2}$. Cảnh báo nếu $r$ nằm ngoài $[r_{\min}, r_{\max}]$. |
| **Phím `U`** | Đổi trạng thái **Uncertain** | Chuyển đổi qua lại giữa nhãn chắc chắn (cyan) và uncertain (cam); tự cập nhật `_uncertain` trong ID và màu vòng tròn tức thì. |
| **Phím `Z`** | **Hoàn tác** | Nếu đang chờ click vành: hủy click tâm. Nếu ở trạng thái nghỉ: xóa đúng vòng tròn và nhãn của hố vừa tạo. |
| **Phím `S`** | **Lưu kết quả** | Gọi `validate_crater_set`; chỉ đóng cửa sổ khi lưu thành công cả JSON và ảnh overlay PNG. |
| **Phím `Q`** | **Thoát** | Đóng cửa sổ không lưu thay đổi phiên hiện tại. |

---

## 3. Quy chuẩn tọa độ và quy tắc nhãn

### 3.1. Quy ước hệ tọa độ pixel

- Gốc tọa độ $(0, 0)$ đặt tại **góc trên-bên trái**, trục $x$ tăng dần sang phải $[0, 511]$, trục $y$ tăng dần xuống dưới $[0, 511]$.
- Extent hiển thị được cấu hình `[-0.5, 511.5, 511.5, -0.5]` để tâm của pixel đầu tiên khớp chính xác với tọa độ $(0, 0)$.

### 3.2. Nhãn thủ công (`manual_label_s110`)

- Áp dụng cho: Hố nhỏ $D < 1\text{ km}$ (đặc biệt các ảnh Apollo 16 có dải $D \in [20\text{ m}, 500\text{ m}]$, nơi danh mục Robbins không có dữ liệu).
- `reference_source`: Bắt đầu bằng `"manual_label_s110; <ghi chú kiểm tra>"`.
- `crater_id`: Đặt theo dạng `C1`, `C2`,... (chắc chắn) hoặc `C4_uncertain` (chưa chắc chắn).
- `confidence`: `null` (không tự ý đặt điểm số khi chưa qua mô hình định lượng).
- `votes`: `null`.

### 3.3. Nhãn từ danh mục Robbins 2019

Chỉ sử dụng cho các hố lớn $D \ge 1\text{--}2\text{ km}$ (chủ yếu trên các ảnh Apollo 15 ở độ phân giải 20 m/px).

#### Quy trình quy đổi tọa độ chuẩn xác:

1. **Chiếu tọa độ địa lý sang tọa độ phẳng ảnh nguồn:**
   - Đọc định dạng CRS từ `metadata["source"]["source_crs_wkt"]`.
   - Dùng thư viện phép chiếu (như `pyproj.Proj`) để biến đổi `(lon_crater, lat_crater)` $\to (X, Y)$ trong hệ tọa độ phẳng của ảnh nguồn.
2. **Nghịch đảo affine sang tọa độ pixel ảnh nguồn:**
   - Đọc ma trận biến đổi affine 6 tham số từ `metadata["source"]["source_transform"]`:
     $$\begin{pmatrix} X \\ Y \end{pmatrix} = \begin{pmatrix} a & b & c \\ d & e & f \end{pmatrix} \begin{pmatrix} col_{source} \\ row_{source} \\ 1 \end{pmatrix}$$
   - Giải phương trình nghịch đảo để tìm $(col_{source}, row_{source})$.
3. **Quy đổi sang tọa độ ảnh cắt 512×512:**
   - Dùng thông số cắt `crop_x0`, `crop_y0` và hệ số giảm mẫu `downsample_k` trong metadata:
     $$x_{crop} = \frac{col_{source} - crop\_x0}{downsample\_k}$$
     $$y_{crop} = \frac{row_{source} - crop\_y0}{downsample\_k}$$
     $$r_{px} = \frac{D_{km} \times 1000}{2 \times scale\_m\_per\_px}$$
4. **Bắt buộc đối chiếu trực quan bằng mắt:**
   - Mở ảnh PNG tương ứng, kiểm tra xem tại $(x_{crop}, y_{crop})$ có thực sự tồn tại hình thái hố va chạm khớp với bán kính $r_{px}$ hay không.
   - Nếu khớp: Ghi nhận với nguồn định danh rõ:
     `--source "Robbins 2019 DOI:10.1029/2018JE005592 crater_id=<ID_cu_the>"`
   - Nếu bị lệch hoặc mờ: Bấm `U` để gắn nhãn `_uncertain`. Tuyệt đối không gán nhãn Robbins nếu ảnh không quan sát thấy hố.

---

## 4. Quản lý nhãn Uncertain và Kiểm tra chéo

### 4.1. Tiêu chí gắn nhãn `uncertain`
- Hố bị xói mòn nặng, bờ vành không khép kín.
- Hố nằm trong vùng bóng đổ sâu hoặc có địa hình đá gồ ghề dễ gây nhầm lẫn.
- Tọa độ danh mục chiếu vào nhưng độ tương phản quá thấp.

### 4.2. Vai trò của `validate_crater_set` vs Kiểm tra chéo
- **`validate_crater_set`**: Chỉ kiểm tra hợp đồng cấu trúc dữ liệu, kiểu dữ liệu, các trường bắt buộc và giới hạn tọa độ trong $[0, 511]$. Hàm này **không** xác nhận vị trí hố có đúng thật trên ảnh hay không.
- **Kiểm tra chéo (Nguyễn Mạnh Tiến)**:
  - Mở file ảnh overlay minh chứng (`data/reference_labels/<image_id>_overlay.png`).
  - Đối chiếu từng vòng tròn với địa hình thực tế.
  - Quyết định: Giữ lại nhãn chắc chắn; xác nhận hoặc loại bỏ các nhãn `_uncertain`.

### 4.3. Ứng dụng khi tính Precision / Recall (S1-11)
- **Kịch bản A (Khắt khe)**: Chỉ sử dụng các hố chắc chắn (`C1, C2...`) làm Ground Truth.
- **Kịch bản B (Thực tế)**: Nhãn `_uncertain` được đưa vào tập bỏ qua (ignored set) — nếu mô hình phát hiện trúng thì không phạt False Positive, nếu bỏ qua thì không phạt False Negative.

---

## 5. Quy chuẩn bàn giao qua Git

Do thư mục `data/processed/*` bị loại trừ trong `.gitignore`, toàn bộ kết quả nhãn tham chiếu bàn giao được tổ chức trong thư mục **`data/reference_labels/`** (được Git theo dõi):

```
data/reference_labels/
├── README.md
├── moon_ap16_m106777343r_c01_craters_catalogue.json   # File nhãn JSON chuẩn
└── moon_ap16_m106777343r_c01_overlay.png             # Ảnh vẽ vòng tròn minh chứng trực quan
```

Khi chạy `scripts/label_craters.py`, script sẽ tự động đồng bộ file JSON vào cả `data/reference_labels/` và `data/processed/`.

---

## 6. Checklist nghiệm thu S1-10

- [x] Đã sửa lỗi nạp nhãn cũ: không làm mất nhãn cũ, bộ đếm `counter` tự tăng tiếp không trùng ID.
- [x] Đã sửa phím `U`: đồng bộ trạng thái `_uncertain` cả trong dữ liệu JSON lẫn màu cam và text trên giao diện.
- [x] Đã sửa phím `Z`: ưu tiên hủy tâm đang chờ click; xóa đúng đối tượng đồ họa của hố vừa tạo.
- [x] Đã sửa `_save()`: kiểm tra `validate_crater_set` chặt chẽ, chỉ đóng cửa sổ khi lưu thành công.
- [x] Đã chuẩn hóa extent `[-0.5, 511.5, 511.5, -0.5]` và kiểm tra tâm nằm trong $[0, 511]$.
- [x] Đã tách bạch nguồn tham chiếu `manual_label_s110` vs `Robbins 2019`.
- [x] Đã đưa dữ liệu nhãn tham chiếu và ảnh overlay vào thư mục `data/reference_labels/` được Git theo dõi.
- [x] Đã hoàn thành bộ nhãn thật 4 hố trên ảnh demo `moon_ap16_m106777343r_c01` (C1, C2, C3 chắc chắn; C4_uncertain).
- [ ] Nguyễn Mạnh Tiến kiểm tra chéo file overlay và xác nhận nghiệm thu PR.
