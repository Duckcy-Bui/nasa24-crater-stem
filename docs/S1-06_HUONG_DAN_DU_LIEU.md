# Bàn giao bộ ảnh S1-06

Repo chứa bundle ngoại tuyến `data/s106_bundle/s106_lroc_browse_v2.zip`: **26 ảnh LROC thật**, cắt từ 16 TIFF tải từ máy chủ LROC/PDS chính thức. Mỗi ảnh có `.npy` float32 [0,1], `.png`, metadata `.json` và `_valid_mask.npy` bool. Clone repo là có thể kiểm tra và giải nén; không cần tải lại 480 MiB ảnh nguồn.

## Chạy trên máy thành viên

Từ thư mục gốc repo, sau khi cài `requirements.txt`:

```bash
python scripts/install_s106_dataset.py
python -m unittest discover -s tests -v
```

Lệnh cài kiểm tra SHA256 của ZIP, từng file, nguồn và cấu hình; sau đó giải nén vào `data/processed/` (được Git bỏ qua). `.gitattributes` giữ Python/JSON/CSV ở LF trên Linux và Windows, tránh Git đổi xuống dòng làm sai hash manifest. Việc dùng bundle không yêu cầu generator trên máy bạn còn nguyên phiên bản; hash generator trong metadata ghi phiên bản đã tạo bộ ảnh. Cài lại cùng dữ liệu là hợp lệ. Nếu bạn đã sửa file đầu ra, dùng thư mục mới hoặc chủ động thêm `--overwrite` sau khi sao lưu. Nếu có catalogue cũ từ phiên bản PR ban đầu, hãy di chuyển chúng ra khỏi `data/processed/`; công cụ từ chối để nhãn chưa xác minh không bị sử dụng nhầm.

```bash
python scripts/install_s106_dataset.py --output-dir /tmp/s106-data
```

Bộ này **chưa có nhãn hố tham chiếu đã xác minh**. Metadata ghi `reference_status: "unavailable"`; không tạo file `*_craters_catalogue.json`. Chưa được chấm Precision/Recall hoặc điểm trò chơi dựa trên danh mục này. Bước S1-10 cần nhập nhãn thật, ghi nguồn/ID hố và kiểm tra khớp tọa độ. Robbins không đầy đủ cho nhóm hố nhỏ 20–500 m; các ảnh đó cần nhãn thủ công được kiểm tra chéo. Thiếu nhãn không đồng nghĩa vùng không có hố.

## Tái tạo từ nguồn chính thức

Manifest `data/s106_bundle/sources.json` lưu URL TIFF, URL trang sản phẩm, số byte và SHA256 của **từng file nguồn tải ngày 14/10/2026**. Các cửa sổ cắt trong `crops.json`. Script từ chối file tải thiếu hoặc sai hash; không coi dữ liệu dở dang là bộ hoàn thành.

```bash
python scripts/download_s106_sources.py
python scripts/generate_s106_crops.py --output-dir /tmp/s106-reproduced
python scripts/build_s106_bundle.py --processed-dir /tmp/s106-reproduced
```

Hai lệnh đầu tái tạo ảnh. Lệnh cuối dành cho người duy trì bộ dữ liệu: tạo ZIP có thứ tự/timestamp cố định và cập nhật manifest; không cần chạy khi chỉ sử dụng ảnh. Khi đổi generator hoặc cửa sổ, tái tạo cả ảnh/bundle để hash phiên bản trong metadata không bị cũ. Metadata lưu hash generator, hash cấu hình, phân vị thực tế, cận chuẩn hóa và chiến lược thực dùng, transform và CRS nguồn để truy vết. Nếu hai phân vị trùng nhưng ảnh còn biến thiên (vật thể nhỏ trên nền phẳng), dùng min/max; ảnh hằng thật mới trả ảnh 0.

Chuẩn hóa chỉ lấy pixel hợp lệ theo `rasterio.read_masks()` và giá trị hữu hạn. Pixel 0 hợp lệ vẫn được giữ; nodata dương không bị tính là dữ liệu. Mặt nạ luôn đi cùng ảnh chuẩn. Nguồn TIFF browse hiện không khai báo nodata; mask raster nguồn không phân biệt thêm vùng trống. Các cửa sổ đã được chọn bên trong vùng có ảnh, cần kiểm tra trực quan khi thay cửa sổ. Không suy mask chỉ từ màu đen.

## Hai kiểu so sánh và giới hạn

- **Cặp cùng vùng Apollo 16**: `moon_ap16_m102064759r_c01` (STT 9, góc tới 81,08°) và `moon_ap16_m109134835l_c01` (STT 17, 7,64°). Cùng cửa sổ (1190,2750), cùng CRS/transform, 512×512 ở 2 m/px. Có thể minh họa ảnh hưởng chiếu sáng tới số ứng viên/biên; chưa gọi đó là chênh lệch độ chính xác khi thiếu nhãn.
- **So sánh mật độ minh họa**: Van de Graaff (cao nguyên) và Mare Frigoris (mare) cùng 20 m/px, D 200–4000 m. Báo số hố/diện tích hợp lệ cùng tham số, nêu yếu tố chiếu sáng và sai số phát hiện. Chưa đủ để suy ra tuổi địa chất.
- **Apollo 15 high/low-Sun** ở các tọa độ khác nhau: chỉ là hai nhóm ảnh điều kiện khác nhau, không phải thí nghiệm cùng vùng chỉ thay góc nắng. Các cửa sổ trong cùng mosaic có thể chồng lấp; không coi chúng là mẫu thống kê độc lập hoặc cộng diện tích để tạo một vùng duy nhất.

Các mosaic chỉ có dải góc tới của ảnh thành phần; `incidence_deg=null`, lưu dải trong `incidence_range_deg`. Không lấy trung điểm dải làm số đo cửa sổ. Apollo 16 có giá trị góc tới từ trang sản phẩm; phía Tây từ S1-02 được biểu diễn thô `side_only`, phương vị quy ước 270°, **không phải số đo phương vị**. Phía Đông của STT 11/15/16 còn là suy từ quy ước dấu: giữ `side_candidate="east"`, `quality="none"`, `azimuth_deg=null` cho tới khi xác minh. Với góc tới <30°, S1-11 cần bỏ qua kiểm tra sáng–tối như S1-04 yêu cầu.

## Nguồn và mức sử dụng

Credit: **NASA/GSFC/Arizona State University (LROC)**. Các trang sản phẩm trong `sources.json` là nguồn trực tiếp. [LROC RDR Software Interface Specification](https://pds.lroc.im-ldi.com/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/DOCUMENT/RDRSIS.PDF), mục 3.2, mô tả TIFF browse là bản 8 bit để xem, không dùng cho đo đạc/phân tích khoa học định lượng. Bundle dùng cho **demo xử lý hình học ảnh trong môn học**, không khôi phục quang học/I/F hoặc độ chính xác trắc địa từ ảnh này. Khi làm nghiên cứu định lượng cần tải PDS `.IMG`, dữ liệu mặt nạ chuẩn và nhãn thật; đó không phải chất lượng đã được xác nhận trong bundle.
