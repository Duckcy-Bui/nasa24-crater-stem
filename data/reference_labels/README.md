# Nhãn hố thủ công (S1-10) — nhãn thưa đã kiểm chéo

Thư mục này chứa nhãn hố ghi tay cho các ảnh cắt, do Git theo dõi:
- `<image_id>_craters_catalogue.json`: nhãn theo schema `crater_set` v1.0.
- `<image_id>_overlay.png`: ảnh vẽ vòng tròn đè lên hố để kiểm tra chéo bằng mắt.

Trạng thái hiện tại: **26/26 bộ nhãn thưa (sparse) đã kiểm chéo**, nguồn ghi `reviewed by Nguyen Manh Tien`.
Nguyễn Mạnh Tiến xác nhận trực tiếp ngày 27/10/2026 rằng đã kiểm đủ 26 overlay.
Hồ sơ: [xác nhận](review_confirmation.json). Xác nhận công khai ngày 28/10/2026: [bình luận của Tiến trên PR #20](https://github.com/Duckcy-Bui/nasa24-crater-stem/pull/20#issuecomment-6462992167).
Mỗi ảnh mới chỉ có vài hố được gán nhãn; còn nhiều hố khác chưa gán. Nhãn chưa đầy đủ cho toàn ảnh:
- Không dùng để tính Precision/Recall hay chấm điểm khi nguồn còn `unreviewed`.
- Kể cả sau khi kiểm chéo, không tính Precision trên nhãn thưa; chỉ báo recall trên tập hố đã gán nhãn.
- Metadata ảnh trong `data/processed/` vẫn giữ `reference_status="unavailable"`.

Không chép các file này vào `data/processed/`: các script S1-06 coi catalogue ở đó là dữ liệu cũ chưa xác minh và dừng lại.
Xem quy tắc đầy đủ tại [docs/S1-10_HUONG_DAN_NHAN_HO.md](../../docs/S1-10_HUONG_DAN_NHAN_HO.md).
