"""Tests for chart exports (skipped when matplotlib is missing)."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import photo_like

from vision_cleanse import clean
from vision_cleanse.charts import ChartsUnavailableError, generate_charts

HAS_MPL = importlib.util.find_spec("matplotlib") is not None


def _classic_dataset(root: Path) -> None:
    for cls, seed in (("cat", 11), ("dog", 12)):
        (root / "train" / cls).mkdir(parents=True)
        (root / "val" / cls).mkdir(parents=True)
        photo_like(root / "train" / cls / "a.jpg", seed=seed)
        photo_like(root / "val" / cls / "a.jpg", seed=seed + 100)


@unittest.skipUnless(HAS_MPL, "matplotlib not installed")
class TestCharts(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_classic_dataset_charts(self):
        root = self.tmp / "ds"
        _classic_dataset(root)
        charts_dir = self.tmp / "charts"
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        made = report["charts"]["generated"]
        self.assertIn("split_sizes.png", made)
        self.assertIn("class_images.png", made)
        self.assertIn("width_hist.png", made)
        # No YOLO boxes in classic layout: box charts must be skipped, not faked.
        skipped = {s["chart"] for s in report["charts"]["skipped"]}
        self.assertIn("boxes_per_class.png", skipped)
        for name in made:
            data = (charts_dir / name).read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG"), name)

    def test_yolo_dataset_box_charts(self):
        root = self.tmp / "yds"
        (root / "images" / "train").mkdir(parents=True)
        photo_like(root / "images" / "train" / "a.jpg", seed=21)
        photo_like(root / "images" / "train" / "b.jpg", seed=22)
        (root / "labels" / "train").mkdir(parents=True)
        (root / "labels" / "train" / "a.txt").write_text(
            "0 0.3 0.3 0.2 0.2\n1 0.7 0.6 0.3 0.3\n", encoding="utf-8"
        )
        (root / "labels" / "train" / "b.txt").write_text(
            "0 0.5 0.5 0.4 0.4\n", encoding="utf-8"
        )
        (root / "data.yaml").write_text(
            "names:\n  - cat\n  - dog\n", encoding="utf-8"
        )
        charts_dir = self.tmp / "ycharts"
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        made = report["charts"]["generated"]
        for name in ("boxes_per_class.png", "box_centers_scatter.png",
                     "box_centers_heatmap.png", "instances_per_image.png"):
            self.assertIn(name, made)
            self.assertTrue((charts_dir / name).read_bytes().startswith(b"\x89PNG"), name)


class TestChartsMissingMatplotlib(unittest.TestCase):
    def test_clear_error_without_matplotlib(self):
        report = {"splits_scanned": ["train"], "health": {"class_distribution": {},
                  "findings": [], "counts": {"errors": 0, "warnings": 0, "info": 0}},
                  "groups_exact": 0, "groups_near": 0, "removals": [],
                  "layout": {"names": None}}
        with mock.patch.dict(sys.modules, {"matplotlib": None, "matplotlib.pyplot": None}), \
                self.assertRaises(ChartsUnavailableError):
            generate_charts(report, [], Path(tempfile.mkdtemp()))
