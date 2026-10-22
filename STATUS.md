# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 100 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-22 by Claude (link sweep acted on: 4 links removed, AIHR paywall, 3 .docx re-shipped)

## Now
- Phases 1 and 2 are built. `python3 tools/sitegen/check.py` is the gate (Python 3.11+):
  build · output audit · html-validate · tests · .docx regression · voice audit on every page ·
  sources untouched. html-validate is not a repo dependency: the gate says SKIP where it isn't installed.
- Learner path: Week 0–21 blocks are tickable (`progress.js`, localStorage `hrsite:v1`); home and plan
  show the next block from the source table; footer resume line; two-step reset on the plan page.
- Copy: every blockquote in docs 4 and 5 and the law card has a Copy button (`copy.js`).
- Glossary search (R8) on `/1/start-here/`: filters doc1's term table as you type (`glossary.js`).
- Library (R19 as decided): cards grouped under doc3's three sections; filter by section and cost
  label, kept in the URL (`library.js`). Cost labels come from `content/resource-verdicts.json`.
- Course cards (R10): each course card lists its Support A tracker courses with ticks that
  share the tracker's keys (`content/course-cards.json`, owner-approved). Non-course cards have none.
- `/check/` lists all external links (was 12, now every bare and parenthesised URL) and reads
  `checks/links.json` when `tools/sitegen/linkcheck.py` has written one. **There are 43 links now.**
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
- **`checks/links.json` is still not committed.** The sweep was run on the owner's PC (2026-10-21,
  47 links: failed 3, inconclusive 5, ok 23, redirected 16), but four of those links have since been
  deleted, so that file is already stale. **Re-run it on a connected machine, commit the result and
  rebuild** — only then does `/check/` show a sweep. This sandbox cannot reach the hosts.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless
  Chromium's print-to-PDF; a real printer and Android print are untested. Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy + denied clipboard,
  keyboard, JS off.

## Closed this round (link sweep acted on, 2026-10-22)
- **Three hard 404s removed**: CIPD's guides-and-resources and podcasts-and-webinars pages, and
  SHRM's charts page. The CIPD card was retitled "the free factsheet hub" and its "plus podcasts and
  open webinars" claim dropped, so the card stops promising what it no longer links to.
- **AIHR removed — it went paid, not dead.** The sweep only ever said *inconclusive* (its certificate
  does not cover `aihr.academy`); checking the working host showed the real problem: no free courses
  are left. AIHR was Credential #7 and Week 18's main block, so the hole ran through doc2, doc3 and
  doc5. Week 18 now uses **Alison's "HRIS in the Cloud and the Social Enterprise"** — already in the
  library, already mapped to Week 18, free to study with a free Learner Record. Nothing new sourced.
- **AIHR is recorded, not deleted silently**: it joins the paid-only list (doc3 §1) and the record of
  what was left out (Support A), each with its reason, so a reader who finds an old "AIHR is free"
  post is not misled.
- **Three .docx re-shipped** (Doc2, Doc3, Doc5), rebuilt from the edited markdown. Doc1 and Doc4 are
  unchanged; `HR_Roadmap_Library.*` stayed frozen. The regression baseline moved with them: Doc3 is
  now **137 paragraphs / 39 hyperlink rels** (was 142/43). Re-shipping downloads was owner-approved.

## Blocked on an owner decision
1. **Two voice-audit hits in the documents** (reported, not failed, by the gate): doc4 §4.4 "what
   capability it **unlocks** for the team" (puffed-up list) and doc5 §5.6 "**Stakeholders** and
   judgement" (consultant-speak list; it is an interview question group). Keep or reword; your call.
   Also: should `html-validate` become a required dev dependency (a `package.json`), or stay optional?
2. **Weeks 22–24 have no week pages.** doc2 hands them to doc5 in one paragraph. The progress
   meter therefore says "Weeks passed (Weeks 0–21)". Options unchanged: keep, or author week blocks.
3. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap.
4. **`--wk-muted` is broken upstream** (self-referencing token); the site avoids it. Fix in `tokens.json`.
5. **Home copy**: "Six files, one plan" still reads as if six files are on the page.
6. **Library intro claims too much**: "each with the link, what it really costs, and how long it
   takes", but only some cards state a time. Site copy, not source; reword or drop "how long".

## Next justified step
Re-run `python3 tools/sitegen/linkcheck.py` on a connected machine (43 links now), commit
`checks/links.json`, rebuild — that closes 0.2 and R14. Then Phase 3: the service worker (R28).
A cron workflow to run the sweep and open an issue on a changed outcome is offered, not started.

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- sitegen.py needs Python 3.11+: an f-string there still parses on 3.11, and 3.10 fails on the
  parser before that. Check `check.py` before assuming a 3.10 user can build.
- `node --test` takes a file path, not a directory, on Node 22.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum`; never patch the
  checksummed copy.
- Generated output goes to `_site/`, never `dist/` or `build/`.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits.** Commit the approved
  content change first, then the gate can pass.
- **Both `content/*.json` files are keyed by card slug.** Deleting or retitling a doc3 card leaves a
  key pointing at a card that no longer exists, and the build fails. Update both files with the card.
- `python-docx` is not installed here by default; `python3 -m pip install --break-system-packages
  python-docx` is needed before the .docx regression will do anything but report SKIP.
