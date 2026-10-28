# Tài liệu tham khảo Hough — theo dõi S1-15

Ngày kiểm tra: **14/10/2026**. Kế thừa danh sách S1-03, kiểm tra lại nguồn
phục vụ bản nháp [S1-15](S1-15_LY_THUYET_HOUGH.md) và đối chiếu
[S1-12](S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md).

Danh mục có **12 nguồn riêng, 3 bài báo có DOI**. “Đã kiểm tra” không đồng
nghĩa “đã đọc toàn văn”. Các mục thuật toán/dữ liệu/khoa học được phân loại
riêng; ảnh LROC và trang NASA không được dùng thay chứng minh thuật toán.

## 1. Bài báo DOI

| Mã | Thông tin trích dẫn | Đã kiểm tra và phạm vi dùng | Cần tiếp tục |
|---|---|---|---|
| [1] | Duda, R. O.; Hart, P. E. (1972). *Use of the Hough transformation to detect lines and curves in pictures*. Communications of the ACM, 15(1), 11–15. [DOI 10.1145/361237.361242](https://doi.org/10.1145/361237.361242). | [NASA NTRS](https://ntrs.nasa.gov/citations/19720033498) xác nhận tác giả/năm/DOI và tóm tắt; nền tảng không gian tham số. Trang ACM không đọc được trong phiên này, NTRS không có bản tải. | Đọc toàn văn; đối chiếu lại số tập/trang kế thừa S1-03 khi có bản nhà xuất bản. |
| [2] | Yuen, H. K.; Princen, J.; Illingworth, J.; Kittler, J. (1990). *Comparative study of Hough Transform methods for circle finding*. Image and Vision Computing, 8(1), 71–77. [DOI 10.1016/0262-8856(90)90059-E](https://doi.org/10.1016/0262-8856(90)90059-E). | [Trang nhà xuất bản](https://www.sciencedirect.com/science/article/pii/026288569090059E): kiểm tra thư mục/DOI và đọc abstract về so sánh biến thể. | Đọc toàn văn trước khi trích dẫn kết quả/thuật toán chi tiết của từng biến thể. |
| [3] | Canny, J. (1986). *A Computational Approach to Edge Detection*. IEEE TPAMI, PAMI-8(6), 679–698. [DOI 10.1109/TPAMI.1986.4767851](https://doi.org/10.1109/TPAMI.1986.4767851). | [Danh mục của tác giả](https://people.eecs.berkeley.edu/~jfc/papers/papers.html) xác nhận tác giả/tên/năm/trang; DOI và tập/số kế thừa S1-03. IEEE không trả nội dung đủ để kiểm tra độc lập DOI trong phiên này. Chỉ dùng làm đầu mối nền tảng biên. | Đối chiếu DOI trực tiếp IEEE và đọc toàn văn; chưa coi là đã kiểm tra đầy đủ DOI qua nguồn gốc trong phiên này. |

Có đủ **3 bài được định danh DOI**; trong phiên này đối chiếu độc lập DOI
được 2/3 từ NTRS/nhà xuất bản. Mục [3] còn bước xác minh DOI trực tiếp;
không ghi thành 3/3 đã đọc hoặc xác minh toàn văn.

## 2. Tài liệu kỹ thuật chính thức

| Mã | Nguồn và liên kết | Nội dung đã đọc/đối chiếu | Cách dùng |
|---|---|---|---|
| [4] | OpenCV, [Hough Circle Transform](https://docs.opencv.org/4.x/d4/d70/tutorial_hough_circle.html) | Kiểu ảnh đầu vào và ý nghĩa tham số, quy trình tìm vòng | Mô tả đối chiếu thư viện |
| [5] | OpenCV, [hough.cpp, tag 4.14.0](https://github.com/opencv/opencv/blob/4.14.0/modules/imgproc/src/hough.cpp) | HoughCirclesGradient: Sobel CV_16S, BORDER_REPLICATE, Canny ngưỡng nửa/đủ, L2=false | Dựng lại điều kiện trích biên cho S1-12; không chép thuật toán vào src/hough.py |
| [6] | Scikit-image, [API skimage.transform.hough_circle](https://scikit-image.org/docs/stable/api/skimage.transform.html#skimage.transform.hough_circle) | Hough từ ảnh biên và tập bán kính, chuẩn hóa accumulator | Hướng đối chiếu bổ sung; chưa chạy |
| [7] | Scikit-image, [Circular and Elliptical Hough Transforms](https://scikit-image.org/docs/stable/auto_examples/edges/plot_circular_elliptical_hough_transform.html) | Ví dụ tích lũy và lấy đỉnh | Tham khảo cách trình bày; không coi là kết quả của repo |
| [8] | NumPy, [numpy.rint](https://numpy.org/doc/stable/reference/generated/numpy.rint.html) | Làm tròn gần nhất, hòa nửa về số chẵn | Giải thích lượng tử hóa offset |
| [9] | NumPy, [numpy.bincount](https://numpy.org/doc/stable/reference/generated/numpy.bincount.html) | Đếm chỉ số nguyên không âm, minlength | Giải thích cộng các phiếu trùng tâm |
| [10] | OpenCV, [Canny Edge Detection](https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html) | Gradient, NMS biên, ngưỡng kép, L2gradient | Liên hệ tiền xử lý; NMS biên khác NMS vòng |

Tài liệu online có thể đổi theo stable/4.x. Bằng chứng thực chạy ghi riêng
NumPy **2.5.3**, OpenCV **4.14.0**, Python **3.12.10** và SHA-256 mã.
Nguồn [5] cố định tag; không dùng nhánh 4.x đang thay đổi để khẳng định
nội bộ mọi phiên bản đều giống nhau.

## 3. Dữ liệu và kiến thức khoa học

| Mã | Loại | Nguồn | Mức kiểm tra và phạm vi |
|---|---|---|---|
| [11] | Dữ liệu | LROC, [WAC Global Morphologic Map](https://data.lroc.im-ldi.com/lroc/view_rdr/WAC_GLOBAL) | Đọc trang dữ liệu gốc, phục vụ hồ sơ nguồn ảnh; không dùng làm nhãn cho cảnh giả lập |
| [12] | Khoa học | NASA Science, [Earth's Moon](https://science.nasa.gov/moon/) | Đọc trang bối cảnh Mặt Trăng; không dùng thay nguồn thuật toán hay kết quả phát hiện hố |

## 4. Việc cần bổ sung khi hoàn thiện báo cáo

Đọc toàn văn [1]–[3] và ghi trang/mục sử dụng; xác minh lại phần thư mục còn
kế thừa S1-03, nhất là DOI [3]. Dẫn xuất trong S1-15 là phần giải thích
toán học và mã của dự án, không gán tùy ý thành một đoạn trích của bài báo.
Nếu bổ sung ảnh thật hoặc scikit-image, cần lưu cấu hình/kết quả riêng;
không nâng trạng thái “tham khảo” thành “đã thực nghiệm” khi chưa chạy.


## 5. Cập nhật xác minh nguồn ngày 27/10/2026 (S3-06)

Đã truy vấn độc lập Crossref cho ba DOI [1]–[3], khớp tiêu đề, tác giả, tập/số và trang.
Mục [3] là PAMI-8(6), 679–698, DOI 10.1109/TPAMI.1986.4767851.
Xem [metadata gốc và URL truy vấn](evidence/s3-06/doi_verification.json).
Các giới hạn “chưa xác minh DOI [3]” phía trên là tình trạng ngày 14/10; đã giải quyết ở mức thư mục.
Không tuyên bố đã đọc toàn văn cả ba bài. Đã mở lại các trang chính thức [4]–[12];
[5] chỉ là mã lịch sử tag 4.14.0, không xác minh nội bộ OpenCV 5.0.0 hiện cài.
Xem [danh sách lần kiểm tra](evidence/s3-06/source_checks.json) và
[bản hoàn thiện lý thuyết/cài đặt](S2-11_S3-06_HOUGH_HOAN_THIEN.md).
