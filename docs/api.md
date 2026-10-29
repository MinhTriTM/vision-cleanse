# API

API công khai hiện tại rất nhỏ và sẽ giữ ổn định tới 1.0:

## `vision_cleanse.clean()`

```python
clean(
    root,
    splits=("train", "val", "test"),
    phash_threshold=10,
    dhash_threshold=10,
    hash_algo="md5",
    dry_run=True,
    quarantine_dir=None,      # mặc định: <root>_quarantine
    report_dir=None,          # nếu có: ghi report.json + conflict_report.csv
    coco_path=None,
    coco_output=None,         # mặc định: <coco_path>.cleaned.json
    lang="vi",                # "vi" | "en" | "zh"
    min_size=32,
    yolo=None,                # None = tự bật khi thấy file .txt
    charts_dir=None,          # nếu có: xuất biểu đồ PNG (cần extra charts)
) -> dict
```

Báo cáo trả về (key luôn tiếng Anh):

- `images_found`, `images_unreadable`, `duplicate_groups`,
  `groups_exact`, `groups_near`, `to_quarantine`, `label_conflicts`
- `groups`: từng nhóm gồm `kept`, `removed`, `method`, `conflict`
- `removals`: từng file bị loại kèm `kept_path` và `reason`
- `conflicts`: các nhóm xung đột nhãn
- `health`: kết quả [kiểm tra sức khỏe](health.md) + `clean`
- `clean`: `True` khi mọi kiểm tra đã bật đều đạt (không lỗi, không
  cảnh báo)

## `vision_cleanse.t()`

```python
from vision_cleanse import t
t("scanned", "zh", n=42)  # -> "已扫描：42 张图片"
```

Trả về thông báo đã dịch cho CLI; ngôn ngữ lạ sẽ fallback về tiếng Anh.

## Module nội bộ

- `vision_cleanse.extractors`: `file_hash`, `phash`, `dhash`,
  `image_size`, `hash_hex`.
- `vision_cleanse.matchers`: `hamming`, `group_duplicates`, `UnionFind`.
- `vision_cleanse.health`: `run_health_checks`.
- `vision_cleanse.utils`: `discover`, `move_to_quarantine`,
  `write_manifest`, `write_conflict_report`, `sync_coco`.
- `vision_cleanse.cli`: `main()` và `build_parser()`.

Các module nội bộ có thể đổi mà không cần báo trước; chỉ `clean()`,
`t()` và CLI được coi là API ổn định.
