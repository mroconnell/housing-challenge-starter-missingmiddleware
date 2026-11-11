"""The Summary tab's policy box quotes the challenge's benchmark wording (ui/src/benchmarks.ts). Each quote must be
the Participant Handbook's own words: every part of it (split at " … ", which marks a left-out sentence) must appear in
the handbook PDF's text, with line breaks joined and words hyphenated across a line ("single-\\nfamily") rejoined.

The PDF is not committed (it is git-ignored at the repo root). The test reads it from the repo root, or from the path
in HANDBOOK_PDF, and is skipped when neither exists or pdftotext is missing. The quotes are also typed into
ui/tests/summary_policy.spec.ts, which checks the rendered page against them."""
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "ui" / "src" / "benchmarks.ts"
PDF_NAME = "Participant Handbook — Housing Data and Technology Innovation Challenge.pdf"


def quotes() -> dict[str, str]:
    text = BENCH.read_text()
    block = text[text.index("HANDBOOK_BENCHMARK"):]
    return dict(re.findall(r'^\s+(\w+): "([^"]+)",$', block, flags=re.M))


def pdf_path() -> Path | None:
    for p in [os.environ.get("HANDBOOK_PDF"), ROOT / PDF_NAME]:
        if p and Path(p).is_file():
            return Path(p)
    return None


class TestHandbookBenchmarks(unittest.TestCase):
    def test_one_quote_per_reform(self):
        self.assertEqual(sorted(quotes()), ["adu", "middle", "parking", "tod"])

    def test_quotes_match_the_handbook_pdf(self):
        pdf = pdf_path()
        if pdf is None or shutil.which("pdftotext") is None:
            self.skipTest("handbook PDF or pdftotext not available")
        raw = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
        text = re.sub(r"-\n\s*(?=[a-z])", "-", raw)          # "single-\nfamily" -> "single-family"
        text = re.sub(r"\s+", " ", text)
        for key, q in quotes().items():
            for part in q.split(" … "):
                with self.subTest(reform=key, part=part[:40]):
                    self.assertIn(part, text)


if __name__ == "__main__":
    unittest.main()
