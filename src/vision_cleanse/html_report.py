"""Self-contained HTML verification report for duplicate groups.

``write_html_report`` renders one card per duplicate group so a human
can *verify* each kept/removed decision visually: kept images on one
side, removed images on the other, each with its split, label and
removal reason, plus a conflict badge when the group was kept whole
because its members disagree on labels. The file is a single HTML
document: thumbnails are downscaled JPEGs embedded as data URIs, so
it opens anywhere without the dataset next to it. No JavaScript
library is needed; the filter/search script is inline and vanilla.

The report also carries the surrounding context: run summary, health
counts, label diagnostics, the health-findings table and the chart
gallery (when the charts live next to the report).
"""

from __future__ import annotations

import base64
import html
import io
from pathlib import Path

from PIL import Image

MAX_THUMB = 256
MAX_PER_GROUP = 100
MAX_FINDINGS = 200

CSS = """
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:#EDF1F7;color:#1e293b;margin:0;padding:24px}
main{max-width:1200px;margin:0 auto}
h1{font-size:28px;margin:0 0 4px}
.sub{color:#64748b;margin:0 0 20px}
.card{background:#fff;border-radius:16px;padding:20px;margin-bottom:16px;
box-shadow:0 2px 8px rgba(0,0,0,.06)}
.stat{display:inline-block;background:#EEF2FF;border-radius:999px;
padding:6px 14px;margin:0 8px 8px 0;font-size:14px}
.stat b{color:#4F46E5}
.badge{display:inline-block;border-radius:999px;padding:2px 10px;
font-size:12px;font-weight:700}
.badge.exact{background:#DCFCE7;color:#166534}
.badge.near{background:#FEF3C7;color:#92400E}
.badge.conflict{background:#FEE2E2;color:#991B1B}
.badge.kept{border:2px solid #16A34A;color:#166534}
.badge.removed{border:2px solid #D97706;color:#92400E}
.group{border:1px solid #E2E8F0}
.group h2{font-size:18px;margin:0 0 8px}
figure{display:inline-block;vertical-align:top;width:270px;margin:0 12px 12px 0}
figure img{width:100%;border-radius:12px;display:block}
figure.kept img{outline:3px solid #16A34A}
figure.removed img{outline:3px solid #D97706}
figcaption{font-size:13px;margin-top:6px;word-break:break-all}
figcaption .path{color:#64748b;display:block;font-size:12px}
figcaption .reason{color:#92400E}
.nothumb{background:#F1F5F9;border-radius:12px;height:160px;
display:flex;align-items:center;justify-content:center;color:#64748b}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid #E2E8F0;text-align:left;padding:6px 8px;
vertical-align:top}
.toolbar label{margin-right:16px;font-size:14px}
.toolbar input,.toolbar select{padding:6px 10px;border-radius:8px;
border:1px solid #CBD5E1;font-size:14px}
.note{color:#64748b;font-size:13px}
"""

JS = """
function applyFilter(){
  const method = document.getElementById('f-method').value;
  const confOnly = document.getElementById('f-conflict').checked;
  const q = document.getElementById('f-search').value.toLowerCase();
  document.querySelectorAll('section.group').forEach(card => {
    let show = true;
    if (method !== 'all' && card.dataset.method !== method) show = false;
    if (confOnly && card.dataset.conflict !== '1') show = false;
    if (q && !card.dataset.text.includes(q)) show = false;
    card.style.display = show ? '' : 'none';
  });
}
document.getElementById('f-method').addEventListener('change', applyFilter);
document.getElementById('f-conflict').addEventListener('change', applyFilter);
document.getElementById('f-search').addEventListener('input', applyFilter);
"""


def _thumb_data_uri(path: str) -> str | None:
    """Downscaled JPEG thumbnail as a data URI, or None if unreadable."""
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((MAX_THUMB, MAX_THUMB))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=65)
            return "data:image/jpeg;base64," + base64.b64encode(
                buf.getvalue()
            ).decode("ascii")
    except Exception:  # noqa: BLE001 - unreadable image: show a placeholder
        return None


def _figure(path: str, role: str, split: str, label: str, reason: str = "") -> str:
    uri = _thumb_data_uri(path)
    if uri:
        media = f'<img src="{uri}" alt="{html.escape(Path(path).name)}" loading="lazy">'
    else:
        media = '<div class="nothumb">Không đọc được ảnh</div>'
    reason_html = (
        f'<div class="reason">{html.escape(reason)}</div>' if reason else ""
    )
    meta = f"{html.escape(split)} · {html.escape(label)}" if label else html.escape(split)
    return (
        f'<figure class="{role}"><div>{media}</div>'
        f"<figcaption><b>{html.escape(Path(path).name)}</b>"
        f"<span class=\"path\">{meta}</span>{reason_html}"
        f"<span class=\"path\">{html.escape(path)}</span></figcaption></figure>"
    )


def write_html_report(report_dir: str | Path, report: dict, records: list[dict]) -> Path:
    """Write ``report.html`` next to ``report.json``; return its path."""
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    rec_by_path = {str(r["path"]): r for r in records}
    removal_reason = {r["path"]: r.get("reason", "") for r in report.get("removals", [])}

    health = report.get("health", {}) or {}
    counts = health.get("counts", {}) or {}
    diag = health.get("label_diagnostics") or {}
    groups = report.get("groups", [])

    parts: list[str] = []
    parts.append(
        "<!DOCTYPE html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
        "<title>VisionCleanse — kiểm tra nhóm trùng lặp</title>"
        f"<style>{CSS}</style></head><body><main>"
    )
    parts.append(
        "<h1>VisionCleanse — kiểm tra nhóm trùng lặp</h1>"
        "<p class=\"sub\">Ảnh <b>giữ lại</b> viền xanh, ảnh <b>chuyển quarantine</b> "
        "viền cam kèm lý do. Nhóm có xung đột nhãn được giữ nguyên toàn bộ "
        "để rà soát, không tự xóa.</p>"
    )
    stats = [
        ("Ảnh đã quét", report.get("images_found", 0)),
        ("Nhóm exact", report.get("groups_exact", 0)),
        ("Nhóm near", report.get("groups_near", 0)),
        ("Chuyển quarantine", report.get("to_quarantine", 0)),
        ("Xung đột nhãn", report.get("label_conflicts", 0)),
        ("Health lỗi", counts.get("errors", 0)),
        ("Health cảnh báo", counts.get("warnings", 0)),
    ]
    parts.append(
        '<div class="card">' + "".join(
            f'<span class="stat">{html.escape(str(k))}: <b>{v}</b></span>'
            for k, v in stats
        )
    )
    if diag:
        rate = diag.get("empty_label_rate")
        rate_txt = f"{100.0 * rate:.1f}%" if rate is not None else "—"
        unknown = ", ".join(map(str, diag.get("unknown_class_ids", []))) or "—"
        parts.append(
            "<p class=\"note\">Chẩn đoán nhãn: "
            f"{diag.get('label_files', 0)} file, {diag.get('lines_scanned', 0)} dòng, "
            f"{diag.get('malformed_lines', 0)} dòng sai định dạng, "
            f"{diag.get('empty_label_files', 0)} file rỗng ({rate_txt}), "
            f"class id ngoài names: {html.escape(unknown)}.</p>"
        )
    parts.append("</div>")

    charts_dir = report_dir / "charts"
    charts = report.get("charts", {}) or {}
    made = charts.get("generated", []) if isinstance(charts, dict) else []
    shown = [c for c in made if (charts_dir / c).is_file()]
    if shown:
        parts.append('<div class="card"><h2>Biểu đồ</h2>')
        for name in shown:
            parts.append(
                f'<figure style="width:360px"><div>'
                f'<img src="charts/{html.escape(name)}" alt="{html.escape(name)}" loading="lazy">'
                f"</div><figcaption>{html.escape(name)}</figcaption></figure>"
            )
        parts.append("</div>")

    parts.append(
        '<div class="card toolbar"><label>Phương pháp: '
        '<select id="f-method"><option value="all">Tất cả</option>'
        '<option value="exact">exact</option><option value="near">near</option>'
        "</select></label><label><input type=\"checkbox\" id=\"f-conflict\"> "
        "Chỉ nhóm xung đột</label><label> Tìm: "
        '<input type="search" id="f-search" placeholder="tên file, nhóm…">'
        "</label></div>"
    )

    for g in groups:
        kept = g.get("kept", [])
        removed = g.get("removed", [])
        conflict = bool(g.get("conflict"))
        members = [str(p) for p in kept] + [str(p) for p in removed]
        search_text = html.escape(" ".join(members + [str(g.get("group_id", ""))])).lower()
        badges = (
            f'<span class="badge {g.get("method", "")}">{html.escape(str(g.get("method", "")))}</span> '
        )
        if conflict:
            badges += '<span class="badge conflict">xung đột nhãn — giữ nguyên</span> '
        parts.append(
            f'<section class="card group" data-method="{html.escape(str(g.get("method", "")))}" '
            f'data-conflict="{"1" if conflict else "0"}" data-text="{search_text}">'
            f"<h2>Nhóm #{g.get('group_id')} {badges}</h2>"
        )
        shown_members = 0
        for path in kept:
            if shown_members >= MAX_PER_GROUP:
                break
            rec = rec_by_path.get(str(path), {})
            parts.append(
                _figure(str(path), "kept", rec.get("split", ""), rec.get("label", ""))
            )
            shown_members += 1
        for path in removed:
            if shown_members >= MAX_PER_GROUP:
                break
            rec = rec_by_path.get(str(path), {})
            parts.append(
                _figure(
                    str(path),
                    "removed",
                    rec.get("split", ""),
                    rec.get("label", ""),
                    removal_reason.get(str(path), ""),
                )
            )
            shown_members += 1
        total_members = len(kept) + len(removed)
        if total_members > MAX_PER_GROUP:
            parts.append(
                f"<p class=\"note\">Nhóm có {total_members} ảnh, chỉ hiển thị "
                f"{MAX_PER_GROUP} ảnh đầu — xem đủ danh sách trong report.json.</p>"
            )
        if conflict:
            parts.append(
                "<p class=\"note\">Nhóm xung đột: các ảnh giống nhau nhưng nhãn "
                "khác nhau nên không tự xóa ảnh nào.</p>"
            )
        parts.append("</section>")

    findings = health.get("findings", [])
    if findings:
        parts.append('<div class="card"><h2>Health findings</h2><table>'
                     "<tr><th>Check</th><th>Mức</th><th>File</th><th>Chi tiết</th></tr>")
        for f in findings[:MAX_FINDINGS]:
            parts.append(
                "<tr><td>" + html.escape(str(f.get("check", ""))) + "</td><td>"
                + html.escape(str(f.get("severity", ""))) + "</td><td>"
                + html.escape(str(f.get("path", ""))) + "</td><td>"
                + html.escape(str(f.get("detail", ""))) + "</td></tr>"
            )
        parts.append("</table>")
        if len(findings) > MAX_FINDINGS:
            parts.append(
                f"<p class=\"note\">Hiển thị {MAX_FINDINGS}/{len(findings)} findings — "
                "xem đủ trong report.json.</p>"
            )
        parts.append("</div>")

    parts.append(
        "<p class=\"note\">Báo cáo chi tiết dạng máy: "
        '<a href="report.json">report.json</a></p>'
        f"<script>{JS}</script></main></body></html>"
    )
    out = report_dir / "report.html"
    out.write_text("".join(parts), encoding="utf-8")
    return out
