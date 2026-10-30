"""Dataset health checks: everything beyond duplicate grouping.

These checks answer "is this dataset actually clean?" in the
mechanical sense: files that cannot be read, files that carry no
signal, annotations that do not line up with images, names that
collide, and duplicates hiding inside the test set itself.

Severity levels:
- ``error``: the file/dataset is broken and must be fixed.
- ``warning``: suspicious and worth reviewing before training.
- ``info``: reported for awareness, never blocks a "clean" verdict.

``clean`` in the returned dict means "every enabled check passed".
It is NOT an absolute guarantee: near-duplicate detection is fuzzy
by nature and no checker can catch semantic label mistakes. The
report lists exactly what was checked so the verdict is auditable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .extractors import IMAGE_EXTENSIONS


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1


def _iter_split_files(root: Path, splits: list[str], layout: dict | None = None):
    """Yield ``(split, file)`` for every file under the scanned splits.

    In YOLO layout this covers both the images tree and the labels
    tree; in classic layout it covers ``root/<split>/``.
    """
    if layout is not None and layout["mode"] == "yolo":
        for split in splits:
            idir = layout["image_dirs"].get(split)
            if idir is not None and idir.is_dir():
                for p in sorted(idir.rglob("*")):
                    if p.is_file():
                        yield split, p
            ldir = layout["label_dirs"].get(split)
            if ldir is not None and ldir.is_dir():
                for p in sorted(ldir.rglob("*")):
                    if p.is_file():
                        yield split, p
        return
    for split in splits:
        split_dir = root / split
        if not split_dir.is_dir():
            continue
        for p in sorted(split_dir.rglob("*")):
            if p.is_file():
                yield split, p


def run_health_checks(
    root: str | Path,
    records: list[dict],
    resolved_groups: list[dict],
    splits: list[str],
    min_size: int = 32,
    yolo: bool | None = None,
    layout: dict | None = None,
) -> dict:
    """Run all health checks. ``records`` are discover() dicts, some
    carrying extracted features (usable ones have ``md5``);
    ``resolved_groups`` are core.resolve_group() outputs."""
    root = Path(root)
    findings: list[dict] = []

    def add(check: str, severity: str, path, detail: str = "") -> None:
        findings.append(
            {"check": check, "severity": severity, "path": str(path), "detail": detail}
        )

    usable = [r for r in records if "md5" in r]

    # --- File-level checks (always on) ---
    for rec in records:
        p = Path(rec["path"])
        if _size(p) == 0:
            add("zero_byte", "error", p)
            continue
        if "md5" not in rec:
            add("corrupt", "error", p)
    for rec in usable:
        p = Path(rec["path"])
        try:
            with Image.open(p) as im:
                gray = np.asarray(im.convert("L"), dtype=np.float64)
        except Exception:  # noqa: BLE001, S112 - already reported as corrupt upstream
            continue
        if float(gray.std()) < 1.0:
            add("blank", "warning", p, "std<1.0 (solid color)")
        w, h = rec.get("width", 0), rec.get("height", 0)
        if w and h and max(w, h) < min_size:
            add("tiny", "warning", p, f"{w}x{h} < {min_size}px")
    for split, p in _iter_split_files(root, splits, layout):
        if p.suffix.lower() not in IMAGE_EXTENSIONS and p.suffix.lower() != ".txt":
            add("other_file", "info", p, f"split={split}")

    # --- YOLO annotation consistency (auto-enabled if any .txt found) ---
    label_files: list[Path] = []
    for split, p in _iter_split_files(root, splits, layout):
        if p.suffix.lower() == ".txt":
            label_files.append(p)
    if yolo is None:
        yolo = len(label_files) > 0
    diag: dict | None = None
    if yolo:
        # Pair by exact expected label path: alongside the image in
        # classic mode, in the labels tree in YOLO mode.
        expected: dict[Path, dict] = {}
        for rec in records:
            lp = rec.get("label_path")
            if lp is not None:
                expected[Path(lp)] = rec
        for rec in records:
            lp = rec.get("label_path")
            if lp is None or not Path(lp).is_file():
                add("missing_label", "warning", rec["path"])
        names = (layout or {}).get("names")
        diag_lines = 0
        diag_malformed = 0
        diag_empty = 0
        diag_unknown_ids: set[int] = set()
        diag_unknown_files = 0
        for lf in label_files:
            if lf not in expected:
                add("orphan_label", "warning", lf)
                continue
            try:
                lines = lf.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                add("invalid_label", "error", lf, "unreadable as UTF-8")
                continue
            content = [ln for ln in lines if ln.strip()]
            if not content:
                add("empty_label", "warning", lf)
                diag_empty += 1
                continue
            diag_lines += len(content)
            file_unknown: set[int] = set()
            for i, ln in enumerate(content, start=1):
                parts = ln.split()
                ok = len(parts) == 5
                if ok:
                    try:
                        cls = int(parts[0])
                        coords = [float(x) for x in parts[1:]]
                        ok = cls >= 0 and all(0.0 <= c <= 1.0 for c in coords)
                    except ValueError:
                        ok = False
                if not ok:
                    add("invalid_label", "error", lf, f"line {i}: {ln.strip()[:60]}")
                    diag_malformed += 1
                elif names is not None and cls >= len(names):
                    # Valid 5-column row, but the class id has no name
                    # in data.yaml: a dialect mismatch (e.g. a dataset
                    # whose .txt ids run past the names list), not a
                    # corrupt line. Warn once per file, not per line.
                    file_unknown.add(cls)
            if file_unknown:
                diag_unknown_ids.update(file_unknown)
                diag_unknown_files += 1
                add(
                    "unknown_class",
                    "warning",
                    lf,
                    f"class ids outside data.yaml names ({len(names)} names): "
                    + ", ".join(str(c) for c in sorted(file_unknown)),
                )
        diag = {
            "label_files": len(label_files),
            "lines_scanned": diag_lines,
            "malformed_lines": diag_malformed,
            "empty_label_files": diag_empty,
            "empty_label_rate": (diag_empty / len(label_files))
            if label_files
            else None,
            "unknown_class_ids": sorted(diag_unknown_ids),
            "unknown_class_files": diag_unknown_files,
        }

    # --- Name collisions across splits/classes ---
    by_name: dict[str, list[dict]] = {}
    for rec in usable:
        by_name.setdefault(Path(rec["path"]).name, []).append(rec)
    for group in by_name.values():
        if len(group) > 1 and len({r["md5"] for r in group}) > 1:
            add(
                "dup_basename",
                "warning",
                group[0]["path"],
                "; ".join(str(r["path"]) for r in group),
            )

    # --- Duplicates inside the test set ---
    for g in resolved_groups:
        members = list(g["kept"]) + [
            {"path": r["path"], "split": r["split"]} for r in g["removed"]
        ]
        test_members = [m for m in members if m.get("split") == "test"]
        if len(test_members) >= 2:
            add(
                "test_internal_dup",
                "warning",
                test_members[0]["path"],
                f"group {g['group_id']}: "
                + "; ".join(str(m["path"]) for m in test_members),
            )

    # --- Class distribution (info only) ---
    distribution: dict[str, dict[str, int]] = {}
    for rec in records:
        distribution.setdefault(rec["split"], {})
        distribution[rec["split"]][rec["label"] or "(no class)"] = (
            distribution[rec["split"]].get(rec["label"] or "(no class)", 0) + 1
        )

    counts = {
        "errors": sum(1 for f in findings if f["severity"] == "error"),
        "warnings": sum(1 for f in findings if f["severity"] == "warning"),
        "info": sum(1 for f in findings if f["severity"] == "info"),
    }
    counts["total"] = len(findings)
    return {
        "findings": findings,
        "counts": counts,
        "class_distribution": distribution,
        # Summary of the YOLO label scan (None when the YOLO checks
        # did not run): rates and dialect-mismatch signals that the
        # per-file findings alone do not show at a glance.
        "label_diagnostics": diag,
        # "Clean" = every enabled check passed (errors and warnings).
        # Info findings never block it. Not an absolute guarantee.
        "clean": counts["errors"] == 0 and counts["warnings"] == 0,
    }
