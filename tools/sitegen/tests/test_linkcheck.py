"""Tests for linkcheck.py: the outcome rules, and real requests to a local server.

    python3 -m unittest discover -s tools/sitegen/tests

No request leaves the machine: the server is 127.0.0.1 on a random port.
"""
import http.server
import json
import os
import pathlib
import socket
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import linkcheck as L  # noqa: E402
import report_worsened as W  # noqa: E402


class ClassifyTest(unittest.TestCase):
    def test_only_404_and_410_count_as_failed(self):
        self.assertEqual(L.classify(404), "failed")
        self.assertEqual(L.classify(410), "failed")
        for code in (401, 403, 405, 429, 451, 500, 502, 503, 999, 400):
            self.assertEqual(L.classify(code), "inconclusive", code)

    def test_success_and_redirects(self):
        self.assertEqual(L.classify(200), "ok")
        self.assertEqual(L.classify(204), "ok")
        self.assertEqual(L.classify(200, redirected=True), "redirected")

    def test_network_errors_are_never_proof_of_absence(self):
        self.assertEqual(L.classify(None, "URLError: Name or service not known"), "inconclusive")
        self.assertEqual(L.classify(None, "timeout"), "inconclusive")
        self.assertEqual(L.classify(None), "inconclusive")


class Handler(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *a):
        pass

    def _reply(self):
        Handler.seen.append((self.command, self.path, self.headers.get("User-Agent")))
        routes = {"/ok": 200, "/gone": 404, "/blocked": 403, "/busy": 429, "/broken": 500}
        if self.path == "/moved":
            self.send_response(301)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        if self.path == "/head-refused" and self.command == "HEAD":
            self.send_response(405)
            self.end_headers()
            return
        if self.path == "/slow":
            time.sleep(1.5)
        code = routes.get(self.path, 200 if self.path in ("/head-refused", "/slow") else 404)
        self.send_response(code)
        self.send_header("Content-Length", "2")
        self.end_headers()
        if self.command == "GET":
            try:
                self.wfile.write(b"ok")
            except BrokenPipeError:   # the client timed out on purpose (/slow)
                pass

    do_HEAD = _reply
    do_GET = _reply


class LiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()  # shutdown() stops serving; only this frees the socket

    def check(self, path, timeout=5.0):
        return L.check_one(self.base + path, timeout)

    def test_outcomes(self):
        self.assertEqual(self.check("/ok")["outcome"], "ok")
        self.assertEqual(self.check("/gone")["outcome"], "failed")
        self.assertEqual(self.check("/blocked")["outcome"], "inconclusive")
        self.assertEqual(self.check("/busy")["outcome"], "inconclusive")
        self.assertEqual(self.check("/broken")["outcome"], "inconclusive")

    def test_redirect_is_recorded_not_failed(self):
        r = self.check("/moved")
        self.assertEqual(r["outcome"], "redirected")
        self.assertEqual(r["final_url"], self.base + "/ok")

    def test_get_only_when_head_is_refused(self):
        Handler.seen.clear()
        self.assertEqual(self.check("/head-refused")["outcome"], "ok")
        self.assertEqual([c for c, p, _ in Handler.seen if p == "/head-refused"], ["HEAD", "GET"])
        Handler.seen.clear()
        self.check("/ok")
        self.assertEqual([c for c, p, _ in Handler.seen], ["HEAD"])

    def test_identifies_itself(self):
        Handler.seen.clear()
        self.check("/ok")
        self.assertTrue(Handler.seen[0][2].startswith("HRLibrary-linkcheck/"))

    def test_timeout_is_inconclusive(self):
        r = self.check("/slow", timeout=0.3)
        self.assertEqual(r["outcome"], "inconclusive")
        self.assertTrue(r["error"])

    def test_refused_connection_is_inconclusive(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        r = L.check_one(f"http://127.0.0.1:{port}/", 2.0)
        self.assertEqual(r["outcome"], "inconclusive")

    def test_sweep_records_sources_previous_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "links.json"
            out.write_text(json.dumps({"links": [{"url": self.base + "/gone", "outcome": "ok",
                                                  "status": 200, "checked_at": "2026-07-01"}]}))
            src = [{"doc": "doc3", "file": "content/docs/src/doc3.md", "section": "X", "page": "/3/library/"}]
            data = L.sweep([(self.base + "/ok", src), (self.base + "/gone", src)],
                           out_path=out, delay=0, timeout=5, log=lambda *a: None)
            saved = json.loads(out.read_text())
            self.assertEqual(saved, data)
            self.assertEqual(data["run"]["counts"], {"ok": 1, "failed": 1})
            gone = data["links"][1]
            self.assertEqual(gone["previous"]["outcome"], "ok")
            self.assertEqual(gone["sources"], src)
            self.assertTrue(gone["checked_at"])


class WorsenedTest(unittest.TestCase):
    """What counts as a link getting worse, for the monthly issue."""

    def found(self, was, now, **extra):
        rec = {"url": "https://example.org/x", "outcome": now, "status": None,
               "sources": [{"doc": "doc3", "section": "A card"}]}
        rec.update(extra)
        if was is not None:
            rec["previous"] = {"outcome": was, "status": 200, "checked_at": "2026-10-01T06:00:00+00:00"}
        return W.worsened([rec])

    def test_a_link_that_answered_and_now_does_not_is_worse(self):
        for now in ("failed", "inconclusive"):
            for was in ("ok", "redirected"):
                with self.subTest(was=was, now=now):
                    self.assertEqual(len(self.found(was, now)), 1)

    def test_a_block_that_turned_out_to_be_a_real_404_is_worse(self):
        self.assertEqual(len(self.found("inconclusive", "failed")), 1)

    def test_a_redirect_is_not_worse_than_a_direct_answer(self):
        self.assertEqual(self.found("ok", "redirected"), [])

    def test_a_link_that_was_already_unreachable_is_not_new_bad_news(self):
        self.assertEqual(self.found("inconclusive", "inconclusive"), [])
        self.assertEqual(self.found("failed", "failed"), [])

    def test_a_link_coming_back_is_not_reported(self):
        self.assertEqual(self.found("failed", "ok"), [])
        self.assertEqual(self.found("inconclusive", "ok"), [])

    def test_a_brand_new_link_has_nothing_to_compare(self):
        self.assertEqual(self.found(None, "failed"), [])

    def test_the_report_names_every_link_and_counts_them(self):
        links = [{"url": "https://example.org/a", "outcome": "failed", "status": 404,
                  "sources": [{"doc": "doc3", "section": "A card"}],
                  "previous": {"outcome": "ok", "status": 200, "checked_at": "x"}}]
        text = W.body(W.worsened(links), {"started": "2026-11-01T06:00:00+00:00"})
        self.assertIn("1 link got worse", text)
        self.assertIn("https://example.org/a", text)
        self.assertIn("2026-11-01", text)
        self.assertIn("doc3 \u203a A card", text)

    def test_a_pipe_in_a_section_name_cannot_break_the_table(self):
        links = [{"url": "https://example.org/b", "outcome": "failed", "status": 410,
                  "sources": [{"doc": "doc3", "section": "A | B"}],
                  "previous": {"outcome": "ok", "status": 200, "checked_at": "x"}}]
        row = [ln for ln in W.body(W.worsened(links), {}).splitlines() if "example.org/b" in ln]
        self.assertEqual(len(row), 1)
        self.assertIn(r"A \| B", row[0])            # the literal pipe is escaped
        unescaped = row[0].replace(r"\|", "")       # remove it, then count delimiters
        self.assertEqual(unescaped.count("|"), 6, row[0])   # 5 columns, 6 pipes

    def test_no_sweep_file_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = W.main(["--checks", str(pathlib.Path(tmp) / "nope.json")])
        self.assertEqual(rc, 0)

    def test_github_output_is_written_for_the_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "gh_out"
            checks = pathlib.Path(tmp) / "links.json"
            checks.write_text(json.dumps({"run": {"started": "2026-11-01T06:00:00+00:00"},
                                          "links": [{"url": "https://example.org/c",
                                                     "outcome": "failed", "status": 404,
                                                     "sources": [],
                                                     "previous": {"outcome": "ok", "status": 200}}]}),
                              encoding="utf-8")
            prev, new = os.environ.get("GITHUB_OUTPUT"), str(out)
            os.environ["GITHUB_OUTPUT"] = new
            try:
                W.main(["--checks", str(checks), "--out", str(pathlib.Path(tmp) / "issue.md")])
            finally:
                if prev is None:
                    del os.environ["GITHUB_OUTPUT"]
                else:
                    os.environ["GITHUB_OUTPUT"] = prev
            self.assertIn("worsened=true", out.read_text(encoding="utf-8"))
            self.assertIn("count=1", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
