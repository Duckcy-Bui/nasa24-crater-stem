<!-- Thành viên tự khai AI, đánh giá và xác nhận; không điền thay. -->

# Phụ lục

Phụ lục dẫn tới mã, hướng dẫn và hồ sơ trong kho GitHub của nhóm.

## A. Hướng dẫn cài đặt và chạy

Xem [README: cài đặt, dữ liệu và demo](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/README.md), [requirements.txt](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/requirements.txt), [requirements-test.txt](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/requirements-test.txt). Lệnh chính, từ thư mục gốc:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate; Windows: .venv\Scripts\activate
python -m pip install -r requirements-test.txt
python -B scripts/install_s106_dataset.py
python -B -m streamlit run app.py
```

[Tái tạo bảng kết quả và giới hạn](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/S3-10_TAI_TAO_KET_QUA.md): `python -X utf8 -B scripts/reproduce_s310.py`. Chỉ nhận manifest `complete/full`; seed 0, giữ kết quả riêng từng lần. Đây không thay số liệu S3-05 chưa tích hợp hay khảo sát chưa làm.

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

[CHỜ cả nhóm: bổ sung ngày họp, nội dung thống nhất và trạng thái từng tuần vào nhật ký; không dựng lịch họp hồi tố khi chưa có xác nhận.]

## D. Sử dụng công cụ AI

Bảng D.1 khai công cụ, phần sử dụng và cách kiểm soát; mỗi người hoàn thiện dòng của mình. Tỷ lệ/chữ ký ở Bảng M.1; bảng đánh giá chéo được dẫn bên dưới.

| Thành viên | Công cụ | Dùng cho việc gì | Cách kiểm soát |
|---|---|---|---|
| Bùi Hải Đức | Claude Code (Anthropic); Codex (OpenAI), từ 31/10/2026 | Claude Code: viết và sửa mã giao diện, chấm điểm, tích hợp và test; rà soát pull request; soạn tài liệu và ghép báo cáo. Codex: sửa lỗi app, kiểm độc lập, chỉnh báo cáo và chạy tái tạo | Đọc thay đổi, chạy test và kiểm tra trên trình duyệt trước khi merge; số liệu trong báo cáo lấy từ kết quả chạy và tài liệu trong kho mã. Với Codex: người kiểm độc lập, chạy test, đối chiếu bằng chứng và trưởng nhóm duyệt trước khi tích hợp |
| Nguyễn Mạnh Tiến | [CHỜ] | [CHỜ] | [CHỜ] |
| Đinh Quang Hưng | [CHỜ] | [CHỜ] | [CHỜ] |
| Hoàng Quốc Anh | [CHỜ] | [CHỜ] | [CHỜ] |

: Bảng D.1. Khai báo sử dụng công cụ AI.

[Khung tự đánh giá, đánh giá chéo và sản phẩm từng thành viên](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/bao_cao/dong_gop_va_danh_gia.md). Các ô chưa xác nhận giữ nguyên, không suy từ sản phẩm hoặc số commit.

## E. Chi tiết thuật toán và bằng chứng bổ sung

[Chi tiết Hough, tiền xử lý, sáng–tối, lọc trùng, thống kê và tọa độ](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/bao_cao/chi_tiet_bo_sung.md) giữ các bảng/hình lịch sử đã chuyển khỏi phần chính. Ví dụ số bắt buộc đã nằm lại ở Chương 2; giả mã và độ phức tạp ở Chương 3. [Chỉ mục bằng chứng](https://github.com/Duckcy-Bui/nasa24-crater-stem/tree/main/docs/evidence) giữ bản gốc; [nguồn ảnh minh họa PNG](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/docs/images/report/README.md) ghi cách chuyển định dạng.
