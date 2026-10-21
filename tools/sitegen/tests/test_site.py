"""Tests for the generated learning path, copy blocks, metadata and /check/.

    python3 -m unittest discover -s tools/sitegen/tests

Each test class builds the site into its own temporary directory, so running the
tests never touches _site/.
"""
import json
import pathlib
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from html import unescape
from io import StringIO

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sitegen as S  # noqa: E402

ROOT = S.ROOT


def build(tmp, site_url=""):
    S.SITE = pathlib.Path(tmp)
    S._manifests.clear()
    with redirect_stdout(StringIO()):
        rc = S.main([f"--site-url={site_url}"] if site_url else [])
    assert rc == 0, rc
    return S.SITE


def read(site, route):
    return (site / route.strip("/") / "index.html").read_text(encoding="utf-8") if route.strip("/") \
        else (site / "index.html").read_text(encoding="utf-8")


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.site = build(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()


class LearningPathTest(SiteTest):
    def test_weeks_follow_the_documented_order(self):
        path = S.learning_path()
        self.assertEqual([w["n"] for w in path], list(range(0, 22)))

    def test_first_four_weeks_are_complete_blocks(self):
        # AC-2: Week 0 plus Weeks 1-4 can be followed from the site alone.
        for w in S.learning_path()[:5]:
            self.assertEqual(w["source"], "blocks", w["n"])
            self.assertGreaterEqual(len(w["acts"]), 4, w["n"])
            for a in w["acts"]:
                self.assertTrue(a["time"] and a["do"] and a["out"], a)

    def test_every_week_has_an_activity(self):
        for w in S.learning_path():
            self.assertTrue(w["acts"], f"week {w['n']} has nothing to tick")

    def test_weeks_without_a_block_table_use_their_tracker_rows(self):
        path = {w["n"]: w for w in S.learning_path()}
        art = S.tracker()["artefacts"]
        for n in (20, 21):
            self.assertEqual(path[n]["source"], "tracker")
            for a in path[n]["acts"]:
                self.assertIn(a["k"], art["keys"])

    def test_keys_are_unique_and_traceable_to_a_doc2_row(self):
        path = S.learning_path()
        keys = [a["k"] for w in path for a in w["acts"]]
        self.assertEqual(len(keys), len(set(keys)))
        source_rows = {}
        for b in S.blocks("doc2"):
            if b["t"] == "table":
                for k, row in zip(b["keys"], b["rows"]):
                    source_rows[k] = row
        for w in path:
            for a in w["acts"]:
                row = source_rows[a["k"]]
                self.assertEqual(a["do"], S.plain_text(row[1]))
                if w["source"] == "blocks":
                    self.assertEqual((a["time"], a["out"]),
                                     (S.plain_text(row[0]), S.plain_text(row[2])))

    def test_every_activity_has_a_tick_on_its_week_page(self):
        for w in S.learning_path():
            html = read(self.site, w["url"])
            for a in w["acts"]:
                self.assertIn(f'data-tick="{a["k"]}"', html, (w["n"], a["k"]))
                self.assertIn(f'id="{a["k"]}"', html)

    def test_manifest_matches_the_path(self):
        m = json.loads(re.search(r'<script type="application/json" id="hr-path">(.*?)</script>',
                                 read(self.site, "/"), re.S).group(1))
        self.assertEqual([w[0] for w in m["weeks"]], [w["n"] for w in S.learning_path()])
        self.assertEqual(len(m["weeks"][0]), 4, "home page carries activity words")
        compact = json.loads(re.search(r'id="hr-path">(.*?)</script>',
                                       read(self.site, "/2/plan/week/3/"), re.S).group(1))
        self.assertEqual(len(compact["weeks"][0]), 3, "other pages carry keys only")

    def test_controls_are_hidden_without_javascript(self):
        html = read(self.site, "/2/plan/week/1/")
        for tag in re.findall(r"<button[^>]*data-tick[^>]*>", html):
            self.assertIn(" hidden", tag)
        self.assertRegex(read(self.site, "/"), r"<section[^>]*data-next hidden")
        self.assertRegex(read(self.site, "/2/plan/"), r"<section[^>]*data-progress hidden")

    def test_start_action_points_at_week_0(self):
        self.assertIn('data-start href="/2/plan/week/0/"', read(self.site, "/"))

    def test_tracker_tables_have_ticks(self):
        html = read(self.site, "/2/plan/")
        t = S.tracker()
        for k in t["courses"]["keys"] + t["artefacts"]["keys"]:
            self.assertIn(f'data-tick="{k}"', html)


class GlossaryTest(SiteTest):
    def test_search_box_ships_hidden_above_the_full_term_table(self):
        html = read(self.site, "/1/start-here/")
        self.assertRegex(html, r'<div class="glossary-search" data-glossary hidden>')
        table = re.search(r'data-glossary-table>(.*?)</table>', html, re.S).group(1)
        rows = next(b["rows"] for b in S.blocks("doc1") if b["t"] == "table" and b["head"][0] == "Term")
        self.assertEqual(table.count("<tr"), len(rows) + 1)  # + the header row
        self.assertIn('<label for="glossary-q">', html)

    def test_script_loads_only_where_the_glossary_is(self):
        for p in self.site.rglob("index.html"):
            h = p.read_text(encoding="utf-8")
            self.assertEqual("glossary.js" in h, "data-glossary-table" in h, p)


class LibraryTest(SiteTest):
    def approved(self):
        return json.loads(S.VERDICTS_FILE.read_text(encoding="utf-8"))["cards"]

    def test_every_sticker_is_the_approved_verdict(self):
        approved = self.approved()
        for c in S.cards():
            html = read(self.site, f"/3/library/{c['id']}/")
            found = re.findall(r'class="sticker sticker-([a-z-]+)"', html)
            want = [approved[c["id"]]["verdict"]] if c["id"] in approved else []
            self.assertEqual(found, want, c["id"])

    def test_a_card_without_a_verdict_gets_no_sticker_and_no_guess(self):
        html = read(self.site, "/3/library/")
        li = re.search(r'<li class="card res-card" data-section="3\.3" data-cost="">.*?</li>', html, re.S)
        self.assertIsNotNone(li)
        self.assertNotIn("sticker", li.group(0))

    def test_every_basis_is_still_on_its_card(self):
        by_id = {c["id"]: c for c in S.cards()}
        for cid, v in self.approved().items():
            self.assertIn(v["basis"], S.card_text(by_id[cid]), cid)

    def test_cards_are_grouped_under_doc3_sections(self):
        html = read(self.site, "/3/library/")
        for key in ("3.1", "3.2", "3.3"):
            self.assertIn(f'data-lib-section="{key}"', html)
        self.assertEqual(html.count('class="card res-card"'), len(S.cards()))

    def test_filter_ships_hidden_and_offers_only_used_labels(self):
        html = read(self.site, "/3/library/")
        self.assertRegex(html, r'<div class="lib-filter" data-lib-filter hidden role="group"')
        used = set(self.approved()[k]["verdict"] for k in self.approved())
        offered = set(re.findall(r'<select name="cost">(.*?)</select>', html, re.S)[0].split('value="')[2:])
        self.assertEqual({o.split('"')[0] for o in offered}, used)

    def test_script_loads_only_on_the_library(self):
        for p in self.site.rglob("index.html"):
            h = p.read_text(encoding="utf-8")
            self.assertEqual("library.js" in h, "data-lib-filter" in h, p)


class VerdictValidationTest(unittest.TestCase):
    def check(self, cards):
        orig = S.VERDICTS_FILE
        with tempfile.TemporaryDirectory() as tmp:
            f = pathlib.Path(tmp) / "v.json"
            f.write_text(json.dumps({"cards": cards}), encoding="utf-8")
            S.VERDICTS_FILE = f
            S._verdicts.clear()
            try:
                return dict(S.verdicts())
            finally:
                S.VERDICTS_FILE = orig
                S._verdicts.clear()

    def test_unknown_card_fails_the_build(self):
        with self.assertRaises(SystemExit):
            self.check({"no-such-card": {"verdict": "paid", "basis": "x"}})

    def test_unknown_verdict_fails_the_build(self):
        with self.assertRaises(SystemExit):
            self.check({"jobberman-nigeria": {"verdict": "cheap", "basis": "free for jobseekers"}})

    def test_reworded_card_fails_the_build(self):
        with self.assertRaises(SystemExit):
            self.check({"jobberman-nigeria": {"verdict": "free-to-use", "basis": "free forever"}})

    def test_valid_entry_loads(self):
        self.assertEqual(self.check({"jobberman-nigeria": {"verdict": "free-to-use",
                                                           "basis": "free for jobseekers"}}),
                         {"jobberman-nigeria": "free-to-use"})


class SqueezeTest(unittest.TestCase):
    def test_strings_survive_untouched(self):
        src = 'var a = "x  ,  y // not a comment /* nor this */";\nsay( \'it\\\'s  fine\' );\n'
        out = S.squeeze_js(src)
        self.assertIn('"x  ,  y // not a comment /* nor this */"', out)
        self.assertIn("'it\\'s  fine'", out)

    def test_comments_and_spaces_go_but_words_stay_apart(self):
        out = S.squeeze_js("/* head */\n// line\nvar  total = a + b;\nreturn x;\n")
        self.assertEqual(out, "var total=a+b;return x;\n")

    def test_line_break_after_a_closing_brace_is_kept(self):
        self.assertIn("}\n(", S.squeeze_js("function f() {}\n(g)();\n"))

    def test_inline_comment_is_a_build_error(self):
        with self.assertRaises(ValueError):
            S.squeeze_js("var a = 1; // trailing\n")


class CopyTest(SiteTest):
    def payloads(self, route):
        html = read(self.site, route)
        return [unescape(p) for p in re.findall(r'data-copy="([^"]*)"', html)]

    def test_every_doc5_template_is_copyable(self):
        quotes = [b for b in S.blocks("doc5") if b["t"] == "quote"]
        self.assertEqual(len(self.payloads("/5/getting-the-job/")), len(quotes))

    def test_payload_is_the_source_text_with_its_line_breaks(self):
        note = next(b for b in S.blocks("doc5") if b["t"] == "quote" and b["text"].startswith("Dear"))
        expected = "\n".join(S.plain_text(x) for x in note["lines"])
        self.assertIn(expected, self.payloads("/5/getting-the-job/"))
        lines = expected.split("\n")
        self.assertEqual(lines[0], "Dear [Hiring team / name],")
        self.assertEqual(lines[-1], "[Name] · [phone] · [portfolio link]")
        self.assertNotIn("**", expected)

    def test_payload_carries_no_interface_text(self):
        for route in ("/5/getting-the-job/", "/5/templates/", "/4/nigeria/law-card/"):
            for p in self.payloads(route):
                self.assertNotRegex(p, r"\bCopy\b|</?[a-z]+[ >]")

    def test_law_card_is_copyable_verbatim(self):
        code = next(b for b in S.blocks("doc4") if b["t"] == "code")
        self.assertIn("\n".join(code["lines"]), self.payloads("/4/nigeria/law-card/"))

    def test_plan_callouts_are_not_turned_into_templates(self):
        self.assertNotIn("copy-btn", read(self.site, "/2/plan/week/1/"))
        self.assertNotIn("copy-btn", read(self.site, "/1/start-here/"))

    def test_plain_text_drops_marks_not_words(self):
        self.assertEqual(S.plain_text("Your advert for **[role]** asks for *x* and [Saylor](https://x.org) `AND`"),
                         "Your advert for [role] asks for x and Saylor AND")


class MetadataTest(SiteTest):
    def heads(self):
        out = {}
        for p in self.site.rglob("index.html"):
            h = p.read_text(encoding="utf-8")
            out[p.relative_to(self.site).as_posix()] = (
                re.search(r"<title>(.*?)</title>", h).group(1),
                re.search(r'<meta name="description" content="([^"]*)"', h).group(1))
        return out

    def test_titles_are_unique(self):
        titles = [t for t, _ in self.heads().values()]
        self.assertEqual(len(titles), len(set(titles)))

    def test_every_page_has_a_description_of_search_length(self):
        for route, (_, d) in self.heads().items():
            self.assertTrue(d.strip(), route)
            self.assertLessEqual(len(d), 200, route)

    def test_no_canonical_or_sitemap_without_a_domain(self):
        self.assertNotIn('rel="canonical"', read(self.site, "/"))
        self.assertFalse((self.site / "sitemap.xml").exists())
        self.assertNotIn("Sitemap:", (self.site / "robots.txt").read_text())

    def test_legal_pages_carry_the_r7_note_and_others_do_not(self):
        for route in ("/4/nigeria/", "/4/nigeria/law-card/"):
            self.assertIn(S.LEGAL_NOTE, read(self.site, route), route)
        for route in ("/", "/2/plan/week/10/", "/5/getting-the-job/", "/3/library/"):
            self.assertNotIn(S.LEGAL_NOTE, read(self.site, route), route)

    def test_priority_questions_have_substantive_pages(self):
        law = read(self.site, "/4/nigeria/")
        self.assertIn("section 11", law)
        self.assertIn("Labour Act", re.search(r"<title>(.*?)</title>", law).group(1))
        self.assertIn("Free HR courses", re.search(r"<title>(.*?)</title>",
                                                   read(self.site, "/3/library/")).group(1))
        self.assertIn("recruitment dashboard", read(self.site, "/2/plan/week/17/"))


class DomainTest(unittest.TestCase):
    def test_canonical_and_sitemap_with_a_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = build(tmp, "https://example.org")
            self.assertIn('<link rel="canonical" href="https://example.org/2/plan/week/4/">',
                          read(site, "/2/plan/week/4/"))
            sm = (site / "sitemap.xml").read_text()
            self.assertEqual(sm.count("<url>"), len(list(site.rglob("index.html"))))
            self.assertIn("Sitemap: https://example.org/sitemap.xml", (site / "robots.txt").read_text())
        S.SITE_URL = ""

    def test_bad_domain_is_refused(self):
        with redirect_stdout(StringIO()):
            self.assertEqual(S.main(["--site-url=example.org/path"]), 2)
        S.SITE_URL = ""


class CheckPageTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig = S.CHECKS_FILE

    def tearDown(self):
        S.CHECKS_FILE = self._orig
        self._tmp.cleanup()

    def test_all_document_links_are_listed(self):
        found = set()
        for name in S.DOCS:
            text = (ROOT / S.DOCS[name]).read_text(encoding="utf-8")
            found |= {u.rstrip(".,;:") for u in re.findall(r"https?://[^\s)|*>`\"]+", text)}
        self.assertEqual(set(S.link_sources()), found)

    def test_without_a_sweep_nothing_is_claimed(self):
        S.CHECKS_FILE = pathlib.Path(self._tmp.name) / "missing.json"
        site = build(self._tmp.name + "/site")
        html = read(site, "/check/")
        self.assertIn("No sweep recorded yet", html)
        self.assertNotIn("Reachable", html)
        self.assertEqual(html.count("Not yet checked"), len(S.link_sources()))

    def test_recorded_results_are_labelled_honestly(self):
        urls = list(S.link_sources())
        f = pathlib.Path(self._tmp.name) / "links.json"
        f.write_text(json.dumps({"run": {"finished": "2026-10-21T10:00:00+00:00"}, "links": [
            {"url": urls[0], "outcome": "failed", "status": 404, "checked_at": "2026-10-21T10:00:00+00:00"},
            {"url": urls[1], "outcome": "inconclusive", "status": 403, "checked_at": "2026-10-21T10:00:01+00:00"},
            {"url": urls[2], "outcome": "redirected", "status": 200, "final_url": "https://new.example/",
             "checked_at": "2026-10-21T10:00:02+00:00",
             "previous": {"outcome": "ok", "status": 200, "checked_at": "2026-07-01T00:00:00+00:00"}},
        ]}))
        S.CHECKS_FILE = f
        html = read(build(self._tmp.name + "/site"), "/check/")
        self.assertIn("Last sweep: 2026-10-21", html)
        self.assertIn('status-failed">Failed</span> (404)', html)
        self.assertIn('status-inconclusive">Inconclusive</span> (403)', html)
        self.assertIn("now at https://new.example/", html)
        self.assertIn("<td>Reachable</td>", html)  # the previous result
        self.assertEqual(html.count("Not yet checked"), len(urls) - 3)

    def test_every_source_page_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = build(tmp)
            for url, where in S.link_sources().items():
                for w in where:
                    route = w["page"].split("#")[0]
                    self.assertTrue((site / route.strip("/") / "index.html").exists(), (url, route))


if __name__ == "__main__":
    unittest.main()
