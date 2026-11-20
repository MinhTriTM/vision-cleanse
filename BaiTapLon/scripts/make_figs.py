import sys
sys.path.insert(0, 'src')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, json
from pathlib import Path
from PIL import Image
from vision_cleanse.extractors import sobel_magnitude_image

FIG = Path('/home/hatch/workspace/BaoCao-Sobel-XuLyAnh/figures'); FIG.mkdir(parents=True, exist_ok=True)

# Fig: edge map goc vs am ban
orig = Image.open('demo_sobel/photo.png'); inv = Image.open('demo_sobel/photo_inv.png')
fig, axes = plt.subplots(2, 2, figsize=(8, 6))
axes[0,0].imshow(orig); axes[0,0].set_title('a) Ảnh gốc'); axes[0,0].axis('off')
axes[0,1].imshow(inv); axes[0,1].set_title('b) Ảnh âm bản'); axes[0,1].axis('off')
axes[1,0].imshow(sobel_magnitude_image('demo_sobel/photo.png'), cmap='gray'); axes[1,0].set_title('c) Bản đồ cạnh Sobel của ảnh gốc'); axes[1,0].axis('off')
axes[1,1].imshow(sobel_magnitude_image('demo_sobel/photo_inv.png'), cmap='gray'); axes[1,1].set_title('d) Bản đồ cạnh Sobel của ảnh âm bản'); axes[1,1].axis('off')
plt.tight_layout(); plt.savefig(FIG/'fig_edge_invert.png', dpi=200); plt.close()

# Fig: bar chart khoang cach Hamming
rows = json.loads(Path('/home/hatch/workspace/BaoCao-Sobel-XuLyAnh/experiment/results.json').read_text())
sel = ['Tăng sáng +50','Gamma 2.0','Âm bản (invert)','Làm mờ Gaussian r=2','Crop 10% mỗi cạnh','Crop 25% mỗi cạnh','Lật ngang','Ảnh khác (không trùng)']
data = {r['variant']: r for r in rows}
x = np.arange(len(sel)); w = 0.27
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(x-w, [data[s]['phash'] for s in sel], w, label='pHash')
ax.bar(x,   [data[s]['dhash'] for s in sel], w, label='dHash')
ax.bar(x+w, [data[s]['edge'] for s in sel], w, label='edge_hash (Sobel)')
ax.axhline(10, color='red', ls='--', lw=1, label='Ngưỡng trùng mặc định = 10')
ax.set_xticks(x); ax.set_xticklabels([s.replace(' (invert)','').replace(' mỗi cạnh','') for s in sel], rotation=18, ha='right', fontsize=8)
ax.set_ylabel('Khoảng cách Hamming (bit)'); ax.set_ylim(0, 70); ax.legend(fontsize=8); ax.grid(axis='y', alpha=0.3)
plt.tight_layout(); plt.savefig(FIG/'fig_hamming.png', dpi=200); plt.close()

# Fig: edge energy ratio
sel2 = ['Giảm sáng -50','Tương phản thấp 0.3','Làm mờ Gaussian r=2','Nhiễu Gaussian sigma=12','Làm nét (sharpen)','Tương phản cao 1.8']
fig, ax = plt.subplots(figsize=(8, 3.8))
vals = [data[s]['energy_ratio'] for s in sel2]
colors = ['#c0392b' if v < 0.75 else '#2471a3' for v in vals]
ax.bar(range(len(sel2)), vals, color=colors)
ax.axhline(1.0, color='gray', ls='--', lw=1)
ax.set_xticks(range(len(sel2))); ax.set_xticklabels([s.replace(' Gaussian','') for s in sel2], rotation=15, ha='right', fontsize=8)
ax.set_ylabel('edge_energy / edge_energy gốc')
plt.tight_layout(); plt.savefig(FIG/'fig_energy.png', dpi=200); plt.close()
print('figs done')
