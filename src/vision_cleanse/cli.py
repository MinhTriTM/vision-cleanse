"""Command-line interface: ``vision-cleanse``.

Dry-run is the default. Pass ``--apply`` to actually move files
to quarantine. Nothing is ever hard-deleted.
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import clean


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vision-cleanse",
        description="Clean near-duplicates and train/val/test leakage from an image dataset.",
    )
    p.add_argument("root", help="Dataset root containing <split>/ subdirectories")
    p.add_argument("--splits", nargs="+", default=["train", "val", "test"],
                   help="Split names to scan (default: train val test)")
    p.add_argument("--phash-threshold", type=int, default=10,
                   help="Max pHash Hamming distance for a near-duplicate pair (default 10)")
    p.add_argument("--dhash-threshold", type=int, default=10,
                   help="Max dHash Hamming distance for a near-duplicate pair (default 10)")
    p.add_argument("--hash-algo", default="md5", choices=["md5", "sha256"],
                   help="Exact-match hash (default md5)")
    p.add_argument("--apply", action="store_true",
                   help="Actually move files to quarantine (default is dry-run: report only)")
    p.add_argument("--quarantine-dir", default=None,
                   help="Quarantine directory (default: <root>_quarantine)")
    p.add_argument("--report-dir", default="vision_cleanse_report",
                   help="Where report.json and conflict_report.csv go (default ./vision_cleanse_report)")
    p.add_argument("--coco", default=None, help="Optional COCO JSON annotation file to sync")
    p.add_argument("--coco-output", default=None,
                   help="Output path for the cleaned COCO file (default <coco>.cleaned.json)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = clean(
        root=args.root,
        splits=tuple(args.splits),
        phash_threshold=args.phash_threshold,
        dhash_threshold=args.dhash_threshold,
        hash_algo=args.hash_algo,
        dry_run=not args.apply,
        quarantine_dir=args.quarantine_dir,
        report_dir=args.report_dir,
        coco_path=args.coco,
        coco_output=args.coco_output,
    )
    mode = "APPLY (files moved to quarantine)" if args.apply else "DRY-RUN (nothing moved)"
    print(f"[{mode}]")
    print(f"Scanned: {report['images_found']} images "
          f"(splits: {', '.join(report['splits_scanned']) or 'none'})")
    if report["splits_missing"]:
        print(f"Missing splits (skipped): {', '.join(report['splits_missing'])}")
    if report["images_unreadable"]:
        print(f"Unreadable files (skipped): {len(report['images_unreadable'])}")
    print(f"Duplicate groups: {report['duplicate_groups']} "
          f"({report['groups_exact']} exact, {report['groups_near']} near)")
    print(f"To quarantine: {report['to_quarantine']} | Label conflicts (kept, needs review): "
          f"{report['label_conflicts']}")
    print(f"Report: {args.report_dir}/report.json")
    if report["label_conflicts"]:
        print(f"Conflicts: {args.report_dir}/conflict_report.csv")
    if "quarantine_dir" in report:
        print(f"Quarantine: {report['quarantine_dir']} (manifest: {report['manifest']})")
    if "coco_sync" in report:
        print(f"COCO sync: {json.dumps(report['coco_sync'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
