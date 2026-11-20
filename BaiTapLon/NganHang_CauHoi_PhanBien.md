# Ngân hàng câu hỏi phản biện — Bẫy trước mọi câu hỏi
## Bài tập lớn: Tích hợp bộ lọc Sobel vào VisionCleanse (Xử lý ảnh IN4152N01)

Cách dùng: mỗi câu gồm **Hỏi** (cách GV có thể hỏi, kể cả hỏi xoáy), **Đáp** (trả lời mẫu — ngắn, đúng trọng tâm, có số liệu), **Bẫy** (GV đang kiểm tra điều gì / lỗi trả lời thường gặp). Người phụ trách theo phân công: Tân = Sobel, Kiệt = tổng quan, Trí = dự án + tích hợp, Ý = thực nghiệm. Mọi số liệu lấy từ `experiment/results.json`.

---

## Phần A — Sobel: lý thuyết gốc rễ (Tân)

**A1. Hỏi: Sobel do ai, năm nào, công bố ở đâu?**
Đáp: Irwin Sobel và Gary Feldman trình bày năm 1968 tại Stanford Artificial Intelligence Project, nhan đề "A 3×3 Isotropic Gradient Operator for Image Processing". Nó không có bài báo chính thức — cộng đồng biết đến qua chú thích "suggested by I. Sobel" trong sách của Duda & Hart (1973). Chính Sobel đã viết lại lịch sử và cách suy ra toán tử trong tài liệu "History and Definition of the Sobel Operator".
Bẫy: trả lời "đăng trên tạp chí năm 1968" là sai. GV hỏi câu này để phân biệt người đọc nguồn gốc với người đọc lướt Wikipedia.

**A2. Hỏi: Vì sao kernel có trọng số 2 ở giữa? Bỏ số 2 thành Prewitt thì sao?**
Đáp: Trọng số [1 2 1] là vector làm trơn dạng tam giác — điểm giữa hàng/cột lân cận được tin cậy gấp đôi điểm góc, giúp ước lượng gradient đẳng hướng (isotropic) hơn và đỡ nhiễu hơn. Bỏ trọng số 2 (mọi hệ số đều 1) thì thành toán tử Prewitt: vẫn tính được gradient nhưng đáp ứng theo hướng chéo kém đều hơn và nhạy nhiễu hơn.
Bẫy: đừng nói "2 cho cạnh đậm hơn" — bản chất là làm trơn có trọng số, không phải khuếch đại tùy tiện.

**A3. Hỏi: Kernel Sobel tách được (separable) nghĩa là gì, lợi gì?**
Đáp: Gx = tích ngoài của vector cột [1 2 1]ᵀ với vector hàng [−1 0 1] — tức làm trơn theo một trục rồi lấy hiệu theo trục còn lại. Nhờ đó phép chập 2D 3×3 (9 phép nhân/pixel) tách thành hai phép chập 1D (3+3 phép nhân/pixel), và với kernel nguyên nhỏ có thể tính bằng cộng/trừ số nguyên. Đây là một phần lý do Sobel rẻ và nhanh.
Bẫy: GV có thể hỏi tiếp "kernel nào cũng tách được không?" — Không. Chỉ kernel hạng 1 (outer product) mới tách được; Laplacian 3×3 chuẩn không tách được theo cách này.

**A4. Hỏi: Tính tay: lân cận có cột trái toàn 100, cột phải toàn 200. Gx, Gy bằng mấy?**
Đáp: Gx = (200×1 + 200×2 + 200×1) − (100×1 + 100×2 + 100×1) = 800 − 400 = 400. Gy = 0 vì hàng trên và hàng dưới giống hệt nhau. Độ lớn G = 400, hướng θ = 0° (cạnh dọc, gradient theo chiều ngang).
Bẫy: quên trọng số 2 ở hàng giữa là lỗi kinh điển — đáp án sai phổ biến là 300.

**A5. Hỏi: Độ lớn gradient có mấy cách tính? Khác nhau thế nào?**
Đáp: Chính xác: G = √(Gx² + Gy²). Xấp xỉ nhanh: G ≈ |Gx| + |Gy| (lệch tối đa ~41% theo hướng chéo, nhưng rẻ và đủ cho nhiều ứng dụng); một số cài đặt dùng max(|Gx|, |Gy|). Dự án dùng dạng chính xác √(Gx²+Gy²) vì cần độ lớn ổn định để xây edge hash.
Bẫy: nếu hỏi "sao không dùng xấp xỉ cho nhanh" — trả lời: chi phí sqrt không đáng kể ở khâu này so với độ ổn định của hash; xấp xỉ L1 làm méo tỉ lệ giữa các hướng.

**A6. Hỏi: Sobel là phép chập (convolution) hay tương quan (correlation)? Dấu kernel có quan trọng không?**
Đáp: Về toán học, chập lật kernel 180°, tương quan thì không. Kernel Sobel phản xứng nên lật kernel chỉ đổi dấu Gx/Gy; độ lớn gradient không đổi nên với mục đích phát hiện cạnh và của dự án này, dấu không ảnh hưởng. Chính Sobel trong tài liệu gốc cũng dùng quy ước mặt nạ (tương quan) và trục y hướng lên — khác quy ước ảnh số ngày nay — nhưng độ lớn vẫn như nhau.
Bẫy: đây là câu hỏi phân loại người hiểu sâu. Đừng khẳng định bừa "OpenCV dùng chập" — OpenCV `filter2D` là tương quan; hàm `Sobel()` của họ cho kết quả nhất quán vì lý do trên.

**A7. Hỏi: Vì sao Sobel nhạy nhiễu? Khắc phục thế nào?**
Đáp: Đạo hàm khuếch đại thành phần tần số cao, mà nhiễu cũng là tần số cao. Sobel có sẵn làm trơn [1 2 1] theo trục vuông góc với hướng đạo hàm nên đỡ hơn Roberts/Prewitt, nhưng không có bước làm mờ riêng như Canny (Gaussian trước). Khắc phục: làm mờ Gaussian nhẹ trước khi tính Sobel, hoặc tăng kích thước kernel (Sobel 5×5), hoặc dùng Scharr cho kernel 3×3.
Bẫy: đừng nói "Sobel khử nhiễu tốt" — thực nghiệm của nhóm: nhiễu σ12 cho khoảng cách 0 là nhờ bước thu nhỏ ảnh khi tính hash, không phải nhờ bản thân Sobel ở độ phân giải đầy đủ.

**A8. Hỏi: Scharr là gì, hơn Sobel ở đâu?**
Đáp: Scharr là biến thể kernel 3×3 với trọng số [3 10 3] thay [1 2 1], tối ưu để đáp ứng góc (rotational symmetry) chính xác hơn — OpenCV khuyến nghị Scharr thay Sobel khi kernel 3×3. Đánh đổi: hệ số lớn hơn, đáp ứng mạnh hơn một chút.
Bẫy: nếu GV hỏi "sao dự án không dùng Scharr" — vì mục tiêu là hash ổn định chứ không phải đo hướng chính xác tuyệt đối; Sobel chuẩn dễ đối chiếu tài liệu và đủ cho kết quả thực nghiệm; Scharr là hướng thay thế khả thi đã nêu trong báo cáo.

**A9. Hỏi: Sobel cho cạnh dày hay mỏng? Muốn cạnh mỏng 1 pixel thì làm sao?**
Đáp: Sobel cho đáp ứng dày quanh cạnh vì độ lớn gradient cao trên một dải. Muốn cạnh mỏng phải thêm triệt cực đại theo hướng gradient (non-maximum suppression) như Canny làm, rồi ngưỡng trễ (hysteresis).
Bẫy: đừng nhầm "ngưỡng hóa độ lớn" với cạnh mỏng — ngưỡng chỉ cắt bớt, không làm đáp ứng tự co thành 1 pixel.

**A10. Hỏi: Laplacian khác Sobel căn bản ở đâu?**
Đáp: Laplacian là đạo hàm bậc hai (một kernel duy nhất, đáp ứng cực trị/điểm qua không — zero crossing — tại cạnh), Sobel là đạo hàm bậc nhất theo hai hướng (cực đại độ lớn tại cạnh). Laplacian nhạy nhiễu hơn và không cho hướng cạnh trực tiếp; LoG (Laplacian of Gaussian) thêm làm mờ để giảm nhiễu. Sobel được chọn cho dự án vì độ lớn gradient ổn định và bất biến tông màu — tính chất Laplacian không có tương đương trực tiếp.
Bẫy: trả lời "Laplacian là Sobel cải tiến" là sai hoàn toàn về bản chất toán học.

**A11. Hỏi: Hướng cạnh θ dùng để làm gì trong thực tế?**
Đáp: Định hướng cạnh cho non-maximum suppression (Canny), gộp vào histogram hướng trong HOG để phát hiện đối tượng (Dalal & Triggs 2005 phát hiện người), và ước lượng hướng cấu trúc (structure tensor). Dự án chỉ dùng độ lớn vì hash cần bất biến tông màu, không cần hướng.
Bẫy: HOG là ví dụ ứng dụng kinh điển của gradient Sobel — nhắc được HOG là cộng điểm.

**A12. Hỏi: Tính Sobel trên số nguyên 8-bit có vấn đề gì?**
Đáp: Gx/Gy dao động trong khoảng ±4×255 = ±1020, vượt miền uint8 (−255..255 sau khi dời) và tràn số nếu tính trực tiếp trên uint8. Phải tính trên mảng số thực/số nguyên có dấu (float32/int16 trở lên) rồi mới chuẩn hóa. Code của dự án tính trên mảng float của numpy nên không gặp lỗi này.
Bẫy: đây là lỗi cài đặt kinh điển khi demo bằng uint8 — GV rất hay hỏi khi thấy code.

---

## Phần B — 14 chủ đề và nền tảng xử lý ảnh (Kiệt)

**B1. Hỏi: Lọc trung vị khác gì "ngưỡng trung vị" trong pHash của dự án?**
Đáp: Khác hoàn toàn. Lọc trung vị là lọc không gian: thay mỗi pixel bằng trung vị của lân cận, dùng khử nhiễu muối tiêu. Ngưỡng trung vị trong pHash là lấy trung vị của 64 hệ số DCT làm ngưỡng nhị phân hóa — một thao tác trên số liệu thống kê, không lọc pixel nào cả.
Bẫy: đây là bẫy khái niệm số 1 của đề tài này. Ai lẫn hai khái niệm này là lộ rõ chưa hiểu dự án.

**B2. Hỏi: Vì sao cân bằng histogram làm tăng tương phản? Nó có làm mất thông tin không?**
Đáp: Nó trải đều mức xám theo hàm phân phối tích lũy (CDF), kéo dãn vùng mức xám đông pixel. Nó ánh xạ đơn điệu nên không tạo mức xám mới ngoài việc gộp/trải; vùng quá tối/sáng bão hòa vẫn mất chi tiết. Không phải phép biến đổi "khôi phục" thông tin.
Bẫy: đừng nói cân bằng histogram "làm ảnh đẹp hơn" một cách vô điều kiện — ảnh nhiễu sẽ bị khuếch đại nhiễu ở vùng phẳng.

**B3. Hỏi: Biến đổi gamma và log khác nhau thế nào, khi nào dùng?**
Đáp: Cả hai là biến đổi điểm đơn điệu. Log nén mạnh vùng sáng, dãn vùng tối — hợp ảnh có dải động rất rộng (như phổ Fourier). Gamma (power-law) linh hoạt theo γ: γ<1 làm sáng ảnh tối, γ>1 làm tối ảnh sáng; còn dùng để hiệu chỉnh hiển thị thiết bị. Liên hệ dự án: cả hai đều đơn điệu nên giữ nguyên thứ tự hệ số so với trung vị — đó là lý do pHash/edge hash bền với gamma (thực nghiệm gamma 0.5/2.0 cho khoảng cách edge 2/8).
Bẫy: nối được biến đổi điểm sang tính bất biến của hash là điểm cộng lớn — đó chính là cầu nối Chương 1 ↔ Chương 4.

**B4. Hỏi: Thresholding là gì? Otsu khác ngưỡng cố định ở đâu?**
Đáp: Thresholding gán pixel thành hai lớp theo ngưỡng mức xám. Otsu tự chọn ngưỡng tối đa hóa phương sai giữa hai lớp (between-class variance) từ histogram, không cần đặt tay. Trong dự án, "ngưỡng" xuất hiện ở dạng khác: ngưỡng Hamming 10 để quyết định trùng, và ngưỡng trung vị để nhị phân hóa hash.
Bẫy: GV có thể cố ý đánh đồng ba loại ngưỡng này — phải phân biệt rõ: ngưỡng mức xám, ngưỡng thống kê nhị phân hóa, ngưỡng khoảng cách quyết định.

**B5. Hỏi: Lọc trung bình, Gaussian, trung vị — chọn cái nào khử nhiễu muối tiêu?**
Đáp: Trung vị. Nhiễu muối tiêu là xung cực trị (0/255) rải rác; trung vị loại bỏ cực trị mà giữ cạnh tốt hơn hẳn. Trung bình và Gaussian làm mờ cả nhiễu lẫn cạnh, và giá trị xung vẫn "rò" vào trung bình.
Bẫy: trả lời "Gaussian" là sai kinh điển. Nhớ thêm: Gaussian là lựa chọn khi nhiễu cộng dạng Gauss.

**B6. Hỏi: Âm bản ảnh là gì, ứng dụng thật ở đâu?**
Đáp: s = (L−1) − r, đảo ngược mức xám. Ứng dụng: xem ảnh y tế (X-quang hiển thị trên nền trắng dễ đọc hơn), tăng dễ đọc chi tiết tối trên nền sáng. Trong đề tài này âm bản là phép biến đổi "khó" nhất cho hash độ sáng: pHash lệch 62/64 bit, dHash 64/64 — nhưng edge hash lệch 0 vì độ lớn gradient không đổi khi đảo tông.
Bẫy: đây là câu hỏi dẫn vào kết quả nổi bật nhất của nhóm — phải thuộc số 62/64/0.

**B7. Hỏi: Cắt bit-plane để làm gì?**
Đáp: Tách ảnh thành 8 mặt phẳng bit; các bit cao mang cấu trúc chính, bit thấp mang chi tiết/nhiễu. Ứng dụng: nén, giấu tin (steganography ở bit thấp nhất), phân tích đóng góp từng bit. Không liên quan trực tiếp pipeline của dự án nhưng thuộc nhóm biến đổi điểm của Chương 1.
Bẫy: nếu bị hỏi xoáy "dự án có dùng không" — trả lời thẳng: không dùng, nó thuộc phần tổng quan học phần.

**B8. Hỏi: Tích chập trong lọc ảnh khác tích chập trong CNN ở đâu?**
Đáp: Trong lọc ảnh cổ điển kernel cố định do người thiết kế (Sobel, Gaussian) và phép toán thường là tương quan trượt nhân-cộng. Trong CNN, kernel được học từ dữ liệu qua lan truyền ngược, và các thư viện deep learning cũng cài đặt dạng tương quan nhưng gọi là "convolution". Điểm chung: tính cục bộ và chia sẻ trọng số theo vị trí.
Bẫy: đây là câu hỏi thời sự hay được hỏi để kiểm tra phân biệt hai học phần (Xử lý ảnh vs Học sâu).

---

## Phần C — VisionCleanse: những gì dự án đã dùng (Trí)

**C1. Hỏi: Vì sao cần làm sạch dataset? Trùng vài ảnh thì có sao?**
Đáp: Ảnh trùng hoặc gần trùng nằm ở cả train và test gây rò rỉ dữ liệu: mô hình "nhớ" ảnh test nên điểm đánh giá cao giả tạo. Kapoor & Narayanan (Patterns, 2023) tổng hợp cho thấy rò rỉ — trong đó có trùng lặp train/test — làm sai lệch ít nhất 294 bài báo thuộc 17 lĩnh vực. VisionCleanse tồn tại để chặn đúng lỗi này trước khi huấn luyện.
Bẫy: trả lời chung chung "để dữ liệu sạch hơn" là yếu. Phải nói được từ khóa *rò rỉ dữ liệu* và hệ quả lên độ tin cậy của đánh giá.

**C2. Hỏi: Hash mật mã (MD5/SHA) khác hash cảm nhận ở điểm nào cốt tử?**
Đáp: Hash mật mã có hiệu ứng tuyết lở: đổi 1 bit đầu vào là đầu ra đổi ~50%, nên chỉ bắt trùng chính xác từng byte. Hash cảm nhận được thiết kế ngược lại: ảnh nhìn giống nhau thì hash phải gần nhau, đo bằng khoảng cách Hamming — đổi nén, đổi kích thước, đổi sáng nhẹ chỉ làm lệch vài bit. VisionCleanse dùng cả hai: vòng 1 hash mật mã cho trùng tuyệt đối, vòng 2 hash cảm nhận cho trùng gần đúng.
Bẫy: đừng nói pHash "tốt hơn" MD5 — hai loại phục vụ hai định nghĩa trùng khác nhau.

**C3. Hỏi: pHash hoạt động thế nào, từng bước?**
Đáp: Thu ảnh xám về 32×32, biến đổi DCT 2D, giữ khối 8×8 hệ số tần số thấp ở góc trên-trái, lấy trung vị của các hệ số làm ngưỡng, hệ số nào lớn hơn trung vị thì bit 1 — được 64 bit. Nền tảng học thuật: luận văn của Zauner (2010) và thư viện pHash. Chỉ giữ tần số thấp nên bền với nén JPEG và thay đổi kích thước, vì các biến đổi đó phá tần số cao là chính.
Bẫy: bị hỏi "vì sao bỏ hệ số DC" — hệ số góc (0,0) là độ sáng trung bình, lớn vượt trội và chỉ mang thông tin sáng tổng thể; các cài đặt thường loại nó khỏi phép tính trung vị để ngưỡng không bị kéo lệch. (Trong code dự án, ngưỡng lấy trên khối hệ số đã trích — trả lời theo đúng code khi bị truy sâu.)

**C4. Hỏi: dHash liên quan gì tới gradient và tới Sobel?**
Đáp: dHash thu ảnh về 9×8 rồi ghi bit theo dấu hiệu của hiệu pixel kề phải: mỗi bit là dấu của đạo hàm rời rạc theo hàng, tức kernel [−1, +1] — dạng gradient thô sơ nhất. Sobel là gradient bậc cao hơn: có làm trơn [1 2 1] và xét cả hai hướng. Nói cách khác dự án đã dùng gradient dạng thô ở vòng 2; vòng 2.5 nâng lên gradient Sobel đầy đủ. Đây là mạch logic của toàn bộ đề tài.
Bẫy: đây là câu hỏi "cốt truyện" — trả lời được mạch dHash → Sobel là chứng minh nhóm hiểu vì sao chọn Sobel chứ không chọn ngẫu nhiên.

**C5. Hỏi: Khoảng cách Hamming là gì? Vì sao ngưỡng là 10?**
Đáp: Là số vị trí bit khác nhau giữa hai hash 64-bit. Hai ảnh không liên quan kỳ vọng lệch ~32 bit (một nửa). Ngưỡng 10 (~15% số bit) là giá trị mặc định của dự án cho cả pHash/dHash/edge hash, chọn theo kinh nghiệm và kiểm chứng bằng thực nghiệm của nhóm: các biến thể của cùng một ảnh cho khoảng cách ≤ 8 ở phần lớn trường hợp, còn ảnh khác hẳn cho 20–26 — ngưỡng 10 nằm giữa hai vùng này.
Bẫy: đừng khẳng định ngưỡng 10 là "chuẩn quốc tế" — Krawetz gợi ý ~5 cho ảnh chụp thật khắt khe hơn; ngưỡng là tham số đánh đổi độ nhạy/báo giả, dự án để nó thành tham số dòng lệnh `--sobel-threshold` chính vì vậy.

**C6. Hỏi: Độ phức tạp của việc so khớp từng cặp là bao nhiêu? Dataset triệu ảnh thì sao?**
Đáp: Gom nhóm hiện tại so từng cặp nên O(n²) phép so Hamming — mỗi phép rất rẻ (XOR + đếm bit) nên quy mô học phần/hàng nghìn ảnh vẫn ổn. Lên quy mô lớn phải dùng cấu trúc chỉ mục Hamming như multi-index hashing (chia hash thành nhiều đoạn, tra bảng băm từng đoạn) hoặc BK-tree — nhóm đã biết hướng này và ghi trong phần mở rộng, không cài đặt vì ngoài phạm vi.
Bẫy: thừa nhận giới hạn kèm hướng giải có nguồn (Norouzi et al., multi-index hashing) tốt hơn nhiều so với nói "vẫn chạy được".

**C7. Hỏi: Ảnh trống/rỗng được phát hiện thế nào?**
Đáp: Hàm kiểm tra độ lệch chuẩn của pixel: ảnh có std dưới ngưỡng 1.0 coi là trống/đơn sắc. Ảnh như vậy cũng là trường hợp biên của hash: bản đồ cạnh toàn 0 khiến edge hash bằng 0 — và luật tích hợp quy định hash 0 thì không được quyền quyết định (xem D3).
Bẫy: nối được health check với trường hợp biên của edge hash cho thấy hiểu hệ thống tổng thể.

**C8. Hỏi: Vì sao dự án chỉ dùng Pillow + numpy, không dùng OpenCV?**
Đáp: Đó là ràng buộc thiết kế có chủ đích của dự án gốc: phụ thuộc tối thiểu, cài đặt nhẹ, hành vi xác định và dễ kiểm chứng bằng test. Mọi phép cần thiết (resize Lanczos, DCT, chập 3×3) đều cài được gọn bằng numpy. Đổi lại, nhóm tự cài Sobel bằng cộng-dịch mảng thay vì gọi `cv2.Sobel` — và đó cũng là yêu cầu học thuật của bài tập lớn: hiểu thuật toán chứ không chỉ gọi thư viện.
Bẫy: câu hỏi này gần như chắc chắn xuất hiện ("sao không dùng OpenCV cho nhanh"). Trả lời theo ràng buộc dự án + mục đích học thuật, đừng nói "OpenCV khó cài".

**C9. Hỏi: Gom nhóm trùng có tính bắc cầu không? A giống B, B giống C nhưng A không giống C thì sao?**
Đáp: Có hiện tượng dây chuyền (chaining): thuật toán gom theo quan hệ từng cặp nên A và C có thể vào cùng nhóm qua B dù khoảng cách trực tiếp vượt ngưỡng. Đây là đặc tính đã biết của gom nhóm theo ngưỡng từng cặp; với mục đích cảnh báo rò rỉ, thiên về bắt thừa còn hơn bỏ sót là chấp nhận được, và báo cáo của công cụ để người dùng xét duyệt cuối.
Bẫy: đừng phủ nhận. Thừa nhận + giải thích đánh đổi precision/recall theo mục đích công cụ là đáp án trưởng thành.

**C10. Hỏi: Hai ảnh khác nhau hoàn toàn có thể cho hash giống nhau không?**
Đáp: Có thể về nguyên lý — 64 bit là không gian hữu hạn và hash cảm nhận cố ý "nén" thông tin, nên va chạm tồn tại; xác suất hai ảnh tự nhiên ngẫu nhiên rơi dưới ngưỡng 10 là rất thấp (phân phối khoảng cách tập trung quanh 32). Vì vậy hash cảm nhận là tín hiệu sàng lọc, không phải bằng chứng tuyệt đối — công cụ báo cáo để người dùng xác nhận.
Bẫy: phân biệt va chạm hash mật mã (bảo mật) với va chạm hash cảm nhận (thống kê) — đừng trộn hai khái niệm.

---

## Phần D — Tích hợp Sobel: vòng 2.5 (Trí)

**D1. Hỏi: Tóm lại em đã sửa những file nào, thêm những gì?**
Đáp: Bốn điểm chạm: `extractors.py` thêm `sobel_magnitude`, `sobel_magnitude_image`, `edge_hash`, `edge_energy`; `matchers.py` thêm tham số `edge_threshold` và luật quyết định bằng edge hash; `core.py` thêm tham số `sobel_verify=False`, `sobel_threshold=10` và ghi vào báo cáo; `cli.py` thêm cờ `--sobel-verify`, `--sobel-threshold`. Cộng 14 test mới trong `tests/test_sobel.py`; toàn bộ 88 test đạt. Mặc định tắt nên hành vi cũ không đổi.
Bẫy: thuộc danh sách này là bắt buộc — GV hỏi câu này để kiểm tra ai thực sự làm phần tích hợp.

**D2. Hỏi: Vì sao Sobel chỉ làm lớp xác minh mà không thay hẳn pHash/dHash?**
Đáp: Ba lý do: (1) edge hash nhìn cấu trúc cạnh, mù về bố cục sáng tổng thể mà pHash nắm tốt — hai tín hiệu bổ sung, không thay thế; (2) tích hợp dạng xác minh giữ nguyên hành vi mặc định và toàn bộ test cũ, đúng nguyên tắc không phá vỡ hệ thống đang chạy; (3) có những ảnh edge hash không dùng được (bằng 0) nên nó không thể là tín hiệu duy nhất.
Bẫy: trả lời "vì chưa kịp làm" là tự hạ thấp thiết kế. Đây là quyết định kiến trúc có lý do.

**D3. Hỏi: Luật quyết định chính xác là gì? Trường hợp biên ra sao?**
Đáp: Khi so một cặp: nếu cả hai ảnh đều có edge hash thật (khác 0) thì khoảng cách edge hash quyết định — dưới ngưỡng thì cứu cặp mà pHash/dHash bỏ lỡ, trên ngưỡng thì phủ quyết cặp mà pHash/dHash tưởng trùng. Nếu một trong hai edge hash bằng 0 hoặc thiếu, quay về luật cũ. Cặp trùng chính xác theo MD5 không bị luật này động vào. Edge hash bằng 0 xảy ra khi bản đồ độ lớn cạnh đều (ảnh đơn sắc, gradient tuyến tính, bàn cờ đều) — trung vị làm ngưỡng khiến mọi bit bằng nhau.
Bẫy: thuộc trường hợp "bàn cờ/gradient đều → hash 0" — đây là chi tiết chỉ người đọc kỹ code mới biết, GV rất thích hỏi.

**D4. Hỏi: edge_hash xây thế nào, từng bước? Vì sao dùng độ lớn mà không dùng Gx, Gy có dấu?**
Đáp: Tính độ lớn Sobel trên ảnh xám 32×32, chia thành lưới 8×8 khối và lấy trung bình từng khối, lấy trung vị 64 giá trị làm ngưỡng, khối nào trên trung vị thì bit 1. Dùng độ lớn vì Gx/Gy có dấu sẽ đổi dấu khi đảo tông màu ảnh, còn độ lớn thì không — đó là gốc của kết quả âm bản lệch 0 bit. Việc thu về lưới 8×8 trước khi nhị phân hóa cũng làm hash bền với xê dịch nhỏ và nhiễu.
Bẫy: nếu hỏi "sao không hash trực tiếp trên bản đồ cạnh đầy đủ" — vì cần đúng định dạng 64 bit để dùng chung khoảng cách Hamming và ngưỡng với hai hash hiện có.

**D5. Hỏi: edge_energy là gì, đo được gì?**
Đáp: Là trung bình độ lớn Sobel trên ảnh thu về 128×128 — một chỉ số "năng lượng cạnh". Ảnh mờ mất tần số cao nên năng lượng sụt (mờ Gaussian r=2 còn 0,58×; làm mờ r=3 trong kiểm chứng code còn ~0,47×), ảnh tăng nét thì năng lượng tăng (1,42×). Ứng dụng: thêm một kiểm tra sức khỏe ảnh (ảnh mờ bất thường) vào pipeline, ngoài kiểm tra ảnh trống hiện có.
Bẫy: phân biệt hai con số 0,58× (thực nghiệm r=2) và 0,47× (test đơn vị r=3) — đừng trộn.

**D6. Hỏi: Vì sao không dùng Canny làm hash thay Sobel?**
Đáp: Canny cho bản đồ cạnh nhị phân mỏng — rất nhạy với tham số ngưỡng và biến đổi nhỏ làm cạnh đứt/nối khác hẳn, nên kém ổn định để xây hash. Độ lớn Sobel là trường liên tục, thay đổi từ từ theo biến đổi ảnh, phù hợp để lấy trung bình khối và nhị phân hóa. Canny mạnh ở định vị cạnh chính xác, không phải ở tính ổn định thống kê.
Bẫy: câu này kiểm tra hiểu biết chọn công cụ theo mục đích, không phải thuật toán nào "xịn hơn".

**D7. Hỏi: Vì sao không dùng mô hình học sâu (embedding CLIP) cho chắc?**
Đáp: Ngoài phạm vi và trái ràng buộc của dự án: embedding cần trọng số mô hình, GPU để chạy nhanh, và phá tính xác định/nhẹ của công cụ. Hash cổ điển chạy CPU, không phụ thuộc ngoài numpy/Pillow, kết quả tái lập hoàn toàn. Nhóm ghi nhận embedding là hướng mạnh hơn cho crop/xoay trong tương lai, nhưng đó là dự án khác.
Bẫy: trả lời thực tế về ràng buộc thay vì chê học sâu — GV có thể là người ủng hộ hướng embedding.

**D8. Hỏi: Tích hợp có làm chậm hệ thống không?**
Đáp: edge hash chỉ tính khi bật `--sobel-verify`, trên ảnh đã thu về 32×32 nên chi phí không đáng kể so với DCT của pHash; phép chập 3×3 cài bằng cộng các mảng dịch chuyển (không vòng lặp theo pixel trong Python) nên vector hóa hoàn toàn. Hành vi mặc định (không bật cờ) không đổi chi phí.
Bẫy: thuộc chi tiết "cộng-dịch mảng" — đó là cách `_conv3x3` được cài trong code.

---

## Phần E — Thực nghiệm và số liệu (Ý)

**E1. Hỏi: Vì sao thực nghiệm trên ảnh tổng hợp (fixture) mà không phải ảnh chụp thật?**
Đáp: Fixture `photo_like` của bộ test cho môi trường kiểm soát được: biết chắc ảnh gốc và từng biến đổi áp lên nó, nên khoảng cách đo được quy đúng về biến đổi đó. Ảnh thật lẫn nhiều biến đổi cùng lúc, không tách được nguyên nhân. Hạn chế này đã ghi trong báo cáo: kết luận định lượng gắn với fixture; bước kiểm chứng tiếp theo là bộ ảnh chụp thật có gán nhãn trùng/không trùng.
Bẫy: đừng nói "ảnh thật không có sẵn" — lý do đúng là kiểm soát biến; và phải thừa nhận hạn chế ngoại suy.

**E2. Hỏi: Thuộc lòng ba con số quan trọng nhất của thực nghiệm?**
Đáp: Âm bản: pHash 62, dHash 64, edge hash 0 (trên 64 bit). Crop 10%: 24/15/14. Ảnh khác hẳn: 26/20/22. Ngưỡng quyết định là 10.
Bẫy: ba bộ số này là "CMND" của bài — cả nhóm đều phải thuộc, không riêng người phụ trách Chương 5.

**E3. Hỏi: Vì sao ảnh âm bản làm pHash lệch gần như toàn bộ bit?**
Đáp: pHash nhị phân hóa hệ số DCT theo trung vị; đảo tông màu gần như đảo dấu quan hệ lớn–nhỏ của các hệ số tần thấp, nên hầu hết bit lật theo — 62/64. dHash tệ nhất (64/64) vì mọi hiệu pixel kề đều đổi dấu. Độ lớn gradient thì không: đảo tông đổi dấu Gx, Gy nhưng độ lớn √(Gx²+Gy²) giữ nguyên, nên edge hash lệch 0.
Bẫy: giải thích phải đi từ cơ chế, không chỉ đọc số. Đây là câu hỏi trung tâm của cả bài.

**E4. Hỏi: Trường hợp biên nào đáng lo nhất trong bảng kết quả?**
Đáp: Tăng sáng mạnh cho edge distance đúng bằng 10 — ngay ngưỡng quyết định: cặp này đứng trên lằn ranh, đổi ngưỡng một chút là đổi kết luận. Và nhóm crop/lật/ảnh khác nằm ở vùng 14–44, gần nhau — cho thấy với biến đổi hình học, cả ba hash đều yếu và không nên kết luận quá tay.
Bẫy: GV hỏi câu này để xem nhóm có biết tự phê bình kết quả của mình không. Đáp án "mọi thứ đều tốt" là đáp án tệ nhất.

**E5. Hỏi: Vì sao JPEG nén mạnh (q40) và nhiễu σ12 lại cho khoảng cách 0?**
Đáp: Cả ba hash đều thu nhỏ ảnh mạnh trước khi tính (32×32 hoặc 9×8) — bước thu nhỏ tự nó đã trung bình hóa nhiễu và loại chi tiết tần cao mà JPEG phá. pHash còn chỉ giữ tần số thấp nên càng bền. Đây là tính chất của pipeline hash nói chung, không riêng Sobel.
Bẫy: đừng nhận công riêng cho Sobel ở hai trường hợp này — trung thực về đóng góp là điểm cộng.

**E6. Hỏi: Vì sao crop và lật làm cả ba hash cùng thua?**
Đáp: Cả ba đều là hash toàn cục: thống kê trên toàn ảnh. Crop bỏ một phần ảnh làm thay đổi mọi thống kê toàn cục; lật ngang đảo thứ tự không gian mà hash ghi theo vị trí cố định. Muốn xử lý phải đổi họ phương pháp: đặc trưng cục bộ (SIFT + đối sánh hình học RANSAC — đã có trong ROADMAP của dự án) hoặc biến thể băm theo mọi hướng lật/xoay (D4 trong DataEval). Nhóm chọn ghi rõ giới hạn thay vì giấu.
Bẫy: thuộc hai hướng giải (SIFT/RANSAC, D4) — hỏi tiếp "vậy làm sao sửa" mà bí là mất điểm phần kết luận.

**E7. Hỏi: Thực nghiệm có kiểm chứng thống kê không? Một ảnh gốc có đủ không?**
Đáp: Chưa đủ cho kết luận thống kê — đây là thực nghiệm minh họa cơ chế trên một ảnh gốc có kiểm soát, với 17 trường hợp biến đổi có hệ thống. Muốn nâng lên mức đánh giá thật cần: nhiều ảnh gốc, cặp trùng/không trùng có nhãn, và vẽ đường cong theo ngưỡng (tỉ lệ bắt đúng/báo giả khi ngưỡng thay đổi) thay vì một ngưỡng 10 cố định. Nhóm nêu đây là hướng hoàn thiện đầu tiên.
Bẫy: câu hỏi về tính khoa học của thực nghiệm — thừa nhận đúng mức, kèm kế hoạch cụ thể, tuyệt đối không cãi "một ảnh là đủ".

**E8. Hỏi: Nếu tăng ngưỡng Hamming lên 15 thì chuyện gì xảy ra?**
Đáp: Bắt thêm được vài trường hợp biên (như tăng sáng ở mức 10) nhưng rủi ro báo giả tăng: ảnh khác hẳn có trường hợp ở 20 nên chưa chạm, song khoảng an toàn co lại; với ảnh thật đa dạng, vùng khoảng cách của ảnh khác sẽ rộng hơn và dễ lấn ngưỡng. Ngưỡng là đánh đổi recall/precision — vì thế dự án để nó là tham số, không khóa cứng.
Bẫy: trả lời phải có hai phía (được gì/mất gì), một phía là chưa đạt.

---

## Phần F — Câu hỏi xoáy về dự án, quá trình và mở rộng

**F1. Hỏi: Bài này khác gì gọi `cv2.Sobel` rồi so hai ảnh?**
Đáp: Ba khác biệt: (1) Sobel được cài từ đầu bằng numpy theo đúng công thức, không gọi thư viện thị giác; (2) đóng góp nằm ở cách biến độ lớn Sobel thành hash 64 bit tương thích hệ thống Hamming hiện có và luật xác minh hai chiều (cứu + phủ quyết) tích hợp vào thuật toán gom nhóm — đó là thiết kế hệ thống, không phải một lời gọi hàm; (3) có thực nghiệm định lượng đối đầu ba loại hash trên 17 trường hợp và 88 test kiểm chứng.
Bẫy: đây là câu hỏi "điểm mới ở đâu" — trả lời phải chỉ đúng ba lớp: cài đặt, thiết kế tích hợp, kiểm chứng.

**F2. Hỏi: Đóng góp mới thật sự là gì, nói một câu?**
Đáp: Chứng minh bằng thực nghiệm rằng một lớp xác minh dựa trên độ lớn gradient Sobel bắt được lớp trùng đã đổi tông màu mạnh (điển hình là âm bản) mà cả pHash và dHash đều bỏ qua hoàn toàn, mà không làm thay đổi hành vi mặc định của công cụ.
Bẫy: thuộc câu này nguyên văn cũng được — đây là câu "thang máy" của cả nhóm.

**F3. Hỏi: Nếu cho thêm hai tuần, em làm gì tiếp?**
Đáp: Theo thứ tự: (1) đánh giá trên bộ ảnh thật có nhãn + quét ngưỡng để chọn ngưỡng theo số liệu; (2) thử biến thể D4 cho lật/xoay 90°; (3) nguyên mẫu vòng trùng từng phần bằng SIFT + RANSAC theo ROADMAP; (4) chỉ mục Hamming khi dữ liệu lớn. Thứ tự này đi từ kiểm chứng → mở rộng khả năng → mở rộng quy mô.
Bẫy: trả lời có thứ tự ưu tiên và lý do; liệt kê ngang hàng mọi thứ là chưa đạt.

**F4. Hỏi: Phần việc của từng thành viên là gì?** (hỏi từng người)
Đáp (mỗi người trả lời phần mình, theo bản phân công đã nộp): Tân — lý thuyết Sobel và Chương 2; Kiệt — tổng quan 14 chủ đề, Mở đầu và Chương 1; Trí — kiến trúc VisionCleanse, thiết kế và cài đặt vòng 2.5, Chương 3–4, tổng hợp; Ý — thiết kế và phân tích thực nghiệm, Chương 5–6, định dạng và slide. Ai cũng phải nói được phần mình sâu hơn các phần khác ít nhất hai lớp câu hỏi.
Bẫy: GV hỏi chéo người không phụ trách là bình thường — vì vậy các con số cốt lõi (62/64/0, ngưỡng 10, luật D3) cả 4 người đều phải thuộc.

**F5. Hỏi: Tài liệu tham khảo của em có Wikipedia — có đáng tin không?**
Đáp: Wikipedia chỉ dùng để tra cứu nhanh công thức và quy ước; các khẳng định chính đều neo vào nguồn gốc: tài liệu của chính Sobel cho toán tử, luận văn Zauner cho pHash, bài báo Patterns 2023 cho rò rỉ dữ liệu, tài liệu chính thức OpenCV cho cài đặt thư viện, và mã nguồn của chính dự án cho mọi khẳng định về hệ thống. Danh mục tài liệu đã nộp kèm báo cáo ghi rõ vai trò từng nguồn.
Bẫy: đừng biện hộ Wikipedia là nguồn chính; cho thấy hệ thống phân tầng nguồn là đáp án đúng.

**F6. Hỏi: Sobel có còn dùng trong thời đại học sâu không, hay lỗi thời?**
Đáp: Còn, ở ba vai trò: (1) tiền xử lý/đặc trưng rẻ cho hệ thống nhỏ và thiết bị biên; (2) thành phần bên trong các thuật toán khác (Canny dùng Sobel tính gradient; HOG xây trên gradient); (3) lớp đầu của CNN học ra các bộ lọc rất giống bộ dò cạnh kiểu Sobel/Gabor — cho thấy gradient bậc nhất là đặc trưng nền của thị giác nói chung. Trong bài toán của nhóm (công cụ nhẹ, không GPU, kết quả xác định) Sobel là lựa chọn hợp lý, không phải hoài cổ.
Bẫy: câu hỏi "phản biện thời đại" — trả lời cân bằng, có ví dụ cụ thể, tránh hai cực đoan.

**F7. Hỏi: Độ lớn gradient bất biến với những biến đổi nào, và không bất biến với những biến đổi nào?**
Đáp: Bất biến (gần đúng) với: đảo tông/âm bản (chính xác tuyệt đối), cộng/trừ độ sáng đều, và bền với thay đổi tương phản/gamma vừa phải vì quan hệ thứ tự quanh trung vị được giữ. Không bất biến với: biến đổi hình học (crop, lật, xoay, phối cảnh) vì vị trí không gian thay đổi; mờ mạnh làm giảm độ lớn toàn cục (dù hash theo trung vị vẫn bền ở mức vừa — blur cho khoảng cách 2).
Bẫy: câu hỏi tổng kết lý tưởng cho cuối buổi — trả lời theo hai cột bất biến/không bất biến, mỗi ý kèm một con số thực nghiệm.

**F8. Hỏi: Vì sao nhóm chọn Sobel mà không chọn các chủ đề khác trong 14 chủ đề?**
Đáp: Vì tiêu chí khớp với tài sản có sẵn: dự án VisionCleanse đã có sẵn dHash — một dạng gradient thô — và pHash dùng ngưỡng trung vị thuộc nhóm thresholding; Sobel là bước nâng tự nhiên của cả hai mạch đó, cho phép vừa học lý thuyết học phần vừa tạo đóng góp đo được trên dự án thật. Các chủ đề còn lại (gamma, histogram, bit-plane) không có điểm bám tương đương trong dự án.
Bẫy: đây là câu hỏi mở đầu thường gặp — trả lời bằng tiêu chí lựa chọn, không phải "vì Sobel dễ".

---

## Phụ lục — Hỏi nhanh 1 câu (thuộc lòng)

| Hỏi | Đáp 1 câu |
|---|---|
| Kernel Gx của Sobel? | [[−1,0,1],[−2,0,2],[−1,0,1]] — Gy là bản chuyển vị đổi dấu tương ứng. |
| Sobel năm nào, của ai? | 1968, Irwin Sobel & Gary Feldman, tại SAIL (Stanford). |
| Ngưỡng Hamming mặc định của dự án? | 10 trên 64 bit, cho cả pHash, dHash và edge hash. |
| Âm bản: ba khoảng cách? | pHash 62, dHash 64, edge hash 0. |
| Edge hash bằng 0 khi nào? | Khi bản đồ độ lớn cạnh đều — ảnh đơn sắc, gradient tuyến tính, bàn cờ đều. |
| Toàn bộ test có bao nhiêu, đạt bao nhiêu? | 88 test, đạt cả 88 (14 test mới cho Sobel). |
| dHash dùng kernel gì? | [−1, +1] — hiệu pixel kề phải, gradient thô nhất. |
| pHash dựa trên biến đổi nào? | DCT 2D trên ảnh 32×32, giữ khối tần thấp 8×8, ngưỡng trung vị (Zauner 2010). |
| Cờ bật xác minh Sobel? | `--sobel-verify`, chỉnh ngưỡng bằng `--sobel-threshold`. |
| Ảnh mờ r=2: năng lượng cạnh còn mấy? | 0,58× so với ảnh gốc. |
| Giới hạn lớn nhất của cả ba hash? | Biến đổi hình học: crop, lật, xoay. |
| Rò rỉ dữ liệu — nguồn nào chứng minh? | Kapoor & Narayanan, Patterns 2023: 294 bài báo, 17 lĩnh vực. |
