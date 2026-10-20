# Wakeout UI — design specification

Spec version 1.0.0 · extracted from https://wakeout.app on 2026-10-20 · 15 pages, 79 kB CSS,
27,931 class uses measured.

This is the human-readable contract. The machine-readable one is `tokens/tokens.json`; if the two
disagree, the JSON wins (it is what `artifacts/` is compiled from).

---

## 1. Model

Four layers, one direction of dependency. Nothing below may reach upward.

```
primitives   --wk-lime, --wk-radius-3xl, --wk-duration-quick   ← literal values, measured
     ↓
semantics    --wk-primary, --wk-background, --wk-shadow-sticker ← var() aliases, never copies
     ↓
components   .wk-button, Button(), Card()                       ← composition only
     ↓
patterns     page scaffolding, section rhythm, surface themes
```

Because semantics are `var()` pointers, a theme change is one declaration:

```css
:root[data-theme="night"] {
  --wk-background: var(--wk-stage);
  --wk-foreground: var(--wk-paper);
  --wk-border: rgba(255, 248, 230, 0.15);
}
```

A component must never hardcode a primitive when a semantic exists. `bg-lime` on a primary button
is wrong; the primary button's tone is `--wk-primary`.

**Naming.** Every emitted variable is `--wk-<group>-<key>`. Tailwind utilities are generated from
them, so `bg-lime` = `background-color: var(--wk-lime)`.

---

## 2. Colour

**The one rule that makes the palette work:** `--wk-ink` (#043629) is simultaneously the text
colour, every border colour, and every shadow colour. That single reuse is why eight saturated
hues read as calm rather than noisy. Introducing a second dark grey for outlines is the most
common way to break this system.

- Surfaces: `paper #fff8e6` (page) → `surface #ffffff` (cards) → `muted #f3ead3` (inset wells).
- Foreground is always ink on a light surface, `paper` on ink/stage/dusk. Never white on lime,
  pink, yellow or orange — the reference deliberately sets `--primary-foreground: #043629`.
- Emphasis is alpha, not extra greys: text at `85% → 70% → 60%`; inverse text `paper/80`.
  Only these alpha steps appear on the reference: 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80,
  85, 90, 95.
- Four themed page surfaces exist: `daylight` (paper), `sunrise` (warm, ink `#5c2e0e`), `stage`
  (near-black green, for product shots), `dusk` (purple, for wind-down content). Charts use
  `chart-1…5` = lime, pink, purple, orange, cyan.
- One gradient in the whole system: `bg-energy` (160°, yellow→orange), used 5 times in 171 pages.
  `bg-sunrise` / `bg-dusk` are surface washes, not decorations.
- `#000` is reserved for media letterboxing. `#0f0f0f / #1a1a1a / #2a2a2a` + traffic-light colours
  exist only inside mock app chrome.

## 3. Typography

Two faces, and the split is functional, not decorative:

| | Face | When |
| --- | --- | --- |
| Statements | **Fredoka** 700 | every heading, every button label, card titles — 773 uses |
| Instructions | **Space Grotesk** 400 | prose, metadata, captions, numbers |

`font-display` on the reference is **not** just a family: `.font-display` ships
`font-family:Fredoka; font-weight:700; letter-spacing:-.02em` together, and this system keeps that
coupling (the generated `@utility font-display` does all three). Applying the display face implies
a bold, tight statement — that is why headings never need `font-bold`.

Weights actually shipped: Fredoka 400/500/600/700, Space Grotesk 300–700 variable. **Never ask for
800 or 900** — `--wk-weight-extrabold/black` are declared in the reference stylesheet but the font
files do not carry them.

Ramp (all measured, ordered by real usage):

```
body-sm 14px  ← 693 uses, the workhorse      headline    36px  leading 1.111
lead    18px  ← card titles + intros         headline-lg 48px  leading 1
caption 12px  ← labels, always uppercase     title       30px
eyebrow 10px  ← 142 uses, tracking .1em      title-sm    24px
label   11px                                  subhead     20px  ← h3
micro    9px  ← inside mock app chrome        display     60px → display-lg 72px → display-xl 88px
```

Hard ceiling: **88px**. Line-height floor: **0.95**, only at ≥48px display sizes.

Leading: `1.625` for paragraphs (415 uses), `1.25` for headings (525), `1` for tight labels,
`0.95` for display. Tracking: `-0.025em` on all display type, `+0.1em` (`tracking-widest`, 255
uses) on every uppercase micro label. Uppercase always comes with wide tracking — an uppercase
label with normal tracking is a bug in this system.

## 4. Space

`--spacing: 0.25rem`; utilities are index × 4px, unchanged from Tailwind.

- Inside components: `gap-2` (8px) is the default inline gap — 293 uses, more than any other gap.
- Cards: `p-6` (24px). Insets: `p-4`.
- Between sections: `py-24` (96px) is the standard rhythm; `py-28` for hero-adjacent, `py-16` for
  dense lists. Section → section separation is a `3px` rule at `ink/10`, not more padding.
- Container: `max-w-6xl mx-auto px-4 md:px-6`; prose columns `max-w-2xl`–`3xl`.

## 5. Shape (radius + border)

The reference remaps Tailwind's radii from a `--radius: 1.25rem` base, so **copying Tailwind's
default scale gives wrong values**. Measured scale, by usage:

```
full  9999px  ×442  ← pills, badges, chips, avatars   (most used)
3xl   3rem    ×220  ← cards
2xl   2.25rem ×216  ← buttons, inputs, panels
lg    1.25rem       ← the base --radius
sm    .5rem / xs .25rem  ← only inside mock chrome and tiny dots
blob-wide  21%/17%  ×10   organic plates, "leaf" shapes
blob-tall  26%/21%  ×10   same, taller variant
```

There is **no small-radius interactive element** in this system. `radius-md` is interpolated (no
rule shipped for it) — do not build on it.

Border widths: `3px` is the default everywhere (517 uses), `4px` for media frames (62), `2px`
inside dark panels (44), `1px` only for dividers and quiet chips. Style is always `solid`, except
`border-dashed` (41 uses) which marks a drop/target zone. Colour is ink at full strength, or
`ink/10–30` when it must recede.

## 6. Elevation

Elevation = a printed sticker. Blur 0, spread 0, x offset === y offset, colour = ink.

```
sticker-sm  3px 3px 0 0 ink    ×179   pressed state, small chips
sticker     6px 6px 0 0 ink    ×324   default raised element
sticker-lg 10px 10px 0 0 ink    ×77   hover state, media frames, hero cards
```

Coloured shadows (`sticker-pink/purple/lime`) exist: identical geometry, ink swapped for a brand
hue — used on one hero card each, so treat them as a highlight, not a default.

Never: blurred shadows, alpha shadows, `shadow-sm/md/lg` from Tailwind (absent from the reference),
inset shadows, or elevation on text-only elements.

## 7. Motion

**Two disconnected systems.** Do not blend them.

*Interaction* — 150ms, `cubic-bezier(0,0,.2,1)`, **only** `transform` and `box-shadow`:

```
rest    → shadow-sticker
hover   → translateY(-2px) rotate(-1deg) + shadow-sticker-lg
active  → translate(4px, 4px) + shadow-sticker-sm
focus   → outline: none + ring 4px rgba(138,56,245,.4)   ← purple at 40%, verbatim from :focus-visible
```

The press distance equals the `sticker-sm` offset, so a pressed element lands exactly flush with
the page. That physicality is the signature interaction; do not change one without the other.

*Atmosphere* — long decorative loops on `aria-hidden` art only:
`wiggle .9s`, `wobble 3s`, `float 5s`, `notif-pop 5s`, `shape-burst 5s`, `spin-slow 12s linear`,
all `ease-in-out` (rotation is `linear`). `notif-pop` is 90% idle then a 3-frame startle — the
long rest *is* the joke, don't shorten it.

Tilt is hierarchy, not spice: `-1deg` interactive feedback · `-2deg` decorative sticker ·
`-6deg` annotation · `±12deg` rare callout (55 uses). Never tilt a paragraph, a form label, or
anything read for more than a second.

`prefers-reduced-motion` stops every loop and drops transitions to 0.01ms; it ships in
`artifacts/wakeout.css`.

## 8. Component contracts

**Button** — the measured recipe, verbatim:

```
inline-flex items-center justify-center gap-2 font-display tracking-wide
border-3 border-ink rounded-2xl shadow-sticker
transition-[transform,box-shadow] duration-150 ease-out cursor-pointer select-none
+ states above
```

Variants (bg → fg, with usage counts): `primary` lime→ink (106) · `ink` ink→paper (115) ·
`paper` white→ink (232) · `pink` pink→ink (69) · `cyan` cyan→paper (21) · `ember` ember→paper (10)
· `purple` purple→paper (5) · `ghost` transparent, **no border, no shadow** (structural, so a
cascade can't re-add them).
Sizes: `sm px-4 py-2 text-body-sm` · `md px-6 py-3 text-body` · `lg px-10 py-5 text-subhead
md:text-title-sm`. `pill` swaps `rounded-2xl` for `rounded-full` (secondary CTAs, filters).

**Card** — `rounded-3xl border-3 border-ink bg-surface shadow-sticker overflow-hidden`, body
`p-6`. Variants: `tilted` adds `-rotate-1`; `flat` removes the shadow and softens the border to
`ink/20` (list rows — the site uses 324 stickers, so rows must not); `media` is `border-4` +
`shadow-sticker-lg` + `bg-black`.

**Sticker / annotation** — `px-4 py-2 rounded-full border-3 border-ink shadow-sticker-sm
text-caption font-bold uppercase tracking-widest`, tilted `-2…-8deg`, absolutely positioned to
overhang the parent edge (the reference offsets it `-left-4 bottom-6`).

**Chip** — same type recipe, but `1px` border at `ink/20`, no shadow, no tilt.
**Eyebrow** — `text-caption font-bold uppercase tracking-widest text-ink/70`, with a 8px dot or
icon when the section is themed.

**Media card** — `aspect-[2/3] rounded-3xl border-4 shadow-sticker-lg`, caption is a `bg-paper/95`
plate *inside* the frame, and a corner `Sticker` carries the duration.

**Toggle** — 2px ink border (not 3px: it lives in mock app chrome), track `w-8 h-3 rounded-full`,
knob `h-3 w-3 rounded-full bg-paper`, `transition-all`.

**Dark panels** — the only place `border-white/10`, `bg-white/5` and `text-white/60` are allowed.
Never mix a white/alpha border with an ink border on the same element.

## 9. Do / don't

| Don't | Instead |
| --- | --- |
| white text on lime/pink/yellow | ink on saturated fills |
| 1px borders on cards/buttons | 3px ink |
| blurred or alpha elevation | hard 0-blur offsets, or none |
| `rounded-sm/md` on interactive surfaces | 2xl controls · 3xl cards · full pills |
| animate colour, size, or opacity on hover | transform + box-shadow only |
| body copy in Fredoka | Fredoka for ≤2-line statements |
| a new hue | reuse the 8 brand hues; charts use chart-1…5 |
| forms on `stage`/`dusk` | those are showcase surfaces; forms live on paper/surface |
| `font-black` / weight 900 | 700 is the ceiling of the shipped files |
| tilt on paragraphs or labels | tilt on stickers, callouts, decorative art |

## 10. Accessibility

- Focus ring: 4px `rgba(138,56,245,.4)` with `outline:none` — exactly as the reference ships it.
  It is visible on paper, surface, lime, pink and yellow; on `ink`/`stage` surfaces add
  `ring-paper/30` alongside it.
- Measured contrast (`ref/contrast.json`): ink on paper **12.67:1** (AAA), ink on white
  **13.42:1**, paper on ink **12.67:1**, primary ink on lime **5.72:1** (AA), accent paper on
  purple **5.0:1** (AA).
- Failures inherited from the reference, kept for fidelity and flagged rather than hidden:
  `ink/60` on paper 3.87:1, `red` on paper 3.69:1, `red` on white 3.91:1, `lime-deep` on paper
  4.27:1 → 18px+ bold only. `ember` on paper **2.67:1 fails** → dark surfaces only.
  If you need small red text, use `--wk-ink` with a red border instead.
- Smallest text in the system is 9px, and it exists only inside mock app chrome; real UI labels
  start at 10px uppercase with `.1em` tracking and should stay under 3 words.
- Decorative loops must be `aria-hidden`. The reference uses
  `aria-pressed` / `aria-current` / `aria-live="polite"` on its interactive bits — so do we.

## 11. Verification

Run `npm run check` (tsc + vite build). The build is the contract test: if a class in the docs has
no token behind it, it will not compile to a rule. Spot-check in a browser:

```js
const b = document.querySelector(".wk-button");
getComputedStyle(b).borderTopWidth     // "3px"
getComputedStyle(b).borderTopColor     // "rgb(4, 54, 41)"
getComputedStyle(b).boxShadow          // "rgb(4,54,41) 6px 6px 0px 0px"
getComputedStyle(b).borderRadius       // "36px"
getComputedStyle(b).transitionDuration // "0.15s"
getComputedStyle(document.querySelector("h1")).letterSpacing // "-0.02em" (from font-display)
```
