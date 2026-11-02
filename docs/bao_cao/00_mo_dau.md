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

# Danh mục ký hiệu

| Ký hiệu và nghĩa (theo thứ tự trong từng nhóm) |
|---|
| **Ảnh và hình học.** $I,I',I_N,I_S$; $V,V'$; $E,E_C$: Ảnh gốc/thu/chuẩn hóa/trơn; mặt nạ gốc/thu; biên B8/Canny. $Y,C_R,C_G,C_B$: Độ sáng, kênh đỏ/lục/lam. $M,N$; $x,y$; $a,b$; $r,R$: Hàng/cột; pixel; tâm Hough; bán kính/lớn hơn (px); $i,j$: chỉ số. $s,s_{nguồn},D,k$; $x_0,y_0$: Tỷ lệ hiện tại/nguồn (m/px), đường kính (m), hệ số thu; gốc ô cắt. |
| **Tiền xử lý và Hough.** $P_{lo},P_{hi},P_{90}$; $N_{ô},N_{bin}$; clipLimit, $\beta$: Phân vị thấp/cao/90 %; pixel/ô, mức xám; hệ số chặn, ngưỡng cắt CLAHE. $h,h_x,h_y$; $R_g,\sigma,\ell$; $K_x,K_y,\star$: Gauss 1D/theo x/y; bán kính lọc, độ lệch chuẩn, lề; Sobel x/y, tương quan. $g_x,g_y,\left\lvert G\right\rvert,\theta$; $T_{low},T_{high}$: Gradient x/y, độ lớn, hướng; ngưỡng Canny thấp/cao. $\mathcal D_r,d_x,d_y,\mathbf n$; $A_r,S_r,S_{max}$: Tập độ lệch, thành phần x/y, pháp tuyến; tích lũy, số độ lệch tại r/lớn nhất. $\varphi,\varphi_j,T,R_n,E_n,B,K,J,L$: Góc quét/thứ j, số góc/r/biên, cỡ lô, số đỉnh, tổng độ dài đoạn, trần vòng. $v_{min},\kappa,\tau_r,q,k_r$; $\Delta r,\Delta\varphi$; $d_{NMS},\delta_{NMS}$: Phiếu/tỷ lệ tối thiểu, ngưỡng, hỗ trợ, nhóm r; bước r/góc; ngưỡng tâm/r. $r_{min/max},D_{min/max}$; $A_{sun},\alpha_N,\psi,\Delta_s$: Cận r/D; góc nắng/Bắc/trong ảnh/sai hướng. |
| **Sáng–tối và ghép.** $\mathbf u,\mathbf p,\mathbf c,t$; $x_c,y_c$; $I_i,\overline I,t_i,\overline t$: Hướng nắng, pixel, tâm, tọa độ dọc nắng; thành phần tâm; mẫu sáng/tọa độ, trung bình. $S,S_{raw},\tau$; $\beta_0,\beta_1,\beta_2$: Điểm sau/trước trừ nền, ngưỡng; mức nền, dốc x/y. $\mathbf c_i,\mathbf q_j,r_j^{ref}$; $\delta,\delta_{ij},x_{ij},\nu$: Tâm dự đoán/nhãn, r nhãn; lệch tâm chuẩn hóa, biến ghép, số cặp tối đa. |
| **Đếm và độ đo.** TP, FP, FN; $TP_{known},FN_{known},N_{known}$: Khớp/sai/bỏ sót; khớp/bỏ sót/số nhãn chắc chắn. Precision, Recall, $F_1$; $Recall_{known}$: Chính xác, bao phủ, trung bình điều hòa; bao phủ nhãn đã biết. $N_{dự\,đoán}=n_p,N_{nhãn}=n_q$; $n_1,m_1$; $P,Q,Z,U,H$: Số dự đoán/nhãn trước rút ma trận; hàng/cột sau rút; pixel đĩa/vành/biên vành, hợp pixel đếm, hố gộp. $\rho,A,N_D,N(\ge D),N_{px\,hợp\,lệ}$: Mật độ, diện tích km², hố trong dải/≥D, số pixel hợp lệ. |
| **Thống kê, tọa độ và sai số.** $\mu,\mu_L,\mu_U,X,P_\mu,p$; $N_1,N_2,A_1,A_2$: Kỳ vọng/cận Poisson, biến đếm, xác suất, giá trị kiểm định; số hố/diện tích hai vùng. $d,e_r,r_{ref},r_{dự\,đoán}$; $R_i,R_{gộp},\overline R,s_R,m,TP_i,N_i$: Lệch tâm/r, r nhãn/dự đoán; Recall ảnh/gộp/trung bình, SD, số ảnh, khớp/nhãn ảnh i. $u,v,u_0,v_0,W,z,v_x,v_y$: Con trỏ, gốc bản đồ, bề rộng, mức phóng, gốc vùng xem. $Z^{np},Z^{cv},P_e,e_{max},MSE$; $n,b_h,c,P_U$: Đầu ra NumPy/OpenCV, số phần tử, sai số cực đại/bình phương TB; vòng/hố, khoảng lớp, ô cắt, pixel khung bao. |

: Bảng M.2. Ký hiệu toán học.
