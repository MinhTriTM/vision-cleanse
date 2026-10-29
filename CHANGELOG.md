# Changelog

Tất cả thay đổi đáng chú ý của VisionCleanse được ghi ở đây, theo định
dạng [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) và
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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

### Changed
- `utils.discover()` nay trả về 3 giá trị `(records, missing, layout)`
  thay vì 2; mỗi record thêm `classes` và `label_path`.

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
