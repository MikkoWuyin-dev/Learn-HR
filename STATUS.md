# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 160 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-22 by Claude (R28 service worker built; the site works offline)

## Now
- Phases 1 and 2 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.11+): build ·
  output audit · html-validate · tests · .docx regression · voice audit · sources untouched.
  **html-validate is required** (`npm install`); a missing binary FAILS rather than skips.
- **All 25 weeks are real pages.** Weeks 22-24 come from doc5 §5.3-§5.8 and tick like any other
  week. The progress meter derives its own range, so it cannot go stale again. Each of their rows
  names the doc5 section it came from, and `test_site.py` fails a row that does not — that is what
  stops the site growing a second copy of doc5.
- **The site works offline (R28).** `sitegen.py` emits `_site/sw.js` with a cache name hashed from
  everything else it wrote, so any edit retires the old version by itself: activate deletes every
  cache that is not the current one. It precaches the shell, all 25 week pages, the glossary and the
  law card (36 entries), serves pages from cache and refreshes them in the background. `/files/` and
  other origins are never touched. `offline.js` registers it and shows a dismissible bar that
  **never reloads on its own** — R28's "must not interrupt mid-read".
- Ticks, resume line, reset (`progress.js`, localStorage `hrsite:v1`) · copy buttons (`copy.js`) ·
  glossary search (`glossary.js`) · library filter (`library.js`) · course cards keyed to the tracker.
- `/check/` lists all 43 external links and reads `checks/links.json`: "Last sweep: 2026-10-22",
  0 failed, 3 inconclusive. `.github/workflows/link-sweep.yml` re-runs it monthly and opens an
  issue only when a link gets worse.
- SEO: unique titles, descriptions from each page's own text, Open Graph, `robots.txt`; canonical
  and `sitemap.xml` only with `--site-url=https://…` (or `HR_SITE_URL`), since the domain is open.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}`, not `weeks/courses/artefacts` maps.
  Derived counts cannot go stale when the curriculum changes.
- **R11 blocked storage**: one line saying progress is not being saved, so a private-mode learner
  is not misled. **R19 facets**: section + cost, which doc3 states; not phase/hours/credential.
- **R5 list**: the intake template and reference-check script are learner outputs, not document
  templates. **R18 JSON-LD** omitted: `price: 0` would be false for the paid resources.
- **R24 JS budget is 14 KB**, not 10 KB: 12 KB (owner, for the library filter), then 14 KB for
  `offline.js`. Forced, not chosen — the thinnest usable version is 739 B against 661 B of headroom.
- **`sw.js` is not counted as page JS.** It runs on its own thread after load, so it neither delays
  a first paint nor adds to what a reader downloads to see a page. Still size-checked.
- **Weeks 22-24 rows are pointers, not prose.** Each cites its doc5 section; a test enforces it.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng (403).
  Bot blocks and a busy server, not breakage. A human should still open them once.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless
  Chromium print-to-PDF; a real printer and Android print are untested. Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy, keyboard, JS off.
- **The service worker has never run in a browser** — there is no browser here. `sw.test.js` covers
  its logic (10 tests, fake caches and network, mutation-checked), but that proves the logic, not the
  platform. Before launch: open the deployed site, let it install, go offline, reload 10 times.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.** The week
  pages follow doc2, which owns the plan. The documents disagree — the owner's call.

## Closed last round (six owner decisions)
Weeks 22-24 authored from doc5 · doc4 §4.4 "unlocks" → "gives" and re-shipped · doc5 §5.6
"Stakeholders and judgement" kept and marked `accepted` · html-validate made required · home copy
reworded to "Five documents, one plan — plus the full research archive" · "how long it takes" dropped
from both places it lived · `--wk-muted` left as won't-fix. Doc2 re-shipped (100 → 106 paras,
25 → 28 tables) and the regression baseline moved with it.

## Closed this round (R28)
- **Service worker built**: versioned cache, 36 entries precached, cache-first with background
  refresh, no manual invalidation anywhere.
- **R28's nudge** plus an offline line, dismissible and fixed to the bottom. A test asserts
  `location.reload()` appears once and only inside a click handler, so it cannot reload by itself.
- **10 Node tests** (worker logic) and **8 Python tests** (build side), including one proving the
  cache name changes when content changes.

## Blocked on an owner decision
1. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap. `learnhr.vercel.app`
   is likely but unconfirmed — nothing is set anywhere until the URL is real. When it is: build
   command `python3 tools/sitegen/sitegen.py`, output dir `_site`, and set `HR_SITE_URL` in Vercel's
   env dashboard. Do **not** run `check.py` in the deploy: it needs python-docx and html-validate,
   and it does not build the site.

## Next justified step
Finish Phase 3: **OG share cards**, one per document, generated from the site's own tokens (no
photography, no AI imagery). Then Phase 4 (pre-launch checks) is the last thing before launch.

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- **The `.docx` regression cannot see a word-for-word swap.** It counts paragraphs, words, tables and
  hyperlinks, so reworded source silently forks the download. Re-ship on purpose, by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- The build clears `_site` itself (`clean_site()`), so a deleted page cannot survive into a deploy.
  Its guard refuses to clear anything that is, or contains, the repo — keep that guard.
- **A site copy string can live outside `content/`** — "how long it takes" was in both. Grep both.
- **`sitegen._cache` memoises parsed documents for the whole process**, so editing `content/` in a
  running process changes nothing until it is cleared. Harmless in production; it makes any test
  that edits content lie unless it clears `_cache` too.
- **`sw.js` templating**: Python's `str.replace` hits every occurrence, JS's only the first, and
  `sw.js`'s own header comment names both tokens — a JS replace without `/g` leaves them in place.
- sitegen.py needs Python 3.11+; 3.10 fails on the parser. `node --test` takes file paths, so a new
  JS test file must be named in `check.py` or it never runs.
- `python-docx` isn't installed here by default: `pip install --break-system-packages -r requirements.txt`.
- **Never rely on `subprocess.run(..., text=True)` without `encoding="utf-8"`** — non-ASCII rots
  silently on a Windows console. PYTHONIOENCODING only fixes the child.
- **A regex escape inside a raw string is not an escape**: `r"\u00a7"` is six characters. Write `§`.
