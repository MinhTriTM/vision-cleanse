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

    def test_dict_names_block(self):
        out = self._parse(
            "train: images/train\nval: images/val\nnc: 2\n"
            "names:\n  0: cat\n  1: dog\n"
        )
        self.assertEqual(out["names"], ["cat", "dog"])

    def test_dict_names_inline(self):
        out = self._parse("names: {0: cat, 1: dog}\n")
        self.assertEqual(out["names"], ["cat", "dog"])

    def test_path_key(self):
        out = self._parse("path: sub\ntrain: images/train\nval: images/val\n")
        self.assertEqual(out["path"], "sub")
        self.assertEqual(out["split_paths"]["train"], "images/train")


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


def _expected_tree(root: Path) -> None:
    """The exact expected tree: train/img1, train/img2, val/img3.

    dataset_root/
      images/train/img1.jpg, img2.jpg
      images/val/img3.jpg
      labels/train/img1.txt, img2.txt
      labels/val/img3.txt
      data.yaml (train/val only -- no test split at all)
    """
    (root / "images" / "train").mkdir(parents=True)
    (root / "images" / "val").mkdir(parents=True)
    photo_like(root / "images" / "train" / "img1.jpg", seed=11)
    photo_like(root / "images" / "train" / "img2.jpg", seed=12)
    photo_like(root / "images" / "val" / "img3.jpg", seed=13)
    _label(root / "labels" / "train" / "img1.txt", ["0 0.5 0.5 0.2 0.3"])
    _label(root / "labels" / "train" / "img2.txt", ["1 0.5 0.5 0.4 0.4"])
    _label(root / "labels" / "val" / "img3.txt", ["1 0.5 0.5 0.3 0.3"])
    (root / "data.yaml").write_text(
        "train: images/train\nval: images/val\nnc: 2\nnames:\n  - cat\n  - dog\n",
        encoding="utf-8",
    )


class TestExpectedTreeTrainValOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "dataset_root"
        _expected_tree(self.root)

    def test_exact_tree_end_to_end(self):
        report = clean(self.root)
        self.assertEqual(report["layout"]["mode"], "yolo")
        self.assertEqual(report["layout"]["names"], ["cat", "dog"])
        self.assertEqual(report["images_found"], 3)
        # No test split exists: it is reported missing (informational)
        # but never an error, and nothing is skipped or lost.
        self.assertEqual(report["splits_scanned"], ["train", "val"])
        self.assertEqual(report["splits_missing"], ["test"])
        self.assertTrue(report["clean"])
        self.assertEqual(report["health"]["findings"], [])
        self.assertEqual(report["duplicate_groups"], 0)
        dist = report["health"]["class_distribution"]
        self.assertEqual(dist["train"], {"cat": 1, "dog": 1})
        self.assertEqual(dist["val"], {"dog": 1})

    def test_val_kept_over_train_without_test(self):
        # val copy of a train image (same class): without any test
        # split, val outranks train, so the train copy is removed.
        shutil.copy(
            self.root / "images" / "train" / "img1.jpg",
            self.root / "images" / "val" / "img3.jpg",
        )
        _label(self.root / "labels" / "val" / "img3.txt", ["0 0.5 0.5 0.2 0.3"])
        report = clean(self.root)
        self.assertEqual(report["duplicate_groups"], 1)
        self.assertEqual(report["to_quarantine"], 1)
        self.assertEqual(report["removals"][0]["path"],
                         str(self.root / "images" / "train" / "img1.jpg"))
        self.assertEqual(report["removals"][0]["reason"],
                         "duplicate_in_lower_priority_split")
        self.assertEqual(report["groups"][0]["kept"],
                         [str(self.root / "images" / "val" / "img3.jpg")])

    def test_apply_quarantine_mirrors_expected_tree(self):
        shutil.copy(
            self.root / "images" / "train" / "img1.jpg",
            self.root / "images" / "val" / "img3.jpg",
        )
        _label(self.root / "labels" / "val" / "img3.txt", ["0 0.5 0.5 0.2 0.3"])
        qdir = self.tmp / "q"
        report = clean(self.root, dry_run=False, quarantine_dir=qdir, report_dir=None)
        self.assertEqual(report["to_quarantine"], 1)
        self.assertFalse((self.root / "images" / "train" / "img1.jpg").exists())
        self.assertFalse((self.root / "labels" / "train" / "img1.txt").exists())
        self.assertTrue((qdir / "images" / "train" / "img1.jpg").exists())
        self.assertTrue((qdir / "labels" / "train" / "img1.txt").exists())
        self.assertTrue((qdir / "manifest.json").exists())
        self.assertTrue((self.root / "images" / "val" / "img3.jpg").exists())
        self.assertTrue((self.root / "labels" / "val" / "img3.txt").exists())

    def test_dot_slash_and_trailing_slash_paths(self):
        (self.root / "data.yaml").write_text(
            "train: ./images/train\nval: images/val/\nnc: 2\n"
            "names:\n  - cat\n  - dog\n",
            encoding="utf-8",
        )
        report = clean(self.root)
        self.assertEqual(report["layout"]["mode"], "yolo")
        self.assertEqual(report["images_found"], 3)
        self.assertEqual(report["splits_scanned"], ["train", "val"])

    def test_path_key_resolves_under_subdir(self):
        sub = self.tmp / "root2" / "sub"
        _expected_tree(sub)
        (self.tmp / "root2" / "data.yaml").write_text(
            "path: sub\ntrain: images/train\nval: images/val\nnc: 2\n"
            "names:\n  0: cat\n  1: dog\n",
            encoding="utf-8",
        )
        (sub / "data.yaml").unlink()
        report = clean(self.tmp / "root2")
        self.assertEqual(report["layout"]["mode"], "yolo")
        self.assertEqual(report["layout"]["names"], ["cat", "dog"])
        self.assertEqual(report["images_found"], 3)
        self.assertEqual(report["splits_scanned"], ["train", "val"])
        dist = report["health"]["class_distribution"]
        self.assertEqual(dist["train"], {"cat": 1, "dog": 1})

    def test_path_key_missing_falls_back(self):
        (self.root / "data.yaml").write_text(
            "path: nowhere\ntrain: images/train\nval: images/val\nnc: 2\n"
            "names:\n  - cat\n  - dog\n",
            encoding="utf-8",
        )
        report = clean(self.root)
        self.assertEqual(report["layout"]["mode"], "yolo")
        self.assertEqual(report["images_found"], 3)
