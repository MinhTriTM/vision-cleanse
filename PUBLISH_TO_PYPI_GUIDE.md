# Hướng Dẫn Phát Hành vision-cleanse Lên PyPI Chính Thức

Tài liệu này hướng dẫn cách đưa thư viện **`vision-cleanse`** lên kho gói toàn cầu của Python (**[pypi.org](https://pypi.org)**).

---

## 1. Trạng thái Hiện tại
- **Tên gói**: `vision-cleanse`
- **Tình trạng trên PyPI**: **HOÀN TOÀN TRỐNG (404)** — Chưa ai đăng ký, bạn có thể đăng ký độc quyền ngay!
- **Phiên bản chuẩn bị phát hành**: `0.3.0`
- **Bộ kiểm thử Pytest**: **74/74 tests PASSED** (100%).
- **Đóng gói wheel**: `vision_cleanse-0.3.0-py3-none-any.whl` (47 KB) hợp lệ 100%.

---

## 2. Thêm Pending Publisher trên PyPI (OpenID Connect - OIDC)

Truy cập: [https://pypi.org/manage/account/publishing/](https://pypi.org/manage/account/publishing/) và điền vào form:

| Tên trường trên PyPI | Giá trị bạn cần điền |
| :--- | :--- |
| **PyPI Project Name** *(required)* | `vision-cleanse` |
| **Owner** *(required)* | `MinhTriTM` |
| **Repository name** *(required)* | `vision-cleanse` |
| **Workflow name** *(required)* | `publish.yml` |
| **Environment name** *(optional)* | *(Để trống)* |

👉 Bấm nút **Add** màu xanh.

---

## 3. Kích hoạt Xuất bản

Sau khi thêm xong trên PyPI, tiến trình xuất bản sẽ tự động chạy qua Git Tag:
```bash
git tag -a v0.3.0 -m "Release v0.3.0: Clean near-duplicates & split leakage from CV datasets"
git push origin v0.3.0
```
Hoặc tạo Release trên GitHub:
- [https://github.com/MinhTriTM/vision-cleanse/releases/new](https://github.com/MinhTriTM/vision-cleanse/releases/new) (chọn tag `v0.3.0`).

Sau 1-2 phút, gói sẽ chính thức có mặt tại:
👉 **[https://pypi.org/project/vision-cleanse/](https://pypi.org/project/vision-cleanse/)**

Và cài đặt qua lệnh:
```bash
pip install vision-cleanse
```
