# Changelog

Tất cả thay đổi đáng chú ý của VisionCleanse được ghi ở đây, theo định
dạng [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Biểu đồ Venn nhóm trùng `duplicate_groups_venn.png` (biểu đồ thứ
  25): đếm mỗi nhóm trùng theo tập split mà members chạm tới (7
  vùng train/val/test); màu vòng cố định RGB, opacity 0.55; skip kèm
  lý do `"no duplicate groups"` khi không có nhóm trùng, vẫn vẽ đủ
  3 vòng khi thiếu split.
- Khóa mới `report["duplicate_groups_detail"]`: danh sách mỗi nhóm
  trùng gồm `group_id`, `method` và `members` (kept + removed, mỗi
  member có `path` và `split`) — nguồn dữ liệu cho biểu đồ Venn.

### Changed
- Toàn bộ 24 biểu đồ cũ được vẽ lại theo style Sáng hiện đại (thẻ
  trắng bo 28px, indigo `#4f46e5` + cyan `#06b6d4`, title 54px,
  subtitle 28px, số liệu 38px bold, font Noto Sans, trục đếm dùng
  nice ticks nguyên) bằng engine HTML/CSS + SVG thuần, render qua
  WeasyPrint rồi `pdftoppm -r 96` thành PNG 1600×900; tên file, cờ
  CLI `--charts`/`--charts-dir` và cơ chế skip kèm reason giữ
  nguyên. Extra `charts` đổi từ matplotlib sang `weasyprint>=70`
  (cộng `pdftoppm` của poppler-utils); lõi vẫn chỉ cần Pillow +
  numpy. Scatter và heatmap tâm box, heatmap class × split được
  thiết kế mới theo cùng ngôn ngữ style (heatmap tâm box dùng lưới
  10×10, thang màu rời rạc thay cho gradient SVG).
- Gallery `docs/assets/charts/` tái tạo bằng engine mới (23 ảnh từ
  dataset demo sạch — 2 ảnh health skip đúng hành vi; xem
  `docs/charts.md`); sơ đồ pipeline cập nhật nhãn "25 PNGs".
- Không bump version (vẫn 0.2.0).

### Added
- Cây dataset kỳ vọng train/val-only cho bố cục YOLO
  (`images/train/img1.jpg`, `images/train/img2.jpg`,
  `images/val/img3.jpg` + `labels/` tương ứng + `data.yaml` chỉ có
  `train`/`val`): chạy đủ chức năng, split `test` thiếu chỉ được báo
  là "đã bỏ qua" chứ không phải lỗi; khi không có test, ưu tiên giữ
  là `val > train`.
- Parser `data.yaml`: tên class dạng dict của Ultralytics
  (`names:` dạng block `0: cat` hoặc inline `{0: cat, 1: dog}`) và
  khóa `path` (đường dẫn split được giải quyết theo `path` trước,
  rồi mới theo thư mục chứa `data.yaml`).
- CI GitHub Actions: test trên Python 3.10–3.13 × Ubuntu/macOS/Windows,
  coverage, ruff, mypy (chưa chặn CI), job benchmark.
- Trang tài liệu MkDocs + Material, deploy GitHub Pages.
- Workflow phát hành PyPI bằng trusted publishing (chờ cấu hình phía PyPI).
- Script benchmark trùng lặp gần đúng `benchmarks/benchmark_near_dup.py`
  (500 ảnh) và kết quả chạy đầu tiên.
- Badge CI / Python / License trên README.

## [Unreleased] — Bố cục YOLO + biểu đồ

### Added
- Hỗ trợ bố cục YOLO chuẩn: `images/<split>/` + `labels/<split>/` +
  `data.yaml` (tên class từ `names`); tự nhận diện cùng bố cục classic
  cũ. Quarantine giữ nguyên cây `labels/`; xung đột nhãn so theo tập
  class-id trong file `.txt`.
- Xuất 24 biểu đồ PNG kiểu YOLO (`--charts`, xem `docs/charts.md`):
  tổng quan split/class, phân phối kích thước/chiều/tỉ lệ/diện tích,
  box YOLO (số box, w/h/diện tích, scatter và heatmap tâm box,
  heatmap class × split), kết quả làm sạch (nhóm trùng, removals,
  health, kept vs quarantined). Biểu đồ không có dữ liệu được bỏ qua
  và ghi lý do, không vẽ biểu đồ rỗng giả.
- Extra `charts` (matplotlib) — lõi vẫn chỉ cần Pillow + numpy; thiếu
  extra mà bật `--charts` thì CLI báo lỗi rõ và thoát mã 2.
- `clean(..., charts_dir=...)` và `report["layout"]` (mode/data.yaml/names).
- Gallery ảnh mẫu: `docs/assets/charts/` (22 biểu đồ thật từ dataset
  YOLO demo, tạo lại bằng `scripts/make_gallery.py`) + sơ đồ luồng
  pipeline `docs/assets/pipeline.png`, nhúng vào `docs/charts.md`,
  `docs/index.md` và README 3 ngôn ngữ.
- Ảnh minh họa AI cho docs/README: `docs/assets/illustrations/`
  (hero banner, minh họa trùng lặp, minh họa bảo vệ split) — ảnh
  minh họa ý tưởng, không phải số liệu thật.

### Changed
- `utils.discover()` nay trả về 3 giá trị `(records, missing, layout)`
  thay vì 2; mỗi record thêm `classes` và `label_path`.

## [0.2.3] - 2026-11-01

### Fixed
- Đồng bộ COCO khớp theo đường dẫn thay vì tên trần: `file_name`
  có tiền tố thư mục (`"train/a.jpg"`) nay được loại đúng (trước
  đây không loại gì cả, ảnh đã quarantine vẫn nằm trong COCO
  sạch); tên trần trùng nhau ở 2 split (`"a.jpg"` ở cả train và
  val) nay được giữ lại kèm cảnh báo trong `coco_sync["warnings"]`
  thay vì xóa cả 2 (trước đây xóa oan annotation của split còn
  lại). Tên trần duy nhất vẫn loại như cũ.
- Quarantine ghi đè khi thư mục ảnh nằm ngoài root (đường dẫn
  tuyệt đối trong `data.yaml`): đích dự phòng nay thêm hậu tố
  hash của đường dẫn nguồn khi đã tồn tại, thay vì ghi đè im
  lặng làm mất file quarantine trước.

### Changed
- Ảnh trơn/đơn sắc (độ lệch chuẩn ảnh xám 32×32 dưới 1.0) không
  còn tạo cạnh near: dHash của ảnh trơn luôn bằng 0 và pHash chỉ
  là nhiễu float nên gộp chúng không có ý nghĩa; ảnh trơn giống
  hệt từng byte vẫn gộp qua cạnh exact. `report["blank_images"]`
  ghi số ảnh trơn đã loại khỏi gộp near.

### Added
- Test: 3 test COCO khớp đường dẫn, 1 test quarantine ngoài
  root, 4 test ảnh trơn (kèm kiểm chứng `clean()` đầu-cuối).

## [0.2.2] - 2026-11-01

### Added
- Luật gom nhóm near mới `--near-mode or|and` (mặc định `or`,
  giữ tương thích ngược) và `clean(..., near_mode=...)`: `and`
  chỉ gộp một cặp khi CẢ pHash VÀ dHash đều trong ngưỡng. Luật
  `or` duy nhất trước đây tạo dương tính giả trên tập ảnh có bố
  cục giống nhau (cặp ảnh khác nhau chạm ngưỡng trên 1 hash trong
  khi hash còn lại lệch xa 18–30, đo thực tế trên bộ nấm 25 loài:
  162 nhóm near, trong đó nhiều nhóm sai) — `and` loại các cặp
  này, đổi lại có thể bỏ sót cặp nén JPEG mạnh trên ảnh trơn
  (pHash trôi tới 16 trong khi dHash bằng 0) mà `or` bắt được.
  `report["near_mode"]` ghi lại luật đã dùng để kết quả kiểm
  chứng được.
- Test `TestNearMode` (5 test): cặp chạm ngưỡng 1 hash chỉ gộp
  dưới `or`, cặp cả 2 hash trong ngưỡng gộp dưới cả 2 luật, cặp
  ngoài ngưỡng không gộp dưới luật nào, exact vẫn gộp dưới cả 2
  luật, `near_mode` lạ báo `ValueError`.

## [0.2.0] - 2026-10-29

### Added
- Kiểm tra sức khỏe dataset (11 kiểm tra): file rỗng 0 byte, file hỏng,
  ảnh trơn/đơn sắc, ảnh quá nhỏ, file lạ trong thư mục split, ảnh thiếu
  nhãn YOLO, nhãn YOLO mồ côi/sai định dạng/rỗng, trùng tên file khác
  nội dung, trùng lặp trong nội bộ tập test. Kiểm tra YOLO tự bật khi
  thấy file `.txt` (hoặc ép bằng `--yolo`).
- Thông báo CLI và tên kiểm tra bằng 3 ngôn ngữ Việt/Anh/Trung qua
  `--lang vi|en|zh` (mặc định `vi`); key trong `report.json` giữ tiếng Anh.
- Kết luận `"clean"` trong báo cáo: true khi mọi kiểm tra đã bật đều đạt.
- README tiếng Anh (`README.en.md`) và tiếng Trung (`README.zh.md`).

### Fixed
- File hỏng không còn bị gán dở đặc trưng trước khi lỗi (từng gây KeyError
  khi gom nhóm) — tính đặc trưng xong mới gán, lỗi thì không gán gì.

## [0.1.0] - 2026-10-29

### Added
- MVP: vòng 1 exact match (MD5/SHA-256), vòng 2 pHash/dHash tự cài đặt
  bằng Pillow + numpy (không cần gói `imagehash`).
- Luật ưu tiên split Test > Val > Train, giữ ảnh tất định theo độ phân
  giải → kích thước file → tên file.
- Xung đột nhãn không tự xóa, ghi `conflict_report.csv` để rà soát tay.
- Dry-run mặc định; `--apply` chuyển file vào quarantine kèm
  `manifest.json`, không xóa thẳng.
- Đồng bộ annotation: nhãn YOLO `.txt` đi cùng ảnh vào quarantine;
  COCO JSON xuất bản đã lọc, không ghi đè file gốc.
- CLI `vision-cleanse` và 23 unit test (unittest).
