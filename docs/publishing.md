# Phát hành

## Lên PyPI (lần đầu)

Workflow `.github/workflows/publish.yml` dùng **trusted publishing**
(OIDC) nên không cần lưu API token trong GitHub Secrets. Trước lần phát
hành đầu tiên, chủ tài khoản PyPI làm một lần duy nhất:

1. Tạo tài khoản trên [pypi.org](https://pypi.org) (nếu chưa có).
2. Vào PyPI → tài khoản → **Pending publishers** → **Add a new pending
   publisher** và điền:
    - PyPI project name: `vision-cleanse`
    - Owner: `MinhTriTM`
    - Repository name: `vision-cleanse`
    - Workflow name: `publish.yml`
    - Environment: để trống
3. Trong repo, bump phiên bản lên 0.3.0 ở cả `pyproject.toml` và
   `src/vision_cleanse/__init__.py`, cập nhật CHANGELOG, push lên `main`.
4. Tạo GitHub release 0.3.0 từ tag `v0.3.0`. Workflow sẽ tự build
   (sdist + wheel) và đẩy lên PyPI. Sau đó kiểm tra bằng
   `pip install vision-cleanse`.

Các lần sau chỉ cần lặp lại bước 3–4 với phiên bản mới. Không bao giờ
gửi token PyPI qua chat.

## Bật GitHub Pages cho docs

Workflow `.github/workflows/docs.yml` tự build và deploy docs mỗi khi
`main` thay đổi. Cần bật một lần: repo → **Settings → Pages → Build
and deployment → Source → GitHub Actions**. Sau đó docs sẽ ở
`https://minhtritm.github.io/vision-cleanse/`.
