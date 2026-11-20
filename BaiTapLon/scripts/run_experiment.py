import sys, io, json
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageEnhance, ImageDraw
import numpy as np
from helpers import photo_like
from vision_cleanse.extractors import phash, dhash, edge_hash, edge_energy
from vision_cleanse.matchers import hamming

tmp = Path('/tmp/exp'); tmp.mkdir(exist_ok=True)
base = photo_like(tmp/'base.png')
im0 = Image.open(base).convert('RGB')
W,H = im0.size

def save(name, im):
    p = tmp/name; im.save(p); return p

variants = {}
variants['Gốc (đối chiếu)'] = base
variants['Thu nhỏ 50% rồi phóng lại'] = save('resize.png', im0.resize((W//2,H//2)).resize((W,H)))
buf = io.BytesIO(); im0.save(buf, 'JPEG', quality=40)
variants['Nén JPEG quality=40'] = save('jpeg.png', Image.open(io.BytesIO(buf.getvalue())).convert('RGB'))
variants['Tăng sáng +50'] = save('bright.png', ImageEnhance.Brightness(im0).enhance(1.5))
variants['Giảm sáng -50'] = save('dark.png', ImageEnhance.Brightness(im0).enhance(0.5))
variants['Tương phản thấp 0.3'] = save('lowcon.png', ImageEnhance.Contrast(im0).enhance(0.3))
variants['Tương phản cao 1.8'] = save('hicon.png', ImageEnhance.Contrast(im0).enhance(1.8))
lut = [round((i/255)**0.5*255) for i in range(256)]
variants['Gamma 0.5'] = save('g05.png', im0.point(lut*3))
lut2 = [round((i/255)**2.0*255) for i in range(256)]
variants['Gamma 2.0'] = save('g20.png', im0.point(lut2*3))
variants['Âm bản (invert)'] = save('inv.png', ImageOps.invert(im0))
variants['Làm mờ Gaussian r=2'] = save('blur.png', im0.filter(ImageFilter.GaussianBlur(2)))
variants['Làm nét (sharpen)'] = save('sharp.png', im0.filter(ImageFilter.UnsharpMask(2,150,3)))
m = int(W*0.10); variants['Crop 10% mỗi cạnh'] = save('crop10.png', im0.crop((m,m,W-m,H-m)).resize((W,H)))
m = int(W*0.25); variants['Crop 25% mỗi cạnh'] = save('crop25.png', im0.crop((m,m,W-m,H-m)).resize((W,H)))
variants['Lật ngang'] = save('flip.png', ImageOps.mirror(im0))
rng = np.random.default_rng(42)
noise = np.clip(np.asarray(im0).astype(int) + rng.normal(0,12,im0.size[::-1]+(3,)), 0, 255).astype(np.uint8)
variants['Nhiễu Gaussian sigma=12'] = save('noise.png', Image.fromarray(noise))
other = photo_like(tmp/'other.png', seed=7)
variants['Ảnh khác (không trùng)'] = other

p0, d0, e0 = phash(base), dhash(base), edge_hash(base)
en0 = edge_energy(base)
rows = []
for name, p in variants.items():
    rows.append({'variant': name,
                 'phash': hamming(p0, phash(p)),
                 'dhash': hamming(d0, dhash(p)),
                 'edge': hamming(e0, edge_hash(p)),
                 'energy_ratio': round(edge_energy(p)/en0, 3)})
print(json.dumps(rows, ensure_ascii=False, indent=1))
Path('/home/hatch/workspace/BaoCao-Sobel-XuLyAnh/experiment/results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1))
