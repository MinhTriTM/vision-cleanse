"""Near-duplicate benchmark (Phase 1).

Generates 100 textured base images and 4 variants each (resize 50%,
resize 200%, JPEG quality 30, JPEG quality 95) = 500 images, then
measures how well ring 1+2 grouping recovers the known ground truth.

Ground truth: images sharing a base id are duplicates.
Metrics: precision, recall, F1 over pairs, per-transform recall, and
timing for extraction + grouping. The script exits 0 unless it
crashes; metric values are reported, not gated, because CI treats
this job as informational until thresholds are calibrated on larger
data.

Run: python benchmarks/benchmark_near_dup.py
Output: benchmarks/results_near_dup.json + printed table.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "src"))

from helpers import photo_like

from vision_cleanse.extractors import dhash, file_hash, phash
from vision_cleanse.matchers import group_duplicates

N_BASES = 100
PHASH_THRESHOLD = 10
DHASH_THRESHOLD = 10


def build_images(workdir: Path) -> list[dict]:
    items = []
    for i in range(N_BASES):
        base = workdir / f"base_{i:03d}.png"
        photo_like(base, seed=i)
        items.append({"path": base, "base": i, "transform": "base"})
        im = Image.open(base)
        small = workdir / f"base_{i:03d}_small.png"
        im.resize((128, 128)).save(small)
        items.append({"path": small, "base": i, "transform": "small"})
        large = workdir / f"base_{i:03d}_large.png"
        im.resize((512, 512)).save(large)
        items.append({"path": large, "base": i, "transform": "large"})
        jpg30 = workdir / f"base_{i:03d}_jpg30.jpg"
        im.save(jpg30, quality=30)
        items.append({"path": jpg30, "base": i, "transform": "jpg30"})
        jpg95 = workdir / f"base_{i:03d}_jpg95.jpg"
        im.save(jpg95, quality=95)
        items.append({"path": jpg95, "base": i, "transform": "jpg95"})
    return items


def pairs_from_groups(groups: list[dict]) -> set:
    out = set()
    for g in groups:
        mem = g["members"]
        for a in range(len(mem)):
            for b in range(a + 1, len(mem)):
                out.add((mem[a], mem[b]))
    return out


def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="vcbench_"))
    try:
        items = build_images(workdir)
        t0 = time.perf_counter()
        recs = []
        for it in items:
            p = it["path"]
            recs.append(
                {
                    "path": p,
                    "md5": file_hash(p),
                    "phash": phash(p),
                    "dhash": dhash(p),
                }
            )
        t_extract = time.perf_counter() - t0
        t1 = time.perf_counter()
        groups = group_duplicates(recs, PHASH_THRESHOLD, DHASH_THRESHOLD)
        t_group = time.perf_counter() - t1

        # Ground-truth pairs: same base id.
        by_base: dict[int, list[int]] = {}
        for idx, it in enumerate(items):
            by_base.setdefault(it["base"], []).append(idx)
        truth = set()
        for mem in by_base.values():
            for a in range(len(mem)):
                for b in range(a + 1, len(mem)):
                    truth.add((mem[a], mem[b]))
        pred = pairs_from_groups(groups)
        tp = len(pred & truth)
        fp = len(pred - truth)
        fn = len(truth - pred)
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

        # Per-transform recall: variant grouped together with its base.
        group_of: dict[int, set[int]] = {}
        for g in groups:
            members = set(g["members"])
            for idx in members:
                group_of[idx] = members
        per_transform: dict[str, dict] = {}
        for tr in ("small", "large", "jpg30", "jpg95"):
            variants = [idx for idx, it in enumerate(items) if it["transform"] == tr]
            base_idx = {it["base"]: idx for idx, it in enumerate(items) if it["transform"] == "base"}
            hit = sum(
                1
                for idx in variants
                if base_idx[items[idx]["base"]] in group_of.get(idx, set())
            )
            per_transform[tr] = {"n": len(variants), "hit": hit, "recall": hit / len(variants)}

        results = {
            "date": date.today().isoformat(),
            "version": "0.2.0",
            "n_bases": N_BASES,
            "n_images": len(items),
            "phash_threshold": PHASH_THRESHOLD,
            "dhash_threshold": DHASH_THRESHOLD,
            "groups_found": len(groups),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "per_transform_recall": per_transform,
            "timing_s": {
                "extract": round(t_extract, 2),
                "group": round(t_group, 2),
                "total": round(t_extract + t_group, 2),
            },
        }
        out = Path(__file__).resolve().parent / "results_near_dup.json"
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Images: {len(items)} ({N_BASES} bases x 5)")
        print(f"Groups found: {len(groups)}")
        print(f"Precision: {precision:.4f}  Recall: {recall:.4f}  F1: {f1:.4f}")
        print(f"TP={tp} FP={fp} FN={fn}")
        for tr, r in per_transform.items():
            print(f"  recall[{tr}]: {r['hit']}/{r['n']} = {r['recall']:.4f}")
        print(f"Timing: extract {t_extract:.2f}s, group {t_group:.2f}s")
        print(f"Results: {out}")
        return 0
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
