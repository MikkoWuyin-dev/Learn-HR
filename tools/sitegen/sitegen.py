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
# R7: legal pages say this beside the stamp. Interface wording fixed by the PRD.
LEGAL_NOTE = "Not legal advice; current to the date checked."

NAV = [
    ("/1/start-here/", "Start here"),
    ("/2/plan/", "The plan"),
    ("/3/library/", "Library"),
    ("/4/nigeria/", "Nigeria & law"),
    ("/5/getting-the-job/", "Getting the job"),
]

# A bare URL wrapped in parentheses, e.g. "(https://search.cac.gov.ng/)" in
# doc5's scam checklist. The shared renderer's URL_RE carries a (?<!\()
# lookbehind, so these would render as plain, unclickable text. The site
# layer linkifies them instead, leaving docx_render.py — and therefore the
# frozen .docx baseline — untouched. The (?<!\]) guard keeps it off a
# markdown link's own "(url)". Used by md() and by link_sources().
PAREN_URL_RE = re.compile(r"(?<!\])\((https?://[^\s)]+)\)")

VERDICTS = {
    "free-to-finish": "Free to finish",
    "free-to-study-paid-cert": "Free to study · paid certificate",
    "limited-access": "Limited access",
    "check-before-committing": "Check before committing",
    "free-to-use": "Free to use",     # not a course: boards, statutes, reference shelves
    "paid": "Paid",
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
    return plain_text(b["text"])


def plain_text(s):
    """Markdown inline -> plain text: links to their label, emphasis and code marks
    dropped. Used for copy payloads, the path manifest and meta descriptions, where
    a stray `**` would be visible to the reader. Words are never changed."""
    s = R.clean_text(s)
    s = re.sub(r"\[([^\]]+)\]\((/[^)\s]*)\)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"\1", s)
    return s.strip()


def summary(s, limit=158):
    """Shorten plain text to a meta-description length at a word boundary."""
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0].rstrip(",;:·—-")
    return cut + "…"


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
        title = re.sub(r"^Week\s+%d\s*[·—-]\s*" % n, "", title, flags=re.I)
        out.append({"n": n, "title": title.strip(), "heading": heading_text(b),
                    "id": b["id"], "blocks": body})
    return out


def cards():
    """doc3: one `####` heading per resource, with its bullet fields and the `##`
    section it sits under (3.1 the spine, 3.2 bodies and institutions, 3.3 jobs)."""
    bs = blocks("doc3")
    out = []
    section = None
    for i, b in enumerate(bs):
        if b["t"] == "h" and b["l"] == 2:
            m = re.match(r"(\d+\.\d+)\s+(.*)", heading_text(b))
            section = {"key": m.group(1), "title": m.group(2), "id": b["id"]} if m else None
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
                    "fields": fields, "blocks": body, "section": section})
    return out


def card_text(c):
    """Everything a card says, as plain text, for checking a verdict's basis."""
    parts = [c["title"]]
    for b in c["blocks"]:
        if b["t"] in ("p", "quote"):
            parts.append(b["text"])
        elif b["t"] == "list":
            parts += [i["text"] for i in b["items"]]
        elif b["t"] == "table":
            parts += [" ".join(r) for r in b["rows"]]
    return " ".join(plain_text(x) for x in parts)


COURSE_CARDS_FILE = CONTENT / "course-cards.json"
_course_cards = {}


def course_cards():
    """Card id -> [(tracker key, course name)], from content/course-cards.json (R10).

    The tracker row keys are reused, so a tick on a card and a tick in the plan's
    tracker are one tick. A row number the tracker doesn't have, an unknown card,
    or wording the card no longer says is a build error.
    """
    if _course_cards:
        return _course_cards
    courses = tracker()["courses"]
    by_num = {row[0].strip(): (k, plain_text(row[1])) for k, row in zip(courses["keys"], courses["rows"])}
    by_id = {c["id"]: c for c in cards()}
    data = json.loads(COURSE_CARDS_FILE.read_text(encoding="utf-8"))["courses"]
    problems, out = [], {}
    for num, where in data.items():
        if num not in by_num:
            problems.append(f"#{num}: no such row in the doc2 tracker")
            continue
        for cid, basis in where.items():
            if cid not in by_id:
                problems.append(f"#{num}: no such card {cid}")
            elif plain_text(basis) not in card_text(by_id[cid]):
                problems.append(f"#{num}: {cid} no longer says {basis!r}")
            else:
                out.setdefault(cid, []).append(by_num[num])
    if problems:
        raise SystemExit("course-cards.json needs the owner:\n  " + "\n  ".join(problems))
    _course_cards.update(out)
    return _course_cards


VERDICTS_FILE = CONTENT / "resource-verdicts.json"
_verdicts = {}


def verdicts():
    """The owner's cost verdict per card, from content/resource-verdicts.json.

    A wrong card id, an unknown verdict, or a basis the card no longer says is a
    build error: the sticker must rest on words the learner can read on the card.
    A card with no entry gets no sticker, never a guess.
    """
    if _verdicts:
        return _verdicts
    data = json.loads(VERDICTS_FILE.read_text(encoding="utf-8"))["cards"]
    by_id = {c["id"]: c for c in cards()}
    problems = []
    for cid, v in data.items():
        if cid not in by_id:
            problems.append(f"{cid}: no such card in doc3")
        elif v.get("verdict") not in VERDICTS:
            problems.append(f"{cid}: unknown verdict {v.get('verdict')!r}")
        elif not v.get("basis") or plain_text(v["basis"]) not in card_text(by_id[cid]):
            problems.append(f"{cid}: basis no longer on the card: {v.get('basis')!r}")
    if problems:
        raise SystemExit("resource-verdicts.json needs the owner:\n  " + "\n  ".join(problems))
    _verdicts.update({cid: v["verdict"] for cid, v in data.items()})
    return _verdicts


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


BLOCK_HEAD = ["time", "do this", "output"]


def learning_path():
    """The ordered list of things a learner ticks, derived from doc2 and nothing else.

    Doc 2: "Each block ends with an output. If you produced the output, the week
    passes." So a week's activities are the rows of its block table (Time · Do this ·
    Output), keyed by the row's data-k. Weeks 20 and 21 have no block table; their
    outputs are the Support A artefacts dated to that week, so those tracker rows are
    the week's activities (same key as the tracker, so a tick in either place is one
    tick). Weeks 22-24 have no activities here: doc2 hands them to doc5.
    """
    art = tracker()["artefacts"]
    dated = {}
    if art:
        wcol = [h.lower() for h in art["head"]].index("week")
        for k, row in zip(art["keys"], art["rows"]):
            if row[wcol].strip().isdigit():
                dated.setdefault(int(row[wcol]), []).append((k, row))
    out = []
    for w in week_sections():
        acts, source = [], "blocks"
        for b in w["blocks"]:
            if b["t"] == "table" and [h.lower() for h in b["head"]] == BLOCK_HEAD:
                acts += [{"k": k, "time": plain_text(r[0]), "do": plain_text(r[1]),
                          "out": plain_text(r[2])} for k, r in zip(b["keys"], b["rows"])]
        if not acts:
            source = "tracker"
            acts = [{"k": k, "time": "", "do": plain_text(r[1]), "out": plain_text(r[1])}
                    for k, r in dated.get(w["n"], [])]
        out.append({"n": w["n"], "title": plain_text(w["title"]), "source": source,
                    "url": f"/2/plan/week/{w['n']}/", "acts": acts})

    return out


_manifests = {}


def path_manifest(detail=False):
    """The JSON the browser needs to derive progress. Keys and week titles only,
    unless `detail`, which adds each activity's words for the next-action card."""
    if detail in _manifests:
        return _manifests[detail]
    t = tracker()
    weeks = []
    for w in learning_path():
        entry = [w["n"], w["title"], [a["k"] for a in w["acts"]]]
        if detail:
            entry.append([[a["time"], a["do"], a["out"]] for a in w["acts"]])
        weeks.append(entry)
    data = {"v": 1, "weeks": weeks,
            "courses": t["courses"]["keys"] if t["courses"] else [],
            "artefacts": t["artefacts"]["keys"] if t["artefacts"] else []}
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # Safe inside <script type="application/json">: no element can be closed early.
    _manifests[detail] = text.replace("</", "<\\/")
    return _manifests[detail]


def external_urls():
    """Every external URL in the five documents, first-seen order (see link_sources)."""
    return list(link_sources())


# ---------------------------------------------------------------- rendering
def tick_button(key, label, context):
    """A progress toggle. Hidden in the HTML; progress.js reveals it, so a page read
    without JavaScript shows no control that does nothing (R12, R25)."""
    return (f'<button type="button" class="tick" data-tick="{key}" aria-pressed="false" hidden>'
            f'{label}<span class="vh"> · {html.escape(context)}</span></button>')


def render_table(b, caption=None, tick_col=None, tick_label="Done", ns=None):
    """`ns` renames the row keys, for a table rendered a second time elsewhere.

    parse() mints each table's data-k once, so rendering one table on two pages
    would emit the same key twice. That fails the site-wide uniqueness check,
    and on a tickable table it would make one click tick two rows (R9). Use it
    only for duplicates that are not themselves progress rows.
    """
    head = "".join(f'<th scope="col">{md(c)}</th>' for c in b["head"])
    rows = []
    for i, row in enumerate(b["rows"]):
        key = b["keys"][i] if i < len(b.get("keys", [])) else ""
        if key and ns:
            key = f"{ns}-{key}"
        cells = []
        for j in range(len(b["head"])):
            cell = md(row[j] if j < len(row) else "")
            if tick_col == j and key:
                context = plain_text(row[2] if tick_col == 2 else row[1]) if len(row) > 2 else key
                cell = f'<span class="cell-text">{cell}</span>{tick_button(key, tick_label, context)}'
            cells.append(f"<td>{cell}</td>")
        rid = f' id="{key}"' if tick_col is not None and key else ""
        rows.append(f'<tr{rid} data-k="{key}">{"".join(cells)}</tr>')
    cap = f'<caption class="table-caption">{md(caption)}</caption>' if caption else ""
    return (f'<div class="card table-card"><div class="scroller"><table>{cap}'
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>")


def copy_button(payload, what):
    """A Copy control for a block the learner reuses. The payload is the source's
    own words as plain text, line breaks kept; copy.js reveals the button."""
    return (f'<button type="button" class="btn btn-sm copy-btn" hidden '
            f'data-copy="{html.escape(payload, quote=True)}">Copy<span class="vh"> {what}</span></button>'
            f'<span class="copy-status" role="status"></span>')


def render_quote(b, copyable):
    if not copyable:
        return f'<aside class="callout"><p>{md(b["text"])}</p></aside>'
    lines = b.get("lines") or [b["text"]]
    payload = "\n".join(plain_text(x) for x in lines)
    return (f'<figure class="copyable"><blockquote><p>{"<br>".join(md(x) for x in lines)}</p>'
            f'</blockquote>{copy_button(payload, "this text")}</figure>')


GLOSSARY_SEARCH = (
    '<div class="glossary-search" data-glossary hidden><label for="glossary-q">Search the terms</label>'
    '<input id="glossary-q" type="search" autocomplete="off" spellcheck="false">'
    '<p class="note" data-glossary-count aria-live="polite"></p></div>')


def render_blocks(bs, level=2, caption_from_heading=True, default_caption="",
                  copyable=False, ticks=False, glossary=False, ns=None):
    """`copyable`: blockquotes are reusable scripts and templates (docs 4 and 5), so
    they get a Copy button; elsewhere they are callouts. `ticks`: block tables get a
    progress toggle in their Output cell. `ns`: rename the row keys, for a table
    that is rendered a second time on another page (see render_table)."""
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
            out.append(render_quote(b, copyable))
        elif t == "code":
            pre = "<pre><code>" + html.escape("\n".join(b["lines"])) + "</code></pre>"
            if copyable:
                pre = (f'<figure class="copyable">{pre}'
                       f'{copy_button(chr(10).join(b["lines"]), "this card")}</figure>')
            out.append(pre)
        elif t == "list":
            tag = "ol" if b["items"][0]["ordered"] else "ul"
            items = "".join(
                f'<li class="{"sub" if it["ind"] >= 2 else ""}">{md(it["text"])}</li>'
                for it in b["items"])
            out.append(f"<{tag}>{items}</{tag}>")
        elif t == "table":
            tick = 2 if ticks and [h.lower() for h in b["head"]] == BLOCK_HEAD else None
            caption = (current if caption_from_heading else default_caption) or None
            table = render_table(b, caption=caption, tick_col=tick,
                                 tick_label="Output done", ns=ns)
            if glossary and b["head"][0].strip().lower() == "term":
                # R8: the search box ships hidden; glossary.js reveals it and filters rows.
                table = GLOSSARY_SEARCH + table.replace('<div class="card table-card">',
                                                        '<div class="card table-card" data-glossary-table>', 1)
            out.append(table)
    return "\n".join(out)


def full_title(title):
    """The site name is appended only while the title stays within 70 characters, the
    length search results show. A long source heading is never cut short."""
    suffixed = f"{title} — HR Library"
    return suffixed if len(suffixed) <= 70 else title


SITE_URL = ""          # production origin, e.g. https://example.org — set by --site-url
WRITTEN = []           # (path, title) of every page, for the sitemap and the audit


def page(path, title, body, *, lead="", extra_head="", body_class="", detail=False):
    """Write one page. `path` is the directory under _site, '' for the root.

    Every page carries the path manifest (keys and week titles) so the footer can say
    where the learner stopped; `detail` adds the activity words for the next-action
    card. Scripts are deferred and optional: with JavaScript off, the page reads the
    same minus the progress and copy controls.
    """
    depth = 0 if not path else path.strip("/").count("/") + 1
    root = "../" * depth
    # The aria-current attribute is built outside the f-string: an escaped quote
    # inside an f-string expression is a SyntaxError before Python 3.12 (PEP 701),
    # and this build has to run on 3.11.
    nav = []
    for href, esc in ((h, html.escape(label)) for h, label in NAV):
        here = (' aria-current="page"'
                if path and href != "/" and path.startswith(href.strip("/"))
                else "")
        nav.append(f'<a href="{root}{href.strip("/")}/"{here}>{esc}</a>')
    nav = "".join(nav)
    stamp = (f'<p class="stamp"><span class="stamp-dot" aria-hidden="true"></span>'
             f'{STAMP} · <a href="{root}check/">see every link checked</a></p>')
    url_path = f"/{path.strip('/')}/" if path else "/"
    desc = html.escape(summary(lead), quote=True)
    meta = [f'<meta name="description" content="{desc}">',
            f'<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="HR Library">',
            f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
            f'<meta property="og:description" content="{desc}">']
    if SITE_URL:
        meta += [f'<link rel="canonical" href="{SITE_URL}{url_path}">',
                 f'<meta property="og:url" content="{SITE_URL}{url_path}">']
    scripts = f'<script src="{root}static/progress.js" defer></script>'
    if "copy-btn" in body:
        scripts += f'\n<script src="{root}static/copy.js" defer></script>'
    if "data-lib-filter" in body:
        scripts += f'\n<script src="{root}static/library.js" defer></script>'
    if "data-glossary" in body:
        scripts += f'\n<script src="{root}static/glossary.js" defer></script>'
    doc = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title(title))}</title>
{chr(10).join(meta)}
<link rel="icon" href="data:,">
<link rel="stylesheet" href="{root}wakeout.css">
<link rel="stylesheet" href="{root}static/site.css">
{extra_head}
{scripts}
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
    <p class="resume" data-resume hidden></p>
    <p class="stamp">Checked 20 October 2026 · <a href="{root}downloads/">downloads</a> · <a href="{root}check/">link status</a></p>
    <p>No accounts, no cookies, nothing leaves your device. Free to read; text shared CC BY-SA 4.0.</p>
    <p class="vh" id="hr-live" aria-live="polite"></p>
  </div>
</footer>
<script type="application/json" id="hr-path">{path_manifest(detail)}</script>
</body>
</html>
"""
    dest = SITE / path / "index.html" if path else SITE / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    WRITTEN.append((url_path, title))
    return dest


def hero(title, lead, kicker="", actions=""):
    k = f'<p class="eyebrow">{kicker}</p>' if kicker else ""
    return (f'<section class="hero">{k}<h1>{title}</h1><p class="lead">{lead}</p>{actions}'
            f'{hero_stamp()}</section>')


def hero_stamp():
    return (f'<p class="stamp"><span class="stamp-dot" aria-hidden="true"></span>'
            f'{STAMP}</p>')


def sticker(verdict):
    if not verdict:
        return ""
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
    body = [hero(md("Your HR Library"), md(intro["text"]) if intro else "", "The compass",
                 actions=start_actions()),
            NEXT_CARD, rendered]
    page("", "Your HR Library", "\n".join(body),
         lead=plain_text(intro["text"]) if intro else "", detail=True)


# Filled by progress.js from the path manifest; empty and hidden on a first visit (R11).
NEXT_CARD = ('<section class="card next-card" data-next hidden aria-labelledby="next-h">'
             '<h2 id="next-h">Your next block</h2><div data-next-body></div></section>')


def start_actions():
    """The primary action. Doc 2 starts at Week 0, and the overview says "do the Week 0
    row"; progress.js turns this into a Resume link once the learner has ticked anything."""
    return ('<p class="actions"><a class="btn btn-primary" data-start href="/2/plan/week/0/">'
            'Start with Week 0</a> <a class="btn btn-paper" href="/2/plan/">See the whole plan</a></p>')


def build_doc(name, path, title, lead="", kicker="", copyable=False, seo_title=None,
              legal=False, glossary=False):
    bs = blocks(name)
    body = [hero(md(title), md(lead) if lead else "", kicker)]
    if kicker:
        body.append(stamp_block(legal))
    body.append(render_blocks(bs, level=2, copyable=copyable, glossary=glossary))
    # The meta description is the document's own first paragraph (R17), which says
    # what the page answers better than the one-line subtitle does.
    first_p = next((b["text"] for b in bs if b["t"] == "p" and not re.match(r"\*[^*]", b["text"])), lead)
    page(path, seo_title or plain(title), "\n".join(body), lead=plain_text(first_p))


def stamp_block(legal=False):
    note = f'<p class="legal-note">{LEGAL_NOTE}</p>' if legal else ""
    return (f'<p class="stamp stamp-block"><span class="stamp-dot" aria-hidden="true"></span>'
            f"{STAMP}</p>{note}")


# Filled by progress.js; hidden on a first visit so nobody sees "0% complete" (R11).
PROGRESS_PANEL = (
    '<section class="card progress-card" data-progress hidden aria-labelledby="progress-h">'
    '<h2 id="progress-h">Your progress</h2><div data-progress-body></div>'
    '<p class="note">Saved in this browser on this device only. It does not follow you to '
    'another phone or browser, and clearing your browser data clears it.</p>'
    '<div class="reset" data-reset><button type="button" class="btn btn-sm btn-paper" '
    'data-reset-ask>Clear my progress</button>'
    '<span data-reset-confirm hidden> Clear every tick on this device? '
    '<button type="button" class="btn btn-sm btn-ink" data-reset-yes>Yes, clear it</button> '
    '<button type="button" class="btn btn-sm btn-paper" data-reset-no>Keep it</button></span>'
    '</div></section>')


def build_plan():
    weeks = week_sections()
    bs = blocks("doc2")
    head = next((b for b in bs if b["t"] == "h" and b["l"] == 3), None)
    body = [hero("The 24-week plan", md(head["text"]) if head else "", "Document 2",
                 actions=start_actions().replace(
                     ' <a class="btn btn-paper" href="/2/plan/">See the whole plan</a>', '')),
            NEXT_CARD, PROGRESS_PANEL]
    rows = "".join(
        f'<li data-week="{w["n"]}"><a href="/2/plan/week/{w["n"]}/"><span class="week-n">{w["n"]:02d}</span>'
        f'<span>{md(w["title"])}</span><span class="week-state" data-week-state="{w["n"]}"></span>'
        f'</a></li>' for w in weeks)
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
            col = [h.lower() for h in table["head"]]
            tick = col.index("status") if "status" in col else col.index("done") if "done" in col else None
            body.append(f'<section><h2 id="tracker-{label.lower().replace(" ", "-")}">'
                        f'Tracker · {label}</h2>{render_table(table, caption=label, tick_col=tick)}</section>')
    page("2/plan", "The 24-week plan: from zero to job-ready in HR", "\n".join(body),
         lead=plain_text(head["text"]) if head else "", detail=True)


def build_week(w):
    path_week = next((x for x in learning_path() if x["n"] == w["n"]), None)
    body = [f'<p class="eyebrow"><a href="/2/plan/">The plan</a> · Week {w["n"]}</p>',
            f'<h1>Week {w["n"]} · {md(w["title"])}</h1>', stamp_block(),
            f'<p class="week-progress" data-week-progress="{w["n"]}" hidden></p>']
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
    pager = f'<nav class="pager" aria-label="Weeks">{"".join(links)}</nav>'
    body.append(pager)
    body.append(render_blocks(w["blocks"], level=2, ticks=True,
                              default_caption=f"Week {w['n']} — {w['title']}"))
    if path_week and path_week["source"] == "tracker" and path_week["acts"]:
        # No block table this week: its outputs are the Support A rows dated to it.
        items = "".join(f'<li id="{a["k"]}"><span class="cell-text">{html.escape(a["out"])}</span> '
                        f'{tick_button(a["k"], "Output done", a["out"])}</li>'
                        for a in path_week["acts"])
        body.append(f'<section class="card"><h2 id="this-weeks-output">This week\'s output</h2>'
                    f'<p class="note">From the plan\'s progress tracker (Support A). Tick only when '
                    f'the output exists.</p><ul class="tick-list">{items}</ul></section>')
    body.append(pager.replace('aria-label="Weeks"', 'aria-label="Weeks, again"'))
    first = path_week["acts"][0]["do"] if path_week and path_week["acts"] else ""
    lead = f"Week {w['n']} of the free 24-week HR plan: {plain_text(w['title'])}. {first}"
    page(f"2/plan/week/{w['n']}", f"Week {w['n']} · {plain_text(w['title'])}", "\n".join(body),
         lead=lead)


LIBRARY_FILTER = (
    '<div class="lib-filter" data-lib-filter hidden role="group" aria-label="Filter the library">'
    '<label>Section <select name="section">{sections}</select></label>'
    '<label>Cost <select name="cost">{costs}</select></label>'
    '<p class="note" data-lib-count aria-live="polite"></p></div>')


def build_library_index():
    cs = cards()
    vs = verdicts()
    groups, order = {}, []
    for c in cs:
        sec = c["section"] or {"key": "", "title": "", "id": ""}
        if sec["key"] not in groups:
            groups[sec["key"]] = (sec, [])
            order.append(sec["key"])
        v = vs.get(c["id"], "")
        groups[sec["key"]][1].append(
            f'<li class="card res-card" data-section="{sec["key"]}" data-cost="{v}">'
            f'<a href="/3/library/{c["id"]}/"><h3>{md(c["raw_title"])}</h3></a>{sticker(v)}'
            f'<p class="note">{md(c["fields"].get("why it matters") or c["fields"].get("why") or "")}</p>'
            f'</li>')
    sections = '<option value="">All sections</option>' + "".join(
        f'<option value="{k}">{html.escape(groups[k][0]["title"].capitalize())}</option>' for k in order if k)
    used = [k for k in VERDICTS if k in set(vs.values())]
    costs = '<option value="">Any cost</option>' + "".join(
        f'<option value="{k}">{VERDICTS[k]}</option>' for k in used)
    body = [hero("The resource library", f"{len(cs)} resources, each with the link, "
                f"what it really costs, and how long it takes.", "Document 3"),
            LIBRARY_FILTER.format(sections=sections, costs=costs)]
    for k in order:
        sec, items = groups[k]
        head = f'<h2 id="{sec["id"]}">{html.escape(k + " " + sec["title"])}</h2>' if k else ""
        body.append(f'<section class="lib-section" data-lib-section="{k}">{head}'
                    f'<ul class="grid grid-3 res-grid">{"".join(items)}</ul></section>')
    body.append('<p class="note">Each cost label sums up the card\'s own cost terms. '
                'Open the card for the full terms before you plan a week around it.</p>')
    sub = next((b["text"] for b in blocks("doc3") if b["t"] == "h" and b["l"] == 3), "")
    page("3/library", "Free HR courses and professional resources", "\n".join(body),
         lead=plain_text(sub) or "Every course worth your time, with the link, the real cost and the hours.")


def build_card(c):
    v = verdicts().get(c["id"], "")
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
    tracked = course_cards().get(c["id"], [])
    if tracked:
        items = "".join(f'<li id="{k}"><span class="cell-text">{html.escape(name)}</span> '
                        f'{tick_button(k, "Done", name)}</li>' for k, name in tracked)
        body.append(f'<section class="card" aria-labelledby="card-courses"><h2 id="card-courses">'
                    f'On your tracker</h2><p class="note">From the plan\'s progress tracker (Support A). '
                    f'A tick here is the same tick as in <a href="/2/plan/#tracker-courses-and-credentials">'
                    f'the plan</a>.</p><ul class="tick-list">{items}</ul></section>')
    what = c["fields"].get("what it is") or c["fields"].get("why it matters") or ""
    page(f"3/library/{c['id']}", c["title"], "\n".join(body),
         lead=f"{c['title']}: {plain_text(what)}" if what else c["title"])


def build_law_card():
    _, body = section("doc4", r"SUPPORT C")
    inner = render_blocks(body, level=2, copyable=True)
    page("4/nigeria/law-card", "The one-page law card",
         '<p class="eyebrow"><a href="/4/nigeria/">Nigeria &amp; law</a> · one page</p>'
         '<h1>Your one-page law card</h1>' + stamp_block(legal=True) + inner,
         lead="Every section you must be able to state, on one page.", body_class="law-card")


def build_templates():
    """R5: doc5's copyable blocks on one page, no prose between them.

    Three blocks exist as copy in the source: the 90-word note (5.5), the
    weak/strong CV bullets (5.3) and the follow-up messages (SUPPORT C). All
    three re-render the same parsed markdown, so this is a second *rendering*
    of one source, not a second copy of the copy (R1).

    R5 originally also named a 12-question intake template and a
    reference-check script. The owner dropped both on 2026-10-21: neither
    exists as copy in any document - doc2 lists them as artefacts the learner
    writes, in Weeks 13 and 12 - and they already render on those week pages
    and in the tracker. See the amendment note under R5 in the PRD.
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
        body.append(render_blocks(note, level=3, copyable=True))
    if bullets:
        body.append('<h2 id="cv-bullets">CV bullets</h2>')
        # Caption is the table's own column names, so it does not echo the
        # heading above it; R26 still gets its <caption>.
        body.append(render_blocks(bullets, level=3, ns="tpl-cv",
                                  caption_from_heading=False,
                                  default_caption="Weak and strong"))
    body.append('<h2 id="follow-up">Follow-up messages</h2>')
    body.append(render_blocks(follow, level=3, ns="tpl-follow", copyable=True))

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
    page("downloads", "Downloads", "\n".join(body),
         lead="The five documents and the research archive, as files, with their sizes.")


CHECKS_FILE = ROOT / "checks" / "links.json"

OUTCOME_LABELS = {
    "ok": "Reachable",
    "redirected": "Reachable after a redirect",
    "failed": "Failed",
    "inconclusive": "Inconclusive",
}


def page_for(name, heading_ids, week_n, card_id):
    """The site route (with anchor) where a source block is shown."""
    if name == "doc2" and week_n is not None:
        return f"/2/plan/week/{week_n}/"
    if name == "doc3" and card_id:
        return f"/3/library/{card_id}/"
    base = {"doc1": "/1/start-here/", "doc2": "/2/plan/", "doc3": "/3/library/",
            "doc4": "/4/nigeria/", "doc5": "/5/getting-the-job/"}[name]
    return base + (f"#{heading_ids[-1]}" if heading_ids and name not in ("doc3",) else "")


def link_sources():
    """Every external URL in the five documents, in first-seen order, with where
    each one appears: document, section heading and the site route that shows it."""
    weeks = {w["id"]: w["n"] for w in week_sections()}
    out = {}
    for name in DOCS:
        heads, week_n, card_id, head_text = [], None, None, ""
        for b in blocks(name):
            if b["t"] == "h":
                heads = [b["id"]]
                head_text = heading_text(b)
                if name == "doc2" and b["l"] <= 3:
                    week_n = weeks.get(b["id"])
                if name == "doc3":
                    card_id = b["id"] if b["l"] == 4 else (None if b["l"] < 4 else card_id)
            texts = []
            if b["t"] in ("p", "quote", "h"):
                texts.append(b["text"])
            elif b["t"] == "list":
                texts += [i["text"] for i in b["items"]]
            elif b["t"] == "table":
                texts += b["head"] + [c for row in b["rows"] for c in row]
            elif b["t"] == "code":
                texts += b["lines"]
            for t in texts:
                # Markdown links first, then bare URLs in what is left — the same two
                # passes the renderer uses, so this list matches the links on the site.
                found = [m.group(2) for m in R.LINK_RE.finditer(t)]
                rest = R.LINK_RE.sub("", t)
                found += [m.group(1) for m in R.URL_RE.finditer(rest)]
                # "(https://…)" in prose: the renderer leaves it as text, but the
                # learner still relies on it, so it is checked too.
                found += [m.group(1) for m in PAREN_URL_RE.finditer(rest)]
                for url in found:
                    src = {"doc": name, "file": DOCS[name], "section": head_text,
                           "page": page_for(name, heads, week_n, card_id)}
                    entry = out.setdefault(url, [])
                    if src not in entry:
                        entry.append(src)
    return out


def load_sweep():
    """The last recorded link sweep, or None. Never invented: the page shows what
    tools/sitegen/linkcheck.py wrote, or says plainly that no sweep has run."""
    if not CHECKS_FILE.exists():
        return None
    try:
        data = json.loads(CHECKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data.get("links"), list) else None
    except (ValueError, AttributeError):
        return None


def build_check():
    sources = link_sources()
    sweep = load_sweep()
    by_url = {r["url"]: r for r in (sweep or {}).get("links", [])}
    rows = []
    for url, where in sources.items():
        places = " ".join(f'<a href="{w["page"]}">{html.escape(w["section"] or w["doc"])}</a>'
                          for w in where[:3])
        r = by_url.get(url)
        if r:
            label = OUTCOME_LABELS.get(r.get("outcome"), "Inconclusive")
            detail = f' ({r["status"]})' if r.get("status") else (
                f' ({html.escape(r["error"])})' if r.get("error") else "")
            if r.get("outcome") == "redirected" and r.get("final_url"):
                detail += f'<br><span class="note">now at {html.escape(r["final_url"])}</span>'
            prev = r.get("previous") or {}
            prev_txt = OUTCOME_LABELS.get(prev.get("outcome"), "—") if prev else "—"
            checked = html.escape((r.get("checked_at") or "")[:10]) or "—"
            state = f'<span class="status status-{r.get("outcome", "inconclusive")}">{label}</span>{detail}'
        else:
            state, prev_txt, checked = "Not yet checked", "—", "—"
        rows.append(f'<tr><td class="url">{html.escape(url)}</td><td>{places}</td>'
                    f'<td>{state}</td><td>{checked}</td><td>{prev_txt}</td></tr>')
    if sweep:
        run = sweep.get("run", {})
        counts = {}
        for r in sweep["links"]:
            counts[r.get("outcome", "inconclusive")] = counts.get(r.get("outcome", "inconclusive"), 0) + 1
        tally = " · ".join(f"{OUTCOME_LABELS.get(k, k)}: {v}" for k, v in sorted(counts.items()))
        intro = (f'<aside class="callout"><p><strong>Last sweep: {html.escape(run.get("finished", "")[:10])}.</strong> '
                 f'{tally}. "Inconclusive" means the site refused or slowed an automated check '
                 f'(403, 429, a timeout, a network error); it does not mean the page is gone. '
                 f'A reachable link only proves the page answered, not that the course or its '
                 f'terms are unchanged.</p></aside>')
    else:
        intro = (f'<aside class="callout"><p><strong>No sweep recorded yet.</strong> All {len(sources)} '
                 f'links were checked on 20 October 2026 when the documents were written; the '
                 f'automated sweep that fills this page has not run. A link that has moved is a '
                 f'defect worth reporting.</p></aside>')
    body = [hero("Link status", "Every external link in the five documents, where it appears, "
                 "and what the last check found.", "Documentation"),
            intro,
            f'<div class="card table-card"><div class="scroller"><table>'
            f'<caption class="eyebrow">{len(sources)} external links</caption>'
            f'<thead><tr><th scope="col">URL</th><th scope="col">Appears in</th>'
            f'<th scope="col">Last result</th><th scope="col">Checked</th>'
            f'<th scope="col">Previous</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>']
    page("check", "Link status", "\n".join(body),
         lead="Every external link in the five documents, where it appears, and what the last check found.")


def write_crawl_files():
    """robots.txt always; sitemap.xml only when the production origin is known,
    because a sitemap must list absolute URLs and the domain is still undecided (D4)."""
    lines = ["User-agent: *", "Allow: /"]
    if SITE_URL:
        lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
        urls = "".join(f"<url><loc>{html.escape(SITE_URL + u)}</loc><lastmod>{LAST_VERIFIED}</lastmod></url>"
                       for u, _ in sorted(set(WRITTEN)))
        (SITE / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n',
            encoding="utf-8")
    (SITE / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- main
WORD = re.compile(r"[A-Za-z0-9_$]")


def squeeze_js(src):
    """Shrink the site's JS to fit R24's 10 KB without a minifier dependency.

    Comments go. Outside string literals, a run of spaces is dropped unless it sits
    between two word characters (`var a`, `return x`). A line break is kept unless
    it follows ; { or , so automatic semicolon insertion means what it meant.
    The sources contain no regex literals or template strings; a `//` or `/*` left
    outside a string after comment removal is a build error, not a guess.
    """
    src = re.sub(r"(?m)^\s*//.*$", "", src)
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("/*", i):
            i = src.index("*/", i) + 2
        elif src.startswith("//", i):
            raise ValueError(f"inline // comment at offset {i}: keep comments on their own line")
        elif c.isspace():
            j = i
            while j < n and src[j].isspace():
                j += 1
            run = src[i:j]
            prev = out[-1][-1:] if out else ""
            nxt = src[j:j + 1]
            if "\n" in run:
                # After ; { or , the next line can only start a new statement or item,
                # so the break carries no meaning. Elsewhere (after } especially) it stays.
                if out and prev not in "\n;{,":
                    out.append("\n")
            elif prev and nxt and WORD.match(prev) and WORD.match(nxt):
                out.append(" ")
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out).strip() + "\n"


def clean_site():
    """Delete any earlier build, so a page that stops being generated cannot survive.

    The build writes files but never removes them, so a deleted route keeps its old
    index.html and would still be counted, served and deployed — a deleted resource
    card can stay live after the content that produced it is gone.

    _site/ is generated output: never edited, never committed, so clearing it costs
    nothing. The guards are narrow on purpose, because the tests reassign S.SITE to
    a temporary directory: this must refuse anything that could take the repository
    with it, and never touch a relative or filesystem-root path.
    """
    if not SITE.is_absolute():
        raise SystemExit(f"refusing to clear {SITE!r}: not an absolute path")
    # Dangerous only when SITE is the repo or holds it. SITE being *inside* the
    # repo (ROOT in SITE.parents) is the normal case and must be allowed.
    if SITE == SITE.parent or SITE == ROOT or SITE in ROOT.parents:
        raise SystemExit(f"refusing to clear {SITE!r}: it is, or contains, the repository")
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)


def copy_assets():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "static").mkdir(parents=True, exist_ok=True)
    (SITE / "fonts").mkdir(exist_ok=True)
    src = ROOT / "design-system/artifacts/wakeout.css"
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};:,])\s*", r"\1", text).strip()
    (SITE / "wakeout.css").write_text(text, encoding="utf-8")
    shutil.copy2(ROOT / "site/static/site.css", SITE / "static/site.css")
    for f in ("progress.js", "copy.js", "glossary.js", "library.js"):
        js = (ROOT / "site/static" / f).read_text(encoding="utf-8")
        (SITE / "static" / f).write_text(squeeze_js(js), encoding="utf-8")
    # The .woff2 files are SIL OFL 1.1, which requires the licence to travel
    # with them, so the two OFL texts ship beside the fonts they cover.
    for f in (ROOT / "design-system/public/fonts").glob("*"):
        if f.suffix in (".woff2", ".txt"):
            shutil.copy2(f, SITE / "fonts" / f.name)
    (SITE / "files").mkdir(exist_ok=True)
    for f in (ROOT / "downloads").glob("HR_*"):
        shutil.copy2(f, SITE / "files" / f.name)


def main(argv):
    global SITE_URL
    import os
    url = os.environ.get("HR_SITE_URL", "")
    for arg in argv:
        if arg.startswith("--site-url="):
            url = arg.split("=", 1)[1]
    SITE_URL = url.rstrip("/")
    if SITE_URL and not re.match(r"^https://[^/\s]+$", SITE_URL):
        print(f"--site-url must be an https origin with no path, got {SITE_URL!r}")
        return 2
    WRITTEN.clear()
    clean_site()
    copy_assets()
    build_home()
    build_doc("doc1", "1/start-here", "Start here",
              "The beginner's guide to learning HR from zero, for free.", "Document 1", glossary=True)
    build_plan()
    weeks = week_sections()
    for w in weeks:
        build_week(w)
    build_library_index()
    for c in cards():
        build_card(c)
    build_doc("doc4", "4/nigeria", "Nigeria: labour law & CIPM",
              "The law and the profession you will actually be hired into.", "Document 4",
              copyable=True, legal=True,
              seo_title="Nigerian Labour Act & CIPM: the provisions you must be able to state")
    build_doc("doc5", "5/getting-the-job", "Getting the job",
              "Positioning, CV, LinkedIn, applications, interviews — weeks 22 to 24.", "Document 5",
              copyable=True)
    build_law_card()
    build_templates()
    build_downloads()
    build_check()
    write_crawl_files()
    pages = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("index.html"))
    print(f"built {len(pages)} routes; weeks={len(weeks)} cards={len(cards())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
