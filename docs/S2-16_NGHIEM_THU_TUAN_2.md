# S2-16 — Biên bản nghiệm thu mốc tuần 2

Người lập: Bùi Hải Đức (trưởng nhóm). Mốc theo kế hoạch: ngày 14 (22/10/2026). Biên bản lập muộn, ngày 27/10/2026, trên main `3cff367`; mục 1–5 tính tới ngày lập. Mục 6 cập nhật ngày 28/10/2026, sau khi merge PR #26 và #30.

Biên bản chỉ ghi điều kiểm được trong repo, trên bảng giao việc và trên bản chạy thử. Mỗi thành viên đọc dòng của mình ở mục 2 và xác nhận ở mục 5; người lập không xác nhận thay.

## 1. Kết luận

**Mốc tuần 2 chưa đạt.** Trong năm tiêu chí của S2-16, hai tiêu chí đạt, hai tiêu chí không đạt, một tiêu chí mới đạt ở mức bản nháp:

| Tiêu chí (bảng giao việc, S2-16) | Kết quả | Căn cứ |
|---|---|---|
| Đủ bốn chức năng | **Không đạt** (3/4) | Phát hiện, trò chơi và thẻ khoa học chạy trên main và VPS. Thống kê (S2-09) chưa có mã; app ghi "Chưa có thống kê" ([S2-13 mục 2.1](S2-13_TICH_HOP.md)) |
| Tham số đã chốt | **Không đạt** | S2-15 bị chặn. PR #26 đề xuất chọn ứng viên cân bằng theo bán kính nhưng chưa merge, và chưa có quyết định cho cấu hình game |
| Mỗi người có phần báo cáo của mình | Đạt ở mức nháp | Báo cáo 5 chương đã ghép (PR #28). Mỗi chương có người chốt (`docs/bao_cao/README.md` mục 1), nhưng Chương 2–4 còn là bản ghép từ tài liệu Sprint 1–2, chưa được người chốt sửa |
| Có danh sách lỗi | Đạt | [S2-13 mục 3](S2-13_TICH_HOP.md): 9 lỗi, mỗi lỗi có mức và người xử lý; 3 lỗi đã sửa |
| Không còn chức năng bắt buộc chưa bắt đầu | **Không đạt** | S2-09 (thống kê) vẫn "Chưa bắt đầu" |

Kiểm thử trên main `3cff367`: 270 test Python và 6 bộ test JavaScript đều qua, CI xanh. Test chỉ cho biết mã đúng thiết kế, không nói gì về độ chính xác phát hiện.

## 2. Trạng thái các đầu việc Sprint 2

| Mã | Việc | Phụ trách | Trạng thái 27/10 | PR | Còn thiếu |
|---|---|---|---|---|---|
| S2-01 | Hough: hố lớn, dải bán kính, thời gian | Tiến | Đang làm | #21 (đã merge), #26 (mở) | Phần hố lớn nằm ở #26: chọn ứng viên theo nhóm bán kính, Recall_known tập kiểm tra 4/66 lên 5/66 |
| S2-02 | Rà biên, kiểm tra theo sáng–tối | Hưng | Hoàn thành | #19 | — |
| S2-03 | Tập điều chỉnh, tập kiểm tra, nhãn | Quốc Anh | Đang làm | #20 (đã merge) | Tiến đăng xác nhận kiểm chéo nhãn trên PR #20 |
| S2-04 | Chấm điểm | Đức | Hoàn thành | #15 | — |
| S2-05 | Lọc trùng | Hưng | Hoàn thành | #22 | Chưa bật trong pipeline (mục 4) |
| S2-06 | Kiểm chứng NumPy, đối chiếu thư viện | Tiến | Có PR, chờ sửa | #26 (mở) | Sửa theo review: cấu hình mặc định của game, dung lượng bằng chứng |
| S2-07 | Ba thí nghiệm, thử nhỏ trò chơi | Quốc Anh | Đang làm | #24 (đã merge) | Chưa có lượt thử người chơi thật nào |
| S2-08 | Màn hình kết quả, lưu lượt chơi | Đức | Hoàn thành | #16, #17 | — |
| S2-09 | Thống kê, histogram, mật độ hai vùng | Hưng | **Chưa bắt đầu** | — | Toàn bộ; hợp đồng đầu ra đã có ở S2-13 mục 1 |
| S2-10 | Thẻ khoa học | Quốc Anh | Đang làm | #25 (đã merge) | Thẻ theo vùng đã chạy (21/26 ảnh). Ghim vị trí chưa đạt (mục 4) |
| S2-11 | Dẫn xuất Hough, mô tả cài đặt | Tiến | Có PR, chờ sửa | #26 (mở) | Như S2-06 |
| S2-12 | Chương 3: sáng–tối, lọc trùng, thống kê | Hưng | Chưa bắt đầu | — | Phần sáng–tối và lọc trùng đã có nháp trong Chương 3 (#28); phần thống kê chờ S2-09 |
| S2-13 | Tích hợp bốn chức năng | Đức | Đang làm | #18, #27, #29 | Chờ S2-09 |
| S2-14 | Phiếu khảo sát, Chương 4 phần phương pháp | Quốc Anh | Chưa bắt đầu | — | Lịch khảo sát ≥ 10 người, phiếu đã thử |
| S2-15 | Chốt tham số | Tiến | Bị chặn | — | Chờ #26 và quyết định ở mục 4 |
| S2-16 | Nghiệm thu tuần 2 | Đức | Biên bản này | #29 | Thành viên xác nhận ở mục 5 |

## 3. Hướng dẫn chạy bản nháp

Bản đang chạy thử: `https://nasa24.webs.id.vn` (có mật khẩu, hỏi trưởng nhóm), cùng mã với main `3cff367`. Chạy trên máy cá nhân:

```bash
pip install -r requirements.txt
python scripts/install_s106_dataset.py
python -m streamlit run app.py --server.address 127.0.0.1
```

Chọn ảnh, khoanh vòng, bấm **Chấm bài**. Ảnh có nhãn đã kiểm chéo (cả 26 ảnh) sẽ có điểm; mục Thống kê hiện "chưa có" cho tới khi S2-09 xong. Lượt chấm đầu của mỗi ảnh mất khoảng 6–7 s trên máy cá nhân và khoảng 9 s trên VPS.

Phần giới thiệu ở đầu `README.md` vẫn tả trạng thái Sprint 1 ("chấm điểm và đánh giá thuộc các đầu việc tiếp theo"). Việc này thuộc S3-10.

## 4. Việc cần làm và quyết định cần chốt

Việc cần làm, xếp theo mức chặn:

1. **S2-09 (Hưng):** đây là chức năng bắt buộc duy nhất chưa có. Cài `statistics.summarize` theo hợp đồng ở S2-13 mục 1. App đã gọi sẵn, không phải sửa `app.py`.
2. **Khảo sát (Quốc Anh, Đức):** chưa có lượt người chơi thật nào. Cần ít nhất một lượt thử nhỏ (S2-07), rồi khảo sát ≥ 10 người (S3-01). Trước buổi khảo sát, làm nóng cache trên VPS (S2-13 lỗi #6).
3. **PR #26 (Tiến):** sửa theo review rồi merge. Sau đó điền số liệu vào các dấu `[CHỜ PR #26]` của báo cáo.

Quyết định cần nhóm chốt, kèm đề xuất của người lập:

| Quyết định | Đề xuất | Lý do |
|---|---|---|
| Cấu hình chọn ứng viên của game (S2-15): `score` hay `radius_balanced` | Tiến chốt trên tập điều chỉnh, ghi rõ vào `configs/default.json` | Chế độ mới chỉ tăng Recall_known tập kiểm tra từ 4/66 lên 5/66, và một ảnh giảm; đổi cấu hình thì phải chụp lại Hình 5.2 |
| Bật lọc trùng S2-05 trong pipeline | Giữ tắt | Mới kiểm trên 2 ảnh có nhãn (3/3 cặp gộp đúng). Bật lúc này sẽ đổi danh sách ứng viên của game ngay trước khảo sát |
| Ghim vị trí cho thẻ khoa học | Giữ thẻ theo vùng, ghi hạn chế trong báo cáo | Không crop nào chứa bãi đáp hay rover. Cắt crop mới cần metadata, nhãn và chia lại tập; không kịp trước 29/10. Báo cáo đã ghi hạn chế ở mục 5.5 và 5.8 |

## 5. Xác nhận của thành viên

Mỗi người ghi "Đồng ý" hoặc nêu điểm sai trong bình luận PR #29, hoặc sửa trực tiếp bảng dưới.

| Thành viên | Xác nhận dòng của mình ở mục 2 | Ý kiến về mục 4 |
|---|---|---|
| Bùi Hải Đức | Đồng ý | Người lập |
| Nguyễn Mạnh Tiến | | |
| Đinh Quang Hưng | | |
| Hoàng Quốc Anh | | |

## 6. Cập nhật ngày 28/10/2026

PR #26 và #30 đã merge. Main `958b589` đã deploy lên VPS. Trên main có 296 test Python và 6 bộ test JavaScript, đều qua, CI xanh.

| Tiêu chí | 27/10 | 28/10 | Căn cứ |
|---|---|---|---|
| Đủ bốn chức năng | Không đạt (3/4) | **Đạt**, còn hai lỗi cao | Thống kê S2-09 chạy trên main và VPS. Lỗi #10: mật độ một ảnh tính trên ứng viên máy nên giống nhau trên mọi ảnh cùng tỷ lệ. Lỗi #11: so sánh hai vùng chưa có trong app ([S2-13 mục 3](S2-13_TICH_HOP.md)) |
| Tham số đã chốt | Không đạt | Không đạt | PR #26 giữ `score` cho game, `radius_balanced` chỉ là cấu hình thử. S2-15 vẫn chưa chốt |
| Mỗi người có phần báo cáo của mình | Đạt ở mức nháp | Đạt ở mức nháp | Bảng 1.1 và mục 5.7 đã có kết quả S2-09; mục 3.6 còn chờ Hưng |
| Có danh sách lỗi | Đạt | Đạt | 11 lỗi, 3 đã sửa |
| Không còn chức năng bắt buộc chưa bắt đầu | Không đạt | **Đạt** | S2-09 đã merge |

Thay đổi trạng thái đầu việc:

- **S2-03 (Quốc Anh):** Tiến đã xác nhận trên PR #20 là đã kiểm đủ 26 overlay. Đầu việc này đủ điều kiện hoàn thành.
- **S2-06, S2-11 (Tiến):** PR #26 đã merge.
  - Trưởng nhóm chạy lại toàn bộ tập kiểm tra và ra đúng 24/24 dòng `results.csv`: NumPy `score` 4/66, `radius_balanced` 5/66, OpenCV 65/66.
  - Còn lại phần điền số vào báo cáo (S3-06).
- **S2-09 (Hưng):** PR #30 đã merge. Kết quả đếm tay hố D = 300–2.000 m:
  - Lunokhod 1: 0,254 hố/km².
  - Mare Frigoris: 0,322 hố/km².
  - Khác biệt không có ý nghĩa (p = 0,35).
  - Quốc Anh được ghi là người kiểm chéo bản đếm. PR được merge trước khi Quốc Anh tự xác nhận, nên vẫn cần Quốc Anh xác nhận trên PR #30.
- **S2-13 (Đức):** đã ghép đủ bốn chức năng. Chưa đóng: còn lỗi #10, #11 và việc kiểm lại mục 2.1 với thống kê.

Thêm một quyết định cần nhóm chốt:

| Quyết định | Đề xuất | Lý do |
|---|---|---|
| Đổi cặp so mật độ từ Van de Graaff – Mare Frigoris (S1-06) sang Lunokhod 1 – Mare Frigoris | Đồng ý (trưởng nhóm); chờ Tiến và Quốc Anh | Van de Graaff chụp lúc nắng gần đứng (27–45°). So với Mare Frigoris (61–84°) thì chênh lệch số hố chủ yếu do ánh sáng. Nếu đồng ý thì sửa mục 4.1 của báo cáo |

## 7. Cập nhật kỹ thuật S2-15 ngày 29/10/2026

Nhánh `NMTien` đã có S2-15 tại `c1fc0cc` và tích hợp main `cc31a8f` bằng merge `3159cb4`. [Biên bản S2-15](S2-15_CHOT_THAM_SO.md) chốt giữ `score`, khóa toàn bộ tham số tiền xử lý/Hough trong `configs/s215_frozen.json`, đồng bộ với cấu hình game. Lọc phân lớp và lọc trùng tiếp tục tắt. Trên 18 ảnh tuning, Recall_known = 10/174 (5,75%); quyết định không dựa trên holdout.

Phần kỹ thuật “tham số đã chốt” có cấu hình và bằng chứng để kiểm tra trên nhánh này. Các mốc 27–28/10 ở trên là lịch sử; cập nhật này không thay xác nhận của thành viên, nghiệm thu toàn bộ S2-16 hay triển khai VPS. S2-13 vẫn cần xử lý lỗi #10, #11 và kiểm lại luồng thống kê; khảo sát người chơi và xác nhận đổi cặp vùng còn theo mục 4–6.
