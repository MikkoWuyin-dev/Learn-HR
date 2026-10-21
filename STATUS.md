# STATUS

<!-- Overwrite this file at the end of each task. Don't append to it. Keep it under 80 lines.
     It is the only place that says "where we are". The commit log is the history. -->

Updated: 2026-10-21 by Buffy (Freebuff)

## Now
- **Phase 1 core is built and green.** `python3 tools/sitegen/sitegen.py` writes 52 routes to
  `_site/`; `python3 tools/sitegen/audit.py` passes 13/13; the .docx regression passes.
- Not started: Phase 2 (progress, copy buttons, filters), Phase 3 (sitemap, JSON-LD, service
  worker), the 47-URL sweep (task 0.2).

## Last done
- Extended `parse()` in `scripts/docx_render.py` (not forked): `slug()`, unique heading ids,
  `#### Title 【KEY】` → `id="card-key"`, per-table `data-k` keys, `{{var}}` support + `subst()`.
- Fixed two real defects found on the way: `inline_html()` nested an anchor inside its own href
  (bare-URL pass re-linkified URLs it had just wrapped); table keys now reset per table and take
  the bold lead-in, so adding a tracker row no longer shifts every artefact key.
- `tools/sitegen/sitegen.py` — extract + five render paths; `site/static/site.css` — token-only
  layer; `tools/sitegen/audit.py` — links, budget, caption/scope, stamp, keys, copy leaks;
  `tools/sitegen/docx_regression.py` — the 1.7 gate, rerunnable.
- Verified through the browser: Fredoka 700 on h1 (−0.02em), 3px ink borders, 48px cards,
  `6px 6px 0 ink` shadows, 12px table text, ink/70 quiet text, no horizontal overflow at 360px.

## Numbers that are proven (rerun the command, don't trust the line)
- Routes: 52 = home, 5 doc pages, plan + **22** week pages, library + 20 cards, law card,
  templates, check, downloads. `find _site -name index.html | wc -l`
- CSS: 4,579 B gzipped (site.css + wakeout.css) against R24's 45 KB.
- Largest page 27,233 B against 120 KB. 234 `data-k` keys, all unique. 34 tables, all with
  `<caption>` and `scope="col"`.

## Decisions locked (owner, 2026-10-21)
- **D1** whole minified `wakeout.css`; **D5** stickers −2°…−6°; **R20** hand-written token-only
  layer, `.wk-*` clause recorded as a deviation; table = guide geometry + 12px type; print =
  token-only layer.

## Not verified, and why
- **Print to A4** (R22): the print layer is written and token-only, but no PDF has been produced —
  that is Phase 4, and needs Chrome or a phone.
- **Lighthouse / throttled 3G** (R25), keyboard-only run (R26 flow), JS-disabled crawl: Phase 4.
- **Screenshots**: the preview webview would not composite in this session, so the design was
  checked by computed styles and DOM, not by eye. Say so before claiming it "looks right".
- `/check/` shows **no sweep data**: task 0.2 has not run, so the page renders the 47 links with
  "not yet swept" rather than inventing statuses.

## Blocked on an owner decision
1. **Weeks 22–24 have no week tables.** doc2 hands them to doc5 in one paragraph, so the site has
   22 week pages, not the 25 the route map and the "/24" progress bar assume. Options: keep 22 +
   the phase-7 note (current), or author three week blocks (new copy — needs your words).
2. **`--wk-muted` is broken upstream.** `wakeout.css` declares it twice, the second time as a
   reference to itself, so every `var(--wk-muted)` resolves to nothing; `--wk-muted-foreground`
   has the same defect. The site uses `--wk-ink-70` and `--wk-sunrise` instead. The fix belongs in
   `tokens.json` — your call, since that changes the design system.
3. **R20 deviation**: the site has no `.wk-*` class surface. Confirmed by you; carried for the
   launch notes.
4. **OFL text**: the fonts may ship (SIL OFL 1.1) but the bundle has no licence file, so the
   required licence text still has to be added before a public deploy.
5. **Home copy**: R6's "Document 2 → the Plan" is applied in two sentences and the five document
   labels are linked; "Six files, one plan" still reads as if six files are on the page.

## Next justified step
Phase 2.1: `progress.js` against the existing `data-k` keys, with every localStorage access in a
try and `aria-pressed` on the toggles — the keys are already stable and audited.

## Session traps
- `python3`/`python` on PATH are Microsoft Store stubs that exit 49. Real interpreter:
  `/c/Users/micha/AppData/Local/Python/bin/python3` (3.14.3). Set `PYTHONIOENCODING=utf-8` before
  printing content: the console is cp1252 and `₦` raises UnicodeEncodeError.
- `/tmp` is not a path for Windows Python — use a workspace dir or `tempfile`.
- `python-docx`, `fonttools`, `brotli` are installed **user-level** for the gates. They are dev
  tools; nothing in the repo depends on them at runtime.
- The design system's `tools/build-tokens.mjs` shells out to `/bin/bash -c shasum` and dies on
  Windows. Never "fix" the checksummed copy; copy the tree, patch that line, diff.
- Generated output goes to `_site/`, never `dist/` or `build/` — those names are dropped from
  snapshots.
