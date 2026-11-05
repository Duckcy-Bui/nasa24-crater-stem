<!-- Thành viên tự khai AI, đánh giá và xác nhận; không điền thay. -->

# Phụ lục

Phụ lục dẫn tới mã, hướng dẫn và hồ sơ trong kho GitHub của nhóm.

## A. Hướng dẫn cài đặt và chạy

**Chữ viết tắt.** LRO (Lunar Reconnaissance Orbiter), LROC (LRO Camera); NAC/WAC (Narrow/Wide Angle Camera); PDS (Planetary Data System); CTX/HiRISE: camera Sao Hỏa. CLAHE (Contrast Limited Adaptive Histogram Equalization); NMS (Non-Maximum Suppression); STEM (Science, Technology, Engineering, Mathematics). JSON/CSV: định dạng văn bản; CI (Continuous Integration); DOI (Digital Object Identifier). SD là độ lệch chuẩn, MSE là sai số bình phương trung bình.

Xem [README: cài đặt, dữ liệu và demo](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/README.md), [requirements.txt](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/requirements.txt), [requirements-test.txt](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/requirements-test.txt). Lệnh chính, từ thư mục gốc:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate; Windows: .venv\Scripts\activate
python -m pip install -r requirements-test.txt
python -B scripts/install_s106_dataset.py
python -B -m streamlit run app.py
```

[Tái tạo bảng kết quả và giới hạn](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/S3-10_TAI_TAO_KET_QUA.md): `python -X utf8 -B scripts/reproduce_s310.py --output outputs/s310_full` (thư mục mới). Nhận manifest `complete/full`, seed 0; `chapter4_tables/` chứa Bảng 4.4–4.8 và nguồn/SHA. Bảng 4.5 dùng nhãn mù lịch sử; S3-05 chờ duyệt, khảo sát chưa làm.

Kiểm Python bằng `python -B -m unittest discover -s tests`; canvas:

```bash
for f in tests/test_canvas_*.js; do node "$f" || exit 1; done
```

Dựng báo cáo: cài `requirements-report.txt`, LibreOffice/Python UNO và Times New Roman; chạy `python -B scripts/build_report.py`. Bản đầy đủ cập nhật và lưu mục lục DOCX trước xuất PDF.

## B. Mã kiểm chứng ví dụ số Chương 2

[Mã NumPy `tiny_example`](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/scripts/verify_hough_examples.py) gọi các hàm Hough nội bộ và so với ma trận tính tay bằng `assert_array_equal`; thử cỡ lô 1, 2, 256. Chạy `python -B scripts/verify_hough_examples.py --tiny-only`. [Vết cộng phiếu từng bước](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md) giải thích cả 32 phiếu. Đây là liên kết tới mã kiểm, theo cách tổ chức phụ lục gọn của tài liệu học phần.

[Mã kiểm sai số tiền xử lý](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/scripts/verify_report_numerics.py): `python -B scripts/verify_report_numerics.py --out outputs/report_numerics.json` (file mới). [Kết quả từng ảnh và môi trường](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/evidence/s3-12/report_numerics.json).

## C. Nhật ký nhóm theo tuần

[Nhật ký CSV: ngày, người, đầu việc, phân công, trạng thái và việc tiếp](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/NHAT_KY_NHOM.csv), [biên bản tuần 2 và cập nhật](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/S2-16_NGHIEM_THU_TUAN_2.md). Tuần 1 (12–18/10) xây dữ liệu, Hough, giao diện; tuần 2 (19–25/10) tích hợp, phân lớp/lọc trùng; tuần 3 (26/10–01/11) đánh giá, chốt tham số và báo cáo. Ngày trong CSV là ngày ghi công việc, không tự nhận là ngày họp.

Theo bảng giao việc, ba sprint kéo dài 09–15/10, 16–22/10 và 23–29/10/2026. Nhóm họp vào ngày cuối mỗi sprint (Bảng C.1).

| Sprint | Ngày họp | Nội dung | Trạng thái đầu việc ngày 05/11/2026 |
|---|---|---|---|
| 1 (09–15/10) | 15/10/2026 | Rà 16 đầu việc sprint 1: dữ liệu 26 ảnh, Hough NumPy, tiền xử lý, giao diện khoanh vòng, bản chạy từ đầu đến cuối | 16 hoàn thành |
| 2 (16–22/10) | 22/10/2026 | Rà 16 đầu việc sprint 2: chấm điểm, lọc trùng, đếm mật độ, tích hợp, chốt tham số; biên bản nghiệm thu tuần 2 lập ngày 27/10/2026 | 12 hoàn thành, 2 chờ kiểm tra, 1 đang làm, 1 chưa bắt đầu |
| 3 (23–29/10) | 29/10/2026 | Rà 16 đầu việc sprint 3: đánh giá, báo cáo, slide, video, đóng gói | 5 hoàn thành, 5 chờ kiểm tra, 5 đang làm, 1 chưa bắt đầu |

: Bảng C.1. Họp cuối sprint.

## D. Sử dụng công cụ AI

Bảng D.1 khai công cụ, phần sử dụng và cách kiểm soát. Dòng của Tiến và Hưng ghi theo dấu vết trong kho mã: mô tả yêu cầu gộp mã #26 và hai commit S1-11 ngày 18/10/2026. Tỷ lệ/chữ ký ở Bảng M.1; bảng đánh giá được dẫn bên dưới.

| Thành viên | Công cụ | Dùng cho việc gì | Cách kiểm soát |
|---|---|---|---|
| Bùi Hải Đức | Claude Code (Anthropic); Codex (OpenAI), từ 31/10/2026 | Claude Code: viết và sửa mã giao diện, chấm điểm, tích hợp và test; rà soát yêu cầu gộp mã (pull request); soạn tài liệu và ghép báo cáo; dựng slide, video demo và phiếu xác nhận. Codex: sửa lỗi app, kiểm độc lập, chỉnh báo cáo và chạy tái tạo | Đọc thay đổi, chạy test và kiểm tra trên trình duyệt trước khi gộp mã (merge); số liệu trong báo cáo lấy từ kết quả chạy và tài liệu trong kho mã. Với Codex: người kiểm độc lập, chạy test, đối chiếu bằng chứng và trưởng nhóm duyệt trước khi tích hợp |
| Nguyễn Mạnh Tiến | Codex (OpenAI) | Hỗ trợ sửa mã, đối chiếu dữ liệu và mã băm, chạy kiểm tra tự động khi hoàn thiện Hough, đánh giá và phần lý thuyết | Không dùng thay việc kiểm nhãn bằng mắt; tự xem đủ 26 ảnh chồng nhãn và xác nhận trước khi dùng nhãn |
| Đinh Quang Hưng | Claude (Anthropic) | Hỗ trợ viết mã chấm sáng–tối theo hướng nắng và ghi nhật ký công việc | Tự kiểm hướng nắng bằng mắt trên 8 ảnh Apollo 16; có test riêng cho bước chấm; bước này chỉ gắn nhãn, không xóa ứng viên |
| Hoàng Quốc Anh | Codex (OpenAI) | Hỗ trợ script, bảng/ảnh và tài liệu S3-05; rà số liệu và bản ghép mục 4.6, kết luận Chương 5; hỗ trợ kiểm số liệu đếm S2-09/S3-03 | Đối chiếu CSV/JSON, cấu hình, mã băm và ảnh; chạy checker/test liên quan, dựng DOCX. Quốc Anh trực tiếp xem và xác nhận phiếu đếm S3-03; phân biệt kiểm tự động với xác nhận thị giác, giữ hạn chế và nguồn số liệu |

: Bảng D.1. Khai báo sử dụng công cụ AI.

[Phân công, sản phẩm và đánh giá từng thành viên theo bảng giao việc](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/bao_cao/dong_gop_va_danh_gia.md).

## E. Chi tiết thuật toán và bằng chứng bổ sung

[Chi tiết Hough, tiền xử lý, sáng–tối, lọc trùng, thống kê và tọa độ](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/bao_cao/chi_tiet_bo_sung.md) giữ các bảng/hình lịch sử đã chuyển khỏi phần chính. Ví dụ số bắt buộc đã nằm lại ở Chương 2; giả mã và độ phức tạp ở Chương 3. [Chỉ mục bằng chứng](https://github.com/Duckcy-Bui/nasa24-crater-stem/tree/main/docs/evidence) giữ bản gốc; [nguồn ảnh minh họa PNG](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/images/report/README.md) ghi cách chuyển định dạng.
