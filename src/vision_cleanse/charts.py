"""PNG charts for dataset exploration and cleaning reports.

Same idea as YOLO's ``results.png`` / ``labels.jpg``: one glance at
the pictures should tell you whether the dataset is sane, before
you spend GPU hours on it.

Matplotlib is an *optional* dependency (``pip install
vision-cleanse[charts]``) so the core stays Pillow+numpy only.
Importing this module never requires matplotlib; only calling
:func:`generate_charts` does, and it raises
:class:`ChartsUnavailableError` with install instructions when the
extra is missing.

Chart titles are English (like YOLO's plots) regardless of the
CLI language; the report JSON stays English too.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path


class ChartsUnavailableError(RuntimeError):
    """Raised when charts are requested but matplotlib is missing."""


def _plt():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except ImportError as exc:
        raise ChartsUnavailableError(
            "Charts need matplotlib: pip install vision-cleanse[charts]"
        ) from exc


def _load_boxes(records: list[dict]) -> list[dict]:
    """Parse valid YOLO rows from each record's label file.

    Returns one dict per box: ``{"split", "class", "x", "y", "w", "h",
    "path"}``. Rows that are not ``<int> <float> x4`` inside [0, 1]
    are skipped here (the health checks already flag them).
    """
    boxes = []
    for rec in records:
        lp = rec.get("label_path")
        if lp is None or not Path(lp).is_file():
            continue
        try:
            lines = Path(lp).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for ln in lines:
            parts = ln.split()
            if len(parts) != 5:
                continue
            try:
                cls = int(parts[0])
                x, y, w, h = (float(v) for v in parts[1:])
            except ValueError:
                continue
            if cls < 0 or not all(0.0 <= c <= 1.0 for c in (x, y, w, h)):
                continue
            boxes.append(
                {"split": rec["split"], "class": cls, "x": x, "y": y,
                 "w": w, "h": h, "path": str(rec["path"])}
            )
    return boxes


def _sample(values: list, limit: int = 5000) -> list:
    """Deterministic downsample (every k-th item) for scatter plots."""
    if len(values) <= limit:
        return values
    step = len(values) / limit
    return [values[int(i * step)] for i in range(limit)]


def _bar(plt, outdir: Path, name: str, title: str, labels, values,
         xlabel: str = "") -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([str(l) for l in labels], values)
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(outdir / name, dpi=120)
    plt.close(fig)
    return name


def _hist(plt, outdir: Path, name: str, title: str, values, xlabel: str,
          bins: int = 30) -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(values, bins=bins)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    fig.tight_layout()
    fig.savefig(outdir / name, dpi=120)
    plt.close(fig)
    return name


def _donut(plt, outdir: Path, name: str, title: str, labels, values) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.pie(values, labels=[str(l) for l in labels], autopct="%1.1f%%",
           wedgeprops={"width": 0.45})
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(outdir / name, dpi=120)
    plt.close(fig)
    return name


def generate_charts(report: dict, records: list[dict], outdir: str | Path) -> dict:
    """Write chart PNGs into ``outdir`` and describe what was made.

    Returns ``{"dir": str, "generated": [filenames],
    "skipped": [{"chart", "reason"}]}``. Charts without data are
    skipped (recorded, not faked with empty plots).
    """
    plt = _plt()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    skipped: list[dict] = []

    def skip(name: str, reason: str) -> None:
        skipped.append({"chart": name, "reason": reason})

    usable = [r for r in records if "md5" in r]
    splits = report["splits_scanned"]
    health = report["health"]
    dist = health["class_distribution"]

    # ---------- Overview ----------
    per_split = Counter(r["split"] for r in records)
    if per_split:
        generated.append(_bar(plt, outdir, "split_sizes.png",
                              "Images per split",
                              [s for s in splits if s in per_split],
                              [per_split[s] for s in splits if s in per_split],
                              xlabel="split"))
        if len(per_split) > 1:
            generated.append(_donut(plt, outdir, "split_share.png",
                                    "Split share",
                                    [s for s in splits if s in per_split],
                                    [per_split[s] for s in splits if s in per_split]))
        else:
            skip("split_share.png", "only one split scanned")
    else:
        skip("split_sizes.png", "no images found")
        skip("split_share.png", "no images found")

    class_totals: Counter = Counter()
    for split_counts in dist.values():
        class_totals.update(split_counts)
    if class_totals:
        top = class_totals.most_common(30)
        generated.append(_bar(plt, outdir, "class_images.png",
                              "Images per class" + (" (top 30)" if len(class_totals) > 30 else ""),
                              [c for c, _ in top], [n for _, n in top],
                              xlabel="class"))
        if len(splits) > 1 and len(class_totals) <= 30:
            classes = sorted(class_totals)
            fig, ax = plt.subplots(figsize=(8, 4.5))
            bottom = [0] * len(classes)
            for s in splits:
                vals = [dist.get(s, {}).get(c, 0) for c in classes]
                ax.bar([str(c) for c in classes], vals, bottom=bottom, label=s)
                bottom = [b + v for b, v in zip(bottom, vals)]
            ax.set_title("Images per class, stacked by split")
            ax.set_ylabel("count")
            ax.legend()
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
            fig.tight_layout()
            fig.savefig(outdir / "class_split_stacked.png", dpi=120)
            plt.close(fig)
            generated.append("class_split_stacked.png")
        else:
            skip("class_split_stacked.png", "needs 2+ splits and <= 30 classes")
    else:
        skip("class_images.png", "no class information")
        skip("class_split_stacked.png", "no class information")

    if usable:
        sizes_kb = [r["size"] / 1024 for r in usable]
        widths = [r["width"] for r in usable]
        heights = [r["height"] for r in usable]
        aspects = [r["width"] / r["height"] for r in usable if r["height"]]
        areas = [r["width"] * r["height"] / 1e6 for r in usable]
        generated.append(_hist(plt, outdir, "file_size_hist.png",
                               "File size distribution", sizes_kb, "size (KB)"))
        generated.append(_hist(plt, outdir, "width_hist.png",
                               "Image width distribution", widths, "width (px)"))
        generated.append(_hist(plt, outdir, "height_hist.png",
                               "Image height distribution", heights, "height (px)"))
        generated.append(_hist(plt, outdir, "aspect_hist.png",
                               "Aspect ratio distribution (w/h)", aspects, "w/h"))
        generated.append(_hist(plt, outdir, "area_hist.png",
                               "Image area distribution", areas, "megapixels"))
    else:
        for name in ("file_size_hist.png", "width_hist.png", "height_hist.png",
                     "aspect_hist.png", "area_hist.png"):
            skip(name, "no readable images")

    # ---------- Boxes (YOLO labels) ----------
    boxes = _load_boxes(records)
    names = (report.get("layout") or {}).get("names")

    def class_name(cls: int) -> str:
        if names and 0 <= cls < len(names):
            return names[cls]
        return str(cls)

    if boxes:
        per_image: Counter = Counter(b["path"] for b in boxes)
        generated.append(_hist(plt, outdir, "instances_per_image.png",
                               "Boxes per image",
                               list(per_image.values()), "boxes"))
        by_class: Counter = Counter(b["class"] for b in boxes)
        top = by_class.most_common(30)
        generated.append(_bar(plt, outdir, "boxes_per_class.png",
                              "Boxes per class" + (" (top 30)" if len(by_class) > 30 else ""),
                              [class_name(c) for c, _ in top],
                              [n for _, n in top], xlabel="class"))
        generated.append(_hist(plt, outdir, "box_width_hist.png",
                               "Box width distribution",
                               [b["w"] for b in boxes], "width (fraction)"))
        generated.append(_hist(plt, outdir, "box_height_hist.png",
                               "Box height distribution",
                               [b["h"] for b in boxes], "height (fraction)"))
        generated.append(_hist(plt, outdir, "box_area_hist.png",
                               "Box area distribution",
                               [b["w"] * b["h"] for b in boxes], "area (fraction)"))
        sample = _sample(boxes)
        fig, ax = plt.subplots(figsize=(6.5, 6))
        ax.scatter([b["x"] for b in sample], [b["y"] for b in sample],
                   s=4, alpha=0.4)
        ax.set_xlim(0, 1)
        ax.set_ylim(1, 0)
        ax.set_title("Box centers (x, y)")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        fig.tight_layout()
        fig.savefig(outdir / "box_centers_scatter.png", dpi=120)
        plt.close(fig)
        generated.append("box_centers_scatter.png")
        fig, ax = plt.subplots(figsize=(6.5, 6))
        ax.hist2d([b["x"] for b in boxes], [b["y"] for b in boxes],
                  bins=20, cmap="Blues")
        ax.set_xlim(0, 1)
        ax.set_ylim(1, 0)
        ax.set_title("Box center heatmap")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        fig.tight_layout()
        fig.savefig(outdir / "box_centers_heatmap.png", dpi=120)
        plt.close(fig)
        generated.append("box_centers_heatmap.png")
        fig, ax = plt.subplots(figsize=(6.5, 4.5))
        ax.scatter([b["w"] for b in sample], [b["h"] for b in sample],
                   s=4, alpha=0.4)
        ax.set_title("Box width vs height")
        ax.set_xlabel("width (fraction)")
        ax.set_ylabel("height (fraction)")
        fig.tight_layout()
        fig.savefig(outdir / "box_wh_scatter.png", dpi=120)
        plt.close(fig)
        generated.append("box_wh_scatter.png")
        classes = sorted(by_class)
        if len(splits) > 1 and len(classes) <= 30:

            matrix = [[sum(1 for b in boxes if b["class"] == c and b["split"] == s)
                       for s in splits] for c in classes]
            fig, ax = plt.subplots(figsize=(8, max(4.5, 0.4 * len(classes))))
            ax.imshow(matrix, aspect="auto", cmap="Blues")
            ax.set_xticks(range(len(splits)))
            ax.set_xticklabels(splits)
            ax.set_yticks(range(len(classes)))
            ax.set_yticklabels([class_name(c) for c in classes])
            ax.set_title("Boxes per class and split")
            for i in range(len(classes)):
                for j in range(len(splits)):
                    ax.text(j, i, matrix[i][j], ha="center", va="center")
            fig.tight_layout()
            fig.savefig(outdir / "class_split_heatmap.png", dpi=120)
            plt.close(fig)
            generated.append("class_split_heatmap.png")
        else:
            skip("class_split_heatmap.png", "needs 2+ splits and <= 30 classes")
    else:
        for name in ("instances_per_image.png", "boxes_per_class.png",
                     "box_width_hist.png", "box_height_hist.png",
                     "box_area_hist.png", "box_centers_scatter.png",
                     "box_centers_heatmap.png", "box_wh_scatter.png",
                     "class_split_heatmap.png"):
            skip(name, "no valid YOLO boxes found")

    # ---------- Cleaning results ----------
    if report["groups_exact"] + report["groups_near"] > 0:
        generated.append(_bar(plt, outdir, "dup_by_method.png",
                              "Duplicate groups by method",
                              ["exact", "near"],
                              [report["groups_exact"], report["groups_near"]],
                              xlabel="method"))
    else:
        skip("dup_by_method.png", "no duplicate groups")
    removals = report["removals"]
    if removals:
        by_split: Counter = Counter(r["split"] for r in removals)
        generated.append(_bar(plt, outdir, "removals_by_split.png",
                              "Removals by split",
                              [s for s in splits if s in by_split],
                              [by_split[s] for s in splits if s in by_split],
                              xlabel="split"))
        by_reason: Counter = Counter(r["reason"] for r in removals)
        generated.append(_bar(plt, outdir, "removals_by_reason.png",
                              "Removals by reason",
                              list(by_reason), list(by_reason.values()),
                              xlabel="reason"))
    else:
        skip("removals_by_split.png", "no removals")
        skip("removals_by_reason.png", "no removals")
    findings = health["findings"]
    if findings:
        by_check: Counter = Counter(f["check"] for f in findings)
        generated.append(_bar(plt, outdir, "health_by_check.png",
                              "Health findings by check",
                              list(by_check), list(by_check.values()),
                              xlabel="check"))
    else:
        skip("health_by_check.png", "no health findings")
    counts = health["counts"]
    sev_labels = [k for k in ("errors", "warnings", "info") if counts[k] > 0]
    if sev_labels:
        generated.append(_donut(plt, outdir, "health_by_severity.png",
                                "Health findings by severity",
                                sev_labels, [counts[k] for k in sev_labels]))
    else:
        skip("health_by_severity.png", "no health findings")
    if per_split:
        removed_by_split: Counter = Counter(r["split"] for r in removals)
        kept = [per_split.get(s, 0) - removed_by_split.get(s, 0) for s in splits]
        removed = [removed_by_split.get(s, 0) for s in splits]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(splits, kept, label="kept")
        ax.bar(splits, removed, bottom=kept, label="quarantined")
        ax.set_title("Kept vs quarantined per split")
        ax.set_ylabel("images")
        ax.legend()
        fig.tight_layout()
        fig.savefig(outdir / "kept_vs_quarantined.png", dpi=120)
        plt.close(fig)
        generated.append("kept_vs_quarantined.png")
    else:
        skip("kept_vs_quarantined.png", "no images found")

    return {"dir": str(outdir), "generated": generated, "skipped": skipped}
