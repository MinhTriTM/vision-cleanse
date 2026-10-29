"""Tests for split-priority resolution and label conflicts."""

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import checkerboard, gradient
from vision_cleanse import clean


def _ds(root, split, label, name, src):
    d = Path(root) / split / label
    d.mkdir(parents=True, exist_ok=True)
    dst = d / name
    shutil.copy(src, dst)
    return dst


class TestSplitPriority(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        self.src = gradient(self.tmp / "src.png")
        self.other = checkerboard(self.tmp / "other.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_test_beats_train(self):
        _ds(self.root, "train", "cat", "a.png", self.src)
        _ds(self.root, "test", "cat", "a_copy.png", self.src)
        rep = clean(self.root, dry_run=True)
        removed = {r["path"] for r in rep["removals"]}
        self.assertIn(str(self.root / "train" / "cat" / "a.png"), removed)
        self.assertNotIn(str(self.root / "test" / "cat" / "a_copy.png"), removed)

    def test_val_beats_train(self):
        _ds(self.root, "train", "cat", "a.png", self.src)
        _ds(self.root, "val", "cat", "b.png", self.src)
        rep = clean(self.root, dry_run=True)
        removed = {r["path"] for r in rep["removals"]}
        self.assertEqual(removed, {str(self.root / "train" / "cat" / "a.png")})

    def test_same_split_keeps_highest_resolution(self):
        from PIL import Image

        big = _ds(self.root, "train", "cat", "big.png", self.src)
        small = self.root / "train" / "cat" / "small.png"
        Image.open(self.src).resize((64, 64)).save(small)
        rep = clean(self.root, dry_run=True)
        removed = {r["path"] for r in rep["removals"]}
        self.assertEqual(removed, {str(small)})
        self.assertNotIn(str(big), removed)

    def test_deterministic_across_runs(self):
        _ds(self.root, "train", "cat", "a.png", self.src)
        _ds(self.root, "test", "cat", "b.png", self.src)
        r1 = clean(self.root, dry_run=True)
        r2 = clean(self.root, dry_run=True)
        self.assertEqual(
            [r["path"] for r in r1["removals"]], [r["path"] for r in r2["removals"]]
        )

    def test_missing_split_skipped(self):
        _ds(self.root, "train", "cat", "a.png", self.src)
        rep = clean(self.root, dry_run=True)
        self.assertIn("val", rep["splits_missing"])
        self.assertIn("test", rep["splits_missing"])

    def test_flat_layout_no_label(self):
        d = self.root / "train"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.src, d / "a.png")
        shutil.copy(self.src, d / "b.png")
        rep = clean(self.root, dry_run=True)
        self.assertEqual(rep["duplicate_groups"], 1)
        self.assertEqual(rep["label_conflicts"], 0)
        self.assertEqual(len(rep["removals"]), 1)


class TestLabelConflict(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        self.src = gradient(self.tmp / "src.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_conflict_group_never_removed(self):
        _ds(self.root, "train", "cat", "a.png", self.src)
        _ds(self.root, "train", "dog", "b.png", self.src)
        report_dir = self.tmp / "report"
        rep = clean(self.root, dry_run=False, report_dir=report_dir,
                    quarantine_dir=self.tmp / "q")
        self.assertEqual(rep["label_conflicts"], 1)
        self.assertEqual(rep["removals"], [])
        self.assertTrue((self.root / "train" / "cat" / "a.png").exists())
        self.assertTrue((self.root / "train" / "dog" / "b.png").exists())
        csv_path = report_dir / "conflict_report.csv"
        self.assertTrue(csv_path.exists())
        text = csv_path.read_text(encoding="utf-8")
        self.assertIn("cat", text)
        self.assertIn("dog", text)


if __name__ == "__main__":
    unittest.main()
