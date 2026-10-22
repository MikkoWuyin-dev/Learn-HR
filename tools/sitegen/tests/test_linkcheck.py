"""Tests for linkcheck.py: the outcome rules, and real requests to a local server.

    python3 -m unittest discover -s tools/sitegen/tests

No request leaves the machine: the server is 127.0.0.1 on a random port.
"""
import http.server
import json
import pathlib
import socket
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import linkcheck as L  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
