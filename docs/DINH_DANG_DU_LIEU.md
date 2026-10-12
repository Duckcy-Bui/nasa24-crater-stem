# Định dạng dữ liệu dùng chung — S1-05

Phiên bản đề xuất `1.0`, dựa trên S1-04. Hưng và Tiến cần kiểm tra trước khi nhóm khóa chuẩn này. Đổi chuẩn thì cập nhật tài liệu, mẫu JSON và bộ kiểm tra cùng một commit.

## 1. Ảnh và metadata

Mỗi ảnh chuẩn có bộ tên `<image_id>.npy`, `<image_id>.png`, `<image_id>.json`.

| Trường | Quy ước |
|---|---|
| `schema_version` | `1.0` |
| `data_kind` | `synthetic` cho mẫu giả lập; `real` cho dữ liệu thật |
| `image_id` | Chữ/số/`_`/`-`, duy nhất; không dùng đường dẫn |
| `source_stt`, `product_id` | Mã nguồn theo S1-02; bắt buộc có với dữ liệu thật |
| `body` | `moon` hoặc `mars` |
| `crop_x0`, `crop_y0` | Góc cắt theo pixel ảnh nguồn |
| `downsample_k` | Số nguyên >=1; chỉ thu nhỏ bằng trung bình khối |
| `width`, `height` | 512, 512 |
| `scale_m_per_px` | Tỷ lệ ảnh nguồn nhân `downsample_k` |
| `center_lat`, `center_lon` | Tọa độ địa lý đã xác minh hoặc `null` |
| `north_up`, `north_angle_deg` | Không biết để `null`; Bắc lên trên thì góc bằng 0 |
| `sun` | Phương vị, góc tới, độ tin cậy và nguồn |
| `radius` | Dải đường kính mét và bán kính pixel đã quy đổi |
| `valid_ratio` | Tỷ lệ pixel hợp lệ trong [0,1] |
| `preprocess` | Tham số đã dùng và `version` mã chạy |

`sun.quality` có ba mức `measured`, `side_only`, `none`. Nếu không có hướng nắng thì `azimuth_deg=null`; không suy đoán để điền đủ. Hướng nắng trong ảnh phải kết hợp với hướng Bắc đã xác minh trước khi dùng kiểm tra sáng–tối.

`schema_version` và `data_kind` là hai trường bổ sung để quản lý chuẩn và phân biệt mẫu với dữ liệu thật, không phải metadata đo từ ảnh.

## 2. Hệ tọa độ và bán kính

- `x` là cột, `y` là hàng; gốc ở trên trái, tăng sang phải/xuống dưới.
- Tâm pixel có tọa độ nguyên; tâm hố có thể là số thực.
- Tâm và bán kính lưu theo pixel của ảnh xử lý 512×512. Tâm hợp lệ nằm trong [0,511].
- Vòng tròn có thể chạm mép ảnh; khâu đánh giá/lọc ứng viên quyết định cách xử lý hố bị cắt.
- Quy đổi về ảnh nguồn: `x_src = crop_x0 + k*x + (k-1)/2`, tương tự cho y; `r_src = k*r`.
- Đường kính mét: `D = 2*r*scale_m_per_px`.
- Dải tìm kiếm: `r_min=max(5,ceil(D_min/(2*s)))`, `r_max=min(128,floor(D_max/(2*s)))`. Nếu `r_min>r_max` thì vùng ảnh không phù hợp với dải này.

## 3. Đầu ra tiền xử lý đưa sang Hough

`src/preprocessing.py::preprocess` trả một dict:

```text
gray, enhanced, smooth: float32[512,512], giá trị [0,1]
gx, gy, mag, theta: float32[512,512]
edges, valid_mask: bool[512,512]
params: dict chứa tham số thực sự đã dùng
```

`theta` dùng radian từ `atan2(gy,gx)`; theo kernel Sobel đã thống nhất trong S1-04, x sang phải và y xuống dưới. Tiến và Hưng cần đối chiếu dấu gradient trước khi dùng hướng gradient để bỏ phiếu.

`detect_circles` nhận `edges`, `r_min_px`, `r_max_px`, `params`, `theta` nếu cần. Không truyền danh mục làm đầu vào phát hiện.

## 4. Danh sách hố

Cả máy, danh mục và người chơi dùng cùng cấu trúc:

```json
{
  "schema_version": "1.0",
  "data_kind": "synthetic",
  "image_id": "s105_synthetic_512",
  "source": "machine",
  "reference_source": null,
  "circles": [
    {"crater_id": "M1", "x": 160.0, "y": 180.0, "r": 32.0,
     "confidence": null, "votes": 45}
  ]
}
```

| Trường | Ý nghĩa |
|---|---|
| `source` | `machine`, `catalogue` hoặc `player`; mỗi nguồn lưu file riêng |
| `reference_source` | Danh mục phải ghi nguồn; nguồn khác có thể `null` |
| `crater_id` | Duy nhất trong một danh sách, ví dụ M1/C1/U1 |
| `x`, `y`, `r` | Hệ tọa độ ảnh xử lý; r phải dương |
| `votes` | Số phiếu Hough nguyên không âm; danh mục/người chơi để `null` |
| `confidence` | Điểm đã chuẩn hóa [0,1] hoặc `null` nếu chưa định nghĩa cách chuẩn hóa |

`confidence` không được coi là xác suất đúng nếu chưa có bước hiệu chuẩn. Không đổi tên `x` thành `a` trong file bàn giao; công thức Hough có thể dùng a/b nội bộ.

## 5. Lưu tham số và kết quả

`save_run` lưu `metadata.json`, `params.json`, `craters.json`, `run.json` vào `outputs/<run_id>/`. Mỗi run_id dùng một thư mục riêng, không ghi đè. Ghi mã commit; nếu còn sửa chưa commit thì ghi hậu tố `+working-tree` để không nhầm với phiên bản đã commit.

Mẫu trong `data/examples/` chỉ kiểm tra định dạng. Checker không xác minh vị trí thật trên ảnh, độ chính xác Hough hay mức đầy đủ của danh mục.
