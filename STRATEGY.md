# Chiến lược phát triển VisionCleanse — từ MVP tới thư viện chuẩn lớn

Ngày lập: 2026-10-29 · Phiên bản hiện tại: 0.2.0 · Repo: MinhTriTM/vision-cleanse

## 1. Tầm nhìn và định vị

**Tầm nhìn:** VisionCleanse trở thành công cụ chuẩn để làm sạch dataset
Computer Vision trước khi huấn luyện: phát hiện trùng lặp, ngăn rò rỉ
Train/Val/Test, và chứng minh dataset sạch bằng báo cáo kiểm chứng được.

**Điểm khác biệt so với các thư viện hiện có** (imagededup, cleanvision,
cleanlab):
- Không chỉ tìm ảnh trùng, mà **bảo vệ tập đánh giá** bằng luật ưu tiên
  Test > Val > Train.
- **Không bao giờ xóa thẳng:** quarantine + manifest để khôi phục.
- **Đồng bộ annotation:** xóa ảnh thì nhãn YOLO/COCO đi kèm, dataset
  không bị vỡ.
- **Kết luận kiểm chứng được:** báo cáo liệt kê từng kiểm tra đã chạy,
  thay vì hứa "sạch 100%".

Định vị này phải giữ xuyên suốt mọi giai đoạn. Mở rộng tính năng nhưng
không được đánh mất 4 điểm trên.

## 2. Một "thư viện lớn" cần những gì — 6 trụ cột

### 2.1. Chất lượng kỹ thuật
- Test tự động chạy trên mọi pull request, nhiều phiên bản Python và
  nhiều hệ điều hành (GitHub Actions).
- Đo độ bao phủ test (coverage) và công khai số liệu.
- Lint + format thống nhất (ruff), kiểm tra kiểu (mypy) cho API công khai.
- Benchmark hiệu năng: thời gian chạy trên 10k / 100k / 1M ảnh, bộ nhớ
  dùng bao nhiêu, để người dùng biết giới hạn.
- Benchmark độ chính xác: bộ ảnh biến thể tự sinh (resize, nén, crop,
  xoay, đổi màu) với precision/recall theo từng vòng, từng ngưỡng.
  Đây là bằng chứng quan trọng nhất, vì hiện tại ngưỡng 10 chỉ mới đo
  trên ảnh giả lập nhỏ.

### 2.2. Tài liệu
- Trang docs riêng (MkDocs hoặc Sphinx, host miễn phí bằng Read the Docs
  hoặc GitHub Pages): hướng dẫn cài đặt, hướng dẫn nhanh, API reference
  tự sinh từ docstring, ví dụ chạy thật.
- README ngắn gọn, có badge (build, coverage, PyPI version, license).
- CHANGELOG theo chuẩn Keep a Changelog, ghi rõ thay đổi theo từng
  phiên bản, đặc biệt là thay đổi phá vỡ tương thích.
- Hướng dẫn đóng góp (CONTRIBUTING), quy tắc ứng xử (CODE_OF_CONDUCT),
  chính sách bảo mật (SECURITY).

### 2.3. Phân phối
- Phát hành lên PyPI (`pip install vision-cleanse`) với semantic
  versioning nghiêm túc: vá lỗi tăng patch, thêm tính năng tăng minor,
  đổi API không tương thích tăng major.
- Mỗi release có ghi chú, tag Git đúng phiên bản, file wheel + sdist.
- Sau này cân nhắc conda-forge khi có người dùng yêu cầu, không làm sớm.

### 2.4. Cộng đồng và quản trị
- Issue template (báo lỗi, đề xuất tính năng), pull request template.
- Nhãn "good first issue" cho người mới đóng góp.
- Thời gian phản hồi issue/PR có mục tiêu (ví dụ: trả lời trong 1 tuần).
- Từ 1.0 trở đi: chính sách deprecation — API cũ được cảnh báo trước
  ít nhất 2 phiên bản minor rồi mới bỏ, không bỏ đột ngột.
- Ghi nhận đóng góp (CONTRIBUTORS hoặc all-contributors).

### 2.5. Bằng chứng và uy tín
- Bảng so sánh với imagededup/cleanvision trên cùng benchmark: nói rõ
  mình thắng ở đâu, thua ở đâu. Thư viện lớn không né so sánh.
- Ví dụ chạy thật trên dataset công khai (ví dụ: một tập con của COCO
  hoặc CIFAR) với báo cáo mẫu đính kèm.
- Trích dẫn học thuật nếu có thể: file CITATION.cff, đăng ký DOI qua
  Zenodo cho mỗi release lớn. Không bắt buộc sớm, nhưng nên có trước 1.0.

### 2.6. Tính ổn định và hỗ trợ
- Ma trận hỗ trợ công khai: hỗ trợ Python 3.10–3.13, bỏ phiên bản cũ
  theo lịch (khi Python ra bản mới, bỏ bản cũ nhất).
- Chính sách hỗ trợ: phiên bản 1.x được vá lỗi bảo mật trong bao lâu.
- Không thêm dependency nặng vào lõi: torch, FAISS, CLIP phải là
  extra tùy chọn (`pip install vision-cleanse[deep]`), để người chỉ
  cần vòng 1–2 cài nhẹ như hiện tại.

## 3. Lộ trình theo giai đoạn

### Giai đoạn 1 — Nền tảng tin cậy (0.2.x → 0.3.0)
Mục tiêu: người lạ vào repo cũng tin được và cài được.
- [x] GitHub Actions: chạy test trên Python 3.10–3.13, Ubuntu/macOS/Windows (2026-10-29).
- [x] Coverage công khai + ruff + mypy cho API công khai (mypy chạy
  non-blocking cho tới khi API được gõ kiểu đầy đủ).
- [ ] Phát hành PyPI đầu tiên (0.3.0) — chờ bạn tạo pending publisher
  trên PyPI theo `docs/publishing.md`; workflow đã sẵn.
- [x] Trang docs MkDocs + badge README + CHANGELOG.
- [x] Benchmark near-dup đầu tiên: 500 ảnh (100 gốc × 5 biến thể),
  precision 0.9756 / recall 1.0000 — xem `docs/benchmark.md` (có 1 cặp
  false positive ở đúng ngưỡng dHash, không chỉnh ngưỡng theo nó).
- Tiêu chí xong: `pip install vision-cleanse` chạy được, docs đọc được,
  badge xanh, benchmark có số.

### Giai đoạn 2 — Năng lực cốt lõi (0.4.0 → 0.5.0)
Mục tiêu: bắt được những ca mà MVP hiện bó tay.
- [ ] Vòng 3: đặc trưng sâu (CLIP/EfficientNet) + FAISS, dạng extra `[deep]`.
- [ ] Tầng xác minh hình học: SIFT + RANSAC sau bước tìm ứng viên, để
      giảm false positive trước khi quarantine.
- [ ] Vòng 4: xử lý crop sâu và xoay/lật bằng xác minh hình học.
- [ ] Cache vector đặc trưng: chạy dở thì chạy tiếp không trích xuất lại.
- [ ] Đa tiến trình cho bước đọc ảnh và băm (I/O-bound).
- [ ] File cấu hình (TOML/YAML) thay cho chỉ dùng cờ dòng lệnh.
- Tiêu chí xong: bắt được crop/xoay trên benchmark với recall đo được,
  chạy 100k ảnh trong thời gian chấp nhận được.

### Giai đoạn 3 — Mở rộng hệ sinh thái (0.6.0 → 0.9.0)
Mục tiêu: dùng được trong pipeline thật của người khác.
- [ ] Thêm định dạng annotation: Pascal VOC, LabelMe (hiện có YOLO, COCO).
- [ ] Tích hợp Hugging Face `datasets`: đọc/ghi dataset trực tiếp.
- [ ] Chế độ tăng dần (incremental): dataset thêm ảnh mới thì chỉ kiểm
      tra phần mới so với phần cũ, không quét lại từ đầu.
- [ ] Báo cáo HTML tương tác: xem nhóm trùng, bấm giữ/xóa từng ảnh.
- [ ] Hỗ trợ frame video (trích frame rồi dedup) nếu có nhu cầu thực.
- Tiêu chí xong: có ít nhất một pipeline ngoài dùng VisionCleanse qua
  API hoặc CLI mà không cần sửa code nguồn.

### Giai đoạn 4 — Ổn định 1.0
Mục tiêu: cam kết API.
- [ ] Đóng băng API công khai (`clean()`, CLI, định dạng report).
- [ ] Chính sách deprecation bằng văn bản, lịch bỏ Python cũ.
- [ ] Tài liệu đầy đủ, ví dụ chạy thật, CITATION.cff + DOI Zenodo.
- [ ] Kiểm thử hiệu năng và bộ nhớ ở quy mô 1M ảnh.
- Tiêu chí xong: phát hành 1.0.0, từ đó mọi thay đổi phá vỡ đều phải
  lên major mới.

### Sau 1.0 — Cộng đồng
- Plugin cho framework khác (PyTorch Lightning, Ultralytics...).
- Demo web (Gradio) để thử nhanh không cần cài đặt.
- Nhận maintainer phụ khi có đóng góp thường xuyên.

## 4. Cần những gì (nguồn lực)

- **Con người:** 1 maintainer chính (bạn) + reviewer cho PR ngoài.
  Giai đoạn 1–2 làm một mình được; từ giai đoạn 3 nên có thêm người.
- **Thời gian:** giai đoạn 1 khoảng vài buổi tập trung (CI, docs, PyPI,
  benchmark). Giai đoạn 2 là phần nặng nhất (deep learning + FAISS).
- **Tiền bạc:** gần như 0 ở giai đoạn đầu — GitHub Actions, Read the
  Docs, Codecov đều miễn phí cho repo public. PyPI miễn phí.
- **Tài khoản bạn cần tự tạo:** PyPI (để phát hành), Codecov (tùy chọn).
  Token không bao giờ gửi qua chat, chỉ nhập qua kênh bảo mật.
- **Dữ liệu:** bộ benchmark biến thể tự sinh (tự làm được, không cần
  mua dataset) + một dataset công khai để demo.

## 5. Chỉ số theo dõi (KPI)

Theo dõi mỗi tháng một lần, không ám ảnh số liệu ngày:
- Lượt tải PyPI, sao GitHub, số contributor.
- Số issue mở/đóng và thời gian phản hồi trung bình.
- Coverage test, thời gian chạy benchmark 100k ảnh.
- Số dự án ngoài dùng VisionCleanse (ghi vào README khi có).

## 6. Rủi ro và cách tránh

- **Mở rộng quá nhanh (scope creep):** mỗi tính năng mới phải trả lời
  được "nó phục vụ định vị ở mục 1 không". Không thì cho vào backlog.
- **Gánh nặng bảo trì:** dependency nặng phải là extra tùy chọn, API
  công khai giữ nhỏ, test bao phủ API trước khi thêm tính năng.
- **Hứa quá:** không bao giờ ghi "sạch 100%" hay "bắt mọi trường hợp".
  Chỉ ghi số đo được trên benchmark kèm điều kiện đo.
- **Đổi API liên tục:** trước 1.0 được phép đổi nhưng phải ghi rõ trong
  CHANGELOG; sau 1.0 tuân thủ deprecation.
- **Bảo mật:** không bao giờ nhận token/mật khẩu qua chat; secret chỉ
  nằm trong GitHub Secrets.

## 7. Ba việc làm ngay tiếp theo

1. Gắn GitHub Actions chạy test + coverage + lint (không cần bạn làm
   gì thêm sau khi gắn).
2. Tạo tài khoản PyPI, phát hành 0.3.0.
3. Xây bộ benchmark biến thể tự sinh và công bố precision/recall đầu tiên.

Ba việc này xong là VisionCleanse đã khác hẳn một project cá nhân: người
lạ cài được, đọc docs được, và tin được bằng số liệu.
