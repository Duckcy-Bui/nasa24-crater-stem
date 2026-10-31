# S3-16 — Nháp bàn giao NASA 24 · Nhóm 2

Ngày 31/10/2026. Đức phụ trách, cả nhóm phối hợp. Đây là danh sách chuẩn bị bàn giao; chưa đóng gói, nộp hoặc nghiệm thu bản cuối. Mỗi người tự xác nhận phần mình; người kiểm độc lập đánh giá trước khi Đức chốt.

## 1. Căn cứ

- [Chương 1, mục 1.2–1.3](bao_cao/01_chuong_1_gioi_thieu.md), [khóa `debai_nasa`](bao_cao/tai_lieu.bib), [phân công](PHAN_CONG.md) và [README báo cáo](bao_cao/README.md).
- [Sheet `Giao_viec`](https://docs.google.com/spreadsheets/d/1yKUWW9lZNTrUFJ4CoFqSsDLIDddZcx6k_QKQN46ed8k/edit#gid=1240581173), ảnh chụp đọc ngày 31/10: `A40:P55`; S3-10 hàng 49, S3-16 hàng 55. Trạng thái dưới đây theo lần đọc đó, không tự xác nhận thay chủ phần. S3-16 phụ thuộc S3-14/S3-15, chỉ sửa lỗi cuối và bàn giao.
- Chưa có đề gốc trong repo/Drive. Các quy định chỉ có ở đề gốc, gồm nơi nộp, hạn, tên tệp và biểu mẫu: **cần trưởng nhóm đối chiếu đề gốc**.

## 2. Sản phẩm cần nhận

Mã nền đang xem là `13394de`; tệp có trong checkout chưa đồng nghĩa đã nghiệm thu bản nộp.

| Sản phẩm | Phụ trách | Đường dẫn và trạng thái |
|---|---|---|
| Mã nguồn, cấu hình, README/phụ thuộc | Đức tích hợp; Tiến: Hough; Hưng: tiền xử lý/thống kê; Quốc Anh: dữ liệu/thẻ | [app.py](../app.py), [src](../src/), [configs](../configs/), [tests](../tests/), [README](../README.md), `requirements*.txt` có trong repo. S3-04 trên Sheet: Đang làm; chờ kiểm luồng cuối. |
| Bundle ngoại tuyến, metadata, nhãn và nguồn ảnh | Quốc Anh; Tiến phối hợp kiểm nhãn | [Bundle](../data/s106_bundle/), [nhãn](../data/reference_labels/), [chia tập](../data/s203_split/), [vùng đếm](../data/s209_counts/), [hướng dẫn cài](S1-06_HUONG_DAN_DU_LIEU.md). Installer tạo 26 ảnh trong `data/processed/`; chờ chủ phần xác nhận bộ cuối. |
| Bảng đánh giá, ba thí nghiệm và thống kê | Tiến: S3-02; Quốc Anh: S3-05; Hưng: S3-03 | [S2-06/S3-02](evidence/s2-06-s3-02/), [S2-07](evidence/s2-07/), [S2-09](evidence/s2-09/), [S2-15](evidence/s2-15/). Sheet S3-02: Hoàn thành; S3-03/S3-05: Chưa bắt đầu. Lượt tái tạo không tự đóng các phần còn chờ. |
| README/script tái tạo và kiểm độc lập S3-10 | Tiến phụ trách, Đức phối hợp | [Script](../scripts/reproduce_s310.py), [cập nhật S3-10](S3-10_TAI_TAO_KET_QUA.md), [hồ sơ Linux](evidence/s3-10/kiem_doc_lap_linux/README.md). Người kiểm độc lập đã đối chiếu ngày 31/10. Đức quyết định nghiệm thu; Sheet J49 do Đức cập nhật. |
| Báo cáo DOCX/PDF, nguồn và phụ lục | Đức ghép; Tiến chốt Hough; Hưng chốt tiền xử lý/thống kê và mục 4.1; Quốc Anh chốt Chương 4 còn lại | [Nguồn báo cáo](bao_cao/), [script dựng](../scripts/build_report.py). S3-12: Đang làm; chưa nhận DOCX/PDF cuối trong checkout này. Đích sau dựng: `outputs/report/BaoCao_Nhom2_NASA24.docx` và `.pdf`. |
| Slide 15–20 trang, phân vai | Hưng, S3-11; cả nhóm | Chưa nhận đường dẫn; Sheet: Chưa bắt đầu. Nội dung phải khớp báo cáo và giới hạn đã ghi. |
| Video demo 5–7 phút | Quốc Anh, S3-13; Đức phối hợp | Chưa nhận đường dẫn; Sheet: Chưa bắt đầu. Cần đủ bốn chức năng, kết quả chính, hình/chữ/âm thanh rõ. |
| Đóng góp, đánh giá chéo, nhật ký, khai báo AI | Quốc Anh tổng hợp S3-09; từng người tự xác nhận | [Phụ lục A/D](bao_cao/07_phu_luc.md), [nhật ký](NHAT_KY_NHOM.csv). Còn phần chờ, chưa đủ xác nhận thành viên. |
| Kiểm đủ bộ S3-14; tổng duyệt S3-15 | Tiến; Hưng; cả nhóm phối hợp | Chưa nhận biên bản cuối; Sheet đều Chưa bắt đầu. Tổng duyệt theo Sheet: 12 phút trình bày, 3 phút demo, 5 phút vấn đáp. |
| Gói cuối, link repo, dự phòng S3-16 | Đức, cả nhóm | [Repo](https://github.com/Duckcy-Bui/nasa24-crater-stem). Sheet: Chưa bắt đầu; chưa tạo ZIP hoặc bản sao dự phòng trong lượt này. |

Báo cáo theo S3-12: đủ Chương 1–5, tài liệu/phụ lục; A4, Times New Roman 13, giãn dòng 1,3; 25–40 trang nội dung chính, tổng 30–60 trang. S3-06 yêu cầu ít nhất 10 nguồn, ít nhất 3 bài có DOI đã kiểm. Số trang cuối phải đếm trên PDF mới.

Bản chạy thử: [https://nasa24.webs.id.vn](https://nasa24.webs.id.vn), có mật khẩu: **hỏi trưởng nhóm**. Chưa đối chiếu commit trên server trong lượt tài liệu này.

## 3. Bằng chứng và giới hạn

Lượt Linux tại `13394de` đã `complete/full`, mặc định `repeats=3`. [Manifest](evidence/s3-10/kiem_doc_lap_linux/manifest.json) giữ nguyên byte; [tóm tắt](evidence/s3-10/kiem_doc_lap_linux/so_khop_tom_tat.json) ghi số dòng khớp/lệch và 10 file khác hash. [README bằng chứng](evidence/s3-10/kiem_doc_lap_linux/README.md) nêu phạm vi so sánh, khác biệt LF/CRLF/CLI và NPZ cũ chưa có để so từng mảng. Ngày 31/10/2026, người kiểm độc lập đối chiếu bằng script riêng: **25/25 nhóm, 9 bảng CSV/102 dòng riêng, 0 giá trị lệch**; xác nhận lượt gốc có đủ **62 artifact**, tất cả đúng hash manifest. Kết quả PASS trong phạm vi S3-10 và nháp S3-16. **Đức quyết định nghiệm thu S3-10; Sheet J49 do Đức cập nhật.**

**Theo quyết định 31/10, không làm thử người chơi thật và khảo sát** của phần thử S2-07, S2-14, S3-01. Tiêu chí khảo sát ít nhất 10 học sinh **chưa đạt**; không có số liệu để kết luận hứng thú/hiểu bài. Báo cáo, slide và video phải cùng ghi hạn chế này.

Nhãn thưa chỉ cho Recall_known, FP/Precision/F1 toàn ảnh chưa xác định; holdout là đánh giá lặp. Game giữ `score` S2-15, ứng viên thường chạm trần 100. Theo Chương 1, Sao Hỏa chưa triển khai, thẻ khoa học chưa ghim vị trí; sáng–tối thiếu hướng nắng có phần không đánh giá được. Giữ đúng giới hạn khi trình bày kết quả.

## 4. Đóng gói sau khi chốt phiên bản

Các bước dưới là hướng dẫn, chưa thực hiện trong lượt soạn nháp.

1. Nhận tệp cuối và biên bản từ các chủ phần; Đức xem biên bản của người kiểm độc lập và chốt SHA đầy đủ. So hash mã/config/đầu vào cuối với manifest S3-10; thay đổi ảnh hưởng kết quả cần kiểm lại. Giữ nhãn `13394de` cho bằng chứng lịch sử, không đổi thành kết quả của commit mới.
2. Tại checkout cuối đã tích hợp tài liệu, tạo thư mục mới và lấy đúng tệp tracked. Điền SHA trước khi chạy:

```bash
N24_FINAL_COMMIT='DIEN_SHA_COMMIT_CUOI'
N24_PACKAGE="/tmp/NASA24_Nhom2_$N24_FINAL_COMMIT"
test "$N24_FINAL_COMMIT" != 'DIEN_SHA_COMMIT_CUOI' || exit 1
test "$(git rev-parse HEAD)" = "$N24_FINAL_COMMIT" || exit 1
test -z "$(git status --porcelain)" || exit 1
mkdir "$N24_PACKAGE" || exit 1
mkdir "$N24_PACKAGE/ma_nguon" "$N24_PACKAGE/bao_cao" "$N24_PACKAGE/slide" "$N24_PACKAGE/video" "$N24_PACKAGE/kiem_tra"
git archive "$N24_FINAL_COMMIT" | tar -xf - -C "$N24_PACKAGE/ma_nguon" || exit 1
```

3. Dựng báo cáo từ cùng checkout, bằng môi trường đã cài `requirements-report.txt` và LibreOffice/UNO theo README báo cáo:

```bash
python -X utf8 -B scripts/build_report.py --out "$N24_PACKAGE/bao_cao" || exit 1
```

   Kiểm có cả DOCX/PDF, mở và đếm trang. Sao slide/video thật từ đường dẫn chủ phần bàn giao vào `slide/`, `video/`; ghi tên tệp thực tế. Không đặt tệp ví dụ thay phần chưa nhận.
4. Gói đã có bundle và hồ sơ Linux gọn trong `ma_nguon/data/` và `ma_nguon/docs/evidence/`; installer sinh ảnh xử lý. Manifest là chỉ mục lượt gốc, không kèm đủ 62 artifact Linux. Nếu cần kèm lượt full chi tiết của mã cuối, chạy script tái tạo ra thư mục mới rồi sao kết quả vào `kiem_tra/`. Thêm biên bản/log kiểm cuối đã nhận. Viết `VERSION.txt` (repo, SHA, ngày, phiên bản từng sản phẩm/bằng chứng) và `HUONG_DAN_BAN_GIAO.md` (danh mục thật, cách cài/chạy theo README, link nội bộ tới tài liệu này và bản demo). Không kèm `.git`, `.venv`, cache, thông tin đăng nhập hoặc dữ liệu người chơi.
5. Mở sản phẩm và chạy kiểm từ thư mục mới; lưu log. Tạo checksum tương đối, ZIP và kiểm ZIP:

```bash
(
  cd "$N24_PACKAGE" || exit 1
  find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
  sha256sum -c SHA256SUMS
) || exit 1
python3.12 -B -m zipfile -c "$N24_PACKAGE.zip" "$N24_PACKAGE" || exit 1
python3.12 -B - "$N24_PACKAGE.zip" <<'PY' || exit 1
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    bad = archive.testzip()
if bad is not None:
    raise SystemExit(f"ZIP hỏng: {bad}")
PY
```

   Giải nén sang nơi trống, kiểm lại checksum và mở DOCX/PDF/slide/video từ đó. Tính SHA-256 riêng cho ZIP, ghi vào biên bản.
6. Đức chốt gói nộp, link repo kèm SHA và vị trí sao dự phòng; kiểm hash bản sao. Ghi tên gói, checksum, nơi lưu thật và người nhận. Không tự đăng/nộp hay cập nhật server khi mới soạn nháp.

## 5. Kiểm tra cuối

Các ô giữ trống cho người thực hiện đánh dấu khi có bằng chứng.

- [ ] Đức đã đối chiếu đề gốc và chốt quy cách/nơi nộp, SHA và danh mục thực tế.
- [ ] Mã/config/dữ liệu trong gói đồng nhất phiên bản; installer chạy từ thư mục trống; game trên 26 ảnh khớp baseline được phép dùng.
- [ ] Đã có biên bản của người kiểm độc lập cho S3-10 và bản cuối; có biên bản S3-14/S3-15, log kiểm và người xử lý lỗi còn lại.
- [ ] Luồng mở ảnh, khoanh/sửa/xóa, lưu, chấm, thống kê/thẻ chạy trên desktop/mobile; Đức kiểm phiên bản và quyền truy cập demo.
- [ ] DOCX/PDF mới mở được, đạt cấu trúc/định dạng/số trang ở mục 2; hình, bảng, công thức và mục lục đúng; từng tác giả xác nhận phần mình.
- [ ] Đủ slide 15–20 trang, video 5–7 phút, phân vai và bảng đóng góp/đánh giá chéo/AI do đúng người cung cấp.
- [ ] Mọi sản phẩm cùng ghi khảo sát chưa đạt và các giới hạn ở mục 3; không có số liệu khảo sát giả hoặc dấu chờ bị xóa thiếu căn cứ.
- [ ] ZIP giải nén được, checksum đúng, tệp mở được; hướng dẫn dùng đường dẫn trong gói; bản sao dự phòng trùng hash và Đức đã quyết định bàn giao.
