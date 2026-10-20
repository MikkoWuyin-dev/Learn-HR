# Wakeout UI — design tokens (drop-in bundle)

Extracted from https://wakeout.app on 2026-10-20.
**183 tokens, 6 artifacts, one source of truth.** No build step needed to consume this.

## Fastest path
Open `artifacts/standalone.html` in a browser — the whole system (palette, type ramp, buttons,
cards, shadows, textures, motion) renders offline from one file, then copy what you need.

## Use in a Tailwind v4 project
Copy `artifacts/wakeout.css` and `artifacts/wakeout.theme.css` next to your stylesheet, then:
```css
@import "tailwindcss" source(none);   /* keep: otherwise it scrapes unrelated HTML */
@import "./wakeout.theme.css";
@source "./src";
```
Utilities come with the tokens: `bg-lime text-ink border-3 rounded-2xl shadow-sticker
animate-wiggle text-eyebrow bg-dots`. Custom utilities added here: `border-3`, `border-t-3`,
`bg-dots`, `bg-grid`, `bg-energy`, `bg-sunrise`, `bg-dusk`, `lift`, `font-display`,
`font-body`, `font-app-ui`.

## No Tailwind?
```html
<link rel="stylesheet" href="wakeout.css">
<button class="wk-button wk-button--primary wk-button--sm">Start</button>
<div class="wk-card"><div class="wk-card__body">…</div></div>
```
Or read a token: `getComputedStyle(document.documentElement).getPropertyValue("--wk-primary")`.

## Figma / style-dictionary
`artifacts/tokens.dtcg.json` (W3C DTCG, with `$extensions["wakeout.evidence"]` on each token).

## Regenerate / change
`node tools/build-tokens.mjs` re-emits every artifact from `tokens/tokens.json` — **zero
dependencies, no npm install**. `node tools/contrast.mjs` re-measures WCAG pairs. Then
`node tools/standalone.mjs` to refresh the specimen.

## If this lands in a sandbox like the one it came from
Do **not** rename `artifacts/` to `dist/`. Names like `dist` and `build` are excluded from
persisted workspace snapshots there, so deliverables written to them disappear from the user's
viewer even though the files exist in the shell.

## Before you change a value
Read `AGENTS.md` §3 (invariants) and §4 (traps). Every token's `evidence` field says which CSS
declaration it came from; the radius scale in particular is **not** Tailwind's default.

## Self-check after copying
```bash
grep -o '\-\-wk-radius-2xl:[^;]*' wakeout.css        # → 2.25rem (not 1rem)
grep -o '\-\-wk-shadow-sticker:[^;]*' wakeout.css   # → 6px 6px 0 0 var(--wk-ink)
grep -c -- '--wk-' wakeout.css                        # 183 tokens + aliases
```
