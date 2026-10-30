# Đóng góp cho VisionCleanse

Cảm ơn bạn đã muốn đóng góp. VisionCleanse là công cụ dọn dataset ảnh:
phát hiện ảnh trùng lặp và rò rỉ giữa train/val/test, mặc định chỉ chạy
khô (dry-run), file bị loại được chuyển vào quarantine kèm `manifest.json`
— không bao giờ xóa cứng.

## Cài đặt môi trường dev

Yêu cầu Python >= 3.10.

```bash
pip install -e .            # bản cơ bản
pip install -e .[charts]    # kèm vẽ biểu đồ
pip install ruff mkdocs mkdocs-material   # lint + docs
```

## Chạy kiểm tra trước khi gửi PR

```bash
PYTHONPATH=src:tests python -m unittest discover -s tests   # toàn bộ test
ruff check src tests benchmarks                             # lint
mkdocs build --strict                                       # docs (nếu sửa docs)
```

CI chạy đúng 3 lệnh này trên Python 3.10–3.13 và Ubuntu/macOS/Windows,
nên PR nào đỏ CI cũng sẽ được yêu cầu sửa trước khi merge.

## Quy tắc cốt lõi (đừng phá vỡ)

- Dry-run là mặc định. Chỉ `--apply` mới di chuyển file.
- Không xóa cứng file của người dùng, kể cả khi "chắc chắn là trùng".
- Xung đột nhãn không tự xóa: giữ nguyên, ghi vào báo cáo.
- Keeper phải xác định (deterministic): cùng input cho cùng output.
- Ưu tiên split: test > val > train — không để rò rỉ vào test.
- Một PR = một việc. PR lớn khó review sẽ được yêu cầu tách nhỏ.

## Gửi PR

- Mô tả rõ vấn đề và cách sửa, kèm test cho hành vi mới.
- Nếu đổi hành vi người dùng thấy được, cập nhật docs tương ứng.
- Không gửi kèm dataset thật hay ảnh riêng tư; dùng ảnh mẫu tổng hợp
  để tái hiện lỗi.

## Báo lỗi

Dùng mẫu bug report khi mở issue: phiên bản, lệnh đã chạy, kết quả
mong đợi/thực tế, bố cục dataset. Lỗi bảo mật thì xem `SECURITY.md`
— đừng mở issue công khai.

Ngôn ngữ đóng góp: tiếng Việt hoặc tiếng Anh đều được.
