# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 80 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-21 by Buffy (Freebuff) — audit-and-fix pass

## Now
- **Phase 1 core is green.** `make check` exits 0: build, 14/14 audit checks, .docx gate.
- Not started: Phase 2 (progress, copy buttons, filters), Phase 3 (sitemap, JSON-LD, service
  worker), the 47-URL network sweep (task 0.2).

## Last done — audit pass, five defects fixed
- **`external_urls()` collected 12 of 47 URLs** — it matched only the markdown `[t](url)`
  form; the corpus also uses bare and parenthesised URLs. Now all three patterns: **47/47**.
- **The build crashed on Python < 3.12** — one f-string used an escaped quote inside its
  expression (PEP 701). Rewritten; runs on 3.11. Minimum version now in AGENTS.md.
- **`(https://…)` was never linkified** — `URL_RE`'s `(?<!\()` lookbehind skipped it, so the
  CAC scam-check link in doc5 was dead text. Fixed in `tools/sitegen` only: `docx_render.py`
  and the frozen .docx are untouched, and their gate is still green.
- **`/5/templates/` held 1 of R5's blocks** — now three: the 90-word note, the CV bullet
  table, the follow-up messages. The other two R5 items aren't in the documents (below).
- **No declared environment** — added `requirements.txt`, `Makefile` (`make check`), and the
  missing R1 gate: `audit.py` now fails the build when `git diff -- content/` is non-empty.
  Proven it can fail: planting an edit in doc1 turns it red.
- **Font licence added** — `OFL-Fredoka.txt`, `OFL-Space-Grotesk.txt` (OFL 1.1, google/fonts)
  ship to `_site/fonts/`; clears the public-deploy blocker. No checksum touched.

## Numbers that are proven (rerun the command, don't trust the line)
- Routes: **52** = home, 5 doc pages, plan + **22** week pages, library + 20 cards, law card,
  templates, check, downloads. `find _site -name index.html | wc -l`
- `make check` → 14/14. Largest page **27,426 B** (R24 allows 120 KB); CSS **4,985 B** gz
  (45 KB); JS **0 B** (10 KB). **238** `data-k` keys, all unique. **35** tables, all captioned.
- **47** URLs on `/check/`, all "not yet swept". .docx gate: paras 51/100/142/87/118,
  hyperlink rels 0/0/43/8/0 — unchanged.

## Decisions locked (owner, 2026-10-21)
- **D1** whole minified `wakeout.css`; **D5** stickers −2°…−6°; **R20** hand-written token-only
  layer (`.wk-*` deviation recorded); table = guide geometry + 12px; print layer token-only.

## Not verified, and why
- **The 47 links have never been network-checked.** Last checked by hand 20 October 2026;
  this sandbox reaches only github/npm/pypi, so task 0.2 could not run. Highest-value job left.
- **Print to A4** (R22): layer written, no PDF produced. **Lighthouse / 3G** (R25),
  keyboard-only run, JS-disabled crawl: Phase 4.
- **Nobody has looked at it.** The design was checked by computed styles and DOM, not by eye.
  Say so before claiming it "looks right".
- **Copy buttons do not exist** (step 2.4); **`html-validate`** (task 1.6) is not wired in.

## Blocked on an owner decision
1. **R5 names two blocks that aren't copy.** The "12-question intake template" and the
   "reference-check script" appear in doc2 only as *artefacts the learner writes* (Weeks 13
   and 12). Rendering them means inventing content, which R1 forbids. Write them, or drop
   them from R5. Everything else in R5 now renders.
2. **Weeks 22–24 have no week tables** — doc2 hands them to doc5 in one paragraph, so there
   are 22 week pages, not the 25 the route map and the "/24" progress bar assume. Keep 22, or
   author three week blocks (new copy — needs your words).
3. **`--wk-muted` is broken upstream.** `wakeout.css` declares it twice, the second time as a
   reference to itself; same for `--wk-muted-foreground`. The site uses `--wk-ink-70` and
   `--wk-sunrise`. The fix belongs in `tokens.json` — your call.
4. **`·`, `—`, `→` and `☐` are absent from the body face** (Space Grotesk latin subset; `·`
   and `—` are in Fredoka, so headings and body disagree). They fall back to a system font.
   Found by reading the woff2 cmaps. Cosmetic — the ₦ problem in miniature.
5. **Home copy**: "Six files, one plan" still reads as if six files are on the page.
6. **`latin-ext` fonts ship but are never fetched** — no `unicode-range` on the `@font-face`,
   so the browser takes the first `src` only. 11 KB of dead deploy weight, and no fallback for
   a glyph outside latin. Fixing it means editing the checksummed `wakeout.css`.

## Next justified step
Task 0.2, the 47-URL sweep — the one thing that makes every claim on the site true or false.
Then Phase 2.1: `progress.js` against the 238 stable `data-k` keys, every `localStorage`
access in a try and `aria-pressed` on the toggles.

## Session traps (the code-level ones now live in AGENTS.md Gotchas)
- `python3`/`python` on the owner's PATH are Microsoft Store stubs that exit 49. Real
  interpreter: `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8`
  before printing content: the console is cp1252 and `₦` raises UnicodeEncodeError.
- `/tmp` is not a path for Windows Python — use a workspace dir or `tempfile`.
- Generated output goes to `_site/`, never `dist/` or `build/` — those names are dropped.
