# S1-13 — Chạy từ đầu đến cuối

Phụ trách: **Bùi Hải Đức**. Mục tiêu tuần 1 là nối các phần đã có thành một lần chạy trên ảnh thật, kể cả các bước chưa cài. Bước chưa cài được ghi rõ là bỏ qua, không làm giả kết quả.

```text
ảnh cắt S1-06 (.npy, .json, _valid_mask.npy)
  → tiền xử lý B1–B8 S1-08 (src/preprocessing.py)
  → Hough tròn NumPy S1-07 (src/hough.py, dải r của từng ảnh)
  → lọc sáng–tối S1-11 (src/postprocessing.py)        [chưa cài → bỏ qua]
  → danh sách hố của máy, source="machine"
  → lưu run + overlay; đặt cạnh vòng người chơi S1-09 và nhãn thủ công S1-10
  → chấm điểm / Precision–Recall                       [bỏ qua: chưa có danh mục đã xác minh]
```

## Cách chạy

```bash
python scripts/install_s106_dataset.py          # một lần, giải nén 26 ảnh vào data/processed/
python scripts/run_end_to_end.py moon_ap16_m106777343r_c01
python scripts/run_end_to_end.py moon_ap16_m106777343r_c01 --voting gradient
python scripts/run_end_to_end.py --all --no-render
```

Mỗi ảnh tạo thư mục mới `outputs/e2e_<image_id>_<UTC>_<id>/` (không ghi đè lần trước, Git bỏ qua):

| File | Nội dung |
|---|---|
| `craters.json` | Hố của máy, schema `crater_set` 1.0, `source="machine"`, `confidence=null`, `votes` = số phiếu Hough |
| `metadata.json`, `params.json`, `run.json` | Metadata ảnh; tham số tiền xử lý và Hough đã dùng; commit (hậu tố `+working-tree` nếu còn sửa) |
| `summary.json` | Trạng thái từng bước, thời gian, số ứng viên, lý do bỏ qua |
| `arrays.npz` | `gray`, `edges`, `theta` để xem lại hoặc chạy lại Hough |
| `overlay.png` | Ảnh và biên B8 với vòng máy (cyan, nét đứt), người chơi (vàng), nhãn thủ công chưa kiểm chéo (đỏ cam, chấm) |
| `player.json`, `reference_unreviewed.json` | Có khi tìm thấy; chỉ để vẽ cạnh, không gộp vào kết quả máy |

Lần lưu mới nhất của người chơi cho đúng `image_id` được lấy tự động từ `outputs/player_answers/` (dùng `--player <craters.json>` hoặc `--no-player` để chọn khác). Nhãn thủ công lấy từ `data/reference_labels/` nếu có.

## Kết quả lần chạy cả bộ (15/10/2026)

Chạy `--all` trên 26 ảnh LROC thật, cấu hình mặc định (`full_circle`, `max_circles=100`). Bảng đầy đủ: [evidence/s1-13/e2e_26_anh.csv](evidence/s1-13/e2e_26_anh.csv).

- Cả 26 ảnh chạy hết chuỗi, không lỗi. Tiền xử lý dưới 0,1 s mỗi ảnh; Hough 5,0–8,2 s mỗi ảnh trên máy phát triển.
- **Cả 26 ảnh đều chạm trần 100 ứng viên.** Biên B8 của ảnh thật có khoảng 27 nghìn pixel, gồm vệt tia, đá và địa hình, không chỉ vành hố. Vì vậy danh sách máy hiện là **ứng viên thô**, nhiều vòng nhỏ r≈5 px nằm trên nhiễu. Đây là lý do cần S1-11 (sáng–tối, lọc trùng) và chọn tham số ở tuần 2. Không đọc số 100 là số hố.
- Ảnh demo `moon_ap16_m106777343r_c01`: [overlay](evidence/s1-13/moon_ap16_m106777343r_c01_overlay.png), [summary](evidence/s1-13/moon_ap16_m106777343r_c01_summary.json), [params](evidence/s1-13/moon_ap16_m106777343r_c01_params.json). 4 nhãn thủ công S1-10 chưa kiểm chéo được vẽ cạnh để nhìn bằng mắt, không dùng để chấm.
- Chấm điểm và Precision/Recall: **bỏ qua** trên cả 26 ảnh vì `reference_status="unavailable"`.

## Kiểm thử

`tests/test_pipeline.py` chạy cả chuỗi trên một cảnh giả lập có hai đĩa biết trước (không phải ảnh NASA), kiểm tra:

- đủ file đầu ra, `craters.json` đúng hợp đồng và có vòng gần mỗi đĩa (sai số ≤ 2 px);
- bước lọc S1-11 và chấm điểm được báo `skipped` kèm lý do;
- vòng người chơi chỉ được vẽ cạnh, không lẫn vào danh sách máy; chọn đúng lần lưu mới nhất của đúng ảnh;
- file vẽ cạnh sai `source` bị từ chối trước khi tạo thư mục run.

## Bàn giao

- **Hưng (S1-11):** khi `filter_candidates` được cài, pipeline tự gọi và ghi `postprocess.status="applied"`; đầu vào là danh sách vòng máy, ảnh `gray` B3, metadata (có hướng nắng).
- **Anh/Tiến (S1-10):** sau khi nhãn được kiểm chéo, đổi nguồn thành `reviewed by <tên>`. Bước chấm vẫn cần `scoring.py`/`evaluation.py` (ghép một–một, sai lệch tâm ≤ 0,5 bán kính).
- **Giao diện:** S1-09 lưu câu trả lời người chơi đúng định dạng pipeline đọc; tuần 2 nối nút "chạy máy" của giao diện vào `src/pipeline.run_end_to_end`.
