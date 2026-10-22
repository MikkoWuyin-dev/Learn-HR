#!/usr/bin/env python3
"""Report links whose latest sweep came back worse than the one before it.

`linkcheck.py` records, against every link, the outcome of the run before the one
it just did — so this needs no history of its own. It reads the sweep file and
lists the links a reader could follow last time and cannot now.

    python3 tools/sitegen/report_worsened.py --out issue.md

Prints the markdown it would file, and writes it to --out when asked.

Exits 0 whether or not anything is wrong. A dead link is a finding, not a broken
run: the sweep's own --strict flag is what fails a build on one, and here the
result has to be committed and reported before anything else happens.

Sets `worsened=true` and `count=N` on $GITHUB_OUTPUT when there is something to
report, so a workflow can decide whether to open an issue.
"""
import argparse
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "checks" / "links.json"

# Only 404 and 410 count as "failed"; every other unreachable answer is
# "inconclusive", which usually means a bot block but just as easily means a
# paywall. Both are worse than a link that answered, so both get reported.
WORSE_THAN = {
    "ok": ("inconclusive", "failed"),
    "redirected": ("inconclusive", "failed"),
    # A block that turned out to be a real 404 is worth knowing about too.
    "inconclusive": ("failed",),
}


def worsened(links):
    """[(was, now, record)] for every link that stopped answering."""
    out = []
    for r in links:
        prev = r.get("previous") or {}
        was = prev.get("outcome") if isinstance(prev, dict) else None
        now = r.get("outcome")
        if was in WORSE_THAN and now in WORSE_THAN[was]:
            out.append((was, now, r))
    return out


def cell(text):
    """One table cell: no pipes, no newlines, and never empty."""
    t = " ".join(str(text or "").split()).replace("|", r"\|")
    return t or "\u2014"


def where(record):
    seen = sorted({f"{s.get('doc', '?')} \u203a {s.get('section', '?')}"
                   for s in record.get("sources", [])})
    return cell("; ".join(seen))


def body(found, run):
    started = (run or {}).get("started") or ""
    when = started[:10] or "latest"
    n = len(found)
    lines = [
        f"## {n} link{'s' if n != 1 else ''} got worse in the {when} sweep",
        "",
        "Each of these answered on the previous sweep and does not answer now. "
        "A reader following the documents would hit it.",
        "",
        "| Was | Now | Status | Link | Appears in |",
        "|---|---|---|---|---|",
    ]
    for was, now, r in found:
        status = r.get("status") or (r.get("error") or "").split(":")[0]
        lines.append(f"| {was} | **{now}** | {cell(status)} | {cell(r.get('url'))} | {where(r)} |")
    lines += [
        "",
        "**What the words mean.** Only 404 and 410 count as *failed* — the page is "
        "gone. 401/403/429, 5xx, timeouts and DNS or TLS errors are *inconclusive*: "
        "often a bot refusing the checker, but sometimes a paywall or a move. Either "
        "way something changed and it is worth a human look.",
        "",
        "**What to do.** Fix the sentence in `content/docs/src/*.md`, never the "
        "generated HTML. If a resource has gone paid rather than missing, follow the "
        "documents' own rule and substitute a free equivalent that is already in the "
        "library.",
        "",
        "**Re-run by hand:** `python3 tools/sitegen/linkcheck.py`, commit "
        "`checks/links.json`, then `python3 tools/sitegen/sitegen.py` so `/check/` "
        "publishes the result.",
        "",
        "The full record is `checks/links.json` on `main`. This issue is updated in "
        "place while any link stays worse, so it will not pile up.",
        "",
        "<!-- link-sweep-report -->",
    ]
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write the report here, as well as printing it")
    ap.add_argument("--checks", default=str(DEFAULT), help="the sweep file to read")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.checks)
    if not path.exists():
        print(f"no sweep at {path}; nothing to compare")
        _emit(False, 0)
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    found = worsened(data.get("links", []))

    if not found:
        print("nothing got worse: every link that answered before still answers")
    else:
        text = body(found, data.get("run"))
        print(text)
        if args.out:
            pathlib.Path(args.out).write_text(text, encoding="utf-8")

    _emit(bool(found), len(found))
    return 0


def _emit(any_worse, count):
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as fh:
            fh.write(f"worsened={'true' if any_worse else 'false'}\n")
            fh.write(f"count={count}\n")


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
