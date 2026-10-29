"""Tests for dataset health checks (0.2.0)."""

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import checkerboard, circle, gradient
from PIL import Image

from vision_cleanse import clean


def _put(root, split, label, name, src):
    d = Path(root) / split / label
    d.mkdir(parents=True, exist_ok=True)
    dst = d / name
    if src is not None:
        shutil.copy(src, dst)
    return dst


def _solid(path, size=128, value=255):
    Image.new("L", (size, size), value).save(path)
    return path


class TestHealthChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        grad = gradient(self.tmp / "grad.png")
        _put(self.root, "train", "cat", "good.png", grad)
        (self.root / "train" / "cat" / "good.txt").write_text("0 0.5 0.5 0.2 0.2\n")
        (self.root / "train" / "cat" / "empty.jpg").write_bytes(b"")
        (self.root / "train" / "cat" / "corrupt.jpg").write_bytes(b"not an image")
        _put(self.root, "train", "cat", "blank.png", _solid(self.tmp / "blank.png"))
        small = self.tmp / "small.png"
        Image.open(grad).resize((16, 16)).save(small)
        _put(self.root, "train", "cat", "tiny.png", small)
        _put(self.root, "train", "cat", "nolabel.png",
             gradient(self.tmp / "rev.png", reverse=True))
        _put(self.root, "train", "cat", "bad.png", circle(self.tmp / "c.png"))
        (self.root / "train" / "cat" / "bad.txt").write_text("not a label\n")
        _put(self.root, "train", "cat", "empty_label.png",
             checkerboard(self.tmp / "cb.png"))
        (self.root / "train" / "cat" / "empty_label.txt").write_text("")
        (self.root / "train" / "cat" / "orphan.txt").write_text("0 0.5 0.5 0.2 0.2\n")
        (self.root / "train" / "cat" / "readme.md").write_text("notes\n")
        _put(self.root, "train", "cat", "dup.png", grad)
        _put(self.root, "test", "dog", "dup.png", circle(self.tmp / "c2.png"))
        _put(self.root, "test", "cat", "t1.png", grad)
        _put(self.root, "test", "cat", "t2.png", grad)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_all_checks_fire(self):
        rep = clean(self.root, dry_run=True)
        found = {f["check"] for f in rep["health"]["findings"]}
        for expected in (
            "zero_byte", "corrupt", "blank", "tiny", "missing_label",
            "orphan_label", "invalid_label", "empty_label",
            "dup_basename", "test_internal_dup", "other_file",
        ):
            with self.subTest(check=expected):
                self.assertIn(expected, found)
        self.assertFalse(rep["clean"])
        self.assertGreaterEqual(rep["health"]["counts"]["errors"], 3)
        self.assertGreaterEqual(rep["health"]["counts"]["warnings"], 6)

    def test_class_distribution_present(self):
        rep = clean(self.root, dry_run=True)
        dist = rep["health"]["class_distribution"]
        self.assertIn("train", dist)
        self.assertIn("cat", dist["train"])


class TestHealthCleanDataset(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        d = self.root / "train" / "cat"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(gradient(self.tmp / "g.png"), d / "a.png")
        (d / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_clean_verdict(self):
        rep = clean(self.root, dry_run=True)
        self.assertTrue(rep["clean"])
        self.assertEqual(rep["health"]["findings"], [])

    def test_yolo_checks_off_without_labels(self):
        root2 = self.tmp / "nolabel_ds"
        d = root2 / "train"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(gradient(self.tmp / "g2.png"), d / "a.png")
        rep = clean(root2, dry_run=True)
        checks = {f["check"] for f in rep["health"]["findings"]}
        self.assertTrue(checks.isdisjoint(
            {"missing_label", "orphan_label", "invalid_label", "empty_label"}))


if __name__ == "__main__":
    unittest.main()
