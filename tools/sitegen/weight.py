#!/usr/bin/env python3
"""Phase 4 gate: what a first visit actually costs, and how long it takes on 3G.

The roadmap asks for a 3G cold-load timing. There is no browser here, so the
time cannot be measured. What can be measured honestly is the other half of
that sum: how many bytes a cold first visit moves. Time is then bytes over a
stated link speed, with the assumption written down rather than buried, so a
reader can disagree with the speed and redo the arithmetic.

This deliberately measures the *first* visit, not a repeat one. A returning
reader has the CSS, the JS and the fonts cached, so their cost is the HTML
alone. The first visit is the one that hurts on a bad connection, and it is
the one a page-weight check that only looks at HTML completely misses.

The critical path is read out of each page rather than assumed: whatever that
page's own <link> and <script> tags pull, plus the fonts its stylesheet asks
for. Sizes are gzipped, because that is what crosses the wire - measuring raw
bytes would overstate every text asset by roughly three to four times.

    python3 tools/sitegen/weight.py            # table, exit 1 over budget
    python3 tools/sitegen/weight.py --top 20   # show more routes

Exit 0 only if every route stays inside the first-visit budget.
"""
import gzip
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"

# What one cold first visit may cost, gzipped, fonts included. Dropping the
# webfonts (owner's decision, 2026-10-24) took the heaviest route from 71,337 B
# to 22,285 B, which left the old 100 KB figure measuring nothing at all.
#
# 40 KB is deliberately tight against that: it leaves room for a route to grow,
# but not for the fonts to come back. Reintroducing Fredoka and Space Grotesk
# alone is 48,628 B, so this budget is the thing that would stop it.
FIRST_VISIT_BUDGET = 40 * 1024

# "Slow 3G" as Chrome's DevTools defines it: 400 kbps down, 2000 ms RTT.
# Chosen because the site is meant for a phone on a bad Nigerian connection,
# and flattering the number would defeat the point of measuring it.
BITS_PER_SECOND = 400_000
BYTES_PER_SECOND = BITS_PER_SECOND / 8
RTT_SECONDS = 2.0
# DNS + TCP + TLS before the first response byte starts arriving.
CONNECTION_ROUND_TRIPS = 3


def gzipped(path):
    return len(gzip.compress(path.read_bytes(), 9))


def first_fonts():
    """The font files a cold visit downloads.

    The @font-face rules here carry no unicode-range, so a browser takes the
    first source in each src: list and stops. The second source in each list -
    the latin-ext subset - is a fallback that is never fetched while the first
    works, so counting it would overstate the page by 11 KB.
    """
    css = (SITE / "fieldnotes.css").read_text(encoding="utf-8")
    out, total = [], 0
    for block in re.finditer(r"@font-face\s*\{([^}]*)\}", css):
        srcs = re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", block.group(1))
        if not srcs:
            continue
        rel = srcs[0].lstrip("/")
        p = SITE / rel
        if p.exists():
            size = p.stat().st_size  # woff2 is already compressed
            out.append((rel, size))
            total += size
    return out, total


def page_assets(html):
    """The css and js this specific page pulls, relative to the site root."""
    css = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html)
    css += re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', html)
    js = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    return sorted(set(css)), sorted(set(js))


def main(argv):
    if not SITE.exists():
        raise SystemExit("no _site - build the site first")
    top = 12
    if "--top" in argv:
        i = argv.index("--top")
        if i + 1 < len(argv):
            top = int(argv[i + 1])

    fonts, font_total = first_fonts()

    html_gz = {}
    per_page_css, per_page_js = {}, {}
    # Asset paths are relative and differ by depth: the home page says
    # "static/site.css" while a week page says "../../../../static/site.css".
    # Resolving them against the site root scores every route but the home
    # page as pulling nothing at all.
    shared = {}

    def resolve(page, href):
        p = (page.parent / href) if not href.startswith("/") else (SITE / href.lstrip("/"))
        return p.resolve() if p.exists() else None

    for page in sorted(SITE.rglob("index.html")):
        rel = str(page.relative_to(SITE))
        raw = page.read_text(encoding="utf-8")
        html_gz[rel] = len(gzip.compress(page.read_bytes(), 9))
        css, js = page_assets(raw)
        per_page_css[rel], per_page_js[rel] = css, js
        for href in css + js:
            p = resolve(page, href)
            if p and p not in shared:
                shared[p] = gzipped(p)

    rows = []
    for page in sorted(SITE.rglob("index.html")):
        rel = str(page.relative_to(SITE))
        h = html_gz[rel]
        css_b = sum(shared[resolve(page, r)] for r in per_page_css[rel]
                    if resolve(page, r) in shared)
        js_b = sum(shared[resolve(page, r)] for r in per_page_js[rel]
                   if resolve(page, r) in shared)
        rows.append((rel, h, css_b, js_b, font_total, h + css_b + js_b + font_total))
    rows.sort(key=lambda r: -r[5])

    failures = []
    for rel, h, c, j, f, total in rows:
        if total > FIRST_VISIT_BUDGET:
            failures.append(
                f"{rel}: first visit is {total:,} B, over the "
                f"{FIRST_VISIT_BUDGET:,} B budget "
                f"(html {h:,} + css {c:,} + js {j:,} + fonts {f:,})")

    worst = rows[0]
    transfer = worst[5] / BYTES_PER_SECOND
    cold = CONNECTION_ROUND_TRIPS * RTT_SECONDS + transfer

    print("cold first visit, gzipped, fonts included")
    print(f"  budget: {FIRST_VISIT_BUDGET:,} B per route")
    print()
    print(f"  {'route':52} {'html':>7} {'css':>6} {'js':>6} {'fonts':>7} {'total':>8}")
    for rel, h, c, j, f, total in rows[:top]:
        name = rel[:-len("/index.html")] if rel.endswith("/index.html") else rel
        name = name or "(home)"
        flag = "  OVER" if total > FIRST_VISIT_BUDGET else ""
        print(f"  {name[:52]:52} {h:>7,} {c:>6,} {j:>6,} {f:>7,} {total:>8,}{flag}")
    if len(rows) > top:
        print(f"  ... {len(rows) - top} lighter routes")
    print()

    print("  shared assets (gzipped, cached after the first page):")
    for path, size in sorted(shared.items(), key=lambda kv: -kv[1]):
        print(f"    {str(path.relative_to(SITE)):32} {size:>7,} B gz")
    print(f"  fonts a cold visit fetches ({len(fonts)}):")
    for rel, size in fonts:
        print(f"    {rel:44} {size:>7,} B")
    print(f"    fonts are {font_total / worst[5] * 100:.0f}% of the heaviest route")
    print()

    print("  on slow 3G (400 kbps, 2000 ms RTT - Chrome's 'Slow 3G'):")
    print(f"    connection setup  {CONNECTION_ROUND_TRIPS} round trips "
          f"{CONNECTION_ROUND_TRIPS * RTT_SECONDS:>5.1f} s")
    print(f"    transfer          {worst[5]:,} B        {transfer:>5.1f} s")
    print(f"    heaviest route                      {cold:>5.1f} s to first paint")
    print("    there are no webfonts to preload: Fieldnotes uses system faces,")
    print("    so nothing waits on a font fetch and the figure is the real one.")
    print("    This is bytes-over-a-stated-link, not a measurement: no browser")
    print("    runs here, so treat it as an estimate with the assumption shown.")
    print()

    if failures:
        print(f"RESULT: {len(failures)} route(s) over the first-visit budget")
        for f in failures[:15]:
            print(f"  - {f}")
        return 1
    print(f"RESULT: all {len(rows)} routes inside "
          f"{FIRST_VISIT_BUDGET:,} B on a cold first visit "
          f"(heaviest {worst[5]:,} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
