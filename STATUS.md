# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 80 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-21 by Claude (AGENTS.md filled; Phase 2 learner experience, link checker, SEO)

## Now
- Phase 1 and most of Phase 2 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.12+):
  build · output audit · Python tests · Node tests · .docx regression · voice audit on site-layer copy.
- Learner path: Week 0–21 blocks are tickable (`progress.js`, localStorage `hrsite:v1`); home and plan
  show the next block from the source table; footer resume line; two-step reset on the plan page.
- Copy: every blockquote in docs 4 and 5 and the law card has a Copy button (`copy.js`).
- `/check/` lists all external links (was 12, now every bare and parenthesised URL) and reads
  `checks/links.json` when `tools/sitegen/linkcheck.py` has written one. No sweep has run yet.
- SEO: unique titles, descriptions from each page's own text, Open Graph, `robots.txt`; canonical and
  `sitemap.xml` only with `--site-url=https://…` (or `HR_SITE_URL`), because the domain (D4) is open.

## Deviations from the PRD, made on purpose
- **R9 storage shape**: `{v:1, ts, done:{rowKey:1}, last}` instead of `weeks/courses/artefacts` maps.
  Weeks passed, artefacts and courses are derived from the build manifest, never stored, so no
  count can go stale when the curriculum changes.
- **R11 blocked storage**: the plan shows one line saying progress is not being saved, rather than
  nothing, so a private-mode learner is not misled.
- **R5 list**: the "12-question intake template" and "reference-check script" are outputs the learner
  writes (doc2 Weeks 12–13), not templates in the documents, so there is nothing to copy for them.
- **R18 JSON-LD** not added: `offers.price: 0` would be false for paid-certificate resources.

## Not verified, and why
- **Link sweep**: neither the build workspace nor the owner's PC shell could reach external sites.
  The checker is tested against a local server only. Run `python3 tools/sitegen/linkcheck.py` on a
  machine with internet, commit `checks/links.json`, rebuild.
- Real phone, iOS Safari, Lighthouse/3G, print to A4 (Phase 4). Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy + denied clipboard,
  keyboard, JS off.
- JS budget: shipped JS is just under R24's 10 KB (`python3 tools/sitegen/audit.py`), so little room is left.

## Blocked on an owner decision
1. **Weeks 22–24 have no week pages.** doc2 hands them to doc5 in one paragraph. The progress
   meter therefore says "Weeks passed (Weeks 0–21)". Options unchanged: keep, or author week blocks.
2. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap.
3. **`--wk-muted` is broken upstream** (self-referencing token); the site avoids it. Fix in `tokens.json`.
4. **OFL licence text** must ship with the fonts before a public deploy.
5. **Home copy**: "Six files, one plan" still reads as if six files are on the page.
6. **CAC link** in doc5 Support A is written as "(https://…)", which the renderer leaves as plain
   text. It is now checked by the sweep; making it clickable needs a markdown edit (your call).
7. **R7 gap**: the legal pages (`/4/nigeria/`, the law card) do not yet show "Not legal advice;
   current to the date checked." It is a build-template line, not new content; add it when approved.

## Next justified step
Run the link sweep from a connected machine, then Phase 2.5 (library filter, glossary search) and
course-card ticks (R10 lists them; course progress is currently ticked in the Support A tracker).

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- sitegen.py needs Python 3.12+: a backslash inside an f-string (PEP 701).
- `node --test` takes a file path, not a directory, on Node 22.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum`; never patch the
  checksummed copy.
- Generated output goes to `_site/`, never `dist/` or `build/`.
