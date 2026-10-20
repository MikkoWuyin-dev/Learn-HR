# Build Roadmap — "HR Library" website

Sequenced build plan. Requirements are cited as `R#` from `01-PRODUCT-REQUIREMENTS.md`; facts and constraints live in `00-CONTEXT.md`. Estimates are focused half-days for one agent working with these files.

## Phase 0 — Inputs and the ground truth check · 1 half-day

| Step | Do | Exit |
|---|---|---|
| 0.1 | Receive the design-system ZIP. Run its `tools/` generators to regenerate `artifacts/wakeout.css` and `wakeout.theme.css`. Read `DESIGN.md` and note the token group names, the table treatment, whether rotation is allowed, and the print guidance. | A written note: token groups, count of `--wk-*` vars actually used by the site, D1 and D5 answered |
| 0.2 | `python3 skills/resource-learning-library/scripts/validate_build.py docs/… HR_Doc*.docx HR_Doc*.html` on the current artefacts, and re-run the 47-URL sweep to refresh `checks.json` | Baseline numbers in hand; any URL that has moved since 2026-10-20 reported to the owner **before** any page is built on it |
| 0.3 | Confirm the repo shape: `content/` (copies or symlinks of `docs/src/doc*.md` + the overview), `tools/sitegen/`, `templates/`, `site/static/`, `checks/` | `make check` runs green on content alone |

**Rule for this phase:** no styling decisions until 0.1 is done. If the ZIP is late, start Phase 1 with unstyled semantic HTML — the markup is the deliverable, not the look.

## Phase 1 — Generator and static pages · 3–4 days · `M1`

**1.1 Extend the parser, don't fork it.** In `skills/resource-learning-library/scripts/docx_render.py` (or a copied `tools/sitegen/render.py` if you'd rather not touch the docx path):
- `slug(text)` → stable ids on every heading; `#### Card Title 【KEY】` → `id="card-key"` using the bracket tag when present, else the slug.
- Emit `data-k="w13-r2"` on table rows, keyed on the enclosing week heading slug plus row index.
- Recognise `{{var}}` for `last_verified` and `source_file`.
- Keep all existing behaviour for .docx rendering — the .docx build must stay byte-comparable. Rebuild and diff the five .docx afterwards (task 1.7).

**1.2 Extract content into data, at build time.** `tools/sitegen/extract.py` writes:
- `site.json` — route graph, per-page source block ids, `last_verified`.
- `resources.json` — 20 cards: title, url, cost verdict (`free-to-finish` · `free-to-study-paid-cert` · `limited-access` · `check-before-committing`), hours, level, phase, the four prose fields, caveats. Parsed from the card bullet lines; a card missing a field is a **build error**, not a blank cell.
- `tracker.json` — the 19 courses, 16 artefacts, 5 job-hunt assets from Doc 2's Support A, with their target weeks and `data-k` ids.
- `glossary.json` — Doc 1's 26 terms.
- `laws.json` — Doc 4's provision table (section, area, what it says) and the 10 myths.

**1.3 Pages.** `tools/sitegen/build.py` renders through five Jinja-free templates (`render_page`, `render_week`, `render_doc`, `render_card`, `render_print`) to `_site/`. Templates produce semantic HTML plus the design system's classes only (R20, R21): no inline styles, no hex, `class="wk-*"` where a documented `.wk-*` class exists, otherwise a site-layer class that consumes `--wk-*` vars.

Route map and rough content sizes, so the budget work is honest up front:

| Route | From | Notes |
|---|---|---|
| `/` | `HR_Library_Overview.md` | R6 wording changes only; the "two notes on the work behind it" paragraph is dropped — it was a message to the owner, not site copy |
| `/1/start-here/` | doc1 | glossary table + 4 sections |
| `/2/plan/` | doc2 head + Support A | index, 25 links, progress bar |
| `/2/plan/week/N/` | doc2 tables ×25 | 182 rows total, 3–8 per page |
| `/3/library/` + 20 card pages | doc3 | filters land in P2; cards need permalinks now |
| `/4/nigeria/`, `/4/nigeria/law-card/` | doc4 | law card in a print-sized layout (R22) |
| `/5/getting-the-job/`, `/5/templates/` | doc5 | templates page = the copyable set, no prose between blocks |
| `/check/`, `/downloads/` | `checks.json`, the 7 files | R14, R15 |

**1.4 CSS.** `site/static/site.css`: import or inline `wakeout.css`, then ~4–8 KB of site layer (`.week-table`, `.card`, `.sticker`, `.callout`, `.stamp`, print rules). Every value a `var(--wk-*)`. Add `/* TODO no token: … */` where one is missing and list them for the owner.

**1.5 Copy safety pass.** Run `style_audit.py` over the generated page strings (extract text from the HTML, not the markdown — this catches template-added filler). Zero mechanical problems, zero banned patterns (R1, R6).

**1.6 Budgets and gates.** `tools/sitegen/audit.py`: internal href resolution against `site.json`; page weight (R24); `html-validate` on every file; table structure check for `caption` + `scope` (R26); assertion that `git diff --stat content/` is empty.

**1.7 Regression on the documents.** Rebuild the five .docx with `docs/build_docs.py` and compare: same paragraph counts (51/100/142/87/118), same word counts (1,268 / 4,171 / 3,101 / 2,874 / 3,128), same hyperlink rels (0/0/43/8/0). This is the check that the parser change didn't damage the source of truth.

**Exit:** 32 routes built by one command, every `M1` requirement demonstrably met, `make check` green, .docx unchanged.

## Phase 2 — Progress, copy, filters · 2 days · `M2`

| Step | Do | Exit |
|---|---|---|
| 2.1 | `progress.js` (~2 KB, no framework): read/merge/write `hrsite:v1`; every access in a try (R12); `aria-pressed` on toggles; `aria-live="polite"` for the count (R10) | Private-mode Safari test: no errors, page identical minus persistence |
| 2.2 | Wire ticks into week rows, tracker items, course cards via `data-k` | Tick, reload, edit a sentence in that row's markdown, rebuild, tick survives (R9) |
| 2.3 | Resume line (R11) and the two progress meters; render nothing on a first visit | No empty progress bar at 0% |
| 2.4 | `copy.js`: one delegated `Copy` button per R5 block, `navigator.clipboard` with a `document.execCommand` fallback and a text-selection fallback after that; label swaps to `Copied` for 1.5 s | Works on `http://` preview, on iOS 12, on keyboard only |
| 2.5 | Library filter + glossary search, state in the URL (R19, R8) | A filtered URL, shared in a fresh browser, restores the same list |
| 2.6 | Reset control behind a confirm (R13) | Two clicks minimum to clear |

## Phase 3 — Findability, offline, polish · 2 days · `M3`

Sitemap with `lastmod`, robots, OG/Twitter meta, per-page canonical (R17, R18) → JSON-LD generation from `resources.json` → service worker + precache manifest with the offline nudge (R28) → OG cards generated from the site's own tokens (one per document, no photography, no AI imagery) → `/check/` wired into CI so the sweep runs on a schedule and opens an issue on a change → optional `/5/templates/` as a single printable sheet, since interview prep is read off-screen once printed.

## Phase 4 — Pre-launch checks · 1 day

Lighthouse mobile on the four heaviest routes, throttled (R25) · 3G cold load of `/2/plan/week/13/` and `/4/nigeria/law-card/` measured from a real device if available · keyboard-only run of the R26 flow · print to PDF from Chrome and from an Android phone and measure the law card against one A4 page · colour audit of 9pt table text on the cream background · JS-disabled crawl · `curl -I` on all 32 routes after deploy to catch a host rewriting trailing slashes · a plain-language README in the repo telling the owner how to change a course's cost line and rebuild.

## Phase 5 — Launch and the maintenance contract · 0.5 day

Deploy static output; verify canonical, sitemap, `/check/` date; post it once where the owner asks. Then the only recurring job, stated as a rule: **every quarter, re-run the sweep; if a resource's terms moved, change the markdown, rebuild, and let the stamp update itself.** Nobody edits HTML by hand, so there is nothing to forget.

## Dependency order

```
0.1 (ZIP) ──► 1.4 CSS ──► 1.6 gates
0.2 (sweep) ─► 1.3 pages ─► Phase 2 ─► Phase 3 ─► 4 ─► 5
1.1 (parser) ┘   ▲
1.2 (extract) ───┘   ← 1.2 must land before any filter or tracker work; R9 and R19 both consume it
```

## Risks, with the mitigation already designed in

| Risk | Mitigation |
|---|---|
| Content fork — site copy drifts from the .docx | R1's build-time provenance check; `git diff` on `content/` is a gate (1.6) |
| Row-key churn wipes people's progress | Keys derive from heading slug + row index, not array order alone (R9); test 2.2 makes it a build failure if a rename orphans ticks |
| `wakeout.css` blows the byte budget | D1 decided in 0.1; subset path exists; budget is CI-enforced at 45 KB gz (R24) |
| Stale free-tier claims damage trust worse than no site | `/check/` publishes every status with its date; the quarterly sweep is the maintenance contract (Phase 5) |
| Hedge language flattens into false certainty on law and money | R7's stamp plus the "not legal advice" line; §4 of the context doc lists the figures that must stay hedged; a reviewer greps the site copy for bare `₦` amounts without a date |
| 9pt table text in a brutalist palette fails contrast | R26's explicit contrast requirement on table text; checked in Phase 4 with the real tokens |
| The archive tempts someone to "add the missing platforms" | Context §6.4 freezes it; out-of-scope list in the PRD; any addition is a content decision by the owner, not a build task |
| Owner's style guide conflicts with itself (`DESIGN.md` vs the React guide) | R21's precedence rule, and the conflict is reported rather than silently resolved |

## Definition of done for the whole engagement

Every route exists and is generated; `M1`–`M3` met or explicitly deferred by the owner; budgets green; a returning visitor's progress survives a rebuild; the site can be taken offline and read; the five .docx are unchanged and still downloadable; the owner can rebuild from a two-line command and knows what to do when a link breaks.
