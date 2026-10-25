# AGENTS.md — HR Library (Learn HR)

Loaded at the start of every session, so it holds only what changes rarely. Anything with a
number, a date or "currently" belongs in `STATUS.md`.
**First, read `HANDOVER.md`** — sandbox-reset recovery, the owner's standing rules, skills, traps.

## What this is

A free website that turns five finished documents into a 24-week path from zero HR background to
a first job as a recruiter or HR assistant in Nigeria. The learner may have no money, no laptop and
prepaid data. Success: a stranger follows the site for four weeks without opening a .docx, and a
returning visitor sees at once where they stopped. The site teaches nothing the documents don't.
Project class: product (public, static, read on phones) — Python from Markdown, no backend.

## Commands

- Python 3.11+ is required (3.10 and older fail on the parser). The .docx regression also needs
  `python-docx`, declared in `requirements.txt`.
- Build: `python3 tools/sitegen/sitegen.py`, written to `_site/`. Add `--site-url=https://…` (or set
  `HR_SITE_URL`) to emit canonical URLs and `sitemap.xml`.
- Preview: `python3 -m http.server 8000 --directory _site`. Internal links are root-absolute, so the
  site must be served from `/`, not opened as files.
- **Gate:** `python3 tools/sitegen/check.py` must exit 0 before work is called done. It runs the build,
  the output audit (`audit.py`), `html-validate` (rules in `.htmlvalidate.json`; reported as SKIP when
  not installed: `npm i -g html-validate@9`), the Python and Node tests, the .docx regression, the voice
  audit over every generated page, and a check that the build left `content/` and `downloads/` untouched.
- Narrow tests: `python3 -m unittest discover -s tools/sitegen/tests -p test_site.py` ·
  `node --test tools/sitegen/tests/progress.test.js` (Node 22 wants a file, not a folder; build first).
- Link sweep (by hand, needs internet): `python3 tools/sitegen/linkcheck.py [--dry-run] [--strict]`
  writes `checks/links.json`; commit it and rebuild so `/check/` shows it. Visitors never trigger it.
- Source checks: `cd scripts && python3 validate_build.py ../content/docs/src/doc*.md` ·
  `python3 style_audit.py FILE` (it exits 0 on banned phrases; `check.py` is what fails on them).

## Browser checks

Chromium is not installed by this repo — 209 MB, and it cannot be required — so these are skipped
unless `CHROME_PATH` names a binary. **Skipping is not passing**: the gate stays green, and the
only thing that catches a visual regression is a person running this by hand.

```bash
npm i --no-save @sparticuz/chromium puppeteer-core   # leaves package.json and git status clean
# inflate() the two Brotli blobs to /tmp/chromium and /tmp/al2023, then chmod +x /tmp/chromium
python3 -m http.server 8000 --bind 0.0.0.0 --directory _site &
CHROME_PATH=/tmp/chromium LD_LIBRARY_PATH=/tmp/al2023/lib \
  node tools/sitegen/browser_check.mjs http://localhost:8000
```

The full recipe, the traps and what each check proves are in the header of
`browser_check.mjs`. `LD_LIBRARY_PATH` is the whole trick — without it Chromium dies on a missing
`libnspr4.so` — and `/tmp` is not persisted, so the install and inflate are redone each session.

## Where things live

Read `STATUS.md` first, then only the rows your task needs.

| You need | Read |
|---|---|
| Current state, open owner decisions, next step | `STATUS.md` |
| Settled facts (law, fees, free-tier rules), voice rules, hard constraints | `site-plan/00-CONTEXT.md` §4–§6 |
| Requirements R1–R28, routes, out-of-scope list, owner decisions D1–D5 | `site-plan/01-PRODUCT-REQUIREMENTS.md` |
| Phase order and exit criteria | `site-plan/02-BUILD-ROADMAP.md` |
| How the site applies the design system; rules and recipes | `site-plan/04-DESIGN-SYSTEM-NOTES.md`, `design-system/docs/DESIGN.md` |
| The curriculum (the only source of copy) | `content/docs/src/doc1.md` … `doc5.md`; home copy in `content/HR_Library_Overview.md` |
| Paths the specs use vs this tree, and history | `README.md` › Path translation · `git log` |

## Code map

```
content/docs/src/   doc1–5.md: the source of truth for every word; also builds the .docx
content/resource-verdicts.json   the owner's cost label per doc3 card, with the card wording it rests on
content/course-cards.json        which doc3 card shows each tracker course (shared tick keys)
scripts/            docx_render.py (shared parser + .docx renderer), validate_build.py, style_audit.py
tools/sitegen/      sitegen.py (extract + render every route), audit.py (output gate), check.py
                    (the gate), browser_check.mjs (needs a real browser), linkcheck.py,
                    docx_regression.py, tests/ (unittest + node:test)
site/static/        site.css (token-only layer), progress.js, copy.js, glossary.js, library.js
                    (all JS squeezed at build)
design-system/      the Fieldnotes design system; fieldnotes.css is copied into _site/
downloads/          the five .docx + the frozen research archive, served as files
checks/links.json   the last link sweep (absent until linkcheck.py has run)
_site/              generated output, never edited, never committed
```

The learning path is `learning_path()` in sitegen.py. Activities are the doc2 block rows (Time ·
Do this · Output); Weeks 20–21 use their Support A artefact rows; Weeks 22–24 live in doc5.

## Invariants (owner approval needed to change)

Content:
- No content fork: every word traces to `content/`, never paste copy into templates, never keep a
  second copy of the tracker, a resource list or a template. Never edit a sentence in `content/` to
  suit a layout — report the collision and let the owner decide.
- No new factual content. Keep every hedge (fees, wages, pension rates, legal entitlements) exactly
  as hedged. A rewrite that makes a hedged figure sound certain is a defect.
- The five .docx must stay unchanged (the regression in the gate). `HR_Roadmap_Library.*` is
  frozen: download-only, never re-rendered. Content pages carry the checked-on stamp from a build
  value; legal pages also say "Not legal advice; current to the date checked." (R7).

Product:
- No accounts, sign-in, backend, database, cookies, analytics, tracking or third-party requests
  (fonts and scripts are served by the site itself).
- Progress lives in `localStorage` (`hrsite:v1`) on the learner's device and never leaves it. The
  site never implies it syncs across devices, no content is gated behind progress, and a first
  visit shows none at all (no empty bar, no "0%").
- Out of scope (PRD §4): community features, email capture, paid plans, affiliate links, quizzes,
  video, dark mode, AI chat.

Technical:
- The design system owns every visual value: `var(--fn-*)` only, no colour literal (audit fails),
  no blur, no gradients. A value with no token gets a `/* TODO no token: … */` and a question to the owner.
- No Tailwind build and no Node toolchain for the site; Node is used only for tests.
- Budgets (R24): ≤120 KB HTML per page, ≤45 KB CSS gzipped, ≤14 KB JS for the whole site (R24 said
  10 KB; 12 KB for the library filter, then 14 KB for the offline bar — both owner-approved). The
  gate in `tools/sitegen/audit.py` enforces these, so trust its number over any document.
- **Raising a budget is mine to decide; reporting it is not optional.** Any increase gets told to
  the owner, with what forced it and how much room is left. Never raise one silently, and never
  weaken a check to stay inside a budget instead of raising it.
- Row keys (`data-k`, e.g. `w13-r2`) are a persistence contract: heading slug plus row index.
  Renaming a week heading or reordering rows orphans learners' ticks.
- Progress counts are derived from the build manifest, never stored. Controls ship `hidden` and the
  script reveals them, so the site reads fully with JavaScript off. Every `<table>` has a
  `<caption>` and every `<th>` a `scope`; toggles are real `<button>`s with `aria-pressed`.
- Cost stickers come only from `content/resource-verdicts.json`, never from guessing at wording. A card
  without an entry shows no sticker; a basis the card no longer says fails the build.
- Link status shown on the site comes only from a recorded sweep. Only 404/410 count as "failed";
  403, 429, 5xx and network errors are "inconclusive". Never hand-edit `design-system/artifacts/`
  or anything listed in its `SHA256SUMS.txt`.

## When sources disagree

- What the site says: the Markdown in `content/`. Settled facts and voice: `00-CONTEXT.md`.
  Behaviour and scope: the PRD. Visuals: `DESIGN.md` over the style guide (R21). Current state:
  `STATUS.md`, checked against the code.
- If the documents contradict each other, don't resolve it silently: report both passages. If
  resolving a conflict would change content, behaviour, persistence or scope, stop, show the
  options and ask. If a doc is simply wrong about the code, fix the doc in the same task.

## Working rules

1. Do the task asked. No unrequested features, dependencies, abstractions or redesigns.
2. Before editing, run `git status` and keep changes you didn't make. Read the relevant PRD
   requirement and the code that implements it.
3. Unclear and costly to get wrong (content, scope, persistence): ask. Unclear but cheap to redo:
   take the most reasonable reading and say which one you took.
4. Extend `docx_render.parse()`; don't fork it. Anything added must leave the .docx output unchanged.
5. Run narrow tests while working and the gate before finishing. Never report a check you didn't
   run, and never weaken a test to make it pass.
6. For UI work, check it in a browser at 360 px wide, by keyboard and with JavaScript off, and
   say what you could not observe. Run the browser checks if a browser is available.
7. Re-read the full diff before finishing.
8. Cut taglines, helper text and secondary labels. If a screen needs them to make sense, fix the
   layout. Elevate UX, DX and AX together, without breaking anything.

## Approval gates: ask first

- Commit: allowed on a feature branch once the gate passes. Merging into `main` needs the owner.
- Push, merge, history rewrite, deploy, release.
- Any edit under `content/` or `downloads/`; deleting data; discarding changes you didn't make.
- Adding a dependency, a third-party service or a build tool.
- Changing the storage key or shape, the row-key scheme, a route, or an owner decision (D1–D5).

Reading, local edits, builds, tests and the link sweep's `--dry-run` need no approval.

## Knowledge upkeep

- Each fact lives in one file. Elsewhere, link to it. Never write a number a command can produce
  (routes, links, keys, bytes) — write the command. Never record git state in a document.
- At the end of a task, update only what became false: `STATUS.md` always (overwrite it, under
  160 lines); the PRD or roadmap only with owner approval; this file only when a command, invariant,
  gate or gotcha changed. Commit messages carry the history.

## Skills

`skills/` holds reference packs only, not workflow procedures: accessibility-compliance,
copywriting, design-system-patterns, design-taste-frontend, responsive-design, ui-ux-pro-max. Read
a pack's SKILL.md first; `00-CONTEXT.md` §5 outranks the copywriting pack.

## Gotchas

- On the owner's PC, `python3`/`python` are Microsoft Store stubs. The real interpreter is
  `/c/Users/micha/AppData/Local/Python/bin/python3`. Set `PYTHONIOENCODING=utf-8` before printing
  content: `₦` breaks a cp1252 console. `/tmp` is not a path for Windows Python.
- Heading ids can start with a digit (`1-1-the-15-word-map-of-hr`). That is valid HTML5, and the
  same slug feeds the row keys, so `.htmlvalidate.json` uses relaxed ids. Don't "fix" the slugs.
- Voice hits from the documents themselves are listed in `KNOWN_SOURCE_HITS` in `check.py`. Only
  the owner clears them, by deciding on the sentence; never by editing `content/` yourself.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum` and dies on
  Windows. Copy the tree and patch the copy; never patch the checksummed original.
- The display face is a system mono stack with no guaranteed `₦` glyph; `md()` wraps the sign in
  `.naira` so it renders in the reading face. `docx_render.URL_RE` skips a URL written as
  "(https://…)", so it renders as plain text — `link_sources()` still checks it.
- The site's JS is squeezed at build (`squeeze_js`): comments and spaces go, strings are kept. It
  has no regex-literal or template-string support, so use neither, keep `//` comments on their own
  line (an inline one fails the build), and end every statement with a semicolon.
- Output goes to `_site/` only, never `dist/` or `build/`.

## Finish with

Outcome · files changed · checks run and their results · what isn't verified and why · next step,
plus anything that needs approval.
