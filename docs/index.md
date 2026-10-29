# VisionCleanse

Làm sạch dataset Computer Vision: phát hiện trùng lặp gần đúng và ngăn
rò rỉ dữ liệu giữa Train / Val / Test.

VisionCleanse không hứa "sạch 100%". Nó chạy một loạt kiểm tra đo được
và trả về báo cáo liệt kê chính xác từng kiểm tra đã chạy, từng nhóm
trùng đã tìm thấy, và từng file đã chuyển vào quarantine.

## Cài đặt

```bash
pip install vision-cleanse
```

Trong lúc chưa phát hành lên PyPI, cài từ mã nguồn:

```bash
git clone https://github.com/MinhTriTM/vision-cleanse
cd vision-cleanse
pip install -e .
```

Chỉ cần Pillow và numpy. Muốn chạy vòng đặc trưng sâu về sau thì cài
thêm extra `[deep]` (chưa có ở phiên bản hiện tại).

## Chạy nhanh

```bash
# Xem trước (dry-run, mặc định): không file nào bị di chuyển
vision-cleanse /path/to/dataset

# Chạy thật: chuyển file trùng vào quarantine
vision-cleanse /path/to/dataset --apply

# Thông báo tiếng Anh, ép kiểm tra YOLO
vision-cleanse /path/to/dataset --apply --lang en --yolo
```

Xem thêm ở [Hướng dẫn sử dụng](usage.md) và [API](api.md).
Bản tiếng Anh và tiếng Trung của README nằm ở `README.en.md` và
`README.zh.md` trong repo.

## Luồng hoạt động

![Sơ đồ luồng pipeline VisionCleanse](assets/pipeline.png)

1. **Discover** — nhận diện bố cục classic hoặc YOLO
   (`images/`, `labels/`, `data.yaml`).
2. **Extract** — băm exact (MD5/SHA-256) và hash cảm nhận (pHash, dHash).
3. **Group** — gom nhóm exact + near-dup theo luật OR, ngưỡng 10.
4. **Resolve** — giữ `test > val > train` (không có test thì
   `val > train`), giữ ảnh tất định; nhóm xung đột nhãn được giữ
   nguyên và ghi `conflict_report.csv`.
5. **Quarantine** — chuyển file bị loại kèm `manifest.json`, không
   bao giờ xóa thẳng.
6. **Health** — 11 kiểm tra, kết luận `clean` khi mọi kiểm tra đạt.
7. **Report + Charts** — `report.json` và 25 biểu đồ PNG.

## Minh họa

Hai ảnh minh họa AI cho docs (không phải số liệu thật — biểu đồ số
liệu nằm ở trang [Biểu đồ](charts.md)):

![Hai ảnh gần giống nhau: một ảnh được giữ, một ảnh vào quarantine](assets/illustrations/duplicates_concept.png)

![Ba thư mục TRAIN, VAL, TEST với lá chắn bảo vệ tập TEST khỏi rò rỉ](assets/illustrations/splits_protection.png)
