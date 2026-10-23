# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 160 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-23 by Claude (Phase 3 finished: offline + share cards)

## Now
- Phases 1-3 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.11+): build · output
  audit · html-validate · tests · .docx regression · voice audit · sources untouched.
  **html-validate is required** (`npm install`); a missing binary FAILS rather than skips.
- **All 25 weeks are real pages.** Weeks 22-24 come from doc5 §5.3-§5.8 and tick like any other week.
  Each of their rows names the doc5 section it came from, and a test fails a row that does not — that
  is what stops the site growing a second copy of doc5.
- **The site works offline (R28).** `_site/sw.js` carries a cache name hashed from everything else
  the build wrote, so any edit retires the old version by itself: activate deletes every cache that
  is not the current one. It precaches the shell, all 25 week pages, the glossary and the law card
  (36 entries), serves from cache and refreshes in the background. `/files/` and other origins are
  never touched. `offline.js` shows a dismissible bar that **never reloads on its own**.
- **Share cards (R28).** One 1200x630 SVG per document plus home, drawn from the design system's own
  colour primitives — no photography, no AI imagery, nothing embedded. A test fails any card using a
  hex that is not a token, so they cannot drift from the site.
- Ticks, resume line, reset (`progress.js`, `hrsite:v1`) · copy buttons (`copy.js`) · glossary search
  (`glossary.js`) · library filter (`library.js`) · course cards keyed to the tracker.
- `/check/` lists all 43 external links and reads `checks/links.json`: "Last sweep: 2026-10-22", 0
  failed, 3 inconclusive. `link-sweep.yml` re-runs it monthly and opens an issue only when a link
  gets worse. SEO: unique titles and descriptions, Open Graph, `robots.txt`; canonical, `sitemap.xml`
  and `og:image` only with `--site-url=https://…` (or `HR_SITE_URL`), since the domain is open.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}`, so derived counts cannot go stale.
- **R11 blocked storage**: one line saying progress is not being saved, so a private-mode learner is
  not misled. **R19 facets**: section + cost, which doc3 states; not phase/hours/credential.
- **R5 list**: the intake template and reference-check script are learner outputs, not document
  templates. **R18 JSON-LD** omitted: `price: 0` would be false for the paid resources.
- **R24 JS budget is 14 KB**, not 10 KB: 12 KB (owner, for the library filter), then 14 KB for
  `offline.js`. Forced — the thinnest usable version is 739 B against 661 B of headroom.
- **`sw.js` is not counted as page JS** — it runs after load, so it is not page weight.
- **Weeks 22-24 rows are pointers, not prose.** Each cites its doc5 section; a test enforces it.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng (403).
  Bot blocks and a busy server, not breakage. A human should still open them once.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless Chromium
  print-to-PDF; a real printer and Android print are untested. Browser checks were headless Chromium
  at 360 px: journey, reload, reset, corrupt/blocked storage, copy, keyboard, JS off.
- **The service worker has never run in a browser** — there is no browser here. `sw.test.js` covers
  its logic (10 tests, fake caches and network, mutation-checked), but that proves the logic, not the
  platform. Before launch: open the deployed site, let it install, go offline, reload 10 times.
- **The share cards are SVG only, and most social platforms reject SVG.** No rasteriser exists here:
  no rsvg-convert, no inkscape, no cairosvg (no libcairo), and ImageMagick has no SVG delegate. The
  build writes SVG and says so loudly. PNGs appear by themselves on any machine with rsvg-convert,
  inkscape or a headless Chrome/Edge — the owner's PC included. Until someone builds on such a
  machine, shared links show no image.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.** The week
  pages follow doc2, which owns the plan. The documents disagree — the owner's call.

## Closed last round (six owner decisions)
Weeks 22-24 authored from doc5 · doc4 "unlocks" → "gives" · doc5 "Stakeholders" kept and marked
`accepted` · html-validate required · home copy reworded · "how long it takes" dropped from both
places. Doc2 re-shipped (100 → 106 paras) and the regression baseline moved with it.

## Closed this round (Phase 3 finished)
- **Service worker (R28)**: versioned cache, 36 entries precached, cache-first with background
  refresh, no manual invalidation. Nudge plus an offline line, dismissible, never reloads itself.
- **OG share cards (R28)**: one drawn SVG per document plus home, from the design system's tokens.
- **27 tests**: 10 Node (worker logic, mutation-checked) and 17 Python. One proves the cache name
  changes when content changes; one fails any card colour that is not a design token.

## Blocked on an owner decision
1. **Production domain** (D4): needed for canonical URLs, `og:url`, `og:image` and the sitemap.
   `learnhr.vercel.app` is likely but unconfirmed — nothing is set anywhere until the URL is real.
   When it is: build command `python3 tools/sitegen/sitegen.py`, output dir `_site`, and set
   `HR_SITE_URL` in Vercel's env dashboard. Do **not** run `check.py` in the deploy: it needs
   python-docx and html-validate, and it does not build the site.

## Next justified step
**Phase 4: pre-launch checks** — the last thing before launch. Lighthouse mobile on the four heaviest
routes, a 3G cold-load timing, the 9pt table-text contrast audit, print from a real printer, and a
`curl -I` sweep of every route after the first deploy.

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- **The `.docx` regression cannot see a word-for-word swap.** It counts paragraphs, words, tables and
  hyperlinks, so reworded source silently forks the download. Re-ship on purpose, by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- The build clears `_site` itself (`clean_site()`); its guard refuses to clear the repo.
- **A site copy string can live outside `content/`** — "how long it takes" was in both. Grep both.
- **`sitegen._cache` memoises parsed documents for the whole process**, so editing `content/` in a
  running process changes nothing until cleared; tests must clear it to see edits.
- **`sw.js` templating**: Python's `str.replace` hits every occurrence, JS's only the first, and
  `sw.js`'s own header comment names both tokens — a JS replace without `/g` leaves them in place.
- **Never promise PNG by checking that a binary exists** — ImageMagick usually has no SVG delegate
  and "succeeds" while writing nothing. The OG probe draws a real card and checks the PNG header.
- sitegen.py needs Python 3.11+; 3.10 fails on the parser. `node --test` takes file paths, so a new
  JS test file must be named in `check.py` or it never runs.
- `python-docx` isn't installed here by default: `pip install --break-system-packages -r requirements.txt`.
- **Never rely on `subprocess.run(..., text=True)` without `encoding="utf-8"`** — it rots silently on
  a Windows console. **A regex escape in a raw string is not an escape**: `r"\u00a7"` is six chars.
