# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 160 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-24 by Claude (a browser ran; it found a real bug in the tap targets)

## Now
- `python3 tools/sitegen/check.py` is the gate: build · output audit · contrast · no-JS crawl ·
  page weight · html-validate · tests · .docx regression · **browser checks** · voice audit ·
  sources untouched. **html-validate is required** (`npm install`); a missing binary FAILS.
- **A browser now runs here, and the site passes 40/40 checks in it.** The gate runs
  `tools/sitegen/browser_check.mjs` when `CHROME_PATH` names a binary and something is served on
  `localhost:8000`; otherwise it prints `SKIP` and stays green. It must be run **by hand** — it
  is not in `npm test` and nothing else reminds you. AGENTS.md says how to get a Chromium, which
  is not in the repo and is not installed by `npm install`.
- **The site is on the Fieldnotes design system.** `design-system/tokens/fieldnotes.tokens.json`
  (122 tokens) is the only source of values; `build-tokens.mjs` compiles it to
  `artifacts/fieldnotes.css` (`--fn-*`), linked ahead of `static/site.css`. The Wakeout set it
  replaced came from an unrelated third-party site, which is why the site used to be green with
  rounded pills. Its evidence stays in `design-system/ref/`; nothing reads it.
- **No webfonts.** The owner dropped Fredoka and Space Grotesk on 2026-10-24: 48,628 B, 68% of a
  cold first visit. The heaviest route went **71,337 B → 22,285 B** (−69%); fonts now 0 B.
- **All 25 weeks are real pages.** Weeks 22-24 come from doc5 §5.3-§5.8. Each row names the doc5
  section it came from, and a test fails a row that does not — that is what stops the site
  growing a second copy of doc5.
- **The site works offline, now proven in a browser.** `_site/sw.js` carries a cache name hashed
  from everything else the build wrote, so any edit retires the old version by itself. Measured:
  **10/10 offline reloads served**, offline nudge on screen at 370x80, 36 precached entries.
- **Share cards (R28).** One 1200x630 SVG per document plus home, drawn from the system's own
  colour primitives. Ticks, resume line and reset (`progress.js`, `hrsite:v1`) · copy buttons
  (`copy.js`) · glossary search (`glossary.js`) · library filter (`library.js`).
- **`/style-guide/` is a live route** (55 pages), linked from every footer. It reads the compiled
  stylesheet at build time rather than restating values, so a component and its token cannot
  drift. It carries no inline styles — the per-token classes it needs are generated into its head
  from the token file, since the repo bans inline style and a style guide is no reason to exempt
  itself. `REDESIGN-ROADMAP.html` is a visual map, and a snapshot not a live document.
- `/check/` lists all 43 external links and reads `checks/links.json`: "Last sweep: 2026-10-22",
  0 failed, 3 inconclusive. Canonical, `sitemap.xml` and `og:image` need `--site-url=https://…`.

## The bug a browser found that no static check could
- **Six control heights were set from the fluid spacing scale**, and a fluid token collapses on a
  phone. `--fn-space-12` is `clamp(28px, 6vw, 48px)`, so `.btn` rendered **38px** at 390px instead
  of 48px and nav links sat at **32px** — both under the 44px floor, on the device where it
  matters most. The token was correct and the declaration well-formed; only the rendered size was
  wrong, so nothing in the gate could see it.
- **Fixed with two fixed tokens**: `dimension.control.height` **48px**,
  `dimension.control.height-nav` **44px**. Spacing may be fluid; a control's height may not,
  because a thumb does not get smaller on a phone. Nav links are standalone targets, so they get
  no WCAG 2.2 inline-link allowance.
- **A guard now stops it recurring** — `audit.py` fails any control selector (`.btn`, `.tick`,
  `.site-nav a`, `input`, `select`, `button`) whose `min-height` is a `--fn-space-*` token. It
  walks rules rather than matching declarations, because a banner's min-height may be fluid and
  nothing is tapped. **Mutation-tested**: fails on the planted bug, passes clean on the fix.

## The redesign, and what it changed
- **Contrast improved while the palette changed.** 35 pairs measured statically, all clear AA,
  worst 5.36:1; a browser re-measures the composited result, worst 4.58:1. The gate reads colours
  back out of `site.css`, so recoloring text fails the build.
- **Paper on the system blue is 4.32:1**, under the 4.5 floor, so the share-card chip is
  ink-on-paper (17.12:1) and the primary button yellow with ink text (14.00:1).
- **Square corners, hard shadows, pink hover.** One `border-radius` (2px) on the smallest
  controls. Cards rest at `6px 6px 0 line` and lift `-3px` into `10px 10px 0 pink` on hover;
  `prefers-reduced-motion` removes the lift.
- **The chrome face is monospace; running copy is not.** Headings, labels, buttons, stamps and
  table heads use the mono stack; `p`, `li`, `td`, `blockquote` opt into the reading face.
- **The reference's hero is adopted as it ships**, and the owner asked for it accepting poor
  contrast — **there was none to accept**: the eyebrow is a yellow chip carrying ink at 14.00:1
  and the text white on blue at 4.58:1, which clears AA even at the lead's body size. An earlier
  note here warned of a 3.54:1 yellow-on-blue eyebrow — a pair computed while auditing the
  palette, not anything the reference renders. `STYLE-GUIDE.md` now says so.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}`, so derived counts cannot go stale.
- **R11 blocked storage**: one line saying progress is not being saved. **R19 facets**: section +
  cost, which doc3 states; not phase/hours/credential.
- **R5 list**: the intake template and reference-check script are learner outputs, not document
  templates. **R18 JSON-LD** omitted: `price: 0` would be false for paid resources.
- **R24 JS budget is 14 KB**, not 10 KB: 12 KB (owner, 2026-10-21), then 14 KB (ratified
  2026-10-23). **Raising a budget is mine to decide; reporting it is not optional.**
- **`sw.js` is not counted as page JS** — it runs after load, so it is not page weight. **Weeks
  22-24 rows are pointers, not prose**: each cites its doc5 section.
- **Cold-visit budget lowered 100 KB → 40 KB.** Dropping the fonts left the old figure measuring
  nothing. The fonts alone are 48,628 B, so this budget is what stops them coming back.
  **Tightened on 2026-10-24 and not yet acknowledged by the owner — mention it again.**

## Phase 4 (pre-launch checks) — all four done, in a real engine
- **Contrast: done.** 25/25 clear AA statically, worst 5.36:1; re-measured as composited in
  Chromium, worst 4.58:1. Runs in the gate on every build.
- **JS-off crawl: done, and the site holds up.** `nojs.py` strips every `<script>` from all 55
  built pages and holds what is left against `content/`. **Nothing ships hidden without a stated
  reason**: an element carrying `hidden` must be a control or saved-progress state, and the check
  refuses a new one until it is classified.
- **Page weight: measured.** Heaviest route **23,594 B** gzipped cold: HTML ~12 KB, CSS ~7 KB,
  JS ~4 KB, **fonts 0 B**. Budget 40 KB, all 55 routes inside it.
- **Layout: no horizontal overflow at 320 / 390 / 430 / 768 / 1024 / 1440 / 1920.** At 320 and 390
  a table and its caption exceed the viewport but the *document* does not scroll, so they are
  contained rather than clipped.
- **3G cold load** (400 kbps, 2000 ms RTT, cache and worker cold, fresh context per route): first
  contentful paint **4.9 s** on `/`, `/2/plan/`, `/3/library/`, `/5/getting-the-job/`; transfers
  28.7 / 46.0 / 16.3 / 35.0 KB. Those are **uncompressed** — `python -m http.server` sends no
  gzip — so they run above the gate's gzipped figures.
- **Print: done.** Card shadow `6px 6px 0 line` → `none`, hero border `0px`, hero shadow `none`,
  body type 12.32px, 5/5 present chrome elements hidden, PDF 124 KB.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng
  (403) — bot blocks and a busy server, not breakage. A human should still open them once.
- **No real phone, no iOS Safari, no Lighthouse.** The layout sweep, the 3G figure and print are
  all headless Chromium. Android print is untested; the check exercises CSS, not a pipeline.
- **Nobody has looked at it.** The checks are measured, not seen — this session had no vision, so
  every claim above is a number read out of the engine. Screenshots of five pages at 390px and
  1440px are in `~/shots/`. A design system can be fully satisfied and still look wrong.
- **Share cards are SVG only, and most social platforms reject SVG.** PNGs appear by themselves on
  any machine with rsvg-convert, inkscape or a headless Chrome/Edge — the owner's PC included.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.** The
  week pages follow doc2, which owns the plan. The documents disagree — the owner's call.

## Deployed
- **Live at https://fieldnotes-hr.vercel.app** — the owner deployed it on 2026-10-24.
- **`vercel.json` carries the deploy settings** so they live in the repo. `framework: null` is the
  load-bearing line: it stops Vercel auto-detecting a Python runtime and hunting for an
  entrypoint, which is how it once found the `Handler` test double in `test_linkcheck.py`.
- **`HR_SITE_URL` is set** by the owner; canonical URLs, `og:image` and `sitemap.xml` are live.
  The dashboard's build-command override may still be set — it takes precedence over
  `vercel.json`, so it should be cleared so the repo is the only source.
- Do **not** run `check.py` in the deploy: it needs python-docx and html-validate, and it does not
  build the site. `python3 tools/sitegen/sitegen.py` builds; `_site` is the output.

## Next justified step
**The owner opening the redesign in a browser** — every rule is satisfied, but nobody has *seen*
it; screenshots are in `~/shots/`. Then clear the dashboard's build-command override so
`vercel.json` is the only source of how the site builds.

## Session traps
- `python3` on the owner's PC is a Store stub; the real one is `.../AppData/Local/Python/bin/python3`.
- **The .docx regression cannot see a word-for-word swap** — re-ship downloads by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- **`sitegen._cache` memoises parsed documents for the whole process**, so editing `content/` in a
  running process changes nothing until cleared; tests must clear it to see edits.
- **A trailing `;` in a CSS regex misses the last declaration in a rule** — the reference
  stylesheet is largely minified, so the final declaration before `}` has no semicolon. **Strip
  CSS comments before parsing**: a comment otherwise becomes part of the selector, and the
  contrast check silently measures inherited body text instead.
- **`node_modules` and `_site` do not survive a sandbox reset** — run `npm install` before the
  gate if html-validate reports itself missing; its absence FAILS by design. **Never put generated
  output in `dist/` or `build/`** — those are excluded from the persisted snapshot.
- **`requirements.txt` makes Vercel hunt for a Python entrypoint**, and it finds the `Handler`
  test double in `test_linkcheck.py`; `framework: null` stops it. **Never paste a value into a
  Vercel dashboard field** — a tab came along once and Vercel looked for `<tab>_site`. Asset
  hrefs are relative and differ by depth. `node --test` takes file paths, so a new JS test must
  be named in `check.py` or it never runs.

## Session traps
- **Browser traps live in `tools/sitegen/browser_check.mjs`**, beside the code they describe —
  the `LD_LIBRARY_PATH` requirement, `offsetParent` being null for fixed elements, a warm service
  worker measuring the cache instead of the connection, FCP already counting the RTT, probing for
  elements a page does not have, and the inline-link exemption in a tap-target sweep.
