# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 100 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-22 by Claude (sweep clean at 43 links, 0 failed; fixed a silently blind gate)

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
  writes (doc2 Weeks 12–13), not templates in the documents, so there is nothing to copy for them.
- **R19 facets**: section + cost label instead of phase/hours/credential, which doc3 does not state.
- **R24 JS budget**: 12 KB, not 10 KB (owner, for the library filter).
- **Cost labels**: two added, "Free to use" (not a course) and "Paid"; one card has none (no cost stated).
- **R18 JSON-LD** not added: `offers.price: 0` would be false for paid-certificate resources.

## Not verified, and why
- **Three links stay inconclusive**: OpenLearn (403), labour.gov.ng (503), search.cac.gov.ng (403).
  Bot blocks and a busy server, not breakage — all three were inconclusive in the first sweep too.
  A human should still open them once, because a 403 can hide a page that really moved.
- Real phone, iOS Safari, Lighthouse/3G (Phase 4). The law card fits one A4 page in headless
  Chromium's print-to-PDF; a real printer and Android print are untested. Browser checks were headless
  Chromium at 360 px: journey, reload, reset, corrupt/blocked storage, copy + denied clipboard,
  keyboard, JS off.

## Closed this round (link sweep acted on, 2026-10-22)
- **The re-run sweep is clean: 43 links — failed 0, inconclusive 3, ok 24, redirected 16.** Both DNS
  flakes from the first run cleared on their own; the AIHR cert problem left with the deleted link.
- **Three hard 404s removed**: CIPD's guides-and-resources and podcasts-and-webinars pages, and
  SHRM's charts page. The CIPD card was retitled "the free factsheet hub" and its "plus podcasts and
  open webinars" claim dropped, so the card stops promising what it no longer links to.
- **AIHR removed — it went paid, not dead.** The sweep only ever said *inconclusive*; checking the
  working host showed no free courses are left. Week 18 now uses **Alison's "HRIS in the Cloud and
  the Social Enterprise"** — already in the library, already mapped to Week 18, free Learner Record.
  AIHR is recorded in the paid-only list and the exclusions, each with its reason, not deleted quietly.
- **Three .docx re-shipped** (Doc2, Doc3, Doc5). Doc1 and Doc4 unchanged; `HR_Roadmap_Library.*`
  stayed frozen. The regression baseline moved with them: Doc3 is now **137 paras / 39 rels**.
- **Fixed a silently blind gate.** `check.py` decoded child output with the console's code page, so on
  a cp1252 Windows console style_audit's "…" marker arrived as "â€¦" and every voice hit was dropped:
  the audit passed while auditing nothing. Now decodes as UTF-8 at all four call sites.
- **The build now clears `_site` before writing.** It only ever wrote, so a deleted page stayed on
  disk and would be served from a deploy. Guarded: refuses to clear the repo or anything holding it.
- **The link sweep runs itself** (`.github/workflows/link-sweep.yml`, the repo's first CI): monthly at
  06:00 UTC, or by hand. It commits `checks/links.json` and opens — or updates — one issue when a
  link that answered before stops answering. `report_worsened.py` decides what "worse" means.

## Blocked on an owner decision
1. **Two voice-audit hits in the documents** (reported, not failed): doc4 §4.4 "what capability it
   **unlocks** for the team" and doc5 §5.6 "**Stakeholders** and judgement". Keep or reword; your call.
   Also: should `html-validate` become a required dev dependency (a `package.json`), or stay optional?
2. **Weeks 22–24 have no week pages.** doc2 hands them to doc5 in one paragraph. The progress
   meter therefore says "Weeks passed (Weeks 0–21)". Options unchanged: keep, or author week blocks.
3. **Production domain** (D4): needed for canonical URLs, `og:url` and the sitemap.
4. **`--wk-muted` is broken upstream** (self-referencing token); the site avoids it. Fix in `tokens.json`.
5. **Home copy**: "Six files, one plan" still reads as if six files are on the page.
6. **Library intro claims too much**: "each with the link, what it really costs, and how long it
   takes", but only some cards state a time. Site copy, not source; reword or drop "how long".

## Next justified step
Phase 3: the service worker (R28). The link sweep looks after itself now, so nothing about it needs
doing by hand unless it opens an issue.

## Session traps
- `python3`/`python` on the owner's PC are Microsoft Store stubs; real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` (`₦` breaks cp1252).
- The build clears `_site` itself (`clean_site()`), so a deleted page cannot survive into a deploy.
  Its guard refuses to clear anything that is, or contains, the repo — keep that guard.
- sitegen.py needs Python 3.11+; 3.10 fails on the parser. Check `check.py` before assuming a 3.10
  user can build. `node --test` takes a file path, not a directory, on Node 22.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum`; never patch the
  checksummed copy. Generated output goes to `_site/`, never `dist/` or `build/`.
- **The R1 guard in `audit.py` fails while `content/` has uncommitted edits.** Commit the approved
  content change first, then the gate can pass.
- **Both `content/*.json` files are keyed by card slug.** Deleting or retitling a doc3 card leaves a
  key pointing at a card that no longer exists, and the build fails. Update both files with the card.
- `python-docx` isn't installed here by default; `pip install --break-system-packages python-docx` first.
- **Never rely on `subprocess.run(..., text=True)` without `encoding="utf-8"`.** It decodes with the
  console code page, so non-ASCII rots silently on Windows; PYTHONIOENCODING only fixes the child.
