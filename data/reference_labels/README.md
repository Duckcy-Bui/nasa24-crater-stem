# Thư mục nhãn tham chiếu (Reference Ground Truth)

Thư mục này chứa các bộ nhãn tham chiếu (Ground Truth) được xác minh cho các ảnh cắt:
- File nhãn JSON: `<image_id>_craters_catalogue.json` (tuân thủ schema `crater_set` v1.0).
- File ảnh overlay: `<image_id>_overlay.png` (ảnh vẽ vòng tròn đè lên hố để kiểm tra chéo bằng mắt).

Các file trong thư mục này được Git theo dõi trực tiếp để phục vụ kiểm tra chéo và tính toán độ đo Precision / Recall.
