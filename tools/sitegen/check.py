#!/usr/bin/env python3
"""The gate: build the site, then run every check. Exit 0 only if all pass.

    python3 tools/sitegen/check.py

Steps: build (sitegen.py) · output audit (audit.py) · Python tests · JavaScript
tests (node --test; reported as skipped if Node is not installed) · the .docx
regression (docx_regression.py, needs python-docx) · the voice audit on the copy
the site layer adds (style_audit.py). Needs Python 3.12+ (sitegen uses PEP 701
f-strings). Sends no network requests; the link sweep is linkcheck.py, run by hand.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

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
Every block in Weeks 0–21 is ticked. Weeks 22–24 live in Getting the job.
This browser is not saving progress (private browsing or storage turned off). Ticks last until you leave the page.
Marked done. Unmarked. Progress cleared on this device.
Week passed: every output exists. Tick a block only when its output exists.
Last sweep. Inconclusive means the site refused or slowed an automated check (403, 429, a timeout, a network error); it does not mean the page is gone. A reachable link only proves the page answered, not that the course or its terms are unchanged.
No sweep recorded yet. Not yet checked. Reachable after a redirect.
Not legal advice; current to the date checked.
"""


def run(name, cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ok = r.returncode == 0
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        print("      " + "\n      ".join(tail))
    return ok


def main():
    if sys.version_info < (3, 12):
        print(f"FAIL  Python {sys.version.split()[0]}: sitegen.py needs 3.12+")
        return 1
    results = [run("build", [PY, "tools/sitegen/sitegen.py"]),
               run("output audit", [PY, "tools/sitegen/audit.py"]),
               run("python tests", [PY, "-m", "unittest", "discover", "-s", "tools/sitegen/tests"])]
    if shutil.which("node"):
        results.append(run("javascript tests", ["node", "--test", "tools/sitegen/tests/progress.test.js"]))
    else:
        print("SKIP  javascript tests (node not installed)")
    results.append(run(".docx regression", [PY, "tools/sitegen/docx_regression.py"]))
    with tempfile.TemporaryDirectory() as tmp:
        f = pathlib.Path(tmp) / "ui.md"
        f.write_text(UI_STRINGS, encoding="utf-8")
        r = subprocess.run([PY, "style_audit.py", str(f)], cwd=ROOT / "scripts",
                           capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        # style_audit.py exits non-zero only on mechanical problems; the PRD's done list
        # also wants zero banned-pattern hits, so those counts are read here.
        hits = [ln.strip() for ln in r.stdout.splitlines()
                if re.match(r"\s*(throat-clearing|puffed-up|negative framing|consultant speak): [1-9]", ln)]
        ok = r.returncode == 0 and not hits
        print(f"{'PASS' if ok else 'FAIL'}  voice audit on site-layer copy" + (f"  {hits}" if hits else ""))
        results.append(ok)
    bad = results.count(False)
    print(f"\nRESULT: {'all checks passed' if not bad else f'{bad} failing'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
