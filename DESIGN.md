# Fieldnotes — Design System

**Deconstructed from:** `Field-Notes_Nature-Photography` (fieldnotes-npl.vercel.app), 2026-10-24.
**Purpose:** the reference for bringing `Learn-HR` into the same family.

This is the system *beneath* the surface — principles, page architecture, components,
interaction and content conventions. Values live in [STYLE-GUIDE.md](STYLE-GUIDE.md).

Everything here was read out of NPL's source, not inferred from screenshots. Where
something could not be determined, it says so.

---

## 1. The one-paragraph summary

A single-page, hard-edged, monospace-first study roadmap on warm cream. Sections are
numbered and announced by an uppercase eyebrow. Content is honest to the point of
sternness: every resource states what is free, what is not, and when it was last
checked. Progress belongs to the reader — stored in their browser, exportable,
and never sent anywhere.

---

## 2. Principles (each with the evidence it was inferred from)

**P1 — The reader owns their data.** Progress sits in `localStorage`, exportable to
JSON and importable again. *"Your progress is stored in this browser, not on a
server. Export a backup to move it between browsers or site addresses."*

**P2 — Never overpromise.** *"The 32-week plan is a first pass, not a promise of
employment or income."* *"This roadmap promises no paid assignment or income."*
Applied per-resource too, not just globally.

**P3 — Separate free from paid, explicitly.** Every resource carries an
**Access and conditions** block naming what is free and what costs money — including
traps: *"The optional 7-day Pro trial auto-converts to the selected paid plan and
charges the payment method unless cancelled; do not start it."*

**P4 — Every fact carries a date.** `Checked 2026-10-23` on every resource. Claims
expire; the system refuses to let them look timeless.

**P5 — Study and practice alternate.** Resources (`R1`, `R2`…) are interleaved with
practice milestones (`P`). Reading without doing is treated as incomplete.

**P6 — Give the next action, not just the link.** Every resource ends with
**Try next:** — a specific, sized action (*"watch Episodes 1-2 and 4-7; test one
setting change during each outing"*).

**P7 — Plain language over polish.** *"Explain assignment versus licence in plain
language."* Short sentences, concrete nouns, no hedging.

---

## 3. Page architecture

The homepage is one continuous document of numbered sections, each announced by an
eyebrow:

| Eyebrow | Section | Role |
|---|---|---|
| `FULL SITE WALKTHROUGH / ABOUT 3 MINUTES` | Tour invitation | Onboarding |
| `FIELD LOG / 01` | Progress panel | Where am I |
| `HOW TO USE THIS ROUTE / 02` | Legend | How this works |
| `32 WEEKS / 09 STAGES` | The catalogue | The content |
| `A PRACTICAL MIX / 03` | Practice loop | How to use time |
| `FIELD GUARDRAILS / 04` | Ethics | Boundaries |
| `FIELD KIT / 05` | Export / import / reset | Data control |

Two eyebrow forms exist, and the choice is meaningful:

- **`NAME / NN`** — a named step in a sequence (`FIELD LOG / 01`)
- **`STAT / STAT`** — a measurement of what follows (`32 WEEKS / 09 STAGES`)

Use the first for orientation, the second for scale.

**Ordering is deliberate:** *where am I → how does this work → the content → how to
spend time → the boundaries → control of my data.* Every new member of the family
should follow that spine.

---

## 4. Component inventory

143 classes. Grouped by role, with anatomy and where it is used.

### Structure
| Component | Anatomy | Notes |
|---|---|---|
| `.shell` | max-width container, fluid padding | `clamp(8px,2.2vw,14px)` |
| `.section-block` | `<section>` + `.section-head` + body | labelled by its heading |
| `.section-head` | eyebrow + `<h2>` on the left, `.count` on the right | flex, space between |
| `.panel` | bordered block with `.panel-heading` + `.panel-note` | the generic container |

### Navigation
| Component | Anatomy | Notes |
|---|---|---|
| `.skip-link` | hidden off-canvas until focused | yellow, 2px border |
| `.filters` | `role="group"` of `.filter-button`s | labelled for screen readers |
| `.search-wrap` | `sr-only` label + `.search` input + `.search-clear` | label is never visible |

### Progress
| Component | Anatomy | Notes |
|---|---|---|
| `.progress-panel` | `.progress-number` (big %) + `.progress-caption` | "0% / 0 of 25 complete" |
| `.progress-track` / `.progress-fill` | bar, animates `width` | `.18s ease` |
| `.streak-row` / `.streak-number` | consecutive-day counter | "0 day practice streak" |
| `.tool-panel` | export / import / reset controls | JSON file in and out |

### Content
| Component | Anatomy | Notes |
|---|---|---|
| `.resource-card` | `.card-top` (badge + `<h5>` title) → provider → `.resource-status` → `.resource-tags` → description → **Access and conditions** → **Try next:** → CTA + `.done-control` | the workhorse |
| `.stage` | `.stage-heading` (numbered) → description → outcomes list → `.resource-grid` | collapsible via `.stage-chevron` |
| `.tag` | uppercase micro-label | variants below |
| `.status` | inline status chip | variants below |
| `.access-details` | `<details>` wrapper for access terms | progressive disclosure |
| `.empty-state` | shown when filters match nothing | never leaves a blank void |

**Tag variants** — the one place colour carries meaning:

| Class | Meaning |
|---|---|
| `.tag` (default, cyan) | LEARN — study material |
| `.tag.p` (pink) | FIELD — practice checkpoint |
| `.tag.px` (yellow) | TIME — planning estimate |
| `.tag.i` (green) | ACCESS — terms and conditions |

**Status variants:** `.status-live` (green), `.status-archive` (pink),
`.status-caveat` (yellow). Each is a background/ink pair — see STYLE-GUIDE.

### Interaction
| Component | Anatomy | Notes |
|---|---|---|
| `.button` | base; `.button-primary` / `-secondary` / `-quiet` | 2px border, hard shadow |
| `.done-control` | visually-hidden checkbox + `.checkmark` box | label wraps the input |
| `.tour-*` (27 classes) | 9-step overlay: highlight, copy, Back/Next, Skip | highlights the live page |
| `.pals-controls` | toggle for decorative companions | explicitly optional |

---

## 5. Interaction patterns

**Hover is a physical lift.** `.resource-card:hover` → `translate(-3px,-3px)` and the
shadow grows from `6px 6px 0` to `10px 10px 0` in pink. Motion is `.14s ease` — fast
enough to feel mechanical, not decorative.

**Focus is loud.** `:focus-visible` gets `outline: 3px solid var(--blue)` with
`outline-offset: 3px`. 4px on some controls. Never removed, never thin.

**Done is a real checkbox.** `.done-control` hides a native `<input type=checkbox>`
under a styled `.checkmark`. Keyboard and screen-reader behaviour come free.

**Filters combine and degrade.** Search + stage filters work together; empty
categories disappear rather than showing empty groups; a no-match shows
`.empty-state` with copy, not a blank space.

**Motion is respected.** `prefers-reduced-motion` is honoured in CSS.

---

## 6. Content conventions

These are the family's fingerprints. They matter more than colour.

- **Eyebrow:** uppercase, letter-spaced, `NAME / NN`
- **Checked stamp:** `Checked YYYY-MM-DD` on every resource
- **Access block:** `**Access and conditions**` — always this heading
- **Next action:** `**Try next:**` followed by a specific, sized task
- **Status:** `Free resource` / `Self-directed practice` / `Practice milestone`
- **Meta chips:** three or four short facts — format, cost, time, checked date
- **Time:** always a range or estimate, never a deadline (*"Plan 1-2 hours"*)
- **Ethics numbered:** `FIELD GUARDRAILS` is a numbered list of imperatives
- **No hedging:** *"do not start it"*, *"never bait"*, *"do not publish precise
  locations"*

---

## 7. Architecture — and the one thing not to copy

**NPL renders its content from JavaScript.** All 25 learning cards are built
client-side from a `DATA` object in `index.html`. With JavaScript disabled, the
catalogue is **empty**.

The workaround is `tools/gen-noscript.py`: a second renderer that produces a plain
HTML equivalent into a `<noscript>` block, kept in sync by a `--check` flag. It
works, but it means **two renderers for one content set**, and a build step that
fails if they drift.

**Do not copy this.** `Learn-HR` builds 54 static pages with Python, so its words are
in the HTML — proven by `tools/sitegen/nojs.py`, which strips every `<script>` from
all 54 routes and verifies the content survives. That property is strictly better and
costs nothing to keep.

**Take the visual system and the conventions. Leave the rendering model where it is.**

---

## 8. What to carry to Learn-HR, and what to leave

**Carry:** the numbered-section spine · eyebrow convention · checked stamps ·
Access and conditions · Try next · tag/status semantics · hard shadow and border
treatment · monospace-first type · loud focus rings · export/import progress ·
guardrails section

**Leave:** client-side rendering · the `<noscript>` parallel renderer · the guided
tour (unless asked — it is 27 classes) · decorative pals

**Decide:** NPL ships **no webfonts** (system mono + system sans). Learn-HR ships
Fredoka and Space Grotesk at 48,628 B — 68% of its cold first visit. Aligning with
the family means either dropping them or accepting that HR is the heavier sibling.
This is the single biggest decision in the redesign, and it is the owner's call.
