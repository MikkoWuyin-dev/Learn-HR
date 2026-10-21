# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 100 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-21 by Claude (Phase 2 done: course-card ticks; 2.5 glossary + library filter)

## Now
- Phases 1 and 2 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.12+):
  build · output audit · html-validate · tests · .docx regression · voice audit on every page ·
  sources untouched. html-validate is not a repo dependency: the gate says SKIP where it isn't installed.
- Learner path: Week 0–21 blocks are tickable (`progress.js`, localStorage `hrsite:v1`); home and plan
  show the next block from the source table; footer resume line; two-step reset on the plan page.
- Copy: every blockquote in docs 4 and 5 and the law card has a Copy button (`copy.js`).
- Glossary search (R8) on `/1/start-here/`: filters doc1's term table as you type (`glossary.js`).
- Library (R19 as decided): cards grouped under doc3's three sections; filter by section and cost
  label, kept in the URL (`library.js`). Cost labels come from `content/resource-verdicts.json`.
- Course cards (R10): each of the 10 course cards lists its Support A tracker courses with ticks that
  share the tracker's keys (`content/course-cards.json`, owner-approved). Non-course cards have none.
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
- **R19 facets**: section + cost label instead of phase/hours/credential, which doc3 does not state.
- **R24 JS budget**: 12 KB, not 10 KB (owner, for the library filter).
- **Cost labels**: two added, "Free to use" (not a course) and "Paid"; one card has none (no cost stated).
- **R18 JSON-LD** not added: `offers.price: 0` would be false for paid-certificate resources.

## Not verified, and why
- **Link sweep**: neither the build workspace nor the owner's PC shell could reach external sites.
  The checker is tested against a local server only. Run `python3 tools/sitegen/linkcheck.py` on a
  machine with internet, commit `checks/links.json`, rebuild.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless
  Chromium's print-to-PDF; a real printer and Android print are untested. Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy + denied clipboard,
  keyboard, JS off.

## Blocked on an owner decision
1. **Two voice-audit hits in the documents** (reported, not failed, by the gate): doc4 §4.4 "what
   capability it **unlocks** for the team" (puffed-up list) and doc5 §5.6 "**Stakeholders** and
   judgement" (consultant-speak list; it is an interview question group). Keep or reword; your call.
   Also: should `html-validate` become a required dev dependency (a `package.json`), or stay optional?
2. **Weeks 22–24 have no week pages.** doc2 hands them to doc5 in one paragraph. The progress
   meter therefore says "Weeks passed (Weeks 0–21)". Options unchanged: keep, or author week blocks.
3. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap.
4. **`--wk-muted` is broken upstream** (self-referencing token); the site avoids it. Fix in `tokens.json`.
5. **OFL licence text** must ship with the fonts before a public deploy.
6. **Home copy**: "Six files, one plan" still reads as if six files are on the page.
7. **CAC link** in doc5 Support A is written as "(https://…)", which the renderer leaves as plain
   text. It is now checked by the sweep; making it clickable needs a markdown edit (your call).
8. **Library intro claims too much**: "each with the link, what it really costs, and how long it
   takes", but only some cards state a time. Site copy, not source; reword or drop "how long".

## Next justified step
The link sweep from a connected machine (closes 0.2 and R14), then Phase 3: the service worker (R28).

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- sitegen.py needs Python 3.12+: a backslash inside an f-string (PEP 701).
- `node --test` takes a file path, not a directory, on Node 22.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum`; never patch the
  checksummed copy.
- Generated output goes to `_site/`, never `dist/` or `build/`.
