::: {custom-style="Cover Strong"}
[TÊN TRƯỜNG]

[TÊN KHOA / VIỆN]
:::

::: {custom-style="Cover"}
Học phần: Xử lý ảnh — Mã lớp: [MÃ LỚP]
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="1800"/></w:pPr></w:p>
```

::: {custom-style="Cover Title"}
BÁO CÁO BÀI TẬP LỚN
:::

::: {custom-style="Cover Big"}
PHÁT HIỆN HỐ VA CHẠM TRÊN ẢNH MẶT TRĂNG BẰNG BIẾN ĐỔI HOUGH VÀ TRÒ CHƠI STEM CHO HỌC SINH
:::

::: {custom-style="Cover"}
Đề tài NASA 24 — Nhóm 2
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="1200"/></w:pPr></w:p>
```

::: {custom-style="Cover"}
Giảng viên hướng dẫn: [HỌ TÊN GIẢNG VIÊN]

Sinh viên thực hiện:

Bùi Hải Đức — [MSSV] (nhóm trưởng)

Nguyễn Mạnh Tiến — [MSSV]

Đinh Quang Hưng — [MSSV]

Hoàng Quốc Anh — [MSSV]
:::

```{=openxml}
<w:p><w:pPr><w:spacing w:before="1800"/></w:pPr></w:p>
```

::: {custom-style="Cover"}
Hà Nội, tháng 10 năm 2026
:::

```{=openxml}
<w:p><w:pPr><w:pStyle w:val="CoverTitle"/><w:pageBreakBefore/></w:pPr><w:r><w:t>MỤC LỤC</w:t></w:r></w:p>
```

```{=openxml}
<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/><w:docPartUnique/></w:docPartObj></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \o "1-2" \h \z \u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Mở bằng Word và nhấn F9 để cập nhật mục lục.</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>
```

# Danh mục ký hiệu và chữ viết tắt

| Ký hiệu | Ý nghĩa |
|---|---|
| $(x, y)$ | Tọa độ cột, hàng trên ảnh xử lý 512 × 512; tâm pixel có tọa độ nguyên |
| $(a, b),\ r$ | Tâm và bán kính vòng tròn trong không gian tham số Hough, tính bằng pixel |
| $s$ | Tỷ lệ ảnh (m/px) |
| $D = 2rs$ | Đường kính hố theo mét |
| $k$ | Hệ số thu nhỏ bằng trung bình khối |
| $r_{\min},\ r_{\max}$ | Dải bán kính tìm kiếm sau khi kẹp theo metadata |
| $\theta$ | Hướng gradient tại pixel biên |
| $\mathrm{TP},\ \mathrm{FP},\ \mathrm{FN}$ | Số cặp khớp, số vòng dự đoán không khớp, số nhãn bị bỏ sót |
| $N_{\mathrm{nhãn}},\ N_{\mathrm{dự\,đoán}}$ | Số nhãn tham chiếu, số vòng dự đoán (của máy hoặc người chơi) |
| $\mathrm{Recall}_{\mathrm{known}}$ | Recall trên nhãn đã biết (nhãn thưa), $\mathrm{TP}_{\mathrm{known}}/N_{\mathrm{known}}$ |

: Bảng ký hiệu.

| Chữ viết tắt | Nghĩa |
|---|---|
| LRO, LROC | Lunar Reconnaissance Orbiter; LRO Camera |
| NAC, WAC | Narrow Angle Camera; Wide Angle Camera của LROC |
| PDS | Planetary Data System, kho dữ liệu hành tinh của NASA |
| CTX, HiRISE | Hai camera chụp Sao Hỏa của tàu Mars Reconnaissance Orbiter |
| CLAHE | Contrast Limited Adaptive Histogram Equalization |
| NMS | Non-Maximum Suppression, loại các đỉnh không cực đại |
| STEM | Science, Technology, Engineering, Mathematics |
| JSON, CSV | Định dạng dữ liệu văn bản dùng để lưu kết quả |
| CI | Continuous Integration, kiểm thử tự động khi có thay đổi mã |
| DOI | Digital Object Identifier, mã định danh bài báo |

: Bảng chữ viết tắt.
