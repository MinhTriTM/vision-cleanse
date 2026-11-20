# Tài liệu tham khảo — Xử lý ảnh, VisionCleanse và bộ lọc Sobel

Soạn 20/11/2026 cho bài tập lớn học phần Xử lý ảnh (IN4152N01). Mọi liên kết đã được kiểm chứng qua tìm kiếm trực tiếp. Mỗi tài liệu ghi rõ dùng cho phần nào của báo cáo/slide.

## A. Xử lý ảnh — nền tảng chung (phục vụ Chương 1)

1. **Gonzalez & Woods — Digital Image Processing, 4th ed., Pearson, 2018** (sách, không có bản mở chính thức)
   Giáo trình chuẩn của học phần: Chương 3 (biến đổi điểm: âm bản, log, gamma, piecewise-linear; histogram), Chương 10 (lọc không gian, phát hiện cạnh). Là nguồn [1] trong báo cáo.

2. **Bài giảng Xử lý ảnh số, Chương 6 "Bài toán dò cạnh" — TS. Ngô Quốc Việt (TPHCM, 2014)** — tiếng Việt
   https://tailieu.vn/doc/bai-giang-xu-ly-anh-so-chuong-6-ngo-quoc-viet-1860717.html
   Bài giảng tiếng Việt đúng cấu trúc học phần: toán tử gradient bậc nhất (Roberts, Sobel, Prewitt), bậc hai (Laplacian), dò cạnh tối ưu Canny, thực hành OpenCV. Rất hợp để đối chiếu thuật ngữ tiếng Việt khi thuyết trình.

3. **Ultralytics — "Giải thích về phát hiện biên: Canny, Sobel và cách chúng hoạt động"** — tiếng Việt
   https://www.ultralytics.com/vi/blog/edge-detection-in-image-processing-explained
   Bài giải thích dễ đọc về tích chập, gradient và quy trình phát hiện cạnh; có phần lịch sử phát triển của xử lý ảnh.

## B. Sobel và phát hiện cạnh — đào sâu (phục vụ Chương 2)

4. **Irwin Sobel — "History and Definition of the Sobel Operator" / "An Isotropic 3×3 Image Gradient Operator" (bản PDF do chính tác giả phổ biến)**
   https://skynet.ecn.purdue.edu/~ace/vip/History_and_Definition_of_Sobel_Operator.pdf
   Tài liệu gốc quý nhất: chính Irwin Sobel kể lại buổi thuyết trình 1968 tại SAIL cùng Gary Feldman và trình bày cách suy ra toán tử (tổng vector của 4 ước lượng gradient trung tâm trong lân cận 3×3). Lưu ý thú vị cho slide: công trình này *chưa từng được xuất bản chính thức* — nó đến với cộng đồng qua chú thích trong sách Duda & Hart (1973).

5. **Wikipedia — Sobel operator**
   https://en.wikipedia.org/wiki/Sobel_operator
   Tra cứu nhanh: hai kernel, công thức độ lớn/hướng, tính tách được (separable), biến thể Scharr, và lưu ý về quy ước dấu kernel gốc của Sobel.

6. **OpenCV — Sobel Derivatives (tài liệu hướng dẫn chính thức)**
   https://docs.opencv.org/2.3/doc/tutorials/imgproc/imgtrans/sobel_derivatives/sobel_derivatives.html
   Lý thuyết + mã nguồn mẫu của hàm `Sobel()`; giải thích vì sao đạo hàm làm nổi bật cạnh và giới thiệu kernel Scharr chính xác hơn cho kernel 3×3. Dùng khi GV hỏi "không dùng OpenCV thì khác gì".

7. **LearnOpenCV — Edge Detection Using OpenCV**
   https://learnopencv.com/edge-detection-using-opencv/
   Hướng dẫn thực hành Sobel và Canny bằng Python/C++ kèm video; hợp để chuẩn bị demo phụ nếu cần.

8. **Condados — "Image Gradients: Sobel, Prewitt, Central Diff"**
   https://condados.ai/blog/image-gradients-sobel-prewitt
   Bài phân tích hiện đại, trình bày rõ mỗi kernel Sobel là tích ngoài (outer product) của vector làm trơn × vector hiệu — đúng luận điểm ở mục 2.3 của báo cáo.

9. **Canny (1986) — "A Computational Approach to Edge Detection", IEEE TPAMI 8(6)** (sách/bài báo — trích dẫn chuẩn, nguồn [3] trong báo cáo)
   Bài báo đặt chuẩn cho phát hiện cạnh: làm mờ Gaussian → gradient Sobel → triệt cực đại không phải cực trị (non-maximum suppression) → ngưỡng trễ. Là cầu nối tự nhiên khi GV hỏi "sau Sobel còn gì nữa".

10. **Dalal & Triggs (2005) — "Histograms of Oriented Gradients for Human Detection", CVPR** (nguồn [5] trong báo cáo)
    HOG dùng histogram hướng gradient (tính bằng Sobel) làm đặc trưng phát hiện người — bằng chứng ứng dụng lớn của gradient Sobel ngoài phát hiện cạnh thuần túy.

## C. Những gì VisionCleanse đã dùng — băm cảm nhận và làm sạch dữ liệu (phục vụ Chương 3–4)

11. **Christoph Zauner — "Implementation and Benchmarking of Perceptual Image Hash Functions" (luận văn, 2010) + trang dự án pHash/Rihamark**
    https://zauner.nllk.net/projects/
    Luận văn nền tảng của pHash dựa trên DCT (khung benchmark Rihamark, thư viện pHash mã nguồn mở). Đây là nguồn [4] trong báo cáo và là gốc học thuật của hàm `phash()` trong VisionCleanse.

12. **Neal Krawetz (Hacker Factor) — loạt bài "Looks Like It" (2011–2013)**, được tổng hợp dễ đọc tại:
    https://centamori.com/index.php?slug=perceptual-hash
    Bài viết phổ biến aHash/dHash/pHash: dHash thu ảnh 9×8 rồi so pixel kề (đúng thuật toán `dhash()` của dự án), pHash dùng DCT + ngưỡng trung vị. Bài tổng hợp của Centamori cài đặt lại cả ba thuật toán từ đầu, dễ theo dõi từng bước.

13. **DataEval — tài liệu "Data Integrity" (thư viện kiểm định dữ liệu của JAIC)**
    https://dataeval.readthedocs.io/en/v1.0.1/concepts/DataIntegrity.html
    Tài liệu kỹ thuật của một thư viện thật khác cũng dùng đúng bộ ba xxHash/pHash/dHash để phát hiện trùng — bằng chứng cách làm của VisionCleanse khớp thực hành ngành. Có thêm biến thể D4 (băm trên 8 hướng xoay/lật rồi lấy min) — ý tưởng đáng nêu ở phần hướng phát triển cho bài toán lật ảnh.

14. **Kapoor & Narayanan (2023) — "Leakage and the reproducibility crisis in machine-learning-based science", Patterns 4(9)**
    https://pmc.ncbi.nlm.nih.gov:443/articles/PMC10499856/ (bản arXiv: https://arxiv.org/abs/2207.07048?context=cs)
    Bài báo Princeton chứng minh rò rỉ dữ liệu (gồm trùng lặp giữa train/test) làm sai lệch ít nhất 294 bài báo ở 17 lĩnh vực — căn cứ học thuật cho *lý do tồn tại* của VisionCleanse, rất mạnh khi mở đầu Chương 3 hoặc trả lời câu hỏi "dự án này để làm gì".

15. **Tài liệu nội bộ của chính dự án** (trên repo/nhánh bài tập lớn): `README.md` (mục giới hạn "chưa bắt crop sâu, xoay, lật, đổi màu mạnh"), `ROADMAP-1.0.md` (vòng trùng từng phần, xác minh hình học SIFT + RANSAC), `STRATEGY.md`, và mã nguồn `src/vision_cleanse/extractors.py`, `matchers.py`. Đây là nguồn chính cho mọi khẳng định về dự án — luôn ưu tiên trích từ đây thay vì mô tả bên ngoài.

## D. Mở rộng — hướng phát triển (phục vụ Chương 6)

16. **Lowe (2004) — SIFT, "Distinctive Image Features from Scale-Invariant Keypoints", IJCV 60(2)**
    Đặc trưng cục bộ bất biến tỉ lệ/xoay — đích đến của vòng 4 trong lộ trình VisionCleanse cho crop sâu và xoay/lật.

17. **Meta PDQ** — hàm băm cảm nhận mã nguồn mở của Meta (phát triển từ cảm hứng pHash, dùng trong kiểm duyệt nội dung quy mô lớn); được giới thiệu trong bài tổng quan:
    https://ghost.fluidvip.com/guides/perceptual-hashes-explained.html
    Bài này cũng giải thích gọn PDQ/pHash/dHash và khoảng cách Hamming — hợp để đọc nhanh trước buổi thuyết trình.

## Gợi ý nạp vào NotebookLM (notebook mới cho học phần Xử lý ảnh)

Thứ tự ưu tiên nếu giới hạn nguồn: (1) file báo cáo DOCX/PDF của nhóm → (2) PDF của chính Sobel [mục 4] → (3) bài giảng Ngô Quốc Việt [2] → (4) bài tổng hợp băm cảm nhận của Centamori [12] → (5) bài Kapoor & Narayanan [14] → (6) trang OpenCV Sobel [6] → (7) Wikipedia Sobel [5] → (8) bài Ultralytics tiếng Việt [3]. Tám nguồn này bao phủ cả 6 chương và đủ sâu cho phần hỏi–đáp.
