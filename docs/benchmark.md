# Benchmark

Script: `benchmarks/benchmark_near_dup.py`. Kết quả chạy đầu tiên lưu ở
`benchmarks/results_near_dup.json`. CI chạy lại benchmark này trên
Ubuntu/Python 3.12 mỗi lần push và lưu kết quả làm artifact.

## Cách đo

- 100 ảnh gốc dạng "giả ảnh chụp" (gradient + nhiễu + hình ngẫu nhiên,
  seed khác nhau) và 4 biến thể mỗi ảnh: thu nhỏ 50%, phóng to 200%,
  JPEG quality 30, JPEG quality 95 — tổng 500 ảnh.
- Ground truth: các ảnh cùng một gốc là trùng lặp.
- Ngưỡng: pHash 10, dHash 10, luật OR (xem README phần Ngưỡng).

## Kết quả đầu tiên (phiên bản 0.2.0)

| Chỉ số | Giá trị |
|---|---|
| Ảnh | 500 (100 gốc × 5) |
| Nhóm tìm thấy | 99 (đúng ra 100) |
| Precision | 0.9756 |
| Recall | 1.0000 |
| F1 | 0.9877 |
| TP / FP / FN | 1000 / 25 / 0 |
| Recall theo biến thể | small 1.0, large 1.0, jpg30 1.0, jpg95 1.0 |
| Thời gian trích xuất | 4.39s (~8.8ms/ảnh) |
| Thời gian gom nhóm | 0.07s |

## Đọc kết quả: false positive duy nhất

Recall đạt tuyệt đối: mọi biến thể đều được gom đúng với ảnh gốc.
Precision mất 25 cặp từ **một** cặp ảnh gốc khác nhau bị gom chung:
base 4 và base 9 có dHash = 10 (đúng ngưỡng), pHash = 26. Vì luật OR
nên cặp này bị gom, kéo theo 25 cặp sai (10 ảnh trong một nhóm thay
vì hai nhóm 5 ảnh).

Bài học, và cách xử lý đúng:

- **Không chỉnh ngưỡng chỉ vì một cặp này.** Hạ ngưỡng dHash xuống 8
  sẽ hết lỗi này nhưng có thể làm mất recall trên dữ liệu khác — đó là
  overfit vào benchmark.
- Cách sửa đúng là **tầng xác minh hình học ở Giai đoạn 2**
  (SIFT + RANSAC): cặp ứng viên phải qua xác minh trước khi quarantine,
  thay vì chỉ dựa vào một hash chạm ngưỡng.
- Benchmark này tồn tại chính để bắt những trường hợp như vậy một cách
  công khai, thay vì giấu đi.

## Chạy lại

```bash
python benchmarks/benchmark_near_dup.py
```
