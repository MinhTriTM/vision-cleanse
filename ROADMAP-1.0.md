# Lộ trình VisionCleanse: 0.3.0 → 1.0.0 — từ công cụ dọn dataset thành hệ sinh thái

Tài liệu này là **kế hoạch phiên bản** đi kèm `STRATEGY.md` (chiến lược).
`STRATEGY.md` trả lời "VisionCleanse là gì và vì sao tồn tại";
tài liệu này trả lời "từng phiên bản làm gì, theo thứ tự nào, và đo xong
bằng tiêu chí nào".

## 1. Tầm nhìn: không chỉ lõi, mà là hệ sinh thái

VisionCleanse 1.0.0 không phải là "công cụ dedup chạy nhanh hơn".
Nó là một hệ sinh thái dọn dataset gồm 3 lớp:

- **Lớp lõi (core engine):** phát hiện trùng lặp và rò rỉ split, chính xác,
  xác định (deterministic), không bao giờ xóa cứng dữ liệu người dùng.
- **Lớp hỗ trợ (supporting modules):** những thứ biến lõi thành quy trình
  làm việc được: cấu hình, cache, chạy tăng dần, review tương tác,
  nhiều định dạng annotation, tích hợp framework, chạy trong CI.
- **Lớp bề mặt hệ sinh thái (ecosystem surface):** những thứ để người
  khác xây tiếp trên VisionCleanse: plugin, benchmark công khai,
  demo thử nhanh, tích hợp vào pipeline của họ mà không cần sửa code nguồn.

Xuyên suốt 3 lớp là **tuyến nghiên cứu thuật toán**: không chỉ lắp ghép
thuật toán có sẵn (hash, FAISS, SIFT), mà tự nghiên cứu thuật toán mới
cho những ca mà công cụ hiện tại bó tay (mục 5).

## 2. Nguyên tắc không đổi (mọi phiên bản đều phải giữ)

1. **Dry-run mặc định.** Chỉ `--apply` mới di chuyển file.
2. **Không xóa cứng.** File bị loại đi vào quarantine kèm `manifest.json`,
   khôi phục được.
3. **Xác định.** Cùng input cho cùng output, mọi lần chạy.
4. **Ưu tiên split: test > val > train.** Không bao giờ để rò rỉ vào test.
5. **Xung đột nhãn không tự xóa.** Giữ nguyên, ghi vào báo cáo.
6. **Benchmark trước, thuật toán sau.** Thuật toán mới chỉ được merge
   khi thắng baseline trên benchmark đóng băng (mục 5.7). Không chỉnh
   ngưỡng trên tập test — bài học từ cặp false positive ở đúng ngưỡng
   dHash trong benchmark 500 ảnh (xem `docs/benchmark.md`).
7. **Số liệu trung thực.** Chỉ ghi số đo được kèm điều kiện đo. Không
   bao giờ ghi "sạch 100%" hay "bắt mọi trường hợp".
8. **Dependency nặng là extra tùy chọn.** Lõi chỉ cần Pillow + numpy.
   Deep learning, FAISS, WeasyPrint đều nằm ở extra.

## 3. Bản đồ phiên bản 0.3.0 → 1.0.0

### 0.3.0 — Nền tảng tin cậy (hoàn tất Giai đoạn 1 của STRATEGY.md)

Mục tiêu: người lạ vào repo cũng tin được và cài được.

- [ ] PyPI pending trusted publisher + phát hành PyPI đầu tiên (0.3.0).
- [ ] GitHub Pages live (Source: GitHub Actions) cho docs MkDocs.
- [ ] CHANGELOG có kỷ luật: mỗi release ghi rõ thêm/sửa/phá vỡ.
- [ ] Chính sách version: semver từ 0.3.0 trở đi; dòng "Phiên bản hiện
      tại" trong README bump theo từng commit (quy tắc đã chốt).
- Tiêu chí xong: `pip install vision-cleanse` chạy được, docs đọc được
  trên Pages, CI xanh, benchmark có số.

### 0.4.0 — Lõi nhanh hơn, cấu hình được

Mục tiêu: chạy dataset lớn mà không quét lại từ đầu mỗi lần.

- [ ] Đa tiến trình cho bước đọc ảnh và băm (I/O-bound).
- [ ] Cache đặc trưng: chạy dở thì chạy tiếp không trích xuất lại.
- [ ] Chế độ tăng dần (incremental): dataset thêm ảnh mới thì chỉ kiểm
      tra phần mới so với phần cũ.
- [ ] File cấu hình (TOML/YAML) thay cho chỉ dùng cờ dòng lệnh.
- Tiêu chí xong: quét lần 2 trên dataset đã quét (thêm 10% ảnh mới)
  nhanh hơn quét từ đầu một cách đo được; cấu hình file cho kết quả
  giống hệt cấu hình cờ.

### 0.5.0 — Lõi sâu hơn (vòng deep + xác minh hình học)

Mục tiêu: bắt được những ca mà hash cổ điển bó tay.

- [ ] Vòng deep: đặc trưng sâu (CLIP/EfficientNet) + FAISS, dạng
      extra `[deep]`.
- [ ] Tầng xác minh hình học: SIFT + RANSAC sau bước tìm ứng viên,
      để giảm false positive trước khi quarantine.
- [ ] Vòng trùng từng phần: xử lý crop sâu và xoay/lật bằng xác minh
      hình học (nền tảng cho thuật toán R5 ở mục 5).
- Tiêu chí xong: trên benchmark biến thể tự sinh, recall trên nhóm
  crop/xoay tăng đo được so với 0.4.0, precision không giảm.

### 0.6.0 — Định dạng và tích hợp (bắt đầu lớp hỗ trợ)

Mục tiêu: VisionCleanse cắm được vào pipeline thật của người khác.

- [ ] Thêm định dạng annotation: Pascal VOC, LabelMe (hiện có YOLO, COCO).
- [ ] Tích hợp Hugging Face `datasets`: đọc/ghi dataset trực tiếp.
- [ ] Plugin registry: extractor, checker, reporter đăng ký được từ
      ngoài mà không sửa code nguồn (nền tảng cho hệ sinh thái).
- [ ] Reusable GitHub Action + pre-commit hook: chạy VisionCleanse
      trong CI của repo khác.
- [ ] Docker image chính thức cho chạy batch/CI.
- Tiêu chí xong: có ít nhất một pipeline ngoài dùng VisionCleanse qua
  API hoặc CLI mà không cần sửa code nguồn.

### 0.7.0 — Review tương tác (con người quyết, máy đề xuất)

Mục tiêu: biến báo cáo tĩnh thành quy trình duyệt.

- [ ] Báo cáo HTML tương tác: xem từng nhóm trùng, bấm giữ/xóa từng
      ảnh, duyệt hàng loạt, hoàn tác (undo) từ manifest.
- [ ] Báo cáo PDF (từ cùng dữ liệu với HTML) và SARIF (để CI khác
      đọc được kết quả).
- [ ] Health suite mở rộng: thêm kiểm tra theo yêu cầu từ issue thực tế.
- Tiêu chí xong: một dataset 15.000 ảnh có thể được duyệt xong bằng
  UI mà không cần chạm vào quarantine bằng tay.

### 0.8.0 — Nghiên cứu 1: thuật toán mới nhóm A (mục 5)

Mục tiêu: 3 thuật toán tự nghiên cứu đầu tiên được chứng minh bằng số.

- [ ] R1 — Ngưỡng thích ứng theo phân phối (adaptive threshold).
- [ ] R2 — Hợp nhất hash có trọng số học được (learned hash fusion).
- [ ] R3 — Dedup nhạy nhãn (label-aware grouping).
- Tiêu chí xong: mỗi thuật toán thắng baseline trên benchmark đóng băng
  (tiêu chí cụ thể ở mục 5) và có mục riêng trong `docs/benchmark.md`.

### 0.9.0 — Quy mô và nghiên cứu 2

Mục tiêu: dataset rất lớn và trùng từng phần khó.

- [ ] R4 — Split-surgeon: sửa rò rỉ tối ưu thay vì chỉ quarantine.
- [ ] R5 — Đối sánh vùng cho trùng từng phần (crop sâu, ảnh ghép,
      meme chữ đè).
- [ ] R6 — Nhúng tương phản tự học (contrastive embedding dedup).
- [ ] Hỗ trợ frame video (trích frame rồi dedup) nếu có nhu cầu thực.
- [ ] Kiểm thử hiệu năng và bộ nhớ ở quy mô 100k ảnh (bước đệm cho
      1M ảnh ở 1.0.0).
- Tiêu chí xong: R4/R5/R6 đều có số benchmark công khai; quét 100k
  ảnh trong thời gian và bộ nhớ đo được, công bố kèm điều kiện đo.

### 1.0.0 — Ổn định và cam kết

Mục tiêu: người khác xây dựng dài hạn trên VisionCleanse mà không sợ
đổi API.

- [ ] Đóng băng API công khai (`clean()`, CLI, định dạng report).
- [ ] Chính sách deprecation bằng văn bản, lịch bỏ Python cũ.
- [ ] Tài liệu đầy đủ, ví dụ chạy thật, CITATION.cff + DOI Zenodo.
- [ ] Kiểm thử hiệu năng và bộ nhớ ở quy mô 1M ảnh.
- [ ] Audit bảo mật: dependency, secrets, quyền workflow.
- Tiêu chí xong: phát hành 1.0.0; từ đó mọi thay đổi phá vỡ đều phải
  lên major mới.

### Sau 1.0 — Cộng đồng

- Plugin cho framework khác (PyTorch Lightning, Ultralytics...).
- Demo web (Gradio) để thử nhanh không cần cài đặt.
- Nhận maintainer phụ khi có đóng góp thường xuyên.

## 4. Bản đồ module của hệ sinh thái (đích đến 1.0.0)

```
vision-cleanse (PyPI)
├── Lõi (luôn có, chỉ cần Pillow + numpy)
│   ├── clean() — engine 5 vòng + vòng deep (extra)
│   ├── split priority test > val > train, quarantine + manifest
│   ├── health checks (11 kiểm tra + diagnostics nhãn)
│   └── report.json / report.html / charts
├── Hỗ trợ (theo phiên bản ở mục 3)
│   ├── config TOML/YAML, cache đặc trưng, incremental
│   ├── review UI tương tác (giữ/xóa/undo), PDF, SARIF
│   ├── annotation: YOLO, COCO, Pascal VOC, LabelMe
│   ├── HF datasets, video frames
│   └── Action GitHub, pre-commit hook, Docker image
└── Bề mặt hệ sinh thái
    ├── plugin registry (extractor / checker / reporter)
    ├── benchmark suite công khai + leaderboard trong docs
    ├── demo Gradio (sau 1.0), plugin framework (sau 1.0)
    └── docs site (MkDocs), CHANGELOG, CITATION.cff + DOI
```

Nguyên tắc phân lớp: lớp trên được phép phụ thuộc lớp dưới, không
ngược lại. Lõi không bao giờ import module hỗ trợ hay bề mặt.

## 5. Tuyến nghiên cứu thuật toán mới

Hiện trạng baseline cần đánh bại: engine 5 vòng — exact bằng
MD5/SHA-256, near bằng pHash + dHash với luật OR (một trong hai
≤ 10 là trùng), keeper xác định, split priority test > val > train.
Mọi thuật toán dưới đây đều là **giả thuyết nghiên cứu**, chưa phải
kết quả đã chứng minh. Mỗi thuật toán chỉ được merge khi thắng
baseline theo đúng tiêu chí của nó.

### R1 — Ngưỡng thích ứng theo phân phối (0.8.0)

- **Vấn đề:** ngưỡng cố định (≤ 10) do người dùng chọn, đổi dataset
  là đổi miền dữ liệu — ngưỡng tốt trên dataset này thành dở trên
  dataset khác, sinh thêm false positive hoặc false negative.
- **Ý tưởng:** học ngưỡng từ chính dataset đang quét: dựng histogram
  khoảng cách Hamming của các cặp ứng viên, tách hai mode
  (trùng / không trùng) bằng Otsu hoặc GMM 2 thành phần, đặt ngưỡng
  ở điểm tách; fallback về ngưỡng cố định khi phân phối không tách
  được (một mode).
- **Điểm mới:** công cụ hiện tại bắt người dùng tự chọn ngưỡng;
  ở đây ngưỡng tự hiệu chuẩn theo từng dataset, không cần tham số.
- **Kiểm chứng:** benchmark biến thể tự sinh + CrowdHuman, so với
  ngưỡng cố định tốt nhất (được chọn trên tập train, không phải
  test). Kiểm tra cross-dataset (hiệu chuẩn trên dataset A, đo
  trên dataset B).
- **Tiêu chí thắng:** F1 cao hơn baseline ≥ 2 điểm trên cả hai
  dataset, không có dataset nào giảm F1.
- **Rủi ro:** phân phối một mode (dataset toàn ảnh khác nhau) làm
  Otsu đặt ngưỡng bậy → bắt buộc có fallback và kiểm tra "tách
  được hay không" trước khi áp dụng.

### R2 — Hợp nhất hash có trọng số học được (0.8.0)

- **Vấn đề:** luật OR bỏ qua mức độ đồng thuận: một cặp có cả pHash
  và dHash đều ở mức 9 được coi bằng một cặp chỉ có một hash ở mức
  2; tương quan giữa các hash cũng bị bỏ qua.
- **Ý tưởng:** thay OR bằng mô hình nhỏ (logistic regression hoặc
  cây quyết định nông) trên vector [pHash_dist, dHash_dist,
  aHash_dist, wavelet_dist, chênh lệch kích thước, chênh lệch tỉ
  lệ], huấn luyện trên cặp trùng/không trùng từ benchmark biến
  thể tự sinh.
- **Điểm mới:** từ luật cứng sang quyết định học được, nhưng vẫn
  giải thích được (trọng số đọc được, không phải hộp đen).
- **Kiểm chứng:** AUC + F1 so với luật OR trên cùng benchmark;
  kiểm tra overfit bằng cross-dataset (train biến thể tự sinh,
  test CrowdHuman và ngược lại).
- **Tiêu chí thắng:** F1 cao hơn OR ≥ 2 điểm và AUC cao hơn, trên
  cả hai chiều cross-dataset.
- **Rủi ro:** overfit vào biến thể tự sinh → bắt buộc cross-dataset
  và giữ mô hình nhỏ, không dùng mạng sâu ở đây.

### R3 — Dedup nhạy nhãn (0.8.0)

- **Vấn đề:** nhóm trùng hiện chỉ dùng ảnh. Cùng một ảnh mà nhãn
  khác nhau (lỗi gán nhãn) thì engine chỉ ghi "xung đột, giữ
  nguyên" — bỏ phí tín hiệu.
- **Ý tưởng:** đồ thị hai lớp ảnh–nhãn: nhóm trùng phải đồng thuận
  cả ảnh lẫn nhãn. Nhóm ảnh giống nhau nhưng nhãn mâu thuẫn được
  tách thành nhóm riêng và báo cáo như "nghi lỗi nhãn", kèm mức độ
  mâu thuẫn (tỉ lệ nhãn thiểu số trong nhóm).
- **Điểm mới:** biến xung đột nhãn từ "vấn đề cần né" thành "tín
  hiệu phát hiện lỗi nhãn" — dedup và kiểm tra chất lượng nhãn
  trong một lần chạy.
- **Kiểm chứng:** dataset có nhãn nhiễu tổng hợp (đổi nhãn ngẫu
  nhiên 5% và 10%): đo tỉ lệ phát hiện đúng lỗi nhãn và F1 dedup.
- **Tiêu chí thắng:** phát hiện ≥ 80% lỗi nhãn tổng hợp ở mức
  nhiễu 10%, trong khi F1 dedup không giảm so với baseline.
- **Rủi ro:** nhãn đúng nhưng đa nghĩa (một ảnh nhiều nhãn hợp lệ)
  bị báo sai → cần phân biệt "nhãn mâu thuẫn" và "nhãn đa trị"
  bằng ngưỡng tỉ lệ thiểu số.

### R4 — Split-surgeon: sửa rò rỉ tối ưu (0.9.0)

- **Vấn đề:** công cụ hiện tại chỉ quarantine file rò rỉ — dữ liệu
  bị mất, tỉ lệ split và cân bằng class lệch đi.
- **Ý tưởng:** mô hình hoá việc sửa rò rỉ thành bài toán tối ưu:
  với mỗi cụm rò rỉ xuyên split, chọn phương án di chuyển tối
  thiểu (min-cost flow trên đồ thị cụm–split, hoặc ILP nhỏ) sao
  cho: hết rò rỉ, tỉ lệ split lệch ít nhất, cân bằng class lệch
  ít nhất. Kết quả là một "phương án sửa" có thể duyệt trước khi
  áp dụng (dry-run cho cả việc sửa).
- **Điểm mới:** từ "xóa để hết rò rỉ" sang "sửa tối ưu để hết rò
  rỉ mà giữ lại tối đa dữ liệu".
- **Kiểm chứng:** dataset rò rỉ tổng hợp (trộn 5% ảnh train vào
  test): đo % dữ liệu giữ lại, độ lệch cân bằng class, và rò rỉ
  còn lại (= 0 bắt buộc).
- **Tiêu chí thắng:** giữ lại nhiều dữ liệu hơn quarantine-naive
  ≥ 10 điểm phần trăm, độ lệch class nhỏ hơn, rò rỉ = 0.
- **Rủi ro:** ILP đắt trên cụm lớn → giới hạn kích thước cụm,
  cụm quá lớn fallback về quarantine-naive và ghi rõ.

### R5 — Đối sánh vùng cho trùng từng phần (0.9.0)

- **Vấn đề:** hash toàn cục gần như mù trước crop sâu, ảnh ghép,
  meme chữ đè — những ca mà ảnh "gần giống" chỉ ở một vùng.
- **Ý tưởng:** vòng đối sánh vùng độc lập: trích đặc trưng cục bộ
  (SIFT/ORB), khớp điểm, RANSAC tìm phép biến đổi, tính tỉ lệ
  vùng chồng lấp; một cặp là "trùng từng phần" nếu vùng chồng
  lấp vượt ngưỡng và phép biến đổi nhất quán hình học.
- **Điểm mới:** chuyển từ "ảnh có giống nhau không" sang "vùng
  nào của ảnh A xuất hiện trong ảnh B" — phát hiện được cả ảnh
  ghép nhiều nguồn.
- **Kiểm chứng:** benchmark crop/ghép tổng hợp (crop 30–70%, ghép
  2 ảnh, đè chữ): đo recall trên trùng từng phần.
- **Tiêu chí thắng:** recall trên trùng từng phần ≥ 70% trong khi
  precision toàn cục không giảm quá 1 điểm so với baseline.
- **Rủi ro:** đắt tính toán → chỉ chạy vòng này trên ứng viên đã
  qua vòng rẻ (cascade), không chạy trên mọi cặp.

### R6 — Nhúng tương phản tự học (0.9.0)

- **Vấn đề:** hash cổ điển dựa trên cấu trúc tần số/thống kê, kém
  trước biến đổi ngữ nghĩa (đổi nền, đổi màu mạnh, phong cách hoá).
- **Ý tưởng:** huấn luyện embedding nhỏ bằng contrastive learning
  trên cặp biến thể tự sinh (một ảnh gốc + các augmentation của
  nó là cặp dương; ảnh khác là cặp âm), dùng làm vòng deep với
  FAISS thay cho hoặc bổ sung cho CLIP zero-shot.
- **Điểm mới:** embedding được huấn luyện riêng cho nhiệm vụ dedup
  (không phải embedding đa năng như CLIP), nên có thể nhỏ, nhanh,
  và tốt hơn trên miền dữ liệu cụ thể.
- **Kiểm chứng:** so với CLIP zero-shot và với hash cổ điển trên
  cùng benchmark biến thể (bao gồm đổi màu/phong cách).
- **Tiêu chí thắng:** F1 cao hơn CLIP zero-shot ≥ 2 điểm trên
  benchmark biến thể, với mô hình nhỏ hơn CLIP và chạy được trên
  CPU.
- **Rủi ro:** cần dữ liệu huấn luyện lớn và dễ overfit vào
  augmentation tự sinh → kiểm chứng cross-dataset bắt buộc, và
  giữ CLIP làm fallback.

### 5.7. Quản trị tuyến nghiên cứu (để không thành "nghiên cứu giấy")

- Benchmark đóng băng: bộ benchmark biến thể tự sinh + CrowdHuman
  được đóng băng trước khi chạy thuật toán mới; ngưỡng và siêu
  tham số không được chỉnh trên tập test.
- Mỗi thuật toán có một file benchmark riêng trong `docs/benchmark.md`
  ghi đủ: baseline, số mới, điều kiện đo, và trường hợp thất bại
  đã biết.
- Thuật toán không đạt tiêu chí thì không merge, ghi lại lý do và
  giữ trong nhánh nghiên cứu — không xoá kết quả âm.
- Thứ tự ưu tiên: R1 → R2 → R3 (0.8.0, rẻ, ít dependency) rồi mới
  R4 → R5 → R6 (0.9.0, đắt, cần deep/FAISS).

## 6. Chỉ số theo dõi (kế thừa STRATEGY.md §5, thêm chỉ số kỹ thuật)

- Mỗi phiên bản: CI xanh, coverage, thời gian quét 100k ảnh, bộ nhớ
  đỉnh khi quét 100k ảnh.
- Mỗi thuật toán mới: F1/AUC trên benchmark đóng băng, so với
  baseline, kèm điều kiện đo.
- Mỗi tháng: lượt tải PyPI, sao GitHub, contributor, issue mở/đóng
  và thời gian phản hồi trung bình, số dự án ngoài dùng VisionCleanse.

## 7. Rủi ro và cách tránh (kế thừa STRATEGY.md §6, thêm rủi ro mới)

- **Scope creep:** mỗi tính năng mới phải trả lời "nó phục vụ lớp
  nào trong mục 4". Không trả lời được thì cho vào backlog.
- **Nghiên cứu không tới:** R1–R6 đều có tiêu chí thắng rõ ràng;
  không đạt thì dừng, không cố "cứu" bằng cách đổi benchmark.
- **Gánh nặng bảo trì:** dependency nặng là extra; API công khai giữ
  nhỏ; test bao phủ API trước khi thêm tính năng.
- **Hứa quá:** không ghi "sạch 100%" hay "bắt mọi trường hợp". Chỉ
  ghi số đo được kèm điều kiện đo.
- **Đổi API liên tục:** trước 1.0 được phép đổi nhưng ghi rõ trong
  CHANGELOG; sau 1.0 tuân thủ deprecation.
- **Bảo mật:** không nhận token/mật khẩu qua chat; secret chỉ nằm
  trong GitHub Secrets.

## 8. Việc làm ngay tiếp theo (từ 0.3.0)

1. Tạo PyPI pending trusted publisher, phát hành 0.3.0 (bản PyPI
   đầu tiên).
2. Bật GitHub Pages (Source: GitHub Actions) cho docs MkDocs.
3. Đóng băng bộ benchmark biến thể tự sinh làm nền cho tuyến
   nghiên cứu R1–R6.
4. Mở milestone GitHub v0.3.0 và gắn các issue tương ứng.

---
*Tài liệu này mở rộng STRATEGY.md, không thay thế nó. Khi hai tài liệu
lệch nhau, STRATEGY.md là chuẩn về định vị, tài liệu này là chuẩn về
thứ tự phiên bản.*
