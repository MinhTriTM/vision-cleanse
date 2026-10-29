# Hướng dẫn sử dụng

## Cấu trúc dataset

```
dataset/
  train/<class>/a.jpg   # hoặc train/a.jpg (không chia class)
  val/<class>/b.jpg
  test/<class>/c.jpg
```

Mỗi split là một thư mục con của root. Split không tồn tại sẽ được bỏ
qua kèm cảnh báo. Nhãn (label) là tên thư mục class chứa ảnh; ảnh nằm
trực tiếp dưới split thì nhãn rỗng và không gây xung đột nhãn.

## Lệnh CLI

```
vision-cleanse ROOT [tùy chọn]
```

| Tùy chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--splits` | `train val test` | Các split cần quét |
| `--phash-threshold` | `10` | Ngưỡng Hamming tối đa của pHash |
| `--dhash-threshold` | `10` | Ngưỡng Hamming tối đa của dHash |
| `--hash-algo` | `md5` | `md5` hoặc `sha256` cho vòng exact |
| `--apply` | (không) | Không có cờ này = dry-run, không di chuyển file |
| `--quarantine-dir` | `<root>_quarantine` | Thư mục quarantine khi `--apply` |
| `--report-dir` | `vision_cleanse_report` | Nơi ghi `report.json` và `conflict_report.csv` |
| `--coco` | (không) | File COCO JSON cần đồng bộ |
| `--coco-output` | `<coco>.cleaned.json` | Nơi ghi COCO đã lọc |
| `--lang` | `vi` | Ngôn ngữ thông báo: `vi`, `en`, `zh` |
| `--min-size` | `32` | Ảnh có cạnh dài nhất dưới ngưỡng này bị gắn cờ "tiny" |
| `--yolo` | (tự động) | Ép bật kiểm tra annotation YOLO |

Một cặp ảnh được coi là trùng gần đúng khi pHash **hoặc** dHash nằm
trong ngưỡng (luật OR — xem [README](https://github.com/MinhTriTM/vision-cleanse)
phần Ngưỡng để biết vì sao không dùng AND).

## Quy tắc xử lý trùng lặp

- Ưu tiên giữ `test > val > train`: trùng giữa test và train thì giữ
  ở test, xóa ở train.
- Trong cùng một split, giữ ảnh có độ phân giải cao nhất, rồi file lớn
  nhất, rồi tên file nhỏ nhất (tất định).
- Cùng ảnh nhưng khác class thì **không tự xóa**: cả nhóm được giữ lại
  và ghi vào `conflict_report.csv`.

## An toàn

- Mặc định là dry-run. Muốn chạy thật phải ghi rõ `--apply`.
- File bị loại không bị xóa mà được **chuyển vào quarantine** giữ nguyên
  cấu trúc thư mục, kèm `manifest.json` để khôi phục.
- Nhãn YOLO `.txt` nằm cạnh ảnh được chuyển cùng ảnh. File COCO gốc
  không bao giờ bị ghi đè.

## Dùng từ Python

```python
from vision_cleanse import clean

report = clean("/path/to/dataset", dry_run=True)
print(report["duplicate_groups"], report["to_quarantine"])
print(report["clean"])  # True khi mọi kiểm tra đã bật đều đạt

report = clean("/path/to/dataset", dry_run=False,
               quarantine_dir="/path/to/quarantine",
               lang="en", min_size=32)
```

Xem đầy đủ tham số ở [API](api.md).
