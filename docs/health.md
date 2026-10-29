# Kiểm tra sức khỏe dataset

Ngoài việc tìm trùng lặp, `clean()` còn chạy một bộ kiểm tra sức khỏe
và ghi vào `report["health"]`. Kết luận `"clean": true` nghĩa là mọi
kiểm tra đã bật đều đạt (không lỗi, không cảnh báo). Đây không phải
cam kết tuyệt đối: trùng gần đúng vốn là bài toán mờ và không công cụ
nào bắt được lỗi nhãn về mặt ngữ nghĩa.

## Bảng kiểm tra

| Kiểm tra | Mức | Ý nghĩa |
|---|---|---|
| `zero_byte` | lỗi | File 0 byte |
| `corrupt` | lỗi | File hỏng, Pillow không đọc được |
| `blank` | cảnh báo | Ảnh trơn/đơn sắc (độ lệch chuẩn kênh xám < 1.0) |
| `tiny` | cảnh báo | Cạnh dài nhất < `--min-size` (mặc định 32px) |
| `other_file` | thông tin | File không phải ảnh, không phải `.txt` trong thư mục split |
| `missing_label` | cảnh báo | Ảnh không có file nhãn YOLO cùng tên |
| `orphan_label` | cảnh báo | File `.txt` không có ảnh tương ứng |
| `invalid_label` | lỗi | Dòng nhãn YOLO không đúng 5 cột, không phải số, hoặc tọa độ ngoài [0, 1] |
| `empty_label` | cảnh báo | File nhãn YOLO rỗng |
| `dup_basename` | cảnh báo | Cùng tên file ở nhiều nơi nhưng nội dung khác nhau |
| `test_internal_dup` | cảnh báo | Từ 2 ảnh trở lên trong tập test thuộc cùng một nhóm trùng |

Kiểm tra YOLO tự bật khi có file `.txt` dưới các split đang quét,
hoặc ép bật bằng `--yolo`. Mức "thông tin" không làm mất kết luận
sạch; chỉ lỗi và cảnh báo mới làm mất.

## Phân bố class

`report["health"]["class_distribution"]` đếm số ảnh theo từng split và
từng class, để phát hiện mất cân bằng trước khi huấn luyện.
