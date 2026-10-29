"""Shared synthetic-image builders for the VisionCleanse tests.

All fixtures are generated with Pillow/numpy -- no external images.
"""

import numpy as np
from PIL import Image, ImageDraw


def gradient(path, size=128, reverse=False):
    g = np.tile(np.linspace(0, 255, size, dtype=np.uint8), (size, 1))
    if reverse:
        g = np.fliplr(g)
    Image.fromarray(g).save(path)
    return path


def checkerboard(path, size=128, cell=16):
    cb = ((np.indices((size, size)).sum(axis=0) // cell) % 2 * 255).astype(np.uint8)
    Image.fromarray(cb).save(path)
    return path


def circle(path, size=128):
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    d.ellipse([size // 4, size // 4, 3 * size // 4, 3 * size // 4], fill=255)
    im.save(path)
    return path


def noise(path, size=128, seed=0):
    rng = np.random.default_rng(seed)
    Image.fromarray(rng.integers(0, 256, (size, size), dtype=np.uint8)).save(path)
    return path


def photo_like(path, size=256, seed=42):
    """Textured pseudo-photo: gradient + noise + random shapes."""
    rng = np.random.default_rng(seed)
    base = np.tile(np.linspace(40, 200, size, dtype=np.uint8), (size, 1)).astype(np.int16)
    base += rng.integers(-25, 26, (size, size))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im)
    for _ in range(30):
        x, y = rng.integers(0, size - 36, 2)
        color = tuple(int(v) for v in rng.integers(0, 255, 3))
        d.rectangle([x, y, x + 30, y + 30], fill=color)
        d.ellipse([x, y, x + 25, y + 25], outline=(255, 255, 255))
    im.save(path)
    return path
