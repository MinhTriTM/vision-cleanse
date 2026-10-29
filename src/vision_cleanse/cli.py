"""Command-line interface: ``vision-cleanse``.

Dry-run is the default. Pass ``--apply`` to actually move files
to quarantine. Nothing is ever hard-deleted.
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import clean
from .i18n import SUPPORTED, normalize_lang, t


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
    p.add_argument("--lang", default="vi", choices=list(SUPPORTED),
                   help="Message language: vi, en, zh (default vi)")
    p.add_argument("--min-size", type=int, default=32,
                   help="Images with longest side below this are flagged tiny (default 32)")
    p.add_argument("--yolo", action="store_true",
                   help="Force YOLO annotation checks on (default: auto-detect .txt labels)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lang = normalize_lang(args.lang)
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
        lang=lang,
        min_size=args.min_size,
        yolo=True if args.yolo else None,
    )
    print(f"[{t('mode_apply' if args.apply else 'mode_dry', lang)}]")
    print(t("scanned", lang, n=report["images_found"])
          + f" (splits: {', '.join(report['splits_scanned']) or 'none'})")
    if report["splits_missing"]:
        print(t("missing_splits", lang, s=", ".join(report["splits_missing"])))
    if report["images_unreadable"]:
        print(t("unreadable", lang, n=len(report["images_unreadable"])))
    print(t("dup_groups", lang, n=report["duplicate_groups"],
            exact=report["groups_exact"], near=report["groups_near"]))
    print(t("to_quarantine", lang, n=report["to_quarantine"])
          + " | " + t("conflicts", lang, n=report["label_conflicts"]))
    print(t("report", lang, p=f"{args.report_dir}/report.json"))
    if report["label_conflicts"]:
        print(t("conflicts_file", lang, p=f"{args.report_dir}/conflict_report.csv"))
    if "quarantine_dir" in report:
        print(t("quarantine_dir", lang, p=report["quarantine_dir"], m=report["manifest"]))
    if "coco_sync" in report:
        print(t("coco_sync", lang, j=json.dumps(report["coco_sync"], ensure_ascii=False)))
    health = report["health"]
    print(f"--- {t('health_title', lang)} ---")
    if health["clean"]:
        print(t("health_ok", lang))
    else:
        c = health["counts"]
        print(t("health_issues", lang, n=c["total"], e=c["errors"], w=c["warnings"]))
        for f in health["findings"][:50]:
            detail = f" ({f['detail']})" if f["detail"] else ""
            print(f"  [{f['severity']}] {t('check_' + f['check'], lang)}: "
                  f"{f['path']}{detail}")
        if len(health["findings"]) > 50:
            print(f"  ... +{len(health['findings']) - 50} more (see report.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
