# Bài tự nghiên cứu — Toán tử Sobel × VisionCleanse

Học phần Xử lý ảnh (IN4152N01). Bộ nộp được tách riêng theo loại source:

## Cấu trúc

```
NOP_BAI/
├── SOURCE/
│   ├── Python/                  ← mã nguồn Python (tích hợp Sobel vào VisionCleanse)
│   │   ├── vision_cleanse/
│   │   │   ├── extractors.py    ← sobel_magnitude, edge_hash, edge_energy (phần Sobel nằm ở đây)
│   │   │   ├── matchers.py      ← luật kiểm chứng vòng 2.5 (edge_hash quyết định)
│   │   │   ├── core.py          ← tham số sobel_verify / sobel_threshold
│   │   │   └── cli.py           ← cờ --sobel-verify, --sobel-threshold
│   │   └── tests/
│   │       └── test_sobel.py    ← 14 test cho phần Sobel (toàn bộ suite: 88 test đạt)
│   └── HTML/
│       └── GUI_Demo_Sobel.html  ← GUI demo 1 file: Sobel trực quan + demo kiểm chứng trùng lặp
└── SLIDE/
    └── Slide_Sobel_VisionCleanse.pptx   ← slide thuyết trình 16 trang
```

## Cách chạy

- **GUI demo:** mở `SOURCE/HTML/GUI_Demo_Sobel.html` bằng trình duyệt — không cần cài đặt.
  Phần 1: Gx/Gy/độ lớn gradient, trượt ngưỡng cạnh, đổi toán tử Sobel/Prewitt/Scharr/Roberts/Laplacian, tải ảnh riêng.
  Phần 2: so khoảng cách Hamming của pHash / dHash / edge_hash trên các biến thể (âm bản, mờ, crop, lật…).
- **Python:** các file trong `SOURCE/Python/vision_cleanse/` là những file được sửa/thêm cho phần Sobel,
  trích từ gói `src/vision_cleanse/` của repo vision-cleanse (cùng nhánh này). Chạy kiểm thử: `pytest tests/test_sobel.py`.
  Bật kiểm chứng Sobel khi quét trùng lặp: thêm cờ `--sobel-verify` (ngưỡng tùy chọn `--sobel-threshold 10`).
- **Slide:** mở `SLIDE/Slide_Sobel_VisionCleanse.pptx` (16 slide, nội dung khớp Phụ lục A của báo cáo).

## Kết quả nổi bật

Ảnh âm bản so với ảnh gốc: pHash lệch 62 bit, dHash lệch 64 bit, **edge_hash lệch 0 bit** —
độ lớn gradient Sobel bất biến với đảo tông màu, nên vòng 2.5 cứu được ca trùng mà hai vòng trước bỏ lỡ.
Số liệu đầy đủ: `BaiTapLon/experiment/results.json`.
