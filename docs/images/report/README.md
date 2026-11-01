# Ảnh chèn trong báo cáo

- `giao_dien_khoanh_ho.png`, `ket_qua_cham_bai.png`, `the_khoa_hoc.png`: giải mã RGB từ JPEG gốc trong `docs/evidence/s3-08/`, lưu PNG, không đổi kích thước, pixel, vùng cắt, màu hoặc độ sáng. Không chụp lại app. So toàn bộ byte pixel giải mã: 3/3 khớp. Hash và kích thước ở `png_provenance.json`. Chuyển định dạng không phục hồi chi tiết đã mất do nén JPEG gốc.
- `so_do_he_thong.svg` và `.png`: sơ đồ do nhóm vẽ bằng Matplotlib, theo `src/pipeline.py`, `src/integration.py`, `app.py` và Chương 3. Nét đứt chỉ bước đã cài nhưng chưa bật mặc định; không phải ảnh chụp bằng chứng runtime.
- Ảnh thiên thể nguồn ghi công NASA/GSFC/Arizona State University. Bản gốc ở evidence được giữ nguyên. Các hình kết quả khác trong thân báo cáo vốn dùng PNG.
