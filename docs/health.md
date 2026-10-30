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
| `unknown_class` | cảnh báo | Dòng nhãn hợp lệ nhưng class id vượt quá danh sách `names` trong `data.yaml` — thường là dialect `.txt` lạ (ví dụ dataset có id tới 77 trong khi `names` chỉ có 1 mục). Cảnh báo gộp theo file, không theo dòng. |
| `dup_basename` | cảnh báo | Cùng tên file ở nhiều nơi nhưng nội dung khác nhau |
| `test_internal_dup` | cảnh báo | Từ 2 ảnh trở lên trong tập test thuộc cùng một nhóm trùng |

Kiểm tra YOLO tự bật khi có file `.txt` dưới các split đang quét,
hoặc ép bật bằng `--yolo`. Mức "thông tin" không làm mất kết luận
sạch; chỉ lỗi và cảnh báo mới làm mất.

## Chẩn đoán nhãn (label_diagnostics)

Khi kiểm tra YOLO chạy, `report["health"]["label_diagnostics"]` tóm tắt
cả đợt quét nhãn thay vì chỉ liệt kê từng file, để những lệch chuẩn ở
quy mô lớn không bị chìm giữa hàng nghìn finding:

| Trường | Ý nghĩa |
|---|---|
| `label_files` | Số file `.txt` dưới các split đang quét |
| `lines_scanned` | Số dòng nhãn không rỗng đã đọc |
| `malformed_lines` | Số dòng sai định dạng (cũng là các lỗi `invalid_label`) |
| `empty_label_files` | Số file nhãn rỗng |
| `empty_label_rate` | Tỉ lệ file nhãn rỗng (ví dụ 0,067 = 6,7% ở CrowdHuman 15k) |
| `unknown_class_ids` | Các class id ngoài phạm vi `names`, đã sắp xếp |
| `unknown_class_files` | Số file chứa ít nhất một class id ngoài phạm vi |

Gợi ý xử lý: file nhãn rỗng thường là ảnh thật sự không có vật thể —
kiểm tra xem đó có phải chủ đích của dataset không trước khi xóa ảnh;
class id ngoài `names` thì kiểm tra lại `data.yaml` hoặc dialect file
`.txt` của nguồn dataset trước khi tin vào phân bố class và các biểu
đồ theo class.

## Phân bố class

`report["health"]["class_distribution"]` đếm số ảnh theo từng split và
từng class, để phát hiện mất cân bằng trước khi huấn luyện.
