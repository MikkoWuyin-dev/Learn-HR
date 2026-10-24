#!/usr/bin/env python3
"""The gate: build the site, then run every check. Exit 0 only if all pass.

    python3 tools/sitegen/check.py

Steps: build (sitegen.py) · output audit (audit.py) · html-validate on every page
(skipped, and said so, if it is not installed) · Python tests · JavaScript tests
(node --test; skipped if Node is missing) · the .docx regression (needs python-docx)
· the voice audit (style_audit.py) over every generated page's text and the run-time
interface strings · proof that the build left content/ and downloads/ byte-identical.
Needs Python 3.11+. Sends no network requests; the link sweep is linkcheck.py.
"""
import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
PY = sys.executable

# Interface text the site adds around the documents' own words (buttons, notes,
# status lines). The documents themselves are covered by validate_build.py.
UI_STRINGS = """Start with Week 0. See the whole plan. Your next block. Your progress.
Saved in this browser on this device only. It does not follow you to another phone or browser, and clearing your browser data clears it.
Clear my progress. Clear every tick on this device? Yes, clear it. Keep it.
Output done. This week's output. From the plan's progress tracker (Support A). Tick only when the output exists.
Copy. Copied. Couldn't copy automatically. The text is selected: press and hold it, then choose Copy.
You left off at Week 4. Resume: Week 4. Open Week 4. Output: Notes.
Every block in Weeks 0–24 is ticked.
This browser is not saving progress (private browsing or storage turned off). Ticks last until you leave the page.
Marked done. Unmarked. Progress cleared on this device.
Week passed: every output exists. Tick a block only when its output exists.
Last sweep. Inconclusive means the site refused or slowed an automated check (403, 429, a timeout, a network error); it does not mean the page is gone. A reachable link only proves the page answered, not that the course or its terms are unchanged.
No sweep recorded yet. Not yet checked. Reachable after a redirect.
Not legal advice; current to the date checked.
Search the terms. 3 of 26 terms match. No term matches. Try fewer letters.
Section. All sections. Cost. Any cost. 4 of 20 resources shown. Free to use. Paid.
Each cost label sums up the card's own cost terms. Open the card for the full terms before you plan a week around it.
"""


def run(name, cmd, cwd=ROOT):
    # encoding= matters: without it the parent decodes the child's UTF-8 output
    # with the console's code page, so on a cp1252 Windows console any non-ASCII
    # byte arrives already mangled. PYTHONIOENCODING alone only fixes the child.
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ok = r.returncode == 0
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print("      " + "\n      ".join(tail))
    return ok


# Banned-pattern hits that come from the documents themselves, not from the site.
# Content edits need the owner, so these are reported, not failed; any other hit
# fails. Each entry is (category, snippet, where, status) and status is either
# "accepted" — the owner has read the sentence and chosen to keep it, so stop
# asking — or "open", still waiting on a decision.
KNOWN_SOURCE_HITS = [
    ("consultant speak", "Stakeholders and judgement", "doc5 §5.6, interview question group", "accepted"),
]
BANNED = ("throat-clearing", "puffed-up", "negative framing", "consultant speak")


class _Text(HTMLParser):
    """Visible text of a generated page, one block per line, scripts dropped."""
    BLOCKS = {"p", "li", "h1", "h2", "h3", "h4", "td", "th", "caption", "blockquote",
              "pre", "br", "tr", "figcaption", "a", "button", "title"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in self.BLOCKS:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def voice_hits(paths):
    """Run style_audit.py; return (mechanical_ok, [(category, snippet)])."""
    # Decoding must be UTF-8, not the console code page: style_audit marks each
    # hit with "…" (U+2026), and decoded as cp1252 that never matches, so every
    # hit is dropped and the audit passes without having audited anything.
    r = subprocess.run([PY, "style_audit.py", *map(str, paths)], cwd=ROOT / "scripts",
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    hits, current = [], None
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*([a-z -]+): (\d+)", ln)
        if m:
            current = m.group(1) if m.group(1) in BANNED and int(m.group(2)) else None
        elif current and ln.strip().startswith("…"):
            hits.append((current, ln.strip()))
    return r.returncode == 0, hits


def source_digest():
    """A hash of every byte under content/ and downloads/."""
    h = hashlib.sha256()
    for f in sorted(p for d in ("content", "downloads") for p in (ROOT / d).rglob("*") if p.is_file()):
        h.update(f.relative_to(ROOT).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def main():
    if sys.version_info < (3, 11):
        print(f"FAIL  Python {sys.version.split()[0]}: sitegen.py needs 3.11+")
        return 1
    before = source_digest()
    results = [run("build", [PY, "tools/sitegen/sitegen.py"]),
               run("output audit", [PY, "tools/sitegen/audit.py"]),
               # Phase 4's contrast check, run on every build rather than once:
               # a palette edit is exactly when a ratio is most likely to slip.
               run("contrast audit", [PY, "tools/sitegen/contrast.py"]),
               # Phase 4's JS-off crawl. The risk it guards is a page whose
               # words only appear once a script runs, which passes every
               # other check here and reaches a reader as an empty page.
               run("no-JavaScript crawl", [PY, "tools/sitegen/nojs.py"]),
               # Phase 4's stand-in for the 3G timing: the bytes half of that
               # sum, which is all that can be measured without a browser.
               run("page weight", [PY, "tools/sitegen/weight.py"])]

    # html-validate (roadmap 1.6), rules in .htmlvalidate.json; the frozen archive under
    # files/ is not ours to change, so only generated pages are checked.
    hv = ROOT / "node_modules/.bin/html-validate"
    hv = str(hv) if hv.exists() else shutil.which("html-validate")
    if hv:
        results.append(run("html-validate", [hv, "_site/**/index.html"]))
    else:
        # Required, not optional: the owner decided on 2026-10-22 that a missing
        # binary must fail the gate rather than silently skip a check. Install
        # with `npm install` (declared in package.json) or `npm i -g html-validate@9`.
        print("FAIL  html-validate is required but not installed")
        print("      run `npm install` in the repo root, or `npm i -g html-validate@9`")
        results.append(False)

    results.append(run("python tests", [PY, "-m", "unittest", "discover", "-s", "tools/sitegen/tests"]))
    if shutil.which("node"):
        # Named one by one: `node --test` takes file paths, not a directory.
        results.append(run("javascript tests", ["node", "--test",
                                                "tools/sitegen/tests/progress.test.js",
                                                "tools/sitegen/tests/sw.test.js"]))
    else:
        print("SKIP  javascript tests (node not installed)")
    results.append(run(".docx regression", [PY, "tools/sitegen/docx_regression.py"]))

    # Browser. Skipped unless a machine has a Chromium to point at, so the gate
    # stays green on a laptop with no browser — but it prints, so it cannot be
    # silently forgotten. It needs the site served, since a service worker will
    # not register from file://. Nothing here is covered by a static check.
    if shutil.which("node") and os.environ.get("CHROME_PATH"):
        results.append(run("browser checks", ["node", "tools/sitegen/browser_check.mjs",
                                              "http://localhost:8000"]))
    elif not shutil.which("node"):
        print("SKIP  browser checks (node not installed)")
    else:
        print("SKIP  browser checks (no CHROME_PATH; serve the site and set it to run)")

    # Voice (roadmap 1.5): the generated pages' text, so template-added filler is caught,
    # plus the interface strings progress.js and copy.js write at run time.
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for page in sorted((ROOT / "_site").rglob("index.html")):
            t = _Text()
            t.feed(page.read_text(encoding="utf-8"))
            name = page.parent.relative_to(ROOT / "_site").as_posix().replace("/", "_") or "home"
            f = pathlib.Path(tmp) / f"{name}.md"
            f.write_text(re.sub(r"\n\s*\n+", "\n\n", "".join(t.out)), encoding="utf-8")
            files.append(f)
        ui = pathlib.Path(tmp) / "zz-runtime-ui.md"
        ui.write_text(UI_STRINGS, encoding="utf-8")
        mechanical_ok, hits = voice_hits(files + [ui])
    known = [h for h in hits if any(c == h[0] and n in h[1] for c, n, _, _ in KNOWN_SOURCE_HITS)]
    new = [h for h in hits if h not in known]
    ok = mechanical_ok and not new
    print(f"{'PASS' if ok else 'FAIL'}  voice audit on every page" +
          (f"  new hits: {new[:3]}" if new else "") + ("" if mechanical_ok else "  mechanical problems"))
    for c, n, where, status in KNOWN_SOURCE_HITS:
        if any(c == h[0] and n in h[1] for h in known):
            note = ("accepted by the owner, kept as written" if status == "accepted"
                    else "owner to decide")
            print(f"      known, in the source, {note}: {c} \"{n}\" ({where})")
    results.append(ok)

    after = source_digest()
    same = before == after
    print(f"{'PASS' if same else 'FAIL'}  content/ and downloads/ untouched by the build")
    results.append(same)
    if shutil.which("git"):
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "content", "downloads"],
                               cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8").stdout.strip()
        if dirty:
            print("NOTE  uncommitted edits under content/ or downloads/ (fine if intended):")
            print("      " + dirty.replace("\n", "\n      "))

    bad = results.count(False)
    print(f"\nRESULT: {'all checks passed' if not bad else f'{bad} failing'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
