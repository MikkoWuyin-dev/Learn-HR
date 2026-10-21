#!/usr/bin/env python3
"""Build the HR Library site from content/docs/src/*.md into _site/.

One command:  python3 tools/sitegen/sitegen.py [--no-css]

Everything visible comes from the markdown (PRD R1: no content fork). The design
system owns every visual value (R20): this file emits class names and structure,
never a colour, size or shadow. Values live in site/static/site.css as var(--wk-*).

Layout of the output:

  _site/index.html                     compass, from HR_Library_Overview.md
  _site/1/start-here/                  doc1
  _site/2/plan/                        doc2 as an index + tracker
  _site/2/plan/week/N/                 one page per week table that exists in doc2
  _site/3/library/                     doc3 cards as a grid
  _site/3/library/<card>/               one page per card
  _site/4/nigeria/                     doc4
  _site/4/nigeria/law-card/            doc4's one-page card, print layout
  _site/5/getting-the-job/             doc5
  _site/5/templates/                   doc5's copyable messages only
  _site/check/                         every external URL with its sweep state
  _site/downloads/                     the seven files, with sizes
"""
import html
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import docx_render as R  # noqa: E402

SITE = ROOT / "_site"
DATA = ROOT / "_data"
CONTENT = ROOT / "content"
DOCS = {
    "doc1": "content/docs/src/doc1.md",
    "doc2": "content/docs/src/doc2.md",
    "doc3": "content/docs/src/doc3.md",
    "doc4": "content/docs/src/doc4.md",
    "doc5": "content/docs/src/doc5.md",
}
LAST_VERIFIED = "2026-10-20"
STAMP = "Checked 20 October 2026"

NAV = [
    ("/1/start-here/", "Start here"),
    ("/2/plan/", "The plan"),
    ("/3/library/", "Library"),
    ("/4/nigeria/", "Nigeria & law"),
    ("/5/getting-the-job/", "Getting the job"),
]

# A bare URL wrapped in parentheses, e.g. "(https://search.cac.gov.ng/)" in
# doc5's scam checklist. The shared renderer's URL_RE carries a (?<!\()
# lookbehind so it cannot re-linkify a markdown (url) — which means these are
# left as plain, unclickable text. Handled here, in the site layer only, so
# docx_render.py and the frozen .docx baseline are untouched.
PAREN_URL_RE = re.compile(r"\((https?://[^\s|)<>]+)\)")

VERDICTS = {
    "free-to-finish": "Free to finish",
    "free-to-study-paid-cert": "Free to study · paid certificate",
    "limited-access": "Limited access",
    "check-before-committing": "Check before committing",
}


# ---------------------------------------------------------------- parsing
_cache = {}


def blocks(name):
    if name not in _cache:
        _cache[name] = R.parse((ROOT / DOCS[name]).read_text(encoding="utf-8"))
    return _cache[name]


def md(s):
    """Markdown inline -> HTML, plus two things the shared renderer lacks.

    `code spans` and internal links ([text](/route/)) are parked while
    R.inline_html() runs, then restored. The shared renderer only knows absolute
    http(s) links, and teaching it internal ones would change the .docx text
    runs, which must stay untouched.
    """
    codes, links = [], []

    def park_code(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x01{len(codes) - 1}\x01"

    def park_link(m):
        links.append(f'<a href="{m.group(2)}">{m.group(1)}</a>')
        return f"\x02{len(links) - 1}\x02"

    s = re.sub(r"`([^`]+)`", park_code, s)
    s = re.sub(r"\[([^\]]+)\]\((/[^)\s]*)\)", park_link, s)
    out = R.inline_html(s)
    # Runs while both links and code spans are still placeholders, so
    # neither can be linkified by mistake.
    out = PAREN_URL_RE.sub(r'(<a href="\1">\1</a>)', out)
    out = re.sub(r"\x02(\d+)\x02", lambda m: links[int(m.group(1))], out)
    out = re.sub(r"\x01(\d+)\x01", lambda m: codes[int(m.group(1))], out)
    # Fredoka has no U+20A6 (verified: 217 glyphs, naira absent; Space Grotesk has
    # it). A bare ₦ inside a display heading would fall back mid-word, so the
    # sign always renders in the body face. Typography only — the character and
    # the copy are untouched.
    return out.replace("\u20a6", '<span class="naira">\u20a6</span>')


def plain(s):
    return R.clean_text(s)


def heading_text(b):
    return plain(b["text"])


# ---------------------------------------------------------------- extraction
def week_sections():
    """Every week heading in doc2 that carries a table, in order."""
    bs = blocks("doc2")
    out = []
    for i, b in enumerate(bs):
        if b["t"] != "h":
            continue
        m = re.search(r"\bweek\s+(\d+)\b", heading_text(b), re.I)
        if not m:
            continue
        n = int(m.group(1))
        body = []
        for nb in bs[i + 1:]:
            if nb["t"] == "h" and nb["l"] <= b["l"]:
                break
            body.append(nb)
        if not body:
            continue
        title = heading_text(b)
        title = re.sub(r"^PHASE\s+\d+\s*·\s*", "", title)
        title = re.sub(r"^Week\s+%d\s*·\s*" % n, "", title)
        out.append({"n": n, "title": title.strip(), "heading": heading_text(b),
                    "id": b["id"], "blocks": body})
    return out


def cards():
    """doc3: one `####` heading per resource, with its bullet fields."""
    bs = blocks("doc3")
    out = []
    for i, b in enumerate(bs):
        if b["t"] != "h" or b["l"] != 4:
            continue
        body = []
        for nb in bs[i + 1:]:
            if nb["t"] == "h" and nb["l"] <= 4:
                break
            body.append(nb)
        fields = {}
        for nb in body:
            if nb["t"] != "list":
                continue
            for it in nb["items"]:
                m = re.match(r"^\*\*([^*]+?):?\*\*\s*(.*)$", it["text"])
                if m:
                    fields.setdefault(m.group(1).strip().lower(), m.group(2).strip())
        out.append({"id": b["id"], "title": heading_text(b), "raw_title": b["text"],
                    "fields": fields, "blocks": body})
    return out


def verdict_of(cost):
    low = (cost or "").lower()
    if "limited access" in low or "time-limited" in low or "no certificate" in low:
        return "limited-access"
    if "check before" in low or "verify" in low or "before you commit" in low:
        return "check-before-committing"
    if "free certificate" in low or "certificate of completion** (no application" in low:
        return "free-to-finish"
    return "free-to-study-paid-cert"


def section(name, pattern):
    """The first heading matching `pattern` and the blocks beneath it."""
    bs = blocks(name)
    for i, b in enumerate(bs):
        if b["t"] == "h" and re.search(pattern, heading_text(b), re.I):
            body = []
            for nb in bs[i + 1:]:
                if nb["t"] == "h" and nb["l"] <= b["l"]:
                    break
                body.append(nb)
            return b, body
    return None, []


def table_by_head(name, first_col):
    for b in blocks(name):
        if b["t"] == "table" and b["head"] and b["head"][0].strip().lower() == first_col:
            return b
    return None


def tracker():
    tables = [b for b in blocks("doc2") if b["t"] == "table"]
    courses = next((t for t in tables if t["head"][:2] == ["#", "Item"]), None)
    artefacts = next((t for t in tables if t["head"][:2] == ["#", "Artefact"]), None)
    return {"courses": courses, "artefacts": artefacts}


def external_urls():
    """Every distinct external URL in the five documents, first-seen order.

    Three patterns are needed because the corpus spells links three ways: the
    markdown form `[text](url)` (LINK_RE), the bare form `Link: https://…`
    (URL_RE) and the parenthesised bare form `(https://…)` (PAREN_URL_RE).
    The page linkifies all three, so the sweep has to cover all three.
    Collecting only the markdown form found 12 of the 47 URLs.

    No trailing-punctuation trimming, deliberately: the URL recorded here is
    the exact string the page links to, so a bad href shows up as a bad sweep
    result rather than being silently corrected in one place only.
    """
    seen, out = set(), []
    for name in DOCS:
        for b in blocks(name):
            texts = []
            if b["t"] in ("p", "quote"):
                texts.append(b["text"])
            elif b["t"] == "list":
                texts += [i["text"] for i in b["items"]]
            elif b["t"] == "table":
                texts += b["head"] + [c for row in b["rows"] for c in row]
            elif b["t"] == "h":
                texts.append(b["text"])
            for t in texts:
                for regex, group in ((R.LINK_RE, 2), (R.URL_RE, 1),
                                     (PAREN_URL_RE, 1)):
                    for m in regex.finditer(t):
                        url = m.group(group)
                        if url not in seen:
                            seen.add(url)
                            out.append(url)
    return out


# ---------------------------------------------------------------- rendering
def render_table(b, caption=None, ns=None):
    """`ns` renames the row keys, for a table that renders on a second page.

    parse() mints each table's data-k once, so rendering one table on two
    pages would emit the same key twice. That fails the site-wide uniqueness
    check and would mean ticking one copy ticked the other (R9). Namespacing
    keeps the keys distinct and still traceable to their source row.
    """
    head = "".join(f'<th scope="col">{md(c)}</th>' for c in b["head"])
    rows = []
    for i, row in enumerate(b["rows"]):
        key = b["keys"][i] if i < len(b.get("keys", [])) else ""
        if key and ns:
            key = f"{ns}-{key}"
        cells = "".join(f"<td>{md(row[j] if j < len(row) else '')}</td>"
                        for j in range(len(b["head"])))
        rows.append(f'<tr data-k="{key}">{cells}</tr>')
    cap = f'<caption class="table-caption">{md(caption)}</caption>' if caption else ""
    return (f'<div class="card table-card"><div class="scroller"><table>{cap}'
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>")


def render_blocks(bs, level=2, caption_from_heading=True, default_caption="", ns=None):
    out, current = [], default_caption
    for b in bs:
        t = b["t"]
        if t == "rule":
            out.append('<hr class="rule">')
        elif t == "h":
            lvl = min(max(b["l"], 2), 4) + (level - 2)
            lvl = max(2, min(lvl, 4))
            current = heading_text(b)
            out.append(f'<h{lvl} id="{b["id"]}">{md(b["text"])}</h{lvl}>')
        elif t == "p":
            out.append(f"<p>{md(b['text'])}</p>")
        elif t == "quote":
            out.append(f'<aside class="callout"><p>{md(b["text"])}</p></aside>')
        elif t == "code":
            out.append("<pre><code>" + html.escape("\n".join(b["lines"])) + "</code></pre>")
        elif t == "list":
            tag = "ol" if b["items"][0]["ordered"] else "ul"
            items = "".join(
                f'<li class="{"sub" if it["ind"] >= 2 else ""}">{md(it["text"])}</li>'
                for it in b["items"])
            out.append(f"<{tag}>{items}</{tag}>")
        elif t == "table":
            out.append(render_table(b, caption=(current if caption_from_heading
                                                else default_caption) or None, ns=ns))
    return "\n".join(out)


def page(path, title, body, *, lead="", extra_head="", body_class=""):
    """Write one page. `path` is the directory under _site, '' for the root."""
    depth = 0 if not path else path.strip("/").count("/") + 1
    root = "../" * depth
    # The attribute is built outside the f-string: an escaped quote inside an
    # f-string expression is a SyntaxError before Python 3.12 (PEP 701), and
    # this build has to run on 3.11.
    nav = []
    for href, esc in NAV:
        here = (' aria-current="page"'
                if path and href != "/" and path.startswith(href.strip("/"))
                else "")
        nav.append(f'<a href="{root}{href.strip("/")}/"{here}>{esc}</a>')
    nav = "".join(nav)
    stamp = (f'<p class="stamp"><span class="stamp-dot" aria-hidden="true"></span>'
             f'{STAMP} · <a href="{root}check/">see every link checked</a></p>')
    doc = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — HR Library</title>
<meta name="description" content="{html.escape(lead)[:180]}">
<link rel="stylesheet" href="{root}wakeout.css">
<link rel="stylesheet" href="{root}static/site.css">
{extra_head}
</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{root}"><span class="brand-mark" aria-hidden="true"></span>HR Library</a>
    <nav class="site-nav" aria-label="Sections">{nav}</nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-foot">
  <div class="wrap">
    <p class="stamp">Checked 20 October 2026 · <a href="{root}downloads/">downloads</a> · <a href="{root}check/">link status</a></p>
    <p>No accounts, no cookies, nothing leaves your device. Free to read; text shared CC BY-SA 4.0.</p>
  </div>
</footer>
</body>
</html>
"""
    dest = SITE / path / "index.html" if path else SITE / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    return dest


def hero(title, lead, kicker=""):
    k = f'<p class="eyebrow">{kicker}</p>' if kicker else ""
    return f'<section class="hero">{k}<h1>{title}</h1><p class="lead">{lead}</p>{hero_stamp()}</section>'


def hero_stamp():
    return (f'<p class="stamp"><span class="stamp-dot" aria-hidden="true"></span>'
            f'{STAMP}</p>')


def sticker(verdict):
    return f'<span class="sticker sticker-{verdict}">{VERDICTS[verdict]}</span>'


# ---------------------------------------------------------------- pages
# R6: "Document 2" becomes "the Plan" with a link; the archive filename becomes a
# download link. Nothing else in the overview copy is touched.
HOME_REWRITES = [
    ("Then open Document 2 and do the Week 0 row.",
     "Then open [the Plan](/2/plan/) and do the Week 0 row."),
    ("Live in Document 2.", "Live in [the Plan](/2/plan/)."),
    ("`HR_Roadmap_Library`", "[`HR_Roadmap_Library`](/files/HR_Roadmap_Library.docx)"),
]
HOME_LINKS = [
    ("<strong>Document 1 — Start Here.</strong>",
     '<strong><a href="/1/start-here/">Document 1 — Start Here.</a></strong>'),
    ("<strong>Document 2 — The 24-Week Plan.</strong>",
     '<strong><a href="/2/plan/">Document 2 — The 24-Week Plan.</a></strong>'),
    ("<strong>Document 3 — The Resource Library.</strong>",
     '<strong><a href="/3/library/">Document 3 — The Resource Library.</a></strong>'),
    ("<strong>Document 4 — Nigeria: Labour Law &amp; CIPM.</strong>",
     '<strong><a href="/4/nigeria/">Document 4 — Nigeria: Labour Law &amp; CIPM.</a></strong>'),
    ("<strong>Document 5 — Getting the Job.</strong>",
     '<strong><a href="/5/getting-the-job/">Document 5 — Getting the Job.</a></strong>'),
]


def build_home():
    src = (CONTENT / "HR_Library_Overview.md").read_text(encoding="utf-8")
    for old, new in HOME_REWRITES:
        assert old in src, f"home rewrite no longer matches: {old[:40]}"
        src = src.replace(old, new)
    blocks_ = R.parse(src)
    intro = next((b for b in blocks_ if b["t"] == "p"), None)
    rest = [b for b in blocks_ if b is not intro and not (b["t"] == "h" and b["l"] == 1)]
    rendered = render_blocks(rest, level=2)
    for old, new in HOME_LINKS:
        rendered = rendered.replace(old, new)
    body = [hero(md("Your HR Library"), md(intro["text"]) if intro else "", "The compass"),
            rendered]
    page("", "Your HR Library", "\n".join(body), lead=plain(intro["text"]) if intro else "")


def build_doc(name, path, title, lead="", kicker=""):
    bs = blocks(name)
    body = [hero(md(title), md(lead) if lead else "", kicker)]
    if kicker:
        body.append(stamp_block())
    body.append(render_blocks(bs, level=2))
    page(path, plain(title), "\n".join(body), lead=plain(lead))


def stamp_block():
    return (f'<p class="stamp stamp-block"><span class="stamp-dot" aria-hidden="true"></span>'
            f"{STAMP}</p>")


def build_plan():
    weeks = week_sections()
    bs = blocks("doc2")
    head = next((b for b in bs if b["t"] == "h" and b["l"] == 3), None)
    body = [hero("The 24-week plan", md(head["text"]) if head else "", "Document 2")]
    rows = "".join(
        f'<li><a href="/2/plan/week/{w["n"]}/"><span class="week-n">{w["n"]:02d}</span>'
        f'<span>{md(w["title"])}</span></a></li>' for w in weeks)
    body.append(f'<section class="card"><h2 id="weeks">The weeks</h2>'
                f'<p class="note">Each week is a table of blocks. If the week\'s output exists, '
                f'the week counts as passed.</p><ol class="week-list">{rows}</ol></section>')
    if weeks:
        last = weeks[-1]["n"]
        body.append(f'<aside class="callout"><p><strong>Weeks {last + 1}–24 are in '
                    f'<a href="/5/getting-the-job/">Getting the job</a>.</strong> Document 2 hands '
                    f'those three weeks to Document 5 in one paragraph, so they are not week pages '
                    f'here. The reading is still complete — it just lives in the other document.</p></aside>')
    t = tracker()
    for label, table in (("Courses and credentials", t["courses"]),
                         ("Portfolio artefacts", t["artefacts"])):
        if table:
            body.append(f'<section><h2 id="tracker-{label.lower().replace(" ", "-")}">'
                        f'Tracker · {label}</h2>{render_table(table, caption=label)}</section>')
    page("2/plan", "The 24-week plan", "\n".join(body),
         lead="Twenty-four weeks at five to ten hours a week, everything free.")


def build_week(w):
    body = [f'<p class="eyebrow"><a href="/2/plan/">The plan</a> · Week {w["n"]}</p>',
            f'<h1>Week {w["n"]} · {md(w["title"])}</h1>', stamp_block()]
    available = {x["n"] for x in week_sections()}
    prev_w = w["n"] - 1 if w["n"] > 0 else None
    links = []
    if prev_w is not None and prev_w in available:
        links.append(f'<a href="/2/plan/week/{prev_w}/">← Week {prev_w}</a>')
    nxt = w["n"] + 1
    if nxt in available:
        links.append(f'<a href="/2/plan/week/{nxt}/">Week {nxt} →</a>')
    else:
        links.append('<a href="/5/getting-the-job/">Weeks 22–24 →</a>')
    body.append(f'<nav class="pager" aria-label="Weeks">{"".join(links)}</nav>')
    body.append(render_blocks(w["blocks"], level=2,
                              default_caption=f"Week {w['n']} — {w['title']}"))
    page(f"2/plan/week/{w['n']}", f"Week {w['n']} · {w['title']}", "\n".join(body))


def build_library_index():
    cs = cards()
    items = []
    for c in cs:
        v = verdict_of(c["fields"].get("cost", ""))
        items.append(
            f'<li class="card res-card"><a href="/3/library/{c["id"]}/">'
            f'<h3>{md(c["raw_title"])}</h3></a>{sticker(v)}'
            f'<p class="note">{md(c["fields"].get("why it matters") or c["fields"].get("why") or "")}</p>'
            f'</li>')
    body = [hero("The resource library", f"{len(cs)} resources, each with the link, "
                f"what it really costs, and how long it takes.", "Document 3"),
            f'<ul class="grid grid-3 res-grid">{"".join(items)}</ul>']
    page("3/library", "The resource library", "\n".join(body),
         lead="Every course worth your time, with the link, the real cost and the hours.")


def build_card(c):
    v = verdict_of(c["fields"].get("cost", ""))
    body = [f'<p class="eyebrow"><a href="/3/library/">Library</a> · resource</p>',
            f'<h1>{md(c["raw_title"])}</h1>{sticker(v)}', stamp_block()]
    if c["fields"].get("cost"):
        body.append(f'<p class="cost-line">{md(c["fields"]["cost"])}</p>')
    for label in ("what it is", "why it matters", "time", "level", "courses", "links",
                  "link", "do this with it"):
        if c["fields"].get(label):
            body.append(f'<section class="field"><h2>{label.capitalize()}</h2>'
                        f'<p>{md(c["fields"][label])}</p></section>')
    body.append(render_blocks(c["blocks"], level=2, default_caption=c["title"]))
    page(f"3/library/{c['id']}", c["title"], "\n".join(body), lead=c["title"])


def build_law_card():
    _, body = section("doc4", r"SUPPORT C")
    inner = render_blocks(body, level=2)
    page("4/nigeria/law-card", "The one-page law card",
         '<p class="eyebrow"><a href="/4/nigeria/">Nigeria &amp; law</a> · one page</p>'
         '<h1>Your one-page law card</h1>' + stamp_block() + inner,
         lead="Every section you must be able to state, on one page.", body_class="law-card")


def build_templates():
    """R5: doc5's copyable blocks on one page, no prose between them.

    Three blocks exist as copy in the source: the 90-word note (5.5), the
    weak/strong CV bullets (5.3) and the follow-up messages (SUPPORT C). All
    three re-render the same parsed markdown, so this is a second *rendering*
    of one source, not a second copy of the copy (R1).

    R5 also names a 12-question intake template and a reference-check script.
    Neither exists as copy anywhere in the five documents: doc2 lists them as
    artefacts the learner writes in Weeks 13 and 12. Emitting them would mean
    inventing content, which R1 and the no-new-content rule forbid. Flagged in
    STATUS.md for the owner to write, or to drop from R5.

    The Copy button itself is roadmap step 2.4 and is not built yet.
    """
    _, apply_bs = section("doc5", r"5\.5 THE APPLICATION")
    note = [b for b in apply_bs if b["t"] == "quote"]
    _, cv_bs = section("doc5", r"5\.3 THE CV")
    bullets = [b for b in cv_bs if b["t"] == "table" and b["head"][:1] == ["Weak"]]
    _, follow = section("doc5", r"SUPPORT C")

    body = ['<p class="eyebrow"><a href="/5/getting-the-job/">Getting the job</a>'
            ' · copyable</p>', '<h1>Templates to copy</h1>', stamp_block()]
    if note:
        body.append('<h2 id="note-90-word">The 90-word note</h2>')
        body.append(render_blocks(note, level=3))
    if bullets:
        body.append('<h2 id="cv-bullets">CV bullets</h2>')
        # Caption is the table's own column names, so it does not echo the
        # heading above it; R26 still gets its <caption>.
        body.append(render_blocks(bullets, level=3, ns="tpl-cv",
                                  caption_from_heading=False,
                                  default_caption="Weak and strong"))
    body.append('<h2 id="follow-up">Follow-up messages</h2>')
    body.append(render_blocks(follow, level=3, ns="tpl-follow"))

    page("5/templates", "Templates to copy", "\n".join(body),
         lead="The 90-word note, the CV bullet rewrites and the follow-up "
              "messages, kept in one place.")


def build_downloads():
    files = sorted((ROOT / "downloads").glob("HR_*"))
    rows = "".join(
        f'<tr><td><a href="/files/{f.name}" download>{f.name}</a></td>'
        f'<td class="num">{f.stat().st_size:,} B</td>'
        f'<td class="num">{(f.stat().st_size / 1024):.0f} KB</td></tr>' for f in files)
    body = [hero("Downloads", "The five documents and the research archive, as files. "
                "Sizes are here so you can see what you are fetching before you pay for data.",
                "Free to download")]
    body.append(f'<div class="card table-card"><div class="scroller"><table>'
                f'<caption class="eyebrow">Files</caption>'
                f'<thead><tr><th scope="col">File</th><th scope="col">Bytes</th>'
                f'<th scope="col">Approx</th></tr></thead><tbody>{rows}</tbody></table></div></div>')
    page("downloads", "Downloads", "\n".join(body))


def build_check():
    urls = external_urls()
    rows = "".join(f'<tr><td class="url">{html.escape(u)}</td><td>not yet swept</td>'
                   f'<td>—</td></tr>' for u in urls)
    body = [hero("Link status", "Every external link in the five documents, with the date it was "
                "last checked.", "Documentation"),
            '<aside class="callout"><p><strong>No sweep recorded yet.</strong> All 47 links were '
            'checked on 20 October 2026 when the documents were written; the automated sweep that '
            'fills this page has not run. A link that has moved is a defect worth reporting.</p></aside>',
            f'<div class="card table-card"><div class="scroller"><table>'
            f'<caption class="eyebrow">{len(urls)} external links</caption>'
            f'<thead><tr><th scope="col">URL</th><th scope="col">Status</th>'
            f'<th scope="col">Checked</th></tr></thead><tbody>{rows}</tbody></table></div></div>']
    page("check", "Link status", "\n".join(body))


# ---------------------------------------------------------------- main
def copy_assets():
    SITE.mkdir(exist_ok=True)
    (SITE / "static").mkdir(parents=True, exist_ok=True)
    (SITE / "fonts").mkdir(exist_ok=True)
    src = ROOT / "design-system/artifacts/wakeout.css"
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};:,])\s*", r"\1", text).strip()
    (SITE / "wakeout.css").write_text(text, encoding="utf-8")
    shutil.copy2(ROOT / "site/static/site.css", SITE / "static/site.css")
    # The .woff2 files are SIL OFL 1.1, which requires the licence to travel
    # with them, so the two OFL texts ship beside the fonts they cover.
    for pat in ("*.woff2", "*.txt"):
        for f in (ROOT / "design-system/public/fonts").glob(pat):
            shutil.copy2(f, SITE / "fonts" / f.name)
    (SITE / "files").mkdir(exist_ok=True)
    for f in (ROOT / "downloads").glob("HR_*"):
        shutil.copy2(f, SITE / "files" / f.name)


def main(argv):
    copy_assets()
    build_home()
    build_doc("doc1", "1/start-here", "Start here",
              "The beginner's guide to learning HR from zero, for free.", "Document 1")
    build_plan()
    weeks = week_sections()
    for w in weeks:
        build_week(w)
    build_library_index()
    for c in cards():
        build_card(c)
    build_doc("doc4", "4/nigeria", "Nigeria: labour law & CIPM",
              "The law and the profession you will actually be hired into.", "Document 4")
    build_doc("doc5", "5/getting-the-job", "Getting the job",
              "Positioning, CV, LinkedIn, applications, interviews — weeks 22 to 24.", "Document 5")
    build_law_card()
    build_templates()
    build_downloads()
    build_check()
    pages = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("index.html"))
    print(f"built {len(pages)} routes; weeks={len(weeks)} cards={len(cards())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
