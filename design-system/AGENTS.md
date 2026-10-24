# Fieldnotes design system — brief for the agent touching it next

Read this before editing a token, a stylesheet rule, or `build-tokens.mjs`.

## 0. The shape of it

```
tokens/fieldnotes.tokens.json   source of truth. Values + the evidence they were read from.
tools/build-tokens.mjs          compiles the JSON into artifacts/fieldnotes.css
artifacts/fieldnotes.css        generated. Never hand-edit — the next build erases it.
```

Consumers never read the JSON at build time except for one thing: `sitegen.py`
reads the share-card colours straight out of it, so a card cannot drift from
the site. Everything else reads the CSS.

Rebuild after any edit to the token file:

```
node design-system/tools/build-tokens.mjs
```

## 1. The one rule

**`tokens/fieldnotes.tokens.json` is the only place a value may be written.**
`site/static/site.css` may only reference `var(--fn-*)`. The build's output
audit fails on a colour literal in the site layer — including inside a
`@media print` block, which is the temptation, because print feels like it
should be exempt. It is not. Add a token instead.

Every token carries `evidence`: the CSS declaration it was read from, or
`"literal, N uses"`. If you invent a value the reference never shipped, set
`"inferred": true` and say why in `note`. An undocumented invention is how a
system quietly becomes a different system.

## 2. Invariants

1. **Corners are square.** The reference stylesheet contains exactly one
   `border-radius` in 27,771 characters (2px, on `.tour-highlight`). Rounding a
   card, a button or a pill is the fastest way to leave the family.
2. **Shadows are hard offsets with no blur.** `3px/6px/10px`, `x === y`, spread
   0. A blur radius anywhere reads as a different brand.
3. **The hover contract is one gesture.** `translate(-3px,-3px)` while the
   shadow grows `6px → 10px` and turns from `--fn-line` to `--fn-pink`. The
   element rises as its shadow deepens. Change one half and the physics break.
4. **The chrome face is monospace.** Headings, labels, buttons, stamps, table
   heads. Only running copy — `p`, `li`, `td`, `blockquote` — opts into the
   reading face. The reference does the same in reverse: its base is mono and
   its prose blocks opt into `--font-prose`.
5. **No webfonts, ever.** Nothing emits `@font-face` and the build copies no
   woff2. Two self-hosted faces cost 48,628 B — 68% of a cold first visit —
   and `weight.py` now carries a 40 KB budget that a reintroduced font would
   blow on its own. If someone asks for a webfont, that budget is the argument.
6. **Saturated fills take ink text, not paper.** Paper on the system blue is
   4.32:1, under the floor; that is why the share-card chip is ink-on-paper
   (17.12:1) rather than blue.
7. **Focus is a 3px blue ring at 2px offset, never removed.** Controls that
   already sit on a coloured ground take a yellow fill as well.
8. **Uppercase always ships with `tracking-widest`.** An uppercase label at
   normal tracking is a bug here.
9. **Motion is confirmation, not decoration.** `transform`, `box-shadow` and
   `background` only, `.14s ease`. Nothing animates on load.
   `prefers-reduced-motion` is honoured in CSS.

## 3. Traps already hit

- **A trailing `;` in a regex misses the last declaration in a rule.** The
  reference stylesheet is largely minified, so the final declaration before `}`
  has no semicolon. Match `(?:^|[;{\s])PROP\s*:\s*([^;}]+)` instead — a naive
  `border-radius:\s*([^;]+);` finds one radius in 27 KB and tells you the
  system is square for the wrong reason.
- **Strip CSS comments before parsing a stylesheet.** A comment above a rule is
  otherwise captured as part of its selector, so the rule never matches and the
  contrast check silently measures inherited body text instead.
- **`--fn-well` and the primitives share a name for a reason.** The soft blue
  notice tint is used by callouts, table heads, code blocks and the current-row
  highlight. It is one token, not four near-identical ones.
- **Never put generated output in `dist/` or `build/`.** Those names are
  excluded from the persisted workspace snapshot, so the files exist in the
  shell and vanish from the user's view. Output lives in `artifacts/`.

## 4. Verify before handing anything back

```bash
python3 tools/sitegen/check.py     # the gate: build, audit, contrast, no-JS,
                                   # weight, html-validate, tests, .docx, voice
```

The gate's contrast step reads colours back out of `site.css` and fails any
colour that no pair measures, so recolouring text cannot slip through. It also
fails a pair whose selector has vanished from the stylesheet rather than
silently measuring a fallback.

A passing gate proves the rules are satisfied, not that the page looks right.
There is no browser in this environment, so visual checks are eyeballed from
the CSS or deferred to the owner.

## 5. Provenance

Read from `github.com/MikkoWuyin-dev/Field-Notes_Nature-Photography` on
2026-10-24: 4 inline `<style>` blocks, 27,771 characters, 143 classes, 27
custom properties, no external stylesheet and no webfonts.

This replaced a token set extracted from `wakeout.app`, an unrelated
third-party site — which is why an earlier version of this site used a green
palette and rounded pills. `ref/` keeps that extraction's evidence so the
provenance is on the record; nothing reads it and it is not in force.
