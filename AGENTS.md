# AGENTS.md — [PROJECT_NAME]

<!--
TEMPLATE NOTES (delete this block once filled)
- Agents load this file at the start of every session, so every line costs tokens every time.
  Target: under 200 lines (~2.5k tokens).
- Put only facts here that change less than once a month. Anything with a number, a date,
  or "currently" goes in STATUS.md.
- Fill every [ ]. If a section would say nothing, delete it. Don't fill it with "UNKNOWN".
- Claude Code reads CLAUDE.md. Add a one-line CLAUDE.md containing `@AGENTS.md` so every agent
  reads this same file.
-->

## What this is

A free, 24-week learn-HR-and-get-a-job course for someone in Nigeria starting from zero,
turned from five finished documents into a static website. The documents are the product;
the site is a rendering of them. The one outcome that matters: a reader follows the site
for four weeks without opening a .docx.

Project class: product.

## Commands

- Install: `python3 -m pip install -r requirements.txt` (dev only — `python-docx`, needed by
  exactly one gate. Nothing is needed to build or view the site.)
- Dev server: none needed while the site is static. `python3 -m http.server -d _site 8000`
  to look at a build.
- **Gate:** `make check`. It must exit 0 before any work is called done. It runs:
  `sitegen.py` (build), `audit.py` (14 checks: links, budgets, table structure, stamp,
  tokens, `data-k` uniqueness, copy integrity, `content/` unmodified), then
  `docx_regression.py` (the five .docx are unchanged).
- Without `make`: `python3 tools/sitegen/sitegen.py && python3 tools/sitegen/audit.py && python3 tools/sitegen/docx_regression.py`
- Narrow test: `python3 scripts/validate_build.py content/docs/src/doc*.md`
- Environment: **Python 3.11 or newer** (the build must not use PEP 701 f-strings — see
  Gotchas). Linux and Windows are both in play; the owner's machine is Windows with a
  cp1252 console, so set `PYTHONIOENCODING=utf-8` before printing content. Windows has no
  `make` by default; use the three commands above.

## Where things live

Read only the rows your task needs.

| You need | Read |
|---|---|
| Current state, next step, open risks | `STATUS.md` (read it first, every session) |
| Product behaviour, scope, non-goals | `site-plan/01-PRODUCT-REQUIREMENTS.md` (R1–R28) |
| Facts, voice rules, hard constraints | `site-plan/00-CONTEXT.md` |
| Planned order of work, exit criteria | `site-plan/02-BUILD-ROADMAP.md` (phases 0–5) |
| How the design system was read, owner decisions | `site-plan/04-DESIGN-SYSTEM-NOTES.md` |
| Visual values (colours, type, spacing, shadow) | `design-system/artifacts/wakeout.css` |
| History | `git log` |

## Code map

```
content/docs/src/doc1..5.md   the only source of copy. Never edit to suit a layout.
content/HR_Library_Overview.md  the home page copy.
scripts/docx_render.py        shared markdown parser. Extend parse(); do not fork it.
                              Also renders the .docx — changes here move the .docx gate.
tools/sitegen/sitegen.py      the site generator: extract + render, writes _site/.
tools/sitegen/audit.py        the gate for generated output.
tools/sitegen/docx_regression.py  the 1.7 gate: the five .docx must not change.
site/static/site.css          the site layer. Every value a var(--wk-*). No colour literals.
design-system/                the Lego box. Checksummed — see Gotchas.
downloads/                    frozen outputs, shipped as files. Never regenerate.
_site/                        generated. Throwaway. Never dist/ or build/.
```

## Invariants (owner approval needed to change)

Product:
- No accounts, no backend, no cookies, no third-party requests, no analytics of people.
  Progress lives in `localStorage` and never leaves the device (R27).
- No new content. Every word on the site traces to `content/` (R1). Nothing hedged in the
  source may be stated flat on the site.

Technical:
- One source of copy. `content/` is never edited by a build; `audit.py` fails the build if
  `git diff -- content/` is non-empty.
- The design system owns every visual value. `site.css` carries no colour literal
  (enforced in `audit.py`).
- `downloads/*.docx` and `HR_Roadmap_Library.*` are byte-frozen. `docx_regression.py` fails
  if a parser change moves them.
- `data-k` values are unique site-wide (R9): they are the future progress keys, so a
  duplicate would make one tick tick two rows.

## When sources disagree

- Product behaviour: PRD. Architecture and contracts: MCD or the decision record. A feature's details: its spec. What exists now: the code and tests. Current state: STATUS.md, but check it against the code.
- Code doesn't prove what was intended, and a doc doesn't prove something was built.
- If resolving the conflict would change behaviour, architecture, data, security or scope, stop, show the conflict and the options, and ask. If it's just a wrong doc, fix the doc in the same task.

## Working rules

1. Do the task you were asked to do. Don't add unrequested features, dependencies, abstractions or refactors.
2. Before editing, run `git status` and keep any changes that aren't yours. Read the relevant spec, code and tests.
3. If something is unclear and costly to get wrong, ask. If it's unclear but cheap to redo, take the most reasonable reading and say which one you took.
4. A non-trivial feature with no spec needs a spec first (skill: `[architect]`), and the owner has to ratify it.
5. Run narrow tests while you work and the gate before you finish. Never report a check you didn't run. Never weaken a test to make it pass.
6. Re-read your full diff before you finish.

## Approval gates: ask first

- Commit: [allowed once the gate passes | ask every time]
- Push, merge, history rewrite, deploy, release
- Deleting data, or discarding changes you didn't make
- Adding a dependency, or upgrading a major dependency or tool version
- Changing an approved architecture decision, a data or persistence contract, a security boundary, or product scope

Everything else (reading, local edits, running tests and builds) needs no approval.

## Knowledge upkeep (keep it cheap)

- Each fact lives in exactly one file. Everywhere else, link to it.
- Never write down a number that a command can produce (test counts, bundle sizes, file or line counts). Write the command instead.
- Never record git state (committed, pushed, clean tree) in a doc. Git already knows it.
- At the end of a task, update only what has become false:
  - `STATUS.md`: always. Overwrite it, don't append. Keep it under 80 lines.
  - The spec: set its status, tick acceptance criteria, note any deviations.
  - `ROADMAP.md`: tick the step.
  - PRD or MCD: only if behaviour or a contract changed, and only with owner approval.
  - `AGENTS.md`: only if a command, invariant, gate, code-map entry or gotcha changed.
- Let commit messages carry the history. Don't keep changelog paragraphs in docs.
- If you hit a trap the next agent would also hit, add one line under Gotchas.

## Gotchas

- **No PEP 701 f-strings.** An escaped quote inside an f-string *expression*
  (`f"{'x' if a else ''}"` written with backslashes) is a SyntaxError before Python 3.12.
  Build the attribute into a variable first. `sitegen.py` broke this way once.
- **The .docx path is shared.** `scripts/docx_render.py` feeds both the site and the five
  downloads. A change there moves `downloads/`, and `docx_regression.py` will fail. To make
  the site behave differently without touching the .docx, do it in `tools/sitegen/` (see
  `PAREN_URL_RE` for the pattern).
- **URLs appear three ways** in the corpus: `[text](url)`, bare `https://…`, and
  `(https://…)`. Any new pass over content has to handle all three or it will silently miss
  some — the sweep missed 35 of 47 this way.
- **Rendering one block on two pages duplicates its `data-k`.** Keys are minted once per
  parse. Pass `ns=` to `render_blocks` on the second rendering.
- **Never edit the checksummed design-system files.** To patch `design-system/tools/*.mjs`
  or an artifact, copy the tree, patch the copy, diff. `SHA256SUMS.txt` is the record.
- **The naira sign needs a face.** Fredoka's subset has no U+20A6; Space Grotesk's does.
  `md()` wraps every `₦` in `<span class="naira">` so it never falls back mid-word.
  `·`, `—`, `→` and `☐` are absent from the body face and do fall back — known, see STATUS.
- `python3`/`python` on the owner's PATH are Microsoft Store stubs that exit 49. Real
  interpreter: `/c/Users/micha/AppData/Local/Python/bin/python3`.
- `/tmp` is not a path for Windows Python — use a workspace dir or `tempfile`.
- Generated output goes to `_site/`, never `dist/` or `build/` — those names are dropped.

## Finish with

Outcome · files changed · checks run and their results · what isn't verified and why · next step, plus anything that needs approval.
