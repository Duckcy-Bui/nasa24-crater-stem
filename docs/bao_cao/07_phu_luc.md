<!--
Người chốt: cả nhóm. Mỗi thành viên kiểm tra dòng của mình ở Phụ lục A và D.
Phụ lục D, dòng của Đức: Đức xác nhận lại mô tả trước khi nộp.
Phụ lục C: Tiến (S3-10) đối chiếu với README cuối và lệnh tái tạo bảng kết quả.
-->

# Phụ lục

## A. Phân công và đóng góp

Bảng A.1 liệt kê các đầu việc chính và sản phẩm đã đưa vào kho mã của từng thành viên. Mã việc theo bảng giao việc của nhóm (S1 là sprint 1, S2 là sprint 2, S3 là sprint 3). Số pull request (PR) là số trong kho mã GitHub của nhóm.

| Thành viên | Đầu việc chính | Sản phẩm trong kho mã |
|---|---|---|
| Bùi Hải Đức | S1-01, S1-05, S1-09, S1-13, S2-04, S2-08, S2-13, S3-04, S3-08, S3-12 | Phạm vi và tiêu chí nghiệm thu; khung kho mã và định dạng dữ liệu; giao diện khoanh hố (PR #6); chạy từ đầu đến cuối và nháp Chương 1 (PR #7, #9); giải thích lệch 0,5 px của OpenCV (PR #8); chấm điểm (PR #15); màn hình kết quả (PR #16, #17); tích hợp (PR #18); sửa tọa độ tâm pixel (PR #27); ghép báo cáo |
| Nguyễn Mạnh Tiến | S1-03, S1-07, S1-12, S1-15, S2-01, S2-06, S2-11, S2-15, S3-02, S3-06, S3-10 | Ghi chú Hough và danh mục tài liệu; Hough tròn NumPy (PR #2); ví dụ tính tay, đối chiếu OpenCV và lý thuyết Hough (PR #5); tăng tốc Hough và cấu hình (PR #21); kiểm chéo nhãn tham chiếu |
| Đinh Quang Hưng | S1-04, S1-08, S1-11, S1-14, S2-02, S2-05, S2-09, S2-12, S3-03, S3-07, S3-11 | Đặc tả tiền xử lý; chuỗi tiền xử lý B0–B8 (PR #3); kiểm tra sáng–tối (PR #12); nháp Chương 2/3 (PR #13); phân lớp ứng viên (PR #19); lọc trùng (PR #22) |
| Hoàng Quốc Anh | S1-02, S1-06, S1-10, S1-16, S2-03, S2-07, S2-10, S2-14, S3-01, S3-05, S3-09, S3-13 | Nguồn ảnh; bộ 26 ảnh cắt và metadata (PR #1); công cụ gán nhãn (PR #4); hồ sơ dữ liệu, khung Chương 4 và khung khảo sát (PR #10); chia tập và nhãn 26 ảnh (PR #20); ba thí nghiệm (PR #24); thẻ khoa học (PR #25) |

: Bảng A.1. Đầu việc và sản phẩm của từng thành viên.

[CHỜ cả nhóm: bổ sung sản phẩm của các đầu việc sprint 3 khi hoàn thành.]

| Thành viên | Tỷ lệ đóng góp | Tự đánh giá | Đánh giá của các thành viên khác | Xác nhận |
|---|---|---|---|---|
| Bùi Hải Đức | [CHỜ] | [CHỜ] | [CHỜ] | [CHỜ] |
| Nguyễn Mạnh Tiến | [CHỜ] | [CHỜ] | [CHỜ] | [CHỜ] |
| Đinh Quang Hưng | [CHỜ] | [CHỜ] | [CHỜ] | [CHỜ] |
| Hoàng Quốc Anh | [CHỜ] | [CHỜ] | [CHỜ] | [CHỜ] |

: Bảng A.2. Tỷ lệ đóng góp và đánh giá chéo.

## B. Quy trình làm việc

- **Bảng giao việc:** 48 đầu việc, mỗi người phụ trách 12, mỗi việc có người phụ trách, người phối hợp, đầu ra, tiêu chí hoàn thành, link kết quả và ghi chú. Một việc chỉ được đánh dấu hoàn thành sau khi đầu ra đã được kiểm tra.
- **Kho mã:** mỗi đầu việc làm trên một nhánh riêng và đưa vào nhánh chính qua pull request. Người phối hợp hoặc nhóm trưởng duyệt nội dung. GitHub Actions chạy kiểm tra hợp đồng dữ liệu, toàn bộ test Python và test JavaScript cho mọi pull request. Pull request chỉ được merge khi kiểm tra đạt.
- **Bằng chứng:** ảnh kết quả, bảng số liệu và file JSON của từng đầu việc lưu trong `docs/evidence/`. Mỗi lần chạy lưu tham số và mã phiên bản.
- **Nhật ký:** mỗi thành viên ghi việc đã làm, đầu ra, vướng mắc và việc tiếp theo vào `docs/NHAT_KY_NHOM.csv`.

## C. Cách chạy lại

Các lệnh sau chạy từ thư mục gốc của kho mã, với Python 3.12. Trên Windows, kích hoạt môi trường bằng `.venv\Scripts\activate`.

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-test.txt
python scripts/install_s106_dataset.py            # giải nén bộ 26 ảnh và kiểm tra SHA-256
python -m streamlit run app.py                    # giao diện trò chơi tại http://127.0.0.1:8501
python scripts/run_end_to_end.py --all            # chạy chuỗi phát hiện trên cả bộ ảnh
python -m unittest discover -s tests              # test Python
for f in tests/test_canvas_*.js; do node "$f"; done   # test giao diện (Node.js)
python scripts/build_report.py                    # dựng báo cáo (cần requirements-report.txt)
```

[CHỜ S3-10: lệnh tái tạo bảng kết quả đánh giá và ba thí nghiệm.]

## D. Khai báo sử dụng công cụ AI

| Thành viên | Công cụ | Dùng cho việc gì | Cách kiểm soát |
|---|---|---|---|
| Bùi Hải Đức | Claude Code (Anthropic) | Viết và sửa mã giao diện, chấm điểm, tích hợp và test; rà soát pull request; soạn tài liệu và ghép báo cáo | Đọc thay đổi, chạy test và kiểm tra trên trình duyệt trước khi merge; số liệu trong báo cáo lấy từ kết quả chạy và tài liệu trong kho mã |
| Nguyễn Mạnh Tiến | [CHỜ] | [CHỜ] | [CHỜ] |
| Đinh Quang Hưng | [CHỜ] | [CHỜ] | [CHỜ] |
| Hoàng Quốc Anh | [CHỜ] | [CHỜ] | [CHỜ] |

: Bảng D.1. Khai báo sử dụng công cụ AI.
