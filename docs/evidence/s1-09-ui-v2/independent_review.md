# Kiểm định độc lập UI v2

Agent: `nasa24-qa` (Codex), phiên `01a13a65-ce1c-7323-b75f-3e0a61abf82f`, pane Herdr `w1:p12`. Kết luận ngày 14/10/2026, sau vòng sửa cuối. Agent viết bộ kiểm thử lưu riêng, không sửa production hoặc thao tác Git.

## Những điểm đã tìm và đóng

| Điểm kiểm | Sửa và bằng chứng |
| --- | --- |
| Dòng chọn vòng và nút sao chép trên mobile còn nhỏ | Vùng nhấn tăng lên tối thiểu 44 px; visual report có kiểm kích thước |
| Vòng đang chọn nằm ngoài phần danh sách desktop đang thấy | Danh sách tự cuộn để hiện vòng đang chọn; ảnh desktop và visual report xác nhận |
| Tọa độ sai chỉ có thông báo chung | Đặt/reset `aria-invalid` và `data-invalid` cho đúng ô, liên kết thông báo; visual report thử tâm x=512 và xác nhận vòng không đổi |

## Kết luận ghi lại từ agent

> Đóng review UIv2: không còn actionable findings trong phạm vi nghiệm thu.
>
> Đã xác nhận P3 được sửa: đánh dấu/reset từng ô lỗi, liên kết thông báo và từ chối input sai trước khi đổi vòng. Docs đủ links, phân biệt mock/runtime, ground truth và persistence đúng.
>
> Evidence cuối khớp: Python 131 OK, JS 9 PASS, browser 7 nhóm PASS, visual 10 nhóm PASS.

Luồng lưu đúng ảnh/phiên, checkpoint nonce trước IO và chống replay đã được kiểm qua nguồn cùng bộ test độc lập. Agent đối chiếu nguồn, report và ảnh chụp; Chromium headless do root chạy. Agent không tự chạy lại trình duyệt và chưa kiểm thiết bị cảm ứng thật hoặc trình duyệt khác. Kết quả này không kế thừa PASS từ UI v1.
