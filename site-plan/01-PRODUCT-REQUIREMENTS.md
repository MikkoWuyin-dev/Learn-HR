# Product Requirements — "HR Library" website

Version 1.0 · for the builder agent · companion to `00-CONTEXT.md`

## 1. Problem

Someone in Nigeria with no HR background, no money for courses, and possibly a phone as their only computer needs a path from zero to a first job. That path exists and is written (see `00-CONTEXT.md` §2), but it currently ships as five documents. Documents are good for studying and poor for the two things a learner actually does daily: answering "what am I supposed to do tonight?" and "did I already finish this?".

## 2. Goal

Make the same path easier to follow than the documents are, by adding only what a site can add: a place to be, per-week pages, remembered progress, copyable objects, and visible link-checking. Nothing new is taught that the documents don't already teach.

**Success looks like:** a stranger follows the site for four weeks without opening a .docx, and a returning visitor sees where they stopped. A secondary signal is being found by search for one of the specific questions this library answers well (free HR courses with a real certificate, Nigerian Labour Act notice periods, how to build a recruitment dashboard).

## 3. Users

| | Profile | What the site must do for them |
|---|---|---|
| **Primary — "Amaka"** | Lagos or Benin City, 23–32, graduate, finished NYSC, job hunting, Android phone, prepaid data, shares mobile hotspot | Load fast on 3G; one-handed reading; a week fits one screen without horizontal scroll; work when data runs out mid-week; no login to lose |
| **Secondary — "Tobi"** | Career-changer in a salaried job, studies evenings, laptop, prints things | Deep links to specific weeks and cards; printable law card and tracker; downloadable .docx for offline study |
| **Tertiary — "Ngozi"** | Runs an SME and needs to hire, doesn't call it HR | Finds the specific answer (what must an offer letter contain; how to run a redundancy) and trusts the source lines |

## 4. In scope / out of scope

**In:** static site generated from the existing markdown; 52 routes (see §6 — the route map
there sums to 52 with the 22 week pages that exist, not the 25 the plan assumes); progress in
`localStorage`; copy buttons; library filter; glossary search; print stylesheets; `/check/`
link-status page; downloads of the five .docx and the archive; SEO metadata and JSON-LD;
service worker.

**Out (do not build):** accounts, sign-in, passwords; a backend or database; comments, forums, "community"; email capture, newsletters, popups; paid plans, coupons, affiliate links; a course player or video hosting; quizzes; dark mode; i18n; analytics of people; a redesign of the .docx files; AI chat; any new factual content; changing the five documents' substance to fit the site.

## 5. Requirements

Numbered for traceability. `M1` must ship in phase 1, `M2` phase 2, `M3` phase 3.

### Content

- **R1 (M1)** Every word on the site traces to `docs/src/doc1-5.md` or `HR_Library_Overview.md`. The generator fails the build if it emits a paragraph with no source block.
- **R2 (M1)** 24 week pages plus Week 0, each showing: phase label, week number, the block table (minutes · activity · output), the pass mark where the source states one, and the source's `>` notes as callouts.
- **R3 (M1)** Doc 3 renders as filterable cards. Each card exposes link, cost verdict, hours, level, phase, and the four prose fields (what it is · why it matters · what to do with it · plus the doc's own caveats).
- **R4 (M1)** Doc 4 renders the statute table, the statute list, the 20 tasks, the 10 myths, and the law card at its own route with a print stylesheet that fits one A4 page at 9–10pt.
- **R5 (M1)** Doc 5's copyable blocks (CV bullet rewrites, the 90-word application note, follow-up messages, the 12-question intake template, the reference-check script) render as discrete blocks with a `Copy` button.
- **R6 (M1)** The home page is `HR_Library_Overview.md`, lightly adapted: "Document 2" → "the Plan" with a link; the file-name mention of `HR_Roadmap_Library` becomes a download link. Do not rewrite the voice.
- **R7 (M1)** Every content page renders the stamp: `Checked 20 October 2026` from `site.json.last_verified`. Legal pages also render `Not legal advice; current to the date checked.`
- **R8 (M2)** A glossary view of Doc 1's 26 terms, searchable as you type, no external search library.

### Progress

- **R9 (M2)** `localStorage` key `hrsite:v1`, versioned object: `{v:1, ts, weeks:{13:true}, courses:{...}, artefacts:{...}}`. Keys are build-stable ids (`w13-r2`), derived from a slug of the heading plus row index — not from array position alone — so editing copy never orphans a tick.
- **R10 (M2)** Ticks appear on week rows, tracker items, and course cards. A progress bar on the plan index shows completed weeks / 24; the artefact count shows separately, because artefacts are the real measure.
- **R11 (M2)** A resume line on the home page, the plan index and the footer: `You left off at Week 13 · Intake, job analysis, the brief`. Absent storage or a first visit renders nothing at all — no empty progress bar, no "0% complete".
- **R12 (M2)** All storage access wrapped so a throwing `localStorage` (private browsing) degrades to a fully working page with no persistence and no console errors. No progress-gating of any content.
- **R13 (M2)** A `Reset` control inside a confirm step, so a shared family phone can be cleared.

### Trust and the links

- **R14 (M1)** `/check/` lists all 47 URLs with status on the last run, previous status, and the date, generated from the sweep file. Any non-200 is surfaced, never hidden.
- **R15 (M1)** A `Downloads` section offering the five .docx and the archive pair, with byte sizes shown, so a reader can see what they're fetching before paying for data.
- **R16 (M3)** Build step re-runs the sweep; failures land in the PR body, not silently.

### Findability

- **R17 (M1)** One HTML file per route; real `<h1>` per page; `<title>` pattern `Week 13 · Intake and the hiring brief — HR Library`; meta description generated from the page's own first paragraph.
- **R18 (M3)** JSON-LD: `LearningResource` per course card with `isAccessibleForFree: true` and `offers.price: 0`; `LearningProgramme` for the plan; `sitemap.xml` with `lastmod` from the sweep date.
- **R19 (M2)** Filter the library by phase, hours and credential; state kept in the URL query so a filter is shareable (`/3/library/?phase=4`).

### Design-system conformance

- **R20 (M1)** Style only through the design system's `--wk-*` custom properties and its documented `.wk-*` classes. No new colour literals, no blur, no gradients, no shadows without hard offsets. A value with no token becomes a `TODO` comment plus a question to the owner.
- **R21 (M1)** The table treatment, sticker label and card border follow `DESIGN.md` and the style guide; where they conflict, `DESIGN.md` wins and the conflict is reported.
- **R22 (M1)** Print styles for the law card, the tracker and the week pages; backgrounds that must survive printing use the print-adjust property, since the aesthetic leans on solid ink blocks.
- **R23 (M1)** CSS ships as one stylesheet: the design system's `wakeout.css` (full or generated subset, per the owner's choice) plus a site layer totalling ≤45 KB gzipped.

### Performance, a11y, privacy

- **R24 (M1)** Per page ≤120 KB HTML, ≤45 KB CSS, ≤10 KB JS across the whole site, 0 web fonts unless the design system already ships one (then `font-display: swap` and subset). Budget checked in CI with a hard fail.
- **R25 (M1)** Lighthouse mobile ≥90 performance / ≥95 a11y / ≥95 best practices on a throttled mid-range Android profile; usable with JS disabled (reading and links only).
- **R26 (M1)** Every data table has a `<caption>` and header cells with `scope`; the 9pt table text meets 4.5:1 against its background; colour never carries meaning alone (a cost sticker carries text); focus visible on all interactive elements; `Copy` and tracker toggles are real `<button>`s with `aria-pressed` and an `aria-live` count announcement.
- **R27 (M1)** No cookies, no third-party requests, no fonts or scripts from a CDN — relevant because a visitor's network may be the only thing they control. Privacy line in the footer: `No accounts, no cookies, nothing leaves your device.`
- **R28 (M3)** Service worker precaching the shell, the 24 week pages, the glossary and the law card; versioned cache; a "new version available" nudge that never interrupts mid-read. Offline test on throttled 3G, 10 reloads, all four routes.

## 6. Information architecture

```
/                                  compass (R6)
/1/start-here/                     Doc 1, one page
/2/plan/                           index: phases, 25 week links, progress bar
/2/plan/week/0/ … /24/             one page per week
/3/library/                        filterable cards
/3/library/<card-slug>/            permalink per card (20 cards)
/4/nigeria/                        Doc 4
/4/nigeria/law-card/               printable one-pager
/5/getting-the-job/                Doc 5
/5/templates/                      the copyable set, standalone
/check/                            link statuses (R14)
/downloads/                        7 files (R15)
```

Numbered routes are deliberate: the order is the product. Slugs stay stable; if the plan is re-cut later, redirect, don't rename.

## 7. Owner decisions still open

Ask before building the affected part; none of these block phase 1.

| # | Decision | Default if you get no answer |
|---|---|---|
| D1 | Full `wakeout.css` vs generated subset | Subset only if `tools/` already produces one; otherwise ship whole and note the byte cost |
| D2 | Licence for the original prose | `CC BY-SA 4.0` with an attribution line, sources excluded |
| D3 | Whether the archive `HR_Roadmap_Library` is hosted as a page | Download only; no hosted page (keeps search intent on the five) |
| D4 | Domain and language | `learn-hr.ng`-agnostic; English only |
| D5 | Is a rotated "sticker" an approved pattern or improvisation? | Approved at ≤12° on status labels only; flat if `DESIGN.md` forbids rotation |

## 8. Definition of done

Phase 1 is done when: the generator emits every route above; `validate_build.py` passes on all output; the internal-link audit finds no dead href; the 47-URL sweep results are published at `/check/`; `style_audit.py` reports zero mechanical problems and zero banned-pattern hits on all page strings; the budgets in R24 pass in CI; a keyboard-only pass completes "read Week 13 → copy the intake template → print the law card"; and `git diff` shows zero changes under `docs/src/` (proof the content fork was avoided).

The site is launched when the owner confirms on a real phone with data roaming, not on their laptop.
