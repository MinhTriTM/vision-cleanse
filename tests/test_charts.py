"""Tests for chart exports (skipped when weasyprint/pdftoppm is missing)."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import photo_like

from vision_cleanse import clean
from vision_cleanse.charts import (
    ChartsUnavailableError,
    _render,
    classify_duplicate_groups,
    generate_charts,
)

HAS_WEASY = (importlib.util.find_spec("weasyprint") is not None
             and shutil.which("pdftoppm") is not None)


def _classic_dataset(root: Path) -> None:
    for cls, seed in (("cat", 11), ("dog", 12)):
        (root / "train" / cls).mkdir(parents=True)
        (root / "val" / cls).mkdir(parents=True)
        photo_like(root / "train" / cls / "a.jpg", seed=seed)
        photo_like(root / "val" / cls / "a.jpg", seed=seed + 100)


@unittest.skipUnless(HAS_WEASY, "weasyprint/pdftoppm not installed")
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


@unittest.skipUnless(HAS_WEASY, "weasyprint/pdftoppm not installed")
class TestClassChartFallback(unittest.TestCase):
    """Over-30-class datasets fold into top 30 + "other", not a skip."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_stacked_folds_top30_plus_other(self):
        root = self.tmp / "many"
        seed = 100
        for split in ("train", "val"):
            for i in range(35):
                d = root / split / f"cls{i:02d}"
                d.mkdir(parents=True)
                photo_like(d / "a.jpg", seed=seed)
                seed += 1
        charts_dir = self.tmp / "mcharts"
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        made = report["charts"]["generated"]
        skipped = {s["chart"] for s in report["charts"]["skipped"]}
        self.assertIn("class_split_stacked.png", made)
        self.assertNotIn("class_split_stacked.png", skipped)
        self.assertTrue((charts_dir / "class_split_stacked.png").read_bytes().startswith(b"\x89PNG"))

    def test_heatmap_folds_top30_plus_other(self):
        root = self.tmp / "ymany"
        root.mkdir(parents=True)
        names = "\n".join(f"  - c{i}" for i in range(35))
        (root / "data.yaml").write_text(f"names:\n{names}\n", encoding="utf-8")
        seed = 500
        for split in ("train", "val"):
            (root / "images" / split).mkdir(parents=True)
            (root / "labels" / split).mkdir(parents=True)
            for i in range(35):
                photo_like(root / "images" / split / f"a{i:02d}.jpg", seed=seed)
                seed += 1
                (root / "labels" / split / f"a{i:02d}.txt").write_text(
                    f"{i} 0.5 0.5 0.2 0.2\n", encoding="utf-8"
                )
        charts_dir = self.tmp / "ymcharts"
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        made = report["charts"]["generated"]
        skipped = {s["chart"] for s in report["charts"]["skipped"]}
        self.assertIn("class_split_heatmap.png", made)
        self.assertNotIn("class_split_heatmap.png", skipped)
        self.assertTrue((charts_dir / "class_split_heatmap.png").read_bytes().startswith(b"\x89PNG"))


class TestChartsMissingEngine(unittest.TestCase):
    def test_clear_error_without_weasyprint(self):
        outdir = Path(tempfile.mkdtemp())
        with mock.patch.dict(sys.modules, {"weasyprint": None}), \
                self.assertRaises(ChartsUnavailableError):
            _render(outdir, "x.png", "T", "S", "<svg/>", "F")

    def test_generate_charts_without_weasyprint(self):
        # One usable record forces a real chart render (split_sizes).
        report = {"splits_scanned": ["train"], "health": {"class_distribution": {},
                  "findings": [], "counts": {"errors": 0, "warnings": 0, "info": 0,
                                             "total": 0}},
                  "groups_exact": 0, "groups_near": 0, "removals": [],
                  "layout": {"names": None}}
        records = [{"split": "train", "md5": "x", "size": 100,
                    "width": 64, "height": 64, "path": "a.jpg"}]
        with mock.patch.dict(sys.modules, {"weasyprint": None}), \
                self.assertRaises(ChartsUnavailableError):
            generate_charts(report, records, Path(tempfile.mkdtemp()))


class TestVennClassification(unittest.TestCase):
    def _group(self, *splits):
        return {"group_id": 0, "method": "exact",
                "members": [{"path": f"{s}.jpg", "split": s} for s in splits]}

    def test_single_split_group(self):
        counts = classify_duplicate_groups([self._group("train", "train")])
        self.assertEqual(counts["train"], 1)
        self.assertEqual(counts["train+val"], 0)

    def test_pair_group(self):
        counts = classify_duplicate_groups([self._group("train", "val")])
        self.assertEqual(counts["train+val"], 1)
        self.assertEqual(counts["train"], 0)

    def test_triple_group(self):
        counts = classify_duplicate_groups(
            [self._group("train", "val", "test")])
        self.assertEqual(counts["train+val+test"], 1)

    def test_split_aliases(self):
        counts = classify_duplicate_groups(
            [self._group("training", "validation")])
        self.assertEqual(counts["train+val"], 1)

    def test_empty_and_unknown_splits(self):
        counts = classify_duplicate_groups([])
        self.assertTrue(all(v == 0 for v in counts.values()))
        self.assertEqual(len(counts), 7)
        counts = classify_duplicate_groups([self._group("other")])
        self.assertTrue(all(v == 0 for v in counts.values()))


@unittest.skipUnless(HAS_WEASY, "weasyprint/pdftoppm not installed")
class TestDuplicateGroupsDetail(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _yolo_root(self, root: Path) -> None:
        (root / "images" / "train").mkdir(parents=True)
        (root / "images" / "val").mkdir(parents=True)
        (root / "labels" / "train").mkdir(parents=True)
        (root / "labels" / "val").mkdir(parents=True)
        photo_like(root / "images" / "train" / "a.jpg", seed=31)
        shutil.copy(root / "images" / "train" / "a.jpg",
                     root / "images" / "val" / "a.jpg")
        (root / "labels" / "train" / "a.txt").write_text(
            "0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        (root / "labels" / "val" / "a.txt").write_text(
            "0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        (root / "data.yaml").write_text("names:\n  - cat\n", encoding="utf-8")

    def test_detail_members_are_kept_plus_removed(self):
        root = self.tmp / "ds"
        self._yolo_root(root)
        report = clean(root, charts_dir=self.tmp / "charts", report_dir=None)
        self.assertEqual(report["duplicate_groups"], 1)
        detail = report["duplicate_groups_detail"]
        self.assertEqual(len(detail), 1)
        group = report["groups"][0]
        member_paths = {m["path"] for m in detail[0]["members"]}
        self.assertEqual(member_paths, set(group["kept"]) | set(group["removed"]))
        member_splits = {m["split"] for m in detail[0]["members"]}
        self.assertEqual(member_splits, {"train", "val"})
        self.assertIn("duplicate_groups_venn.png",
                      report["charts"]["generated"])
        venn = (self.tmp / "charts" / "duplicate_groups_venn.png").read_bytes()
        self.assertTrue(venn.startswith(b"\x89PNG"))

    def test_venn_skipped_without_duplicate_groups(self):
        root = self.tmp / "ds2"
        (root / "images" / "train").mkdir(parents=True)
        photo_like(root / "images" / "train" / "a.jpg", seed=41)
        report = clean(root, charts_dir=self.tmp / "charts2", report_dir=None)
        self.assertEqual(report["duplicate_groups_detail"], [])
        skipped = {s["chart"]: s["reason"] for s in report["charts"]["skipped"]}
        self.assertEqual(skipped.get("duplicate_groups_venn.png"),
                         "no duplicate groups")


@unittest.skipUnless(HAS_WEASY, "weasyprint/pdftoppm not installed")
class TestDirtyHealthCharts(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_health_charts_render_from_real_findings(self):
        root = self.tmp / "dirty"
        (root / "images" / "train").mkdir(parents=True)
        (root / "labels" / "train").mkdir(parents=True)
        photo_like(root / "images" / "train" / "good.jpg", seed=51)
        (root / "labels" / "train" / "good.txt").write_text(
            "0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        # Image without a label -> missing_label.
        photo_like(root / "images" / "train" / "nolabel.jpg", seed=52)
        # Label without an image -> orphan_label.
        (root / "labels" / "train" / "ghost.txt").write_text(
            "0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
        # Empty label file -> empty_label.
        (root / "labels" / "train" / "empty.txt").write_text("", encoding="utf-8")
        # Malformed row -> invalid_label.
        (root / "labels" / "train" / "bad.txt").write_text(
            "0 0.5 0.5\n", encoding="utf-8")
        # Zero-byte image -> zero_byte.
        (root / "images" / "train" / "zero.jpg").write_bytes(b"")
        (root / "data.yaml").write_text("names:\n  - cat\n", encoding="utf-8")
        charts_dir = self.tmp / "charts"
        report = clean(root, charts_dir=charts_dir, report_dir=None)
        self.assertGreater(len(report["health"]["findings"]), 0)
        made = report["charts"]["generated"]
        for name in ("health_by_check.png", "health_by_severity.png"):
            self.assertIn(name, made)
            self.assertTrue((charts_dir / name).read_bytes().startswith(b"\x89PNG"),
                            name)
