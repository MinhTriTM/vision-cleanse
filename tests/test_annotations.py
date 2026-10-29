"""Tests for COCO annotation sync and the CLI."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import gradient

from vision_cleanse import clean
from vision_cleanse.cli import main as cli_main


def _coco(path):
    data = {
        "images": [
            {"id": 1, "file_name": "a.png"},
            {"id": 2, "file_name": "keep.png"},
        ],
        "annotations": [
            {"id": 10, "image_id": 1},
            {"id": 11, "image_id": 1},
            {"id": 12, "image_id": 2},
        ],
        "categories": [],
    }
    Path(path).write_text(json.dumps(data), encoding="utf-8")
    return path


class TestCocoSync(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        src = gradient(self.tmp / "src.png")
        keep_src = gradient(self.tmp / "keep.png", reverse=True)
        d = self.root / "train"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, d / "a.png")
        shutil.copy(src, d / "a_dup.png")  # duplicate of a.png -> removed
        shutil.copy(keep_src, d / "keep.png")
        self.coco = _coco(self.tmp / "ann.json")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_apply_syncs_coco_without_touching_original(self):
        out = self.tmp / "ann.cleaned.json"
        before = (self.tmp / "ann.json").read_text(encoding="utf-8")
        rep = clean(self.root, dry_run=False, coco_path=self.coco, coco_output=out,
                    quarantine_dir=self.tmp / "q")
        sync = rep["coco_sync"]
        self.assertEqual(sync["images_before"], 2)
        # a.png is the keeper (lexicographically smaller than a_dup.png),
        # so a_dup.png is removed; COCO has no a_dup.png entry, so the
        # cleaned file keeps both images but drops nothing extra.
        self.assertEqual(sync["images_after"], 2)
        self.assertEqual((self.tmp / "ann.json").read_text(encoding="utf-8"), before)
        self.assertTrue(out.exists())

    def test_coco_entry_matching_removed_file_is_dropped(self):
        # COCO lists the file that will be removed (a_dup.png).
        data = {
            "images": [{"id": 1, "file_name": "a_dup.png"}, {"id": 2, "file_name": "a.png"}],
            "annotations": [{"id": 10, "image_id": 1}, {"id": 11, "image_id": 2}],
            "categories": [],
        }
        coco2 = self.tmp / "ann2.json"
        coco2.write_text(json.dumps(data), encoding="utf-8")
        out = self.tmp / "ann2.cleaned.json"
        clean(self.root, dry_run=False, coco_path=coco2, coco_output=out,
              quarantine_dir=self.tmp / "q")
        cleaned = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual([im["file_name"] for im in cleaned["images"]], ["a.png"])
        self.assertEqual([a["id"] for a in cleaned["annotations"]], [11])

    def test_dry_run_only_plans_coco(self):
        out = self.tmp / "planned.json"
        rep = clean(self.root, dry_run=True, coco_path=self.coco, coco_output=out)
        self.assertIn("planned_output", rep["coco_sync"])
        self.assertFalse(out.exists())


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        src = gradient(self.tmp / "src.png")
        d = self.root / "train"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, d / "a.png")
        shutil.copy(src, d / "b.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_cli_dry_run_writes_report(self):
        report_dir = self.tmp / "report"
        rc = cli_main([str(self.root), "--report-dir", str(report_dir)])
        self.assertEqual(rc, 0)
        self.assertTrue((report_dir / "report.json").exists())
        self.assertTrue((self.root / "train" / "a.png").exists())
        self.assertTrue((self.root / "train" / "b.png").exists())

    def test_cli_apply_quarantines(self):
        qdir = self.tmp / "q"
        rc = cli_main([str(self.root), "--apply", "--quarantine-dir", str(qdir),
                       "--report-dir", str(self.tmp / "report")])
        self.assertEqual(rc, 0)
        self.assertTrue((qdir / "manifest.json").exists())
        remaining = [p for p in (self.root / "train").glob("*.png")]
        self.assertEqual(len(remaining), 1)


if __name__ == "__main__":
    unittest.main()
