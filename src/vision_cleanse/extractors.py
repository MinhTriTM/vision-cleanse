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


def hash_hex(value: int, bits: int = 64) -> str:
    """Render an integer hash as a zero-padded hex string."""
    return format(value, f"0{bits // 4}x")
