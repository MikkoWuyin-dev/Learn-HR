# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 80 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-21 by Buffy (Freebuff)

## Now
- Phase / roadmap step: **Phase 0, step 0.1 done; all decisions locked. 0.2/0.3 not started.**
  Holding at the kickoff's gate: no page code until the owner says go.
- In progress: nothing. Nothing blocks Phase 1.

## Last done
- Unpacked `hr-site-handoff.zip` to the repo root; read 00-CONTEXT, 01-PR, 02-ROADMAP, doc1, overview.
- Environment proof, all three green: word counts 1382/4973/3271/3013/3211; overview
  `mechanical problems: 0`; renderer dry-run writing nothing.
- Unpacked the design system to `design-system/`; 23/23 SHA256SUMS OK (still OK after adding the
  style guide as an unlisted doc).
- Ran `tools/` generators (scratch copy, one POSIX line swapped for `node:crypto`): 183 tokens,
  20 groups; all seven outputs byte-identical to the shipped artifacts.
- Received `styleguide.html`: served it on loopback and read the **rendered** DOM (it is a built
  React SPA, content is in the bundle, so the HTML source alone proves nothing). Marked up its three
  tables' computed styles — that is where the table treatment now comes from.
- Wrote `site-plan/04-DESIGN-SYSTEM-NOTES.md` — the 0.1 exit artifact, now including the style-guide
  analysis, the measured table recipe and the locked decisions.

## Decisions locked (owner, 2026-10-21)
- **D1**: ship whole `wakeout.css`, minified — 2,080 B gzip of a 45 KB budget.
- **D5**: rotated stickers approved at −2°…−6°, stickers/annotations only.
- **R20**: hand-write a token-only site layer; R20's `.wk-*` clause is a **recorded deviation**.
- **Table**: guide geometry + 12px (9pt) type per R26, real `<caption>`, `scope` on header cells.
- **Print**: hand-written token-only print layer per R22.

## Not verified, and why
- Generators executed unmodified: **no** — Windows cannot run their `/bin/bash -c shasum` line.
  Reproduced from a scratch copy with only that hash call replaced, then diffed byte-for-byte
  against the pristine shipped files.
- Whether the shipped woff2 latin subsets contain `₦` (U+20A6): no `brotli`/`fontTools` available.
  Check at 1.4 by rendering the glyph in the specimen.
- Phase 1 regression on the five `.docx` (paragraph counts 51/100/142/87/118, hyperlink rels
  0/0/43/8/0): **not run.** Nothing under `content/` or `scripts/` has been touched, so there is
  nothing to regress yet — the numbers are the baseline to hold against 1.7.
- No git repository exists here, so the "`git diff` shows zero changes under `content/`" proof in
  the PRD's definition of done cannot run. Needs `git init` + a baseline commit when building starts.

## Next justified step
Phase 1.1: extend `parse()` in `scripts/docx_render.py` (add `slug()`, `#### Card 【KEY】` →
`id="card-key"`, `data-k` row keys, `{{var}}`) without touching the `.docx` path, and prove it with
the 1.7 regression before any page is rendered.

## Session traps
- `python3`/`python` on PATH are Microsoft Store stubs that exit 49. Real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3` (3.14.3). Use that path, or `py`.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c "shasum -a 256 …"` and
  dies on Windows. Never "fix" the checksummed copy; copy the tree, patch that one line, diff.
- `styleguide.html` is a client-rendered SPA: the HTML source has no copy, only a bundle. Serve it
  and read the DOM, or you will "verify" an empty page.
- `grep -- '--wk-…'` needs the `--` separator, or grep reads the pattern as an option.
- Generated output must never live in `dist/` or `build/` — those names are dropped from snapshots.
