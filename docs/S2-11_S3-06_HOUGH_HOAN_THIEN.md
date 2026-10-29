# S2-11 / S3-06 — Hough: lý thuyết, cài đặt và kiểm chứng

Bản hoàn thiện ngày 27/10/2026, phục vụ phần Hough Chương 2/3.
Người phụ trách theo phân công: Nguyễn Mạnh Tiến; hỗ trợ soạn/cài đặt bằng Codex.
Kế thừa [dẫn xuất S1-15](S1-15_LY_THUYET_HOUGH.md),
[ví dụ S1-12](S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md),
[danh mục 12 nguồn](TAI_LIEU_THAM_KHAO_HOUGH.md).

## 1. Dẫn xuất Hough tròn

Ý tưởng Hough chuyển tìm đường cong sang tìm đỉnh trong không gian tham số [1].
Từ $(x-a)^2+(y-b)^2=r^2$, đặt $(x-a,y-b)=r(\cos\varphi,\sin\varphi)$:

$$a=x-r\cos\varphi,\qquad b=y-r\sin\varphi.$$

Tập offset rời rạc là $D_r=\mathrm{unique}\{(\mathrm{rint}(r\cos\varphi_k),
\mathrm{rint}(r\sin\varphi_k))\}$; góc lấy từ 0 đến dưới 360°.
`rint` làm tròn gần nhất, hòa nửa về số chẵn [8]. Làm tròn offset trước khi trừ khỏi
pixel nguyên; khử offset trùng tránh cộng phiếu nhiều lần chỉ vì góc cùng rơi vào một pixel.
Trong mã, accumulator có thứ tự hàng/cột: $A_r[b,a]$.

$$A_r[b,a]=\sum_{(x,y)\in E}\sum_{(d_x,d_y)\in D_r}
\mathbf1[a=x-d_x\land b=y-d_y].$$

Chỉ cộng tâm trong ảnh. Với gradient $\theta=\operatorname{atan2}(g_y,g_x)$,
pháp tuyến vành cho hai giả thuyết $(a,b)=(x,y)\pm r(\cos\theta,\sin\theta)$
vì chưa biết phía sáng/tối. Nguồn [2] cung cấp bối cảnh các biến thể;
dẫn xuất trên giải thích mã dự án, không trích kết quả từ phần toàn văn chưa đọc.

Ngưỡng $\tau_r=\max(v_{min},\lceil q S_r\rceil)$, với $S_r=|D_r|$ cho full-circle,
$S_r=\lceil2\pi r\rceil$ cho gradient. Điểm $A_r/S_r$ chỉ là hỗ trợ hình học;
`confidence=null`. Cực đại 3×3 hòa phiếu ưu tiên hàng trên rồi cột trái.
Canny [3,10] tạo đầu vào biên; NMS của biên khác NMS của vòng tròn.

Từ đường kính vật lý D và độ phân giải s:
$r_{min}=\max(5,\lceil D_{min}/(2s)\rceil)$,
$r_{max}=\min(128,\lfloor D_{max}/(2s)\rfloor)$.
Dải chạy là giao với cấu hình; dải rỗng báo lỗi. Lưới 12..29 bước 4 chỉ quét 12,16,20,24,28.

## 2. Ví dụ nhỏ tái tạo được

Bốn điểm $(2,1),(1,2),(3,2),(2,3)$ trên ảnh 5×5, r=1, có tám offset duy nhất.
Tính tay và NumPy với lô 1/2/256 đều cho:

```text
0 1 1 1 0
1 2 2 2 1
1 2 4 2 1
1 2 2 2 1
0 1 1 1 0
```

Với min_votes=3, q=0,35, ngưỡng là 3; tâm (2,2) nhận 4 phiếu, score=0,5.
Giữ min_votes=12 thì không có đỉnh. Gradient: tâm nhận 4 phiếu, bốn ô ngoài mỗi ô 1 phiếu,
$S_r=\lceil2\pi\rceil=7$. Ví dụ dùng hàm nội bộ, không gọi API 512×512 với r=1.

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_hough_examples.py --tiny-only
```

Trace từng phiếu nằm trong `tiny_example` của báo cáo S2-06/S3-02.

## 3. Giả mã và ánh xạ sang cài đặt

```text
kiểm tra edges, theta, cấu hình; lấy tọa độ pixel biên
với mỗi r trong lưới:
    full_circle: _circle_offsets → _accumulate
    gradient: _accumulate_gradient, bỏ phiếu hai dấu
    tính support_size, ngưỡng → _local_peaks
    lưu tuple (score, votes, y, x, r)
xếp score giảm, votes giảm, y/x/r tăng
nếu candidate_selection = radius_balanced:
    chia nhóm floor(log2(r/5))
    lấy luân phiên đầu mỗi nhóm không rỗng; trong nhóm giữ thứ tự score
duyệt ứng viên, NMS theo cả khoảng tâm và khoảng bán kính
    bỏ nếu d_tâm ≤ nms_center_px và |r-r_đã_giữ| ≤ nms_radius_px
    dừng khi đủ max_circles
trả M1..Mn, x/y/r float, votes int, confidence null
```

Các nhóm bán kính là [5,10), [10,20), [20,40), [40,80), [80,160), giới hạn thực vẫn 128.
`radius_balanced` là chế độ thử nghiệm bật trong `configs/s201_large_craters.json`,
nhằm giảm tình trạng vòng nhỏ chiếm hết ngân sách đầu ra. Mặc định mã và game vẫn là `score`;
[S2-15](S2-15_CHOT_THAM_SO.md) đã chốt giữ score cho game/tuần 3 ngày 29/10/2026.
Nhóm không có đỉnh đủ ngưỡng không được thêm ứng viên để đủ số lượng.
Nếu ngân sách ít hơn số nhóm, thứ tự nhóm nhỏ trước vẫn có thể bỏ nhóm lớn.
Chế độ này có thể giảm Recall hố nhỏ; không bảo đảm mọi hố lớn được tìm thấy.
`candidate_selection=score` giữ thứ tự mặc định/lịch sử, cũng được ghi trong cấu hình benchmark cũ.

`_accumulate` dùng `bincount` [9] trên đoạn chỉ số có phiếu mỗi lô, rồi cộng đúng lát accumulator.
NMS Hough chỉ loại đỉnh gần nhau. S2-05 là lọc trùng hình học riêng; có thể xóa vòng thật gần nhau
nếu hình học quá giống. Kết quả trước/sau được lưu riêng, chưa bật lọc trùng trong pipeline game.

## 4. Phân tích thời gian và bộ nhớ

Đặt N=H×W, E=số pixel biên, R=số mức r, T=số góc mẫu, S=max số offset duy nhất,
B=kích thước lô, K=tổng số đỉnh, L=max_circles. I là tổng chiều dài histogram theo đoạn
qua mọi lô và mọi bán kính. Full-circle có chi phí
$O(R(E S+N+T\log T)+I+K\log K+KL)$: bỏ phiếu ES, lấy đỉnh N, unique T log T,
sort K log K và NMS tối đa KL. Trường hợp phiếu phủ rộng,
$I\le R\lceil E/B\rceil N$; tối ưu đoạn không cải thiện mọi trường hợp xấu nhất.
Gradient có chi phí $O(R(E+N)+K\log K+KL)$; bỏ phiếu không phụ thuộc mẫu góc.
Luân phiên nhóm thêm O(K) thời gian và O(K) tham chiếu.

Bộ nhớ full-circle $O(N+BS+K+E+T)$, gradient $O(N+K+E+T)$ trong mã hiện tại.
Không giữ accumulator R×H×W nhưng K vẫn có thể lớn trên ảnh nhiễu.
Các số thời gian phải đọc cùng điều kiện máy; không suy hệ số tăng tốc từ công thức.

## 5. Đối chiếu và giới hạn đánh giá

OpenCV Hough gradient tìm tâm rồi tìm bán kính [4]; khác cách quét từng r.
Cùng ảnh xám làm trơn và dải r không đồng nghĩa cùng Canny, ngưỡng hay NMS.
Nguồn mã [5] là tag 4.14.0 lịch sử, không chứng minh nội bộ OpenCV 5.0.0 hiện cài giống hệt.
Nguồn scikit-image [6,7] là tham khảo API/ví dụ; thực nghiệm này đối chiếu OpenCV.
Thời gian NumPy chỉ gồm Hough; OpenCV gồm phát hiện biên nội bộ, nên không xếp hạng tốc độ toàn pipeline.
Ngân sách đầu ra khác nhau: NumPy tối đa 100, OpenCV không cắt 100; phải đọc cả số ứng viên.

Nhãn thưa chỉ cho TP_known, FN_known và Recall_known; FP/Precision/F1 toàn ảnh chưa xác định.
Ghép một–một theo tâm lệch ≤0,5 r_ref, ưu tiên số cặp tối đa rồi tổng khoảng cách chuẩn hóa nhỏ nhất.
Không dùng sai số bán kính làm điều kiện ghép; một vòng sai bán kính vẫn có thể là TP,
nên phải đọc cả `radius_error_px`. Ưu tiên nhãn chắc chắn trước, rồi bỏ qua mọi dự đoán
nằm trong vùng uncertain. LROC [11] và NASA [12] là nguồn dữ liệu/bối cảnh, không thay nhãn.

## 6. Nguồn và minh chứng

Mã [1]–[12] khớp [danh mục nguồn](TAI_LIEU_THAM_KHAO_HOUGH.md).
Ngày 27/10/2026 đã đối chiếu cả ba DOI qua Crossref, khớp tiêu đề, tác giả, tập/số/trang;
xem [metadata gốc](evidence/s3-06/doi_verification.json).
Các trang chính thức [4]–[12] đã mở lại; mức kiểm tra ghi trong
[source_checks.json](evidence/s3-06/source_checks.json).
Đây là xác minh định danh và tài liệu kỹ thuật, không tuyên bố đã đọc toàn văn ba bài DOI.
Dẫn xuất, giả mã và độ phức tạp trên được đối chiếu trực tiếp mã repo.
Kết quả thực chạy và hướng dẫn tái tạo: [S2-06/S3-02](S2-06_S3-02_KIEM_CHUNG.md).
