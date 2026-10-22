# S2-04 — Chấm điểm người chơi với máy và danh mục

Phụ trách: Bùi Hải Đức; phối hợp: Hoàng Quốc Anh. Mã: `src/matching.py`, `src/scoring.py`; nối vào `src/pipeline.py`. Test: `tests/test_scoring.py`, `tests/test_pipeline.py`.

## 1. Ghép hố một–một

Một vòng của người chơi khớp một hố tham chiếu khi khoảng cách hai tâm ≤ 0,5 × bán kính hố tham chiếu (`configs/default.json`, mục `evaluation`). Mỗi vòng và mỗi hố dùng tối đa một lần, nên hai vòng khoanh cùng một hố chỉ được tính một lần.

Trong các cách ghép có nhiều cặp nhất, `match_one_to_one` chọn cách có tổng khoảng cách tâm (chia bán kính) nhỏ nhất, bằng thuật toán Hungary viết bằng NumPy. Cách ghép tham lam "lấy cặp gần nhất trước" có thể bỏ mất cặp: `tests/test_scoring.py` có ca như vậy, và so kết quả với vét cạn trên 150 cảnh ngẫu nhiên.

## 2. Hai nguồn so sánh, không trộn lẫn

| So với | Khi nào | Kết quả | Điểm |
|---|---|---|---|
| Máy (ứng viên Hough) | Luôn có khi đã chạy máy | Số vòng trùng, vòng chỉ người chơi có, vòng chỉ máy có | Không có. Máy không phải đáp án |
| Danh mục, nhãn chưa kiểm chéo | `reference_source` không có "reviewed by" | `status = unavailable` kèm lý do | Không có |
| Danh mục, nhãn thưa đã kiểm chéo (mặc định) | `reviewed by <tên>` | Hố tìm đúng, hố bỏ sót; vòng ngoài nhãn **không** bị tính là khoanh sai | Tỉ lệ hố đã gán nhãn được tìm thấy × 100 |
| Danh mục, nhãn đầy đủ | thêm `catalogue_coverage = "complete"` (S2-03 xác nhận) | Thêm khoanh sai và precision | F1 × 100 |

Hố có `uncertain` trong `crater_id` (quy ước S1-10) bị loại khỏi phần chấm.

## 3. Trạng thái hiện tại

Bộ ảnh chưa có nhãn nào đã kiểm chéo: 4 nhãn S1-10 trên `moon_ap16_m106777343r_c01` vẫn ghi `unreviewed`. Vì vậy hiện mọi lượt chơi chỉ có phần so với máy. Khi Tiến kiểm chéo xong và đổi nguồn thành `reviewed by <tên>`, cùng mã này tự chấm theo danh mục, không cần sửa code.

Chạy thử 22/10/2026 trên `moon_ap16_m106777343r_c01` với 2 vòng người chơi: 100 ứng viên máy, 1 vòng trùng máy, phần danh mục `unavailable` vì nhãn chưa kiểm chéo.

```bash
python scripts/run_end_to_end.py moon_ap16_m106777343r_c01   # ghi score.json khi có câu trả lời người chơi
python -m unittest tests.test_scoring tests.test_pipeline
```

## 4. Việc sau

- S2-08: hiện kết quả này trong giao diện và lưu từng lượt chấm.
- S3-02 (Tiến): `evaluation.py` tính Precision/Recall của máy có thể dùng lại `match_one_to_one`.
