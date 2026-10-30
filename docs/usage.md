# Hướng dẫn sử dụng

## Cấu trúc dataset

Hai bố cục được tự nhận diện:

**Classic:**

```
dataset/
  train/<class>/a.jpg   # hoặc train/a.jpg (không chia class)
  val/<class>/b.jpg
  test/<class>/c.jpg
```

Nhãn YOLO `.txt` nằm cạnh ảnh. Nhãn (label) là tên thư mục class
chứa ảnh; ảnh nằm trực tiếp dưới split thì nhãn rỗng và không gây
xung đột nhãn.

**YOLO (chuẩn Ultralytics) — cấu trúc kỳ vọng:**

```
dataset_root/
  images/
    train/img1.jpg
    train/img2.jpg
    val/img3.jpg
  labels/
    train/img1.txt
    train/img2.txt
    val/img3.txt
  data.yaml
```

`data.yaml` mẫu:

```yaml
train: images/train
val: images/val
nc: 2
names:
  - cat
  - dog
```

Tập `test` là tùy chọn: dataset chỉ có `train`/`val` vẫn chạy đủ
chức năng, split thiếu chỉ được báo là "đã bỏ qua" chứ không phải
lỗi. Khi không có `test`, thứ tự ưu tiên giữ là `val > train`.

Tên class lấy từ `names` trong `data.yaml` (dạng danh sách gạch đầu
dòng, inline `[cat, dog]`, hoặc dạng dict của Ultralytics `0: cat`
/ `{0: cat, 1: dog}`); `train`/`val`/`test` trong `data.yaml` nếu trỏ
tới thư mục có sẵn cũng được dùng làm thư mục ảnh — chấp nhận cả
`./images/train`, `images/train/` và khóa `path` (đường dẫn trong
`data.yaml` được giải quyết theo `path` trước, rồi mới theo thư mục
chứa `data.yaml`). Khi quarantine, file nhãn được giữ nguyên cây
`labels/`.

Mỗi split là một thư mục con. Split không tồn tại sẽ được bỏ qua
kèm cảnh báo.

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
| `--report-dir` | `vision_cleanse_report` | Nơi ghi `report.json`, `conflict_report.csv` và `report.html` (xem dưới) |
| `--coco` | (không) | File COCO JSON cần đồng bộ |
| `--coco-output` | `<coco>.cleaned.json` | Nơi ghi COCO đã lọc |
| `--lang` | `vi` | Ngôn ngữ thông báo: `vi`, `en`, `zh` |
| `--min-size` | `32` | Ảnh có cạnh dài nhất dưới ngưỡng này bị gắn cờ "tiny" |
| `--yolo` | (tự động) | Ép bật kiểm tra annotation YOLO |
| `--charts` | (không) | Xuất 25 biểu đồ PNG (xem [Biểu đồ](charts.md); cần `pip install vision-cleanse[charts]`) |
| `--charts-dir` | `<report-dir>/charts` | Thư mục ghi biểu đồ |

Một cặp ảnh được coi là trùng gần đúng khi pHash **hoặc** dHash nằm
trong ngưỡng (luật OR — xem [README](https://github.com/MinhTriTM/vision-cleanse)
phần Ngưỡng để biết vì sao không dùng AND).

## Báo cáo HTML kiểm tra nhóm trùng

Mỗi lần chạy có `--report-dir` đều ghi thêm `report.html`: một file
HTML độc lập (không cần dataset đi kèm) để rà soát từng quyết định
giữ/xóa bằng mắt trước khi tin vào kết quả:

- Một thẻ cho mỗi nhóm trùng: ảnh **giữ lại** viền xanh, ảnh **chuyển
  quarantine** viền cam kèm lý do (`duplicate_within_same_split` hoặc
  `duplicate_in_lower_priority_split`), nhóm xung đột nhãn gắn cờ đỏ và
  được giữ nguyên toàn bộ.
- Ảnh hiển thị bằng thumbnail nén (tối đa 256px) nhúng trực tiếp vào
  file; nhóm quá 100 ảnh chỉ hiển thị 100 ảnh đầu, danh sách đủ nằm
  trong `report.json`.
- Kèm theo: tóm tắt đợt chạy, chẩn đoán nhãn, bảng health findings và
  gallery biểu đồ (khi biểu đồ nằm cùng thư mục báo cáo).
- Bộ lọc theo phương pháp (exact/near), chỉ nhóm xung đột, và tìm theo
  tên file — không cần máy chủ, mở file bằng trình duyệt là dùng được.

## Quy tắc xử lý trùng lặp

- Ưu tiên giữ `test > val > train`: trùng giữa test và train thì giữ
  ở test, xóa ở train. Dataset không có test thì ưu tiên `val > train`.
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
