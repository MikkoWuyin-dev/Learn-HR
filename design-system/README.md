# Fieldnotes design system

The shared visual system for the Fieldnotes family of resource libraries.
Learn-HR is the first site to consume it; the Nature Photography Library is the
reference it was read from.

```
tokens/fieldnotes.tokens.json   the one source of truth
        |
        |  node design-system/tools/build-tokens.mjs
        v
artifacts/fieldnotes.css        --fn-* custom properties, the only artefact
        |
        |  copied and minified by tools/sitegen/sitegen.py
        v
_site/fieldnotes.css            linked by every page, ahead of site/static/site.css
```

## The rule

**`tokens/fieldnotes.tokens.json` is the only place a value may be written.**
`site/static/site.css` may only reference `var(--fn-*)`; the output audit fails
the build on a colour literal in the site layer. If a value has no token, it
does not belong on the page — add a token instead.

Rebuild after editing the token file:

```
node design-system/tools/build-tokens.mjs
```

## What the system is

- **Square corners.** The reference stylesheet contains exactly one
  `border-radius` (2px) in 27,771 characters.
- **Hard offset shadows, never a blur.** Rest `6px 6px 0 line`; hover lifts
  `-3px` and the shadow grows to `10px 10px 0 pink`.
- **The chrome face is monospace**; only running copy opts into the reading
  face, because a monospace paragraph is harder work than a monospace label.
- **No webfonts.** The family ships system fonts. Nothing here emits
  `@font-face`, and the build copies no woff2. This is a decision, not a
  limitation: two self-hosted faces cost 48,628 B, 68% of a cold first visit.

Full reasoning is in the repository root:

- [`DESIGN.md`](../DESIGN.md) — principles, the page spine, the component
  inventory and the content conventions, each tied to its evidence.
- [`STYLE-GUIDE.md`](../STYLE-GUIDE.md) — the measured surface: tokens, type
  scale, spacing, borders, shadows, motion, focus and print.

## History

This replaced a token set extracted from `wakeout.app`, an unrelated
third-party site, which is why an earlier version of this site used a green
palette and rounded pills. `ref/` keeps the evidence from that extraction so the
provenance is on the record. It is not in force and nothing reads it.
