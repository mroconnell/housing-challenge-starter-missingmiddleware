"""Offline check that relative links in Markdown files point to real files."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Matches the target of an inline Markdown link: [text](target)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def markdown_files():
    return [p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "node_modules" not in p.parts]


def broken_links(path):
    broken = []
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(SKIP_PREFIXES):
            continue
        file_part = target.split("#", 1)[0]
        if file_part and not (path.parent / file_part).exists():
            broken.append(target)
    return broken


class TestDocsLinks(unittest.TestCase):
    def test_finds_markdown_files(self):
        self.assertTrue(markdown_files())

    def test_relative_links_resolve(self):
        for path in markdown_files():
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertEqual(broken_links(path), [])

    def test_detects_a_broken_link(self):
        tmp = ROOT / "tests" / "_tmp_link_check.md"
        tmp.write_text("[ok](test_docs_links.py) [bad](no_such_file.md)", encoding="utf-8")
        try:
            self.assertEqual(broken_links(tmp), ["no_such_file.md"])
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
