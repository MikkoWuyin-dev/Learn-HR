# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 160 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-23 by Claude (Phase 3 finished: offline + share cards)

## Now
- Phases 1-3 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.11+): build · output
  audit · contrast · no-JS crawl · page weight · html-validate · tests · .docx regression · voice
  audit · sources untouched.
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
- **R24 JS budget is 14 KB**, not 10 KB: 12 KB (owner, 2026-10-21, for the library filter), then
  14 KB (ratified by the owner 2026-10-23) for `offline.js`, which was 739 B against 661 B of
  headroom. Raising a budget is mine to decide; reporting every increase is not optional.
- **`sw.js` is not counted as page JS** — it runs after load, so it is not page weight.
- **Weeks 22-24 rows are pointers, not prose.** Each cites its doc5 section; a test enforces it.

## Phase 4 (pre-launch checks)
- **Contrast: done, and the flagged risk does not materialise.** The roadmap feared 9pt table text
  failing on cream. Measured: **13.42:1**, which is AAA. Worst text pair anywhere is quiet text at
  5.18:1, still clear of AA's 4.5. `tools/sitegen/contrast.py` now runs in the gate on every build,
  reading colours back out of site.css rather than restating them, so recoloring text fails it.
- **JS-off crawl: done, and the site holds up.** `tools/sitegen/nojs.py` strips every `<script>` from
  all 54 built pages and holds what is left against `content/`, not against the build — comparing the
  build to itself would pass no matter what went missing. Every page keeps its `<h1>`, its prose, its
  week rows, its terms and its resources. **Nothing ships hidden without a stated reason**: an element
  carrying `hidden` must be a control (tick, copy, search, filter) or saved-progress state, and the
  check names the file and refuses a new one until it is classified. That is the part that keeps this
  true later. Three mutations planted, three caught.
- **Page weight: measured, and fonts are the whole story.** `tools/sitegen/weight.py` weighs a cold
  first visit — not the HTML alone, which is what a page-weight check usually measures and which
  misses everything a returning reader has already cached. Heaviest route is **71,337 B** gzipped:
  HTML 12,144 + CSS 6,494 + JS 4,071 + **fonts 48,628, which is 68% of it**. New budget: a cold
  first visit may cost **100 KB**, set well above the 71 KB seen, to catch a route that grows.
- **Fonts are not preloaded**, so they start downloading only after the CSS is parsed. `<link
  rel=preload>` on the two latin faces is the obvious fix, but it needs `crossorigin` even
  same-origin or the font downloads twice — and there is no browser here to catch that. Left alone
  on purpose; do it where it can be watched.
- **Still to do**: Lighthouse mobile, 3G cold load, Android print, and the post-deploy `curl -I`
  sweep. All four need a browser or a deploy, and there is neither here.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng (403).
  Bot blocks and a busy server, not breakage. A human should still open them once.
- Real phone, iOS Safari, Lighthouse/3G. The law card fits one A4 page in headless Chromium
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

Weeks 22-24 authored from doc5 · doc4 "unlocks" → "gives" · doc5 "Stakeholders" kept and marked
`accepted` · html-validate required · home copy reworded · "how long it takes" dropped from both

## Closed this round (Phase 3 finished)
- **Service worker (R28)**: versioned cache, 36 entries precached, cache-first with background
  refresh, no manual invalidation. Nudge plus an offline line, dismissible, never reloads itself.
- **OG share cards (R28)**: one drawn SVG per document plus home, from the design system's tokens.
- **27 tests**: 10 Node (worker logic, mutation-checked) and 17 Python. One proves the cache name
  changes when content changes; one fails any card colour that is not a design token.

## Deployed
- **Live at https://fieldnotes-hr.vercel.app** — the owner deployed it on 2026-10-24. The project is
  "FieldNotes HR", one of a family of FieldNotes resource libraries.
- **`vercel.json` carries the deploy settings** so they live in the repo, not in dashboard text
  fields. `framework: null` is the load-bearing line: it stops Vercel auto-detecting a Python
  runtime from `requirements.txt` and hunting for an entrypoint, which is how it once found the
  `Handler` test double in `test_linkcheck.py` and tried to deploy the test suite as a web app.
- **Still unset**: `HR_SITE_URL`. Canonical URLs, `og:image` and `sitemap.xml` are all inert until
  it is set in Vercel's env dashboard. That is the next thing to do.
- Do **not** run `check.py` in the deploy: it needs python-docx and html-validate, and it does not
  build the site. `python3 tools/sitegen/sitegen.py` builds; `_site` is the output.

## Next justified step
The site is live, so the four checks that were blocked on a deploy are now unblocked: `curl -I`
every route against the real URL, Lighthouse mobile on the four heaviest routes, the 3G cold load,
and the service-worker acceptance run (install, go offline, reload ten times). Before any of them
mean much, `HR_SITE_URL` needs setting so canonical URLs and `og:image` exist.

## Session traps
- `python3` on the owner's PC is a Store stub; real one is `.../AppData/Local/Python/bin/python3`.
- **The `.docx` regression cannot see a word-for-word swap** — re-ship downloads by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- The build clears `_site` itself (`clean_site()`); its guard refuses to clear the repo.
- **`sitegen._cache` memoises parsed documents for the whole process**, so editing `content/` in a
  running process changes nothing until cleared; tests must clear it to see edits.
- **`sw.js` templating**: Python's `str.replace` hits every occurrence, JS's only the first, so a
  JS replace without `/g` leaves the tokens that `sw.js`'s own header comment also names.
- **Never promise PNG by checking that a binary exists** — the OG probe draws a card, then checks.
- sitegen.py needs Python 3.11+; 3.10 fails on the parser. `node --test` takes file paths, so a new
  JS test file must be named in `check.py` or it never runs.
- **Strip CSS comments before parsing a stylesheet.** A comment above a rule is otherwise captured
  as part of its selector, so the rule never matches and the check silently measures a fallback.
- **`requirements.txt` makes Vercel look for a Python entrypoint**, and it will find one — the
  `Handler` test double in `test_linkcheck.py`. `framework: null` in `vercel.json` is what stops it.
- **Never paste a value into a Vercel dashboard field.** A tab came along once and Vercel looked
  for a directory named `<tab>_site`. Put deploy settings in `vercel.json`, where the bytes are
  visible and reviewed.
- **Asset hrefs are relative and differ by depth** — the home page says `static/site.css`, a week
  page says `../../../../static/site.css`. Resolve against the page's own directory; against the
  site root, every route but the home page scores as pulling nothing.
- **Normalise HTML the same way on both sides of a comparison.** Turning tags into "" on one side and
  " " on the other makes `</strong>:` read as `:` in one and ` :` in the other, so every bold cell in
  the content looks missing when it is plainly there.
- **`subprocess.run(..., text=True)` needs `encoding="utf-8"`**; `r"\u00a7"` is six chars, not `§`.
- **A site copy string can live outside `content/`** — "how long it takes" was in the source and in
  `sitegen.py` at once. Grep both before calling a string removed.
- `python-docx` is not installed here by default: `pip install --break-system-packages -r
  requirements.txt`.
