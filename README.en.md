# VisionCleanse

![VisionCleanse hero illustration — messy photos inspected for duplicates, then organized into folders with duplicates quarantined](docs/assets/illustrations/hero_banner.png)

[![CI](https://github.com/MinhTriTM/vision-cleanse/actions/workflows/ci.yml/badge.svg)](https://github.com/MinhTriTM/vision-cleanse/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Current version: **0.2.0**. ([Tiếng Việt](README.md) · [中文](README.zh.md))

Clean computer vision datasets: detect near-duplicates and prevent
data leakage between Train / Val / Test.

## What it does

- **Ring 1 — Exact match:** MD5 (or SHA-256) for byte-identical copies.
- **Ring 2 — Perceptual hash:** pHash and dHash implemented with Pillow +
  numpy (no `imagehash` dependency). Catches resize, format change and
  JPEG re-encode. Does not catch deep crop or rotation — those need
  later rings.
- **Split logic:** keep priority `test > val > train`. Within one split,
  keep the highest resolution, then the largest file, then the
  lexicographically smallest path (deterministic: re-runs agree).
- **Label conflicts:** the same (or near-identical) image under two
  classes is **never auto-deleted** — it goes to `conflict_report.csv`
  for human review.
- **Deletion safety:** **dry-run by default** (report only). With
  `--apply`, removed files are **moved to a quarantine folder**
  (mirroring the dataset layout) with `manifest.json`, never deleted.
- **Annotation sync:** a YOLO `.txt` label next to an image moves with
  it into quarantine. A COCO JSON file (with `--coco`) is exported as
  a cleaned copy; the original is never overwritten.
- **Dataset health checks (0.2.0):** beyond duplicates, checks for
  0-byte files, corrupt files, blank/solid-color images, tiny images,
  unexpected files inside split dirs, images missing YOLO labels,
  orphan/malformed/empty YOLO labels, same filename with different
  content, and duplicates inside the test set. YOLO checks auto-enable
  when `.txt` labels are found (or force with `--yolo`).
- **Three languages (0.2.0):** CLI messages and check names in
  Vietnamese, English and Chinese via `--lang vi|en|zh` (default
  `vi`). Keys in `report.json` always stay in English for machines.

## What "clean dataset" means

When the report says `"clean": true`, it means **every enabled check
passed** (no errors, no warnings). That is not an absolute guarantee:
near-duplicate detection is fuzzy by nature and no checker catches
semantic label mistakes. The report lists every check that ran, so the
verdict is auditable.

## Install

```bash
pip install -e .
```

Only Pillow and numpy are required. Tests use stdlib `unittest`,
no pytest needed:

```bash
python -m unittest discover -s tests -v
```

(Without installing, run with `PYTHONPATH=src`.)

## Command line

```bash
# Preview (dry-run, default): nothing moves
vision-cleanse /path/to/dataset

# Really quarantine duplicates
vision-cleanse /path/to/dataset --apply

# English messages, YOLO checks forced on
vision-cleanse /path/to/dataset --apply --lang en --yolo

# With COCO sync
vision-cleanse /path/to/dataset --apply --coco /path/to/annotations.json
```

Expected dataset layout:

```
dataset/
  train/<class>/a.jpg   # or train/a.jpg (no class subdirs)
  val/<class>/b.jpg
  test/<class>/c.jpg
```

YOLO layout (Ultralytics standard) — the expected structure:

```
dataset_root/
  images/train/img1.jpg
  images/train/img2.jpg
  images/val/img3.jpg
  labels/train/img1.txt
  labels/train/img2.txt
  labels/val/img3.txt
  data.yaml   # train: images/train, val: images/val, names: [cat, dog]
```

The `test` split is optional: a train/val-only dataset runs with
full functionality, and without test the keep priority is
`val > train`.

Missing splits are skipped with a warning. Reports go to
`vision_cleanse_report/report.json` and (on label conflicts)
`vision_cleanse_report/conflict_report.csv`.

## Python API

```python
from vision_cleanse import clean

report = clean("/path/to/dataset", dry_run=True)
print(report["duplicate_groups"], report["to_quarantine"])

# Really run it
report = clean("/path/to/dataset", dry_run=False,
               quarantine_dir="/path/to/quarantine")
```

## Supported layouts

Two layouts are auto-detected:

- **Classic:** `train/<class>/a.jpg` (or `train/a.jpg`), YOLO `.txt`
  labels next to the images.
- **YOLO:** `images/train/a.jpg` + `labels/train/a.txt` + `data.yaml`
  (class names from `names` in `data.yaml`). In this mode, label
  files are quarantined under their own `labels/` tree.

## Charts

```bash
pip install vision-cleanse[charts]
vision-cleanse /path/to/dataset --charts
```

Exports 24 PNG charts to `<report-dir>/charts` (see `docs/charts.md`):
split/class overviews, file-size, width, height, aspect and area
distributions; with YOLO labels: boxes per image/class, box w/h/area
distributions, box-center scatter and heatmap, class × split heatmap;
and cleaning results: duplicate groups by method, removals by split
and reason, health findings by check and severity, kept vs
quarantined. Charts without data are skipped and listed with a
reason in `report.json` (no fake empty plots).

Sample charts (see all 22 in `docs/charts.md`):

![Images per split](docs/assets/charts/split_sizes.png)

![Box center heatmap](docs/assets/charts/box_centers_heatmap.png)

![Kept vs quarantined per split](docs/assets/charts/kept_vs_quarantined.png)

## Thresholds

A pair counts as a near-duplicate when pHash **or** dHash is within
threshold (default 10 on 64-bit hashes). The two hashes complement
each other: dHash reads horizontal gradient signs and stays stable
under JPEG noise (measured distance 0 even at JPEG quality 30,
including smooth images where pHash drifts to 16), while pHash reads
global low-frequency structure and catches changes dHash is blind to
(dHash only compares left-right neighbours). The OR rule favors
recall; because files are only quarantined with a report, never
silently deleted, users can still review. Tune with
`--phash-threshold` / `--dhash-threshold` after measuring on your data.

## Limitations (stated plainly)

- Deep crop, rotation, flip and strong color shifts are not caught
  yet — they need deep-feature and geometric-verification rings.
- Near-duplicate grouping is pairwise O(n²). For very large datasets,
  scan per split first or wait for the FAISS ring.
- No "100% clean" promise: near-duplicates are fuzzy. Measure
  precision/recall on self-generated variants before trusting the
  default thresholds.
- Unreadable files are skipped and listed in `images_unreadable`,
  never crashing the pipeline.
