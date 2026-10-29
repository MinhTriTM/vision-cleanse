"""Tests for vi/en/zh messages."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from helpers import gradient
from vision_cleanse import clean, t
from vision_cleanse.cli import main as cli_main
from vision_cleanse.i18n import normalize_lang


class TestI18n(unittest.TestCase):
    def test_all_languages_have_messages(self):
        for lang in ("vi", "en", "zh"):
            self.assertTrue(t("scanned", lang, n=3))
            self.assertTrue(t("health_title", lang))

    def test_languages_differ(self):
        texts = {t("scanned", lang, n=3) for lang in ("vi", "en", "zh")}
        self.assertEqual(len(texts), 3)

    def test_normalize_and_fallback(self):
        self.assertEqual(normalize_lang("zh-CN"), "zh")
        self.assertEqual(normalize_lang("vi-VN"), "vi")
        self.assertEqual(normalize_lang("xx"), "en")
        self.assertEqual(t("scanned", "xx", n=1), t("scanned", "en", n=1))

    def test_report_lang_normalized(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            d = tmp / "ds" / "train"
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy(gradient(tmp / "g.png"), d / "a.png")
            rep = clean(tmp / "ds", dry_run=True, lang="zh-CN")
            self.assertEqual(rep["lang"], "zh")
        finally:
            shutil.rmtree(tmp)


class TestCliLang(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "dataset"
        d = self.root / "train"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(gradient(self.tmp / "g.png"), d / "a.png")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _run_cli(self, lang):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main([str(self.root), "--lang", lang,
                           "--report-dir", str(self.tmp / "rep")])
        self.assertEqual(rc, 0)
        return buf.getvalue()

    def test_cli_english(self):
        self.assertIn("Scanned:", self._run_cli("en"))

    def test_cli_chinese(self):
        self.assertIn("已扫描", self._run_cli("zh"))


if __name__ == "__main__":
    unittest.main()
