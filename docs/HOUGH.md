# S1-07: Hough tròn tự viết bằng NumPy

`src/hough.py` không gọi `cv2.HoughCircles` hay hàm Hough của thư viện khác.
Đầu vào là ảnh biên `bool` 512×512, khoảng bán kính nguyên 5–128 px và tham số
Hough. Bước bán kính mặc định là 1 px; tâm dùng hệ tọa độ ảnh: x sang phải,
y xuống dưới. Tâm phải nằm trong ảnh, nhưng vòng tròn có thể bị cắt ở mép.


## Ví dụ tính tay và nháp lý thuyết

- [S1-12 — Ví dụ 5×5 và đối chiếu OpenCV](S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md):
  từng phép bỏ phiếu, ma trận cộng dồn, ngưỡng, đỉnh, NMS và chênh lệch thực chạy.
- [S1-15 — Nháp Chương 2 về Hough](S1-15_LY_THUYET_HOUGH.md):
  dẫn xuất công thức, sơ đồ gọi hàm trong `hough.py`, giả mã và chi phí.
- [Danh mục 12 nguồn / 3 bài DOI](TAI_LIEU_THAM_KHAO_HOUGH.md):
  ghi riêng mức xác minh và phần còn cần đọc toàn văn.

```powershell
python -B scripts/verify_hough_examples.py --tiny-only
python -B scripts/verify_hough_examples.py
```

Ví dụ 5×5 dùng các hàm nội bộ; API phát hiện vẫn yêu cầu ảnh 512×512 và
bán kính 5–128 px. Mã đối chiếu thư viện nằm riêng trong script S1-12.

![Minh họa Hough trên ba vòng tròn giả lập](images/hough_synthetic_demo.png)

Ảnh do `scripts/demo_hough.py --method full_circle` tạo: tâm và bán kính
được biết từ cách dựng hình. Đây là minh họa thuật toán, không phải ảnh NASA
hay kết quả đánh giá độ chính xác trên dữ liệu thật. Thời gian trên ảnh là
thời gian của một lần chạy trên máy tạo ảnh; không phải cam kết hiệu năng.

## Hai cách bỏ phiếu

- `voting_method="full_circle"` (mặc định): mỗi điểm biên bỏ phiếu cho các tâm
  trên một vòng bán kính r. Tọa độ tâm được làm tròn và loại offset trùng để
  không tăng phiếu giả do nhiều góc cùng rơi vào một pixel. Mỗi bán kính giữ
  một accumulator 2 chiều. Bỏ phiếu theo lô bằng `np.bincount` giữ nguyên kết
  quả cộng phiếu, giảm thời gian so với `np.add.at`.
- `voting_method="gradient"` (tùy chọn): cần thêm `theta = arctan2(gy, gx)`
  theo radian. Mỗi điểm biên chỉ bỏ phiếu theo hai hướng của pháp tuyến,
  `a=x±r*cos(theta)`, `b=y±r*sin(theta)`, vì chưa biết hố sáng hay tối. Cách này
  nhanh hơn trên ảnh nhiều biên, nhưng nhạy với hướng gradient nhiễu hoặc
  mép hố không tròn. Không tự chuyển phương pháp nếu thiếu theta.

`angle_step_deg` và `edge_batch_size` chỉ điều khiển bỏ phiếu `full_circle`.
Khi cung cấp theta cho `full_circle`, hàm kiểm tra định dạng nhưng không dùng
hướng đó.

Ở mỗi bán kính, ngưỡng là `max(min_votes, ceil(min_vote_ratio * support_size))`.
Với `full_circle`, `support_size` là số offset khác nhau. Với `gradient`, nó
là chu vi ước lượng `ceil(2*pi*r)` vì mọi pixel biên có thể bỏ phiếu; không
dùng số mẫu góc làm mẫu số để tránh ưu tiên sai bán kính lớn.
Sau cực đại cục bộ 3×3, các ứng viên được xếp theo tỷ lệ phiếu, rồi khử trùng
tâm/bán kính bằng NMS. Tỷ lệ phiếu chỉ là mức hỗ trợ để xếp hạng, chưa phải
xác suất. Đầu ra giữ `confidence=null`, `votes` nguyên, `crater_id` duy nhất
và các trường `x,y,r` đúng hợp đồng S1-05. Điểm hỗ trợ giữa hai phương pháp
không thể coi là số đo độ chính xác đã hiệu chuẩn.

Vòng bị cắt quá nhiều tại mép hoặc mép hố bị đứt có thể không đủ ngưỡng.
Ảnh biên dày/nhiễu có thể sinh vòng giả; cần bước lọc sáng–tối, khử trùng
S1-11/S2 và đánh giá với nhãn thật. Không dùng demo làm bằng chứng NASA.

## Chạy và bàn giao

Sau khi cài `requirements.txt`, từ thư mục gốc repo:

```bash
python scripts/demo_hough.py --method full_circle
python scripts/demo_hough.py --method gradient
python -m unittest discover -s tests -v
```

Demo tự tạo ba hố giả lập có tâm/bán kính biết trước, gồm một hố bị cắt tại
mép. Nó yêu cầu tìm lại cả ba trong sai số 1 px, lưu ảnh `demo.png` có vòng
phát hiện và accumulator, `synthetic_truth.json`, ảnh/biên/theta `.npy`, thời
gian chạy và JSON theo `save_run`. Mỗi lần chạy có thư mục riêng trong
`outputs/`; không ghi đè lần chạy cũ. `params.json` chứa tất cả tham số mặc
định đã được giải quyết, phương pháp và khoảng bán kính thực dùng. `run.json`
ghi commit hoặc commit kèm `+working-tree` nếu mã chưa được commit.

Cả metadata, dự đoán và danh mục demo đều là `data_kind="synthetic"`;
nguồn danh mục ghi rõ hình tròn do script tạo, không gắn nhãn Robbins.
Tỷ lệ 2 m/px trong demo chỉ là giả định để kiểm tra hợp đồng dữ liệu.
Ảnh minh họa này dùng biên và gradient giải tích để tách kiểm tra Hough
khỏi tiền xử lý. Chạy ghép với S1-08 và bộ ảnh thật là kiểm tra riêng.

```python
from src.hough import detect_circles, resolve_hough_params

params = resolve_hough_params({"hough": {"voting_method": "gradient"}})
circles = detect_circles(edges, 10, 125, params, theta=theta)
```

Khi ghi kết quả thật, giữ metadata nguồn ảnh, lưu `params` đã giải quyết và
phiên bản mã; không gán tọa độ hố giả lập thành danh mục tham chiếu thật.

## Kiểm tra ghép các PR ngày 14/10/2026

Bản ghép S1-06/S1-07/S1-08 đã đọc đúng ảnh, mặt nạ, metadata và chạy tiền xử lý + Hough gradient trên cả 26 ảnh trong bundle. Chạy thêm full-circle mặc định trên cặp Apollo 16 STT 9/17 và một ảnh Mare Frigoris; kết quả máy qua bộ kiểm tra định dạng. Bốn đĩa sáng/nền phẳng bán kính 24/32/64/100 px cũng đi qua tiền xử lý và được Hough tìm lại.

Đây là kiểm tra ghép module, **không phải xác nhận độ chính xác**: chưa có nhãn hố thật. Với tham số mặc định hiện tại, gradient chỉ giữ 0–2 ứng viên mỗi ảnh; full-circle trên ba ảnh thử đạt giới hạn 100 ứng viên. Cần điều chỉnh ngưỡng, lọc ứng viên và đánh giá ở các đầu việc tiếp theo; chưa dùng các danh sách máy này làm đáp án khoa học. Giữ full-circle làm mặc định, gradient là lựa chọn thử nghiệm có thể bỏ sót khi hướng biên không đúng pháp tuyến vành hố.

## Cập nhật S2-01 / S2-06 / S3-02 ngày 27/10/2026

Mặc định mã và game vẫn dùng `score`. Chế độ `radius_balanced` trước NMS/giới hạn đầu ra
chỉ bật tường minh trong `configs/s201_large_craters.json` để thử nghiệm; S2-15 chưa chốt cấu hình game.
Xem [báo cáo thực chạy](S2-06_S3-02_KIEM_CHUNG.md) và [lý thuyết cập nhật](S2-11_S3-06_HOUGH_HOAN_THIEN.md).
