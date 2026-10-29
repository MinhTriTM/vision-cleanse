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
