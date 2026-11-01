# S3-16 — Đóng gói và bàn giao NASA 24 · Nhóm 2

Cập nhật 01/11/2026. Đức phụ trách bàn giao; từng thành viên tự xác nhận nội dung của mình. Gói chạy thử đã tạo từ main `c466c2d`; việc tạo gói không thay nghiệm thu bộ nộp cuối.

## 1. Trạng thái main

Mã nền: `c466c2d14a47d424b2ec74e61c782ef534dcfdcf`. Các PR sau đã merge và nằm trong mã này:

| PR | Nội dung đã vào main | Phần còn cần chủ nội dung chốt |
|---|---|---|
| [#33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33) | S2-12: Chương 3 về sáng–tối, lọc trùng, thống kê; cập nhật mục 3.3.5 và 4.1 | Hưng, Tiến, Quốc Anh đọc lại phần liên quan; rút gọn và kiểm lại số liệu/nguồn |
| [#34](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/34) | S2-13/S3-04: cảnh báo chạm trần, so sánh đếm tay hai vùng, sửa nút bán kính và nhãn điểm | Theo dõi A-06 và hợp đồng câu cảnh báo tại [S2-13 mục 3.2–3.4](S2-13_TICH_HOP.md) |
| [#35](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/35) | S3-08: quyết định bỏ khảo sát, rút Chương 1/5, Phụ lục và cập nhật biên bản S2-16 | Chương 2–4, số trang, dấu chờ và xác nhận thành viên vẫn cần hoàn thiện |
| [#36](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/36) | Hồ sơ Linux S3-10 và tài liệu bàn giao S3-16 | Chốt sản phẩm còn thiếu và gói cuối |

Theo xác nhận của trưởng nhóm ngày 01/11, VPS đã chạy `c466c2d`. Bản demo: [https://nasa24.webs.id.vn](https://nasa24.webs.id.vn), có mật khẩu: **hỏi trưởng nhóm**. Lượt đóng gói này không truy cập hoặc thay đổi VPS.

**Trưởng nhóm đã nghiệm thu S3-10**, căn cứ [bình luận PR #31](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/31#issuecomment-6552877683) và [hồ sơ Linux trong repo](evidence/s3-10/kiem_doc_lap_linux/README.md). Người kiểm độc lập đã đối chiếu 25/25 nhóm, 9 bảng CSV/102 dòng riêng, 0 giá trị lệch; đủ 62 artifact lượt gốc đúng hash. Sheet J49 do người điều phối cập nhật; không ghi URL hoặc sửa bảng trong lượt này. Giữ giới hạn NPZ cũ và mã nền `13394de` của bằng chứng lịch sử.

## 2. Yêu cầu đã biết và thông tin còn thiếu

Đề gốc “ĐỀ TÀI LIÊN QUAN ĐẾN NASA.docx” không có trong repo, Drive hoặc máy theo xác nhận của trưởng nhóm. [Khóa `debai_nasa`](bao_cao/tai_lieu.bib) ghi tên nguồn; các yêu cầu sau có bản ghi trong repo:

| Yêu cầu đã biết | Nguồn trong repo | Mức đáp ứng cần trình bày |
|---|---|---|
| Bốn chức năng: tiền xử lý/Hough tự viết và sáng–tối; thống kê/mật độ hai vùng; khoanh/chấm; thẻ khoa học | [Chương 1, mục 1.2](bao_cao/01_chuong_1_gioi_thieu.md) | Mã đã có; nêu đúng giới hạn của từng chức năng, không coi ứng viên máy là đáp án |
| Đánh giá Precision/Recall, ghép tâm lệch ≤0,5 bán kính; khảo sát ít nhất 10 học sinh | Chương 1, mục 1.2–1.3 | Nhãn thưa chỉ cho Recall_known, Precision/F1 toàn ảnh chưa xác định. Theo quyết định 31/10, không thử người chơi thật/khảo sát; tiêu chí khảo sát **chưa đạt** |
| Phạm vi dữ liệu hiện tại: 26 ảnh LROC Mặt Trăng, metadata/nhãn/bundle | Chương 1, mục 1.3; [hướng dẫn dữ liệu](S1-06_HUONG_DAN_DU_LIEU.md) | Sao Hỏa chưa triển khai; dùng ảnh browse, không suy tuổi tuyệt đối |
| S3-12: năm chương, tài liệu và phụ lục; A4, Times New Roman 13, giãn dòng 1,3; 25–40 trang chính, tổng 30–60 | [README báo cáo, mục 4](bao_cao/README.md) | Đếm lại trên PDF cuối; bản hiện tại còn vượt ngân sách và có dấu chờ |
| Ít nhất 10 tài liệu, ít nhất 3 bài có DOI; IEEE; bìa đủ thông tin; đóng góp/AI do thành viên xác nhận | README báo cáo, mục 4 | Người chốt kiểm danh mục, bìa, hình/bảng/công thức và xác nhận thật |
| S3-11: slide 15–20 trang, phân vai; S3-13: video 5–7 phút, đủ bốn chức năng/kết quả chính | [Tiêu chí đã ghi trong S3-16 tại c466c2d](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/c466c2d14a47d424b2ec74e61c782ef534dcfdcf/docs/S3-16_BAN_GIAO.md#L22-L23) | Hưng bàn giao slide; Quốc Anh bàn giao video. Chưa có tệp được nhận làm đầu vào đóng gói |

Các mục **chỉ đề gốc mới trả lời được**, Đức cung cấp trước khi nộp:

| Thông tin cần Đức cung cấp | Nội dung cần chốt |
|---|---|
| Nơi nộp | Hệ thống/thư mục/người nhận, cách gửi và quyền truy cập |
| Hạn nộp | Ngày, giờ và múi giờ chính thức |
| Tên tệp | Quy tắc tên ZIP, báo cáo, slide, video; định dạng bắt buộc |
| Biểu mẫu | Mẫu bìa, đánh giá/đóng góp, chữ ký hoặc phiếu nộp riêng của học phần |

Không dùng hạn trong kế hoạch sprint làm hạn nộp chính thức. Không tự tạo biểu mẫu hoặc số liệu để thay phần chưa có.

Tên `BaoCao_Nhom2_NASA24.docx` và `.pdf` là **quy ước nội bộ của nhóm**, do `NAME = "BaoCao_Nhom2_NASA24"` trong [scripts/build_report.py](../scripts/build_report.py) đặt từ commit `f3366c5` ngày 27/10/2026. Không có nguồn cho thấy học phần yêu cầu tên này. Chờ đề gốc hoặc giảng viên xác nhận quy cách tên tệp và nơi nộp; các tên do script tạo hiện chỉ là tên làm việc.

## 3. Sản phẩm và xác nhận thành viên

Mã, [bundle/metadata](../data/s106_bundle/), [nhãn](../data/reference_labels/), [chia tập](../data/s203_split/), [vùng đếm](../data/s209_counts/), [bảng đánh giá](evidence/) và [nguồn báo cáo](bao_cao/) có trong main. Script dưới dựng DOCX/PDF và hướng dẫn chạy cùng nguồn; slide, video và xác nhận người thật phải nhận riêng.

Bảng này liệt kê việc cần từng người tự xác nhận, không ký thay. Cột cuối để trống cho bằng chứng xác nhận phiên bản cuối. [S2-16 mục 5](S2-16_NGHIEM_THU_TUAN_2.md) đã có “Đồng ý” lịch sử của Đức; không tự điền các ô còn lại.

| Người | Cần xác nhận gì | Ghi ở đâu | Xác nhận bản cuối |
|---|---|---|---|
| Nguyễn Mạnh Tiến | Đóng góp/đánh giá chéo và AI; dòng của mình trong S2-16; tự xác nhận không phản đối đổi cặp vùng Lunokhod 1 – Mare Frigoris; phần Hough Chương 2 và 3, nhất là 3.3.5 được sửa hộ ở PR #33; số liệu đánh giá cùng Quốc Anh; đọc lại sau rút gọn; kết quả kiểm đủ bộ S3-14 | [Phụ lục A/D](bao_cao/07_phu_luc.md), S2-16 mục 5; việc đổi cặp vùng theo [review PR #30](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/30#pullrequestreview-5679533272), trả lời tại PR #30 hoặc [PR #29](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/29) mục 5; [PR #33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33), Chương 2–4 và biên bản kiểm phiên bản cuối | |
| Đinh Quang Hưng | Đóng góp/AI và S2-16; Chương 2 phần tiền xử lý/sáng–tối, Chương 3 phần 3.4–3.6 sau PR #33; nguồn các số đo thời gian, mô tả mật độ khớp app PR #34; nội dung sau rút gọn; slide/phân vai S3-11 và tổng duyệt S3-15 | Phụ lục A/D, S2-16 mục 5, PR #33, [Chương 2](bao_cao/02_chuong_2_co_so_ly_thuyet.md), [Chương 3](bao_cao/03_chuong_3_phuong_phap_cai_dat.md), tệp slide và biên bản tổng duyệt | |
| Hoàng Quốc Anh | Đóng góp/AI và S2-16; tự xác nhận kiểm chéo đếm tay/cặp vùng trên PR #30; mục 4.1 sửa hộ ở PR #33; Chương 4 sau rút gọn, ba thí nghiệm S3-05 và giới hạn không khảo sát; thẻ khoa học và video S3-13 | Phụ lục A/D, S2-16 mục 5, [PR #30](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/30), PR #33, [Chương 4](bao_cao/04_chuong_4_du_lieu_danh_gia.md), tệp video | |
| Bùi Hải Đức | Tự rà dòng đóng góp/AI và xác nhận S2-16 của mình; Chương 1/5 và bản ghép sau khi Chương 2–4 rút gọn; PDF/số trang, các sản phẩm, gói cuối và thông tin nộp chính thức. S3-10 đã nghiệm thu theo mục 1 | Phụ lục A/D, S2-16 mục 5, [README báo cáo](bao_cao/README.md), biên bản bàn giao cuối; người điều phối cập nhật trạng thái giao việc | |

Người chốt từng chương đối chiếu số liệu sau rút gọn, không chỉ xóa dấu `[CHỜ]`. Theo [góp ý PR #33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33#issuecomment-6553202790), cần rút phần lặp/giả mã và bổ sung nguồn thời gian hoặc bỏ số đo chưa có bằng chứng. Giữ hợp đồng câu cảnh báo theo [S2-13 mục 3.2](S2-13_TICH_HOP.md) khi sửa phần thống kê.

## 4. Đóng gói bằng script

[package_s316.py](../scripts/package_s316.py) chỉ lấy file từ commit qua `git archive`. Script dựng báo cáo bằng `scripts/build_report.py` trong chính bản archive, kiểm bundle/SHA, yêu cầu có cả DOCX/PDF, ghi manifest mọi file, tạo ZIP và gọi `ZipFile.testzip()`; sau đó so lại byte ZIP với gói và ghi checksum ZIP riêng. Không cần `data/processed/` để đóng gói, không ghi đè thư mục đầu ra có sẵn.

Từ gốc repo, dùng Python 3.12 đã cài `requirements-report.txt` và LibreOffice/UNO theo README báo cáo:

```bash
python -B scripts/package_s316.py \
  --commit c466c2d \
  --output outputs/s316_c466c2d
```

Nếu Python dựng báo cáo nằm ở venv khác, thêm `--report-python <đường-dẫn-python>`. Đường dẫn tương đối tính từ thư mục gọi lệnh, giữ nguyên symlink của venv; tên lệnh đơn như `python3.12` được tìm qua PATH. Để tạo gói nộp cuối, thay `c466c2d` bằng SHA đã chốt và chọn thư mục đầu ra mới; dùng tên chính thức sau khi Đức cung cấp.

```text
outputs/s316_<phiên-bản>/
  NASA24_Nhom2_<SHA>/
    ma_nguon/                 # đúng tệp tracked của commit, gồm README và bundle
    bao_cao/                  # DOCX/PDF dựng từ cùng commit
    HUONG_DAN_BAN_GIAO.md
    manifest.json             # SHA-256/kích thước mọi file trừ chính manifest
  NASA24_Nhom2_<SHA>.zip
  NASA24_Nhom2_<SHA>.zip.sha256
  build_report.log
  report_build/               # đầu ra dựng và tệp trung gian để kiểm
  result.json
```

Lượt thử r5 đã tạo gói từ `c466c2d`, DOCX/PDF dựng được, manifest và ZIP qua kiểm SHA-256/CRC. Gói chỉ chứa nguồn của commit đó, nên chưa có script/tài liệu r5 đang sửa; SHA của công cụ đóng gói được ghi riêng trong manifest. Sau khi thay đổi được tích hợp, chạy lại bằng commit cuối. Kết quả chạy thử không xác nhận chất lượng nội dung, số trang hoặc hoàn thành các phần của thành viên.

Script ghi số dấu chờ và phạm vi chưa kiểm (slide/video/xác nhận) trong manifest. Không đưa gói hoặc thư mục dựng vào Git. Khi bàn giao thật: nhận thêm sản phẩm còn thiếu; kiểm mọi hash sau giải nén, mở DOCX/PDF/slide/video từ bản sao; kiểm giao diện desktop/mobile và đúng phiên bản demo; ghi SHA ZIP, nơi lưu dự phòng và người nhận. Chỉ đánh dấu S3-16 hoàn thành khi Đức chốt đủ bộ.

## 5. Kiểm tra cuối

- [ ] Đức đã cung cấp bốn nhóm thông tin đề gốc còn thiếu ở mục 2.
- [ ] Mã/config/bundle và báo cáo cùng SHA đã chốt; phần đánh giá bị ảnh hưởng bởi thay đổi đã kiểm lại.
- [ ] DOCX/PDF cuối mở được, đạt cấu trúc/định dạng/số trang và hết dấu chờ chưa giải quyết; các chương sau rút gọn được đúng tác giả xác nhận.
- [ ] Đủ slide 15–20 trang, video 5–7 phút, phân vai; đóng góp/đánh giá chéo/AI và các xác nhận ở mục 3 có bằng chứng thật.
- [ ] Mọi sản phẩm ghi đúng khảo sát chưa đạt, nhãn thưa, đánh giá lặp và giới hạn khoa học; không tạo số liệu thay thế.
- [ ] Có biên bản kiểm đủ bộ/tổng duyệt và người xử lý lỗi còn lại; luồng game, thống kê/thẻ và demo đã được kiểm trên bản cuối.
- [ ] ZIP giải nén và kiểm hash được, tệp mở được, hướng dẫn không cần đường dẫn máy tác giả; bản sao dự phòng trùng hash.
- [ ] Đức quyết định nghiệm thu gói nộp, lưu link repo/SHA, checksum ZIP, nơi nộp và nơi dự phòng.
