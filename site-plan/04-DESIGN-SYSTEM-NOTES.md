# Phase 0.1 — design-system note (roadmap exit artifact)

Status: **complete, decisions locked 2026-10-21.** D1 and D5 confirmed by the owner; R20 resolved as
a hand-written token-only site layer with the deviation recorded below; the React style guide
arrived and is analysed in §"The style guide". Table and print treatments were ratified as
specified here.
Environment: Windows, Git Bash, Python 3.14.3, Node 24.13.0. No network used.
Bundle: `wakeout-ds-tokens-1.0.0.zip` unpacked to `design-system/` (sibling of `content/`,
`scripts/`, `site-plan/`). All 23 `SHA256SUMS.txt` entries verified **OK** before and after.

## What was executed

`design-system/tools/build-tokens.mjs` refuses to run on Windows: it shells out to
`/bin/bash -c "shasum -a 256 …"` to hash the source for `manifest.json`. That is a POSIX-only
assumption in one line, not a network problem. To keep the checksummed bundle pristine, the
generators were run from a scratch copy (`/tmp/dsrun`) with **only that one line** swapped for
Node's own `crypto.createHash`. The shipped `design-system/` tree was restored and re-verified
afterwards (23/23 OK).

```
✓ 183 tokens → artifacts/ (20 groups)
✓ contrast: 17 approved pairs, 11 pass AA(4.5:1)
✓ artifacts/standalone.html (111.5 kB, self-contained)
```

Regenerated output is **byte-identical** to the shipped artifacts for all six generated files
(`wakeout.css`, `wakeout.theme.css`, `tokens.dtcg.json`, `tokens.js`, `tailwind.preset.cjs`,
`manifest.json`) and for `standalone.html`. Generation is deterministic. Reproducible.

## Token groups in `tokens/tokens.json` (183 tokens, 20 groups, from `artifacts/manifest.json`)

| Group | n | Group | n |
|---|---|---|---|
| `color.primitive` | 35 | `dimension.container` | 10 |
| `color.semantic` | 31 | `dimension.aspect` | 2 |
| `typography.fontFamily` | 4 | `dimension.blur` | 2 |
| `typography.fontWeight` | 6 | `elevation` | 6 |
| `typography.fontSize` | 16 | `motion.duration` | 7 |
| `typography.lineHeight` | 7 | `motion.easing` | 4 |
| `typography.letterSpacing` | 11 | `motion.transition` | 1 |
| `dimension.base` | 1 | `motion` | 1 |
| `dimension.space` | 18 | `motion.tilt` | 5 |
| `dimension.radius` | 12 | | |
| `dimension.borderWidth` | 4 | **total** | **183** |

Plus a non-token `rule` group (`principles` 9, `doNot` 8, `accessibility` 3) that carries the
prohibitions as prose, and `$meta` (version 1.0.0, captured 2026-10-20).

## Sizes

| File | raw | minified | gzip-9 raw | gzip-9 min |
|---|---|---|---|---|
| `wakeout.css` | 11,460 B | **6,694 B** (−41.6%) | 2,878 B | **2,080 B** |
| `wakeout.theme.css` (unused, see D1) | 13,851 B | 12,654 B (−8.6%) | 2,908 B | 2,626 B |

Minification method: comments removed, whitespace collapsed and tightened around `{};:,>`, trailing
semicolons dropped. A conservative mechanical strip, not a name-mangling minifier — no CSS
minifier is installed and installing one would add a dependency. All 197 custom properties survive
it. The operative number for R24 is the gzip column.

`--wk-*` custom properties in `wakeout.css`: **197 distinct, 199 declarations**
(`--wk-muted` and `--wk-muted-foreground` are each declared twice), all in `:root`; 233 textual
occurrences. Matches `00-CONTEXT.md` §3.

README self-checks pass verbatim: `--wk-radius-2xl: 2.25rem`,
`--wk-shadow-sticker: 6px 6px 0 0 var(--wk-ink)`.

## Can `tools/` emit a subset of only the tokens used?

**No.** There is no subset mode. `grep -n "process.argv\|subset\|--only\|usedOnly\|purge" tools/*.mjs`
returns nothing but two hits on *font* subsetting in `standalone.mjs`. `build-tokens.mjs` flattens
all 183 tokens and compiles every artifact unconditionally; `artifacts/` is a pure function of
`tokens/tokens.json`. Building a token subset would mean editing the extraction pipeline — the one
thing this bundle's `AGENTS.md` §1 forbids ("if you improve a value you are shipping an opinion").

## The style guide (received 2026-10-21)

`styleguide.html`, 426,355 B, copied to `design-system/docs/styleguide.html` (outside the
`SHA256SUMS.txt` set, so 23/23 still verifies). It is **not** 2,546 lines of source: it is a built
Vite/React 18 single-file SPA — one 133 kB `<style>` head, a `<div id="root">`, one inline bundle
with the woff2 subsets base64'd in, plus a Cloudflare challenge stub at the tail. It renders
38,906 characters of text across twelve sections (Foundations 01–07, System 01–05) and needs no
network. Read by serving the file on loopback and reading the rendered DOM, then measuring computed
styles — the copy in the bundle is JSX string literals and is not trustworthy without rendering.

What it adds that `DESIGN.md` does not carry: the reference's own scale (77.3 kB stylesheet,
171 pages, 27,931 class uses, 15 pages sampled); all 35 primitives with per-site usage counts; the
shadcn-style semantic alias table (`--primary` → `--wk-primary` etc.); a 16-column contrast matrix;
a 183-row token browser with `--wk-*` and evidence per row; a Theme Lab; and the extraction
pipeline. Its nine rules and its Do/don't table are the same ten prohibitions as `DESIGN.md` §9,
worded differently, with no contradiction. Verified consistent: button recipe and 8 variants, the
sm/md/lg sizes (14/16/20px = `text-body-sm`/`text-body`/`text-subhead`), card and sticker recipes,
the focus ring (4px `rgba(138,56,245,.4)`, `outline:none`), contrast values, 10px as the uppercase
label floor, and `chart-1…5` for data colour.

Two divergences, both trivial to lose to `DESIGN.md`:

1. Its contrast blurb says ink-on-paper is **12.4:1**; its own matrix, `DESIGN.md` §10 and
   `ref/contrast.json` all say **12.67:1**. Typo in the prose. 12.67 governs.
2. Its table header cells are 10px (`--wk-text-eyebrow`) and its table body is 11px
   (`--wk-text-label`) — see the R26 override below.

## Table treatment: absent from `DESIGN.md`, demonstrated in the style guide

The bundle's specs never mention tables: zero `table`/`caption`/`thead`/`th`/`td` in `DESIGN.md`;
the `component` token group has ten components (`button`, `pill`, `eyebrow`, `chip`, `card`,
`mediaFrame`, `toggle`, `windowChrome`, `section`, `divider`) and no table; `wakeout.css` carries
only Tailwind's preflight `table{border-collapse:collapse}`; `ref/main.css` has no table rule. The
reference site never shipped a styled table.

The style guide answers it **by construction**: it contains three real `<table>` elements (the
31-row semantic-alias table, the 13×16 contrast matrix, the 8-row Do/don't table) built by the
design-system's own author. Measured recipe, all of it tokens:

- **Wrapper** `overflow-x-auto`; the Do/don't table sits inside the full Card recipe
  (`rounded-3xl border-3 border-ink bg-surface shadow-sticker overflow-hidden`). The alias table
  adds `min-w-[52rem]` and scrolls horizontally rather than collapsing on small screens.
- **Table** `w-full text-label … ` → transparent, radius 0, no shadow, no borders of its own; type
  is Space Grotesk (body face) in ink.
- **`thead tr`** `border-b-3 border-ink` (3px ink rule) + `bg-muted/60` on dense data tables;
  header cells `text-eyebrow uppercase tracking-widest text-ink/70`, padding 12px 16px.
- **`tbody tr`** `border-b border-ink/10 last:border-0` — 1px ink/10 row rules, none on the last
  row; no zebra, no hover, no tilt, no row shadow (Card `flat`: rows must not carry stickers).
- **Cells** `px-4 py-2.5` (16px / 10px); the dense matrix tightens to `p-2` and `ink/5` rules.

**R26 override, ratified:** the guide's body size (11px = 8.25pt) and header size (10px = 7.5pt)
are below R26's 9pt floor for table text. Table type therefore moves to `--wk-text-caption`
(0.75rem = 12px = exactly 9pt) for both header and body. This is not an invented value: `DESIGN.md`
§8 defines **Eyebrow** as `text-caption font-bold uppercase tracking-widest`, so a 12px uppercase
header *is* the documented Eyebrow recipe, and the guide's 10px variant is the deviation. Inherit
ink 12.67:1 on surface, secondary cells `--wk-muted-foreground` (6.12:1). Never `ink/60` (3.87:1)
or `lime-deep` (4.27:1) in a cell. `font-variant-numeric: tabular-nums` on minutes/numbers (no
token — this is a CSS default, not a visual value).
**R26 also requires** a `<caption>` and `scope` on header cells; the guide's tables have neither (it
uses a heading above). We add a real `<caption>` styled as the Eyebrow, and `scope="col"`.

## Print rules: documented nowhere, including the style guide

Zero `@media print` rules in either stylesheet and none in the guide; the only media query is
`prefers-reduced-motion`. `DESIGN.md`'s only "print" is the elevation metaphor ("elevation = a
printed sticker"). R22 is ratified as a hand-written token-only print layer in `site.css`:
`print-color-adjust: exact` on the ink blocks R22 calls out, `--wk-paper` page, `--wk-ink` text and
borders, sticker offsets kept (they are ink on paper and cost nothing), motion dropped, nav/progress/
copy controls hidden, `thead` repeated, law card fitted to one A4 at `--wk-text-caption` body.
Note 10pt (13.33px) has **no token** — the ramp jumps 12px → 14px (10.5pt) — so the law card sits at
9pt or 10.5pt, never exactly 10.

## Owner decisions, locked 2026-10-21

**D1 — ship the whole `wakeout.css`, minified: 6,694 B raw / 2,080 B gzip.** R23 gives CSS 45 KB
gzipped; this spends 4.6% and leaves ~43 KB for the site layer. There is no subset mode to use and
the subset would not pay for itself. `wakeout.theme.css` is **not** shipped: it is the Tailwind v4
bridge (198 `@theme inline` mappings, 15 `@utility`, 6 `@keyframes`, 20 `.wk-*` classes, 16
Tailwind-only directives) and §6.3 rules out a Tailwind build.

**D5 — rotated stickers are an approved pattern, at −2°…−6°.** Rotation is a token group
(`--wk-tilt-rest: 0`, `subtle: -1deg`, `medium: -2deg`, `sticker: -6deg`, `dramatic: ±12deg`).
`DESIGN.md` §7 and the guide's rule 07: −1° interactive feedback, −2° decorative sticker, −6°
annotation, ±12° rare callout. Site rule: **stickers and annotations only, never on prose, table
rows, headings, labels or anything read for more than a second.**

**R20 — hand-written token-only site layer, deviation recorded.** The owner's ruling supersedes
R20's "and its documented `.wk-*` classes". `wakeout.css` contains **zero** `.wk-*` component
classes; all 20 live in `wakeout.theme.css` (needs Tailwind) and, already written against
`var(--wk-*)`, inside the generated `artifacts/standalone.html`. §6.3 forbids the Tailwind build, so
the site ships `wakeout.css` + a handwritten `site.css` of layout and component rules built from
`var(--wk-*)` only, transcribing the component *recipes* (button, card, sticker, eyebrow, chip,
table) from `DESIGN.md` §8 and the guide rather than importing a second copy of component CSS. The
deviation to carry into Phase 1.6 and the launch notes: **the site has no `.wk-*` class surface; it
implements R20 through the custom properties, plus component classes of its own naming.** This is
the explicit R21 tie-break case and is not a silent substitution.

## Conflicts found, and which document wins

1. **`README.md`'s "No Tailwind?" recipe does not work as written** — see R20 above. Resolved by
   owner ruling; the README's snippet (`wakeout.css` + `.wk-button`) stays wrong for this site.
2. **`00-CONTEXT.md` §3 counts are three of four right.** "Seven dependency-free generator
   scripts" — **four** ship (`build-tokens`, `contrast`, `extract`, `standalone`). "21 `.wk-*`
   classes" — there are **20**. 197 `--wk-*` properties — **correct**. 183 tokens in 20 groups —
   **correct**. "A 2,546-line React style guide" — the guide is a built SPA, not source lines
   (see above); the substance it promised is present.
3. **Style-guide prose vs its own matrix:** 12.4:1 vs 12.67:1. `DESIGN.md` and the tokens win.
4. **Style-guide table type vs R26:** 11px body and 10px header are below the 9pt floor. R26 and
   `DESIGN.md`'s Eyebrow recipe win (12px). Geometry from the guide wins.
5. **Contrast debt inherited by the design system** (`ref/contrast.json`, guide's matrix): 11 of 17
   approved pairs pass AA. `ember` on paper 2.67 fails; `red` on paper 3.69, `red` on white 3.91,
   `ink/60` on paper 3.87, `lime-deep` on paper 4.27. R26 wants 4.5:1 for 9pt table text, so table
   and body text use `--wk-ink` (12.67:1) and `--wk-muted-foreground` (6.12:1) only. Cost-verdict
   stickers carry text, never colour alone — and their own text must clear 4.5:1 on its fill.
6. **Rights.** `design-system/AGENTS.md` §8: the bundle is a reverse extraction of a live brand —
   "if this ships publicly, rename the system and replace the copy." Values and geometry are facts;
   the name, copy and domain are not ours. The four woff2 files are OFL 1.1 subsets and may ship
   **with the licence text**; pull from `@fontsource` for production. No "Wakeout" name on the site.

## Open risks carried into Phase 1

- **The Naira sign.** The content uses `₦` throughout; whether `public/fonts/*latin*.woff2` carries
  U+20A6 is **unverified** — no `brotli`/`fontTools` in this Python, and installing one is a
  dependency decision. If it is missing, every money figure falls back to a system face mid-sentence.
  Cheap check at 1.4: render `₦` in the specimen and compare glyph metrics against a sentinel.
- **Font cost.** Fredoka + Space Grotesk latin subsets = 48,628 B; with `-ext`, 59,964 B. Both
  families are mandatory (`DESIGN.md` §3 splits statements/instructions). R24 allows them because the
  system ships them; `font-display: swap` and a preload of the one face above the fold, latin only,
  is the budget-conscious path for a 3G visitor.
- `--wk-radius-md` (0.75rem) and `--wk-duration-instant` are **interpolated, not measured** — do not
  build on them (`DESIGN.md` §5, `AGENTS.md` §4). `--wk-radius-4xl` (2.5rem) sits oddly below 3xl;
  use 3xl for cards.
