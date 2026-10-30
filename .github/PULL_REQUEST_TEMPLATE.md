## Mô tả thay đổi

<!-- Thay đổi này làm gì và vì sao cần thiết? Link issue liên quan nếu có. -->

## Loại thay đổi

- [ ] Sửa lỗi
- [ ] Tính năng mới
- [ ] Docs
- [ ] Việc khác (ghi rõ)

## Checklist

- [ ] Đã thêm/cập nhật test cho hành vi mới và chạy đủ bộ test
  (`PYTHONPATH=src:tests python -m unittest discover -s tests`)
- [ ] `ruff check src tests benchmarks` sạch
- [ ] Đã cập nhật docs nếu thay đổi hành vi người dùng thấy được
- [ ] Giữ nguyên dry-run mặc định, file bị loại vẫn qua quarantine
  (không xóa cứng), xung đột nhãn không tự xóa
