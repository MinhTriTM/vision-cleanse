# Phân công nghiên cứu chi tiết — 4 thành viên
## Bài tập lớn Xử lý ảnh (IN4152N01): Tích hợp bộ lọc Sobel vào VisionCleanse

Nhóm: Đoàn Minh Trí (trưởng nhóm, 0024417136) · Lê Tuấn Kiệt (0024417193) · Võ Thanh Tân (0024416594) · Phạm Thị Như Ý (0024419356). GV: Trần Ngọc Thuận.

**Cách làm việc của nhóm:** mỗi thành viên *nghiên cứu chuyên sâu một phần và viết báo cáo nghiên cứu cho phần đó* → trưởng nhóm tổng hợp thành báo cáo tổng + bản tích hợp dự án hoàn chỉnh → từ báo cáo tổng làm slide thuyết trình. Không ai viết lan man ngoài phần của mình; chất lượng của báo cáo tổng nằm ở chất lượng từng báo cáo phần.

**Nguồn sự thật duy nhất (single source of truth):** mọi con số thực nghiệm lấy từ `BaiTapLon/experiment/results.json` trên nhánh `vision-cleanse-BaiTapLonImageProcessing`; mọi khẳng định về dự án lấy từ mã nguồn và tài liệu của repo; danh mục tài liệu dùng chung ở `BaiTapLon/TaiLieu_ThamKhao_Sobel_VisionCleanse.md`. Cấm tự chế số liệu hoặc trích nguồn ngoài danh mục mà chưa qua kiểm chứng của trưởng nhóm.

---

## Giai đoạn 1 — Nghiên cứu cá nhân và viết báo cáo phần

### 1. Võ Thanh Tân — Lý thuyết Sobel chuyên sâu (nền của Chương 2)

**Câu hỏi nghiên cứu:** Toán tử Sobel ra đời thế nào, được suy ra từ đâu, vì sao kernel lại có trọng số 1-2-1, và nó hơn/kém gì các toán tử cạnh khác?

**Nội dung bắt buộc:**
- Lịch sử: buổi thuyết trình Sobel–Feldman 1968 tại SAIL; vì sao công trình không xuất bản chính thức mà lan truyền qua Duda & Hart (1973).
- Suy ra kernel: tổng vector của 4 ước lượng gradient trung tâm trong lân cận 3×3; phân tích kernel thành tích ngoài của vector làm trơn [1 2 1] × vector hiệu [−1 0 1]; tính tách được (separable) và ý nghĩa tính toán.
- Công thức độ lớn G = √(Gx²+Gy²), xấp xỉ |Gx|+|Gy|, hướng cạnh θ; ví dụ tính tay lân cận cạnh dọc 100|200 cho Gx = 400, Gy = 0 (thuộc lòng để trả lời hỏi–đáp).
- Bảng so sánh có căn cứ: Roberts (2×2), Prewitt (trọng số đều), Sobel, Scharr (chính xác hơn ở kernel 3×3), Canny (đa giai đoạn, dùng Sobel bên trong).
- Ưu/nhược điểm trung thực: nhạy nhiễu vì không có bước làm mờ riêng; cạnh dày; đổi lại nhanh, đơn giản, độ lớn gradient bất biến với đảo tông màu (làm cầu nối sang phần của Trí).

**Nguồn bắt buộc:** PDF lịch sử của chính Irwin Sobel; Wikipedia "Sobel operator"; bài Condados về gradient; tài liệu OpenCV Sobel; bài giảng dò cạnh của TS. Ngô Quốc Việt.
**Sản phẩm bàn giao:** báo cáo phần 5–7 trang (Word hoặc Markdown) gồm: nội dung trên + ít nhất 1 bảng so sánh + 1 hình kernel/Gx/Gy tự vẽ lại + danh sách nguồn đã đọc. Gửi trưởng nhóm để ghép thành Chương 2.

### 2. Lê Tuấn Kiệt — Lý thuyết xử lý ảnh tổng quan (nền của Chương 1 + Mở đầu)

**Câu hỏi nghiên cứu:** 14 chủ đề của học phần nằm ở đâu trong bức tranh xử lý ảnh, và chúng liên kết với nhau (và với đề tài Sobel) như thế nào?

**Nội dung bắt buộc:**
- Khung phân loại: biến đổi điểm (âm bản, logarit, power-law/gamma, piecewise-linear, cắt bit-plane), thống kê ảnh (cân bằng histogram), lọc không gian (trung bình, trung vị, Gaussian, Laplacian, Sobel, Prewitt), xử lý theo ngưỡng (thresholding).
- Với mỗi chủ đề: nguyên lý 3–5 dòng, công thức cốt lõi, khi nào dùng, một ví dụ trực quan. Không đào sâu Sobel (phần của Tân) — chỉ đặt Sobel đúng vị trí trong bản đồ.
- Viết Mở đầu của báo cáo tổng: bối cảnh học phần, lý do nhóm chọn Sobel trong 14 chủ đề (khớp dự án có sẵn + dHash là gradient thô), mục tiêu và phạm vi đề tài.
- Chỉ ra rõ các "bẫy khái niệm": ngưỡng trung vị của pHash không phải lọc trung vị; tích chập trong CNN khác tích chập lọc ảnh cổ điển ở điểm nào.

**Nguồn bắt buộc:** Gonzalez & Woods (Chương 3 và 10); bài giảng Xử lý ảnh số của TS. Ngô Quốc Việt; bài Ultralytics tiếng Việt về phát hiện biên.
**Sản phẩm bàn giao:** báo cáo phần 6–8 trang gồm bản đồ 14 chủ đề (1 bảng tổng hợp) + bản thảo Mở đầu 1–2 trang. Ghép thành Chương 1 và Mở đầu.

### 3. Đoàn Minh Trí — Dự án VisionCleanse và tích hợp Sobel (nền của Chương 3 + 4, kiêm tổng hợp)

**Câu hỏi nghiên cứu:** VisionCleanse đang giải quyết bài toán gì và bằng cơ chế nào; Sobel được tích hợp vào đâu, theo luật nào, và thay đổi hành vi hệ thống ra sao?

**Nội dung bắt buộc:**
- Bài toán làm sạch dataset: trùng chính xác, trùng gần đúng, rò rỉ train/val/test; căn cứ học thuật về rò rỉ dữ liệu (Kapoor & Narayanan 2023).
- Kiến trúc 2 vòng hiện tại: hash mật mã (MD5/SHA-256); pHash (DCT 32×32, ngưỡng trung vị — nguồn Zauner 2010); dHash (so pixel kề = gradient [-1,+1] — nguồn Krawetz); khoảng cách Hamming và ngưỡng 10; kiểm tra ảnh trống/rỗng.
- Thiết kế vòng 2.5: `edge_hash` (độ lớn Sobel → trung bình khối 8×8 → ngưỡng trung vị → 64 bit), `edge_energy`; luật quyết định trong `group_duplicates` (edge hash chỉ quyết khi cả hai phía đều có hash thật ≠ 0; cặp MD5 không bị ảnh hưởng); cờ `--sobel-verify` mặc định tắt.
- Tự chạy lại toàn bộ test (88 test) và demo trực tiếp khi thuyết trình; chịu trách nhiệm mọi câu hỏi về code.

**Nguồn bắt buộc:** mã nguồn + README/ROADMAP của repo; luận văn Zauner và trang dự án pHash; bài Kapoor & Narayanan; tài liệu DataEval (đối chiếu thực hành ngành).
**Sản phẩm bàn giao:** Chương 3 + Chương 4 hoàn chỉnh kèm mã nguồn trích dẫn đúng file/dòng, sơ đồ vòng 2.5, và bản demo chạy được. Đồng thời là người tổng hợp Giai đoạn 2.

### 4. Phạm Thị Như Ý — Thực nghiệm, đánh giá và hướng phát triển (nền của Chương 5 + 6)

**Câu hỏi nghiên cứu:** Tích hợp Sobel đo được hiệu quả đến đâu, ở đâu nó thua, và bước tiếp theo có căn cứ là gì?

**Nội dung bắt buộc:**
- Thiết kế thực nghiệm: ảnh gốc `photo_like`, 16 biến thể biến đổi (resize, JPEG, nhiễu, sáng/tối, tương phản, gamma, âm bản, mờ, nét, crop 10%/25%, lật) + 1 ảnh khác hẳn; ba khoảng cách Hamming pHash/dHash/edge_hash và tỉ lệ năng lượng cạnh.
- Phân tích kết quả theo nhóm hiện tượng (không liệt kê máy móc): bất biến tông màu (âm bản 62/64/0), bền với mờ/nhiễu, giới hạn hình học (crop 10% → 24/15/14; lật → 32/44/32; ảnh khác 26/20/22 — sát vùng mơ hồ), phát hiện mờ qua năng lượng (mờ r=2 còn 0,58×).
- Viết Chương 6: kết luận; hạn chế trung thực (không xử lý xoay/lật; ảnh có bản đồ cạnh đều cho edge hash = 0); hướng phát triển có nguồn: xác minh SIFT + RANSAC (đã có trong ROADMAP), biến thể D4 của DataEval, PDQ của Meta, Canny thay Sobel.
- Chịu trách nhiệm hình thức: thống nhất định dạng, mục lục, danh mục tài liệu tham khảo của báo cáo tổng.

**Nguồn bắt buộc:** `experiment/results.json` (nguồn số liệu duy nhất); bài Lowe 2004 (SIFT); tài liệu DataEval; bài tổng quan PDQ/pHash/dHash.
**Sản phẩm bàn giao:** báo cáo phần 5–7 trang gồm bảng kết quả đầy đủ + 2 biểu đồ + bản thảo Chương 6. Ghép thành Chương 5 + 6.

---

## Giai đoạn 2 — Tổng hợp thành báo cáo tổng và dự án hoàn chỉnh

Trưởng nhóm (Trí) ghép 4 báo cáo phần theo cấu trúc cố định: Mở đầu (Kiệt) → Ch.1 Tổng quan (Kiệt) → Ch.2 Sobel (Tân) → Ch.3 VisionCleanse (Trí) → Ch.4 Tích hợp (Trí) → Ch.5 Thực nghiệm (Ý) → Ch.6 Kết luận (Ý) → Tài liệu tham khảo → Phụ lục.

Quy tắc tổng hợp (bắt buộc):
1. **Đọc chéo:** mỗi chương do một người khác tác giả đọc và góp ý một vòng; mâu thuẫn số liệu/thuật ngữ do trưởng nhóm quyết theo nguồn sự thật duy nhất.
2. **Thống nhất thuật ngữ:** "băm cảm nhận", "khoảng cách Hamming", "độ lớn gradient", "vòng 2.5" dùng nhất quán toàn văn; ký hiệu Gx, Gy, G, θ theo Chương 2.
3. **Kiểm chứng cuối:** chạy lại test suite + thực nghiệm từ bản tổng hợp; đối chiếu từng con số trong văn bản với `results.json` trước khi chốt.
4. **Dự án đi kèm:** nhánh GitHub `vision-cleanse-BaiTapLonImageProcessing` là bản nộp chính thức — code Sobel + test ở thư mục gốc repo, toàn bộ tài liệu trong `BaiTapLon/`. Mọi bản sửa sau tổng hợp đều đẩy lên nhánh này.

## Giai đoạn 3 — Làm slide và thuyết trình

Slide chính làm bằng **NotebookLM** (notebook mới, nạp báo cáo tổng làm nguồn đầu tiên, theo prompt 16 slide trong file chuẩn bị thuyết trình), sau đó mỗi người chỉnh lại các trang thuộc phần mình:

| Slide | Nội dung | Người phụ trách |
|---|---|---|
| 1–2 | Bìa, lý do chọn đề tài | Ý |
| 3–5 | Bản đồ lý thuyết 14 chủ đề | Kiệt |
| 6–9 | Sobel: lịch sử, kernel, ví dụ tính tay, so sánh | Tân |
| 10–13 | VisionCleanse, tích hợp vòng 2.5, demo trực tiếp | Trí |
| 14–16 | Kết quả thực nghiệm, kết luận, hướng phát triển | Ý |

- Tổng thời lượng 12–15 phút; mỗi người thuộc sẵn 2 câu hỏi–đáp của phần mình (danh sách 8 câu trong file `ChuanBi_ThuyetTrinh_Sobel.md`).
- Slide bản chính (sau khi chỉnh xong) thay thế bản nháp trên nhánh GitHub.
- Họp thử 1 buổi trước khi thuyết trình: chạy demo trực tiếp, bấm giờ từng phần, chốt người trả lời dự phòng cho từng nhóm câu hỏi.

## Bảng tóm tắt phân công

| Thành viên | Phần nghiên cứu | Chương | Slide | Bàn giao chính |
|---|---|---|---|---|
| Võ Thanh Tân | Sobel chuyên sâu | Ch.2 | 6–9 | Báo cáo phần 5–7 trang + bảng so sánh toán tử |
| Lê Tuấn Kiệt | Tổng quan xử lý ảnh | Mở đầu + Ch.1 | 3–5 | Báo cáo phần 6–8 trang + bản đồ 14 chủ đề |
| Đoàn Minh Trí | VisionCleanse + tích hợp | Ch.3 + Ch.4 | 10–13 | Chương hoàn chỉnh + demo + tổng hợp toàn bài |
| Phạm Thị Như Ý | Thực nghiệm + kết luận | Ch.5 + Ch.6 | 1–2, 14–16 | Báo cáo phần 5–7 trang + biểu đồ + định dạng tổng |

*Ghi chú: báo cáo tổng 30 trang hiện có trên nhánh được dùng làm bản khung — mỗi thành viên đối chiếu phần của mình với chương tương ứng, bổ sung/sửa theo nội dung nghiên cứu ở trên rồi gửi trưởng nhóm ghép bản cuối.*
