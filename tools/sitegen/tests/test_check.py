"""Tests for the gate's own helpers in check.py.

    python3 -m unittest discover -s tools/sitegen/tests
"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import check as C  # noqa: E402


class PageTextTest(unittest.TestCase):
    def test_visible_text_only(self):
        t = C._Text()
        t.feed('<p>One</p><script>var robust = 1;</script><style>.x{}</style><li>Two</li>'
               '<script type="application/json">{"comprehensive":1}</script>')
        text = "".join(t.out)
        self.assertIn("One", text)
        self.assertIn("Two", text)
        self.assertNotIn("robust", text)
        self.assertNotIn("comprehensive", text)


class VoiceTest(unittest.TestCase):
    def audit(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            f = pathlib.Path(tmp) / "page.md"
            f.write_text(text, encoding="utf-8")
            return C.voice_hits([f])

    def test_banned_words_are_found_with_their_category(self):
        ok, hits = self.audit("A seamless and transformative plan for every stakeholder.\n")
        self.assertTrue(ok)
        self.assertEqual({c for c, _ in hits}, {"puffed-up", "consultant speak"})

    def test_plain_copy_has_no_hits(self):
        self.assertEqual(self.audit("Tick a block only when its output exists.\n")[1], [])

    def test_known_source_hits_still_appear_in_the_source(self):
        # If the owner edits one of these sentences, the entry must be removed here.
        root = C.ROOT / "content/docs/src"
        text = "".join(p.read_text(encoding="utf-8") for p in root.glob("doc*.md"))
        for _, needle, where in C.KNOWN_SOURCE_HITS:
            self.assertIn(needle, text, where)


class DigestTest(unittest.TestCase):
    def test_any_byte_change_under_sources_changes_the_digest(self):
        orig = C.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            C.ROOT = pathlib.Path(tmp)
            try:
                for d in ("content", "downloads"):
                    (C.ROOT / d).mkdir()
                (C.ROOT / "content/a.md").write_text("x")
                (C.ROOT / "downloads/b.docx").write_bytes(b"\x00\x01")
                first = C.source_digest()
                self.assertEqual(first, C.source_digest())
                (C.ROOT / "downloads/b.docx").write_bytes(b"\x00\x02")
                self.assertNotEqual(first, C.source_digest())
            finally:
                C.ROOT = orig


if __name__ == "__main__":
    unittest.main()
