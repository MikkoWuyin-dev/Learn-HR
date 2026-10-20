# Kickoff prompt — paste this into the new agent

Copy everything below the line into the first message. It assumes two uploads: `hr-site-handoff.zip` (content + specs + scripts) and your design-system ZIP.

---

You are building a static website from a finished learning library. Everything you need is in the two ZIPs I uploaded; nothing is in your memory, and you should not go and re-research the subject.

Do this in order, and stop and report after step 3.

1. Unpack `hr-site-handoff.zip` so the tree matches `README.md` at its root. Read, in this order: `site-plan/00-CONTEXT.md`, `site-plan/01-PRODUCT-REQUIREMENTS.md`, `site-plan/02-BUILD-ROADMAP.md`, then skim `content/docs/src/doc1.md` and `content/HR_Library_Overview.md` so you know what the words actually look like.

2. Prove the environment by running these and reporting the raw output:

   ```bash
   python3 scripts/validate_build.py content/docs/src/doc*.md
   python3 scripts/style_audit.py content/HR_Library_Overview.md
   python3 scripts/docx_render.py --no-write
   ```

   Expected: word counts near 1382 / 4973 / 3271 / 3013 / 3211 for the five content files, `mechanical problems: 0` on the overview, and the renderer reporting a dry run with nothing written. If any number is far off, stop — the upload is wrong, and building on it wastes the whole session.

3. Run step 0.1 of the roadmap against the design-system ZIP: execute its `tools/` generators to reproduce `artifacts/wakeout.css`, count the `--wk-*` custom properties, read `DESIGN.md` for the table treatment and for whether rotated stickers and print rules are sanctioned, then report:

   - the token group names in `tokens.json`
   - minified byte size of `wakeout.css`, and whether `tools/` can emit a subset of only the tokens used
   - the documented table treatment in one paragraph
   - answers to decisions D1 and D5 in the PRD's open-decisions table
   - any conflict between `DESIGN.md` and the style guide, with which one you propose to follow

   If your sandbox has no network and cannot run the generators, say so plainly and continue on the shipped `artifacts/` files. Say which you did.

Then wait for my go-ahead before writing any page code.

Rules for the whole engagement, from `00-CONTEXT.md` §6 — restate them back to me in step 3 so I know you read them: the markdown under `content/` is the only source of copy; the design system owns every visual value; no Tailwind build; `HR_Roadmap_Library.*` and the five `.docx` are untouched; no accounts, no cookies, no requests off-device; every fact page renders the checked-on stamp; output is static files.

While working, four refusals matter more than anything else you might do well. Do not write a colour literal; use a `--wk-*` variable or leave a `/* TODO no token: … */` and ask me. Do not edit a sentence in `content/` to suit a layout; report the collision and let me decide. Do not state a fee, a wage or a legal entitlement as certain if the source hedges it; copy the hedge. Do not report any task complete without the command output that proves it, including the Phase 1 regression on the five `.docx` (paragraph counts 51 / 100 / 142 / 87 / 118 and hyperlink rels 0 / 0 / 43 / 8 / 0 must be unchanged).
