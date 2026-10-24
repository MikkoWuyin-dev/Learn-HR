# Fieldnotes — Style Guide

**Deconstructed from:** `Field-Notes_Nature-Photography`, 2026-10-24.
**Companion:** [DESIGN.md](DESIGN.md) for principles, components and conventions.

Every value here was read out of NPL's stylesheet, not estimated. Contrast ratios were
computed with the same maths as `tools/sitegen/contrast.py`.

---

## 1. Tokens

NPL declares **27 custom properties** in one `:root`. That is the entire design
system's vocabulary.

### Core

| Token | Value | Role |
|---|---|---|
| `--ink` | `#11142B` | Near-black indigo. Body text and borders' darkest note |
| `--paper` | `#FFF8E7` | Warm cream. Page ground |
| `--cream` | `#FFFDF6` | Near-white. Card ground, sits on paper |
| `--line` | `#1E2553` | Deep indigo. Every border and the default hard shadow |
| `--muted` | `#565C73` | Secondary text |
| `--shade` | `#D8D9EA` | Disabled / inactive fills |

### Accents

| Token | Value | Used for |
|---|---|---|
| `--blue` | `#3768FF` | Interactive. Hero ground, focus rings, links |
| `--blue-ink` | `#2C55DA` | Link hover on light grounds |
| `--cyan` | `#65E8FF` | Default tag, hero border |
| `--pink` | `#FF4E91` | The hover shadow. The system's signature |
| `--yellow` | `#FFE168` | Emphasis, focus fill, skip link |
| `--green` | `#5EE780` | Complete / action tag |
| `--orange` | `#FF9958` | Warm accent |

### Status pairs

Each is a background/ink pair, so a status never needs a rule about its text colour.

| Status | Background | Ink | Ratio |
|---|---|---|---|
| live | `#E9FFEF` | `#164D2D` | **9.38:1** |
| archive | `#FFE9F2` | `#822444` | **7.96:1** |
| caveat | `#FFF1BD` | `#6E4A00` | **7.03:1** |

### Tag colours

| Token | Value | Meaning |
|---|---|---|
| `--tag-default` | `#65E8FF` | LEARN |
| `--tag-playful` | `#FFC3DE` | FIELD |
| `--tag-pixel` | `#FFE168` | TIME |
| `--tag-action` | `#5EE780` | ACCESS |
| `--tag-mobile` | `#DCD0FF` | (reserved) |

### Type stacks

```css
--font-mono:  ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
--font-prose: system-ui, sans-serif;
```

**No `@font-face` rules exist.** NPL ships zero webfont bytes. This is the single
largest difference from `Learn-HR`, which loads Fredoka and Space Grotesk at
48,628 B — 68% of its cold first visit.

---

## 2. Colour usage

**Ground is warm, ink is cool.** `#FFF8E7` paper under `#11142B` ink. The warmth
keeps a hard-edged system from feeling clinical.

**One accent does the work at a time.** Blue carries interaction. Pink appears
almost exclusively as a *hover shadow* — never as a fill behind text.

**Colour is never the only signal.** Tags pair colour with an uppercase word
(`LEARN`, `FIELD`). Status chips pair colour with words.

### Contrast, measured

| Pair | Ratio | Verdict |
|---|---|---|
| ink on paper | **17.12:1** | AAA |
| ink on cream | **17.81:1** | AAA |
| muted on paper | **6.25:1** | AA |
| blue-ink on paper | **5.80:1** | AA |
| white on blue (hero) | **4.58:1** | AA — but only just |
| ink on cyan / yellow / green / pink / orange | 11.4–14.0:1 | AAA |

**A correction, because this document was wrong once.** An earlier version of this
guide warned that the hero eyebrow is yellow on blue at 3.54:1. That was a pair
computed while auditing the palette, not something the reference renders: the
eyebrow is a **yellow chip carrying ink text at 14.00:1**, and no yellow-on-blue
text exists anywhere in the reference. The real hero measures:

| Part of the hero | Pair | Ratio |
|---|---|---|
| title | white on blue | **4.58:1** — clears AA even at body size |
| lead | white on blue | **4.58:1** |
| stat chips | white on the chip fill over blue | **11.41:1** |
| eyebrow | ink on yellow | **14.00:1** |

The hero is safe as drawn. The 3.54:1 figure is real but describes a pairing to
avoid, not one to fix.

---

## 3. Type

**The base font is monospace.** `body { font: 16px/1.55 var(--font-mono) }`. This is
unusual and is most of the family's character. Prose (`--font-prose`) is reserved for
running copy inside cards, where legibility at length matters more.

### Scale

| rem | px @16 | Where |
|---|---|---|
| 2.75 | 44 | Hero heading |
| 1.55 | 24.8 | Section heading |
| 1.2 | 19.2 | Card title (`h5`) |
| 1.08 / 1.05 | ~17 | Lead paragraphs |
| 1 | 16 | Body |
| .82 | 13.1 | Provider line |
| .77 / .76 / .75 | ~12.3 | Meta chips |
| .72 | 11.5 | Eyebrow, tags |
| .68 / .67 | ~10.8 | Done control, fine print |

The scale is **untyped** — values are set per component, not from a named ramp. If
this becomes a shared system, it should be turned into named steps so both sites can
draw from the same set.

### Weight and case

- **800** dominates (9 uses), then **900** (5), then **700** (3). Light weights are
  absent.
- **`text-transform: uppercase`** appears 8 times — eyebrows, tags, buttons.
- **Letter-spacing** splits by direction: positive `.05em`–`.06em` on uppercase
  micro-labels; negative `-.02em` to `-.06em` on headings, tightening as size grows.

---

## 4. Spacing

No fixed scale — **fluid `clamp()` throughout**, so spacing is continuous rather than
stepped. Every clamp shares a shape: a floor in px, a `vw` middle, a ceiling in px.

| clamp | Used |
|---|---|
| `clamp(8px, 2.2vw, 14px)` | Shell padding |
| `clamp(10px, 2vw, 14px)` | Tight internal padding |
| `clamp(10px, 2.7vw, 14px)` | Control padding |
| `clamp(12px, 3vw, 18px)` | Grid gap — the most common |
| `clamp(13px, 3.6vw, 18px)` | Card padding — the most common |
| `clamp(13px, 2.7vw, 29px)` | Section rhythm |
| `clamp(20px, 3.6vw, 52px)` | Large section gap |
| `clamp(18px, 6.3vw, 77px)` | Hero padding |
| `clamp(14px, 5.4vw, 70px)` | Hero inline padding |

**Grid gap and card padding are the same value** (`~12–18px`), which is what makes the
layout read as a system rather than a set of guesses.

---

## 5. Borders, corners, shadow

**Corners are square.** Exactly one `border-radius` in 27 KB of CSS: `2px`. Everything
else is a right angle.

**Borders are heavy and always visible.**

| Width | Uses |
|---|---|
| 2px | 16 — controls, tags, inputs |
| 3px | 12 — cards, panels |
| 1px | 8 — hairlines, checkmarks |
| 4px | 2 — the hero |

**Shadow is a hard offset, never a blur.** No blur radius anywhere.

| Shadow | Uses |
|---|---|
| `6px 6px 0 var(--line)` | 5 — cards at rest |
| `3px 3px 0 var(--line)` | 2 — small controls |
| `10px 10px 0 var(--pink)` | 2 — card hover |
| `8px 8px 0` / `5px 5px 0 var(--pink)` | 3 — hero, emphasis |
| `4px 4px 0 var(--shade)` | 1 — disabled |
| `0 0 0 2px var(--cyan)` | 1 — ring |

**The hover contract:** a card lifts `translate(-3px,-3px)` while its shadow grows
from `6px` to `10px` and changes from line to pink. The element appears to rise
toward the reader as its shadow deepens.

---

## 6. Layout

- **Shell:** `max-width: 1320px`, centred, fluid padding
- **Catalogue grid:** single column, reflowing wider where space allows
- **Section head:** flex row — heading group left, count right — collapsing on narrow
  screens
- **Card top:** a two-column grid, `29px` badge beside the title

---

## 7. Motion

| Property | Duration | Easing |
|---|---|---|
| `transform`, `box-shadow` | `.14s` | `ease` |
| `width` (progress bar) | `.18s` / `.2s` | `ease` |

Motion is **confirmation, not decoration** — it tells you a card is interactive or a
bar moved. Nothing animates on load. `prefers-reduced-motion` is honoured in CSS.

---

## 8. Focus and accessibility

- **Focus ring:** `outline: 3px solid var(--blue)`, `outline-offset: 3px`. Some
  controls use 4px. Never removed.
- **Secondary focus treatment:** fill `--yellow` with a `3px 3px 0` shadow, for
  controls where an outline alone would be lost.
- **Skip link:** off-canvas until focused, then yellow with a 2px border.
- **`sr-only`:** a real utility class, used for search and filter labels.
- **`[hidden] { display: none !important }`** — one rule, applied consistently.
- **`prefers-reduced-motion`:** honoured.

---

## 9. Print

A genuine print stylesheet, not an afterthought:

- `html, body` → white ground, `#111` text
- `body` → **11pt**
- `.shell` → no max-width, no padding
- `.hero` → white ground, 2px border, **no shadow**, `14pt` padding

The rule is: **drop the colour, drop the shadow, keep the structure.** A printed page
costs the reader ink, so the system stops spending it.

---

## 10. The short version

Warm cream ground. Cool near-black ink. Square corners. Heavy borders. Hard offset
shadows that turn pink on hover. Monospace by default. Uppercase micro-labels with
positive tracking, headings with negative. Fluid spacing, no fixed steps. System
fonts only. A focus ring you cannot miss.
