# S2-01 — Hough NumPy, dải bán kính và thời gian chạy

Phạm vi: tối ưu Hough và lưu cấu hình/thời gian để tái tạo. Không triển khai S2-05 (lọc trùng), S2-06 (đối chiếu thư viện) hoặc thay quy tắc chấm điểm.

## Thay đổi

`src/hough.py::_accumulate` trước đây cấp phát `bincount` dài H×W cho mỗi lô điểm biên. Các điểm biên lấy theo thứ tự hàng nên một lô thường chỉ bỏ phiếu vào một dải nhỏ. Bản S2-01 dịch các chỉ số hợp lệ về `first`, đếm trong `[first, stop)` rồi cộng vào đúng lát accumulator. Không thay đổi bất kỳ phiếu nguyên, cách làm tròn, ngưỡng, NMS, ID hay x/y/r nào. Lô không có tâm hợp lệ được bỏ qua an toàn.

Accumulator vẫn là int32 H×W cho từng bán kính; không giữ khối 3D. Chi phí histogram mỗi lô giảm từ H×W xuống độ dài khoảng chỉ số có phiếu. Với ảnh phân tán hoặc bán kính lớn, lợi ích giảm; cần đọc số đo thực tế thay vì suy ra hệ số tăng tốc từ công thức.

Giữ `full_circle`, bước bán kính 1 và mọi ngưỡng mặc định. Gradient vẫn là tùy chọn hiện có. Không thu hẹp dải vật lý để tăng tốc khi chưa có nhãn đủ căn cứ.

## Chạy cấu hình đã lưu

Từ gốc repo trên PowerShell:

```powershell
.\.venv\Scripts\python.exe -B scripts/run_end_to_end.py moon_ap16_m106777343r_c01 --hough-config configs/s201_hough.json --no-player
```

`--hough-config` nhận dict Hough hoặc object có khóa `hough`. Các cờ `--voting` và `--max-circles` ghi đè file chỉ khi được truyền rõ. Không có file/cờ thì hành vi mặc định giữ nguyên. Khóa lạ, JSON hỏng, giá trị không hợp lệ đều bị từ chối trước khi chạy ảnh.

Cấu hình `configs/s201_hough.json` ghi đầy đủ tham số. Muốn khảo sát dải khác, sao chép sang config mới rồi đổi `r_min_limit_px`, `r_max_limit_px` hoặc `radius_step_px`; luôn giữ giới hạn 5–128. Không sửa metadata nguồn.

Dải chạy là giao giữa metadata và giới hạn config. Metadata dùng r=D/(2s), làm tròn ceil/floor theo hợp đồng hiện có. Dải rỗng báo lỗi. `params.json` và `summary.json` nay có `radius_search`: dải metadata, dải kẹp, bước, số mức và bán kính cuối thực quét. Ví dụ [12,29], step=4 quét 12,16,20,24,28, không ghi nhầm 29 là bán kính đã quét.

## Đo trước/sau cùng máy

```powershell
.\.venv\Scripts\python.exe -B scripts/benchmark_s201.py --images moon_ap16_m106777343r_c01 moon_ap16_m132732855l_c01 moon_ap15_hia_c01 --repeats 5 --warmups 1
```

Đầu vào cần nằm trong `data/processed/`. Nếu chưa có, dùng `scripts/install_s106_dataset.py` để xác minh/giải nén bundle ngoại tuyến. Script benchmark không chỉnh dữ liệu nguồn.

Baseline cố định là commit `eb8278cc82901cc28dbbc6509b0ff0b6bfefa0cc`; cần lịch sử Git chứa commit này. `--baseline-ref` cho phép chọn commit khác. Script lưu cả nguồn baseline vào run và ghi SHA-256. Bản tối ưu và baseline dùng cùng tham số đầy đủ, cùng edges/theta đã tiền xử lý và cùng toàn dải metadata. Mỗi bản warm-up rồi đo 5 lần, đảo thứ tự giữa các lần.

Run mới trong `outputs/s201/` gồm `report.json`, `timings.csv`, `config.json`, `baseline_hough.py`, các `*_inputs.npz`. Báo cáo có thời gian từng lần/median/min/max, môi trường CPU/Python/NumPy, hash mã/ảnh/metadata/mask, danh sách r đã quét, số vòng/chạm trần và kết quả so đầu ra. Thời gian chỉ gồm Hough, không I/O, tiền xử lý, sáng–tối hoặc render. Tiền xử lý đo một lần và ghi riêng.

Script so toàn bộ danh sách vòng gồm phiếu, tâm, bán kính và thứ tự ở mọi lần đo. Sai khác hoặc không ổn định làm trạng thái failed và exit code 1. Lỗi giữa chừng ghi status=error; không coi thư mục run đang chạy là minh chứng hoàn thành.

Benchmark dùng ảnh thật chỉ để đo hiệu năng và tương đương đầu ra; không dùng nhãn để chỉnh ngưỡng hoặc tính P/R. Không thay thế manifest tách tập của S2-03 hay đánh giá tuần 3.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p 'test_s201.py' -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -p 'test_hough*.py' -v
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
```

Test S2-01 kiểm phiếu bằng vòng lặp scalar độc lập trên nhiều kích thước/batch, lô rỗng/ngoài ảnh, config/ưu tiên CLI và lưu lưới r thưa chính xác. Không đặt ngưỡng thời gian trong unit test vì tải máy thay đổi.

Kết quả đo thực tế và giới hạn xem `docs/evidence/s2-01/` sau lần chạy nghiệm thu. Vẫn có thể chạm trần 100 vòng và còn vòng giả; S2-01 này tăng tốc mà giữ nguyên kết quả, chưa xử lý các vấn đề thuộc S2-02/S2-05.

## Kết quả đo ngày 24/10/2026

Ba ảnh thật, mỗi bản đo 5 lần sau warm-up: tăng tốc 2,10–2,40 lần trên toàn dải metadata; đầu ra giống hệt ở mọi lần đo. Xem [bảng số liệu và giới hạn](evidence/s2-01/README.md), [CSV](evidence/s2-01/timings.csv), [báo cáo JSON](evidence/s2-01/report.json).

Trên Windows, bật UTF-8 cho cả tiến trình con trước khi chạy bộ test cũ: `$env:PYTHONUTF8 = "1"`. Venv cần đủ dependency trong `requirements-test.txt`. Lần kiểm tra ban đầu thiếu thư viện và đọc dữ liệu bằng cp1252; log đó đã bỏ vì không phải minh chứng. Không sửa test hoặc module của task khác để xử lý điều kiện môi trường này.

Kết quả kiểm tra cuối: **209/209 test Python đạt**, gồm **5 test S2-01** và **18 test Hough/ví dụ hiện có**. Log: [regression.log](evidence/s2-01/regression.log).
