"""PNG charts for dataset exploration and cleaning reports.

Same idea as YOLO's ``results.png`` / ``labels.jpg``: one glance at
the pictures should tell you whether the dataset is sane, before
you spend GPU hours on it.

The charts are rendered from a pure HTML/CSS + inline-SVG template
(no JavaScript, no CDN, no external references) through WeasyPrint
(``pip install vision-cleanse[charts]``) to PDF, then rasterised
with ``pdftoppm -r 96`` (poppler-utils) to a 1600x900 PNG. Importing
this module never requires WeasyPrint; only calling
:func:`generate_charts` does, and it raises
:class:`ChartsUnavailableError` with install instructions when the
extra (or ``pdftoppm``) is missing.

Style is the approved "light modern" look: a white card with a
28px radius and a soft shadow on a pale background, indigo
``#4f46e5`` + cyan ``#06b6d4`` as the main palette, 54px titles,
28px subtitles, 38px bold value labels, Noto Sans, and integer
("nice") ticks on every count axis -- never fractional counts.

Chart titles are English (like YOLO's plots) regardless of the
CLI language; the report JSON stays English too.

WeasyPrint limits respected here (verified on this engine):
no SVG ``linearGradient`` (solid colours only) and no
``mix-blend-mode`` -- the Venn diagram blends with
``fill-opacity="0.55"`` instead.
"""

from __future__ import annotations

import html
import math
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

# --- Palette (light modern) -------------------------------------------
INDIGO = "#4f46e5"
CYAN = "#06b6d4"
VIOLET = "#8b5cf6"
RED = "#dc2626"
AMBER = "#d97706"
GREEN = "#16a34a"
INK = "#0f172a"
GREY = "#64748b"
GRID = "#e2e8f0"
LIGHT_FILL = "#eef2ff"
ZERO_FILL = "#f1f5f9"

# Split colours for stacked charts / donut legends.
SPLIT_COLORS = {"train": INDIGO, "val": CYAN, "test": VIOLET,
                "validation": CYAN, "training": INDIGO}
# Fixed Venn colours (red=train, green=val, blue=test) regardless of style.
VENN_FILL = {"train": "#ef4444", "val": "#22c55e", "test": "#3b82f6"}
VENN_STROKE = {"train": "#dc2626", "val": "#16a34a", "test": "#2563eb"}
SEVERITY_COLORS = {"errors": RED, "warnings": AMBER, "info": CYAN}

# Card geometry: 1600x900 page, white card, plot SVG 1360 wide.
PAGE_CSS = """
@page { size: 1600px 900px; margin: 0; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1600px; height: 900px; background: #eef2f7;
  font-family: "Noto Sans", "DejaVu Sans", sans-serif; }
.card { width: 1480px; height: 820px; background: #ffffff;
  border-radius: 28px; box-shadow: 0 24px 64px rgba(15, 23, 42, 0.14);
  padding: 48px 60px 32px; margin: 40px auto; }
h1 { font-size: 54px; color: #0f172a; letter-spacing: -0.5px; }
.sub { font-size: 28px; color: #64748b; margin-top: 10px; }
.plot { margin-top: 20px; }
.foot { margin-top: 12px; font-size: 24px; color: #64748b; }
.foot b { color: #4f46e5; }
svg text { font-family: "Noto Sans", "DejaVu Sans", sans-serif; }
"""


class ChartsUnavailableError(RuntimeError):
    """Raised when charts are requested but WeasyPrint/pdftoppm is missing."""


def _esc(value) -> str:
    return html.escape(str(value), quote=True)


def _fmt_num(value: float) -> str:
    """Short human number: 25, 8.5, 0.1, 0.0655 (no trailing zeros)."""
    value = float(value)
    if value == int(value):
        return str(int(value))
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    if abs(value) >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _nice_step(max_value: float, target: int = 5) -> float:
    """1/2/5 x 10^k step so ~``target`` intervals cover ``max_value``."""
    if max_value <= 0:
        return 1.0
    raw = max_value / target
    mag = 10 ** math.floor(math.log10(raw))
    for mult in (1, 2, 5, 10):
        step = mult * mag
        if step >= raw:
            return step
    return 10 * mag


def _count_ticks(max_value: int) -> tuple[list[int], int]:
    """Integer ticks + nice ceiling for a count axis (never fractions)."""
    step = max(1, math.ceil(_nice_step(float(max_value)))) if max_value > 0 else 1
    nice = step * max(1, math.ceil(max_value / step)) if max_value > 0 else 1
    ticks = []
    tick = step
    while tick <= nice:
        ticks.append(tick)
        tick += step
    return ticks, nice


def _blend(hex_a: str, hex_b: str, ratio: float) -> str:
    """Linear RGB blend between two #rrggbb colours."""
    ratio = min(1.0, max(0.0, ratio))
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * ratio):02x}" for x, y in zip(a, b))


def _short(label: str, limit: int = 18) -> str:
    label = str(label)
    return label if len(label) <= limit else label[: limit - 1] + "…"


def _foot_parts(parts: list[str]) -> str:
    return " · ".join(parts)


# --- Page rendering ----------------------------------------------------

def _page(title: str, subtitle: str, svg: str, footer: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
        f"<style>{PAGE_CSS}</style></head><body><div class=\"card\">\n"
        f"<h1>{_esc(title)}</h1><div class=\"sub\">{_esc(subtitle)}</div>\n"
        f"<div class=\"plot\">{svg}</div><div class=\"foot\">{footer}</div>\n"
        "</div></body></html>"
    )


def _render(outdir: Path, name: str, title: str, subtitle: str,
            svg: str, footer: str) -> str:
    """Render one chart page to ``outdir / name`` (PNG, 1600x900)."""
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ChartsUnavailableError(
            "Charts need weasyprint + pdftoppm: "
            "pip install vision-cleanse[charts]"
        ) from exc
    doc = _page(title, subtitle, svg, footer)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pdf = tmp / "chart.pdf"
        HTML(string=doc).write_pdf(str(pdf))
        try:
            proc = subprocess.run(
                ["pdftoppm", "-r", "96", "-png", "-singlefile",
                 str(pdf), str(tmp / "chart")],
                capture_output=True, text=True, check=False,
            )
        except FileNotFoundError as exc:
            raise ChartsUnavailableError(
                "Charts need pdftoppm (poppler-utils) on PATH: "
                "pip install vision-cleanse[charts]"
            ) from exc
        png = tmp / "chart.png"
        if proc.returncode != 0 or not png.is_file():
            raise ChartsUnavailableError(
                f"pdftoppm failed for {name}: {proc.stderr.strip()}"
            )
        (outdir / name).write_bytes(png.read_bytes())
    return name


# --- SVG chart builders (all pure functions of the data) ---------------

def _bar_svg(labels, values, colors) -> str:
    """Vertical bars, 1360x500, baseline y=430, plot top y=60."""
    width, base, top = 1360, 430, 60
    plot_h = base - top
    ticks, nice = _count_ticks(max(values) if values else 0)
    parts = [f'<svg viewBox="0 0 {width} 500" width="{width}" height="500">']
    for tick in ticks:
        y = base - tick / nice * plot_h
        parts.append(f'<line x1="0" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" '
                     f'stroke="{GRID}" stroke-width="2"/>')
        parts.append(f'<text x="0" y="{y - 12:.1f}" font-size="26" '
                     f'fill="{GREY}">{tick}</text>')
    parts.append(f'<line x1="0" y1="{base}" x2="{width}" y2="{base}" '
                 f'stroke="{GREY}" stroke-width="3"/>')
    n = len(labels)
    slot = width / max(1, n)
    bar_w = min(220.0, slot * 0.62)
    rx = min(18.0, max(2.0, bar_w * 0.18))
    lab_font = 30 if n <= 8 else (22 if n <= 16 else 18)
    # Shrink x labels until the longest fits its slot (long bin ranges
    # like "0.0655–0.0666" must not overlap or clip at the edges).
    max_len = max((len(str(label)) for label in labels), default=0)
    while lab_font > 15 and max_len * lab_font * 0.58 > slot:
        lab_font -= 1
    val_font = 38 if n <= 8 else 28
    for i, (label, value) in enumerate(zip(labels, values)):
        cx = slot * i + slot / 2
        x = cx - bar_w / 2
        height = value / nice * plot_h if nice else 0
        if 0 < value and height < 6:
            height = 6
        y = base - height
        color = colors[i % len(colors)]
        if value > 0:
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                         f'height="{height:.1f}" rx="{rx:.1f}" fill="{color}"/>')
        label_y = (y - 16) if value > 0 else base - 16
        parts.append(f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                     f'font-size="{val_font}" font-weight="700" '
                     f'fill="{INK}">{value}</text>')
        parts.append(f'<text x="{cx:.1f}" y="482" text-anchor="middle" '
                     f'font-size="{lab_font}" fill="{GREY}">'
                     f'{_esc(_short(label))}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _hist_bins(values: list[float]) -> tuple[list[str], list[int]]:
    """Bin counts: one bar per integer when the range is small and
    integral, else 10 equal-width bins (labels like ``8.5–9.6``)."""
    if not values:
        return [], []
    lo, hi = min(values), max(values)
    integral = all(float(v) == int(v) for v in values)
    if integral and hi - lo <= 20:
        labels = [str(int(v)) for v in range(int(lo), int(hi) + 1)]
        counts = Counter(int(v) for v in values)
        return labels, [counts[int(v)] for v in range(int(lo), int(hi) + 1)]
    if hi == lo:
        return [_fmt_num(lo)], [len(values)]
    width = (hi - lo) / 10
    # Bin-edge labels use just enough decimals to tell bins apart:
    # integers for pixel-sized bins, 1 decimal for KB sizes ("8.5–9.6"
    # like the approved sample), more for tiny spans (megapixels).
    if width >= 2:
        decimals = 0
    elif width >= 0.2:
        decimals = 1
    else:
        decimals = max(2, -math.floor(math.log10(width)) + 1)

    def edge(v: float) -> str:
        return f"{v:.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{v:.0f}"

    labels, counts = [], []
    for i in range(10):
        a, b = lo + i * width, lo + (i + 1) * width
        if i < 9:
            count = sum(1 for v in values if a <= v < b)
        else:
            count = sum(1 for v in values if a <= v <= b)
        labels.append(f"{edge(a)}–{edge(b)}")
        counts.append(count)
    return labels, counts


def _donut_svg(labels, values, colors, center_value, center_word) -> str:
    """Donut, 1360x500: ring at (330, 250) r=150, legend on the right."""
    width = 1360
    total = sum(values)
    circ = 2 * math.pi * 150
    parts = [f'<svg viewBox="0 0 {width} 500" width="{width}" height="500">']
    parts.append(f'<circle cx="330" cy="250" r="150" fill="none" '
                 f'stroke="{GRID}" stroke-width="90"/>')
    offset = 0.0
    for value, color in zip(values, colors):
        seg = circ * value / total if total else 0
        parts.append(
            f'<circle cx="330" cy="250" r="150" fill="none" stroke="{color}" '
            f'stroke-width="90" stroke-dasharray="{seg:.1f} {circ - seg:.1f}" '
            f'stroke-dashoffset="{-offset:.1f}" '
            f'transform="rotate(-90 330 250)"/>')
        offset += seg
    parts.append(f'<text x="330" y="240" text-anchor="middle" font-size="72" '
                 f'font-weight="700" fill="{INK}">{center_value}</text>')
    parts.append(f'<text x="330" y="292" text-anchor="middle" font-size="28" '
                 f'fill="{GREY}">{_esc(center_word)}</text>')
    for i, (label, value) in enumerate(zip(labels, values)):
        y = 150 + i * 92
        pct = 100.0 * value / total if total else 0.0
        parts.append(f'<rect x="620" y="{y}" width="34" height="34" rx="9" '
                     f'fill="{colors[i % len(colors)]}"/>')
        parts.append(f'<text x="676" y="{y + 28}" font-size="32" fill="{INK}">'
                     f'{_esc(label)} · {value} ({pct:.1f}%)</text>')
    parts.append("</svg>")
    return "".join(parts)


def _stacked_svg(categories, series) -> str:
    """Stacked columns. ``series`` = [(label, colour, [values])]."""
    width, base, top = 1360, 430, 60
    plot_h = base - top
    totals = [sum(s[2][i] for s in series) for i in range(len(categories))]
    _, nice = _count_ticks(max(totals) if totals else 0)
    parts = [f'<svg viewBox="0 0 {width} 500" width="{width}" height="500">']
    ticks, _ = _count_ticks(max(totals) if totals else 0)
    for tick in ticks:
        y = base - tick / nice * plot_h
        parts.append(f'<line x1="0" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" '
                     f'stroke="{GRID}" stroke-width="2"/>')
        parts.append(f'<text x="0" y="{y - 12:.1f}" font-size="26" '
                     f'fill="{GREY}">{tick}</text>')
    parts.append(f'<line x1="0" y1="{base}" x2="{width}" y2="{base}" '
                 f'stroke="{GREY}" stroke-width="3"/>')
    n = len(categories)
    slot = width / max(1, n)
    bar_w = min(220.0, slot * 0.62)
    rx = min(18.0, max(2.0, bar_w * 0.18))
    lab_font = 30 if n <= 8 else (22 if n <= 16 else 18)
    max_len = max((len(str(c)) for c in categories), default=0)
    while lab_font > 15 and max_len * lab_font * 0.58 > slot:
        lab_font -= 1
    val_font = 38 if n <= 8 else 28
    for i, category in enumerate(categories):
        cx = slot * i + slot / 2
        x = cx - bar_w / 2
        y_cur = float(base)
        for _label, color, values in series:
            value = values[i]
            height = value / nice * plot_h if nice and value else 0
            if value > 0:
                parts.append(f'<rect x="{x:.1f}" y="{y_cur - height:.1f}" '
                             f'width="{bar_w:.1f}" height="{height:.1f}" '
                             f'rx="{rx:.1f}" fill="{color}" '
                             f'stroke="#ffffff" stroke-width="2"/>')
            y_cur -= height
        top_y = y_cur
        parts.append(f'<text x="{cx:.1f}" y="{top_y - 16:.1f}" '
                     f'text-anchor="middle" font-size="{val_font}" '
                     f'font-weight="700" fill="{INK}">{totals[i]}</text>')
        parts.append(f'<text x="{cx:.1f}" y="482" text-anchor="middle" '
                     f'font-size="{lab_font}" fill="{GREY}">'
                     f'{_esc(_short(category))}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _scatter_svg(points, x_ticks, y_ticks, invert_y: bool) -> str:
    """Scatter, 1360x500. Plot area x 90..1300, y 40..430."""
    left, right, top, bottom = 90, 1300, 40, 430
    plot_w, plot_h = right - left, bottom - top
    x_max = x_ticks[-1] if x_ticks else 1
    y_max = y_ticks[-1] if y_ticks else 1
    parts = ['<svg viewBox="0 0 1360 500" width="1360" height="500">']
    for tick in x_ticks:
        x = left + tick / x_max * plot_w
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" '
                     f'stroke="{GRID}" stroke-width="2"/>')
        parts.append(f'<text x="{x:.1f}" y="470" text-anchor="middle" '
                     f'font-size="26" fill="{GREY}">{_fmt_num(tick)}</text>')
    for tick in y_ticks:
        y = (top + tick / y_max * plot_h) if invert_y else (bottom - tick / y_max * plot_h)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" '
                     f'stroke="{GRID}" stroke-width="2"/>')
        parts.append(f'<text x="{left - 14}" y="{y + 9:.1f}" text-anchor="end" '
                     f'font-size="26" fill="{GREY}">{_fmt_num(tick)}</text>')
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
                 f'stroke="{GREY}" stroke-width="3"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
                 f'stroke="{GREY}" stroke-width="3"/>')
    for px, py in points:
        x = left + px / x_max * plot_w
        y = (top + py / y_max * plot_h) if invert_y else (bottom - py / y_max * plot_h)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" '
                     f'fill="{INDIGO}" fill-opacity="0.5"/>')
    parts.append("</svg>")
    return "".join(parts)


def _centers_heatmap_svg(boxes) -> str:
    """10x10 box-center heatmap, 1360x560: grid 480x480 + legend."""
    grid_x, grid_y, cell = 360, 20, 48
    counts = Counter()
    for box in boxes:
        counts[(min(9, int(box["x"] * 10)), min(9, int(box["y"] * 10)))] += 1
    peak = max(counts.values()) if counts else 0
    parts = ['<svg viewBox="0 0 1360 560" width="1360" height="560">']
    for row in range(10):
        for col in range(10):
            count = counts.get((col, row), 0)
            fill = ZERO_FILL if count == 0 else _blend(LIGHT_FILL, INDIGO, count / peak)
            text_col = "#ffffff" if count and count / peak > 0.55 else INK
            x, y = grid_x + col * cell, grid_y + row * cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell - 2}" height="{cell - 2}" '
                         f'rx="8" fill="{fill}"/>')
            if count:
                parts.append(f'<text x="{x + cell / 2}" y="{y + cell / 2 + 7}" '
                             f'text-anchor="middle" font-size="20" font-weight="700" '
                             f'fill="{text_col}">{count}</text>')
    for label, pos in (("0", 0.0), ("0.5", 0.5), ("1", 1.0)):
        parts.append(f'<text x="{grid_x + pos * 480 - 6}" y="530" font-size="26" '
                     f'fill="{GREY}">{label}</text>')
        parts.append(f'<text x="{grid_x - 16}" y="{grid_y + pos * 480 + 9}" '
                     f'text-anchor="end" font-size="26" fill="{GREY}">{label}</text>')
    # Discrete colour-scale legend (no gradients: WeasyPrint-safe).
    parts.append(f'<text x="920" y="60" font-size="26" fill="{GREY}">boxes</text>')
    for i in range(5):
        ratio = i / 4
        y = 80 + i * 56
        fill = ZERO_FILL if i == 0 else _blend(LIGHT_FILL, INDIGO, ratio)
        parts.append(f'<rect x="920" y="{y}" width="64" height="40" rx="8" fill="{fill}"/>')
        label = "0" if i == 0 else (str(peak) if i == 4 else "")
        parts.append(f'<text x="1000" y="{y + 28}" font-size="26" fill="{GREY}">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _class_split_heatmap_svg(classes, splits, matrix, class_names) -> str:
    """Grid heatmap: rows = classes, columns = splits, counts in cells."""
    n_rows, n_cols = len(classes), len(splits)
    grid_x, grid_y = 280, 60
    cell_w = min(200, 900 // max(1, n_cols))
    cell_h = min(64, 440 // max(1, n_rows))
    peak = max((v for row in matrix for v in row), default=0)
    label_font = min(28, max(14, cell_h - 6))
    count_font = min(30, max(14, cell_h - 10))
    parts = ['<svg viewBox="0 0 1360 500" width="1360" height="500">']
    for j, split in enumerate(splits):
        cx = grid_x + j * cell_w + cell_w / 2
        parts.append(f'<text x="{cx:.1f}" y="{grid_y - 16}" text-anchor="middle" '
                     f'font-size="26" fill="{GREY}">{_esc(split)}</text>')
    for i, cls in enumerate(classes):
        y = grid_y + i * cell_h
        parts.append(f'<text x="{grid_x - 16}" y="{y + cell_h / 2 + 9:.1f}" '
                     f'text-anchor="end" font-size="{label_font}" fill="{GREY}">'
                     f'{_esc(_short(class_names[i], 20))}</text>')
        for j in range(n_cols):
            count = matrix[i][j]
            fill = ZERO_FILL if count == 0 else _blend(LIGHT_FILL, INDIGO, count / peak)
            text_col = "#ffffff" if count and count / peak > 0.55 else INK
            x = grid_x + j * cell_w
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
                         f'rx="8" fill="{fill}"/>')
            parts.append(f'<text x="{x + cell_w / 2:.1f}" y="{y + cell_h / 2 + 10:.1f}" '
                         f'text-anchor="middle" font-size="{count_font}" '
                         f'font-weight="700" fill="{text_col}">{count}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _venn_svg(counts: dict) -> str:
    """Three-circle RGB Venn, fixed geometry (matches the approved sample)."""
    circles = [
        ("train", 570, 155),
        ("val", 790, 155),
        ("test", 680, 346),
    ]
    # Badge centres per region: (region key, x, y).
    badges = [
        ("train", 480, 155),
        ("val", 880, 155),
        ("test", 680, 415),
        ("train+val", 680, 105),
        ("train+test", 598, 285),
        ("val+test", 762, 285),
        ("train+val+test", 680, 219),
    ]
    label_pos = {"train": (570, 70), "val": (790, 70), "test": (680, 478)}
    parts = ['<svg viewBox="0 0 1360 520" width="1360" height="520">']
    for name, cx, cy in circles:
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="140" fill="{VENN_FILL[name]}" '
                     f'fill-opacity="0.55" stroke="{VENN_STROKE[name]}" stroke-width="4"/>')
    for name, (lx, ly) in label_pos.items():
        parts.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="28" '
                     f'font-weight="700" fill="#ffffff">{name}</text>')
    for key, bx, by in badges:
        value = counts.get(key, 0)
        color = INK if value else GREY
        parts.append(f'<circle cx="{bx}" cy="{by}" r="30" fill="#ffffff" fill-opacity="0.95"/>')
        parts.append(f'<text x="{bx}" y="{by + 12}" text-anchor="middle" font-size="34" '
                     f'font-weight="700" fill="{color}">{value}</text>')
    parts.append("</svg>")
    return "".join(parts)


# --- Venn classification (pure, unit-tested) ----------------------------

_CANONICAL_SPLIT = {"train": "train", "training": "train",
                    "val": "val", "validation": "val", "test": "test"}
_VENN_KEYS = ("train", "val", "test", "train+val", "train+test",
              "val+test", "train+val+test")


def classify_duplicate_groups(detail: list[dict]) -> dict:
    """Count duplicate groups by the set of splits their members touch.

    ``detail`` is ``report["duplicate_groups_detail"]``: each group has
    ``members`` of ``{"path", "split"}`` (kept + removed). A group
    touching only non-standard splits is counted in the total but in
    no region. Returns counts for all 7 Venn regions.
    """
    counts = dict.fromkeys(_VENN_KEYS, 0)
    for group in detail or []:
        touched = set()
        for member in group.get("members", []):
            split = member.get("split") if isinstance(member, dict) else member
            if split in _CANONICAL_SPLIT:
                touched.add(_CANONICAL_SPLIT[split])
        if not touched:
            continue
        key = "+".join(s for s in ("train", "val", "test") if s in touched)
        counts[key] += 1
    return counts


# --- Data loading (unchanged semantics from the previous version) ---

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


def _split_color(split: str) -> str:
    return SPLIT_COLORS.get(split, INDIGO)


def _legend_dots(items) -> str:
    """Footer legend: coloured dots + labels, e.g. ``● train ● val``."""
    out = []
    for label, color in items:
        out.append(f'<span style="color:{color}">●</span> {_esc(label)}')
    return " ".join(out)


def generate_charts(report: dict, records: list[dict], outdir: str | Path) -> dict:
    """Write chart PNGs into ``outdir`` and describe what was made.

    Returns ``{"dir": str, "generated": [filenames],
    "skipped": [{"chart", "reason"}]}``. Charts without data are
    skipped (recorded, not faked with empty plots).
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    skipped: list[dict] = []

    def skip(name: str, reason: str) -> None:
        skipped.append({"chart": name, "reason": reason})

    def make(name, title, subtitle, svg, footer) -> None:
        generated.append(_render(outdir, name, title, subtitle, svg, footer))

    usable = [r for r in records if "md5" in r]
    splits = report["splits_scanned"]
    health = report["health"]
    dist = health["class_distribution"]

    # ---------- Overview ----------
    per_split = Counter(r["split"] for r in records)
    if per_split:
        ordered = [s for s in splits if s in per_split]
        total_images = sum(per_split.values())
        labels = [f"{s} ({100.0 * per_split[s] / total_images:.1f}%)" for s in ordered]
        make("split_sizes.png", "Images per split", f"{total_images} images",
             _bar_svg(labels, [per_split[s] for s in ordered], [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{total_images} images</b>"] +
                         [f"{s} <b>{per_split[s]}</b>" for s in ordered]))
        if len(per_split) > 1:
            make("split_share.png", "Split share", f"{total_images} images",
                 _donut_svg(ordered, [per_split[s] for s in ordered],
                            [_split_color(s) for s in ordered],
                            total_images, "images"),
                 _foot_parts([f"Total <b>{total_images} images</b>"] +
                             [f"{s} <b>{100.0 * per_split[s] / total_images:.1f}%</b>"
                              for s in ordered]))
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
        suffix = " (top 30)" if len(class_totals) > 30 else ""
        total_class_images = sum(class_totals.values())
        make("class_images.png", f"Images per class{suffix}",
             f"{len(class_totals)} classes",
             _bar_svg([str(c) for c, _ in top], [n for _, n in top], [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{total_class_images} images</b>",
                          f"{len(class_totals)} <b>classes</b>"]))
        if len(splits) > 1 and len(class_totals) <= 30:
            classes = sorted(class_totals)
            series = [(s, _split_color(s), [dist.get(s, {}).get(c, 0) for c in classes])
                      for s in splits]
            make("class_split_stacked.png", "Images per class, stacked by split",
                 f"{len(classes)} classes × {len(splits)} splits",
                 _stacked_svg([str(c) for c in classes], series),
                 _foot_parts([_legend_dots([(s, _split_color(s)) for s in splits]),
                              f"Total <b>{total_class_images} images</b>"]))
        else:
            skip("class_split_stacked.png", "needs 2+ splits and <= 30 classes")
    else:
        skip("class_images.png", "no class information")
        skip("class_split_stacked.png", "no class information")

    if usable:
        hist_specs = [
            ("file_size_hist.png", "File size distribution",
             [r["size"] / 1024 for r in usable], "Size in KB", "KB"),
            ("width_hist.png", "Image width distribution",
             [r["width"] for r in usable], "Width in pixels", "px"),
            ("height_hist.png", "Image height distribution",
             [r["height"] for r in usable], "Height in pixels", "px"),
            ("aspect_hist.png", "Aspect ratio distribution (w/h)",
             [r["width"] / r["height"] for r in usable if r["height"]],
             "Aspect ratio (w/h)", ""),
            ("area_hist.png", "Image area distribution",
             [r["width"] * r["height"] / 1e6 for r in usable],
             "Area in megapixels", "MP"),
        ]
        for name, title, values, unit, suffix in hist_specs:
            labels, counts = _hist_bins(values)
            integer_bins = (all(float(v) == int(v) for v in values)
                            and max(values) - min(values) <= 20)
            bin_note = ("one bar per value" if integer_bins else "10 equal-width bins")
            make(name, title,
                 f"{unit} · {len(values)} images · {_fmt_num(min(values))}–{_fmt_num(max(values))}",
                 _bar_svg(labels, counts, [INDIGO, CYAN]),
                 _foot_parts([(f"Range <b>{_fmt_num(min(values))}–{_fmt_num(max(values))}"
                               f"{' ' + suffix if suffix else ''}</b>"),
                              bin_note]))
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
        labels, counts = _hist_bins([float(v) for v in per_image.values()])
        make("instances_per_image.png", "Boxes per image",
             f"{len(per_image)} images · {len(boxes)} boxes",
             _bar_svg(labels, counts, [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{len(boxes)} boxes</b>",
                          f"{len(per_image)} <b>images</b>"]))
        by_class: Counter = Counter(b["class"] for b in boxes)
        top = by_class.most_common(30)
        suffix = " (top 30)" if len(by_class) > 30 else ""
        foot_items = [(class_name(c), n) for c, n in top[:5]]
        make("boxes_per_class.png", f"Boxes per class{suffix}",
             f"{len(boxes)} boxes",
             _bar_svg([class_name(c) for c, _ in top], [n for _, n in top],
                      [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{len(boxes)} boxes</b>"] +
                         [f"{label} <b>{n}</b>" for label, n in foot_items]))
        for name, title, values, unit in [
            ("box_width_hist.png", "Box width distribution",
             [b["w"] for b in boxes], "Fraction of image width"),
            ("box_height_hist.png", "Box height distribution",
             [b["h"] for b in boxes], "Fraction of image height"),
            ("box_area_hist.png", "Box area distribution",
             [b["w"] * b["h"] for b in boxes], "Fraction of image area"),
        ]:
            labels, counts = _hist_bins(values)
            make(name, title, f"{unit} · {len(boxes)} boxes",
                 _bar_svg(labels, counts, [INDIGO, CYAN]),
                 _foot_parts([f"Range <b>{_fmt_num(min(values))}–{_fmt_num(max(values))}</b>",
                              "10 equal-width bins"]))
        sample = _sample(boxes)
        sample_note = (f"Sample of {len(sample)} from {len(boxes)} boxes"
                       if len(sample) < len(boxes) else f"{len(boxes)} boxes")
        make("box_centers_scatter.png", "Box centers (x, y)", sample_note,
             _scatter_svg([(b["x"], b["y"]) for b in sample],
                          [0, 0.25, 0.5, 0.75, 1.0], [0, 0.25, 0.5, 0.75, 1.0],
                          invert_y=True),
             "Centers in normalized [0, 1] coordinates · y grows downward (image space)")
        make("box_centers_heatmap.png", "Box center heatmap",
             f"{len(boxes)} boxes · 10×10 bins",
             _centers_heatmap_svg(boxes),
             _foot_parts([f"Total <b>{len(boxes)} boxes</b>", "darker = more centers"]))
        w_max = max(b["w"] for b in sample)
        h_max = max(b["h"] for b in sample)
        w_step = _nice_step(w_max, target=4)
        h_step = _nice_step(h_max, target=4)
        x_ticks = [round(w_step * i, 6) for i in range(1, math.ceil(w_max / w_step) + 1)]
        y_ticks = [round(h_step * i, 6) for i in range(1, math.ceil(h_max / h_step) + 1)]
        make("box_wh_scatter.png", "Box width vs height", sample_note,
             _scatter_svg([(b["w"], b["h"]) for b in sample], x_ticks, y_ticks,
                          invert_y=False),
             "Width vs height, normalized fractions")
        classes = sorted(by_class)
        if len(splits) > 1 and len(classes) <= 30:
            matrix = [[sum(1 for b in boxes if b["class"] == c and b["split"] == s)
                       for s in splits] for c in classes]
            make("class_split_heatmap.png", "Boxes per class and split",
                 f"{len(classes)} classes × {len(splits)} splits",
                 _class_split_heatmap_svg(classes, splits, matrix,
                                          [class_name(c) for c in classes]),
                 _foot_parts([f"Total <b>{len(boxes)} boxes</b>", "darker = more boxes"]))
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
        total_groups = report["groups_exact"] + report["groups_near"]
        make("dup_by_method.png", "Duplicate groups by method",
             f"{total_groups} duplicate groups",
             _bar_svg(["exact", "near"],
                      [report["groups_exact"], report["groups_near"]],
                      [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{total_groups} groups</b>",
                          f"exact <b>{report['groups_exact']}</b>",
                          f"near <b>{report['groups_near']}</b>"]))
    else:
        skip("dup_by_method.png", "no duplicate groups")
    detail = report.get("duplicate_groups_detail")
    if detail:
        counts = classify_duplicate_groups(detail)
        total = len(detail)
        make("duplicate_groups_venn.png", "Duplicate groups by split overlap",
             "RGB Venn · groups counted by splits touched",
             _venn_svg(counts),
             _foot_parts([_legend_dots([("train", VENN_FILL["train"]),
                                        ("val", VENN_FILL["val"]),
                                        ("test", VENN_FILL["test"])]),
                          f"Total <b>{total} groups</b>"]))
    else:
        skip("duplicate_groups_venn.png", "no duplicate groups")
    removals = report["removals"]
    if removals:
        by_split: Counter = Counter(r["split"] for r in removals)
        ordered = [s for s in splits if s in by_split]
        make("removals_by_split.png", "Removals by split",
             f"{len(removals)} removals",
             _bar_svg(ordered, [by_split[s] for s in ordered], [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{len(removals)} removals</b>"] +
                         [f"{s} <b>{by_split[s]}</b>" for s in ordered]))
        by_reason: Counter = Counter(r["reason"] for r in removals)
        make("removals_by_reason.png", "Removals by reason",
             f"{len(removals)} removals",
             _bar_svg(list(by_reason), list(by_reason.values()), [INDIGO, CYAN]),
             _foot_parts([f"Total <b>{len(removals)} removals</b>"] +
                         [f"{reason} <b>{n}</b>" for reason, n in by_reason.items()]))
    else:
        skip("removals_by_split.png", "no removals")
        skip("removals_by_reason.png", "no removals")
    findings = health["findings"]
    if findings:
        by_check: Counter = Counter(f["check"] for f in findings)
        check_colors = []
        for check in by_check:
            sevs = {f["severity"] for f in findings if f["check"] == check}
            if sevs == {"error"}:
                check_colors.append(RED)
            elif sevs == {"warning"}:
                check_colors.append(AMBER)
            elif sevs == {"info"}:
                check_colors.append(CYAN)
            else:
                check_colors.append(INDIGO)
        counts = health["counts"]
        make("health_by_check.png", "Health findings by check",
             f"{len(findings)} findings",
             _bar_svg(list(by_check), list(by_check.values()), check_colors),
             _foot_parts([f"Total <b>{len(findings)} findings</b>"] +
                         [f"{k} <b>{counts[k]}</b>" for k in ("errors", "warnings", "info")
                          if counts[k] > 0]))
    else:
        skip("health_by_check.png", "no health findings")
    counts = health["counts"]
    sev_labels = [k for k in ("errors", "warnings", "info") if counts[k] > 0]
    if sev_labels:
        make("health_by_severity.png", "Health findings by severity",
             f"{counts['total']} findings",
             _donut_svg(sev_labels, [counts[k] for k in sev_labels],
                        [SEVERITY_COLORS[k] for k in sev_labels],
                        counts["total"], "findings"),
             _foot_parts([f"Total <b>{counts['total']} findings</b>"] +
                         [f"{k} <b>{counts[k]}</b>" for k in sev_labels]))
    else:
        skip("health_by_severity.png", "no health findings")
    if per_split:
        removed_by_split: Counter = Counter(r["split"] for r in removals)
        kept = [per_split.get(s, 0) - removed_by_split.get(s, 0) for s in splits]
        removed = [removed_by_split.get(s, 0) for s in splits]
        total_kept, total_removed = sum(kept), sum(removed)
        make("kept_vs_quarantined.png", "Kept vs quarantined per split",
             f"{total_kept + total_removed} images",
             _stacked_svg(splits, [("kept", INDIGO, kept),
                                   ("quarantined", AMBER, removed)]),
             _foot_parts([_legend_dots([("kept", INDIGO), ("quarantined", AMBER)]),
                          f"Kept <b>{total_kept}</b>",
                          f"quarantined <b>{total_removed}</b>"]))
    else:
        skip("kept_vs_quarantined.png", "no images found")

    return {"dir": str(outdir), "generated": generated, "skipped": skipped}
