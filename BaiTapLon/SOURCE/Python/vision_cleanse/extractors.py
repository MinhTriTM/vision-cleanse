"""Feature extractors for VisionCleanse MVP (rings 1 and 2).

Ring 1: cryptographic file hashes (exact byte duplicates).
Ring 2: perceptual hashes (pHash / dHash) for resize / re-encode /
format-change duplicates.

Only Pillow + numpy are required. pHash/dHash are implemented here
instead of depending on the ``imagehash`` package, so the MVP has
zero heavy dependencies.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".gif"}

_CHUNK_SIZE = 1024 * 1024


def file_hash(path: str | Path, algo: str = "md5") -> str:
    """Stream-hash a file. ``algo`` is ``md5`` (default) or ``sha256``."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def image_size(path: str | Path) -> tuple[int, int]:
    """Return ``(width, height)`` without fully decoding the image."""
    with Image.open(path) as im:
        return im.size


def _grayscale_pixels(path: str | Path, size: tuple[int, int]) -> np.ndarray:
    with Image.open(path) as im:
        im = im.convert("L").resize(size, Image.Resampling.LANCZOS)
        return np.asarray(im, dtype=np.float64)


def _bits_to_int(bits: np.ndarray) -> int:
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bool(bit))
    return value


def dhash(path: str | Path, hash_size: int = 8) -> int:
    """Difference hash: 64-bit int for the default ``hash_size=8``.

    Compares each pixel with its right neighbour on a small grayscale
    image. Robust to resize, re-encode and format change; weak to
    crop and rotation (those belong to a later ring).
    """
    pixels = _grayscale_pixels(path, (hash_size + 1, hash_size))
    bits = pixels[:, 1:] > pixels[:, :-1]
    return _bits_to_int(bits)


def _dct_matrix(n: int) -> np.ndarray:
    """Orthogonal DCT-II matrix of size ``n`` (direct cos formula).

    Cached: the same matrix is reused for every image, which matters
    when hashing thousands of files (benchmarks, large datasets).
    The matrix is never mutated by callers.
    """
    return _dct_matrix_cached(n)


@lru_cache(maxsize=8)
def _dct_matrix_cached(n: int) -> np.ndarray:
    m = np.empty((n, n), dtype=np.float64)
    for k in range(n):
        for i in range(n):
            m[k, i] = np.cos((np.pi / n) * (i + 0.5) * k)
    m[0, :] *= np.sqrt(1.0 / n)
    m[1:, :] *= np.sqrt(2.0 / n)
    return m


def phash(path: str | Path, hash_size: int = 8, highfreq_factor: int = 4) -> int:
    """Perceptual hash (DCT-based): 64-bit int for ``hash_size=8``.

    Keeps the low-frequency DCT coefficients of a small grayscale
    image and thresholds them at their median. Robust to resize,
    re-encode, format change and light JPEG artefacts; weak to
    crop and rotation (later rings).
    """
    img_size = hash_size * highfreq_factor
    pixels = _grayscale_pixels(path, (img_size, img_size))
    dct = _dct_matrix(img_size)
    coeffs = dct @ pixels @ dct.T
    low = coeffs[:hash_size, :hash_size]
    median = np.median(low)
    return _bits_to_int(low > median)


def is_blank(path: str | Path) -> bool:
    """True when the image carries (almost) no structure.

    Grayscale-resized (32x32) standard deviation below 1.0 -- the
    same criterion the health check uses for "blank" images, but
    measured on the small image so it costs one cheap decode.
    Solid images have no structure for perceptual hashes to read:
    their dHash is always 0 and their pHash is float noise, so
    grouping them as near-duplicates is meaningless. Since 0.2.3,
    blank records are excluded from near-duplicate edges (byte
    identical blanks still group as exact).
    """
    pixels = _grayscale_pixels(path, (32, 32))
    return float(pixels.std()) < 1.0

# --- Sobel edge features (ring 2.5) -------------------------------------
# dHash is already a 1-D gradient ([-1, +1] between neighbours).
# Sobel is the standard 2-D version of the same idea: two 3x3
# kernels, one per axis, with a centre weight of 2 that smooths
# noise along the other axis. Only numpy + Pillow, like the rest
# of this module -- no OpenCV.

_SOBEL_GX = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
_SOBEL_GY = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64)


def _conv3x3(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """3x3 convolution by shifted adds (edge-padded, no per-pixel loop)."""
    out = np.zeros_like(img)
    p = np.pad(img, 1, mode="edge")
    h, w = img.shape
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            out += kernel[i + 1, j + 1] * p[1 + i:1 + i + h, 1 + j:1 + j + w]
    return out


def sobel_magnitude(path: str | Path, size: tuple[int, int] = (32, 32)) -> np.ndarray:
    """Sobel gradient magnitude ``sqrt(Gx^2 + Gy^2)`` on a small grayscale image.

    Returns a float64 array of shape ``size`` (default 32x32).
    Magnitude depends on *where* brightness changes, not on the
    absolute brightness -- so it is (near-)invariant to global
    brightening, contrast change and even inversion, where pHash /
    dHash can drift.
    """
    pixels = _grayscale_pixels(path, size)
    gx = _conv3x3(pixels, _SOBEL_GX)
    gy = _conv3x3(pixels, _SOBEL_GY)
    return np.hypot(gx, gy)


def sobel_magnitude_image(path: str | Path) -> Image.Image:
    """Full-resolution Sobel magnitude image (for slides / demo).

    Flat areas are near-black, object boundaries light up.
    Normalised to 0-255; a blank image returns an all-black image.
    """
    with Image.open(path) as im:
        pixels = np.asarray(im.convert("L"), dtype=np.float64)
    mag = np.hypot(_conv3x3(pixels, _SOBEL_GX), _conv3x3(pixels, _SOBEL_GY))
    peak = float(mag.max()) if mag.size else 0.0
    if peak <= 0:
        return Image.fromarray(np.zeros_like(mag, dtype=np.uint8))
    return Image.fromarray((mag / peak * 255).astype(np.uint8))


def edge_hash(path: str | Path, hash_size: int = 8) -> int:
    """64-bit structural hash from the Sobel edge map (default ``hash_size=8``).

    Sobel magnitude on a 32x32 grayscale image, block-averaged down
    to ``hash_size`` x ``hash_size``, thresholded at its median --
    the same median-threshold trick pHash uses, applied to edges
    instead of DCT coefficients. Two images that differ only by a
    strong tonal change (brightness / contrast / inversion) keep
    (near-)identical edge hashes, while images with different
    structure do not.
    """
    mag = sobel_magnitude(path, (32, 32))
    block = 32 // hash_size
    small = mag.reshape(hash_size, block, hash_size, block).mean(axis=(1, 3))
    return _bits_to_int(small > np.median(small))


def edge_energy(path: str | Path, size: tuple[int, int] = (128, 128)) -> float:
    """Mean Sobel magnitude on a grayscale image (default 128x128).

    A sharp, structured image scores high; a flat image scores ~0.
    Measured at 128x128 on purpose: at 32x32 the resize already
    blurs everything, so a Gaussian blur (r=3) only drops the
    score to 0.93x; at 128x128 the same blur drops it to 0.47x
    (measured on the synthetic photo fixture). Intended as a
    cheap "blurry?" health signal -- the health check today only
    catches flat images (std < 1.0).
    """
    return float(sobel_magnitude(path, size).mean())
