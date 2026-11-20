# -*- coding: utf-8 -*-
"""Generate the full demo-image set for the Sobel x VisionCleanse report.

Sets:
  01_sobel_co_ban/      Sobel fundamentals (Ch.2)
  02_so_sanh_toan_tu/   operator comparison (Ch.2)
  03_14_chu_de/         the 14 course topics (Ch.1)
  04_pipeline_hash/     pHash / dHash pipeline visuals (Ch.3)
  05_edge_hash/         Sobel integration visuals (Ch.4)
  06_bien_the/          experiment variants (Ch.5)

Everything is computed with numpy/Pillow/scipy only, reusing the project's
own Sobel implementation from repo-files/src/vision_cleanse/extractors.py.
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, fft

sys.path.insert(0, os.path.expanduser(
    "~/workspace/BaoCao-Sobel-XuLyAnh/repo-files/src"))
from vision_cleanse.extractors import (sobel_magnitude, sobel_magnitude_image,
                                       edge_hash, edge_energy, phash, dhash)

ROOT = os.path.expanduser("~/workspace/BaoCao-Sobel-XuLyAnh/demo_images")
rng = np.random.default_rng(42)


def save(arr, folder, name):
    d = os.path.join(ROOT, folder)
    os.makedirs(d, exist_ok=True)
    a = np.asarray(arr)
    if a.dtype != np.uint8:
        a = np.clip(a, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(d, name))
    print("wrote", folder + "/" + name)


def conv3x3(img, k):
    """Correlation with 3x3 kernel, replicate padding (project style)."""
    p = np.pad(img.astype(np.float64), 1, mode="edge")
    out = np.zeros_like(img, dtype=np.float64)
    for i in range(3):
        for j in range(3):
            if k[i][j] != 0:
                out += k[i][j] * p[i:i + img.shape[0], j:j + img.shape[1]]
    return out


def norm_signed(g):
    """Map signed gradient to 0..255 with 0 -> mid gray."""
    return np.clip(g / (np.abs(g).max() + 1e-9) * 127 + 128, 0, 255)


def norm_mag(g):
    return np.clip(g / (np.percentile(g, 99.5) + 1e-9) * 255, 0, 255)


# ---------------------------------------------------------------- scene
def make_scene():
    """Synthetic 512x512 scene: sky gradient, sun, mountains, house, tree,
    checkerboard, diagonal stripes, text — edges at many orientations."""
    h = w = 512
    img = np.zeros((h, w), dtype=np.float64)
    # sky gradient
    for y in range(300):
        img[y, :] = 190 - y * 0.25
    img[300:, :] = 90
    im = Image.fromarray(img.astype(np.uint8), "L")
    dr = ImageDraw.Draw(im)
    # sun
    dr.ellipse([380, 40, 470, 130], fill=245)
    # mountains
    dr.polygon([(0, 300), (140, 170), (280, 300)], fill=130)
    dr.polygon([(180, 300), (330, 150), (480, 300)], fill=110)
    # ground
    dr.rectangle([0, 300, 512, 512], fill=80)
    # house
    dr.rectangle([60, 330, 210, 450], fill=170)
    dr.polygon([(45, 330), (135, 270), (225, 330)], fill=60)
    dr.rectangle([115, 385, 155, 450], fill=40)      # door
    dr.rectangle([75, 350, 100, 380], fill=230)      # window
    dr.rectangle([170, 350, 195, 380], fill=230)     # window
    # tree
    dr.rectangle([300, 380, 318, 460], fill=70)
    dr.ellipse([255, 290, 365, 400], fill=140)
    dr.ellipse([285, 265, 395, 360], fill=150)
    img = np.asarray(im).astype(np.float64)
    # checkerboard patch
    cell = 16
    for i in range(6):
        for j in range(6):
            img[430 + i * cell:430 + (i + 1) * cell,
                400 + j * 8:400 + (j + 1) * 8] = 230 if (i + j) % 2 == 0 else 30
    # diagonal stripes patch
    yy, xx = np.mgrid[0:80, 0:80]
    img[420:500, 240:320] = np.where(((xx + yy) // 10) % 2 == 0, 210, 50)
    # texture noise for realism
    img += rng.normal(0, 3, img.shape)
    return np.clip(img, 0, 255)


scene = make_scene()
scene_u8 = scene.astype(np.uint8)
save(scene_u8, "01_sobel_co_ban", "sobel_01_anh_goc_xam.png")

# color version (tinted) for the negative/topic demos
color = np.stack([scene_u8,
                  np.clip(scene * 0.85, 0, 255).astype(np.uint8),
                  np.clip(scene * 0.65 + 30, 0, 255).astype(np.uint8)], -1)
save(color, "03_14_chu_de", "t00_anh_mau_goc.png")

# ------------------------------------------------------- 01 Sobel basics
gx = conv3x3(scene, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
gy = conv3x3(scene, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
mag = np.hypot(gx, gy)
save(norm_signed(gx), "01_sobel_co_ban", "sobel_02_Gx.png")
save(norm_signed(gy), "01_sobel_co_ban", "sobel_03_Gy.png")
save(norm_mag(mag), "01_sobel_co_ban", "sobel_04_do_lon_gradient.png")
# direction as hue-like map (grayscale-encoded angle bands)
ang = (np.degrees(np.arctan2(gy, gx)) + 180) / 360.0
save(ang * 255, "01_sobel_co_ban", "sobel_05_huong_gradient.png")
save((mag > 120) * 255, "01_sobel_co_ban", "sobel_06_ban_do_canh_nguong.png")

# 4-up composite with labels via matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def grid_plot(panels, folder, name, figsize=(10, 10), cmap="gray"):
    n = int(np.ceil(np.sqrt(len(panels))))
    fig, axes = plt.subplots(n, n, figsize=figsize)
    axes = np.atleast_1d(axes).ravel()
    for ax, (title, im) in zip(axes, panels):
        ax.imshow(im, cmap=cmap, vmin=0, vmax=255)
        ax.set_title(title, fontsize=13)
        ax.axis("off")
    for ax in axes[len(panels):]:
        ax.axis("off")
    fig.tight_layout()
    d = os.path.join(ROOT, folder); os.makedirs(d, exist_ok=True)
    fig.savefig(os.path.join(d, name), dpi=110)
    plt.close(fig)
    print("wrote", folder + "/" + name)

grid_plot([("Ảnh gốc (xám)", scene_u8),
           ("Gx — cạnh dọc", norm_signed(gx).astype(np.uint8)),
           ("Gy — cạnh ngang", norm_signed(gy).astype(np.uint8)),
           ("Độ lớn gradient G", norm_mag(mag).astype(np.uint8))],
          "01_sobel_co_ban", "sobel_07_ghep_4_hinh.png")

# hand-calc step edge: left 100, right 200 + Gx row profile
step = np.tile(np.concatenate([np.full(32, 100), np.full(32, 200)]), (64, 1)).astype(np.float64)
save(step, "01_sobel_co_ban", "sobel_08a_canh_bac_100_200.png")
gx_step = conv3x3(step, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(gx_step[32], lw=2)
ax.axhline(400, color="r", ls="--", lw=1)
ax.annotate("Gx = 400 tại biên", (33, 405), fontsize=11, color="r")
ax.set_xlabel("cột pixel"); ax.set_ylabel("Gx")
ax.set_title("Đáp ứng Gx qua một cạnh bậc 100 → 200")
fig.tight_layout()
d = os.path.join(ROOT, "01_sobel_co_ban"); fig.savefig(os.path.join(d, "sobel_08b_do_thi_Gx.png"), dpi=110)
plt.close(fig); print("wrote 01_sobel_co_ban/sobel_08b_do_thi_Gx.png")
save(norm_signed(gx_step), "01_sobel_co_ban", "sobel_08c_Gx_canh_bac.png")

# L1 vs L2 magnitude
grid_plot([("G = √(Gx²+Gy²) (L2)", norm_mag(mag).astype(np.uint8)),
           ("G ≈ |Gx|+|Gy| (L1)", norm_mag(np.abs(gx) + np.abs(gy)).astype(np.uint8))],
          "01_sobel_co_ban", "sobel_09_L2_vs_L1.png", figsize=(10, 5.4))

# noise sensitivity: raw Sobel vs blur-then-Sobel
noisy = np.clip(scene + rng.normal(0, 18, scene.shape), 0, 255)
mag_noisy = np.hypot(conv3x3(noisy, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
                     conv3x3(noisy, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]))
blurred = ndimage.gaussian_filter(noisy, 1.2)
mag_blur = np.hypot(conv3x3(blurred, [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
                    conv3x3(blurred, [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]))
grid_plot([("Ảnh nhiễu σ=18", noisy.astype(np.uint8)),
           ("Sobel trực tiếp (nhiễu bị khuếch đại)", norm_mag(mag_noisy).astype(np.uint8)),
           ("Làm mờ Gaussian rồi Sobel", norm_mag(mag_blur).astype(np.uint8))],
          "01_sobel_co_ban", "sobel_10_nhay_nhieu.png", figsize=(12, 4.6))

# ------------------------------------------------- 02 operator comparison
def edge_mag(img, kx, ky):
    return np.hypot(conv3x3(img, kx), conv3x3(img, ky))

ops = {
    "cmp_01_roberts.png": edge_mag(scene, [[-1, 0], [0, 1]] if False else [[0, 0, 0], [0, -1, 0], [0, 0, 1]],
                                            [[0, 0, 0], [0, 0, -1], [0, 1, 0]]),
    "cmp_02_prewitt.png": edge_mag(scene, [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]],
                                          [[-1, -1, -1], [0, 0, 0], [1, 1, 1]]),
    "cmp_03_sobel.png": mag,
    "cmp_04_scharr.png": edge_mag(scene, [[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]],
                                         [[-3, -10, -3], [0, 0, 0], [3, 10, 3]]),
}
for fn, m in ops.items():
    save(norm_mag(m), "02_so_sanh_toan_tu", fn)
lap = conv3x3(scene, [[0, 1, 0], [1, -4, 1], [0, 1, 0]])
save(norm_signed(lap), "02_so_sanh_toan_tu", "cmp_05_laplacian.png")
grid_plot([("Roberts", norm_mag(ops["cmp_01_roberts.png"]).astype(np.uint8)),
           ("Prewitt", norm_mag(ops["cmp_02_prewitt.png"]).astype(np.uint8)),
           ("Sobel", norm_mag(mag).astype(np.uint8)),
           ("Scharr", norm_mag(ops["cmp_04_scharr.png"]).astype(np.uint8)),
           ("Laplacian (đạo hàm bậc 2)", norm_signed(lap).astype(np.uint8)),
           ("Ảnh gốc", scene_u8)],
          "02_so_sanh_toan_tu", "cmp_06_ghep_so_sanh.png")

# ------------------------------------------------------- 03 the 14 topics
sp = scene.copy()
mask = rng.random(scene.shape) < 0.03
sp[mask & (rng.random(scene.shape) < 0.5)] = 0
sp[mask & (sp != 0)] = 255
grid_plot([("Nhiễu muối tiêu", sp.astype(np.uint8)),
           ("Lọc trung bình 3×3 (còn mờ)", ndimage.uniform_filter(sp, 3).astype(np.uint8)),
           ("Lọc trung vị 3×3 (sạch, giữ cạnh)", ndimage.median_filter(sp, 3).astype(np.uint8))],
          "03_14_chu_de", "t01_trung_binh_vs_t02_trung_vi.png", figsize=(12, 4.6))
save(ndimage.uniform_filter(scene, 5), "03_14_chu_de", "t01_loc_trung_binh.png")
save(ndimage.median_filter(sp, 3), "03_14_chu_de", "t02_loc_trung_vi.png")
save(ndimage.gaussian_filter(scene, 2), "03_14_chu_de", "t03_loc_gaussian.png")
sharp = np.clip(scene - lap, 0, 255)
grid_plot([("Ảnh gốc", scene_u8), ("Laplacian", norm_signed(lap).astype(np.uint8)),
           ("Tăng nét bằng Laplacian (gốc − Laplacian)", sharp.astype(np.uint8))],
          "03_14_chu_de", "t04_laplacian_tang_net.png", figsize=(12, 4.6))
save(norm_mag(mag), "03_14_chu_de", "t05_loc_sobel.png")
save(norm_mag(ops["cmp_02_prewitt.png"]), "03_14_chu_de", "t06_loc_prewitt.png")
# thresholding: fixed + Otsu
hist, bins = np.histogram(scene_u8, 256, (0, 256))
cdf = hist.cumsum(); total = scene.size
w0 = cdf; w1 = total - cdf
mu = (hist * np.arange(256)).cumsum()
mu_t = mu[-1]
with np.errstate(invalid="ignore", divide="ignore"):
    bcv = (mu_t * w0 - mu * total) ** 2 / (w0 * w1)
otsu = int(np.nanargmax(bcv))
grid_plot([("Ảnh gốc", scene_u8),
           (f"Ngưỡng cố định 128", (scene > 128) * 255),
           (f"Ngưỡng Otsu = {otsu}", (scene > otsu) * 255)],
          "03_14_chu_de", "t07_thresholding_otsu.png", figsize=(12, 4.6))
# spatial filtering concept: impulse response of a 3x3 mean kernel
imp = np.zeros((64, 64)); imp[32, 32] = 255
grid_plot([("Ảnh xung đơn vị", imp.astype(np.uint8)),
           ("Sau lọc trung bình 3×3 (đáp ứng xung)", ndimage.uniform_filter(imp, 3).astype(np.uint8)),
           ("Sau lọc Gaussian (đáp ứng xung)", ndimage.gaussian_filter(imp, 1.0).astype(np.uint8))],
          "03_14_chu_de", "t08_loc_khong_gian_dap_ung_xung.png", figsize=(12, 4.6))
save(255 - color, "03_14_chu_de", "t09_bien_doi_am_ban.png")
log_img = np.log1p(scene / 255.0) / np.log(2) * 255
grid_plot([("Ảnh gốc", scene_u8), ("Biến đổi Logarit", log_img.astype(np.uint8))],
          "03_14_chu_de", "t10_bien_doi_logarit.png", figsize=(10, 5.4))
fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
for ax, g in zip(axes, [0.45, 1.0, 1.8, 2.6]):
    ax.imshow(np.clip(255 * (scene / 255.0) ** g, 0, 255), cmap="gray", vmin=0, vmax=255)
    ax.set_title(f"γ = {g}"); ax.axis("off")
fig.suptitle("Biến đổi Power-Law (Gamma)")
fig.tight_layout()
d = os.path.join(ROOT, "03_14_chu_de"); fig.savefig(os.path.join(d, "t11_bien_doi_gamma.png"), dpi=110)
plt.close(fig); print("wrote 03_14_chu_de/t11_bien_doi_gamma.png")
# piecewise-linear contrast stretching
lo, hi = np.percentile(scene, 5), np.percentile(scene, 95)
stretch = np.clip((scene - lo) / (hi - lo) * 255, 0, 255)
grid_plot([("Ảnh gốc", scene_u8), ("Kéo dãn tương phản (Piecewise-Linear)", stretch.astype(np.uint8))],
          "03_14_chu_de", "t12_piecewise_linear.png", figsize=(10, 5.4))
# bit planes
panels = [(f"Bit-plane {b}", ((scene_u8 >> b) & 1) * 255) for b in range(7, -1, -1)]
grid_plot(panels, "03_14_chu_de", "t13_cat_bit_plane.png", figsize=(11, 11))
# histogram equalization on a low-contrast version
low = (90 + scene * 0.3).astype(np.uint8)
h, _ = np.histogram(low, 256, (0, 256))
eq_map = np.round(h.cumsum() / low.size * 255).astype(np.uint8)
eq = eq_map[low]
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].imshow(low, cmap="gray", vmin=0, vmax=255); axes[0, 0].set_title("Ảnh tương phản thấp")
axes[0, 1].bar(range(256), np.histogram(low, 256, (0, 256))[0], width=1); axes[0, 1].set_title("Histogram trước")
axes[1, 0].imshow(eq, cmap="gray", vmin=0, vmax=255); axes[1, 0].set_title("Sau cân bằng histogram")
axes[1, 1].bar(range(256), np.histogram(eq, 256, (0, 256))[0], width=1); axes[1, 1].set_title("Histogram sau")
for ax in axes.ravel(): ax.axis("on")
fig.tight_layout(); fig.savefig(os.path.join(d, "t14_can_bang_histogram.png"), dpi=110)
plt.close(fig); print("wrote 03_14_chu_de/t14_can_bang_histogram.png")

# ---------------------------------------------------- 04 hash pipelines
import tempfile
TMPD = tempfile.mkdtemp(prefix="vc_demo_")
def P(im, name):
    p = os.path.join(TMPD, name)
    im.save(p)
    return p

def bits_grid(bits, title):
    g = np.array([(bits >> (63 - i)) & 1 for i in range(64)]).reshape(8, 8)
    return (g * 255).astype(np.uint8), title

pil_scene = Image.fromarray(scene_u8)
SCENE_PATH = P(pil_scene, "scene.png")
small32 = np.asarray(pil_scene.resize((32, 32), Image.LANCZOS)).astype(np.float64)
dct = fft.dctn(small32, type=2, norm="ortho")
grid_plot([("Thu về 32×32", np.asarray(pil_scene.resize((32, 32), Image.LANCZOS))),
           ("DCT 2D (log độ lớn)", np.clip(np.log1p(np.abs(dct)) / np.log1p(np.abs(dct)).max() * 255, 0, 255).astype(np.uint8)),
           ("Khối tần thấp 8×8 (phóng to)", np.asarray(Image.fromarray(np.clip(dct[:8, :8] / (np.abs(dct[:8, :8]).max() + 1e-9) * 127 + 128, 0, 255).astype(np.uint8)).resize((256, 256), Image.NEAREST))),
           ("pHash 64 bit (8×8)", bits_grid(phash(SCENE_PATH), "")[0])],
          "04_pipeline_hash", "hash_01_cac_buoc_phash.png")
small9 = np.asarray(pil_scene.resize((9, 8), Image.LANCZOS))
grid_plot([("Thu về 9×8 (phóng to)", np.asarray(Image.fromarray(small9.astype(np.uint8)).resize((288, 256), Image.NEAREST))),
           ("dHash 64 bit (so pixel kề phải)", bits_grid(dhash(SCENE_PATH), "")[0])],
          "04_pipeline_hash", "hash_02_cac_buoc_dhash.png", figsize=(10, 5.4))
# hamming visual: original vs inverted hashes
inv = Image.fromarray((255 - scene).astype(np.uint8))
INV_PATH = P(inv, "inv.png")
h1, h2 = phash(SCENE_PATH), phash(INV_PATH)
diff = np.array([((h1 ^ h2) >> (63 - i)) & 1 for i in range(64)]).reshape(8, 8)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
for ax, g, t in zip(axes,
                    [np.array([(h1 >> (63 - i)) & 1 for i in range(64)]).reshape(8, 8),
                     np.array([(h2 >> (63 - i)) & 1 for i in range(64)]).reshape(8, 8), diff],
                    ["pHash ảnh gốc", "pHash ảnh âm bản", "Bit khác nhau (đỏ = lệch)\nHamming = 62"]):
    ax.imshow(g, cmap="gray", vmin=0, vmax=1); ax.set_title(t); ax.axis("off")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "04_pipeline_hash", "hash_03_hamming_am_ban.png"), dpi=110)
plt.close(fig); print("wrote 04_pipeline_hash/hash_03_hamming_am_ban.png")

# ------------------------------------------------------- 05 edge hash
mag32 = sobel_magnitude(SCENE_PATH)
blocks = mag32.reshape(8, 4, 8, 4).mean(axis=(1, 3))
grid_plot([("Độ lớn Sobel 32×32", np.clip(mag32 / (mag32.max() + 1e-9) * 255, 0, 255).astype(np.uint8)),
           ("Trung bình khối 8×8", np.asarray(Image.fromarray(np.clip(blocks / (blocks.max() + 1e-9) * 255, 0, 255).astype(np.uint8)).resize((256, 256), Image.NEAREST))),
           ("edge_hash 64 bit", bits_grid(edge_hash(SCENE_PATH), "")[0])],
          "05_edge_hash", "edge_01_cac_buoc_edge_hash.png", figsize=(12, 4.6))
mag32_inv = sobel_magnitude(INV_PATH)
grid_plot([("Độ lớn Sobel — ảnh gốc", np.clip(mag32 / (mag32.max() + 1e-9) * 255, 0, 255).astype(np.uint8)),
           ("Độ lớn Sobel — ảnh âm bản (giống hệt)", np.clip(mag32_inv / (mag32_inv.max() + 1e-9) * 255, 0, 255).astype(np.uint8)),
           ("edge_hash gốc", bits_grid(edge_hash(SCENE_PATH), "")[0]),
           ("edge_hash âm bản (lệch 0 bit)", bits_grid(edge_hash(INV_PATH), "")[0])],
          "05_edge_hash", "edge_02_bat_bien_am_ban.png")
# blur series + energies
fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
energies = []
for ax, r in zip(axes, [0, 1, 2, 3]):
    im_r = pil_scene if r == 0 else Image.fromarray(ndimage.gaussian_filter(scene, r).astype(np.uint8))
    _p = P(im_r, f"blur_{r}.png")
    e = edge_energy(_p)
    energies.append(e)
    m = sobel_magnitude(_p)
    ax.imshow(np.clip(m / (m.max() + 1e-9) * 255, 0, 255), cmap="gray", vmin=0, vmax=255)
    ax.set_title(f"Gaussian r={r}\nnăng lượng cạnh = {e:.1f}"); ax.axis("off")
fig.suptitle("Ảnh càng mờ, năng lượng cạnh càng sụt — cơ sở phát hiện ảnh mờ")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "05_edge_hash", "edge_03_nang_luong_canh_va_mo.png"), dpi=110)
plt.close(fig); print("wrote 05_edge_hash/edge_03_nang_luong_canh_va_mo.png")
print("energies:", [round(e, 2) for e in energies])

# --------------------------------------------------------- 06 variants
from PIL import ImageEnhance, ImageFilter
variants = [
    ("Gốc", pil_scene),
    ("Âm bản", inv),
    ("Sáng ×1.8", ImageEnhance.Brightness(pil_scene).enhance(1.8)),
    ("Tối ×0.5", ImageEnhance.Brightness(pil_scene).enhance(0.5)),
    ("Tương phản 0.3", ImageEnhance.Contrast(pil_scene).enhance(0.3)),
    ("Gamma 0.5", Image.fromarray((255 * (scene / 255.0) ** 0.5).astype(np.uint8))),
    ("Gamma 2.0", Image.fromarray((255 * (scene / 255.0) ** 2.0).astype(np.uint8))),
    ("Mờ r=2", pil_scene.filter(ImageFilter.GaussianBlur(2))),
    ("Nét", pil_scene.filter(ImageFilter.UnsharpMask(2, 150, 3))),
    ("Crop 10%", pil_scene.crop((26, 26, 486, 486)).resize((512, 512))),
    ("Crop 25%", pil_scene.crop((64, 64, 448, 448)).resize((512, 512))),
    ("Lật ngang", pil_scene.transpose(Image.FLIP_LEFT_RIGHT)),
    ("JPEG q40", None),
]
buf = os.path.join(ROOT, "06_bien_the", "_tmp.jpg")
os.makedirs(os.path.dirname(buf), exist_ok=True)
pil_scene.save(buf, quality=40)
variants[-1] = ("JPEG q40", Image.open(buf).convert("L").copy())
os.remove(buf)
h0 = (phash(SCENE_PATH), dhash(SCENE_PATH), edge_hash(SCENE_PATH))
fig, axes = plt.subplots(3, 5, figsize=(14, 8.6))
for ax, (name, im) in zip(axes.ravel(), variants + [("—", None)] * (15 - len(variants))):
    if im is None:
        ax.axis("off"); continue
    ax.imshow(np.asarray(im), cmap="gray", vmin=0, vmax=255)
    _vp = P(im, "var_tmp.png")
    dd = [bin(a ^ b).count("1") for a, b in zip(h0, (phash(_vp), dhash(_vp), edge_hash(_vp)))]
    ax.set_title(f"{name}\npHash {dd[0]} · dHash {dd[1]} · edge {dd[2]}", fontsize=10)
    ax.axis("off")
fig.suptitle("13 biến thể của ảnh gốc và khoảng cách Hamming tới ảnh gốc (ngưỡng trùng = 10)", fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "06_bien_the", "var_00_ghep_bien_the.png"), dpi=110)
plt.close(fig); print("wrote 06_bien_the/var_00_ghep_bien_the.png")
# key 2-ups
for name, im, fn in [("Âm bản", inv, "var_01_am_ban.png"),
                     ("Crop 25%", variants[10][1], "var_02_crop25.png"),
                     ("Lật ngang", variants[11][1], "var_03_lat_ngang.png")]:
    grid_plot([("Ảnh gốc", scene_u8), (name, np.asarray(im))],
              "06_bien_the", fn, figsize=(10, 5.4))

print("DONE")
