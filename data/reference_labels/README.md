# Nhãn hố thủ công (S1-10) — thưa, chưa kiểm chéo

Thư mục này chứa nhãn hố ghi tay cho các ảnh cắt, do Git theo dõi:
- `<image_id>_craters_catalogue.json`: nhãn theo schema `crater_set` v1.0.
- `<image_id>_overlay.png`: ảnh vẽ vòng tròn đè lên hố để kiểm tra chéo bằng mắt.

Trạng thái hiện tại: **nhãn thưa (sparse), chưa kiểm chéo** (`reference_source` ghi `unreviewed`).
Mỗi ảnh mới chỉ có vài hố được gán nhãn; còn nhiều hố khác chưa gán. Đây chưa phải ground truth đã xác minh:
- Không dùng để tính Precision/Recall hay chấm điểm khi nguồn còn `unreviewed`.
- Kể cả sau khi kiểm chéo, không tính Precision trên nhãn thưa; chỉ báo recall trên tập hố đã gán nhãn.
- Metadata ảnh trong `data/processed/` vẫn giữ `reference_status="unavailable"`.

Không chép các file này vào `data/processed/`: các script S1-06 coi catalogue ở đó là dữ liệu cũ chưa xác minh và dừng lại.
Xem quy tắc đầy đủ tại [docs/S1-10_HUONG_DAN_NHAN_HO.md](../../docs/S1-10_HUONG_DAN_NHAN_HO.md).
