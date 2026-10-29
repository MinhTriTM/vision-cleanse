"""Tests for rings 1 (exact hash) and 2 (pHash / dHash)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import checkerboard, circle, gradient, noise, photo_like

from vision_cleanse.extractors import dhash, file_hash, phash
from vision_cleanse.matchers import group_duplicates, hamming


def _rec(path):
    return {"path": Path(path), "md5": file_hash(path), "phash": phash(path), "dhash": dhash(path)}


class TestHamming(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(hamming(0b101, 0b100), 1)
        self.assertEqual(hamming(0, 0), 0)
        self.assertEqual(hamming(0xFF, 0x00), 8)


class TestExactHash(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_identical_bytes_same_md5(self):
        a = gradient(self.tmp / "a.png")
        b = self.tmp / "b.png"
        shutil.copy(a, b)
        self.assertEqual(file_hash(a), file_hash(b))

    def test_renamed_copy_groups_as_exact(self):
        a = gradient(self.tmp / "a.png")
        b = self.tmp / "copy.png"
        shutil.copy(a, b)
        groups = group_duplicates([_rec(a), _rec(b)])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["method"], "exact")


class TestPerceptualHash(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.grad = gradient(self.tmp / "grad.png")
        self.photo = photo_like(self.tmp / "photo.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _grouped(self, a, b):
        return len(group_duplicates([_rec(a), _rec(b)])) == 1

    def test_resized_copy_groups(self):
        from PIL import Image

        small = self.tmp / "small.png"
        Image.open(self.grad).resize((64, 64)).save(small)
        self.assertTrue(self._grouped(self.grad, small))

    def test_format_change_groups(self):
        jpg = self.tmp / "grad_q95.jpg"
        from PIL import Image

        Image.open(self.grad).save(jpg, quality=95)
        self.assertTrue(self._grouped(self.grad, jpg))

    def test_heavy_jpeg_on_smooth_image_groups_via_dhash(self):
        """Regression: pHash alone drifts to 16 on smooth gradients
        at JPEG quality 30, but dHash stays 0 -- the OR rule must
        still group them."""
        jpg = self.tmp / "grad_q30.jpg"
        from PIL import Image

        Image.open(self.grad).save(jpg, quality=30)
        self.assertEqual(dhash(jpg), dhash(self.grad))
        self.assertTrue(self._grouped(self.grad, jpg))

    def test_heavy_jpeg_on_textured_image_groups(self):
        jpg = self.tmp / "photo_q30.jpg"
        from PIL import Image

        Image.open(self.photo).save(jpg, quality=30)
        self.assertLessEqual(hamming(phash(self.photo), phash(jpg)), 10)
        self.assertTrue(self._grouped(self.photo, jpg))

    def test_different_images_do_not_group(self):
        others = [
            gradient(self.tmp / "rev.png", reverse=True),
            checkerboard(self.tmp / "check.png"),
            circle(self.tmp / "circle.png"),
            noise(self.tmp / "noise.png", seed=0),
            photo_like(self.tmp / "photo2.png", seed=7),
        ]
        for other in others:
            with self.subTest(other=other.name):
                self.assertFalse(self._grouped(self.grad, other))
        self.assertFalse(self._grouped(self.photo, self.tmp / "photo2.png"))


if __name__ == "__main__":
    unittest.main()
