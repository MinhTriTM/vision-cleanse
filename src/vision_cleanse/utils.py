"""File utilities: discovery, quarantine, reports and annotation sync."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from .extractors import IMAGE_EXTENSIONS


def discover(root: str | Path, splits: list[str]) -> tuple[list[dict], list[str]]:
    root = Path(root)
    records: list[dict] = []
    missing: list[str] = []
    for split in splits:
        split_dir = root / split
        if not split_dir.is_dir():
            missing.append(split)
            continue
        for path in sorted(split_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                if path.parent == split_dir:
                    label = ""
                else:
                    label = path.parent.name
                records.append(
                    {
                        "path": path,
                        "split": split,
                        "label": label,
                        "rel": str(path.relative_to(root)),
                    }
                )
    return records, missing


def yolo_label_path(image_path: str | Path) -> Path:
    """YOLO label file sitting next to the image (same stem, .txt)."""
    p = Path(image_path)
    return p.with_suffix(".txt")


def move_to_quarantine(
    image_path: str | Path,
    root: str | Path,
    quarantine_dir: str | Path,
    move_yolo_label: bool = True,
) -> dict:
    """Move one image (plus its YOLO .txt label, if any) to quarantine.

    The quarantine tree mirrors the path relative to ``root`` so two
    files with the same name in different splits/classes never clash.
    Returns a manifest entry dict.
    """
    root, quarantine_dir = Path(root), Path(quarantine_dir)
    image_path = Path(image_path)
    rel = image_path.relative_to(root)
    dest = quarantine_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(image_path), str(dest))
    moved = [{"from": str(image_path), "to": str(dest)}]
    if move_yolo_label:
        label_src = yolo_label_path(image_path)
        if label_src.is_file():
            label_dest = dest.with_suffix(".txt")
            shutil.move(str(label_src), str(label_dest))
            moved.append({"from": str(label_src), "to": str(label_dest)})
    return {"image": str(image_path), "quarantined_to": str(dest), "moved": moved}


def write_manifest(quarantine_dir: str | Path, entries: list[dict]) -> Path:
    """Write ``manifest.json`` listing every quarantined file."""
    quarantine_dir = Path(quarantine_dir)
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    out = quarantine_dir / "manifest.json"
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_conflict_report(report_dir: str | Path, conflicts: list[dict]) -> Path:
    """Write ``conflict_report.csv``: one row per label-conflict group.

    Nothing in a conflict group is ever auto-deleted; a human reviews
    this file instead.
    """
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / "conflict_report.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group_id", "method", "labels", "splits", "files"])
        for c in conflicts:
            w.writerow(
                [
                    c["group_id"],
                    c["method"],
                    ";".join(sorted(c["labels"])),
                    ";".join(sorted(c["splits"])),
                    ";".join(c["files"]),
                ]
            )
    return out


def write_json_report(report_dir: str | Path, report: dict) -> Path:
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    out = report_dir / "report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def sync_coco(coco_path: str | Path, removed_image_paths: list[str | Path], output_path: str | Path) -> dict:
    """Return a COCO dict with removed images (and their annotations) dropped.

    ``removed_image_paths`` are matched against COCO ``file_name``
    by basename, because COCO files usually store bare filenames.
    The original file is never overwritten: the cleaned copy goes to
    ``output_path``.
    """
    coco = json.loads(Path(coco_path).read_text(encoding="utf-8"))
    removed_names = {Path(p).name for p in removed_image_paths}
    kept_images = [im for im in coco.get("images", []) if im.get("file_name") not in removed_names]
    kept_ids = {im["id"] for im in kept_images}
    kept_anns = [a for a in coco.get("annotations", []) if a.get("image_id") in kept_ids]
    cleaned = dict(coco)
    cleaned["images"] = kept_images
    cleaned["annotations"] = kept_anns
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "images_before": len(coco.get("images", [])),
        "images_after": len(kept_images),
        "annotations_before": len(coco.get("annotations", [])),
        "annotations_after": len(kept_anns),
        "output": str(output_path),
    }
