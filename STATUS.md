# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 160 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-24 by Claude (Fieldnotes redesign: tokens, type, and the webfonts dropped)

## Now
- `python3 tools/sitegen/check.py` is the gate (Python 3.11+): build · output
  audit · contrast · no-JS crawl · page weight · html-validate · tests · .docx
  regression · voice audit · sources untouched.
  **html-validate is required** (`npm install`); a missing binary FAILS rather than skips.
- **The site is on the Fieldnotes design system.** `design-system/tokens/fieldnotes.tokens.json`
  is the only source of values; `design-system/tools/build-tokens.mjs` compiles it to
  `artifacts/fieldnotes.css` (`--fn-*`), which every page links ahead of `static/site.css`.
  The Wakeout token set it replaced was extracted from an unrelated third-party site, which
  is why the site used to be green with rounded pills. Its evidence stays in
  `design-system/ref/`; nothing reads it and it is not in force.
- **No webfonts.** The owner chose to drop Fredoka and Space Grotesk on 2026-10-24. They
  were 48,628 B, 68% of a cold first visit. The heaviest route went **71,337 B → 22,285 B**
  (−69%) and fonts are now 0 B. Nothing emits `@font-face` and the build copies no woff2.
  The system faces are `ui-monospace…` for chrome and `system-ui` for prose.
- **All 25 weeks are real pages.** Weeks 22-24 come from doc5 §5.3-§5.8 and tick like any
  other week. Each of their rows names the doc5 section it came from, and a test fails a row
  that does not — that is what stops the site growing a second copy of doc5.
- **The site works offline (R28).** `_site/sw.js` carries a cache name hashed from everything
  else the build wrote, so any edit retires the old version by itself. It precaches the
  shell, all 25 week pages, the glossary and the law card (36 entries), serves from cache and
  refreshes in the background. `offline.js` shows a dismissible bar that never reloads on its own.
- **Share cards (R28).** One 1200x630 SVG per document plus home, drawn from the design
  system's own colour primitives. A test fails any card using a hex that is not a token.
- Ticks, resume line, reset (`progress.js`, `hrsite:v1`) · copy buttons (`copy.js`) · glossary
  search (`glossary.js`) · library filter (`library.js`) · course cards keyed to the tracker.
- **`/style-guide/` is a live route** (55 pages now) and is linked from every footer. It
  reads the compiled stylesheet at build time rather than restating values, so a component
  and the token behind it cannot drift. It carries no inline styles — the per-token classes
  it needs are generated into its head from the token file, because the repo bans inline
  style and a style guide is not a reason to exempt itself. `REDESIGN-ROADMAP.html` at the
  root is a visual map of the redesign, and is a snapshot rather than a live document.
- `/check/` lists all 43 external links and reads `checks/links.json`: "Last sweep:
  2026-10-22", 0 failed, 3 inconclusive. `link-sweep.yml` re-runs it monthly and opens an
  issue only when a link gets worse. Canonical, `sitemap.xml` and `og:image` only appear with
  `--site-url=https://…` (or `HR_SITE_URL`), since the domain is open.

## The redesign, and what it changed
- **Contrast improved while the palette changed.** 35 pairs measured, all clear AA; the worst
  is quiet text in a callout at **5.36:1** (previously the worst anywhere was 5.18:1). Body
  text on paper is 17.12:1. The gate reads colours back out of `site.css`, so recoloring text
  fails the build rather than passing on a stale assumption.
- **Two pairs forced a design decision.** Paper on the system blue is **4.32:1**, under the
  4.5 floor, so the share-card chip is ink-on-paper (17.12:1) instead. And the primary button
  is yellow with ink text (14.00:1) rather than a saturated fill with light text — which is
  what the reference does anyway.
- **Square corners, hard shadows, pink hover.** One `border-radius` (2px) on the smallest
  controls; everything structural is a right angle. Cards rest at `6px 6px 0 line` and lift
  `-3px` into `10px 10px 0 pink` on hover. `prefers-reduced-motion` removes the lift.
- **The chrome face is monospace; running copy is not.** Headings, labels, buttons, stamps
  and table heads use the mono stack; `p`, `li`, `td`, `blockquote` opt into the reading
  face. The reference does the same in reverse — its base is mono and its prose blocks opt
  out — but this site carries far more prose, so opting out per block would be unreadable.
- **The reference's hero is adopted as it ships** — a blue ground inside a thick cyan
  border, a ten pixel pink shadow, a huge tight-tracked title, a row of stat chips. The
  owner asked for it accepting poor contrast; **there was none to accept**: the eyebrow
  is a yellow chip carrying ink at 14.00:1 and the text is white on blue at 4.58:1, which
  clears AA even at the lead's body size. An earlier note here warned of a 3.54:1
  yellow-on-blue eyebrow — a pair computed while auditing the palette, not anything the
  reference renders. `STYLE-GUIDE.md` now says so.
- **The hero's stats are a real list.** The reference labels them with `aria-label` on a
  plain `div`, which assistive tech does not honour and `html-validate` rejects.
- **The style guide reports each colour the way it is used.** Measuring everything against
  ink alone would report that ink fails against ink, which is true and useless, so a light
  colour reports ink-on-it and a dark one reports it-on-paper. That is how `--fn-blue`
  surfaces as "large only" at 4.32:1 instead of being quietly reused.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}`, so derived counts cannot go stale.
- **R11 blocked storage**: one line saying progress is not being saved. **R19 facets**:
  section + cost, which doc3 states; not phase/hours/credential.
- **R5 list**: the intake template and reference-check script are learner outputs, not
  document templates. **R18 JSON-LD** omitted: `price: 0` would be false for paid resources.
- **R24 JS budget is 14 KB**, not 10 KB: 12 KB (owner, 2026-10-21), then 14 KB (ratified by
  the owner 2026-10-23). Raising a budget is mine to decide; reporting it is not optional.
- **`sw.js` is not counted as page JS** — it runs after load, so it is not page weight.
- **Weeks 22-24 rows are pointers, not prose.** Each cites its doc5 section; a test enforces it.
- **Cold-visit budget lowered 100 KB → 40 KB.** Dropping the fonts left the old figure
  measuring nothing (22 KB actual against a 100 KB ceiling). 40 KB still lets a route grow,
  but the fonts alone are 48,628 B, so this budget is now what stops them coming back.

## Phase 4 (pre-launch checks)
- **Contrast: done.** 25/25 clear AA, worst 5.36:1. Runs in the gate on every build.
- **JS-off crawl: done, and the site holds up.** `tools/sitegen/nojs.py` strips every
  `<script>` from all 54 built pages and holds what is left against `content/`. Every page
  keeps its `<h1>`, its prose, its week rows, its terms and its resources. **Nothing ships
  hidden without a stated reason**: an element carrying `hidden` must be a control or
  saved-progress state, and the check names the file and refuses a new one until classified.
- **Page weight: measured.** Heaviest route is **23,594 B** gzipped cold: HTML ~12 KB,
  CSS ~7 KB, JS ~4 KB, **fonts 0 B**. Budget 40 KB, all 55 routes inside it.
- **Still to do**: Lighthouse mobile, 3G cold load, Android print, and the post-deploy
  `curl -I` sweep. All four need a browser or a deploy, and there is neither here.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng
  (403). Bot blocks and a busy server, not breakage. A human should still open them once.
- Real phone, iOS Safari, Lighthouse/3G. The law card fits one A4 page in headless Chromium
  print-to-PDF; a real printer and Android print are untested.
- **The service worker has never run in a browser** — there is no browser here. `sw.test.js`
  covers its logic (10 tests, mutation-checked), but that proves the logic, not the platform.
  Before launch: open the deployed site, let it install, go offline, reload 10 times.
- **The share cards are SVG only, and most social platforms reject SVG.** No rasteriser exists
  here. PNGs appear by themselves on any machine with rsvg-convert, inkscape or a headless
  Chrome/Edge — the owner's PC included. Until then, shared links show no image.
- **No browser ran on the redesign.** The gate proves the rules are satisfied, not that the
  page looks right. Every value is tokenised and measured, but the visual result — square
  cards, pink hover lift, monospace headings — has not been seen by anyone. The owner should
  open it once before this ships.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.**
  The week pages follow doc2, which owns the plan. The documents disagree — the owner's call.

## Deployed
- **Live at https://fieldnotes-hr.vercel.app** — the owner deployed it on 2026-10-24.
- **`vercel.json` carries the deploy settings** so they live in the repo. `framework: null` is
  the load-bearing line: it stops Vercel auto-detecting a Python runtime and hunting for an
  entrypoint, which is how it once found the `Handler` test double in `test_linkcheck.py`.
- **`HR_SITE_URL` is set** by the owner (2026-10-24). Canonical URLs, `og:image` and
  `sitemap.xml` are live. The dashboard's build-command override may still be set — it takes
  precedence over `vercel.json`, so it should be cleared so the repo is the only source.
- Do **not** run `check.py` in the deploy: it needs python-docx and html-validate, and it
  does not build the site. `python3 tools/sitegen/sitegen.py` builds; `_site` is the output.

## Next justified step
**The owner opening the redesign in a browser.** The gate proves the rules are satisfied, not
that the page looks right, and no browser has run on it. After that, the four checks blocked
on a browser or a deploy: Lighthouse mobile on the four heaviest routes, the 3G cold load,
Android print, and the service-worker acceptance run (install, go offline, reload ten times).
Then the dashboard's build-command override wants clearing so `vercel.json` is the only
source of how the site builds.

## Session traps
- `python3` on the owner's PC is a Store stub; real one is `.../AppData/Local/Python/bin/python3`.
- **The `.docx` regression cannot see a word-for-word swap** — re-ship downloads by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- **`sitegen._cache` memoises parsed documents for the whole process**, so editing `content/`
  in a running process changes nothing until cleared; tests must clear it to see edits.
- **A trailing `;` in a CSS regex misses the last declaration in a rule.** The reference
  stylesheet is largely minified, so the final declaration before `}` has no semicolon; match
  `(?:^|[;{\s])PROP\s*:\s*([^;}]+)` or you find one radius in 27 KB for the wrong reason.
- **Strip CSS comments before parsing a stylesheet.** A comment above a rule is otherwise
  captured as part of its selector, so the rule never matches and the contrast check silently
  measures inherited body text instead.
- **`node_modules` and `_site` do not survive a sandbox reset** — run `npm install` before
  the gate if html-validate reports itself missing. Its absence FAILS the gate by design.
- **Never put generated output in `dist/` or `build/`** — those names are excluded from the
  persisted workspace snapshot. Design-system output lives in `design-system/artifacts/`.
- **`requirements.txt` makes Vercel look for a Python entrypoint**, and it will find one — the
  `Handler` test double in `test_linkcheck.py`. `framework: null` in `vercel.json` stops it.
- **Never paste a value into a Vercel dashboard field.** A tab came along once and Vercel
  looked for a directory named `<tab>_site`. Put deploy settings in `vercel.json`.
- **Asset hrefs are relative and differ by depth** — resolve against the page's own directory.
- `node --test` takes file paths, so a new JS test file must be named in `check.py` or it
  never runs. `python-docx` is not installed here by default.
