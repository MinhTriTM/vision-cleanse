"""Tests for YOLO dataset layout: images/<split>/ + labels/<split>/ + data.yaml."""

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import photo_like

from vision_cleanse import clean
from vision_cleanse.utils import parse_data_yaml


def _label(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


class TestDataYaml(unittest.TestCase):
    def _parse(self, text: str) -> dict:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        p = tmp / "data.yaml"
        p.write_text(text, encoding="utf-8")
        return parse_data_yaml(p)

    def test_block_names(self):
        out = self._parse(
            "train: images/train\nval: images/val\nnc: 2\n"
            "names:\n  - cat\n  - dog\n"
        )
        self.assertEqual(out["names"], ["cat", "dog"])
        self.assertEqual(out["nc"], 2)
        self.assertEqual(out["split_paths"]["train"], "images/train")

    def test_inline_names_and_quotes(self):
        out = self._parse("names: ['cat', \"dog\"]  # comment\n")
        self.assertEqual(out["names"], ["cat", "dog"])

    def test_malformed_never_raises(self):
        out = self._parse("this is not: [valid yaml\nnames: [\n")
        self.assertIsNone(out["names"])
        self.assertEqual(out["split_paths"], {})


def _yolo_dataset(root: Path) -> None:
    """train: a (cat), b (dog), nolabel; val: a (dog, same pixels as train a)."""
    (root / "images" / "train").mkdir(parents=True)
    (root / "images" / "val").mkdir(parents=True)
    photo_like(root / "images" / "train" / "a.jpg", seed=1)
    photo_like(root / "images" / "train" / "b.jpg", seed=2)
    photo_like(root / "images" / "train" / "nolabel.jpg", seed=3)
    shutil.copy(
        root / "images" / "train" / "a.jpg", root / "images" / "val" / "a.jpg"
    )
    _label(root / "labels" / "train" / "a.txt", ["0 0.5 0.5 0.2 0.3"])
    _label(root / "labels" / "train" / "b.txt", ["1 0.5 0.5 0.4 0.4"])
    _label(root / "labels" / "train" / "orphan.txt", ["0 0.5 0.5 0.2 0.2"])
    _label(root / "labels" / "val" / "a.txt", ["1 0.5 0.5 0.2 0.3"])
    (root / "data.yaml").write_text(
        "train: images/train\nval: images/val\nnc: 2\nnames:\n  - cat\n  - dog\n",
        encoding="utf-8",
    )


class TestYoloLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "ds"
        _yolo_dataset(self.root)

    def test_detection_and_class_names(self):
        report = clean(self.root)
        self.assertEqual(report["layout"]["mode"], "yolo")
        self.assertEqual(report["layout"]["names"], ["cat", "dog"])
        self.assertEqual(report["images_found"], 4)
        self.assertEqual(report["splits_scanned"], ["train", "val"])
        dist = report["health"]["class_distribution"]
        self.assertEqual(dist["train"]["cat"], 1)
        self.assertEqual(dist["train"]["dog"], 1)
        self.assertEqual(dist["val"]["dog"], 1)

    def test_missing_and_orphan_labels(self):
        report = clean(self.root)
        checks = {(f["check"], Path(f["path"]).name) for f in report["health"]["findings"]}
        self.assertIn(("missing_label", "nolabel.jpg"), checks)
        self.assertIn(("orphan_label", "orphan.txt"), checks)

    def test_conflict_across_class_ids(self):
        report = clean(self.root)
        # Same pixels in train (cat) and val (dog): conflict, nothing removed.
        self.assertEqual(report["label_conflicts"], 1)
        self.assertEqual(report["to_quarantine"], 0)

    def test_apply_moves_image_and_label_tree(self):
        root = self.tmp / "ds2"
        (root / "images" / "train").mkdir(parents=True)
        (root / "images" / "val").mkdir(parents=True)
        photo_like(root / "images" / "train" / "dup.jpg", seed=7)
        photo_like(root / "images" / "val" / "dup.jpg", seed=7)
        shutil.copy(
            root / "images" / "train" / "dup.jpg", root / "images" / "val" / "dup.jpg"
        )
        _label(root / "labels" / "train" / "dup.txt", ["0 0.5 0.5 0.2 0.2"])
        _label(root / "labels" / "val" / "dup.txt", ["0 0.5 0.5 0.2 0.2"])
        qdir = self.tmp / "q"
        report = clean(root, dry_run=False, quarantine_dir=qdir, report_dir=None)
        self.assertEqual(report["to_quarantine"], 1)
        # Train copy removed (lower priority); its label went with it,
        # mirrored under the labels tree, not next to the image.
        self.assertFalse((root / "images" / "train" / "dup.jpg").exists())
        self.assertFalse((root / "labels" / "train" / "dup.txt").exists())
        self.assertTrue((qdir / "images" / "train" / "dup.jpg").exists())
        self.assertTrue((qdir / "labels" / "train" / "dup.txt").exists())
        self.assertTrue((root / "images" / "val" / "dup.jpg").exists())
