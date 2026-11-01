<!-- S3-12, 01/11/2026: rút theo giao việc của Đức trên main c466c2d (đã gồm PR #26, #31, #33–#36).
Bảng mọi chỗ cắt, kèm lý do và chủ phần, ở mô tả PR S3-12. Chủ phần chưa xác nhận bản rút gọn; bản trước rút là main c466c2d.
-->

# Chương 3. Phương pháp và cài đặt

Chuỗi phát hiện dùng lý thuyết ở Chương 2 và được đánh giá ở Chương 4. STT 13 (`moon_ap16_m132732855l_c01`, góc tới 87,7°) và STT 17 (`moon_ap16_m109134835l_c01`, 7,64°) là hai ảnh Apollo 16 ở 2 m/px.

## 3.1. Tổng quan chuỗi phát hiện

Hàm `run_end_to_end` trong `src/pipeline.py` chạy chuỗi trên một ảnh cắt 512 × 512 px. Phần lõi `detect_machine` cũng được màn hình chấm bài của trò chơi dùng lại, nên hai nơi cho cùng một danh sách ứng viên máy.

```text
ảnh .npy + metadata .json + mặt nạ hợp lệ
 ▼ preprocess()        B1…B8: edges, theta, gray
 ▼ detect_circles()    Hough NumPy, r ⊂ [5, 128] px
 ▼ filter_candidates() gắn nhãn sáng–tối
 ┊ review_candidates(), apply_filter()   (chưa bật)
 ┊ dedupe_circles()                      (chưa bật)
 ▼ save_run()          outputs/e2e_<image_id>_<UTC>_<id>/
```

Hai mô-đun phân lớp ứng viên (mục 3.4.3) và lọc vòng trùng (mục 3.5) đã cài đặt và thử trên ảnh có nhãn, nhưng chuỗi mặc định chưa gọi. Đầu ra mặc định vì vậy là danh sách ứng viên máy thô (`source = "machine"`) kèm nhãn sáng–tối. Trường `confidence` để `null` vì số phiếu Hough chưa được hiệu chuẩn thành xác suất.

Mỗi lần chạy tạo một thư mục mới, gồm danh sách vòng, metadata, tham số đã dùng, mã commit, thời gian từng bước và ảnh overlay. Nếu một bước lỗi, cả thư mục bị xóa.

Lần chạy 26 ảnh ngày 15/10/2026 không lỗi nhưng đều chạm trần 100 ứng viên; thời gian và overlay lịch sử ở Phụ lục E.2.

## 3.2. Cài đặt tiền xử lý

### 3.2.1. Các bước và phần tự viết

Chuỗi B0–B8 nằm trong `src/preprocessing.py`; nguyên lý ở mục 2.1. Bảng 3.1 cho biết phần tự viết, phần dùng thư viện và tham số mặc định.

| Bước | Thao tác | Cài đặt | Tham số mặc định |
|---|---|---|---|
| B0 | Đọc file, cắt cửa sổ 512·k, mặt nạ nodata | Thư viện rasterio | — |
| B1 | Thu nhỏ trung bình khối k × k | Tự viết | k theo metadata |
| B2 | Ảnh xám BT.601 [@itu601] | Tự viết | — |
| B3 | Chuẩn hóa theo phân vị | Tự viết | 0,5 % và 99,5 % |
| B4 | CLAHE | OpenCV `createCLAHE` | `clipLimit` 2,0; lưới 8 × 8; 8 bit |
| B5 | Gauss tách hai chiều | Tự viết | σ = 1,5; kernel 11 |
| B6 | Sobel 3 × 3, \|G\|, θ | Tự viết | không chia 8 |
| B7 | Canny | OpenCV `Canny`; ngưỡng tự viết | $T_{high}$ = P90 của \|G\|·255; $T_{low}$ = 0,4 $T_{high}$ |
| B8 | Bỏ biên trong lề tính từ mép và vùng nodata | Tự viết | lề 6 px |

: Bảng 3.1. Các bước tiền xử lý, phần tự viết và phần dùng thư viện.

"Tự viết" nghĩa là chỉ dùng phép toán mảng của NumPy, không gọi hàm lọc ảnh dựng sẵn. B5 và B6 dùng chung hàm `correlate_1d`: đệm ảnh bằng `np.pad(mode="reflect")`, tương đương biên `BORDER_REFLECT_101` của OpenCV, rồi cộng dồn các lát cắt dịch chuyển nhân trọng số trong float64. CLAHE và Canny dùng thư viện vì dài và không phải trọng tâm đề tài [@zuiderveld1994; @opencv_clahe; @canny1986; @opencv_canny]. Hàm `preprocess` ghi vào `params` cả giá trị tính ra như $T_{low}$, $T_{high}$ và số pixel biên. Ảnh `.npy` đã có cỡ 512 × 512 nên B1 được bỏ qua. Ảnh phẳng trả biên rỗng, ảnh toàn nodata bị từ chối, và lề B8 tự tăng theo kernel Gauss.

### 3.2.2. Kết quả và kiểm chứng

Hình 3.1 cho thấy từng bước trên STT 13. Ngưỡng Canny tự co theo độ tương phản: STT 13 có $T_{low}$ = 63,6 và $T_{high}$ = 159,0, còn STT 17 có 46,3 và 115,8, thấp hơn khoảng 27 %. Số pixel biên sau B8 là 24.291 ở STT 13 và 26.642 ở STT 17, khoảng 9–10 % diện tích ảnh. Trên 26 ảnh, số này từ 20.949 đến 35.590. Phần lớn là biên kết cấu, không phải vành hố.

![Hình 3.1. Các bước tiền xử lý trên ảnh STT 13 (nắng Tây, góc tới 87,7°). Tiêu đề xanh: bước tự viết; đỏ: bước dùng thư viện. Canny giữ 25.203 pixel biên, còn 24.291 pixel sau B8.](../images/s114/truoc_sau_stt13.png){width=75%}

Phần tự viết được so với OpenCV trong 33 bài kiểm thử. CLAHE dùng 8 bit để tránh ngưỡng cắt luôn bằng 1 ở 16 bit. Số đo sai khác và ảnh hưởng lượng tử ở Phụ lục E.2; các phép đo phụ này chưa có script trong repo.

### 3.2.3. Hạn chế

- Ngưỡng P90 giả định khoảng 10 % pixel là biên mạnh. Trên vùng gồ ghề, Canny giữ nhiều biên kết cấu, nên Hough nhận nhiều phiếu rác.
- Ở ảnh nắng rất xiên, mép bóng có gradient mạnh hơn vành hố. Tiền xử lý không phân biệt được hai loại biên này; mục 3.4.3 xử lý ở mức ứng viên.
- 11,1 % pixel của STT 17 và 3,2 % của STT 13 đã bão hòa ở mức 255 trong ảnh nguồn 8 bit. Ảnh này chỉ dùng minh họa xử lý ảnh, không dùng đo quang học [@lroc_rdrsis].

## 3.3. Cài đặt Hough tròn bằng NumPy

Hough tròn tự cài đặt bằng NumPy nằm trong `src/hough.py`, không gọi `cv2.HoughCircles` hay hàm Hough của thư viện khác. Tâm pixel có tọa độ nguyên, x sang phải, y xuống dưới. Lý thuyết và chi phí tính toán ở mục 2.2 [@duda1972; @yuen1990].

### 3.3.1. Cấu trúc dữ liệu và vector hóa

Mỗi bán kính dùng một accumulator int32 cỡ 512 × 512 (1 MiB); chỉ các đỉnh được giữ qua các bán kính. Điểm biên được xử lý theo lô 256, tạo tâm bằng broadcast, loại tâm ngoài ảnh rồi đếm chỉ số phẳng bằng `np.bincount`. Bảng độ lệch được khử trùng như (2.9). Mã rút gọn ở Phụ lục E.3.

### 3.3.2. Cách bỏ phiếu và dải bán kính

Cách mặc định `full_circle` bỏ phiếu theo bảng độ lệch trên. Cách tùy chọn `gradient` cần `theta` từ B6: mỗi điểm biên chỉ bỏ phiếu cho hai tâm ở hai đầu pháp tuyến, với $S_r = \lceil 2\pi r \rceil$. Thiếu `theta` thì hàm báo lỗi. Khi kiểm tra ghép mô-đun ngày 14/10/2026, cách `gradient` chỉ giữ 0–2 ứng viên mỗi ảnh với tham số mặc định, nên nhóm giữ `full_circle` làm mặc định.

Dải quét là giao giữa dải của ảnh và giới hạn cấu hình: $r_{\min} = \max(r_{\min}^{\text{meta}}, 5)$, $r_{\max} = \min(r_{\max}^{\text{meta}}, 128)$. Với bộ 26 ảnh, dải này là 5–125 px cho 11 ảnh 2 m/px và 5–100 px cho 15 ảnh 20 m/px. `params.json` ghi bán kính thực quét; ví dụ dải [12, 29] bước 4 chỉ quét 12, 16, 20, 24, 28.

### 3.3.3. Chọn đỉnh và giới hạn số vòng

Ngưỡng phiếu và điểm q theo (2.12), cực đại trong cửa sổ 3 × 3; ví dụ r = 10 cần 28 phiếu. Sắp theo (−q, −phiếu, y, x, r), rồi NMS theo (2.13), dừng ở `max_circles`. q là điểm xếp hạng, không phải xác suất. Tham số ở Bảng E.2.

Cấu hình dùng `full_circle`, bước r = 1 px, bước góc 1°, tối thiểu 12 phiếu và tỷ lệ 0,35; NMS tâm 4 px/bán kính 2 px, tối đa 100 vòng. Bảng đủ khóa cấu hình ở Phụ lục E.3.

### 3.3.4. Tăng tốc bỏ phiếu

Chỉ đếm đoạn chỉ số có phiếu giúp tăng tốc 2,10–2,40 lần trên ba ảnh đo ngày 24/10/2026; danh sách vòng không đổi. Bảng đo, môi trường và giới hạn so sánh ở Phụ lục E.3.

### 3.3.5. Bản sửa chọn ứng viên theo nhóm bán kính

Các mục trên mô tả bản cài đặt gốc, chọn ứng viên theo tỷ lệ phiếu (`candidate_selection = score`). Với cách này, 100 vòng giữ lại trên STT 13 đều có r ≤ 10 px; nâng trần lên 1.000 vòng cũng chỉ có 8 vòng r > 16 px. Bản sửa thêm cách chọn `radius_balanced` (cấu hình `configs/s201_large_craters.json`). Sau khi sắp xếp, ứng viên được chia nhóm theo octave bán kính $k = \lfloor \log_2(r/5) \rfloor$, tức [5, 10), [10, 20), [20, 40), [40, 80), [80, 160) px. Danh sách mới lấy luân phiên phần tử đầu của từng nhóm, từ nhỏ tới lớn, rồi mới qua NMS và giới hạn 100 vòng. Ngưỡng và phiếu không đổi. Trên STT 13, 100 vòng mới có 29 vòng r > 16 px, lớn nhất 31 px. Kết quả đối chiếu và các ca vẫn bỏ sót ở mục 4.7: cải thiện còn nhỏ, không chứng minh Precision cao. S2-15 chọn `score` trên tập điều chỉnh; `radius_balanced` chỉ bật tường minh khi thử nghiệm.

## 3.4. Cài đặt kiểm tra sáng–tối và phân lớp ứng viên

### 3.4.1. Gắn nhãn sáng–tối

Bước sáng–tối trong `src/postprocessing.py` tự viết bằng NumPy, theo mục 2.3. `resolve_sun` chỉ cho chấm khi hướng nắng có nguồn hoặc được xác nhận, góc tới ≥ 30° và hướng đã kiểm bằng mắt; ảnh khác ghi `not_checked` kèm lý do. `score_one` so điểm trên ảnh gốc với điểm sau trừ mặt phẳng; chỉ gán hợp/ngược khi cả hai cùng vượt ngưỡng theo Bảng 2.1. Bước này **chỉ gắn nhãn, không xóa vòng**.

Giả mã `score_one` và độ phức tạp ở Phụ lục E.4; mỗi đĩa cần ít nhất 30 pixel và đủ 80 % diện tích, vành ngoài cần ít nhất 30 pixel và đủ 50 %.

Hướng nắng sai sẽ đảo ngược mọi kết luận, nên mỗi ảnh có hướng nắng và đủ góc tới được lập một phiếu kiểm tra bằng mắt: mũi tên chỉ về phía Mặt Trời và các hố tham chiếu phóng to, chọn theo số phiếu Hough để tránh lập luận vòng tròn. Ngày 18/10/2026, cả 8 phiếu đều cho kết quả `consistent`.

### 3.4.2. Kết quả trên 26 ảnh

Chỉ 8/26 ảnh được chấm: năm ảnh nắng Tây (STT 8, 9, 13, 14, 18) và ba ảnh nắng Đông (STT 11, 15, 16). Ba ảnh có góc tới dưới 30° và 15 ảnh cắt từ mosaic không có hướng nắng ghi `not_checked`; ứng viên của chúng vẫn được giữ. Trên mỗi ảnh được chấm, 100 ứng viên chia thành 17–31 vòng hợp, 18–27 vòng ngược và 44–56 vòng không rõ. So với vòng đặt ngẫu nhiên, vòng Hough nhiều hơn ở **cả hai** nhãn hợp và ngược, nên điểm sáng–tối chủ yếu cho biết vòng nằm trên vùng có dải sáng–tối rõ, chưa tách được hố thật với ứng viên sai. Hình E.3 minh họa trên STT 13: trong 4 vòng điểm cao nhất chỉ M9 (+0,75) là hố thật, còn 4 vòng điểm thấp nhất (−0,72 đến −0,79) đều là mép bóng hoặc địa hình nhiễu.

### 3.4.3. Phân lớp ứng viên và thử lọc

Hàm `review_candidates` xếp mỗi vòng vào lớp `rim` (vành hố), `shadow_edge` (ranh giới bóng), `texture` (kết cấu) hoặc `unclear`. Vùng bóng lớn là vùng liền khối có độ sáng B3 dưới 0,06 và diện tích từ 1.500 px, tìm bằng hàm `connectedComponentsWithStats` của OpenCV [@opencv_components]. Phần còn lại tự viết; luật dùng độ phủ vành, độ nổi biên và tỷ lệ bóng, không dùng điểm sáng–tối. `apply_filter` mới loại vòng và ghi lý do, đồng thời từ chối tên lớp/nhãn sai. Giả mã, ngưỡng và độ phức tạp ở Phụ lục E.4.

Để đo tác dụng, một thành viên gán nhãn mù (không thấy lớp do máy xếp) cho 100 ứng viên của STT 13, một thành viên khác kiểm chéo: 8 `rim`, 7 `shadow_edge`, 79 `texture`, 6 `unclear`. STT 13 thuộc tập điều chỉnh. Trên 94 vòng có nhãn rõ, lớp `texture` của máy chứa 47/48 vòng kết cấu và không hố thật nào, còn lớp `rim` lẫn 24/33 vòng kết cấu. STT 17 được gán nhãn theo cùng cách (17 `rim`, 66 `texture`, 17 `unclear`). Bảng 3.2 so các cách lọc.

| Cách lọc | STT 13: loại / mất hố thật | STT 13: tỷ lệ hố thật | STT 17: loại / mất hố thật | STT 17: tỷ lệ hố thật |
|---|---:|---:|---:|---:|
| Không lọc | 0 / 0 | 8,5 % | 0 / 0 | 20,5 % |
| **Bỏ `texture`** | **48 / 0** | **17,4 %** | **35 / 0** | **35,4 %** |
| Bỏ `shadow_edge` + `texture` | 61 / 1 | 21,2 % | 35 / 0 | 35,4 % |
| Bỏ sáng–tối `inverted` | 23 / 2 | 8,5 % | không chấm | 20,5 % |

: Bảng 3.2. Kết quả lọc trên ứng viên có nhãn: STT 13 (94 vòng, 8 hố thật) và STT 17 (83 vòng, 17 hố thật).

Bỏ lớp `texture` không mất hố thật nào và tăng gần gấp đôi tỷ lệ hố thật trên cả hai ảnh. Bỏ thêm `shadow_edge` mất hố M7, nằm sát vùng bóng lớn (Hình E.4). Lọc theo nhãn `inverted` có hại: nó loại nhầm M8 và M19, hai vòng nhỏ lệch tâm nằm trong hố thật M32 và M15, chỉ bao lòng hố tối và vách sáng nên bị đảo dấu (mục 3.5). Chuỗi mặc định chưa bật bộ lọc vì mới có hai ảnh có nhãn, cùng là Apollo 16 ở 2 m/px; STT 13 đã dùng để thiết kế luật; và các ngưỡng là giá trị ban đầu.

## 3.5. Lọc vòng tròn trùng

NMS của Hough chỉ gộp hai đỉnh khi tâm lệch ≤ 4 px **và** bán kính lệch ≤ 2 px. Hai dạng trùng lọt qua: vòng nhỏ lồng trong vành thật (STT 13: M8, r = 6, trong M32, r = 9; M19, r = 6, trong M15, r = 10) và hai vòng cùng cỡ lệch tâm (STT 17: M66 và M67, r = 7, tâm cách 5 px). Vòng trùng làm một hố bị đếm hai lần và gây nhãn sáng–tối "ngược" giả. Hàm tự viết `dedupe_circles` coi hai vòng là một hố khi thỏa công thức (3.1):

$$ \frac{d}{R} \le \text{0,75} \quad \text{và} \quad \frac{r}{R} \ge \text{0,5} \qquad (3.1) $$

với R, r là bán kính vòng lớn, vòng nhỏ và d là khoảng cách tâm. Điều kiện thứ hai giữ lại hố nhỏ thật nằm trong hố lớn. Điều kiện thứ nhất giữ lại hai hố cạnh nhau, vì khi hai vành chạm hoặc chồng một phần thì d thường từ R trở lên. Ba cặp trùng thật có d/R = 0,33; 0,45; 0,71, nên ngưỡng 0,5 sẽ bỏ sót M66/M67.

Vòng được duyệt tham lam theo khóa sắp xếp: vòng đủ tin trước (tỷ lệ phiếu q ≥ 0,35 và không thuộc lớp `texture`), rồi vòng lớn hơn, tỷ lệ phiếu, số phiếu, `crater_id`. Vòng trùng với một vòng đã giữ thì bị loại và ghi `duplicate_of`:

```text
dedupe_circles(C):
    với mỗi c ∈ C: q(c) ← phiếu(c) / S_r(c)     S_r: số độ lệch như Hough
    đủ_tin(c) ← q(c) ≥ 0,35 và lớp(c) ≠ texture
    sắp C theo (không đủ_tin, −r, −q, −phiếu, crater_id)
    G ← [], L ← []
    với mỗi c theo thứ tự đó:
        nếu ∃ g ∈ G mà cặp (c, g) thỏa (3.1):
            duplicate_of(c) ← g; thêm c vào L
        ngược lại: thêm c vào G
    trả G (giữ thứ tự đầu vào), L
```

Ví dụ tính tay với cặp M32/M8 trên STT 13. M32 có tâm (52, 372), r = 9, 39 phiếu; M8 có tâm (49, 372), r = 6, 28 phiếu. Ta có d = 3, R = 9, r = 6, nên d/R = 0,33 ≤ 0,75 và r/R = 0,67 ≥ 0,5: hai vòng là một hố. Số độ lệch là 72 với r = 9 và 48 với r = 6, nên q(M32) = 39/72 = 0,542 và q(M8) = 28/48 = 0,583. Cả hai đủ tin; M32 lớn hơn nên đứng trước và được giữ, M8 bị loại với `duplicate_of = M32`. Nếu chọn theo tỷ lệ phiếu thì M8 sẽ được giữ nhầm, vì vòng nhỏ có ít điểm chu vi nên dễ đạt tỷ lệ cao. Bộ 10 ca và độ phức tạp ở Phụ lục E.5.

Bộ kiểm thử `tests/test_dedupe.py` (8 bài) chạy cả 10 ca, kiểm tra thêm việc đảo thứ tự đầu vào không đổi kết quả và hai ngưỡng biên. Trên ảnh thật, STT 13 giảm từ 100 xuống 96 vòng, gộp đúng 2/2 cặp trùng thật; STT 17 giảm từ 100 xuống 97, gộp đúng 1/1 cặp; cả hai không mất hố thật nào (Hình E.5). Bốn vòng bị loại còn lại thuộc các cặp có nhãn người `texture` hoặc `unclear`.

Ngưỡng 0,75 mới chọn theo 3 cặp trên hai ảnh 2 m/px, và hai hố thật chồng gần hết sẽ bị gộp. Lọc trùng không đưa thêm hố mới và chưa được bật trong chuỗi mặc định.

## 3.6. Thống kê hố và mật độ

Mô-đun `src/statistics.py` tự viết bằng Python và NumPy, không dùng thư viện thống kê. Nó có hai đường dùng: hàm `summarize` cho màn hình trò chơi, và các hàm `region_count`, `size_frequency`, `compare_regions` để so mật độ hai vùng.

### 3.6.1. Chọn khoảng bán kính

Dải tìm Hough được tính theo (2.14): cận 5 px tránh vòng quá thô sau rời rạc hóa và Gauss; cận 128 px hạn chế hố bị cắt mất phần lớn vành. Ở 20 m/px, D = 200–4.000 m cho r = 5–100 px.

Để so mật độ, hai vùng phải **cùng tỷ lệ ảnh và cùng khoảng đường kính**; `region_count` và `compare_regions` báo lỗi nếu không thỏa. Nhóm chọn D = 300–2.000 m, tức r = 7,5–50 px ở 20 m/px. Cận dưới 300 m cao hơn dải tìm vì hố có r < 7,5 px khó nhận chắc chắn, và khả năng nhìn thấy hố nhỏ phụ thuộc mạnh vào góc nắng. Cận trên 2.000 m vì hố lớn hơn quá hiếm trong 100–200 km². Một hố được đếm khi D = 2rs thỏa $D_{\min} \le D < D_{\max}$ và tâm nằm trong vùng đếm.

### 3.6.2. Mật độ, khoảng tin cậy và so sánh

Diện tích tính trên **hợp** các vùng đếm hợp lệ trong hệ ảnh nguồn, tránh tính hai lần phần chồng lấp. Mật độ và diện tích theo (2.24).

Khoảng tin cậy 95 % của ρ là khoảng Poisson chính xác [@garwood1936] chia cho A. Với n hố quan sát, cận dưới $\mu_L$ và cận trên $\mu_U$ là nghiệm của:

$$ P_{\mu_L}(X \ge n) = \text{0,025}, \qquad P_{\mu_U}(X \le n) = \text{0,025}, \qquad X \sim \mathrm{Poisson}(\mu) \qquad (3.2) $$

Ở đây $P_\mu$ là xác suất theo phân phối Poisson có trung bình μ. Hai nghiệm được tìm bằng chia đôi 200 lần; kết quả khớp bảng tra, ví dụ n = 0 cho [0; 3,689] và n = 10 cho [4,795; 18,39]. Hai vùng được so bằng kiểm định nhị thức có điều kiện [@przyborowski1940]: nếu hai mật độ bằng nhau thì, với tổng $N_1 + N_2$ cố định,

$$ N_1 \sim \mathrm{Binomial}\left(N_1 + N_2,\ \frac{A_1}{A_1 + A_2}\right) \qquad (3.3) $$

và p-value hai phía là tổng xác suất các kết quả không lớn hơn xác suất của $N_1$ quan sát được. Phân bố kích thước dùng bin √2 bắt đầu tại $D_{\min}$, theo cách trình bày chuẩn [@catwg1979], kèm tần suất tích lũy $N(\ge D)/A$.

Giả mã `region_count`, độ phức tạp và 12 bài kiểm thử thống kê ở Phụ lục E.6.

### 3.6.3. Kết quả so hai vùng

Nhóm so Lunokhod 1 (Mare Imbrium) với Mare Frigoris: cả hai là biển bazan, cùng 20 m/px và cùng chụp lúc Mặt Trời thấp (góc tới của các ảnh thành phần 60–79° và 61–84°). Cặp Van de Graaff – Mare Frigoris dự kiến ban đầu không dùng được: Van de Graaff chụp lúc Mặt Trời cao (27–45°) nên hố nhỏ gần như không thấy, và chênh lệch số đếm sẽ chủ yếu do ánh sáng. Vùng đếm Mare Frigoris chỉ lấy mặt biển, bỏ hố lớn 6–8 km, vùng bóng và dải ghép; các vùng đếm không chồng nhau trên ảnh nguồn.

Mật độ chỉ có nghĩa khi đếm đủ mọi hố trong dải trên toàn diện tích, nên nhóm không dùng nhãn tham chiếu thưa mà đếm tay đầy đủ trên bốn ảnh cắt; một thành viên đếm, một thành viên khác kiểm chéo. Bảng 3.3 và Hình 3.2 cho kết quả.

| Vùng | Diện tích (km²) | N | ρ (hố/km²) | Khoảng tin cậy 95 % |
|---|---:|---:|---:|---|
| Lunokhod 1 | 184,7 | 47 | 0,254 | 0,187–0,338 |
| Mare Frigoris | 99,2 | 32 | 0,322 | 0,221–0,455 |

: Bảng 3.3. Mật độ đếm tay đầy đủ, cùng 20 m/px, D = 300–2.000 m.

Theo các bin 300–424; 424–600; 600–849; 849–1.200; 1.200–2.000 m, số hố của Lunokhod 1 lần lượt là 22; 15; 7; 1; 2; của Mare Frigoris là 26; 4; 2; 0; 0.

![Hình 3.2. Tần suất tích lũy N(≥ D)/km² của hai vùng; dải tô là khoảng tin cậy Poisson 95 %.](../evidence/s2-09/tich_luy.png){width=65%}

Tổng mật độ **không khác nhau có ý nghĩa thống kê**: tỷ số 0,79 và p = 0,35 theo công thức (3.3). Hai đường tích lũy cắt nhau: Mare Frigoris có nhiều hố 300–424 m hơn, còn Lunokhod 1 có nhiều hố từ 424 m trở lên (tỷ số 2,24; p = 0,09). Theo mục 2.5, điều này chỉ gợi ý yếu rằng bề mặt Lunokhod 1 có tuổi tương đối già hơn, chưa đủ để kết luận. Giới hạn chính: số hố nhỏ nên khoảng tin cậy rộng; vùng đếm nhỏ và được chọn để tránh hố lớn, nên không phải mẫu ngẫu nhiên; metadata không có phương vị Mặt Trời, nên khả năng thấy hố nhỏ có thể khác nhau giữa hai vùng; cụm hố liền nhau ở Lunokhod 1 có thể là hố thứ cấp; đếm tay có sai số khoảng ±2 px ở bán kính. Phép so sánh không cho tuổi tuyệt đối.

Trên cùng vùng đếm và dải D, ứng viên máy (Hough mặc định, rồi bỏ lớp `texture` và lọc trùng) chỉ có 11 vòng ở Lunokhod 1 và 0 vòng ở Mare Frigoris, vì Hough chỉ trả vòng có r ≤ 13 px. Mật độ tính từ ứng viên máy vì vậy chưa dùng được (mục 3.7).

### 3.6.4. Thống kê trên màn hình trò chơi

`summarize` trả số vòng, diện tích, mật độ, histogram và giới hạn (hợp đồng ở Phụ lục E.6). Sai hợp đồng thì app báo lỗi và không hiện số. Khi số ứng viên **thô ≥ `max_circles`**, `statistics_presentation_view` ẩn giá trị mật độ bằng dấu “—” và hiện cảnh báo không dùng để so tuổi hay so vùng; số vòng, diện tích và histogram vẫn hiện. Lớp này bỏ đúng câu cảnh báo chạm trần vô điều kiện cũ, giữ các hạn chế khác.

Khi mở ảnh Lunokhod 1 hoặc Mare Frigoris có metadata phù hợp, app hiện riêng bảng so sánh **đếm tay** từ `docs/evidence/s2-09/so_sanh.json` và `data/s209_counts/regions.json`, độc lập với lượt chấm. Ảnh cùng nguồn nhưng ngoài ô đếm có lời giải thích; bảng không đại diện riêng ảnh đang mở. Cách hiển thị khớp `docs/S2-13_TICH_HOP.md` mục 3.2, `src/integration.py` và `app.py`.

## 3.7. Hạn chế của chuỗi phát hiện

**Chạm trần và bỏ sót hố.** Cả 26 ảnh trả 100 ứng viên; trên bốn ảnh rà biên, 80–94 vòng có r = 5–6 px, không vòng nào r > 12 px. STT 17 vẫn bỏ sót cả 10 nhãn dù thay ngưỡng phiếu hoặc bước bán kính (mục 4.6). Chi tiết ảnh hưởng tiền xử lý ở E.2. Chọn theo nhóm bán kính chỉ gỡ một phần nguyên nhân, như kết quả ở mục 4.7.

**Bộ lọc chưa bật, sáng–tối phạm vi hẹp.** Đầu ra mặc định chưa qua phân lớp và lọc trùng. Chỉ 8/26 ảnh được chấm sáng–tối, phiếu hướng nắng do một người kiểm, và STT 16 là ảnh duy nhất có nhãn ngược (27) nhiều hơn hợp (17), chưa đủ căn cứ để kết luận hướng nắng sai.

**Tham số đã chốt, độ nhạy còn thấp.** Ngày 29/10/2026, S2-15 khóa `configs/s215_frozen.json`, đồng bộ với `configs/default.json` cho tuần 3. Các giá trị tiền xử lý và Hough ở Bảng 3.1 và Bảng E.2; chọn `score`, sáng–tối chỉ gắn nhãn, phân lớp và lọc trùng tắt.

Trên đủ 18 ảnh điều chỉnh, cấu hình này tìm lại 10/174 hố đã biết (Recall_known = 5,75%). Nhãn thưa nên không tính Precision/F1 toàn ảnh. Đây là mốc so sánh cố định, chưa phải cấu hình tối ưu. Quyết định giữ `score` dựa trên tuning; không dùng kết quả tập kiểm tra để chọn tham số. Tập kiểm tra đã được xem ở S2-06, nên những lần đánh giá lại phải ghi rõ là đánh giá lặp. Cấu hình, bằng chứng và điều kiện đánh giá lại nằm trong `docs/S2-15_CHOT_THAM_SO.md` và `docs/evidence/s2-15/`.

**Thời gian.** Hough chiếm gần hết thời gian, từ vài giây tới vài chục giây mỗi ảnh tùy máy; tiền xử lý dưới 0,1 s.
