"""Core engine: run rings 1-2, resolve conflicts, quarantine.

Safety contract (read this before using ``apply`` mode):

* Dry-run is the default: nothing moves unless ``dry_run=False``.
* Removal never deletes: files are *moved* to a quarantine tree
  that mirrors the dataset layout, with ``manifest.json`` so every
  move is reversible.
* Label conflicts are never auto-resolved: the whole group is kept
  and written to ``conflict_report.csv`` for human review.
* Split priority protects evaluation data: ``test > val > train``.
  A duplicate found in test and train is kept in test.
* Within one split, the keeper is deterministic: highest
  resolution, then largest file, then lexicographically smallest
  path. Re-running gives the same result.
"""

from __future__ import annotations

from pathlib import Path

from . import utils
from .extractors import dhash, file_hash, image_size, phash
from .matchers import group_duplicates

# Lower rank = higher priority (kept first).
SPLIT_PRIORITY = {"test": 0, "val": 1, "validation": 1, "train": 2, "training": 2}


def _split_rank(split: str) -> int:
    return SPLIT_PRIORITY.get(split, 3)


def _keeper_key(rec: dict) -> tuple:
    """Sort key for choosing the keeper: smaller wins."""
    w, h = rec.get("width", 0), rec.get("height", 0)
    return (_split_rank(rec["split"]), -(w * h), -rec.get("size", 0), str(rec["path"]))


def resolve_group(group_id: int, group: dict, records: list[dict]) -> dict:
    """Resolve one duplicate group into kept / removed / conflict.

    Returns ``{"group_id", "method", "kept", "removed", "conflict"}``
    where ``kept``/``removed`` are record dicts and ``conflict`` is
    a conflict-report row (or ``None``).
    """
    members = [records[i] for i in group["members"]]
    labels = {m["label"] for m in members if m["label"]}
    if len(labels) > 1:
        return {
            "group_id": group_id,
            "method": group["method"],
            "kept": members,
            "removed": [],
            "conflict": {
                "group_id": group_id,
                "method": group["method"],
                "labels": sorted(labels),
                "splits": sorted({m["split"] for m in members}),
                "files": [str(m["path"]) for m in members],
            },
        }
    ordered = sorted(members, key=_keeper_key)
    kept, removed = ordered[0], ordered[1:]
    return {
        "group_id": group_id,
        "method": group["method"],
        "kept": [kept],
        "removed": [
            {
                "path": str(m["path"]),
                "split": m["split"],
                "label": m["label"],
                "kept_path": str(kept["path"]),
                "reason": (
                    "duplicate_in_lower_priority_split"
                    if m["split"] != kept["split"]
                    else "duplicate_within_same_split"
                ),
            }
            for m in removed
        ],
        "conflict": None,
    }


def clean(
    root: str | Path,
    splits: tuple[str, ...] = ("train", "val", "test"),
    phash_threshold: int = 10,
    dhash_threshold: int = 10,
    hash_algo: str = "md5",
    dry_run: bool = True,
    quarantine_dir: str | Path | None = None,
    report_dir: str | Path | None = None,
    coco_path: str | Path | None = None,
    coco_output: str | Path | None = None,
) -> dict:
    """Run the MVP pipeline over ``root`` and return a report dict.

    Parameters
    ----------
    root: dataset root containing ``<split>/`` subdirectories.
    splits: split names to scan (missing ones are skipped).
    phash_threshold, dhash_threshold: max Hamming distance for a
        near-duplicate pair (either hash within threshold groups
        the pair -- see matchers.py for why OR, not AND).
    dry_run: when True (default) nothing moves; the report only
        lists what *would* be quarantined.
    quarantine_dir: where removed files are moved in apply mode.
        Defaults to ``<root>_quarantine`` (a sibling of root).
    report_dir: if given, ``report.json`` and ``conflict_report.csv``
        are written there.
    coco_path / coco_output: optional COCO annotation file to sync.
        The original is never overwritten; the cleaned copy goes to
        ``coco_output`` (default ``<coco_path>.cleaned.json``).
        In dry-run mode the sync is only counted, not written.
    """
    root = Path(root)
    records, missing = utils.discover(root, list(splits))

    # --- Feature extraction (rings 1 + 2) ---
    unreadable: list[str] = []
    for rec in records:
        p = Path(rec["path"])
        try:
            # Compute into locals first: on failure nothing is
            # assigned, so a half-hashed record can never leak
            # into grouping (that was a real KeyError bug).
            md5 = file_hash(p, hash_algo)
            ph, dh = phash(p), dhash(p)
            w, h = image_size(p)
            size = p.stat().st_size
        except Exception as exc:  # corrupt / truncated / not an image
            unreadable.append(f"{p}: {exc}")
            continue
        rec.update({"md5": md5, "phash": ph, "dhash": dh,
                    "width": w, "height": h, "size": size})

    usable = [r for r in records if "md5" in r]
    groups = group_duplicates(usable, phash_threshold, dhash_threshold)
    # group_duplicates indexes into ``usable``; resolve against it.
    resolved = [resolve_group(i, g, usable) for i, g in enumerate(groups)]
    conflicts = [r["conflict"] for r in resolved if r["conflict"] is not None]
    removals = [x for r in resolved for x in r["removed"]]
    kept_paths = {str(r["kept"][0]["path"]) for r in resolved}

    report: dict = {
        "root": str(root),
        "splits_scanned": [s for s in splits if s not in missing],
        "splits_missing": missing,
        "images_found": len(records),
        "images_unreadable": unreadable,
        "duplicate_groups": len(groups),
        "groups_exact": sum(1 for g in groups if g["method"] == "exact"),
        "groups_near": sum(1 for g in groups if g["method"] == "near"),
        "to_quarantine": len(removals),
        "label_conflicts": len(conflicts),
        "dry_run": dry_run,
        "groups": [
            {
                "group_id": r["group_id"],
                "method": r["method"],
                "kept": [str(k["path"]) for k in r["kept"]],
                "removed": [x["path"] for x in r["removed"]],
                "conflict": r["conflict"] is not None,
            }
            for r in resolved
        ],
        "removals": removals,
        "conflicts": conflicts,
        "kept_sample": sorted(kept_paths)[:10],
    }

    # --- Side effects (apply mode only, except reports) ---
    if report_dir is not None:
        utils.write_json_report(report_dir, report)
        if conflicts:
            utils.write_conflict_report(report_dir, conflicts)

    removed_paths = [r["path"] for r in removals]
    if coco_path is not None:
        out = Path(coco_output) if coco_output else Path(str(coco_path) + ".cleaned.json")
        if dry_run:
            report["coco_sync"] = {"planned_output": str(out), "would_remove_images": len(removed_paths)}
        else:
            report["coco_sync"] = utils.sync_coco(coco_path, removed_paths, out)

    if not dry_run:
        qdir = Path(quarantine_dir) if quarantine_dir else Path(str(root) + "_quarantine")
        manifest = []
        for r in removals:
            entry = utils.move_to_quarantine(r["path"], root, qdir)
            entry.update({"reason": r["reason"], "kept_path": r["kept_path"]})
            manifest.append(entry)
        report["quarantine_dir"] = str(qdir)
        report["manifest"] = str(utils.write_manifest(qdir, manifest))

    return report
