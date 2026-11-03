<!-- S3-12 r5: Tiến chốt Hough/đối sánh; Hưng chốt tiền xử lý, sáng–tối và thống kê. -->

# Chương 2. Cơ sở lý thuyết

## 2.1. Tiền xử lý ảnh và trích biên

**Quy ước.** Ảnh I có M hàng, N cột; x sang phải, y xuống dưới, tâm pixel có tọa độ nguyên. Mặt nạ V = 1 chỉ pixel hợp lệ. Chuỗi đưa ảnh về [0, 1], tăng tương phản, giảm nhiễu rồi trích biên cho Hough.

**Thu nhỏ và chuẩn hóa.** Ô cắt cạnh 512k được thu về 512 bằng trung bình khối k × k; khối có pixel lỗi bị loại:

$$ I'(x,y)=\frac{1}{k^2}\sum_{i,j=0}^{k-1} I(kx+i,ky+j),\qquad V'(x,y)=\bigwedge_{i,j}V(kx+i,ky+j). \qquad (2.1) $$

Hệ số nguyên k tránh nội suy, tỷ lệ mới $s=ks_{nguồn}$. Ảnh ba kênh đỏ/lục/lam $C_R,C_G,C_B$ được đổi sang độ sáng $Y=\text{0,299}C_R+\text{0,587}C_G+\text{0,114}C_B$ theo BT.601 [@itu601]; 16 ảnh nguồn thực tế đều một kênh. Với $P_{lo},P_{hi}$ là phân vị 0,5 % và 99,5 % trên pixel hợp lệ:

$$ I_N=\operatorname{clip}\left(\frac{I-P_{lo}}{P_{hi}-P_{lo}},0,1\right). \qquad (2.2) $$

Phân vị giảm ảnh hưởng điểm bão hòa; nếu hai phân vị bằng nhau nhưng ảnh còn biến thiên thì dùng min–max, còn ảnh phẳng trả 0. Thu hẹp khoảng phân vị làm tăng tương phản nhưng cũng cắt nhiều giá trị cực trị hơn.

**Tăng tương phản.** Cân bằng lược đồ mức xám (histogram) thích nghi có giới hạn tương phản (contrast limited adaptive histogram equalization — CLAHE) chia ảnh thành ô, cắt ngọn histogram, phân bố lại phần bị cắt rồi nội suy song tuyến ánh xạ giữa bốn ô [@zuiderveld1994]. Trong OpenCV, với $N_{ô}$ pixel và $N_{bin}$ mức xám:

$$ \beta=\max\left(1,\left\lfloor\mathrm{clipLimit}\,N_{ô}/N_{bin}\right\rfloor\right). \qquad (2.3) $$

Ngưỡng lớn tăng tương phản và khuếch đại nhiễu. Ô 64 × 64, ảnh 8 bit và clipLimit = 2 cho β = 32; với 16 bit và clipLimit < 32 thì β luôn bằng 1. Vì vậy nhóm dùng CLAHE 8 bit, sau đó làm trơn Gauss; không coi tăng tương phản là khôi phục dữ liệu đã bão hòa.

**Gauss và Sobel.** Đặt bán kính mặt nạ lọc (kernel) $R_g=\lceil3\sigma\rceil$, phép tương quan là $\star$:

$$ h(i)=\frac{e^{-i^2/(2\sigma^2)}}{\sum_{j=-R_g}^{R_g}e^{-j^2/(2\sigma^2)}},\quad i=-R_g,\ldots,R_g;\qquad I_S=(I_N\star h_x)\star h_y. \qquad (2.4) $$

$h_x,h_y$ là cùng kernel h đặt theo hàng/cột. Tính tách được giảm từ $(2R_g+1)^2$ xuống $2(2R_g+1)$ phép nhân/pixel: σ = 1,5 cho 22 thay vì 121. Đệm phản chiếu không lặp pixel mép, tương ứng `BORDER_REFLECT_101`. Tăng σ xóa nhiễu nhưng làm mờ hố nhỏ; nhóm giữ σ dưới $r_{min}/3\approx\text{1,67}$ khi $r_{min}=5$.

$$ K_x=\begin{bmatrix}1\\2\\1\end{bmatrix}\begin{bmatrix}-1&0&1\end{bmatrix},\ K_y=K_x^{\mathsf T};\quad \left\lvert G\right\rvert=\sqrt{g_x^2+g_y^2},\quad\theta=\operatorname{atan2}(g_y,g_x). \qquad (2.5) $$

Ở (2.5), $g_x=I_S\star K_x$, $g_y=I_S\star K_y$. Dấu dương ứng với sáng dần sang phải/xuống dưới. Kernel không chia 8, nên $255\left\lvert G\right\rvert$ cùng thang gradient Canny của OpenCV trên ảnh 8 bit.

**Canny và mặt nạ.** Sau gradient, Canny [@canny1986] triệt tiêu không cực đại (non-maximum suppression — NMS) theo θ rồi nối biên bằng ngưỡng kép. Pixel mạnh vượt $T_{high}$ được giữ; pixel yếu chỉ giữ nếu nối với biên mạnh:

$$ T_{high}=P_{90}(255\left\lvert G\right\rvert),\qquad T_{low}=\text{0,4}T_{high}. \qquad (2.6) $$

Phân vị tính trên vùng hợp lệ đã loại lề; nếu nền phẳng chiếm hơn 90 % thì dùng gradient dương. Ngưỡng cao giảm biên rác nhưng dễ đứt vành. Để loại biên mép, vùng thiếu dữ liệu (nodata) và đường ghép:

$$ E(x,y)=E_C(x,y)\wedge\bigwedge_{\left\lvert i\right\rvert,\left\lvert j\right\rvert\le\ell}V(x+i,y+j),\quad\ell=\max(6,R_g+1). \qquad (2.7) $$

$E_C$ là biên Canny; lề $\ell$ bù ảnh hưởng của Gauss và Sobel, σ = 1,5 cho $\ell=6$. Lề lớn hơn giảm biên giả nhưng mất vành gần mép.

## 2.2. Biến đổi Hough tròn

### 2.2.1. Dẫn xuất và rời rạc hóa

Từ đường tròn $(x-a)^2+(y-b)^2=r^2$, chia hai vế cho $r^2$ được $((x-a)/r)^2+((y-b)/r)^2=1$. Đặt $(x-a)/r=\cos\varphi$, $(y-b)/r=\sin\varphi$ rồi chuyển vế cho các tâm khả dĩ [@duda1972]:

$$ a=x-r\cos\varphi,\qquad b=y-r\sin\varphi,\qquad0\le\varphi<2\pi. \qquad (2.8) $$

Với r cố định, mỗi điểm biên bỏ phiếu trên một vòng tâm khả dĩ; các điểm cùng vành hội tụ tại tâm thật. Bảng tích lũy (accumulator) $A_r[b,a]$ có M × N ô; giữ lần lượt từng r thay vì cả khối ba chiều. Hình 2.1 minh họa sự hội tụ.

![Hình 2.1. Hough trên ba đĩa giả lập: ảnh vào, biên/vòng tìm được và tích lũy tại r = 32 px. Đỉnh ở tâm (160, 180); một đĩa bị cắt mép.](../images/hough_synthetic_demo.png){width=95%}

Với T góc cách nhau Δφ, làm tròn độ lệch trước rồi khử trùng:

$$ \mathcal D_r=\operatorname{unique}\{(\operatorname{rint}(r\cos\varphi_j),\operatorname{rint}(r\sin\varphi_j))\}_{j=0}^{T-1}. \qquad (2.9) $$

$$ A_r[b,a]=\sum_{E(x,y)=1}\sum_{(d_x,d_y)\in\mathcal D_r}\mathbf1[a=x-d_x\wedge b=y-d_y],\quad0\le a<N,\ 0\le b<M. \qquad (2.10) $$

`rint` làm tròn gần nhất, hòa nửa về số chẵn. Khử trùng tránh một điểm biên bỏ nhiều phiếu vào cùng tâm. Với bước 1°, số độ lệch $S_r=\left\lvert \mathcal D_r\right\rvert$ là 40, 80, 144, 224 khi r = 5, 10, 20, 32, không luôn bằng T = 360. Chỉ số phẳng $bN+a$ được đếm bằng `bincount`; vành có thể cắt mép nhưng tâm phải trong ảnh.

### 2.2.2. Gradient, chọn đỉnh và NMS

Gradient hình học của $(x-a)^2+(y-b)^2-r^2$ là $(2(x-a),2(y-b))$, vuông góc tiếp tuyến. Nếu gradient ảnh gần pháp tuyến vành, vector $\mathbf n=(\cos\theta,\sin\theta)$ cho hai tâm:

$$ (a,b)=(x,y)\mp\operatorname{rint}(r\mathbf n). \qquad (2.11) $$

Hai dấu ứng với hai chiều sáng–tối; θ đo tại điểm biên, khác φ đang quét. Cách này chỉ bỏ tối đa hai phiếu/bán kính, dùng $S_r=\lceil2\pi r\rceil$, nhưng nhạy với nhiễu và mép bóng. Nhóm giữ bỏ phiếu toàn vòng làm mặc định, gradient là phương án đối chiếu [@yuen1990].

Với số phiếu tối thiểu $v_{min}$ và tỷ lệ hỗ trợ κ:

$$ \tau_r=\max(v_{min},\lceil\kappa S_r\rceil),\qquad q=A_r[b,a]/S_r. \qquad (2.12) $$

Ô vượt ngưỡng và cực đại 3 × 3 là đỉnh; hòa phiếu ưu tiên trên rồi trái. Tăng ngưỡng giảm ứng viên nhưng có thể mất vành yếu. q dùng xếp hạng, không phải xác suất; nhánh gradient có thể cho q > 1. Các đỉnh xếp theo (−q, −phiếu, y, x, r), tùy chọn xen kẽ nhóm bán kính trước NMS. Một ứng viên bị loại nếu gần vòng đã giữ j ở cả tâm và bán kính:

$$ (a-a_j)^2+(b-b_j)^2\le d_{NMS}^2\quad\wedge\quad\left\lvert r-r_j\right\rvert\le\delta_{NMS}. \qquad (2.13) $$

Dừng khi đủ L vòng. Với ngưỡng tâm 4 px/bán kính 2 px, vòng (352, 311, 21) bị vòng (350, 310, 20) loại; vòng đồng tâm r = 24 vẫn giữ. NMS này không giải quyết mọi vòng lồng nhau; tăng ngưỡng có thể gộp nhầm hố cạnh nhau.

### 2.2.3. Ví dụ số 5 × 5 từng bước

**Bước 1 — Đầu vào.** Đặt bốn điểm $P_1=(2,1)$, $P_2=(1,2)$, $P_3=(3,2)$, $P_4=(2,3)$ trên ảnh biên E dưới đây, r = 1. Ví dụ $P_1$ cách (2,2) một pixel vì $(2-2)^2+(1-2)^2=1$.

**Bước 2 — Độ lệch.** Với 360 góc bước 1°, (2.9) cho tám độ lệch $(\pm1,\pm1),(\pm1,0),(0,\pm1)$; $S_1=8$. Độ lệch chéo dài $\sqrt2$ là hệ quả lượng tử hóa, không phải điểm trên đường tròn liên tục r = 1.

**Bước 3 — Bỏ phiếu.** Mỗi điểm cộng 1 tại tám tâm $(x-d_x,y-d_y)$; cả 32 tâm trong ảnh. Tại (2,2), P1 dùng (0,−1), P2 dùng (−1,0), P3 dùng (1,0), P4 dùng (0,1); chỉ số phẳng đều là $2\cdot5+2=12$. Các ma trận A1–A4 ghi sau từng điểm:

```text
E             A1            A2            A3            A4
0 0 0 0 0     0 1 1 1 0     0 1 1 1 0     0 1 1 1 0     0 1 1 1 0
0 0 1 0 0     0 1 0 1 0     1 2 1 1 0     1 2 2 2 1     1 2 2 2 1
0 1 0 1 0     0 1 1 1 0     1 1 2 1 0     1 1 3 1 1     1 2 4 2 1
0 0 1 0 0     0 0 0 0 0     1 1 1 0 0     1 1 2 1 1     1 2 2 2 1
0 0 0 0 0     0 0 0 0 0     0 0 0 0 0     0 0 0 0 0     0 1 1 1 0
```

**Bước 4 — Lấy đỉnh.** Với $v_{min}=3$, κ = 0,35, ngưỡng là $\max(3,\lceil2,8\rceil)=3$. Chỉ A4[2,2] = 4 vượt ngưỡng và lớn hơn tám ô kề, nên tâm (2,2), r = 1, q = 4/8 = 0,5. Nếu dùng $v_{min}=12$ thì không có đỉnh. Gradient lý tưởng cho 4 phiếu tại tâm, một phiếu ở mỗi ô (2,0), (0,2), (4,2), (2,4), q = $4/\lceil2\pi\rceil=4/7$.

Ví dụ **đã kiểm chứng bằng NumPy**, dùng chính các hàm Hough nội bộ với lô 1, 2 và 256; mã và lệnh ở Phụ lục B. r = 1 chỉ dùng minh họa, không đổi hợp đồng đầu vào 512 × 512, r ≥ 5.

### 2.2.4. Tham số, lượng tử hóa và chi phí

Dải đường kính $[D_{min},D_{max}]$ và tỷ lệ s quyết định:

$$ r_{min}=\max\left(5,\left\lceil\frac{D_{min}}{2s}\right\rceil\right),\qquad r_{max}=\min\left(128,\left\lfloor\frac{D_{max}}{2s}\right\rfloor\right). \qquad (2.14) $$

Dải rỗng báo lỗi. Bước Δr gây sai số tới Δr/2; dải [12,29] bước 4 quét 12,16,20,24,28. Sai r làm phiếu rải quanh tâm thật thay vì hội tụ. Bước góc thưa tăng khoảng cách cung $r\Delta\varphi$; tâm nguyên có sai số tối đa 0,5 px mỗi trục (0,71 px theo đường chéo). OpenCV `HOUGH_GRADIENT` tìm tâm trước, ước r sau, trả tâm ô (chỉ số + 0,5)dp; với dp = 1 phải trừ 0,5 trước đối chiếu, dp = 2 không có bù hằng số [@opencv_hough_source].

Gọi $E_n$ là số điểm biên, $R_n$ số bán kính, $S_{max}=\max_r S_r\le T$ số độ lệch lớn nhất, B cỡ lô, K tổng đỉnh, L trần vòng và J tổng độ dài các đoạn `bincount`. Thời gian toàn vòng:

$$ O\big(R_n(E_nS_{max}+MN+T\log T)+J+K\log K+KL\big),\quad J\le R_n\lceil E_n/B\rceil MN. \qquad (2.15) $$

Bỏ phiếu gradient giảm hạng $E_nS_{max}$ còn $E_n$ và không đếm theo lô. Bộ nhớ phụ:

$$ O(MN+BS_{max}+K+E_n+T)\ \text{toàn vòng};\quad O(MN+K+E_n+T)\ \text{gradient}. \qquad (2.16) $$

Một mặt phẳng 512 × 512 int32 tốn 1 MiB; giữ cả 124 bán kính tốn 124 MiB. Chương 3 nêu giả mã và chi phí của các khối còn lại. Hai ví dụ lượng tử hóa/số phiếu được giữ nguyên ở mục E.9 của tài liệu bổ sung (liên kết Phụ lục E); phép đo tăng tốc lịch sử ở E.3.

## 2.3. Kiểm tra sáng–tối theo hướng nắng

Hough không phân biệt hố lõm với gò hoặc biên tình cờ gần tròn. Khi nắng xiên, thành hố phía gần Mặt Trời thường tối, phía xa sáng; gò cho chiều ngược lại. Với phương vị nắng $A_{sun}$ theo chiều kim đồng hồ từ Bắc và hướng Bắc trong ảnh $\alpha_N$, đặt $\psi=A_{sun}+\alpha_N$:

$$ \mathbf u=(\sin\psi,-\cos\psi). \qquad (2.17) $$

Ví dụ ψ = 270° cho nắng Tây, $\mathbf u=(-1,0)$. Trong đĩa tâm c, bán kính r, đặt vị trí theo chiều xa Mặt Trời t và hệ số tương quan Pearson S:

$$ t(\mathbf p)=-\frac{(\mathbf p-\mathbf c)\cdot\mathbf u}{r},\qquad S=\frac{\sum(I_i-\overline{I})(t_i-\overline{t})}{\sqrt{\sum(I_i-\overline{I})^2}\sqrt{\sum(t_i-\overline{t})^2}}. \qquad (2.18) $$

S dương hợp chiều hố, S âm hợp gò/vòng sai; cộng hằng hoặc nhân độ sáng với hệ số dương không đổi S. Để loại độ dốc nền, khớp mặt phẳng trên vành $1,3r<\left\lvert \mathbf p-\mathbf c\right\rvert\le2r$ rồi trừ trước khi tính S:

$$ \min_{\beta_0,\beta_1,\beta_2}\sum_{\mathbf p\in\text{vành ngoài}}\left[I(\mathbf p)-\beta_0-\beta_1\frac{x-x_c}{r}-\beta_2\frac{y-y_c}{r}\right]^2. \qquad (2.19) $$

Vành ngoài tránh vành nổi; ba hệ số mô tả mức nền và hai độ dốc. Trên giả lập, độ dốc 0,001/pixel cho S = +0,48 hoặc −0,50 dù không có hố; trừ dốc còn −0,03. Nhưng mép bóng có thể làm điểm sau trừ thành +0,90 trong khi điểm gốc −0,01. Vì thế tính cả $S_{raw}$ trên ảnh gốc và S sau trừ; Bảng 2.1 yêu cầu cùng nhãn.

| Điều kiện | Nhãn |
|---|---|
| $S\ge\tau$ và $S_{raw}\ge\tau$ | hợp |
| $S\le-\tau$ và $S_{raw}\le-\tau$ | ngược |
| Các trường hợp còn lại | không rõ |

: Bảng 2.1. Phân loại sáng–tối; nhãn hợp chưa chứng minh là hố thật.

Ngưỡng τ = 0,15 khi có phương vị đo, 0,25 khi chỉ biết Đông/Tây. Nếu hướng lệch $\Delta_s$ thì tín hiệu giảm khoảng $\cos\Delta_s$; ngưỡng cao hơn làm kết luận bảo thủ. Chỉ chấm khi nắng có nguồn/xác nhận, biết hướng Bắc, góc tới ≥30° và đã kiểm hướng bằng mắt trên hố tham chiếu không dùng để đánh giá. Sai hướng đảo dấu; ảnh không đủ điều kiện ghi `not_checked` và giữ ứng viên. Cảnh giả lập nắng Tây 70° cho hố/gò S = +0,98/−0,98; hình và bằng chứng ở Phụ lục E.

## 2.4. Đối sánh một–một và độ đo

Dự đoán tâm $\mathbf c_i$ ghép với nhãn tâm $\mathbf q_j$, bán kính $r_j^{ref}$ khi:

$$ \delta_{ij}=\left\lVert \mathbf c_i-\mathbf q_j\right\rVert/r_j^{ref}\le\text{0,5}. \qquad (2.20) $$

Ngưỡng 0,5 lấy từ đề; tăng ngưỡng tăng cơ hội ghép nhầm. Bán kính dự đoán không là điều kiện ghép nhưng phải báo sai lệch. Mỗi vòng/nhãn dùng tối đa một lần. Với $x_{ij}=1$ chỉ ở cặp hợp lệ:

$$ \max\sum x_{ij},\quad\text{sau đó}\quad\min\sum\delta_{ij}x_{ij};\qquad\sum_jx_{ij}\le1,\quad\sum_ix_{ij}\le1. \qquad (2.21) $$

Ghép tham lam có thể mất cặp: dự đoán 1 gần nhãn 1 nhưng cũng ghép được nhãn 2, còn dự đoán 2 chỉ ghép nhãn 1. Hungary [@kuhn1955] giải bài toán trên ma trận $n_1\times m_1$ sau khi bỏ hàng/cột không có cặp. Phạt cặp sai $(\nu+1)(0,5+1)$ với $\nu=\min(n_1,m_1)$ lớn hơn tổng chi phí mọi ν cặp hợp lệ, nên ưu tiên số cặp trước khoảng cách. Độ phức tạp $O(n_1^2m_1)$ khi $n_1\le m_1$.

Gọi TP là số cặp, $FP=N_{dự\,đoán}-TP$, $FN=N_{nhãn}-TP$. Với nhãn đầy đủ:

$$ Precision=\frac{TP}{TP+FP},\qquad Recall=\frac{TP}{TP+FN},\qquad F_1=\frac{2TP}{N_{dự\,đoán}+N_{nhãn}}. \qquad (2.22) $$

Độ chính xác dương tính (Precision) cần biết vòng nào sai. Nhãn thưa không cho FP vì vòng không khớp vẫn có thể là hố chưa gán. Nhóm chỉ báo độ bao phủ trên nhãn đã biết:

$$ Recall_{known}=TP_{known}/N_{known},\qquad FN_{known}=N_{known}-TP_{known}. \qquad (2.23) $$

Không tính nhãn `uncertain`; ghép nhãn chắc chắn trước rồi bỏ qua dự đoán rơi vào nhãn chưa chắc. Recall_known luôn kèm mẫu số và dải kích thước; vòng người chơi ngoài nhãn thưa không bị coi là sai.

## 2.5. Mật độ, phân bố và bất định

Với đường kính D = 2rs và $N_D$ hố trong dải $D_{min}\le D<D_{max}$:

$$ \rho=N_D/A,\qquad A=N_{px\,hợp\,lệ}s^2/10^6\ (\mathrm{km}^2). \qquad (2.24) $$

Diện tích lấy hợp vùng đếm trên ảnh nguồn để tránh lặp. Hai vùng phải cùng s và dải D. Phân bố dùng khoảng lớp (bin) tăng theo $\sqrt2$ và tần suất tích lũy $N(\ge D)/A$ [@catwg1979]. Khoảng tin cậy (confidence interval) 95 % của ρ là cận Poisson chính xác chia cho A [@garwood1936]:

$$ P_{\mu_L}(X\ge n)=\text{0,025},\quad P_{\mu_U}(X\le n)=\text{0,025},\quad X\sim Poisson(\mu). \qquad (2.25) $$

n là số hố, X là biến đếm, μ là kỳ vọng và $P_\mu$ chỉ xác suất Poisson; khi n = 0 đặt cận dưới bằng 0. Hai vùng có cùng mật độ thì, điều kiện trên tổng $N_1+N_2$, số hố vùng 1 có phân phối [@przyborowski1940]:

$$ N_1\sim Binomial\left(N_1+N_2,\frac{A_1}{A_1+A_2}\right). \qquad (2.26) $$

Giá trị p hai phía cộng xác suất các kết quả không lớn hơn xác suất quan sát. Nhiều hố hơn làm khoảng bất định hẹp hơn; diện tích, nhãn thiếu và điều kiện nắng đều ảnh hưởng mật độ. Chỉ trong điều kiện quan sát tương đồng, mật độ cao mới gợi ý tuổi tương đối [@neukum2001]. Hố thứ cấp, ô chồng lấp, lựa chọn vùng và đếm nhầm có thể phá giả định; kết quả ở đây không cho tuổi tuyệt đối.
