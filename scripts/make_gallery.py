"""Regenerate the chart gallery and pipeline diagram in docs/assets/.

Builds a small deterministic YOLO demo dataset in a temp dir, runs
``clean(..., charts_dir=docs/assets/charts)`` so reviewers can see
real chart output without running anything, and draws the pipeline
flow diagram (docs/assets/pipeline.png).

Run: PYTHONPATH=src python scripts/make_gallery.py
Requires the charts extra (matplotlib).
"""

from __future__ import annotations

import itertools
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from vision_cleanse import clean


def _photo(path: Path, seed: int, size: tuple[int, int]) -> None:
    """Textured pseudo-photo (same recipe as tests/helpers.photo_like)."""
    rng = np.random.default_rng(seed)
    w, h = size
    base = np.tile(np.linspace(40, 200, w, dtype=np.uint8), (h, 1)).astype(np.int16)
    base += rng.integers(-25, 26, (h, w))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y = int(rng.integers(0, max(1, w - 36))), int(rng.integers(0, max(1, h - 36)))
        color = tuple(int(v) for v in rng.integers(0, 255, 3))
        d.rectangle([x, y, x + 30, y + 30], fill=color)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def _boxes(path: Path, seed: int, n: int, cls: int) -> None:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        x, y = round(float(rng.uniform(0.2, 0.8)), 2), round(float(rng.uniform(0.2, 0.8)), 2)
        w, h = round(float(rng.uniform(0.1, 0.4)), 2), round(float(rng.uniform(0.1, 0.4)), 2)
        rows.append(f"{cls} {x} {y} {w} {h}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _build_demo(root: Path) -> None:
    sizes = [(256, 256), (320, 240), (240, 320), (256, 256)]
    # train: 24 images (cat 14, dog 10); val: 12 images (cat 7, dog 5).
    plan = [("train", "cat", 14, 1000), ("train", "dog", 10, 2000),
            ("val", "cat", 7, 3000), ("val", "dog", 5, 4000)]
    idx = 0
    for split, cls_name, count, base in plan:
        cls = 0 if cls_name == "cat" else 1
        for k in range(count):
            seed = base + k
            name = f"{split}_{idx:02d}.jpg"
            _photo(root / "images" / split / name, seed, sizes[idx % len(sizes)])
            _boxes(root / "labels" / split / f"{split}_{idx:02d}.txt",
                   seed, 1 + (seed % 4), cls)
            idx += 1
    # Exact duplicate across splits (same class -> removal in train).
    shutil.copy(root / "images" / "train" / "train_00.jpg",
                 root / "images" / "val" / "train_00.jpg")
    shutil.copy(root / "labels" / "train" / "train_00.txt",
                 root / "labels" / "val" / "train_00.txt")
    # Near duplicate inside train (JPEG recompress, same class).
    im = Image.open(root / "images" / "train" / "train_01.jpg")
    im.save(root / "images" / "train" / "train_01_q40.jpg", quality=40)
    shutil.copy(root / "labels" / "train" / "train_01.txt",
                 root / "labels" / "train" / "train_01_q40.txt")
    (root / "data.yaml").write_text(
        "train: images/train\nval: images/val\nnc: 2\nnames:\n  - cat\n  - dog\n",
        encoding="utf-8",
    )


def _pipeline_diagram(out: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(9, 11))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    boxes = [
        (5, 13, "1. Discover\nClassic / YOLO layout\n(images, labels, data.yaml)"),
        (5, 11, "2. Extract\nMD5 / SHA-256  ·  pHash  ·  dHash"),
        (5, 9, "3. Group\nExact + near duplicates (OR rule, threshold 10)"),
        (5, 7, "4. Resolve\nKeep test > val > train · deterministic keeper"),
        (5, 5, "5. Quarantine\nMove + manifest.json (never hard-delete)"),
        (5, 3, "6. Health checks\n11 checks · clean verdict"),
        (5, 1, "7. Report + Charts\nreport.json · conflict_report.csv · 24 PNGs"),
    ]
    for cx, cy, text in boxes:
        ax.add_patch(FancyBboxPatch((cx - 3.4, cy - 0.7), 6.8, 1.4,
                                    boxstyle="round,pad=0.08",
                                    facecolor="#dce8ff", edgecolor="#2f5db3"))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=10)
    for (_, y0, _), (_, y1, _) in itertools.pairwise(boxes):
        ax.add_patch(FancyArrowPatch((5, y0 - 0.7), (5, y1 + 0.7),
                                     arrowstyle="-|>", mutation_scale=16,
                                     color="#2f5db3"))
    # Conflict side branch from step 4.
    ax.add_patch(FancyBboxPatch((7.6, 6.3), 2.3, 1.4,
                                boxstyle="round,pad=0.08",
                                facecolor="#ffe8cc", edgecolor="#b35c2f"))
    ax.text(8.75, 7.0, "Label conflict?\nKeep all +\nconflict_report.csv",
            ha="center", va="center", fontsize=9)
    ax.add_patch(FancyArrowPatch((8.4, 7.0), (7.6, 7.0),
                                 arrowstyle="-|>", mutation_scale=14,
                                 color="#b35c2f"))
    ax.set_title("VisionCleanse pipeline", fontsize=14)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main() -> int:
    assets = REPO / "docs" / "assets"
    charts_dir = assets / "charts"
    if charts_dir.exists():
        shutil.rmtree(charts_dir)
    charts_dir.mkdir(parents=True)
    tmp = Path(tempfile.mkdtemp(prefix="vcgallery_"))
    try:
        root = tmp / "demo"
        _build_demo(root)
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        print(f"Demo images: {report['images_found']}, "
              f"groups: {report['duplicate_groups']}, "
              f"to_quarantine: {report['to_quarantine']}")
        print(f"Charts: {len(report['charts']['generated'])} generated, "
              f"{len(report['charts']['skipped'])} skipped")
        for name in report["charts"]["generated"]:
            p = charts_dir / name
            print(f"  {name} ({p.stat().st_size // 1024} KB)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    _pipeline_diagram(assets / "pipeline.png")
    print(f"Pipeline diagram: {assets / 'pipeline.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
