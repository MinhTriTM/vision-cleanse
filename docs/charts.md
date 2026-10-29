# Biểu đồ

```bash
pip install vision-cleanse[charts]
vision-cleanse /path/to/dataset --charts
# hoặc chỉ định thư mục: --charts-dir /path/to/charts
```

Biểu đồ được ghi vào `<report-dir>/charts` (mặc định) và liệt kê
trong `report.json` ở khóa `"charts"`: `generated` (file đã tạo) và
`skipped` (biểu đồ bị bỏ qua kèm lý do — ví dụ không có box YOLO,
không có nhóm trùng, không có health findings).

## Gallery — ảnh mẫu từ dataset demo

Các ảnh dưới đây được tạo thật bằng `scripts/make_gallery.py` từ
một dataset YOLO demo (38 ảnh, 2 class, có 1 cặp trùng exact và 1
cặp near-dup). Người xem không cần chạy gì cũng thấy biểu đồ trông
như thế nào.

![Số ảnh mỗi split](assets/charts/split_sizes.png)

![Tỉ lệ mỗi split](assets/charts/split_share.png)

![Số ảnh mỗi class](assets/charts/class_images.png)

![Số ảnh mỗi class xếp chồng theo split](assets/charts/class_split_stacked.png)

![Phân phối kích thước file](assets/charts/file_size_hist.png)

![Phân phối chiều rộng ảnh](assets/charts/width_hist.png)

![Phân phối chiều cao ảnh](assets/charts/height_hist.png)

![Phân phối tỉ lệ w/h](assets/charts/aspect_hist.png)

![Phân phối diện tích ảnh](assets/charts/area_hist.png)

![Số box mỗi ảnh](assets/charts/instances_per_image.png)

![Số box mỗi class](assets/charts/boxes_per_class.png)

![Phân phối chiều rộng box](assets/charts/box_width_hist.png)

![Phân phối chiều cao box](assets/charts/box_height_hist.png)

![Phân phối diện tích box](assets/charts/box_area_hist.png)

![Scatter tâm box](assets/charts/box_centers_scatter.png)

![Heatmap tâm box](assets/charts/box_centers_heatmap.png)

![Scatter w vs h của box](assets/charts/box_wh_scatter.png)

![Heatmap box theo class × split](assets/charts/class_split_heatmap.png)

![Nhóm trùng theo phương pháp](assets/charts/dup_by_method.png)

![File bị loại theo split](assets/charts/removals_by_split.png)

![File bị loại theo lý do](assets/charts/removals_by_reason.png)

![Kept vs quarantined mỗi split](assets/charts/kept_vs_quarantined.png)

## Danh sách 24 biểu đồ

Tổng quan:

- `split_sizes.png` — số ảnh mỗi split (cột)
- `split_share.png` — tỉ lệ mỗi split (donut)
- `class_images.png` — số ảnh mỗi class (cột, top 30 nếu nhiều class)
- `class_split_stacked.png` — số ảnh mỗi class, xếp chồng theo split
- `file_size_hist.png` — phân phối kích thước file (KB)
- `width_hist.png`, `height_hist.png` — phân phối chiều ảnh (px)
- `aspect_hist.png` — phân phối tỉ lệ w/h
- `area_hist.png` — phân phối diện tích ảnh (megapixel)

Nhãn YOLO (chỉ khi có box hợp lệ):

- `instances_per_image.png` — số box mỗi ảnh
- `boxes_per_class.png` — số box mỗi class (tên từ `data.yaml`)
- `box_width_hist.png`, `box_height_hist.png`, `box_area_hist.png`
  — phân phối w, h, diện tích box (tỉ lệ 0–1)
- `box_centers_scatter.png` — scatter tâm box (x, y)
- `box_centers_heatmap.png` — heatmap tâm box 20×20
- `box_wh_scatter.png` — scatter w vs h của box
- `class_split_heatmap.png` — heatmap số box theo class × split

Kết quả làm sạch:

- `dup_by_method.png` — nhóm trùng theo phương pháp (exact/near)
- `removals_by_split.png`, `removals_by_reason.png` — file bị loại
  theo split và lý do
- `health_by_check.png` — vấn đề sức khỏe theo từng kiểm tra
- `health_by_severity.png` — vấn đề theo mức độ (donut)
- `kept_vs_quarantined.png` — kept vs quarantined mỗi split

## Lưu ý

- Matplotlib là dependency tùy chọn (`charts` extra): lõi vẫn chỉ cần
  Pillow + numpy. Nếu chưa cài extra mà bật `--charts`, CLI báo lỗi
  rõ ràng và thoát mã 2 thay vì traceback.
- Scatter plot lấy mẫu tối đa 5000 điểm (đều nhau, tất định) để file
  PNG không phình khi dataset lớn.
- Tiêu đề biểu đồ dùng tiếng Anh theo quy ước của YOLO; key trong
  `report.json` cũng luôn tiếng Anh.
