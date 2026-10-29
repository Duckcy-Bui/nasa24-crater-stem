# S2-15 — Chốt tham số và cấu hình đánh giá tuần 3

Ngày thực hiện: **29/10/2026**. Phụ trách theo phân công: Nguyễn Mạnh Tiến; phối hợp Hoàng Quốc Anh.
Căn cứ dòng 38, sheet Giao_viec trong Nhom_2_NASA24_Phan_cong_3_tuan.xlsx.

## Quyết định

Chốt `configs/s215_frozen.json` cho tuần 3; `configs/default.json` có nội dung JSON giống hệt và được game sử dụng. Giữ chính sách `score` đang triển khai, ghi tường minh toàn bộ tham số Hough. Đây là quyết định giữ mốc so sánh nhất quán; chưa phải kết luận cấu hình tối ưu hoặc chất lượng phát hiện đạt yêu cầu.

Chỉ căn cứ tuning: S2-06 trên ba ảnh cho score 0/28 và radius_balanced 2/28, mức cải thiện còn thấp; smoke test S2-07 trên một ảnh cho cả bốn biến thể 0/10. Chưa đủ căn cứ đổi chính sách game. Không dùng số liệu holdout để chọn cấu hình. Các cấu hình S2-01 tiếp tục là nhánh thử nghiệm riêng.

| Thành phần | Tham số cố định |
|---|---|
| Ảnh | 512×512; float32 [0,1]; tọa độ tâm pixel nguyên |
| Tiền xử lý | p_lo=0,5; p_hi=99,5; CLAHE clip=2, grid=8, bits=8; Gaussian sigma=1,5, kernel=11, reflect_101; Canny high_pct=90, low_ratio=0,4; edge_margin=6 px |
| Hough | NumPy full_circle; candidate_selection=score; r=5–128 px kẹp theo metadata từng ảnh; bước r=1 px; bước góc=1° |
| Ngưỡng và chọn vòng | min_votes=12; min_vote_ratio=0,35; NMS tâm=4 px/r=2 px; max_circles=100; edge_batch_size=256 |
| Hậu xử lý | S1-11 chỉ gắn nhãn sáng–tối; không loại inverted/texture; không bật dedupe S2-05 |
| Đánh giá | Ghép một–một theo tâm ≤0,5 r_ref; ưu tiên nhãn chắc chắn, bỏ qua uncertain; nhãn thưa chỉ có Recall_known |

App đọc rõ cả preprocess và hough từ cấu hình. Kernel 11 tương đương mặc định tự tính với sigma=1,5 nên giữ hành vi hiện tại. Tham số sáng–tối và hash mã hậu xử lý được lưu trong report.

## Kết quả và nhận diện phiên bản

Đã chạy **18/18 ảnh tuning** của S2-03: **TP_known=10, FN_known=164, Recall_known micro=10/174=5,75%**. FP/Precision/F1 để null do nhãn thưa. Không coi 100 ứng viên máy là 100 hố thật. Recall vẫn thấp và cần ghi hạn chế trong game, thống kê và báo cáo.

- [Báo cáo đầy đủ](evidence/s2-15/report.json): cấu hình, phiên bản, môi trường, hash và từng ảnh.
- [Bảng từng ảnh](evidence/s2-15/results.csv): TP/FN/Recall, thời gian Hough và trạng thái chạm trần ứng viên.
- [Hồ sơ bằng chứng](evidence/s2-15/README.md): JSON vòng máy và các cặp ghép từng ảnh.

Commit nền: `66d3adf99923d7ab7223139f76406236421e3c69`. Đây là commit trước thay đổi S2-15, không phải commit đã chứa S2-15. Report lưu trạng thái working tree và SHA-256 byte thực tế của mã/config/manifest/ảnh/metadata/mask/nhãn. Hash byte local có thể đổi khi Git chuyển CRLF sang LF. Thời gian một lượt/ảnh, không warm-up, chỉ để chẩn đoán chứ không dùng so tốc độ.

## Tái tạo

Môi trường requirements-test.txt, dữ liệu S1-06 đã giải nén. Từ gốc repo, chọn thư mục đầu ra mới:

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -X utf8 -B scripts/freeze_s215.py --output outputs/s215_tuning_recheck
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p test_s215.py -v
```

Script mặc định chạy đủ 18 tuning, không ghi đè hồ sơ; --images chỉ nhận ảnh tuning không trùng. Holdout, ảnh lạ và cấu hình game khác snapshot bị từ chối. Lỗi giữa lượt được ghi report status=failed; không dùng lượt chưa complete làm kết quả.

## Dùng cho tuần 3 và điều kiện đánh giá lại

S3-02/S3-03/S3-05 dùng cùng snapshot và phiên bản mã có hash tương ứng. Bảng holdout S2-06 giữ là phép đo lịch sử. Không chạy lại để tìm cấu hình tốt hơn. Nếu cần tái tạo S3-02:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/evaluate_hough.py --config configs/s215_frozen.json --holdout --output outputs/s215_holdout_reproduction --repeats 3
```

Script đối chiếu vẫn đo riêng score/balanced/OpenCV; chỉ numpy_score đại diện chính sách game đã chốt. Không lấy dòng tốt nhất trên holdout để đổi chính sách. Holdout đã được xem ở S2-06, không còn là bộ kiểm tra chưa xem cho các lần thay đổi mới.

- Đổi tiền xử lý/Hough/ngưỡng/NMS/dải r/giới hạn ứng viên/chính sách chọn: tạo phiên bản mới và chạy lại tuning, các đánh giá máy liên quan; chạy lại holdout phải ghi là đánh giá lặp.
- Bật bỏ inverted/texture hoặc dedupe: đo Recall trước/sau và đánh giá lại số đếm/kích thước/mật độ, game liên quan.
- Đổi ảnh/crop/scale/mask/nhãn/split/matching: tăng phiên bản dữ liệu/đánh giá và tái tạo các bảng/ảnh phụ thuộc; không trộn lượt cũ/mới.
- Đổi thư viện/môi trường: kiểm hồi quy và đối chiếu đầu ra. Muốn so tốc độ phải đo lại cùng điều kiện và lặp sau warm-up.
- Khi triển khai cấu hình/mã mới: khởi động lại app để xóa cache máy theo ảnh, làm nóng tối đa 8 ảnh khảo sát. Nếu đổi đầu ra, người viết báo cáo cập nhật Bảng 1.1, mục 3.7/5.4 và Hình 5.2.

Sau khi đồng bộ main `cc31a8f` ngày 29/10/2026, S2-09 đã được tích hợp. S2-13 còn lỗi #10 (mật độ tính trên ứng viên chạm trần), #11 (so hai vùng chưa có trong app) và cần kiểm lại luồng với thống kê. S2-14 chưa có bằng chứng thử phiếu/người dùng trong repo. Chốt kỹ thuật S2-15 không thay thế nghiệm thu các phụ thuộc hay khảo sát thật. Chưa cập nhật Excel, chưa triển khai dịch vụ và chưa gửi thông báo cho thành viên.

## Kiểm chứng kỹ thuật

284/284 test Python đạt với PYTHONUTF8=1 (gồm hai test mới từ chối holdout và cấu hình lệch snapshot); kiểm tra hợp đồng dữ liệu đạt. Log tại [validation.log](evidence/s2-15/validation.log). Đã đối chiếu lại toàn bộ hash mã/config trong report sau chạy, không có thay đổi.

### Kiểm lại sau khi tích hợp main ngày 29/10/2026

Commit `3159cb4` tích hợp main `cc31a8f` vào `NMTien`, giữ commit S2-15 `c1fc0cc`. Xung đột duy nhất ở nhật ký nhóm đã được xử lý bằng cách giữ đủ dòng của cả hai nhánh.

- **298/298 test Python**, **6/6 bộ test JavaScript** và kiểm tra hợp đồng dữ liệu đạt; log tại [validation_post_merge.log](evidence/s2-15/validation_post_merge.log).
- Chạy lại đủ **18/18 ảnh tuning**, TP_known=10, FN_known=164, Recall_known=5,75%; không chạy holdout. Danh sách vòng máy, kết quả ghép, hash dữ liệu đầu vào, dải bán kính và chính sách hậu xử lý giống hoàn toàn hồ sơ ban đầu trên cả 18 ảnh.
- [report_post_merge.json](evidence/s2-15/report_post_merge.json) lưu phiên bản mã, hash nguồn và kết quả mới; [post_merge_verification.json](evidence/s2-15/post_merge_verification.json) ghi đối chiếu từng ảnh. JSON vòng máy gốc vẫn đại diện đúng đầu ra; JSON lần chạy mới nằm tại `outputs/s215_post_merge_20261029/` trên máy local. Đã kiểm lại toàn bộ hash nguồn sau lượt chạy.
- Cấu hình đã chốt và hạn chế Recall thấp được bổ sung vào báo cáo mục 3.7; biên bản S2-16 có cập nhật kỹ thuật riêng ngày 29/10, giữ nguyên lịch sử và phần xác nhận của thành viên.
