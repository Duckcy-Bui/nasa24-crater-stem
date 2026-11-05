# Báo cáo bài tập lớn — nguồn Markdown (S3-12)

Báo cáo cuối được ghép từ các file `NN_*.md` trong thư mục này, theo thứ tự tên file, bằng `scripts/build_report.py`. File này (README) không được ghép.

## 1. Ai viết, ai chốt

| File | Nội dung | Bản ghép đầu tiên | Người chốt nội dung (mã việc) |
|---|---|---|---|
| `00_mo_dau.md` | Bìa, cam đoan/phân công, mục lục, danh mục hình/bảng/ký hiệu | Đức | Đức (S3-12). Cả nhóm điền tên trường, mã lớp, MSSV, giảng viên |
| `01_chuong_1_gioi_thieu.md` | Chương 1. Tổng quan bài toán | Đức, từ `CHUONG_1_NHAP.md` | Đức (S3-08) |
| `02_chuong_2_co_so_ly_thuyet.md` | Chương 2. Cơ sở lý thuyết | Ghép từ S1-14, S1-15, S1-12 | Tiến (S3-06) phần Hough; Hưng (S3-07) phần tiền xử lý và sáng–tối |
| `03_chuong_3_phuong_phap_cai_dat.md` | Chương 3. Thiết kế và cài đặt | Ghép từ S1-14, S1-11, S1-13, S2-01, S2-02, S2-05 | Hưng (S3-07); Tiến (S3-06) phần cài đặt Hough; Hưng phần thống kê; Đức kiến trúc/game |
| `04_chuong_4_du_lieu_danh_gia.md` | Chương 4. Thực nghiệm và đánh giá | Ghép từ S1-16, S1-10, S2-03, S2-07 | Quốc Anh (S3-09); Tiến (S3-02) phần Precision/Recall |
| `05_chuong_5_he_thong_ket_luan.md` | Chương 5. Kết luận và hướng phát triển | Đức | Đức (S3-08) |
| `06_tai_lieu_tham_khao.md` | Tài liệu tham khảo (pandoc tự sinh từ `tai_lieu.bib`) | Đức | — |
| `07_phu_luc.md` | Phụ lục A–E: cách chạy, mã kiểm, nhật ký, AI, liên kết bổ sung | Đức | Cả nhóm xác nhận phần của mình |

Bản ghép đầu tiên chỉ chuyển nội dung đã có trong repo sang dạng chương, không thêm kết quả mới. Người chốt đọc lại, sửa số liệu theo phiên bản chạy cuối và xóa các ghi chú `<!-- ... -->` khi xong.

## 2. Quy ước viết

**Cấu trúc.** Mỗi file có đúng một tiêu đề `# Chương N. Tên`. Mục con đánh số tay: `## N.M. Tên`, `### N.M.K. Tên`, không sâu hơn ba cấp. Mục lục lấy hai cấp đầu.

**Văn phong.** Tiếng Việt có dấu đầy đủ, câu ngắn, ngôi "nhóm". Báo cáo mô tả sản phẩm và kết quả, không kể tiến độ nội bộ: không ghi "PR #20", "Tiến cần…", "chờ duyệt" trong thân bài. Thông tin quy trình (PR, nhật ký) để ở Phụ lục.

**Chỉ ghi điều có bằng chứng.** Mọi con số phải có trong repo (`docs/`, `docs/evidence/`, `outputs/` được dẫn lại, test). Phần chưa có kết quả ghi đúng một dấu chờ, ví dụ `[CHỜ S3-02: bảng Precision/Recall trên tập kiểm tra]`. Script dựng báo cáo đếm và in các dấu này. Không thay kết quả thật bằng số ước lượng.

**Số và đơn vị.** Dấu thập phân là dấu phẩy trong văn bản (0,5 r; 2 m/px). Trong công thức viết `\text{0,5}` (cách viết `0{,}5` bị LibreOffice tách thành "0 , 5"). Đơn vị cách số một khoảng trắng.

**Công thức.** Công thức trong dòng dùng `$...$`. Công thức riêng dòng dùng `$$ ... \qquad (2.1) $$`, đánh số theo chương và nhắc trong văn bản là "công thức (2.1)".

**Hình.** Mỗi hình là một đoạn riêng, có số và chú thích:

```markdown
![Hình 3.2. Ảnh trước và sau tiền xử lý trên ảnh STT 13.](../images/s114/truoc_sau_stt13.png){width=85%}
```

Đường dẫn tính từ thư mục `docs/bao_cao/`. Dùng PNG, giữ nguồn gốc trong evidence. Chỉ dùng ảnh đã có trong repo (`docs/images/`, `docs/evidence/`). Hình phải được nhắc trong văn bản trước khi xuất hiện, ví dụ "Hình 3.2 cho thấy…".

**Bảng.** Dùng bảng `|...|`. Chú thích đặt ngay dưới bảng, bắt đầu bằng dấu hai chấm. Khi xuất, chú thích hiện phía trên bảng:

```markdown
| Bước | Thư viện |
|---|---|
| CLAHE | OpenCV |

: Bảng 3.1. Phần tự viết và phần dùng thư viện.
```

**Trích dẫn.** Viết `[@duda1972]` hoặc `[@duda1972; @yuen1990]`. Khóa phải có trong `tai_lieu.bib`. Pandoc tự đánh số [1], [2]… theo thứ tự xuất hiện, và tự tạo danh mục ở `06_tai_lieu_tham_khao.md` theo chuẩn IEEE (`ieee.csl`). Thêm nguồn mới thì thêm mục vào `tai_lieu.bib` kèm DOI hoặc URL và ngày truy cập. Hai nguồn học phần chỉ ghi tên “Quy định BTL Xử lý ảnh” và “Danh sách đề tài NASA, Đề 24”; diễn giải ngắn bằng lời của nhóm, không chép dài nội dung đề. Không trích file nội bộ của repo như một tài liệu tham khảo; chỉ ghi tên file trong văn bản khi mô tả cài đặt.

**Thuật ngữ thống nhất.** Dùng: ứng viên máy (vòng Hough trả về, chưa kiểm chứng); nhãn tham chiếu (vòng do người gán và kiểm chéo); Recall trên nhãn đã biết (Recall_known); tập điều chỉnh / tập kiểm tra; tâm pixel có tọa độ nguyên; Hough tròn tự cài đặt bằng NumPy.

## 3. Dựng báo cáo

```bash
pip install -r requirements-report.txt        # pypandoc_binary (kèm pandoc), python-docx
python scripts/build_report.py                # outputs/report/BTL_XLA.docx và .pdf
python scripts/build_report.py --no-pdf       # chỉ DOCX
python scripts/build_report.py --only 03 --no-pdf --out outputs/ch3   # thử riêng một chương
```

Script in số chữ và số dấu `[CHỜ]` của từng file. Bản PDF cần LibreOffice và Python có module `uno` (trên Ubuntu: gói `python3-uno`; nơi khác đặt biến `REPORT_UNO_PYTHON` trỏ tới python của LibreOffice). Script tự gọi `scripts/report_to_pdf.py` để cập nhật mục lục và số trang, lưu DOCX qua bộ lọc `Office Open XML Text`, mở lại để ổn định dàn trang, cập nhật/lưu trường lần nữa rồi xuất PDF. `--no-pdf` chỉ tạo bản nháp, chưa cập nhật mục lục; không dùng bản đó để nộp. Nếu không có LibreOffice, mở DOCX bằng Word, nhấn Ctrl+A rồi F9 để cập nhật mục lục, sau đó lưu PDF.

Khi ghép, script đổi `\qquad (2.1)` ở cuối công thức thành 8 khoảng trắng không ngắt, vì LibreOffice bỏ khoảng trắng TeX và làm số công thức dính vào công thức. Trang bìa hiện vẫn mang số trang 1. Danh mục hình/bảng sinh từ chú thích, số trang dùng trường PAGEREF được cập nhật cùng mục lục. PDF xuất ảnh bằng nén không mất dữ liệu, không giảm độ phân giải; DOCX giữ ảnh PNG. Thân bài dùng Times New Roman; công thức có thể dùng font toán thay thế.

Định dạng do script đặt: A4, Times New Roman 13, giãn dòng 1,3; lề trái 3 cm, phải 2 cm, trên/dưới 2,5 cm; số trang ở giữa chân trang; mỗi chương bắt đầu trang mới.

## 4. Kiểm tra trước khi nộp (theo yêu cầu học phần)

- [ ] Đủ 5 chương; 25–40 trang nội dung chính; tổng 30–60 trang.
- [ ] Ít nhất 10 tài liệu tham khảo, trong đó ít nhất 3 bài có DOI; trích dẫn theo IEEE.
- [ ] Không còn dấu `[CHỜ ...]` và ghi chú `<!-- ... -->`.
- [ ] Số liệu khớp phiên bản mã cuối; hình và bảng đánh số liên tục theo chương.
- [ ] Bìa đủ tên trường, mã lớp, MSSV, giảng viên.
- [ ] Phụ lục có bảng đóng góp đã được cả bốn người xác nhận và phần khai báo dùng AI.

## 5. Đối chiếu quy định học phần (01/11/2026, S3-12 r5)

Nền `94c17ff`, nhánh `s3-12-doi-chieu-de-goc`, đã gồm PR #40. Ngân sách dưới đây theo **Quy định BTL Xử lý ảnh** (tài liệu học phần), thay bảng ngân sách cũ. Bản nền dựng lại có 56 trang, 37 trang chính; bản đối chiếu có **44 trang, phần chính 33 trang (7–39)**. Chương 3+4 có 21/33 trang (63,6 %). Số trang đo từ PDF bằng pypdf, có thể đổi khi điền kết quả còn thiếu hoặc đổi môi trường dựng.

| Phần | Nền 94c17ff | Bản r5 | Ngân sách | Người chốt |
|---|---:|---:|---:|---|
| Mở đầu | 4 | 6 | 4–6 | Đức; cả nhóm ký và chốt tỷ lệ |
| Chương 1 | 3 | 3 | 3–4 | Đức |
| Chương 2 | 9 | 7 | 5–8 | Tiến; Hưng tiền xử lý/sáng–tối |
| Chương 3 | 10 | 9 | 6–10 | Tiến Hough; Hưng hậu xử lý/thống kê; Đức kiến trúc/game |
| Chương 4 | 9 | 12 | 7–12 | Quốc Anh; Hưng dữ liệu/thống kê; Tiến Hough |
| Chương 5 | 6 | 2 | 1–2 | Đức |
| Tài liệu tham khảo | 3 | 2 | 1–2 | Cả nhóm |
| Phụ lục | 12 | 3 | Không giới hạn, ưu tiên liên kết GitHub | Cả nhóm |

Ví dụ 5×5 đã trở lại Chương 2; Chương 3 có chín khối giả mã đánh số dòng, đầu vào/đầu ra, độ phức tạp, bảng sai số số học mới trên 26 ảnh. Giữ `dedupe_circles` và ví dụ M32/M8. Thiết kế ứng dụng chuyển từ Chương 5 về Chương 3; hình và kết quả sang Chương 4. Hình 5.1–5.3 cũ nay là Hình 4.5–4.7, PNG cùng pixel giải mã từ bằng chứng JPEG S3-08; không coi chuyển định dạng là khôi phục chi tiết đã mất hay một lượt chụp mới.

Phụ lục A hướng dẫn chạy; B dẫn mã kiểm ví dụ; C tóm tắt tuần và dẫn nhật ký; D khai báo AI; E chỉ dẫn liên kết. Chi tiết cũ được giữ trong [chi_tiet_bo_sung.md](chi_tiet_bo_sung.md), đóng góp/đánh giá chéo trong [dong_gop_va_danh_gia.md](dong_gop_va_danh_gia.md), hai file không ghép vào PDF. Các file mới đã vào `main` qua PR #43.

Cập nhật 04/11/2026: giữ bản 4.6 và kết luận S3-05 rút gọn từ main, bỏ hai dấu chờ duyệt theo yêu cầu của Quốc Anh và điền khai báo AI của Quốc Anh. Cập nhật 05/11/2026: theo quyết định của Đức (S3-16 mục 2.7), bản ghép và file đóng góp/đánh giá **không còn dấu chờ**:

| Nơi | Số dấu | Ai cần bổ sung |
|---|---:|---|
| Mở đầu | 0 | Tỷ lệ 25 % mỗi người theo 12 đầu việc/người; Đức ký ô của mình, ô của Tiến, Hưng, Quốc Anh để trống cho ký tay trên bản in |
| Chương 4 | 0 | Tiến gửi ngày 04/11/2026: RAM 12 GB; CPU giữ đúng mã hồ sơ đo ghi (`Intel64 Family 6 Model 154 Stepping 4`), không suy ra tên thương mại |
| Chương 5 | 0 | Đã xử lý dấu chờ duyệt kết luận S3-05 của Quốc Anh; Đức chốt toàn chương |
| Phụ lục C | 0 | Đức xác nhận nhóm họp ngày cuối mỗi sprint: 15/10, 22/10, 29/10/2026 (Bảng C.1); ngày trong CSV vẫn là ngày ghi công việc |
| Phụ lục D | 0 | Dòng Tiến và Hưng ghi theo dấu vết trong repo (mô tả PR #26; commit S1-11 `c3452f4`, `6f1b5f0`); hai bạn bổ sung nếu dùng thêm công cụ |
| File đóng góp/đánh giá chéo | 0 | Đức đánh giá theo bảng giao việc ngày 05/11/2026; ô xác nhận của ba bạn ký tay |

Môi trường lượt Linux 31/10 dùng đúng hồ sơ S3-10, hồ sơ đó chưa có RAM; không thay bằng cấu hình máy đo khác. Lượt kiểm số học 01/11 có môi trường riêng trong `docs/evidence/s3-12/`. Số test ở mục 3.8: 380 test Python và 6 bộ JavaScript, đo ngày 04/11/2026 trên nhánh dùng số S3-03 (nền main `b091f96` và PR #46); so với 370 thêm 2 test đóng gói trên Windows (PR #48) và 8 test S3-03. Trước đó 370 = 342 + 5 test trung bình ± SD, 16 test xuất bảng Chương 4 và 7 test liên kết công khai. r6 không chạy lại toàn bộ kiểm thử ứng dụng.

Đối chiếu Đề 24 vẫn có phần chưa đạt: chưa có Sao Hỏa; chưa ghép danh mục/đo Precision; chưa khảo sát ≥10 học sinh; thẻ theo vùng thay vì kích hoạt khi tìm thấy. Nhóm 4 người thay vì 5 theo quy định đã được chấp nhận (Đức xác nhận ngày 05/11/2026). Nêu ở Chương 1/5, không xem chỉnh văn bản là hoàn thành chức năng. Bản ghép và kết luận S3-05 đã được rà theo yêu cầu của Quốc Anh; vẫn cần Tiến tự xác nhận nghiệm thu S3-05 trên PR. Quốc Anh đã trực tiếp đồng ý bản đếm S3-03 mới 73/43 hố; chuyển số chính thức theo mục 7 tài liệu S3-03 là bước riêng, không thay bằng số cũ 47/32. Đây là **bản làm việc**, chưa đủ điều kiện nộp cuối; các xác nhận cá nhân khác vẫn chờ.

## 6. Hiệu chỉnh bảng chuyển/cắt sau kiểm r5 (r6)

R5-03 phát hiện hai ví dụ số đã bị bỏ khỏi bản r5 dù câu dẫn nói có ở tài liệu bổ sung. r6 khôi phục nguyên văn từ mốc `94c17ff`, không coi chúng đã được giữ trong r5.

| Mục nguồn tại 94c17ff | Đích sau r6 | Nội dung khôi phục và lý do | Chủ phần |
|---|---|---|---|
| 2.2.5, dòng 111 | Tài liệu bổ sung E.9; dẫn từ 2.2.4 | Điều kiện góc 180/π ≈ 57,3; 360 độ lệch lần đầu ở r=62, dao động 352–360 tới r=66, ổn định từ r=67 trong dải xét. Khôi phục ví dụ minh họa lượng tử hóa | Tiến |
| 2.2.6, dòng 125 | Tài liệu bổ sung E.9; dẫn từ 2.2.4 | Tổng 35.365/36.445 độ lệch; 24.291 điểm biên cho 859.051.215 ≈ 8,6×10^8 phiếu trước cắt biên. Khôi phục minh họa chi phí, giữ ký hiệu lịch sử và nguồn | Tiến |
