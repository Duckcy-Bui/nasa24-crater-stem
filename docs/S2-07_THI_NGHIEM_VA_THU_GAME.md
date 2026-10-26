# S2-07 — Ba thí nghiệm và thử nhỏ trò chơi

**Phụ trách:** Hoàng Quốc Anh · **Phối hợp:** Bùi Hải Đức  
**Đầu ra:** `scripts/s207_experiments.py`, phiếu thử nhỏ dưới đây, và `docs/evidence/s2-07/results.json` khi chạy.

## 1. Nguyên tắc đo và giới hạn

- Nhãn 26 ảnh đã ghi `reviewed by Nguyen Manh Tien`, nhưng là **nhãn thưa**. Mọi bảng máy chỉ báo `Recall_known`; không suy Precision hoặc F1 toàn ảnh.
- Chỉ chọn tham số trên **tuning**. Holdout dùng một lần để báo cáo, không quay lại chỉnh ngưỡng.
- Cả 8 holdout là mosaic 20 m/px và `sun.quality=none`; S1-11 trên holdout luôn `not_checked`. Vì vậy thí nghiệm 1 không có phép đo ngoài mẫu cho tác động của sáng–tối. Đây là giới hạn đã chốt ở [S2-03](S2-03_TAP_DIEU_CHINH.md).
- S1-11 hiện chỉ gắn nhãn `shading`, không tự xóa vòng. Không được gọi số vòng giảm sau S1-11 là hiệu quả nếu chưa gọi rõ một quy tắc lọc độc lập.

## 2. Kịch bản ba thí nghiệm

| TN | Câu hỏi | Ảnh và split | Can thiệp | Chỉ số báo cáo | Quy tắc diễn giải |
|---|---|---|---|---|---|
| E1 | S1-11 thay đổi gì so với Hough cơ bản? | Apollo 16 tuning có hướng nắng dùng được | Hough thô ↔ cùng danh sách vòng, thêm nhãn `shading` | số ứng viên, phân bố `consistent/inverted/unclear/not_checked`, `Recall_known` | Hai Recall phải bằng nhau vì S1-11 không lọc. `inverted` chỉ là kiểm tra rủi ro; không là cấu hình chính vì S2-02 từng mất hố thật. Holdout ghi không đánh giá được. |
| E2 | Tham số Hough nhạy thế nào? | các ảnh tuning đại diện; sau khi chốt mới chạy holdout | `min_vote_ratio=0.30/0.35/0.40`, `radius_step=1/2`; mỗi lượt chỉ đổi một tham số | số vòng, thời gian Hough, `Recall_known` | Chọn trước trên tuning: không giảm Recall_known và giảm vòng/thời gian theo mục tiêu nêu trước. Holdout chỉ báo cáo, không chọn lại. |
| E3 | Hệ thống xử lý ảnh khó ra sao? | bóng mạnh: STT 13; nắng gần đứng: STT 17; mosaic mare: Mare Frigoris | gắn lớp S2-02; thử bỏ `texture`; thử S2-05 lọc trùng | số lớp, số vòng giữ/bỏ, Recall_known, lý do từng vòng bị bỏ | Đây là chẩn đoán lỗi. `remove_texture` và dedupe được báo cáo riêng, không tự bật trong pipeline khi chưa có quyết định nhóm. |

Chạy tái tạo (khi `data/processed/` đã giải nén):

```powershell
python scripts/s207_experiments.py --write
```

Kết quả mặc định gồm ba ảnh Apollo 16 tuning và hai ảnh holdout mosaic. Không commit `results.json` nếu chưa ghi rõ máy chạy, commit mã, ngày chạy và việc holdout chưa dùng chọn tham số.

### Chạy kiểm tra kỹ thuật ngày 26/10/2026

Đã chạy một ca tái tạo trên `moon_ap16_m109134835l_c01`; dữ liệu đầy đủ ở [`evidence/s2-07/results.json`](evidence/s2-07/results.json). Ảnh này có góc tới 7,64°, nên S1-11 ghi 100/100 `not_checked` và E1 có trạng thái `not_evaluable_no_usable_sun` — đúng quy tắc, không phải kết quả so sánh sáng–tối. Cả bốn biến thể E2 đều chạm trần 100 ứng viên và `Recall_known = 0/10`; vì vậy **chưa chọn tham số** từ ca này, dù `radius_step=2` nhanh hơn. Đây là smoke test của luồng và giới hạn, không phải kết quả cuối của ba thí nghiệm.

## 3. Phiếu thử nhỏ trò chơi (1–2 người)

Mục tiêu thử nhỏ là sửa thao tác và câu chữ, **không** là khảo sát hiệu quả hay kết quả thống kê. Dùng một ảnh có nhãn reviewed, ưu tiên `moon_ap16_m106777343r_c01`; lưu mã người thử thay vì tên.

| Mã người thử | Thiết bị/trình duyệt | Bắt đầu–kết thúc | Ảnh | Lưu được JSON? | Điểm Recall hiện? | Lỗi/chỗ vướng | Sửa đề xuất |
|---|---|---|---|---|---|---|---|
| P01 |  |  | `moon_ap16_m106777343r_c01` | Có / Không | Có / Không |  |  |
| P02 |  |  | `moon_ap16_m106777343r_c01` | Có / Không | Có / Không |  |  |

Kịch bản điều phối đọc nguyên văn:

> Bạn sẽ khoanh những vùng bạn cho là hố trên ảnh Mặt Trăng. Vòng của máy chỉ là ứng viên, không phải đáp án. Kéo từ tâm ra vành để tạo vòng; bạn có thể chọn/sửa/xóa vòng. Hãy lưu câu trả lời, sau đó bấm **Chấm bài**. Chúng tôi đang thử giao diện, nên hãy nói ngay khi thao tác hoặc câu chữ gây khó hiểu.

Sau lượt chơi, hỏi ngắn:

1. Bạn có biết cách thêm, sửa, xóa và lưu một vòng không? Chỗ nào không rõ?
2. Bạn hiểu câu “vòng máy là ứng viên” thế nào?
3. Kết quả chấm có khiến bạn hiểu nhầm rằng mọi vòng ngoài nhãn là sai không?
4. Mất bao lâu từ mở ảnh đến lưu/chấm bài? Có lỗi hay độ trễ nào?

## 4. Danh sách lỗi thử game

Ghi từng lỗi theo mẫu dưới đây; không ghi “không có lỗi” nếu chưa có người thử.

| ID | Bước tái hiện | Kỳ vọng | Thực tế | Mức độ | Bằng chứng | Trạng thái |
|---|---|---|---|---|---|---|
| GP-01 | Chọn ảnh có nhãn sparse reviewed, khoanh 1 vòng khớp và bấm Chấm bài | điểm là Recall của nhãn đã biết; vòng không khớp không bị gọi là sai | Chưa thử người dùng | Cao | `score.json` + ảnh chụp | Mở |
| GP-02 | Tạo/sửa/xóa vòng rồi lưu và tải lại JSON | tọa độ và bán kính giữ nguyên; không mất vòng | Chưa thử người dùng | Cao | JSON trước/sau | Mở |
| GP-03 | Chấm bài trên ảnh holdout 20 m/px | không hứa hẹn S1-11 đã lọc; hiển thị rõ `not_checked` nếu có | Chưa thử người dùng | Trung bình | `summary.json` | Mở |

Sau thử nhỏ, bổ sung thời lượng trung vị và các lỗi đã xác nhận vào [S1-16_KHAO_SAT.md](S1-16_KHAO_SAT.md); chỉ khi đó mới chốt lịch, thời lượng và hướng chạy cho khảo sát S2-14/S3-01.
