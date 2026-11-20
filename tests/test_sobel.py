"""Tests for the Sobel ring (2.5): edge_hash / edge_energy / verification.

Headline result, measured on the synthetic photo fixture:
inverting the image destroys pHash (distance 62) and dHash (64)
but leaves the Sobel edge hash untouched (distance 0) -- edges
are structure, not tone. The same fixture blurred with
Gaussian r=3 drops edge_energy to 0.47x at 128x128.

Honest limits, also tested here: a linear gradient (or a regular
checkerboard) has a uniform edge map, so its edge hash is 0 --
"no edge structure". Such pairs are never vetoed by the edge
check, and edge_hash is a verification layer only, never a
standalone grouping signal.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from helpers import checkerboard, gradient, photo_like

from vision_cleanse.extractors import edge_energy, edge_hash, sobel_magnitude_image
from vision_cleanse.matchers import group_duplicates, hamming


class TestEdgeHash(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photo = photo_like(self.tmp / "photo.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _variant(self, name, fn):
        p = self.tmp / name
        fn(Image.open(self.photo)).save(p)
        return p

    def test_inversion_keeps_edge_hash_but_breaks_phash_dhash(self):
        from vision_cleanse.extractors import dhash, phash

        inv = self._variant("inv.png", lambda im: ImageOps.invert(im.convert("RGB")))
        self.assertEqual(hamming(edge_hash(self.photo), edge_hash(inv)), 0)
        self.assertGreaterEqual(hamming(phash(self.photo), phash(inv)), 60)
        self.assertGreaterEqual(hamming(dhash(self.photo), dhash(inv)), 60)

    def test_low_contrast_and_blur_keep_edge_hash_close(self):
        from PIL import ImageEnhance

        lowcon = self._variant("lowcon.png", lambda im: ImageEnhance.Contrast(im).enhance(0.3))
        blur = self._variant("blur.png", lambda im: im.filter(ImageFilter.GaussianBlur(2)))
        self.assertLessEqual(hamming(edge_hash(self.photo), edge_hash(lowcon)), 10)
        self.assertLessEqual(hamming(edge_hash(self.photo), edge_hash(blur)), 10)

    def test_different_photo_has_distant_edge_hash(self):
        other = photo_like(self.tmp / "photo2.png", seed=7)
        self.assertGreaterEqual(hamming(edge_hash(self.photo), edge_hash(other)), 20)

    def test_uniform_edge_map_hashes_to_zero(self):
        # A linear gradient has the same gradient everywhere, so
        # its edge map is flat and the median-thresholded hash is 0.
        grad = gradient(self.tmp / "grad.png")
        self.assertEqual(edge_hash(grad), 0)
        self.assertEqual(edge_hash(checkerboard(self.tmp / "check.png")), 0)

    def test_sobel_magnitude_image_is_black_on_blank(self):
        blank = self.tmp / "blank.png"
        Image.new("L", (64, 64), 255).save(blank)
        out = sobel_magnitude_image(blank)
        self.assertEqual(out.size, (64, 64))
        self.assertEqual(max(out.getdata()), 0)
        self.assertGreater(max(sobel_magnitude_image(self.photo).getdata()), 0)


class TestEdgeEnergy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.photo = photo_like(self.tmp / "photo.png", size=256)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_blur_drops_energy_to_about_half(self):
        blur = self.tmp / "blur.png"
        Image.open(self.photo).filter(ImageFilter.GaussianBlur(3)).save(blur)
        ratio = edge_energy(blur) / edge_energy(self.photo)
        self.assertLess(ratio, 0.6)
        self.assertGreater(ratio, 0.3)

    def test_blank_energy_is_zero(self):
        blank = self.tmp / "blank.png"
        Image.new("L", (64, 64), 0).save(blank)
        self.assertEqual(edge_energy(blank), 0.0)


class TestEdgeVerification(unittest.TestCase):
    """group_duplicates(edge_threshold=...) vetoes only with real edges."""

    def _rec(self, md5, ph, dh, eh=None):
        r = {"path": md5, "md5": md5, "phash": ph, "dhash": dh}
        if eh is not None:
            r["edge_hash"] = eh
        return r

    def test_edge_hash_rescues_pair_hashes_miss(self):
        # pHash and dHash both far away, edge hashes identical:
        # without the edge signal this pair never groups.
        a = self._rec("a", (1 << 62) - 1, (1 << 63) - 1, 0b101010)
        b = self._rec("b", 0, 0, 0b101010)
        self.assertEqual(len(group_duplicates([a, b])), 0)
        self.assertEqual(len(group_duplicates([a, b], edge_threshold=10)), 1)

    def test_edge_disagreement_vetoes_hash_pair(self):
        a = self._rec("a", 0, 0, 0b101010)
        b = self._rec("b", (1 << 5) - 1, (1 << 5) - 1, (1 << 40) - 1)
        self.assertEqual(len(group_duplicates([a, b])), 1)
        # With the veto on, the same pair must NOT group.
        self.assertEqual(group_duplicates([a, b], edge_threshold=10), [])

    def test_edge_agreement_keeps_hash_pair(self):
        a = self._rec("a", 0, 0, 0b101010)
        b = self._rec("b", (1 << 5) - 1, (1 << 5) - 1, 0b101011)
        self.assertEqual(len(group_duplicates([a, b], edge_threshold=10)), 1)

    def test_missing_or_zero_edge_hash_never_vetoes(self):
        a = self._rec("a", 0, 0)
        b = self._rec("b", (1 << 5) - 1, (1 << 5) - 1)
        self.assertEqual(len(group_duplicates([a, b], edge_threshold=10)), 1)
        c = self._rec("c", 0, 0, 0)
        d = self._rec("d", (1 << 5) - 1, (1 << 5) - 1, 0)
        self.assertEqual(len(group_duplicates([c, d], edge_threshold=10)), 1)

    def test_exact_pair_is_never_vetoed(self):
        a = self._rec("same", 0, 0, 0b101010)
        b = self._rec("same", (1 << 40) - 1, (1 << 40) - 1, (1 << 40) - 1)
        self.assertEqual(len(group_duplicates([a, b], edge_threshold=10)), 1)

    def test_off_by_default(self):
        a = self._rec("a", 0, 0, 0b101010)
        b = self._rec("b", (1 << 5) - 1, (1 << 5) - 1, (1 << 40) - 1)
        self.assertEqual(len(group_duplicates([a, b])), 1)


if __name__ == "__main__":
    unittest.main()


class TestEdgeEndToEnd(unittest.TestCase):
    """clean(..., sobel_verify=True) rescues an inverted duplicate."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        (self.root / "train").mkdir(parents=True)
        (self.root / "val").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_inverted_photo_groups_only_with_sobel_verify(self):
        from PIL import ImageOps

        from vision_cleanse import clean

        photo = photo_like(self.tmp / "photo.png")
        shutil.copy(photo, self.root / "train" / "photo.png")
        ImageOps.invert(Image.open(photo).convert("RGB")).save(
            self.root / "val" / "photo_inv.png")
        plain = clean(self.root, dry_run=True, report_dir=self.tmp / "rep1")
        self.assertEqual(plain["duplicate_groups"], 0)
        verified = clean(self.root, dry_run=True, report_dir=self.tmp / "rep2",
                         sobel_verify=True)
        self.assertEqual(verified["duplicate_groups"], 1)
        self.assertEqual(verified["groups_near"], 1)
        self.assertTrue(verified["sobel_verify"])
