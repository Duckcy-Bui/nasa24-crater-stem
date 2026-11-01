# Báo cáo bài tập lớn — nguồn Markdown (S3-12)

Báo cáo cuối được ghép từ các file `NN_*.md` trong thư mục này, theo thứ tự tên file, bằng `scripts/build_report.py`. File này (README) không được ghép.

## 1. Ai viết, ai chốt

| File | Nội dung | Bản ghép đầu tiên | Người chốt nội dung (mã việc) |
|---|---|---|---|
| `00_mo_dau.md` | Bìa, mục lục, danh mục ký hiệu và chữ viết tắt | Đức | Đức (S3-12). Cả nhóm điền tên trường, mã lớp, MSSV, giảng viên |
| `01_chuong_1_gioi_thieu.md` | Chương 1. Giới thiệu | Đức, từ `CHUONG_1_NHAP.md` | Đức (S3-08) |
| `02_chuong_2_co_so_ly_thuyet.md` | Chương 2. Cơ sở lý thuyết | Ghép từ S1-14, S1-15, S1-12 | Tiến (S3-06) phần Hough; Hưng (S3-07) phần tiền xử lý và sáng–tối |
| `03_chuong_3_phuong_phap_cai_dat.md` | Chương 3. Phương pháp và cài đặt | Ghép từ S1-14, S1-11, S1-13, S2-01, S2-02, S2-05 | Hưng (S3-07); Tiến (S3-06) phần cài đặt Hough; thống kê chờ S2-09 |
| `04_chuong_4_du_lieu_danh_gia.md` | Chương 4. Dữ liệu, đánh giá và khảo sát | Ghép từ S1-16, S1-10, S2-03, S2-07 | Quốc Anh (S3-09); Tiến (S3-02) phần Precision/Recall |
| `05_chuong_5_he_thong_ket_luan.md` | Chương 5. Hệ thống, trò chơi và kết luận | Đức | Đức (S3-08) |
| `06_tai_lieu_tham_khao.md` | Tài liệu tham khảo (pandoc tự sinh từ `tai_lieu.bib`) | Đức | — |
| `07_phu_luc.md` | Phụ lục: phân công, đóng góp, cách chạy lại, khai báo dùng AI | Đức | Cả nhóm xác nhận phần của mình |

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

Đường dẫn tính từ thư mục `docs/bao_cao/`. Chỉ dùng ảnh đã có trong repo (`docs/images/`, `docs/evidence/`). Hình phải được nhắc trong văn bản trước khi xuất hiện, ví dụ "Hình 3.2 cho thấy…".

**Bảng.** Dùng bảng `|...|`. Chú thích đặt ngay dưới bảng, bắt đầu bằng dấu hai chấm. Khi xuất, chú thích hiện phía trên bảng:

```markdown
| Bước | Thư viện |
|---|---|
| CLAHE | OpenCV |

: Bảng 3.1. Phần tự viết và phần dùng thư viện.
```

**Trích dẫn.** Viết `[@duda1972]` hoặc `[@duda1972; @yuen1990]`. Khóa phải có trong `tai_lieu.bib`. Pandoc tự đánh số [1], [2]… theo thứ tự xuất hiện, và tự tạo danh mục ở `06_tai_lieu_tham_khao.md` theo chuẩn IEEE (`ieee.csl`). Thêm nguồn mới thì thêm mục vào `tai_lieu.bib` kèm DOI hoặc URL và ngày truy cập. Không trích file nội bộ của repo như một tài liệu tham khảo; chỉ ghi tên file trong văn bản khi mô tả cài đặt.

**Thuật ngữ thống nhất.** Dùng: ứng viên máy (vòng Hough trả về, chưa kiểm chứng); nhãn tham chiếu (vòng do người gán và kiểm chéo); Recall trên nhãn đã biết (Recall_known); tập điều chỉnh / tập kiểm tra; tâm pixel có tọa độ nguyên; Hough tròn tự cài đặt bằng NumPy.

## 3. Dựng báo cáo

```bash
pip install -r requirements-report.txt        # pypandoc_binary (kèm pandoc), python-docx
python scripts/build_report.py                # outputs/report/BaoCao_Nhom2_NASA24.docx và .pdf
python scripts/build_report.py --no-pdf       # chỉ DOCX
python scripts/build_report.py --only 03 --no-pdf --out /tmp/ch3   # thử riêng một chương
```

Script in số chữ và số dấu `[CHỜ]` của từng file. Bản PDF cần LibreOffice và Python có module `uno` (trên Ubuntu: gói `python3-uno`; nơi khác đặt biến `REPORT_UNO_PYTHON` trỏ tới python của LibreOffice). Script tự gọi `scripts/report_to_pdf.py` để cập nhật mục lục và số trang. Nếu không có LibreOffice, mở DOCX bằng Word, nhấn Ctrl+A rồi F9 để cập nhật mục lục, sau đó lưu PDF.

Khi ghép, script đổi `\qquad (2.1)` ở cuối công thức thành 8 khoảng trắng không ngắt, vì LibreOffice bỏ khoảng trắng TeX và làm số công thức dính vào công thức. Trang bìa hiện vẫn mang số trang 1.

Định dạng do script đặt: A4, Times New Roman 13, giãn dòng 1,3; lề trái 3 cm, các lề còn lại 2 cm; số trang ở giữa chân trang; mỗi chương bắt đầu trang mới.

## 4. Kiểm tra trước khi nộp (theo yêu cầu học phần)

- [ ] Đủ 5 chương; 25–40 trang nội dung chính; tổng 30–60 trang.
- [ ] Ít nhất 10 tài liệu tham khảo, trong đó ít nhất 3 bài có DOI; trích dẫn theo IEEE.
- [ ] Không còn dấu `[CHỜ ...]` và ghi chú `<!-- ... -->`.
- [ ] Số liệu khớp phiên bản mã cuối; hình và bảng đánh số liên tục theo chương.
- [ ] Bìa đủ tên trường, mã lớp, MSSV, giảng viên.
- [ ] Phụ lục có bảng đóng góp đã được cả bốn người xác nhận và phần khai báo dùng AI.

## 5. Trạng thái bản ghép (cập nhật 31/10/2026)

Dựng trên main `13394de` trước sửa: 55 trang, phần chính 45 trang. Sau bản sửa ngày 31/10 (nhánh `s3-08-report-final`): 53 trang, phần chính 43 trang (trang 5–47); bìa, mục lục và ký hiệu 4 trang, tài liệu tham khảo 3 trang, phụ lục 3 trang. **Phần chính còn vượt mức 40 trang.** Mức 25–40 trang phần chính và 30–60 trang toàn báo cáo được ghi ở mục 4; chưa tìm thấy bản quy định học phần gốc trong repo để đối chiếu.

| Chương | Trước | Sau | Ngân sách đề xuất | Việc tiếp theo (người chốt quyết định) |
|---|---:|---:|---:|---|
| 1 | 4 | 3 | 3 | Đã bỏ lặp mục tiêu, rút Bảng 1.1 và phần tổ chức |
| 2 | 11 | 11 | 9 | Tiến rút 2.2.5–2.2.6; Hưng rút ví dụ CLAHE và 2.3.3 |
| 3 | 12 | 12 | 10 | Hưng xem bỏ overlay cũ 3.1, rút 3.4–3.5; Tiến rút phần lặp và bảng thời gian 3.3 |
| 4 | 11 | 11 | 9 | Quốc Anh thay 4.8 bằng trạng thái chưa khảo sát và thiết kế tương lai; rút 4.2, 4.6 |
| 5 | 7 | 6 | 6 | Đã rút mô tả thao tác, dữ liệu và kết luận lặp; giữ ba hình |

Ngân sách đề xuất tổng 37 trang, chừa 3 trang trong mức 40 cho kết quả và hình còn phải cập nhật. Đây là ước lượng biên tập, chưa phải số trang sau sửa Chương 2–4. Số trang đo bằng pypdf trên bản dựng trước và sau sửa; đề xuất cắt chi tiết cho từng chương đã gửi riêng cho người chốt. Chưa sửa Chương 2–4 trong vòng này.

**Sau khi ghép PR #33 (S2-12), đo ngày 01/11/2026:** 58 trang, phần chính 48 trang (trang 5–52). Chương 3 tăng từ 12 lên 17 trang, vượt ngân sách 7 trang; các chương khác giữ số ở cột Sau. Phần chính cần rút thêm 8 trang để về mức 40.

Các dấu chờ và việc còn lại:

- **PR #26:** đã merge tại `d315169`, có trong main `13394de`; S2-16 mục 6 ghi lượt đối chiếu của trưởng nhóm. Đã bỏ dấu chờ ở Bảng 1.1, mục 5.4 và 5.7. Riêng 3.3.5 đã đối chiếu và xóa trong S2-12 (PR #33). Tiến đối chiếu rồi xử lý các dấu còn ở 2.2.3, 4.3.1 và 4.7 cùng người chốt chương.
- **S2-15:** đã chốt `configs/s215_frozen.json`, đồng bộ `configs/default.json`, giữ `score`, tập điều chỉnh 10/174. Mục 3.7 đã cập nhật; Quốc Anh và Tiến cần bỏ dấu chờ cũ ở 4.5, mô tả các lượt holdout sau là đánh giá lặp.
- **Hình 5.1–5.3:** giữ ảnh hiện có. Chính sách game không đổi, nên bỏ lý do chụp lại Hình 5.2 do chuyển sang cân bằng. Chụp lại giao diện ở vòng sau, khi lỗi #10 và #11 đã merge; ảnh hiện tại chưa chứng minh giao diện cuối.
- **S2-09/S3-03:** Bảng 1.1 và 5.7 đã ghi kết quả đếm tay. Mục 3.6 và câu về cặp vùng ở 4.1 đã cập nhật theo cặp Lunokhod 1 – Mare Frigoris, dải 300–2.000 m (S2-12, PR #33). Quốc Anh còn xác nhận S2-09. Nếu quy tắc loại vùng đổi thì đối chiếu lại các số liên quan.
- **S3-05 (Quốc Anh):** giữ dấu chờ kết quả ba thí nghiệm ở 4.6 và 5.7.
- **Thử người chơi và khảo sát:** trưởng nhóm quyết định bỏ ngày 31/10/2026 (phần thử của S2-07, S2-14, S3-01). Bảng 1.1, mục 5.7–5.9 đã ghi yêu cầu khảo sát ít nhất 10 học sinh chưa đạt, không có dữ liệu hứng thú/hiểu bài. Dấu chờ khảo sát đã bỏ trong phần của Đức. Quốc Anh cập nhật 4.8, 4.9 và ghi chú đầu Chương 4 theo quyết định này; đề xuất câu chữ ở `page-budget.md`. Khung phiếu chỉ còn là thiết kế cho hướng tiếp theo.
- **Số test cuối:** giữ nguyên dấu chờ ở 5.6, điền sau khi merge các PR cuối.
- **Phụ lục A, D:** giữ các ô chờ đóng góp, đánh giá và khai báo của từng người. Chỉ bổ sung Codex vào dòng của Đức ở Bảng D.1; các thành viên tự xác nhận phần mình.

Số dấu chờ trong phần được ghép (không tính ghi chú HTML): Chương 1 từ 2 xuống 0; Chương 5 từ 4 xuống 2; Chương 2, 3, 4 và Phụ lục lần lượt giữ 1, 2, 6 và 26. Tổng từ 41 xuống 37. Sau khi ghép PR #33, Chương 3 còn 0 dấu chờ, tổng còn 35. Đây vẫn là bản làm việc, chưa phải bản nộp.

Còn để người chốt xem lại: tiêu đề ảnh có mã việc ở Hình 3.4–3.5, sơ đồ chữ ở 3.1 chưa có số hình, các công thức hoặc ví dụ lặp giữa Chương 2–4. Ghi chú đầu Chương 2–4 còn nhiều trạng thái cũ về PR #26, nhãn và thống kê; cần đối chiếu nguồn trước khi xóa. Bảng trong `S2-03_TAP_DIEU_CHINH.md` còn ghi `sparse_unreviewed`; `manifest_split.json` ghi `sun_quality=measured` cho ảnh Apollo 16 trong khi metadata ghi `side_only` hoặc `none`.
