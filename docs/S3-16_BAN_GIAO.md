# S3-16 — Đóng gói và bàn giao NASA 24 · Nhóm 2

Cập nhật 01/11/2026, đối chiếu main `94c17ff`. Đức phụ trách bàn giao; từng thành viên tự xác nhận nội dung của mình. Gói thử cũ từ `c466c2d` chỉ là bằng chứng đóng gói tại mốc đó, chưa phải bộ nộp cuối.

## 1. Trạng thái main

Mã nền đối chiếu: `94c17ffbdced8178083d9092cd0d1207e1b62226`. Đã có bản rút gọn báo cáo; các PR #33–#36 dưới đây là mốc tích hợp trước đó:

| PR | Nội dung đã vào main | Phần còn cần chủ nội dung chốt |
|---|---|---|
| [#33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33) | S2-12: Chương 3 về sáng–tối, lọc trùng, thống kê; cập nhật mục 3.3.5 và 4.1 | Hưng, Tiến, Quốc Anh đọc lại phần liên quan; rút gọn và kiểm lại số liệu/nguồn |
| [#34](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/34) | S2-13/S3-04: cảnh báo chạm trần, so sánh đếm tay hai vùng, sửa nút bán kính và nhãn điểm | Theo dõi A-06 và hợp đồng câu cảnh báo tại [S2-13 mục 3.2–3.4](S2-13_TICH_HOP.md) |
| [#35](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/35) | S3-08: quyết định bỏ khảo sát, rút Chương 1/5, Phụ lục và cập nhật biên bản S2-16 | Chương 2–4, số trang, dấu chờ và xác nhận thành viên vẫn cần hoàn thiện |
| [#36](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/36) | Hồ sơ Linux S3-10 và tài liệu bàn giao S3-16 | Chốt sản phẩm còn thiếu và gói cuối |

Cập nhật 02/11/2026: PR #38 (S3-05), #42 (S3-16) và #43 (báo cáo) đã merge vào main.

Mốc triển khai do trưởng nhóm xác nhận trước đó: `c466c2d` ngày 01/11. Bản demo: [https://nasa24.webs.id.vn](https://nasa24.webs.id.vn), có mật khẩu: **hỏi trưởng nhóm**. Chưa kiểm lại commit đang chạy trên VPS trong lượt đối chiếu này.

**Trưởng nhóm đã nghiệm thu S3-10**, căn cứ [bình luận PR #31](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/31#issuecomment-6552877683) và [hồ sơ Linux trong repo](evidence/s3-10/kiem_doc_lap_linux/README.md). Người kiểm độc lập đã đối chiếu 25/25 nhóm, 9 bảng CSV/102 dòng riêng, 0 giá trị lệch; đủ 62 artifact lượt gốc đúng hash. Sheet J49 do người điều phối cập nhật; không ghi URL hoặc sửa bảng trong lượt này. Giữ giới hạn NPZ cũ và mã nền `13394de` của bằng chứng lịch sử.

## 2. Đối chiếu tài liệu học phần

Đã đọc **Quy định BTL Xử lý ảnh** (Q) và **Danh sách đề tài NASA, Đề 24** (N24), do trưởng nhóm cung cấp ngày 01/11. Hai tài liệu học phần được giữ ngoài repo public; ở đây chỉ tóm tắt yêu cầu và dẫn tên/mục, không chép tài liệu gốc. [Khóa `debai_nasa`](bao_cao/tai_lieu.bib) là bản ghi nguồn đã có trong báo cáo.

**Đạt** chỉ áp dụng cho phạm vi có bằng chứng của từng dòng; **Lệch** là còn thiếu hoặc khác yêu cầu; **Chưa biết** là chưa có bản cuối hoặc kết quả kiểm. Đạt kiểm kỹ thuật không thay xác nhận của tác giả hay giảng viên.

### 2.1. Sản phẩm nộp

| Yêu cầu và nguồn | Đối chiếu repo/gói | Trạng thái; người chốt |
|---|---|---|
| PDF 30–60 trang (Q, Hình thức; Định dạng văn bản) | [README báo cáo mục 5](bao_cao/README.md) ghi bản rút gọn trước đó 56 trang; `validate_reports` bắt buộc PDF, DOCX là bản chỉnh sửa kèm theo | **Chưa biết** bản PDF cuối. Người phụ trách báo cáo kiểm số trang, chương, lề và phụ lục; Đức nhận bản đã chốt |
| Mã nguồn dưới dạng repo Git (Q, Hình thức) | [Repo Git](https://github.com/Duckcy-Bui/nasa24-crater-stem), [README](../README.md), `ma_nguon/` từ `git archive`; gói ghi URL repo và SHA | **Đạt** khả năng truy cập nguồn. Archive không mang lịch sử Git; lịch sử đối chiếu riêng ở 2.3 |
| Ứng dụng demo có giao diện (Q, Hình thức) | [app.py](../app.py), Streamlit, bundle ngoại tuyến và lệnh chạy trong hướng dẫn gói; [S2-13](S2-13_TICH_HOP.md) | **Đạt** phần giao diện/mã chạy; phạm vi bốn chức năng còn lệch ở 2.4. Đức kiểm demo bản cuối |
| 15–20 slide (Q, Hình thức) | Chưa nhận tệp slide làm đầu vào; script có `--slides` và ô `san_pham_bo_sung/slide/` | **Lệch** bộ nộp hiện tại; Hưng giao tệp và tự xác nhận số slide/phân vai |
| Video demo 5–7 phút (Q, Hình thức) | Chưa nhận tệp video; script có `--video` và ô `san_pham_bo_sung/video/` | **Lệch** bộ nộp hiện tại; Quốc Anh giao tệp, kiểm thời lượng và nội dung |
| Bảng đánh giá chéo thành viên (Q, Hình thức) | [Bảng đánh giá chéo](bao_cao/dong_gop_va_danh_gia.md) còn các ô chờ; `--peer-review` nhận bản được cả nhóm hoàn thiện | **Lệch**; từng người tự đánh giá, nhận đánh giá của bạn và xác nhận, không ký thay |
| Bảng phân công ở phần mở đầu, có công việc, file mã, mục báo cáo, tỷ lệ (%) và chữ ký cả nhóm (Q, Phần mở đầu) | [Bảng M.1 ở phần mở đầu](bao_cao/00_mo_dau.md) đã có, còn trống tỷ lệ và chữ ký; `--signed-assignment` nhận bản có chữ ký thật | **Lệch** phần tỷ lệ/chữ ký; bốn người tự xác nhận. Không coi bình luận S2-16 là đủ chữ ký của bảng cuối |

### 2.2. Bảo vệ và vai trò

| Yêu cầu và nguồn | Bằng chứng, việc cần làm | Trạng thái |
|---|---|---|
| 20 phút: 12 trình bày, 3 demo, 5 vấn đáp (Q, Hình thức) | Hưng điều phối tổng duyệt S3-15, ghi thời gian từng phần; Đức chuẩn bị bản demo dự phòng. Chưa có biên bản tổng duyệt bản cuối | **Chưa biết** |
| Giảng viên chỉ định người trả lời; mỗi người hiểu cả phần bạn (Q, Hình thức) | Bảng mục 3 bổ sung xác nhận đọc chéo; tập trả lời câu hỏi về Hough, tiền xử lý, dữ liệu, đánh giá, game và giới hạn | **Chưa biết**; không khóa người trả lời theo phân vai slide |
| Nhóm 5 người/5 vai trò; được điều chỉnh vai trò nhưng ghi rõ trong đề cương (Q, Quy định chung; Cơ cấu 5 vai trò) | [PHAN_CONG](PHAN_CONG.md) chỉ có bốn thành viên | **Lệch**; Đức xin giảng viên xác nhận cơ cấu bốn người và cách gộp vai trò, không tự thêm thành viên |

### 2.3. Mã nguồn và liêm chính

| Yêu cầu và nguồn | Bằng chứng repo; xử lý đề xuất | Trạng thái |
|---|---|---|
| Python 3.10+, thuật toán cốt lõi tự cài NumPy; đối chiếu thư viện (Q, Hình thức) | [Hough](../src/hough.py), [tiền xử lý](../src/preprocessing.py), [S2-06/S3-02](S2-06_S3-02_KIEM_CHUNG.md), ví dụ số và OpenCV ở [S3-10](S3-10_TAI_TAO_KET_QUA.md) | **Đạt** phần cài đặt/đối chiếu, không suy ra độ chính xác toàn ảnh |
| `src/`, `data/`, `results/`, `notebooks/` nếu có, README, requirements (Q, Mã nguồn) | Có `src/`, `data/`, `README.md`, `requirements.txt`. Kết quả ở `docs/evidence/` và `outputs/`, chưa có `results/` tracked. Không có notebook tracked nên `notebooks/` chưa áp dụng | **Lệch** tên/vị trí kết quả; đề xuất giảng viên chấp nhận bảng ánh xạ, hoặc mở lượt chuyển cấu trúc riêng. Không tạo thư mục rỗng để coi là đạt |
| Một lệnh tái tạo **toàn bộ bảng kết quả Chương 4**, seed cố định (Q, Mã nguồn) | [README, S3-10](../README.md) và [runner](../scripts/reproduce_s310.py) cố định seed 0; danh mục và đầu ra từng bảng ở dưới | **Đạt** nguồn/đầu ra cho Bảng 4.5–4.6; **chưa biết** mức bao phủ bản cuối khi chủ Chương 4 chốt bảng lịch sử 4.4 và kết quả E1–E3. Không dùng bảng mô tả/thiết kế để kết luận thiếu bảng kết quả |
| PEP 8; mỗi hàm có docstring nêu vào/ra/công thức (Q, Mã nguồn) | Ví dụ `sha256`, `inventory` trong [script đóng gói](../scripts/package_s316.py) chưa có docstring; chưa có kết quả lint PEP 8 toàn repo | **Lệch** docstring; PEP 8 **chưa biết**. Đề xuất lượt audit riêng, không định dạng lại mã trong vòng này |
| Commit trải đều 8 tuần từ tài khoản từng thành viên (Q, Mã nguồn) | Lịch sử main có commit từ 12/10 đến 02/11/2026; cả bốn thành viên có trong mục Contributors của repo. Mở đầu Q ghi BTL trong 3 tuần | **Đạt theo quyết định của Đức** ngày 02/11/2026: giữ lịch sử commit hiện tại theo thời lượng 3 tuần. Không tạo lại hoặc lùi ngày commit |
| Mỗi thành viên có commit riêng và tham gia phân tích kết quả Chương 4 (Q, Cơ cấu 5 vai trò) | Từng người ghi đoạn phân tích/bảng liên quan và link commit/PR ở mục 3; đối chiếu với [Bảng M.1](bao_cao/00_mo_dau.md), [bảng đóng góp](bao_cao/dong_gop_va_danh_gia.md) và nhật ký nhóm | **Chưa biết** phần phân tích của từng người; chờ chính tác giả xác nhận, không thay bằng việc chỉ đọc chéo hoặc tập vấn đáp |
| Ghi nguồn mã, hình, dữ liệu trong mã và báo cáo (Q, Liêm chính) | [Nguồn dữ liệu](S1-06_HUONG_DAN_DU_LIEU.md), [bib](bao_cao/tai_lieu.bib), nguồn thẻ khoa học; cần rà toàn bộ bản cuối | **Chưa biết** mức bao phủ đầy đủ; từng chủ phần xác nhận |
| Phụ lục “Sử dụng công cụ AI”: tên công cụ, phần dùng, cách kiểm; tự giải thích mã (Q, Liêm chính) | [Phụ lục D](bao_cao/07_phu_luc.md) có dòng Đức, ba người còn ô chờ; cần khai đúng phạm vi thực tế | **Lệch** khai báo chưa đủ. Các thành viên tự hoàn thiện và chuẩn bị giải thích mã |
| Mục tiêu trùng lặp ≤25%, loại trích dẫn/công thức; vượt 25% phải giải trình (Q, Liêm chính) | Chưa có kết quả kiểm trùng lặp bản PDF cuối; không có căn cứ tự ghi tỷ lệ | **Chưa biết**; Đức nhận kết quả chính thức và giải trình nếu vượt ngưỡng |
| Che mờ mặt/biển số của người khác khi công bố (Q, Liêm chính) | Bộ dữ liệu chính là ảnh LROC; chưa nhận video/slide cuối để rà hình có người/biển số | **Chưa biết** toàn bộ bộ nộp; Hưng, Quốc Anh và Đức kiểm trước công bố |

#### Danh mục bảng kết quả và đối chiếu runner

Theo [Chương 4 tại pin `9b87a61`](https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/9b87a61295617c88b3bf96a90862a938b7a37063/docs/bao_cao/04_chuong_4_du_lieu_danh_gia.md). Các đường dẫn đầu ra dưới đây tính từ thư mục lượt full của runner. Đã đối chiếu artifact trong [S3-10/full](evidence/s3-10/full/), chưa chạy lại toàn bộ Hough trong lượt sửa tài liệu này.

| Bảng kết quả | Nguồn/đầu ra runner | Mức đối chiếu và giới hạn |
|---|---|---|
| 4.4 — kiểm tra luồng E2 trên STT 17 ngày 26/10 | Nguồn lịch sử [S2-07/results.json](evidence/s2-07/results.json); bước `experiments_tuning` xuất `E2.csv` và `experiments_tuning.json`, chọn `moon_ap16_m109134835l_c01` | Bốn biến thể có cùng số ứng viên, TP/nhãn và Recall_known. Thời gian trong Bảng 4.4 thuộc lượt cũ; không yêu cầu trùng số giây khi chạy lại. Chủ Chương 4 chốt giữ bảng lịch sử hay thay bằng lượt mới có cấu hình/mốc đo rõ ràng |
| 4.5 — kết quả gộp và theo ảnh của ba phương pháp trên tuning/holdout | Hai bước `evaluation_tuning`, `evaluation_holdout`: `evaluation_*/summary.json`, trường `aggregate`; kèm `results.csv` | Sáu dòng khớp TP/FN, Recall_known gộp, trung bình và SD mẫu sau làm tròn. Runner có đủ trường tính bảng; không cần một file Markdown trùng bố cục báo cáo |
| 4.6 — kết quả từng ảnh holdout | `evaluation_holdout/results.csv` và `summary.json`: `images[].methods.*`, gồm `candidate_count` cho OpenCV | Tám dòng ảnh và dòng tổng khớp nhãn, TP/FN và số vòng OpenCV; không nhầm `radii_gt16` trong CSV với tổng số vòng |
| Các bảng kết quả E1–E3 còn chờ S3-05 trong mục 4.6 | `experiments_tuning.json`, `experiments_holdout.json`, `E1.csv`, `E2.csv`, `E3.csv` do runner xuất | Đã có artifact; chủ phần chưa chốt các bảng sẽ đưa vào báo cáo nên chưa kết luận bao phủ toàn bộ bản cuối. Không tự coi thiếu bảng trình bày là thiếu bước chạy |

Bảng 4.1 (nguồn ảnh), 4.2 (thống kê nhãn) và 4.3 (thiết kế thí nghiệm) là các bảng mô tả dữ liệu/thiết kế, không dùng việc runner chưa xuất chúng để nâng yêu cầu “bảng kết quả”. Mục 4.8 chưa có bảng kết quả khảo sát vì khảo sát chưa làm; yêu cầu khảo sát vẫn **chưa đạt**, tách khỏi kiểm độ bao phủ runner. Khi Chương 4 được chốt hoặc đổi số bảng, chủ phần cập nhật lại danh mục và dẫn artifact tương ứng.

Kết quả S3-05 đã có trong repo qua PR #38, còn chờ chủ phần ghép và diễn giải ở mục 4.6.

### 2.4. Danh sách đề tài NASA, Đề 24

| Yêu cầu | Bằng chứng và giới hạn hiện tại | Trạng thái |
|---|---|---|
| (1) Tương phản/làm trơn, Hough tròn tự viết, kết hợp cặp sáng–tối theo nắng | `src/preprocessing.py`, `src/hough.py`, `src/postprocessing.py`; [hồ sơ sáng–tối](evidence/s1-11/). Game chỉ gắn nhãn sáng–tối; nhiều ảnh thiếu hướng nắng đo được nên không kiểm được | **Đạt** phần mã/luồng; chưa chứng minh hiệu quả kết hợp sáng–tối trên toàn bộ dữ liệu |
| (2) Đếm, phân bố kích thước, so mật độ hai vùng để giải thích tuổi tương đối | [S3-03](S3-03_KIEM_TRA_MAT_DO.md) (bản đếm dùng từ 04/11; [S2-09](evidence/s2-09/) giữ làm lịch sử), `src/statistics.py`, bảng đếm tay Lunokhod 1/Mare Frigoris. Ứng viên game chạm trần thì ẩn mật độ; không đủ căn cứ kết luận vùng nào già hơn | **Lệch** phần diễn giải tuổi theo yêu cầu; không thay đếm tay thành kết quả máy hoặc suy tuổi tuyệt đối |
| (3) Học sinh khoanh, hệ thống chấm và so máy/danh mục | [app.py](../app.py), [scoring.py](../src/scoring.py), [màn hình kết quả](S2-08_MAN_HINH_KET_QUA.md). Điểm dùng nhãn tham chiếu; giao máy chỉ là so sánh tham khảo | **Đạt** luồng kỹ thuật; chưa thử học sinh thật, nhãn/danh mục còn giới hạn dưới đây |
| (4) Thẻ thiết bị NASA trong vùng ảnh, hiện khi học sinh tìm thấy | [S2-10](S2-10_THE_KHOA_HOC.md), [science_cards.py](../src/science_cards.py). Chỉ có thẻ vùng, `position: null`, thiết bị ngoài crop, không mở khóa khi tìm/nhấp vị trí; Lunokhod không phải thiết bị NASA | **Lệch** phần vị trí/kích hoạt; giữ rõ giới hạn, không tạo ghim giả |
| Ảnh LRO, CTX/HiRISE Sao Hỏa, bãi Apollo/rover; danh mục hố công bố | [Chương 1 mục 1.3](bao_cao/01_chuong_1_gioi_thieu.md), [hướng dẫn dữ liệu](S1-06_HUONG_DAN_DU_LIEU.md): 26 crop LROC Mặt Trăng; không có CTX/HiRISE, thiết bị ngoài crop. Nhãn tay thưa không thay đối chiếu danh mục đầy đủ | **Lệch** phạm vi dữ liệu; Đức xác nhận với giảng viên cách trình bày phần chưa đạt |
| Precision và Recall so danh mục; tâm lệch ≤0,5 bán kính | [matching.py](../src/matching.py), [evaluation.py](../src/evaluation.py), [Chương 4 mục 4.5/4.7](bao_cao/04_chuong_4_du_lieu_danh_gia.md): ghép một–một đúng ngưỡng, chỉ có Recall_known; Precision/F1 toàn ảnh chưa xác định | **Lệch** độ đo/danh mục, **đạt** quy tắc ghép. Không biến nhãn thưa thành ground truth đầy đủ |
| Khảo sát ≥10 học sinh về hứng thú và hiểu bài | [Chương 4 mục 4.10](bao_cao/04_chuong_4_du_lieu_danh_gia.md), [S2-16 mục 8](S2-16_NGHIEM_THU_TUAN_2.md): quyết định 31/10 không khảo sát/thử người thật | **Lệch — chưa đạt**, giữ nguyên quyết định của Đức; không thay bằng test kỹ thuật hoặc số liệu giả |

Chọn điểm hạ cánh, quản lý tiền đồn và bản tiếng Việt ngoại tuyến nằm ở mục **ý tưởng phát triển tiếp** của N24, không cộng thành chức năng bắt buộc mới.

### 2.5. Thông tin vẫn chờ giảng viên

Hai tài liệu không ghi **nơi nộp, hạn nộp hay quy cách tên tệp**. Đức cần nhận thông báo chính thức về hệ thống/người nhận, ngày giờ/múi giờ và tên ZIP/PDF/slide/video. Các nội dung bảng phân công/chữ ký và đánh giá chéo đã có yêu cầu; nếu học phần dùng biểu mẫu riêng, xin đúng mẫu. Không dùng hạn sprint làm hạn chính thức. Người phụ trách báo cáo đối chiếu thêm cấu trúc phụ lục A/B/C, định dạng và chương theo Q; tài liệu này không sửa nguồn báo cáo.

`BaoCao_Nhom2_NASA24.pdf`/`.docx` là **quy ước nội bộ**, do [build_report.py](../scripts/build_report.py) đặt từ commit `f3366c5` ngày 27/10/2026; hai tài liệu không yêu cầu tên này. Chờ giảng viên xác nhận tên tệp và nơi nộp. Các lệch nhóm bốn người, 8 tuần, vị trí `results/`, mức bao phủ bảng kết quả Chương 4 còn chờ bản cuối và phạm vi Đề 24 cần Đức chốt cách xử lý; không tự coi là ngoại lệ đã được chấp nhận.

## 3. Sản phẩm và xác nhận thành viên

Mã, [bundle/metadata](../data/s106_bundle/), [nhãn](../data/reference_labels/), [chia tập](../data/s203_split/), [vùng đếm](../data/s303_counts/), [bảng đánh giá](evidence/) và [nguồn báo cáo](bao_cao/) có trong main. Script dựng PDF/DOCX cùng nguồn; slide, video, đánh giá chéo và phân công có chữ ký nhận bằng các cờ riêng ở mục 4.

Bảng này liệt kê việc cần từng người tự xác nhận, không ký thay. Cột cuối để trống cho bằng chứng xác nhận phiên bản cuối. [S2-16 mục 5](S2-16_NGHIEM_THU_TUAN_2.md) đã có “Đồng ý” lịch sử của Đức; không tự điền các ô còn lại.

**Áp dụng riêng cho từng người trong cả bốn dòng:** tự đối chiếu công việc, file mã, mục báo cáo và tỷ lệ đóng góp; ký bảng phân công bản cuối; tự đánh giá/đánh giá chéo và khai AI; đọc phần của bạn để trả lời khi giảng viên chỉ định. Ghi ở Bảng M.1, bảng đóng góp/đánh giá chéo và Phụ lục D (AI), kèm bản ký và biên bản tổng duyệt 12/3/5. Các tệp ký/đánh giá do chính thành viên cung cấp, chưa có xác nhận nào được điền thêm ở đây.

**Nghĩa vụ phân tích riêng của từng thành viên:** tham gia phân tích kết quả Chương 4, ghi rõ bảng/mục và nhận xét mình đóng góp, kèm link commit hoặc bình luận PR của phần đánh giá. Ghi dẫn chứng này trong [bảng đóng góp](bao_cao/dong_gop_va_danh_gia.md) và [nhật ký nhóm](NHAT_KY_NHOM.csv); nếu chưa ghép vào chương thì dẫn bình luận phân tích trên PR để chủ chương đối chiếu. Bốn người tự xác nhận bằng chứng của mình ở cột cuối, hiện để trống. Đọc chéo để vấn đáp không thay nghĩa vụ phân tích.

| Người | Cần xác nhận gì | Ghi ở đâu | Xác nhận bản cuối |
|---|---|---|---|
| Nguyễn Mạnh Tiến | Đóng góp/đánh giá chéo và AI; dòng của mình trong S2-16; tự xác nhận không phản đối đổi cặp vùng Lunokhod 1 – Mare Frigoris; phần Hough Chương 2 và 3, nhất là 3.3.5 được sửa hộ ở PR #33; tham gia phân tích kết quả Chương 4 về Hough/độ đo cùng Quốc Anh, dẫn bằng chứng phân tích theo quy tắc trên; đọc lại sau rút gọn; kết quả kiểm đủ bộ S3-14 | [Bảng M.1](bao_cao/00_mo_dau.md), [đóng góp/đánh giá chéo](bao_cao/dong_gop_va_danh_gia.md), [Phụ lục D (AI)](bao_cao/07_phu_luc.md), S2-16 mục 5; việc đổi cặp vùng theo [review PR #30](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/30#pullrequestreview-5679533272), trả lời tại PR #30 hoặc [PR #29](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/29) mục 5; [PR #33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33), Chương 2–4 và biên bản kiểm phiên bản cuối | |
| Đinh Quang Hưng | Đóng góp/AI và S2-16; Chương 2 phần tiền xử lý/sáng–tối, Chương 3 phần 3.4–3.6 sau PR #33; nguồn các số đo thời gian, mô tả mật độ khớp app PR #34; tham gia phân tích kết quả Chương 4 về tiền xử lý/sáng–tối/thống kê, dẫn bằng chứng phân tích theo quy tắc trên; nội dung sau rút gọn; slide/phân vai S3-11 và tổng duyệt S3-15 | Bảng M.1, bảng đóng góp/đánh giá chéo, Phụ lục D (AI), S2-16 mục 5, PR #33, [Chương 2](bao_cao/02_chuong_2_co_so_ly_thuyet.md), [Chương 3](bao_cao/03_chuong_3_phuong_phap_cai_dat.md), tệp slide và biên bản tổng duyệt | |
| Hoàng Quốc Anh | Đóng góp/AI và S2-16; tự xác nhận kiểm chéo đếm tay/cặp vùng trên PR #30; mục 4.1 sửa hộ ở PR #33; tham gia phân tích kết quả Chương 4 sau rút gọn, ba thí nghiệm S3-05 và giới hạn không khảo sát, dẫn bằng chứng phân tích theo quy tắc trên; thẻ khoa học và video S3-13 | Bảng M.1, bảng đóng góp/đánh giá chéo, Phụ lục D (AI), S2-16 mục 5, [PR #30](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/30), PR #33, [Chương 4](bao_cao/04_chuong_4_du_lieu_danh_gia.md), tệp video | |
| Bùi Hải Đức | Tự rà dòng đóng góp/AI và xác nhận S2-16 của mình; tham gia phân tích kết quả Chương 4 và hệ quả cho phạm vi/demo, dẫn bằng chứng phân tích theo quy tắc trên; Chương 1/5 và bản ghép sau khi Chương 2–4 rút gọn; PDF/số trang, các sản phẩm, gói cuối và thông tin nộp chính thức. S3-10 đã nghiệm thu theo mục 1 | Bảng M.1, bảng đóng góp/đánh giá chéo, Phụ lục D (AI), S2-16 mục 5, [README báo cáo](bao_cao/README.md), biên bản bàn giao cuối; người điều phối cập nhật trạng thái giao việc | |

Người chốt từng chương đối chiếu số liệu sau rút gọn, không chỉ xóa dấu `[CHỜ]`. Theo [góp ý PR #33](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/33#issuecomment-6553202790), cần rút phần lặp/giả mã và bổ sung nguồn thời gian hoặc bỏ số đo chưa có bằng chứng. Giữ hợp đồng câu cảnh báo theo [S2-13 mục 3.2](S2-13_TICH_HOP.md) khi sửa phần thống kê.

## 4. Đóng gói bằng script

[package_s316.py](../scripts/package_s316.py) lấy mã/bundle/nguồn báo cáo từ commit qua `git archive`, dựng bằng `scripts/build_report.py` trong bản archive. Script bắt buộc có PDF để nộp và DOCX kèm theo, kiểm bundle/SHA, ghi manifest mọi file, kiểm ZIP bằng `ZipFile.testzip()` và so byte với manifest, rồi ghi checksum ZIP. Không cần `data/processed/`, không ghi đè đầu ra có sẵn. URL repo Git được ghi trong hướng dẫn/manifest để xem lịch sử, ngoài bản archive tĩnh.

Từ gốc repo, dùng Python 3.12 đã cài `requirements-report.txt` và LibreOffice/UNO theo README báo cáo:

```bash
python -B scripts/package_s316.py \
  --commit 94c17ff \
  --output outputs/s316_94c17ff
```

Nếu Python dựng báo cáo nằm ở venv khác, thêm `--report-python <đường-dẫn-python>`. Đường dẫn tương đối tính từ thư mục gọi lệnh, giữ nguyên symlink venv; tên lệnh đơn như `python3.12` được tìm qua PATH. Chỉ thêm các cờ dưới khi chủ phần đã giao file, không dùng README giữ chỗ làm sản phẩm:

| Cờ | Chủ phần/đầu vào | Chỗ trong gói |
|---|---|---|
| `--slides ban_giao/slide.pdf` | Hưng, kiểm 15–20 slide | `san_pham_bo_sung/slide/` |
| `--video ban_giao/video.mp4` | Quốc Anh, kiểm 5–7 phút | `san_pham_bo_sung/video/` |
| `--peer-review ban_giao/danh_gia_cheo.pdf` | Cả nhóm tự đánh giá và xác nhận | `san_pham_bo_sung/danh_gia_cheo/` |
| `--signed-assignment ban_giao/phan_cong_ky.pdf` | Công việc/file mã/mục báo cáo/tỷ lệ và chữ ký cả nhóm | `san_pham_bo_sung/phan_cong_ky/` |

Đuôi file ở ví dụ là lựa chọn nội bộ; đề không ấn định định dạng slide/video/phiếu. Script sao chép file có nội dung, giữ đuôi nhưng dùng tên theo vai trò, không ghi đường dẫn máy hoặc tên gốc vào manifest. File ngoài commit được ghi SHA/kích thước và `received_not_reviewed`; chưa cung cấp thì `missing`, liệt kê trong `required_deliverables_missing`. Mỗi ô có README nói rõ chỉ giữ chỗ. Tất cả file thật và README đều nằm trong ZIP, được kiểm hash; việc có file chưa chứng minh số slide, thời lượng hoặc chữ ký hợp lệ.

```text
outputs/s316_<phiên-bản>/
  NASA24_Nhom2_<SHA>/
    ma_nguon/                 # đúng tệp tracked của commit, gồm README và bundle
    bao_cao/                  # PDF bắt buộc, DOCX kèm theo, dựng cùng commit
    san_pham_bo_sung/         # slide/, video/, danh_gia_cheo/, phan_cong_ky/
    HUONG_DAN_BAN_GIAO.md
    manifest.json             # SHA-256/kích thước mọi file trừ chính manifest
  NASA24_Nhom2_<SHA>.zip
  NASA24_Nhom2_<SHA>.zip.sha256
  build_report.log
  report_build/               # đầu ra dựng và tệp trung gian để kiểm
  result.json
```

Lượt thử r5 từ `c466c2d` đã qua kiểm dựng/manifest/ZIP, là hồ sơ lịch sử. PR #42 và #43 đã merge; khi đóng gói lại, chọn commit chốt và thư mục mới, nhận đủ bốn tệp bổ sung rồi chạy lại. Mã nguồn/báo cáo luôn lấy từ commit chọn; SHA công cụ đóng gói ghi riêng vì công cụ đang gọi có thể mới hơn commit đó.

Lượt thử đối chiếu ngày 01/11 từ `94c17ff` dựng được PDF 56 trang và DOCX, còn 28 dấu chờ; manifest có bốn sản phẩm bổ sung `missing`. Kiểm đủ 467 file nguồn theo archive, 474 hash payload và 475 mục ZIP/CRC đều khớp. Đây là gói thử kỹ thuật, chưa đủ bộ nộp hoặc xác nhận nội dung cuối.

Pin `94c17ff` còn đường dẫn máy trong log/manifest lịch sử. Trước khi phát hành gói, tích hợp thay đổi ẩn đường dẫn đã chuẩn bị riêng, kiểm lại chuỗi SHA chứng cứ và quét bản archive theo commit cuối. Không coi gói thử từ pin cũ là bản đã làm sạch để công bố.

Manifest schema `s316-package-2` ghi số dấu chờ, sản phẩm còn thiếu và các kiểm nội dung chưa làm. `status=complete` chỉ xác nhận tạo gói kỹ thuật; `submission_ready=false` luôn giữ để chờ Đức kiểm bộ nộp, không tự nghiệm thu dù đã nhận đủ file. Không đưa gói/thư mục dựng vào Git. Khi bàn giao thật: kiểm từng hash sau giải nén, mở PDF/slide/video/phiếu từ bản sao; kiểm demo desktop/mobile đúng phiên bản; ghi checksum ZIP, bản dự phòng và người nhận.

Cập nhật kiểm kỹ thuật 04/11/2026: [biên bản S3-14](S3-14_KIEM_TRA_BAN_GIAO.md) và [bằng chứng](evidence/s3-14/README.md) có 370 test Python, 6 bộ canvas, Chromium local và full đủ Bảng 4.4–4.8. Lỗi chọn Python đóng gói Windows đã sửa. R14-03–R14-07 còn mở: PDF cuối, slide/video, xác nhận thành viên và đồng nhất phiên bản bộ nộp; giữ nguyên các ô chưa nghiệm thu.

## 5. Kiểm tra cuối

- [ ] Đức đã nhận nơi nộp, hạn/múi giờ và quy cách tên tệp từ giảng viên; xác nhận cơ cấu bốn người.
- [ ] Các lệch mục 2 có hướng xử lý được Đức ghi rõ; không biến hạn chế đã nêu thành tiêu chí đạt hoặc miễn trừ của giảng viên.
- [ ] Mã/config/bundle và báo cáo cùng SHA đã chốt; phần đánh giá bị ảnh hưởng bởi thay đổi đã kiểm lại.
- [ ] PDF cuối 30–60 trang, mở được và được người phụ trách báo cáo kiểm chương/lề/định dạng; DOCX kèm theo; hết dấu chờ chưa giải quyết, các tác giả xác nhận bản sau rút gọn và bằng chứng từng người tham gia phân tích kết quả Chương 4.
- [ ] Đủ slide 15–20, video 5–7 phút, bảng đánh giá chéo và bảng phân công có công việc/file mã/mục báo cáo/tỷ lệ/chữ ký thật; manifest không còn ô thiếu file, mọi nội dung đã được chủ phần kiểm.
- [ ] AI đã khai đủ từng người; nguồn mã/hình/dữ liệu đầy đủ; có kết quả trùng lặp ≤25% hoặc giải trình theo quy định; mặt/biển số của người khác đã che mờ nếu có.
- [ ] Mọi sản phẩm ghi đúng khảo sát chưa đạt, nhãn thưa, đánh giá lặp và giới hạn khoa học; không tạo số liệu thay thế.
- [ ] Có biên bản tổng duyệt đủ 20 phút: 12 trình bày, 3 demo, 5 vấn đáp; mỗi người đã tập trả lời phần bạn, người trả lời thực tế do giảng viên chỉ định.
- [ ] Có biên bản kiểm đủ bộ và người xử lý lỗi còn lại; luồng game, thống kê/thẻ và demo đã kiểm trên bản cuối, có demo dự phòng.
- [ ] ZIP giải nén và kiểm hash được, tệp mở được, hướng dẫn không cần đường dẫn máy tác giả; bản sao dự phòng trùng hash.
- [ ] Đức quyết định nghiệm thu gói nộp, lưu link repo/SHA, checksum ZIP, nơi nộp và nơi dự phòng.
