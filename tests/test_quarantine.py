"""Tests for dry-run safety, quarantine moves and YOLO label sync."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import gradient

from vision_cleanse import clean


class TestQuarantine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        src = gradient(self.tmp / "src.png")
        for split, name in (("train", "a.png"), ("test", "a_copy.png")):
            d = self.root / split / "cat"
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, d / name)
        # YOLO label next to the train copy (must move with it).
        (self.root / "train" / "cat" / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")
        self.qdir = self.tmp / "quarantine"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_dry_run_moves_nothing(self):
        rep = clean(self.root, dry_run=True, quarantine_dir=self.qdir)
        self.assertEqual(rep["to_quarantine"], 1)
        self.assertTrue((self.root / "train" / "cat" / "a.png").exists())
        self.assertFalse(self.qdir.exists())

    def test_apply_moves_to_quarantine_with_manifest(self):
        rep = clean(self.root, dry_run=False, quarantine_dir=self.qdir)
        self.assertEqual(rep["to_quarantine"], 1)
        moved_img = self.qdir / "train" / "cat" / "a.png"
        moved_lbl = self.qdir / "train" / "cat" / "a.txt"
        self.assertTrue(moved_img.exists())
        self.assertTrue(moved_lbl.exists())  # YOLO label moved alongside
        self.assertFalse((self.root / "train" / "cat" / "a.png").exists())
        self.assertTrue((self.root / "test" / "cat" / "a_copy.png").exists())  # keeper stays
        manifest = json.loads((self.qdir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]["image"], str(self.root / "train" / "cat" / "a.png"))
        self.assertIn("reason", manifest[0])

    def test_corrupt_file_listed_not_crash(self):
        bad = self.root / "train" / "cat" / "bad.jpg"
        bad.write_bytes(b"this is not an image at all")
        rep = clean(self.root, dry_run=True)
        self.assertTrue(any("bad.jpg" in u for u in rep["images_unreadable"]))
        self.assertEqual(rep["duplicate_groups"], 1)


if __name__ == "__main__":
    unittest.main()
