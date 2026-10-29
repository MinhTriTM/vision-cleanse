"""File utilities: discovery, quarantine, reports and annotation sync."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from .extractors import IMAGE_EXTENSIONS


def _strip_yaml_comment(line: str) -> str:
    """Remove a trailing ``#`` comment that sits outside quotes."""
    in_single, in_double = False, False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def parse_data_yaml(path: str | Path) -> dict:
    """Parse the small subset of a YOLO ``data.yaml`` that we need.

    Returns ``{"names": list[str] | None, "nc": int | None,
    "split_paths": {split: str}}`` for ``train``/``val``/``test``
    entries. Everything else is ignored, and malformed input never
    raises: it just yields whatever could be parsed.
    """
    names: list[str] | None = None
    nc: int | None = None
    split_paths: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {"names": None, "nc": None, "split_paths": {}}
    i = 0
    while i < len(lines):
        raw = _strip_yaml_comment(lines[i]).rstrip()
        i += 1
        if not raw.strip():
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key, val = key.strip(), val.strip()
        if key == "names":
            if val.startswith("[") and val.endswith("]"):
                names = [_unquote(v) for v in val[1:-1].split(",") if v.strip()]
            else:
                items = []
                while i < len(lines):
                    item = _strip_yaml_comment(lines[i]).strip()
                    if item.startswith("- "):
                        items.append(_unquote(item[2:]))
                        i += 1
                    else:
                        break
                names = items
        elif key == "nc":
            try:
                nc = int(val)
            except ValueError:
                pass
        elif key in ("train", "val", "test", "validation") and val:
            split_paths["val" if key == "validation" else key] = _unquote(val)
    if not names:
        names = None
    return {"names": names, "nc": nc, "split_paths": split_paths}


def detect_layout(root: str | Path) -> dict:
    """Detect classic vs YOLO dataset layout.

    Classic: ``root/<split>/[<class>/]<image>`` with ``.txt`` labels
    sitting next to each image.
    YOLO: ``root/images/<split>/`` + ``root/labels/<split>/`` (+
    optional ``data.yaml`` with class ``names``). A ``data.yaml``
    whose ``train``/``val``/``test`` entries resolve to existing
    directories also triggers YOLO mode, with those directories as
    the image dirs.

    Returns ``{"mode", "image_dirs", "label_dirs", "names",
    "data_yaml"}``. In classic mode the dir maps are empty.
    """
    import os

    root = Path(root)
    names: list[str] | None = None
    data_yaml: str | None = None
    split_paths: dict[str, Path] = {}
    yaml_path = root / "data.yaml"
    if yaml_path.is_file():
        data_yaml = str(yaml_path)
        parsed = parse_data_yaml(yaml_path)
        names = parsed["names"]
        for split, val in parsed["split_paths"].items():
            p = Path(val)
            if not p.is_absolute():
                p = yaml_path.parent / p
            p = Path(os.path.normpath(p))
            if p.is_dir():
                split_paths[split] = p
    images_dir = root / "images"
    if not split_paths and not images_dir.is_dir():
        return {"mode": "classic", "image_dirs": {}, "label_dirs": {},
                "names": None, "data_yaml": data_yaml}
    image_dirs = dict(split_paths)
    if images_dir.is_dir():
        for sub in sorted(images_dir.iterdir()):
            if sub.is_dir() and sub.name not in image_dirs:
                image_dirs[sub.name] = sub
    label_dirs: dict[str, Path | None] = {}
    for split, idir in image_dirs.items():
        cand = None
        if idir.parent.name == "images":
            cand = idir.parent.parent / "labels" / split
        if cand is not None and cand.is_dir():
            label_dirs[split] = cand
        else:
            root_labels = root / "labels" / split
            label_dirs[split] = root_labels if root_labels.is_dir() else None
    return {"mode": "yolo", "image_dirs": image_dirs, "label_dirs": label_dirs,
            "names": names, "data_yaml": data_yaml}


def _rel_or_str(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _yolo_label_for(image_path: Path, split: str, layout: dict) -> Path:
    """Label file for an image in YOLO mode (labels tree, else alongside)."""
    label_dir = layout["label_dirs"].get(split)
    if label_dir is not None:
        return label_dir / (image_path.stem + ".txt")
    return image_path.with_suffix(".txt")


def _classes_from_label(label_path: Path | None, names: list[str] | None) -> tuple[tuple, str]:
    """Class ids + display label parsed from a YOLO ``.txt`` file.

    Returns ``(classes, display)`` where ``classes`` is the sorted
    tuple of unique class ids (empty when the file is missing or
    holds no valid rows) and ``display`` joins class names from
    ``data.yaml`` when available, else the raw ids. Invalid rows are
    ignored here; the health checks flag them separately.
    """
    if label_path is None or not Path(label_path).is_file():
        return (), ""
    ids: set[int] = set()
    try:
        lines = Path(label_path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return (), ""
    for ln in lines:
        parts = ln.split()
        if len(parts) == 5:
            try:
                ids.add(int(parts[0]))
            except ValueError:
                pass
    if not ids:
        return (), ""
    classes = tuple(sorted(ids))
    if names:
        display = ",".join(
            names[i] if 0 <= i < len(names) else str(i) for i in classes
        )
    else:
        display = ",".join(str(i) for i in classes)
    return classes, display


def discover(root: str | Path, splits: list[str]) -> tuple[list[dict], list[str], dict]:
    """Discover images under ``root`` in either supported layout.

    Returns ``(records, missing_splits, layout)``. Each record has
    ``path``, ``split``, ``label`` (display string), ``classes``
    (tuple used for conflict comparison), ``label_path`` (``Path``
    or ``None``) and ``rel``.
    """
    root = Path(root)
    layout = detect_layout(root)
    records: list[dict] = []
    missing: list[str] = []
    if layout["mode"] == "yolo":
        for split in splits:
            idir = layout["image_dirs"].get(split)
            if idir is None or not idir.is_dir():
                missing.append(split)
                continue
            for path in sorted(idir.rglob("*")):
                if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                    label_path = _yolo_label_for(path, split, layout)
                    classes, display = _classes_from_label(label_path, layout["names"])
                    records.append(
                        {
                            "path": path,
                            "split": split,
                            "label": display,
                            "classes": classes,
                            "label_path": label_path,
                            "rel": _rel_or_str(path, root),
                        }
                    )
        return records, missing, layout
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
                        "classes": (label,) if label else (),
                        "label_path": path.with_suffix(".txt"),
                        "rel": _rel_or_str(path, root),
                    }
                )
    return records, missing, layout


def yolo_label_path(image_path: str | Path) -> Path:
    """YOLO label file sitting next to the image (same stem, .txt)."""
    p = Path(image_path)
    return p.with_suffix(".txt")


def move_to_quarantine(
    image_path: str | Path,
    root: str | Path,
    quarantine_dir: str | Path,
    move_yolo_label: bool = True,
    label_path: str | Path | None = None,
) -> dict:
    """Move one image (plus its YOLO .txt label, if any) to quarantine.

    The quarantine tree mirrors the path relative to ``root`` so two
    files with the same name in different splits/classes never clash.
    In YOLO layout the label lives in the labels tree, so it is
    mirrored under its own relative path (``labels/<split>/...``),
    not next to the quarantined image. Returns a manifest entry dict.
    """
    root, quarantine_dir = Path(root), Path(quarantine_dir)
    image_path = Path(image_path)
    try:
        rel = image_path.relative_to(root)
    except ValueError:
        # Image dir outside root (data.yaml absolute path): mirror by
        # parent dir + filename instead of failing.
        rel = Path(image_path.parent.name) / image_path.name
    dest = quarantine_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(image_path), str(dest))
    moved = [{"from": str(image_path), "to": str(dest)}]
    if move_yolo_label:
        label_src = Path(label_path) if label_path else yolo_label_path(image_path)
        if label_src.is_file():
            try:
                label_dest = quarantine_dir / label_src.relative_to(root)
            except ValueError:
                label_dest = dest.with_suffix(".txt")
            label_dest.parent.mkdir(parents=True, exist_ok=True)
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
