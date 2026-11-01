::: {custom-style="Cover Strong"}
TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI

KHOA CÔNG NGHỆ THÔNG TIN
:::

::: {custom-style="Cover"}
Học phần: Xử lý ảnh — Lớp: Công nghệ thông tin 2 – K64
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="900"/></w:pPr></w:p>
```

::: {custom-style="Cover Title"}
BÁO CÁO BÀI TẬP LỚN
:::

::: {custom-style="Cover Big"}
PHÁT HIỆN HỐ VA CHẠM TRÊN ẢNH MẶT TRĂNG BẰNG BIẾN ĐỔI HOUGH VÀ TRÒ CHƠI STEM CHO HỌC SINH
:::

::: {custom-style="Cover"}
Đề tài NASA 24: Tìm hố va chạm và trò chơi STEM — Nhóm 2
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="600"/></w:pPr></w:p>
```

::: {custom-style="Cover"}
Giảng viên hướng dẫn: Cao Thị Luyên

Sinh viên thực hiện:

Bùi Hải Đức — 231230747 (nhóm trưởng)

Nguyễn Mạnh Tiến — 231230923

Đinh Quang Hưng — 231230804

Hoàng Quốc Anh — 231230703
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="900"/></w:pPr></w:p>
```

::: {custom-style="Cover"}
Hà Nội, tháng 11 năm 2026
:::

# Lời cam đoan và phân công

**Dự thảo chờ cả nhóm ký.** Nhóm cam đoan số liệu có nguồn, phân biệt kết quả đã kiểm với việc chưa làm; ghi nguồn mã, hình và dữ liệu, khai báo AI ở Phụ lục D. Mỗi người chịu trách nhiệm giải thích phần mình. Nội dung chỉ được xác nhận sau khi cả nhóm ký.

Bảng M.1 là khung phân công theo Quy định BTL Xử lý ảnh [@quydinh_btl]. Tỷ lệ và chữ ký để trống, do thành viên thống nhất; không suy tỷ lệ từ số commit.

| Thành viên | Công việc | File mã chính | Mục viết | Tỷ lệ (%) | Chữ ký |
|---|---|---|---|---|---|
| Bùi Hải Đức | Trò chơi, tích hợp, ghép báo cáo | `app.py`, `src/matching.py`, `src/scoring.py`, `src/integration.py`, `src/crater_canvas/` | Ch1, 3.1, 3.7, Ch5 | ____ | ____ |
| Nguyễn Mạnh Tiến | Hough, kiểm chứng, đánh giá | `src/hough.py`, `src/evaluation.py`, `scripts/evaluate_hough.py` | 2.2, 2.4, 3.3, 3.8, 4.7 | ____ | ____ |
| Đinh Quang Hưng | Tiền xử lý, sáng–tối, thống kê | `src/preprocessing.py`, `src/postprocessing.py`, `src/statistics.py` | 2.1, 2.3, 2.5, 3.2, 3.4–3.6, 4.8 | ____ | ____ |
| Hoàng Quốc Anh | Dữ liệu, nhãn, thí nghiệm, thẻ | `scripts/label_craters.py`, `scripts/s207_experiments.py`, `src/science_cards.py` | 4.1–4.6, 4.9–4.10 | ____ | ____ |

: Bảng M.1. Phân công để cả nhóm xác nhận tỷ lệ và ký.

[CHỜ cả nhóm: thống nhất tỷ lệ tổng 100 % và ký cam đoan/Bảng M.1; đánh giá chéo ở Phụ lục D.]

```{=openxml}
<w:p><w:pPr><w:pStyle w:val="CoverTitle"/><w:pageBreakBefore/></w:pPr><w:r><w:t>MỤC LỤC</w:t></w:r></w:p>
```

```{=openxml}
<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/><w:docPartUnique/></w:docPartObj></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \o "1-2" \h \z \u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Mở bằng Word và nhấn F9 để cập nhật mục lục.</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>
```

# Danh mục hình và bảng

<!-- REPORT_LISTS -->

# Danh mục ký hiệu và chữ viết tắt

Bảng M.2 liệt kê ký hiệu; nghĩa cục bộ được giải thích tại công thức.

| Ký hiệu | Ý nghĩa |
|---|---|
| $I, I_N, I_S, E, V$ | Ảnh, ảnh chuẩn hóa, ảnh làm trơn, ảnh biên, mặt nạ hợp lệ |
| $M, N; x, y; a, b; r$ | Số hàng/cột; tọa độ pixel; tâm Hough; bán kính (px) |
| $s, D, k$ | Tỷ lệ (m/px), đường kính (m), hệ số thu nhỏ |
| $P_{lo}, P_{hi}, \sigma, R_g$ | Phân vị thấp/cao; độ lệch chuẩn và bán kính mặt nạ lọc Gauss |
| $g_x,g_y,\left\lvert G\right\rvert,\theta;\varphi$ | Gradient theo hai trục, độ lớn/hướng; góc quét Hough |
| $A_r,\mathcal D_r,S_r,T,R_n$ | Tích lũy, độ lệch vòng, số độ lệch, số góc, số bán kính |
| $v_{min},\kappa,\tau_r,q,L$ | Phiếu/tỷ lệ tối thiểu, ngưỡng, điểm hỗ trợ, trần số vòng |
| $B,K,J,E_n$ | Cỡ lô, số đỉnh, tổng đoạn đếm, số biên |
| $r_{min/max},D_{min/max}$; $\Delta r,\Delta\varphi$; $d_{NMS},\delta_{NMS}$ | Cận bán kính/đường kính, bước bán kính/góc, ngưỡng NMS tâm/r |
| $A_{sun},\alpha_N,\mathbf u,t,S,S_{raw},\tau$ | Góc nắng/Bắc, vector nắng, tọa độ; điểm sáng–tối và ngưỡng |
| $\beta_0,\beta_1,\beta_2;\beta$ | Hệ số mặt phẳng độ sáng; ngưỡng cắt histogram |
| $\mathbf c_i,\mathbf q_j,r_j^{ref},\delta_{ij},x_{ij}$ | Tâm dự đoán/nhãn, r nhãn, lệch tâm chuẩn hóa, biến ghép |
| TP, FP, FN; $N_{known}$ | Số khớp, dương tính giả, bỏ sót; số nhãn chắc chắn |
| $\rho,A,N_D;\mu_L,\mu_U,p$ | Mật độ, diện tích km², số hố; cận Poisson, xác suất kiểm định |
| $d,R,r;n,b_h;c,P_U$ | Lệch tâm, r lớn/nhỏ; số vòng/bin/ô, diện tích khung bao (px) |
| $n_p,n_q,n_1,m_1;x_0,y_0$ | Số dự đoán/nhãn trước/sau rút ma trận ghép; góc ô cắt |
| $u,v,L,T,W,z,v_x,v_y$ | Con trỏ, góc bản đồ, bề rộng, mức phóng, góc vùng xem |
| $e_{max},\mathrm{MSE};R_i,\overline{R},s_R,m$ | Sai số lớn nhất/MSE; Recall từng ảnh, trung bình, SD mẫu, số ảnh |

: Bảng M.2. Ký hiệu toán học.

LRO (Lunar Reconnaissance Orbiter), LROC (LRO Camera); NAC/WAC (Narrow/Wide Angle Camera); PDS (Planetary Data System); CTX/HiRISE: camera Sao Hỏa. CLAHE (Contrast Limited Adaptive Histogram Equalization); NMS (Non-Maximum Suppression); STEM (Science, Technology, Engineering, Mathematics). JSON/CSV: định dạng văn bản; CI (Continuous Integration); DOI (Digital Object Identifier). $\mathrm{Recall}_{known}$ chỉ đo tỷ lệ tìm lại nhãn đã biết; SD là độ lệch chuẩn.
