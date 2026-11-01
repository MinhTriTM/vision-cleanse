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


class TestNearMode(unittest.TestCase):
    """OR vs AND grouping on synthetic hash records (0.2.2)."""

    def _rec(self, md5, ph, dh):
        return {"path": md5, "md5": md5, "phash": ph, "dhash": dh}

    def _grouped(self, a, b, **kw):
        return len(group_duplicates([a, b], **kw)) == 1

    def test_one_hash_only_groups_under_or_not_and(self):
        # pHash at the threshold (10), dHash far away (30): the
        # borderline single-hash collision seen on the mushroom set.
        a = self._rec("a", 0, 0)
        b = self._rec("b", (1 << 10) - 1, (1 << 30) - 1)
        self.assertTrue(self._grouped(a, b, near_mode="or"))
        self.assertFalse(self._grouped(a, b, near_mode="and"))

    def test_both_within_groups_under_both_modes(self):
        a = self._rec("a", 0, 0)
        b = self._rec("b", (1 << 5) - 1, (1 << 8) - 1)
        self.assertTrue(self._grouped(a, b, near_mode="or"))
        self.assertTrue(self._grouped(a, b, near_mode="and"))

    def test_neither_within_groups_under_neither_mode(self):
        a = self._rec("a", 0, 0)
        b = self._rec("b", (1 << 20) - 1, (1 << 25) - 1)
        self.assertFalse(self._grouped(a, b, near_mode="or"))
        self.assertFalse(self._grouped(a, b, near_mode="and"))

    def test_exact_groups_under_both_modes(self):
        a = self._rec("same", 0, 0)
        b = self._rec("same", (1 << 40) - 1, (1 << 40) - 1)
        self.assertTrue(self._grouped(a, b, near_mode="or"))
        self.assertTrue(self._grouped(a, b, near_mode="and"))

    def test_invalid_mode_raises(self):
        a = self._rec("a", 0, 0)
        b = self._rec("b", 0, 0)
        with self.assertRaises(ValueError):
            group_duplicates([a, b], near_mode="xor")


if __name__ == "__main__":
    unittest.main()


class TestBlank(unittest.TestCase):
    """Solid images are excluded from near grouping (0.2.3)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _solid(self, name, value):
        from PIL import Image
        p = self.tmp / name
        Image.new("L", (64, 64), value).save(p)
        return p

    def test_is_blank(self):
        from vision_cleanse.extractors import is_blank
        self.assertTrue(is_blank(self._solid("black.png", 0)))
        self.assertTrue(is_blank(self._solid("white.png", 255)))
        self.assertFalse(is_blank(gradient(self.tmp / "grad.png")))

    def test_blank_records_never_form_near_edges(self):
        recs = [
            {"path": "black", "md5": "b1", "phash": 0, "dhash": 0, "blank": True},
            {"path": "white", "md5": "b2", "phash": 0, "dhash": 0, "blank": True},
            {"path": "gray", "md5": "b3", "phash": 0, "dhash": 0, "blank": True},
        ]
        for mode in ("or", "and"):
            self.assertEqual(group_duplicates(recs, near_mode=mode), [])

    def test_identical_blanks_still_group_as_exact(self):
        recs = [
            {"path": "a", "md5": "same", "phash": 0, "dhash": 0, "blank": True},
            {"path": "b", "md5": "same", "phash": 0, "dhash": 0, "blank": True},
        ]
        groups = group_duplicates(recs)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["method"], "exact")

    def test_clean_excludes_solid_images_from_near_groups(self):
        from vision_cleanse import clean
        root = self.tmp / "dataset"
        (root / "train").mkdir(parents=True, exist_ok=True)
        (root / "val").mkdir(parents=True, exist_ok=True)
        shutil.copy(self._solid("black.png", 0), root / "train" / "black.png")
        shutil.copy(self._solid("white.png", 255), root / "val" / "white.png")
        rep = clean(root, dry_run=True, report_dir=self.tmp / "rep")
        self.assertEqual(rep["duplicate_groups"], 0)
        self.assertEqual(rep["blank_images"], 2)
