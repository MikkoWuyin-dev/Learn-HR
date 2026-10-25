# HANDOVER.md — read this before you touch anything

Written **2026-10-25** at `e5fc150` (main, just after PR #17 merged).

This file exists because the two capped docs cannot hold it. `STATUS.md` sits at its
**160-line** ceiling and `AGENTS.md` at its **200-line** ceiling, so the volatile
things a new session needs live here, where there is no cap. Read `AGENTS.md` for
the project itself, then this file for the state of the work and the traps.

Nothing here replaces reading the code. It tells you what the code will not tell you.

---

## 1. Get running

```bash
cd /home/user/Learn-HR
python3 tools/sitegen/sitegen.py                       # build -> _site/
python3 -m http.server 8000 --bind 0.0.0.0 --directory _site

npm install                                            # html-validate; gate FAILS without it

# Chromium, for the 41 browser checks (~209 MB):
npm i --no-save --no-audit --no-fund @sparticuz/chromium puppeteer-core
rm -f /tmp/chromium && rm -rf /tmp/al2023
node -e "const c=require('@sparticuz/chromium').default;const {inflate}=require('@sparticuz/chromium');(async()=>{await c.executablePath();await inflate('node_modules/@sparticuz/chromium/bin/al2023.tar.br');})();"

# The gate:
CHROME_PATH=/tmp/chromium LD_LIBRARY_PATH=/tmp/al2023/lib python3 tools/sitegen/check.py
```

Verified 2026-10-25: **Chromium 153.0.8010.0**. `/tmp` is *not* reliably wiped —
check with `ls` before re-inflating, it has survived a turn boundary before.

---

## 2. THE SANDBOX RESET — read this before you trust `git status`

This has happened on **four consecutive sessions**. Between turns the sandbox resets:

- `_site/`, `node_modules/`, `/tmp/chromium`, `/tmp/al2023/` are **deleted**
- any running preview server is **killed**
- **the branch pointer is reset to an older commit, while the files stay on disk**

That last one is the dangerous one. You will see something like:

```
$ git status
 M site/static/site.css
 M tools/sitegen/sitegen.py      <-- looks like uncommitted work
$ git rev-parse --short HEAD
1cf1167                          <-- an OLD commit
```

**The work is almost certainly not lost — it is on the remote.**
Do not commit it, do not force-push, do not "clean up". Recover in this order:

```bash
git fetch origin <your-branch>                     # e.g. arena/0718610d-learn-hr
git log --oneline origin/<your-branch> -5          # is your work there?

# Prove it matches before moving the pointer:
for f in $(git diff --name-only HEAD); do
  a=$(git show origin/<branch>:"$f" 2>/dev/null | sha256sum | cut -c1-12)
  b=$(sha256sum "$f"                             | cut -c1-12)
  [ "$a" = "$b" ] && echo "SAME $f" || echo "DIFFER $f"
done

# Only if EVERY file says SAME:
git reset --mixed origin/<branch>
```

**If any file DIFFERS, stop and ask the owner.** Your on-disk files are newer than
the remote and resetting would destroy them.

Related: after a PR is merged the branch enters `pr_merged` and **remote GitHub
access is blocked** until the owner presses **Continue**. That is expected, not an error.

---

## 3. What is built right now

Measured from a fresh build at `e5fc150`, not remembered:

| | |
|---|---|
| Routes | 55 |
| Top band | **55/55** — 9 tall (has a hero), 46 slim |
| Numbered section tabs | 275 (55 × 5) |
| Tinted block cards | 251 |
| Inline SVG icons | 372 |
| Old cream navbar | **0 pages** |
| Worst composited contrast | 4.72:1 (all routes, 390px) |
| Worst contrast in the new band | 4.58:1 |
| Heaviest cold route | **27,516 B** of the 40,960 B budget |

The most recent change (PR #17) removed the cream navbar and made the hero a
full-bleed band at the top of every page, carrying the name
**"Fieldnotes — open learning"** and the five sections as numbered folder tabs.

The catch that shaped it: **the navbar was on all 55 pages but the hero was on only
nine.** Deleting the bar would have stranded the other **46** — the 25 week pages,
19 resource pages, the law card and the templates — with no navigation at all. So
the band is built on every page: tall where there is a hero to put inside it, slim
where there is not.

The band sits **outside `<main>`**, which is what keeps the skip link honest.

---

## 4. Standing rules from the owner

These are not all in `AGENTS.md`; several live only in conversation.

- **No webfonts.** 48,628 B was deleted for this. Do not reintroduce one.
- **No inline styles anywhere** — enforced by `no-inline-style` from `html-validate:recommended`.
- **No Tailwind.** The design system owns every visual value. New colours and spacing go in `design-system/tokens/fieldnotes.tokens.json`, then `node design-system/tools/build-tokens.mjs`.
- **The gate must exit 0** before work is called done. **Never weaken a test to make it pass — retarget it.**
- **`content/` is the only source of copy.** Never edit generated output.
- **One concern per PR.**
- **`HR_Roadmap_Library.*` and the five `.docx` files are frozen.**
- No accounts, no cookies, no tracking. Every fact page carries a "checked on" stamp.
- Output goes to `_site/`, never `dist/` or `build/`.
- **The owner explicitly invited pushback:** "You're allowed to push back on my decisions if they'll cause issues in future."
- Raising the JS page budget is allowed at your discretion, but **must be reported every time**, with a dated comment in `audit.py`.
- **Doc caps: `STATUS.md` 160, `AGENTS.md` 200.** Ceilings, not targets. **Do not run a reflow/re-wrap script on either file — it mangled them twice.** Move content into this file instead.
- Commit once the gate passes; push to the session branch at the end of every implementation round. Merge, history-rewrite, deploy and release need the owner's approval.

---

## 5. Skills

There are **no global skills installed on this machine.** Checked `~/.claude/skills`,
`~/.codex/skills`, `~/.gemini/skills`, `~/.config/opencode/skills`, `~/.cursor/skills`,
`~/.agents/skills`, `~/.amp/skills` — none exist. The only skills are the seven in `skills/`:

| Skill | Use it? |
|---|---|
| `accessibility-compliance` | **Yes** — landmarks, skip links, 44px targets |
| `responsive-design` | **Yes** — touch targets, wrapping |
| `design-system-patterns` | **Yes** — tokens own every value |
| `ui-ux-pro-max` | Partly — 202 layout patterns; its icon data has **no SVG paths** |
| `design-taste-frontend` | **Overridden for this work** — it wants one accent colour and no decorative shapes; the owner asked for the opposite. Follow the owner. |
| `copywriting` | Lightly |
| `react-state-management` | No — there is no React here |

**Do not install `nextlevelbuilder/ui-ux-pro-max-skill`.** The repo already ships
`skills/ui-ux-pro-max`; a second copy would diverge. (This was declined once already.)

---

## 6. Traps that cost real time

**Verification**
- **A renamed class blinds two guards silently.** `audit.py`'s control-height guard and the browser's 44px sweep both matched `.site-nav a`. When that class became `.hero-nav a`, both had to be updated or they would keep passing while measuring nothing. **If you rename a control class, grep `audit.py` and `browser_check.mjs`.**
- **Verify composition, not just values.** The band's colours, contrast, tab size and print behaviour were all correct while the headline sat 4px from the window edge and the wordmark 52px clear of the body text. **No check compares one element's position to another's.** When you move or add a block, measure its left edge against the page body's.
- **A colour can pass for body ink and still fail for muted text.** The coral tint carried ink at 12.93:1 but muted `#565C73` at only 3.86:1. Validate a tint against *every* text role that can land on it.
- A guard is worthless until **mutation-tested both ways**.

**CSS**
- **A full-bleed box insets its contents by its border width.** At 1440px the centring absorbed the band's 4px border; at 390px it did not. Side borders on an edge-to-edge box cannot be seen but still cost layout.
- **`.hero.band` outspecifies `.hero`.** Any rule you write for `.hero` (print, narrow-screen) needs a `.hero.band` twin or it silently loses.
- **A `@media` block adds no specificity.** A print rule placed *before* the rules it overrides will lose. Several print overrides sit at the **end** of `site.css` for exactly this reason.
- Multiple `<aside>` elements fail `html-validate unique-landmark`; repeatable wrappers must be `<div>`.

**Tooling**
- **`html-validate` FAILS the gate when missing** (owner's decision, 2026-10-22) — it does not skip. `npm install` before running the gate.
- **Chromium checks print `SKIP`, not fail**, when `CHROME_PATH` is unset. A skipped run is not a clean run.
- **`browser_check.mjs` samples a fixed selector list.** It will not notice text failing on a new component. Check 41 (the all-routes card sweep) exists for exactly this.
- **`grep -c` counts lines, not occurrences**; built HTML is one line. Use `grep -o … | wc -l`.
- **Never use Python's `hash()` to pick a colour** — it is salted per process. `tint_for()` uses `zlib.crc32`.
- **`contrast.py`: `rgb(x)` returns `(tuple, alpha)`**; `ratio()` wants raw tuples — `ratio(rgb(a)[0], rgb(b)[0])`.
- **`ratio()` inside `build_style_guide` takes token *names*** — `ratio("mint", "ink")`, not hex.
- Puppeteer's `page.evaluate` with a template-literal string throws; pass a real function.
- `inflate()` in `@sparticuz/chromium` returns a **path, not data**, and `executablePath()` lives on `.default`.
- A Python `str.replace` on source containing `\"` escapes silently matches 0 times — use `edit_file` with literal text instead.
- When checking a built site, resolve relative hrefs with `urljoin` against each page's own URL. Naive concatenation gives false alarms, and collapsing `http://` to `http:/` silently checks nothing.

---

## 7. Open decisions waiting on the owner

- **The band's cyan side borders** were removed to fix a 4px misalignment. The owner may want them back — the 4px returns with them unless the content is inset to compensate.
- **The home page kicker** ("The compass") was removed; "Fieldnotes — open learning" now sits in the band on every page. The owner may want it back as its own line in the hero.
- **The visible name and the machine-readable name disagree.** The band says "Fieldnotes — open learning", but `<title>` suffix and `og:site_name` are still "HR Library" (`sitegen.py:627`, `:668`), and the home page's own title is still "Your HR Library" (`:887`, `:890`). Undecided whether to align them.
- **`/check/`** is the only route with no tinted cards — deliberate or not, undecided.
- **doc5 puts the five direct approaches in Week 24; doc2's Phase 7 puts them in Week 23.** Owner's call.
- **Share cards are SVG only** — no rasteriser in this environment, and most social platforms reject SVG.
- **Nobody has looked at the site.** Every claim in this repo is measured, never observed. **No session has had vision.** Screenshots live in `~/shots-vibrant/` and `~/shots-band/`.
- Already **acknowledged** by the owner, no need to re-raise: the 40 KB cold-visit budget, and the cleared Vercel dashboard build-command override.

---

## 8. What "done" means

`CHROME_PATH=/tmp/chromium LD_LIBRARY_PATH=/tmp/al2023/lib python3 tools/sitegen/check.py`
must exit 0 — **12 steps**, and **41 browser checks** inside the "browser checks" step.
As of `e5fc150` both were green.
