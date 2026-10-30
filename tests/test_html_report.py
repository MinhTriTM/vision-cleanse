"""Tests for the self-contained HTML verification report."""

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import gradient, photo_like

from vision_cleanse import clean


class TestHtmlReport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_report_html_written_with_groups(self):
        root = self.tmp / "ds"
        d = root / "train" / "cat"
        d.mkdir(parents=True)
        grad = gradient(self.tmp / "g.png")
        shutil.copy(grad, d / "a.png")
        shutil.copy(grad, d / "b.png")  # exact duplicate of a.png
        photo_like(d / "c.png", seed=77)
        rep_dir = self.tmp / "rep"
        report = clean(root, report_dir=rep_dir)
        self.assertIn("html_report", report)
        html_path = Path(report["html_report"])
        self.assertTrue(html_path.is_file())
        text = html_path.read_text(encoding="utf-8")
        self.assertIn("Nhóm #0", text)
        self.assertIn("a.png", text)
        self.assertIn("b.png", text)
        self.assertIn("data:image/jpeg;base64", text)
        self.assertIn('id="f-method"', text)
        self.assertIn('id="f-search"', text)
        self.assertIn("duplicate_within_same_split", text)

    def test_conflict_group_kept_whole(self):
        root = self.tmp / "cds"
        for label in ("cat", "dog"):
            d = root / "train" / label
            d.mkdir(parents=True)
            shutil.copy(gradient(self.tmp / f"g{label}.png"), d / "same.png")
        rep_dir = self.tmp / "rep2"
        report = clean(root, report_dir=rep_dir)
        text = Path(report["html_report"]).read_text(encoding="utf-8")
        self.assertIn("xung đột nhãn", text)

    def test_no_html_without_report_dir(self):
        root = self.tmp / "ds2"
        d = root / "train" / "cat"
        d.mkdir(parents=True)
        photo_like(d / "a.png", seed=78)
        report = clean(root, report_dir=None)
        self.assertNotIn("html_report", report)


if __name__ == "__main__":
    unittest.main()
