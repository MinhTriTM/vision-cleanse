# Bài tập lớn — Học phần Xử lý ảnh (IN4152N01)

**Chủ đề:** Bộ lọc Sobel trong phát hiện cạnh và tích hợp vào dự án VisionCleanse
**Lớp học phần:** ĐHCNTT24A-CS – IN4152N01 — GV: ThS. Trần Ngọc Thuận
**Nhóm:** Đoàn Minh Trí (trưởng nhóm, 0024417136), Lê Tuấn Kiệt (0024417193), Võ Thanh Tân (0024416594), Phạm Thị Như Ý (0024419356)

## Nội dung thư mục

| Tệp / thư mục | Mô tả |
|---|---|
| `BaoCao_Sobel_VisionCleanse.docx` / `.pdf` | Báo cáo đầy đủ 30 trang: lý thuyết chung → Sobel chuyên sâu → dự án VisionCleanse → tích hợp vòng 2.5 → thực nghiệm |
| `Slide_Sobel_VisionCleanse.pptx` | Slide nháp 16 trang (bản chính sẽ làm lại bằng NotebookLM rồi chỉnh từng trang) |
| `figures/` | 4 hình dùng trong báo cáo: bộ 4 ảnh Sobel (gốc/Gx/Gy/độ lớn), bản đồ cạnh gốc vs âm bản, biểu đồ khoảng cách Hamming, biểu đồ năng lượng cạnh |
| `demo_sobel/` | Ảnh demo Sobel sinh từ `sobel_magnitude_image()` |
| `experiment/results.json` | Số liệu thô của thực nghiệm (17 trường hợp) |
| `scripts/` | Mã nguồn sinh báo cáo, chạy thực nghiệm và vẽ hình |

## Phần mã nguồn tích hợp (ở thư mục gốc của repo trên nhánh này)

- `src/vision_cleanse/extractors.py`: `sobel_magnitude()`, `edge_hash()`, `edge_energy()`, `sobel_magnitude_image()`
- `src/vision_cleanse/matchers.py`: luật xác minh Sobel hai chiều trong `group_duplicates()`
- `src/vision_cleanse/core.py`, `cli.py`: cờ `--sobel-verify`, `--sobel-threshold`
- `tests/test_sobel.py`: 14 kiểm thử (toàn bộ dự án: 88 passed, 7 skipped)

## Kết quả nổi bật

- Ảnh âm bản: pHash lệch 62 bit, dHash lệch 64 bit, **edge_hash (Sobel) lệch 0 bit** so với ảnh gốc.
- Làm mờ Gaussian r=3: năng lượng cạnh còn 0,47 lần → tín hiệu cảnh báo ảnh mờ.
- Giới hạn trung thực: crop 10%+ và lật ngang vẫn ngoài tầm của cả ba hàm băm toàn cục.

## Chạy lại

```bash
git clone -b vision-cleanse-BaiTapLonImageProcessing https://github.com/MinhTriTM/vision-cleanse.git
cd vision-cleanse
pip install -e .
python -m pytest tests/test_sobel.py -q
visioncleanse ./dataset --sobel-verify --sobel-threshold 10
```
