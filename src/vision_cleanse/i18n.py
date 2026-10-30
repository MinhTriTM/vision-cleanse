"""Multilingual user-facing messages (Vietnamese / English / Chinese).

Report JSON keys stay in English for machine readability; only the
human-readable CLI summary and health-check titles are localized.
Use :func:`t` everywhere a message is printed.
"""

from __future__ import annotations

MESSAGES = {
    "vi": {
        "mode_dry": "DRY-RUN (không di chuyển file)",
        "mode_apply": "APPLY (file đã chuyển vào quarantine)",
        "scanned": "Đã quét: {n} ảnh",
        "missing_splits": "Split thiếu (đã bỏ qua): {s}",
        "unreadable": "File không đọc được (đã bỏ qua): {n}",
        "dup_groups": "Nhóm trùng lặp: {n} ({exact} exact, {near} near)",
        "to_quarantine": "Cần quarantine: {n}",
        "conflicts": "Xung đột nhãn (giữ lại, cần rà soát): {n}",
        "report": "Báo cáo: {p}",
        "html_report": "Báo cáo HTML (xem từng nhóm trùng): {p}",
        "conflicts_file": "File xung đột: {p}",
        "quarantine_dir": "Quarantine: {p} (manifest: {m})",
        "coco_sync": "Đồng bộ COCO: {j}",
        "charts_done": "Biểu đồ: {n} file trong {p}",
        "health_title": "Kiểm tra sức khỏe dataset",
        "health_ok": "Đạt: không phát hiện vấn đề",
        "health_issues": "Phát hiện {n} vấn đề ({e} lỗi, {w} cảnh báo)",
        "check_zero_byte": "File rỗng (0 byte)",
        "check_corrupt": "File hỏng, không đọc được",
        "check_blank": "Ảnh trơn/đơn sắc (nghi là ảnh trắng)",
        "check_tiny": "Ảnh quá nhỏ",
        "check_other_file": "File lạ trong thư mục split",
        "check_missing_label": "Ảnh thiếu nhãn YOLO",
        "check_orphan_label": "Nhãn YOLO không có ảnh tương ứng",
        "check_invalid_label": "Nhãn YOLO sai định dạng",
        "check_empty_label": "Nhãn YOLO rỗng",
        "check_unknown_class": "Nhãn YOLO chứa class id ngoài data.yaml",
        "label_diag": "Chẩn đoán nhãn: {files} file, {lines} dòng, {malformed} dòng sai định dạng, {empty} file rỗng ({rate}), class id ngoài names: {unknown}",
        "check_dup_basename": "Trùng tên file nhưng nội dung khác nhau",
        "check_test_internal_dup": "Trùng lặp trong nội bộ tập test",
    },
    "en": {
        "mode_dry": "DRY-RUN (no files moved)",
        "mode_apply": "APPLY (files moved to quarantine)",
        "scanned": "Scanned: {n} images",
        "missing_splits": "Missing splits (skipped): {s}",
        "unreadable": "Unreadable files (skipped): {n}",
        "dup_groups": "Duplicate groups: {n} ({exact} exact, {near} near)",
        "to_quarantine": "To quarantine: {n}",
        "conflicts": "Label conflicts (kept, needs review): {n}",
        "report": "Report: {p}",
        "html_report": "HTML report (inspect each duplicate group): {p}",
        "conflicts_file": "Conflicts: {p}",
        "quarantine_dir": "Quarantine: {p} (manifest: {m})",
        "coco_sync": "COCO sync: {j}",
        "charts_done": "Charts: {n} files in {p}",
        "health_title": "Dataset health checks",
        "health_ok": "Pass: no issues found",
        "health_issues": "Found {n} issues ({e} errors, {w} warnings)",
        "check_zero_byte": "Empty file (0 bytes)",
        "check_corrupt": "Corrupt / unreadable file",
        "check_blank": "Blank / solid-color image (possibly empty)",
        "check_tiny": "Image too small",
        "check_other_file": "Unexpected file inside split dir",
        "check_missing_label": "Image missing YOLO label",
        "check_orphan_label": "YOLO label without matching image",
        "check_invalid_label": "YOLO label malformed",
        "check_empty_label": "YOLO label empty",
        "check_unknown_class": "YOLO label class id outside data.yaml",
        "label_diag": "Label diagnostics: {files} files, {lines} lines, {malformed} malformed lines, {empty} empty files ({rate}), class ids outside names: {unknown}",
        "check_dup_basename": "Same filename, different content",
        "check_test_internal_dup": "Duplicates inside the test set",
    },
    "zh": {
        "mode_dry": "演练模式（未移动任何文件）",
        "mode_apply": "已执行（文件已移至隔离区）",
        "scanned": "已扫描：{n} 张图片",
        "missing_splits": "缺失的数据集划分（已跳过）：{s}",
        "unreadable": "无法读取的文件（已跳过）：{n}",
        "dup_groups": "重复组：{n}（{exact} 个完全相同，{near} 个近似重复）",
        "to_quarantine": "待隔离：{n}",
        "conflicts": "标签冲突（已保留，需人工复核）：{n}",
        "report": "报告：{p}",
        "html_report": "HTML 报告（逐组检查重复图片）：{p}",
        "conflicts_file": "冲突文件：{p}",
        "quarantine_dir": "隔离区：{p}（清单：{m}）",
        "coco_sync": "COCO 同步：{j}",
        "charts_done": "图表：{p} 中有 {n} 个文件",
        "health_title": "数据集健康检查",
        "health_ok": "通过：未发现问题",
        "health_issues": "发现 {n} 个问题（{e} 个错误，{w} 个警告）",
        "check_zero_byte": "空文件（0 字节）",
        "check_corrupt": "损坏/无法读取的文件",
        "check_blank": "空白/纯色图片（疑似空图）",
        "check_tiny": "图片过小",
        "check_other_file": "划分目录中的异常文件",
        "check_missing_label": "图片缺失 YOLO 标签",
        "check_orphan_label": "YOLO 标签无对应图片",
        "check_invalid_label": "YOLO 标签格式错误",
        "check_empty_label": "YOLO 标签为空",
        "check_unknown_class": "YOLO 标签包含超出 data.yaml 的类别 id",
        "label_diag": "标签诊断：{files} 个文件，{lines} 行，{malformed} 行格式错误，{empty} 个空文件（{rate}），超出 names 的类别 id：{unknown}",
        "check_dup_basename": "同名文件但内容不同",
        "check_test_internal_dup": "测试集内部重复",
    },
}

SUPPORTED = ("vi", "en", "zh")


def normalize_lang(lang: str | None) -> str:
    """Map 'vi-VN', 'zh-CN', ... to 'vi' / 'zh'; unknown -> 'en'."""
    if not lang:
        return "vi"
    code = lang.lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED else "en"


def t(key: str, lang: str | None = "vi", **kwargs) -> str:
    """Localized message for ``key``; falls back to English, then the key."""
    table = MESSAGES.get(normalize_lang(lang), MESSAGES["en"])
    template = table.get(key, MESSAGES["en"].get(key, key))
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
