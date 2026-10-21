# S1-11 — Thử kiểm tra vùng sáng–tối theo hướng nắng

Phụ trách: Đinh Quang Hưng · Phụ thuộc: S1-06 (ảnh, metadata hướng nắng), S1-08 (tiền xử lý) · Mã: [src/postprocessing.py](../src/postprocessing.py)

**Đầu ra:** bản thử chấm mức phù hợp sáng–tối cho từng ứng viên hố.
**Phạm vi:** chỉ chấm điểm, **không xóa vòng nào**. Ngưỡng loại bỏ do S2-02 quyết định khi đã có số liệu.

## 1. Cơ sở vật lý (S1-04 mục 6.3)

Hố là chỗ lõm. Thành hố phía gần Mặt Trời quay lưng với nắng nên tối, còn thành phía xa hướng về nắng nên sáng. Gò nổi cho kết quả ngược lại. Một vòng đặt vào chỗ không có hố thì không có quy luật nào.

## 2. Cách chấm (tự viết bằng NumPy)

1. Vector chỉ về phía Mặt Trời trong ảnh (S1-04 mục 6.1): `u = (sin φ, −cos φ)`, với `φ = azimuth_deg + north_angle_deg`.
2. Lấy các pixel hợp lệ trong đĩa bán kính r quanh tâm c. Vị trí của mỗi pixel dọc hướng ra xa Mặt Trời là `t = −((p − c)·u) / r`.
3. **Trừ độ dốc địa hình:** khớp mặt phẳng độ sáng `a + b·x + c·y` (bình phương tối thiểu) trên vành khuyên ngoài [1,3r; 2r], rồi trừ mặt phẳng đó khỏi pixel trong đĩa. Vành khuyên bắt đầu từ 1,3r để bỏ qua phần vành nổi của hố.
4. **score** = hệ số tương quan Pearson giữa độ sáng đã trừ dốc và `t`, trong [−1, 1]. **score_raw** là cùng phép tính nhưng không trừ dốc.
5. **Chỉ kết luận khi hai cách cùng nhãn.** Khác nhãn thì gán `unclear` và ghi lý do. Quy tắc này cần thiết vì mặt phẳng không mô tả được mép bóng sắc: khi mép bóng nằm sát vòng, trừ dốc một mình có thể *tạo ra* quy luật sáng–tối giả (xem mục 7).

| score | Nhãn `shading.status` | Ý nghĩa |
|---|---|---|
| ≥ +ngưỡng (cả hai cách) | `consistent` | Sáng dần về phía xa Mặt Trời, khớp với hố lõm |
| ≤ −ngưỡng (cả hai cách) | `inverted` | Ngược: có thể là gò nổi, mép bóng trong vòng, hoặc vòng sai |
| giữa hai ngưỡng, hoặc hai cách khác nhãn | `unclear` | Không đủ quy luật, hoặc kết quả do địa hình quyết định |
| — | `not_checked` | Không chấm; trường `reason` ghi lý do |

- Ngưỡng ban đầu: 0,15 cho `measured`, 0,25 cho `side_only`. Ngưỡng của `side_only` nới hơn vì chỉ biết hướng Đông/Tây (S1-04 mục 6.2).
- Tương quan không phụ thuộc độ sáng hay độ tương phản chung của ảnh; unit test đã kiểm tra.
- Vòng có vành ngoài phần lớn nằm trong nodata (dưới 50% hợp lệ) sẽ là `not_checked`, vì không ước lượng được độ dốc.
- Mỗi vòng giữ nguyên các trường theo hợp đồng S1-05 và có thêm `shading = {status, score, score_raw, reason}`.
- `pipeline.py` (S1-13) gọi bước này qua `filter_candidates()`.

## 3. Khi nào hướng nắng "có căn cứ"

Một ảnh chỉ được chấm khi đạt **cả ba** điều kiện sau:

1. **Có hướng nắng từ nguồn.** Metadata có `sun.quality` là `measured` hoặc `side_only` kèm `azimuth_deg`, lấy từ trang LROC. Trường hợp khác: phía nắng ứng viên (`side_candidate`) đã được xác nhận bằng mắt.
2. **Góc tới ≥ 30°.** Nắng gần đứng thì bóng quá ngắn (S1-04 mục 6.2). Ngưỡng 30° là đề xuất ban đầu.
3. **Đã kiểm tra bằng mắt trên hố tham chiếu** (S1-04 mục 6.3), ghi trong [data/s111_sun_checks.json](../data/s111_sun_checks.json). Bước này kiểm tra luôn `north_up`: nếu ảnh bị lật thì mọi kết luận sẽ đảo ngược.

Căn cứ của từng ảnh được ghi vào trường `sun_basis` trong `report.json`.

## 4. Trường hợp không có metadata đủ tin cậy

Tình trạng bộ 26 ảnh S1-06 **sau khi** điền phiếu kiểm tra bằng mắt (18/10/2026). Chi tiết từng ảnh ở [docs/evidence/s1-11/s111_tong_hop.csv](evidence/s1-11/s111_tong_hop.csv).

| Nhóm ảnh | Số ảnh | Kết quả |
|---|---|---|
| STT 8, 9, 13, 14, 18 (nắng Tây, góc tới 80–88°) | 5 | **Được chấm**: `side_only` 270° theo LROC, đã kiểm tra hướng Bắc/nắng bằng mắt |
| STT 11, 15, 16 (nắng Đông, góc tới 42–65°) | 3 | **Được chấm**: phía Đông được xác nhận bằng mắt, dùng `side_only` 90° |
| STT 10 (28,38°), STT 17 (7,64°) | 3 | Không chấm: góc tới < 30°, nắng gần đứng |
| Mosaic STT 1–6 | 15 | Không chấm: `sun.quality=none`, trang nguồn không ghi hướng nắng (S1-02) |

Như vậy **8/26 ảnh** được chấm, **18 ảnh** là `not_checked` kèm lý do. Các vòng trong ảnh không chấm vẫn được giữ, không bị loại và không bị coi là sai. Mỗi lần bỏ qua đều được ghi log (`logging.WARNING`).

## 5. Kiểm tra hướng nắng bằng mắt

Quốc Anh (S1-06) giao việc này cho S1-11.

```powershell
python scripts/s111_sun_check_sheet.py
```

Script tạo `docs/evidence/s1-11/sun_check_<image_id>.png` cho 8 ảnh: ảnh toàn cảnh có mũi tên chỉ về phía Mặt Trời và 6 ứng viên phóng to. Ứng viên được chọn theo số phiếu Hough; số phiếu không dùng độ sáng hai nửa hố nên tránh được lập luận vòng tròn.

Với mỗi hố nhìn rõ, trả lời: **phía tối của thành hố có nằm về phía mũi tên không?** Sau đó điền vào `data/s111_sun_checks.json`:

- `dark_side` của từng hố: `toward_sun`, `away` hoặc `unclear`.
- `verdict` của ảnh:
  - `consistent`: các hố nhìn rõ đều `toward_sun`;
  - `inverted`: các hố nhìn rõ đều `away`. Khi đó báo Quốc Anh, vì hướng nắng hoặc hướng Bắc đang sai;
  - `unclear`: không đủ hố nhìn rõ.
- `checked_by` và `checked_on` (YYYY-MM-DD).
- Nếu không ứng viên nào là hố rõ: ghi `manual_craters = [{"x":…, "y":…, "r":…}]` rồi chạy lại script để có phiếu mới.

Hố tham chiếu **không được dùng** làm ví dụ đánh giá. `run_shading_check.py` vẽ chúng bằng nét chấm và loại khỏi `examples.png`.

## 6. Chạy

```powershell
python scripts/run_shading_check.py moon_ap16_m132732855l_c01     # một ảnh
python scripts/run_shading_check.py --all --no-render             # bảng tổng hợp 26 ảnh
python scripts/run_shading_check.py <image_id> --preview          # xem trước khi chưa điền phiếu
```

Lưu ý về `--preview`: chế độ này bỏ điều kiện 3. Ảnh kết quả có chữ đỏ "XEM TRƯỚC", và `report.json` ghi `"preview": true`. Không dùng kết quả xem trước làm minh chứng.

Mỗi lần chạy lưu `outputs/s111_<image_id>_<UTC>/` gồm `craters.json`, `report.json`, `candidates.csv`, `overlay.png` và `examples.png`.

## 7. Ví dụ hố đúng và ứng viên sai

**Cảnh giả lập có đáp án** ([tests/test_postprocessing.py](../tests/test_postprocessing.py)), nắng Tây, góc tới 70°:

| Trường hợp | Không trừ dốc | Có trừ dốc + quy tắc cùng nhãn |
|---|---|---|
| 3 hố lõm | +0,98 → hợp | +0,98 → **hợp** |
| Gò nổi | −0,98 → ngược | −0,98 → **ngược** |
| Vòng chỗ phẳng, nền phẳng | −0,01 → không rõ | −0,03 → **không rõ** |
| Vòng chỗ phẳng, dốc sáng +0,001/px | **+0,48 → hợp (sai)** | −0,03 → **không rõ** |
| Vòng chỗ phẳng, dốc sáng −0,001/px | **−0,50 → ngược (sai)** | −0,03 → **không rõ** |
| Mép bóng sắc sát mép vòng | −0,01 → không rõ | trừ dốc +0,90, gốc −0,01 → hai cách khác nhau → **không rõ** |
| Mép bóng cắt qua tâm vòng | −0,85 → ngược | −0,66 → **ngược** (đúng: không phải hố) |

Ghi nhầm nắng Đông thay vì Tây thì cả 3 hố thật đều bị chấm "ngược". Đây là lý do bắt buộc kiểm tra bằng mắt.

**Ảnh thật, chế độ xem trước** (chưa kiểm tra bằng mắt, chỉ để so sánh trước/sau khi sửa):

| Ảnh | Không trừ dốc (hợp / ngược / không rõ) | Có trừ dốc | Số vòng đổi nhãn |
|---|---|---|---|
| STT 13 | 31 / 29 / 40 | 28 / 25 / 47 | 7, đều sang "không rõ" |
| STT 14 | 32 / 28 / 40 | 28 / 24 / 48 | 8 |
| STT 8 | 33 / 29 / 38 | 26 / 26 / 48 | 10 |
| STT 18 | 33 / 25 / 42 | 24 / 22 / 54 | 12 |
| STT 9 | 29 / 29 / 42 | 27 / 24 / 49 | 7 |

Không vòng nào bị đảo từ hợp sang ngược hay ngược lại. Mỗi ảnh có 100 ứng viên Hough (chạm `max_circles`), nhiều vòng không phải hố.

**Ví dụ chính thức trên ảnh thật: STT 13** (nắng Tây, góc tới 87,7°, đã kiểm tra bằng mắt). Bộ minh chứng ở [docs/evidence/s1-11/vi_du_stt13/](evidence/s1-11/vi_du_stt13/), gồm `examples.png`, `overlay.png`, `report.json` (có `visual_verdict` từng vòng) và `candidates.csv`. Kết quả: 100 ứng viên Hough, gồm 28 hợp, 25 ngược, 47 không rõ; 9 vòng trùng hố tham chiếu bị loại khỏi phần ví dụ.

| Vòng | Máy chấm | Nhìn bằng mắt |
|---|---|---|
| **M9** | hợp (+0,75) | **Hố đúng**: tối phía Tây, vành sáng lưỡi liềm phía Đông |
| M11, M3, M66 | hợp (+0,69 đến +0,74) | Không phải hố, chỉ là địa hình gồ ghề |
| **M51, M92, M71, M60** | ngược (−0,72 đến −0,79) | **Ứng viên sai**: mép bóng, ranh giới bóng hoặc địa hình nhiễu. Máy đánh dấu đúng là đáng ngờ |

Rút ra:
- Trên ví dụ này, cả 4 vòng điểm thấp nhất ("ngược") đều không phải hố. Đây mới là **4 vòng do một người nhìn**, chưa đủ để kết luận nhãn "ngược" đáng tin.
- Nhãn **"hợp" chưa đủ để khẳng định là hố**: 3/4 vòng điểm cao nhất không phải hố.
- So với vòng đặt ngẫu nhiên, vòng Hough nhiều hơn ở **cả hai** nhãn, gần như đối xứng. Đo lại ngày 21/10/2026: 500 vòng ngẫu nhiên mỗi ảnh (seed 0, bán kính lấy từ chính các vòng Hough của ảnh, tâm đều trong ảnh) trên STT 8, 13, 16, 18:

  | Ảnh | Hough: hợp / ngược | Ngẫu nhiên: hợp / ngược |
  |---|---|---|
  | STT 8 | 26% / 26% | 12% / 18% |
  | STT 13 | 28% / 25% | 12% / 18% |
  | STT 16 | 17% / 27% | 17% / 17% |
  | STT 18 | 24% / 22% | 16% / 16% |

  Vậy điểm số hiện chủ yếu cho biết vòng nằm trên vùng có dải sáng–tối rõ, **chưa tách được hố thật với ứng viên sai**.
- Vì vậy S1-11 hiện chỉ **chấm thêm thông tin** cho từng vòng. Muốn dùng để loại ứng viên (S2-02) cần nhãn đã kiểm chéo để đo lại; không dùng làm đáp án chấm người chơi.
- 8 phiếu kiểm tra hướng nắng bằng mắt hiện do một người kiểm. Nên nhờ người thứ hai kiểm chéo STT 11, 15, 16 trước khi chép hướng nắng sang `crops.json`. Phiếu chỉ xác nhận hướng nắng trong hệ tọa độ ảnh, với giả định `north_angle_deg = 0`.

## 8. Hạn chế đã biết

- **Mép bóng sắc** không trừ được bằng mặt phẳng. Quy tắc "hai cách phải cùng nhãn" chặn được trường hợp mép bóng sát vòng, nhưng vòng có mép bóng cắt qua bên trong vẫn bị chấm "ngược". Nhãn này đúng về hướng (vòng đó không phải hố lõm sáng–tối bình thường), nhưng không phân biệt được với gò nổi.
- **Vành ngoài chứa hố khác.** Mặt phẳng có thể bị kéo lệch khi hố lân cận nằm trong [1,3r; 2r].
- **Ứng viên Hough nhiễu.** S1-11 không sửa được; đây là việc của S1-07/S2-15.
- **`side_only`** chỉ cho chiều Đông–Tây. Phương vị thật lệch Δ thì độ tương phản giảm khoảng cos Δ, nhưng dấu vẫn đúng khi Δ < 90°.
- **Ảnh browse 8 bit** (LROC RDR SIS mục 3.2) chỉ dùng cho demo xử lý ảnh.
- **STT 16 cần xem lại khi có thêm căn cứ.** Phía Đông được xác nhận bằng mắt chỉ dựa trên 1 hố lớn và 1 hố nhỏ, và đây là ảnh duy nhất có số vòng "ngược" (27) nhiều hơn "hợp" (17). Các ảnh khác có tỉ lệ khoảng 1:1. Số liệu này chưa đủ để kết luận phía Đông sai, nhưng nên kiểm tra lại bằng nhãn PDS (phương vị Mặt Trời) nếu có.
- **"Hợp" không có nghĩa là hố.** Địa hình gồ ghề đôi khi tình cờ có quy luật sáng–tối giống hố (mục 7). Không dùng S1-11 một mình để chấm người chơi.
- Các ngưỡng 0,15, 0,25, 30° và vành khuyên [1,3r; 2r] là giá trị ban đầu, cần chỉnh trên tập điều chỉnh.
