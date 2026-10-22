# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 100 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-22 by Claude (weeks 22-24 are real pages; six owner decisions closed)

## Now
- Phases 1 and 2 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.11+):
  build · output audit · html-validate · tests · .docx regression · voice audit on every page ·
  sources untouched. **html-validate is required**: `npm install` (see `package.json`), and the gate
  now FAILS rather than skips when the binary is missing.
- **All 25 weeks are real pages.** Weeks 22-24 are built from doc5 §5.3-§5.8 and are tickable like
  every other week. The progress meter derives its own range (`Weeks 0-24`), so it cannot go stale
  again. Each of their rows names the doc5 section it comes from — `test_site.py` fails a row that
  describes work without citing it, which is what stops the site growing a second copy of doc5.
- Learner path: every week's blocks are tickable (`progress.js`, localStorage `hrsite:v1`); home and
  plan show the next block from the source table; footer resume line; two-step reset on the plan page.
- Copy: every blockquote in docs 4 and 5 and the law card has a Copy button (`copy.js`).
- Glossary search (R8) on `/1/start-here/` filters doc1's term table as you type (`glossary.js`).
- Library (R19 as decided): cards grouped under doc3's three sections; filter by section and cost
  label, kept in the URL (`library.js`). Cost labels come from `content/resource-verdicts.json`.
- Course cards (R10): each lists its Support A courses with ticks sharing the tracker's keys
  (`content/course-cards.json`, owner-approved). Non-course cards have none.
- `/check/` lists all external links (every bare and parenthesised URL, **43 of them**) and reads
  `checks/links.json`. It now reads **"Last sweep: 2026-10-22"** — 0 failed, 3 inconclusive.
- SEO: unique titles, descriptions from each page's own text, Open Graph, `robots.txt`; canonical and
  `sitemap.xml` only with `--site-url=https://…` (or `HR_SITE_URL`), because the domain (D4) is open.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}` instead of `weeks/courses/artefacts` maps.
  Weeks passed, artefacts and courses are derived from the build manifest, never stored, so no
  count can go stale when the curriculum changes.
- **R11 blocked storage**: the plan shows one line saying progress is not being saved, rather than
  nothing, so a private-mode learner is not misled.
- **R5 list**: the "12-question intake template" and "reference-check script" are outputs the learner
  writes (doc2 Weeks 12-13), not templates in the documents, so there is nothing to copy.
- **R19 facets**: section + cost label, not phase/hours/credential, which doc3 does not state.
- **R24 JS budget**: 12 KB, not 10 KB (owner, for the library filter).
- **Cost labels**: two added, "Free to use" (not a course) and "Paid"; one card has none (no cost stated).
- **Weeks 22-24 rows are pointers, not prose.** Each cites its doc5 section instead of restating it;
  this is the one thing the source-of-truth rule forbids, so the test enforces it structurally.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng (403) —
  bot blocks and a busy server, not breakage. A human should still open them once, since a 403 can
  hide a page that really moved.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless
  Chromium's print-to-PDF; a real printer and Android print are untested. Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy, keyboard, JS off.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.** The week
  pages follow doc2, which owns the plan. The documents disagree — the owner's call.

## Closed this round (six owner decisions, 2026-10-22)
- **Weeks 22-24 authored** from doc5's own sections — no new content invented. Doc2 re-shipped
  (100 → 106 paras, 25 → 28 tables); the regression baseline moved with it.
- **doc4 §4.4 reworded**: "what capability it **unlocks** for the team" → "what capability it
  **gives** the team". Doc4 re-shipped. The swap is invisible to every gate column (one word for one
  word), so the re-ship had to be done deliberately — nothing would ever have prompted for it.
- **doc5 §5.6 "Stakeholders and judgement" kept**, and marked `accepted` in `KNOWN_SOURCE_HITS`, so
  the voice audit reports it without asking again. Entries are now `(category, snippet, where, status)`.
- **html-validate is required**: `package.json` declares it, `node_modules/` is gitignored, and a
  missing binary fails the gate. One-line reversal if the owner ever wants it forgiving again.
- **Home copy reworded**: "Six files, one plan" → "Five documents, one plan — plus the full research
  archive". The library intro dropped "how long it takes" in **both** places it lived (`content/`
  and a hardcoded string in `sitegen.py`).
- `--wk-muted` left as-is: **decided won't-fix**. Nothing reads the token; regenerating the
  checksummed design system would be disproportionate.

## Blocked on an owner decision
1. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap. `learnhr.vercel.app`
   is likely but unconfirmed — nothing is set anywhere until the URL is real. When it is: build command
   `python3 tools/sitegen/sitegen.py`, output dir `_site`, and set `HR_SITE_URL` in Vercel's env
   dashboard. Do **not** run `check.py` in the deploy: it needs python-docx and html-validate, and it
   does not build the site.

## Next justified step
Phase 3: the service worker (R28). The link sweep looks after itself, so nothing about it needs
doing by hand unless it opens an issue.

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- **The `.docx` regression cannot see a word-for-word swap.** It compares paragraph, word, table and
  hyperlink counts, so reworded source silently forks the download. After any content edit, re-ship
  the affected documents on purpose and move the gate numbers by hand.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits** — commit first.
- The build clears `_site` itself (`clean_site()`), so a deleted page cannot survive into a deploy.
  Its guard refuses to clear anything that is, or contains, the repo — keep that guard.
- **A site copy string can live outside `content/`** — "how long it takes" was in both. Grep both.
- sitegen.py needs Python 3.11+; 3.10 fails on the parser. `node --test` takes a file path, not a
  directory, on Node 22.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum`; never patch the
  checksummed copy. Generated output goes to `_site/`, never `dist/` or `build/`.
- **Both `content/*.json` files are keyed by card slug**; retitling a doc3 card breaks the build.
- `python-docx` isn't installed here by default; `pip install --break-system-packages -r requirements.txt`.
- **Never rely on `subprocess.run(..., text=True)` without `encoding="utf-8"`** — non-ASCII rots
  silently on a Windows console. PYTHONIOENCODING only fixes the child.
- **A regex escape inside a raw string is not an escape**: `r"\u00a7"` is six characters. Write `§`.
