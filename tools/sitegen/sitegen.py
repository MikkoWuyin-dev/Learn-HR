#!/usr/bin/env python3
"""Build the HR Library site from content/docs/src/*.md into _site/.

One command:  python3 tools/sitegen/sitegen.py [--no-css]

Everything visible comes from the markdown (PRD R1: no content fork). The design
system owns every visual value (R20): this file emits class names and structure,
never a colour, size or shadow. Values live in site/static/site.css as var(--fn-*),
which design-system/tokens/fieldnotes.tokens.json compiles into fieldnotes.css.

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
  _site/style-guide/                   the Fieldnotes system, read live from the stylesheet
  _site/downloads/                     the seven files, with sizes
"""
import html
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile

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
    # The display face is a system monospace stack, and no such stack is
    # guaranteed to carry U+20A6. A bare ₦ inside a heading would fall back
    # mid-word, so the sign always renders in the reading face. Typography only
    # — the character and the copy are untouched.
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
    tick). Weeks 22-24 do carry block tables: doc2 gives them the sequence, doc5
    §5.3-§5.8 carries the detail behind each row.
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
    # Recorded rather than written out again: every page comes through here, so
    # this is where a share card learns the title it has to draw.
    if path.strip("/") in OG_ROUTES:
        _og_specs[path.strip("/")] = (title, lead)
    card = og_image_url(path)
    if card:
        meta += [f'<meta property="og:image" content="{html.escape(card, quote=True)}">',
                 f'<meta property="og:image:width" content="{OG_W}">',
                 f'<meta property="og:image:height" content="{OG_H}">',
                 f'<meta name="twitter:card" content="summary_large_image">']
    scripts = (f'<script src="{root}static/progress.js" defer></script>'
               f'\n<script src="{root}static/offline.js" defer></script>')
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
<link rel="stylesheet" href="{root}fieldnotes.css">
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
    <p class="stamp">Checked 20 October 2026 · <a href="{root}downloads/">downloads</a> · <a href="{root}check/">link status</a> · <a href="{root}style-guide/">style guide</a></p>
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
    # The hero kicker is a chip, as in the reference: a yellow block with ink
    # text (14.00:1) rather than loose uppercase. Elsewhere .eyebrow stays a
    # plain label, so the chip reads as the hero's own.
    k = f'<p class="hero-eyebrow">{kicker}</p>' if kicker else ""
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
        links.append('<a href="/5/getting-the-job/">Getting the job →</a>')
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
                f"what it really costs, and what to make of it.", "Document 3"),
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


def write_service_worker(weeks):
    """Emit _site/sw.js carrying this build's cache name and R28's precache list.

    The cache name is a hash of everything else the build wrote, so any change to
    any page gives the next build a new name; the worker's activate step then
    deletes every cache that is not that one, which is what retires the old
    version. Nothing has to be told to invalidate anything by hand.

    R28 asks for the shell, the week pages, the glossary and the law card. There
    are no fonts to precache: Fieldnotes is a system-font family, so a cold
    install costs no webfont bytes at all.
    """
    import hashlib
    import json

    shell = ["/", "/1/start-here/", "/2/plan/", "/4/nigeria/law-card/",
             "/fieldnotes.css", "/static/site.css", "/static/progress.js",
             "/static/copy.js", "/static/glossary.js", "/static/library.js",
             "/static/offline.js"]
    precache = shell + [f"/2/plan/week/{w['n']}/" for w in weeks]
    missing = [u for u in precache if not (SITE / u.strip("/") / "index.html").exists()
               and not (SITE / u.lstrip("/")).is_file()]
    if missing:
        raise SystemExit(f"service worker would precache missing routes: {missing}")

    h = hashlib.sha256()
    for p in sorted(SITE.rglob("*")):
        # sw.js hashes itself, so it must stay out of its own digest.
        if p.is_file() and p.name != "sw.js":
            h.update(p.relative_to(SITE).as_posix().encode("utf-8"))
            h.update(p.read_bytes())
    src = (ROOT / "site/static/sw.js").read_text(encoding="utf-8")
    out = (src.replace("__CACHE__", "hrsite-" + h.hexdigest()[:12])
              .replace("__PRECACHE__", json.dumps(precache, separators=(",", ":"))))
    (SITE / "sw.js").write_text(squeeze_js(out), encoding="utf-8")
    return len(precache)


# ---------------------------------------------------------------- share cards
# One card per document, plus one for the home page. R28 asks for these to be
# generated from the site's own tokens with no photography and no AI imagery, so
# they are drawn: a frame, a colour chip, type. Nothing else.
OG_ROUTES = ("", "1/start-here", "2/plan", "3/library", "4/nigeria", "5/getting-the-job")
OG_W, OG_H = 1200, 630
OG_FOOTER = "Free to read \u00b7 No account \u00b7 Nothing leaves your device"
_og_specs = {}
# Decided before any page is written, because og:image is an absolute URL baked
# into the head and the extension has to be known up front.
_og_ext = "svg"


def _token(name, default):
    """One colour primitive from the Fieldnotes system, so a card cannot drift."""
    try:
        data = json.loads((ROOT / "design-system/tokens/fieldnotes.tokens.json").read_text(encoding="utf-8"))
        got = data["color"]["primitive"][name]["value"]
    except (OSError, ValueError, KeyError, TypeError):
        return default
    return got if isinstance(got, str) and got.startswith("#") else default


def _wrap(text, width, limit):
    """Greedy word wrap. SVG has no wrapping, so every line is placed by hand."""
    words, lines, cur, i = text.split(), [], "", 0
    while i < len(words):
        trial = (cur + " " + words[i]).strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = ""
            if len(lines) == limit:
                break
            continue
        cur = trial
        i += 1
    if cur and len(lines) < limit:
        lines.append(cur)
    if i < len(words) and lines:
        lines[-1] = lines[-1].rstrip() + "\u2026"
    return lines


def _og_svg(label, title, lead):
    ink = _token("ink", "#11142B")
    paper = _token("paper", "#FFF8E7")
    green = _token("green", "#5EE780")
    yellow = _token("yellow", "#FFE168")
    esc = html.escape
    # Fieldnotes ships no webfonts, so a card is drawn in the same system faces
    # the page uses. The monospace stack is what makes it look like family.
    stack = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

    title_lines = _wrap(title, 22, 3)
    # A three-line title leaves room for one line of lead, not two: the card is
    # a fixed 630px tall and the footer sticker is not going to move.
    lead_lines = _wrap(lead, 46, 2 if len(title_lines) < 3 else 1) if lead else []
    title_size, lead_size = 76, 34

    # The block is centred in the band between the header and the footer, so a
    # one-line title and a three-line title both look placed rather than top-heavy.
    line_h, lead_h, band_top, band_bottom = 86, 44, 150, 496
    block = len(title_lines) * line_h + (30 + len(lead_lines) * lead_h if lead_lines else 0)
    top = band_top + max(0, (band_bottom - band_top - block) // 2)
    title_y = [top + 62 + i * line_h for i in range(len(title_lines))]
    rule_y = top + len(title_lines) * line_h + 6
    lead_y = [rule_y + 52 + i * lead_h for i in range(len(lead_lines))]

    chip_w = 44 + len(label) * 19 if label else 0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{OG_W}" height="{OG_H}" '
           f'viewBox="0 0 {OG_W} {OG_H}" role="img" '
           f'aria-label="{esc(title)}">',
           f'<title>{esc(title)}</title>',
           f'<rect width="{OG_W}" height="{OG_H}" fill="{paper}"/>',
           f'<rect x="14" y="14" width="{OG_W - 28}" height="{OG_H - 28}" fill="none" '
           f'stroke="{ink}" stroke-width="14"/>',
           # brand mark, same geometry as the site's own
           f'<rect x="72" y="66" width="46" height="46" fill="{green}" stroke="{ink}" '
           f'stroke-width="6"/>',
           f'<text x="140" y="105" font-family="{stack}" font-size="38" font-weight="700" '
           f'fill="{ink}" letter-spacing="1.5">HR LIBRARY</text>']
    if label:
        out += [f'<rect x="{OG_W - 72 - chip_w}" y="62" width="{chip_w}" height="54" '
                f'fill="{ink}" stroke="{ink}" stroke-width="6"/>',
                f'<text x="{OG_W - 72 - chip_w // 2}" y="99" font-family="{stack}" '
                f'font-size="30" font-weight="700" fill="{paper}" '
                f'text-anchor="middle">{esc(label.upper())}</text>']
    for n, line in enumerate(title_lines):
        out.append(f'<text x="72" y="{title_y[n]}" font-family="{stack}" '
                   f'font-size="{title_size}" font-weight="800" fill="{ink}">{esc(line)}</text>')
    if lead_lines:
        out.append(f'<rect x="72" y="{rule_y}" width="150" height="10" fill="{green}"/>')
        for n, line in enumerate(lead_lines):
            out.append(f'<text x="72" y="{lead_y[n]}" font-family="{stack}" '
                       f'font-size="{lead_size}" fill="{ink}">{esc(line)}</text>')
    foot_w = 60 + len(OG_FOOTER) * 17
    out += [f'<rect x="72" y="{OG_H - 118}" width="{foot_w}" height="60" fill="{yellow}" '
            f'stroke="{ink}" stroke-width="6"/>',
            f'<text x="102" y="{OG_H - 76}" font-family="{stack}" font-size="28" '
            f'font-weight="600" fill="{ink}">{esc(OG_FOOTER)}</text>',
            '</svg>']
    return "\n".join(out) + "\n"


def _og_png(svg_path, png_path):
    """Rasterise with whatever is installed. Returns False if nothing can."""
    # Best first: rsvg-convert and inkscape are real SVG renderers. Browsers are
    # next, because nearly every desktop has one and headless screenshotting is
    # faithful. ImageMagick is last and its output is never trusted blindly - it
    # is often installed without an SVG delegate and can "succeed" on garbage.
    browsers = []
    for name in ("chromium", "google-chrome", "chrome", "microsoft-edge", "msedge"):
        found = shutil.which(name)
        if found:
            browsers.append([found, "--headless", "--disable-gpu", "--no-sandbox",
                             f"--screenshot={png_path}", f"--window-size={OG_W},{OG_H}",
                             f"--default-background-color=00000000", str(svg_path)])
            break
    for cmd in (
        ["rsvg-convert", "-w", str(OG_W), "-o", str(png_path), str(svg_path)],
        ["inkscape", "-w", str(OG_W), "-o", str(png_path), str(svg_path)],
        *browsers,
        ["convert", "-background", "none", "-density", "192", "-resize", str(OG_W),
         str(svg_path), str(png_path)],
    ):
        if not shutil.which(cmd[0]):
            continue
        try:
            subprocess.run(cmd, capture_output=True, timeout=120,
                           encoding="utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            continue
        # ImageMagick's built-in SVG renderer is poor and can "succeed" while
        # writing nothing usable, so the output is checked rather than trusted.
        if png_path.exists() and _valid_png(png_path):
            return True
    if png_path.exists():
        png_path.unlink()
    return False


def _og_probe():
    """'png' if a rasteriser can actually do it, else 'svg'."""
    probe = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{OG_W}" height="{OG_H}">'
             f'<rect width="{OG_W}" height="{OG_H}" fill="#fff"/></svg>')
    with tempfile.TemporaryDirectory() as tmp:
        svg = pathlib.Path(tmp) / "probe.svg"
        svg.write_text(probe, encoding="utf-8")
        return "png" if _og_png(svg, pathlib.Path(tmp) / "probe.png") else "svg"


def _valid_png(path, width=OG_W):
    try:
        raw = path.read_bytes()
        return raw[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">I", raw[16:20])[0] >= width
    except (OSError, struct.error):
        return False


def write_og_cards():
    """Draw and write the share cards. Returns (written, extension used).

    SVG is the source: it is small, crisp at any size and readable in a
    repository. PNG is what social platforms actually want - most reject SVG -
    so it is produced too wherever a rasteriser exists. Where none does, the
    build says so out loud instead of quietly shipping cards that will not
    appear when someone shares a page.
    """
    out_dir = SITE / "og"
    out_dir.mkdir(exist_ok=True)
    written = 0
    for route in OG_ROUTES:
        if route not in _og_specs:
            continue
        title, lead = _og_specs[route]
        label = "" if not route else "Document " + route.split("/")[0]
        slug = route.replace("/", "-") or "home"
        svg_path = out_dir / f"{slug}.svg"
        svg_path.write_text(_og_svg(label, title, lead), encoding="utf-8")
        written += 1
        if _og_ext == "png" and not _og_png(svg_path, out_dir / f"{slug}.png"):
            print(f"      no rasteriser produced {slug}.png; sharing {slug}.svg instead")
    return written


def og_image_url(path):
    """The absolute og:image for a route, or None when the origin is unknown."""
    key = path.strip("/")
    if not SITE_URL or key not in OG_ROUTES or key not in _og_specs:
        return None
    slug = key.replace("/", "-") or "home"
    card = f"og/{slug}.{_og_ext}"
    if _og_ext == "png" and not (SITE / card).exists():
        card = f"og/{slug}.svg"
    return f"{SITE_URL}/{card}"


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
    src = ROOT / "design-system/artifacts/fieldnotes.css"
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};:,])\s*", r"\1", text).strip()
    (SITE / "fieldnotes.css").write_text(text, encoding="utf-8")
    shutil.copy2(ROOT / "site/static/site.css", SITE / "static/site.css")
    for f in ("progress.js", "copy.js", "glossary.js", "library.js", "offline.js"):
        js = (ROOT / "site/static" / f).read_text(encoding="utf-8")
        (SITE / "static" / f).write_text(squeeze_js(js), encoding="utf-8")
    (SITE / "files").mkdir(exist_ok=True)
    for f in (ROOT / "downloads").glob("HR_*"):
        shutil.copy2(f, SITE / "files" / f.name)


# What the style guide shows, and in what order. The names are token names
# without the --fn- prefix, so a rename in the token file surfaces here as a
# missing swatch rather than as a silent gap.
SG_COLOUR_GROUPS = (
    ("Ground and ink", ("ink", "paper", "cream", "line", "muted", "shade")),
    ("Accent", ("blue", "blue-ink", "cyan", "pink", "yellow", "green", "orange")),
    ("Notice and control", ("well", "white")),
)
SG_STATUS = ("live", "archive", "caveat")
SG_TAGS = ("default", "playful", "pixel", "action", "mobile")
SG_TYPE = ("hero", "title", "headline", "lead", "subhead", "body", "body-sm",
           "small", "caption", "meta", "eyebrow")
SG_SPACE = ("1", "2", "2-5", "3", "4", "5", "6", "8", "10", "12", "16")
SG_BORDER = ("hairline", "thin", "base", "thick")
SG_SHADOW = ("sticker-sm", "sticker", "sticker-hover", "sticker-lg", "disabled", "ring")


def build_style_guide():
    """Render the Fieldnotes system from the compiled stylesheet.

    Every value on this page is read out of artifacts/fieldnotes.css at build
    time rather than written here, so a component and the token behind it
    cannot drift apart: change a token, rebuild, and the page changes with it.

    That is the whole reason for the route. A style guide that restates its
    own values is a second source of truth, and two sources of truth
    eventually disagree - which is how a design system decays into a
    description of what the system used to be.

    The one thing it cannot do is use inline styles, which the repo bans. A
    style guide is exactly the page that wants them - every swatch needs a
    different value - so the per-token classes it needs are generated into the
    page's head from the same token file. The rule stays absolute, and a class
    that appears here is by construction a token that exists.
    """
    from contrast import rgb as _rgb, ratio as _ratio

    css = (ROOT / "design-system/artifacts/fieldnotes.css").read_text(encoding="utf-8")
    tok = dict(re.findall(r"(--fn-[a-z0-9-]+):\s*([^;}]+);", css))

    def val(name):
        return tok.get("--fn-" + name, "").strip()

    def hexval(name):
        v = val(name)
        return v if v.startswith("#") else ""

    def ratio(a, b):
        ha, hb = hexval(a), hexval(b)
        if not ha or not hb:
            return None
        return _ratio(_rgb(ha)[0], _rgb(hb)[0])

    def verdict(r):
        if r is None:
            return ""
        if r >= 7:
            return "AAA"
        if r >= 4.5:
            return "AA"
        if r >= 3:
            return "large only"
        return "fails"

    def pairing(name):
        """How this colour is actually used, as a measured pair.

        Measuring every colour against ink alone would report that ink fails
        against ink, which is true and useless. A dark colour is something that
        sits *on* a ground; a light colour is a ground that ink sits on. So
        take the pair with the more separation and name which one it is - the
        reader always sees the number that describes real use.
        """
        on_ink, on_paper = ratio(name, "ink"), ratio(name, "paper")
        if on_ink is None or on_paper is None:
            return ""
        if on_ink >= on_paper:
            return f"ink {on_ink:.2f}:1 · {verdict(on_ink)}"
        return f"{on_paper:.2f}:1 on paper · {verdict(on_paper)}"

    esc = html.escape

    # ------------------------------------------------------------ the classes
    # Collected as we go, then emitted once. A token named here and missing
    # from the token file produces a rule pointing at nothing, which the
    # contrast table on the page would then show as an empty ratio.
    rules = []

    def bg(name):
        rules.append(f".sg-bg-{name}{{background:var(--fn-{name})}}")
        return f"sg-bg-{name}"

    def fg(name):
        rules.append(f".sg-fg-{name}{{color:var(--fn-{name})}}")
        return f"sg-fg-{name}"

    def bw(name):
        rules.append(f".sg-bw-{name}{{border-width:var(--fn-border-{name})}}")
        return f"sg-bw-{name}"

    def sh(name):
        rules.append(f".sg-sh-{name}{{box-shadow:var(--fn-shadow-{name})}}")
        return f"sg-sh-{name}"

    def fs(name):
        rules.append(f".sg-fs-{name}{{font-size:var(--fn-text-{name})}}")
        return f"sg-fs-{name}"

    def w(name):
        rules.append(f".sg-w-{name}{{width:var(--fn-space-{name})}}")
        return f"sg-w-{name}"

    def face(kind):
        rules.append(f".sg-ff-{kind}{{font-family:var(--fn-font-{kind})}}")
        return f"sg-ff-{kind}"

    # ---------------------------------------------------------------- colour
    body = [hero("Style guide",
                 "Every colour, size, space and component in the Fieldnotes system, "
                 "read live from the stylesheet this site ships.",
                 "Fieldnotes")]

    body.append("<h2>Colour</h2>")
    body.append('<p class="lead">Each swatch shows the token, its value, and what '
                'ink text measures against it. The ratio is computed at build time '
                'with the same maths as the gate\'s contrast check, so a colour that '
                'stops being safe says so here rather than passing quietly.</p>')

    for group_name, names in SG_COLOUR_GROUPS:
        cells = []
        for n in names:
            if not hexval(n):
                continue
            cells.append(f'<div class="sg-swatch {bg(n)}">'
                         f'<code>--fn-{esc(n)}</code>'
                         f'<span class="sg-swatch-val">{esc(hexval(n))}</span>'
                         f'<span class="sg-swatch-c">{esc(pairing(n))}</span>'
                         f'</div>')
        body.append(f'<div class="card"><h3>{esc(group_name)}</h3>'
                    f'<div class="sg-grid">{"".join(cells)}</div></div>')

    cells = []
    for s in SG_STATUS:
        pair, pair_ink = f"status-{s}-bg", f"status-{s}-ink"
        r = ratio(pair_ink, pair)
        cells.append(f'<div class="sg-swatch {bg(pair)} {fg(pair_ink)}">'
                     f'<code>--fn-{esc(s)}</code>'
                     f'<span class="sg-swatch-val">{esc(hexval(pair))}</span>'
                     f'<span class="sg-swatch-c">{r:.2f}:1 · {verdict(r)}</span>'
                     f'</div>')
    body.append('<div class="card"><h3>Status pairs</h3>'
                '<p>Each status is a background and an ink together, so a status never '
                'needs a rule about the colour of its own text.</p>'
                f'<div class="sg-grid">{"".join(cells)}</div></div>')

    cells = []
    for t in SG_TAGS:
        cells.append(f'<div class="sg-swatch {bg("tag-" + t)}">'
                     f'<code>--fn-tag-{esc(t)}</code>'
                     f'<span class="sg-swatch-val">{esc(hexval("tag-" + t))}</span>'
                     f'<span class="sg-swatch-c">{esc(pairing("tag-" + t))}</span>'
                     f'</div>')
    body.append('<div class="card"><h3>Tag colours</h3>'
                '<p>Colour carries meaning, so every tag also carries a word. '
                'Nothing here is signalled by hue alone.</p>'
                f'<div class="sg-grid">{"".join(cells)}</div></div>')

    # ------------------------------------------------------------------ type
    body.append("<h2>Type</h2>")
    body.append('<p class="lead">The chrome face is monospace: headings, labels, '
                'buttons, stamps and table heads. Running copy opts into the reading '
                'face, because a monospace paragraph is harder work than a monospace '
                'label. Each size below is shown in the face that would use it.</p>')
    rows = []
    for t in SG_TYPE:
        rows.append(f'<tr><td><code>--fn-text-{esc(t)}</code></td>'
                    f'<td class="num">{esc(val("text-" + t))}</td>'
                    f'<td><span class="{face("mono")} {fs(t)}">Week 24 · HR</span></td>'
                    f'<td><span class="{face("prose")} {fs(t)}">Read the whole clause '
                    f'before you rely on it.</span></td></tr>')
    body.append('<div class="card table-card"><div class="scroller"><table>'
                '<caption class="eyebrow">The type scale, in both faces</caption>'
                '<thead><tr><th scope="col">Token</th><th scope="col">Value</th>'
                '<th scope="col">Chrome face</th><th scope="col">Reading face</th>'
                f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>')

    # ---------------------------------------------------------------- spacing
    body.append("<h2>Spacing</h2>")
    body.append('<p class="lead">Fluid throughout, so spacing is continuous rather '
                'than stepped. Each step is a clamp with a floor, a viewport middle '
                'and a ceiling; the bar shows the step at its ceiling.</p>')
    rows = []
    for s in SG_SPACE:
        rows.append(f'<tr><td><code>--fn-space-{esc(s)}</code></td>'
                    f'<td class="num">{esc(val("space-" + s))}</td>'
                    f'<td><span class="sg-bar {w(s)}"></span></td></tr>')
    body.append('<div class="card table-card"><div class="scroller"><table>'
                '<caption class="eyebrow">The spacing scale</caption>'
                '<thead><tr><th scope="col">Token</th><th scope="col">Value</th>'
                f'<th scope="col">At its ceiling</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div></div>')

    # ------------------------------------------------- borders, corners, shadow
    body.append("<h2>Borders, corners and shadow</h2>")
    rows = []
    for b in SG_BORDER:
        rows.append(f'<tr><td><code>--fn-border-{esc(b)}</code></td>'
                    f'<td class="num">{esc(val("border-" + b))}</td>'
                    f'<td><span class="sg-box {bw(b)}"></span></td></tr>')
    body.append('<div class="card table-card"><div class="scroller"><table>'
                '<caption class="eyebrow">Border widths</caption>'
                '<thead><tr><th scope="col">Token</th><th scope="col">Value</th>'
                f'<th scope="col">Rendered</th></tr></thead>'
                f'<tbody>{"".join(rows)}</tbody></table></div></div>')

    cells = []
    for s in SG_SHADOW:
        cells.append(f'<div class="sg-shadow-cell">'
                     f'<span class="sg-box sg-shadow {sh(s)}"></span>'
                     f'<code>--fn-shadow-{esc(s)}</code>'
                     f'<span class="sg-swatch-val">{esc(val("shadow-" + s))}</span>'
                     f'</div>')
    body.append('<div class="card"><h3>Shadow</h3>'
                '<p>Hard offsets with no blur. Cards rest at six pixels and lift '
                'into a ten pixel pink shadow on hover, which is the one gesture '
                'that makes the system feel physical.</p>'
                f'<div class="sg-grid">{"".join(cells)}</div></div>')

    body.append('<div class="card"><h3>Corners</h3>'
                '<p>Square. The reference stylesheet contains exactly one '
                'border-radius in 27,771 characters, and this system keeps it to the '
                'smallest controls.</p><div class="sg-grid">'
                f'<div class="sg-swatch"><code>--fn-radius-none</code>'
                f'<span class="sg-swatch-val">{esc(val("radius-none"))}</span></div>'
                f'<div class="sg-swatch"><code>--fn-radius-sm</code>'
                f'<span class="sg-swatch-val">{esc(val("radius-sm"))}</span></div>'
                '</div></div>')

    # ---------------------------------------------------------------- pieces
    body.append("<h2>Components</h2>")
    body.append('<p class="lead">The pieces the site is built from, rendered with the '
                'classes the pages actually use rather than with copies of their '
                'styles. Change a token and these change with it.</p>')

    body.append('<div class="card"><h3>Hero and eyebrow</h3>'
                '<p class="hero-eyebrow">Document 1</p>'
                '<p>The eyebrow is a chip, not loose uppercase: yellow with ink text, '
                'at fourteen to one.</p></div>')

    body.append('<div class="card"><h3>Stickers</h3>'
                '<p>One class, six grounds. Each carries its own background, and the '
                'gate measures the text on every one of them.</p>'
                '<p><span class="sticker sticker-free-to-finish">Free to finish</span> '
                '<span class="sticker sticker-free-to-use">Free to use</span> '
                '<span class="sticker sticker-limited-access">Limited access</span> '
                '<span class="sticker sticker-paid">Paid</span> '
                '<span class="sticker sticker-check-before-committing">Check first</span> '
                '<span class="sticker sticker-free-to-study-paid-cert">Free to study'
                '</span></p></div>')

    body.append('<div class="card"><h3>Buttons</h3>'
                '<p>Every control is at least three rem tall for a thumb.</p>'
                '<p class="actions">'
                '<button type="button" class="btn btn-primary">Start with Week 0</button> '
                '<button type="button" class="btn btn-paper">See the whole plan</button> '
                '<button type="button" class="btn btn-ink">Reset</button> '
                '<button type="button" class="btn btn-sm">Copy</button></p></div>')

    body.append('<div class="card"><h3>Hover</h3>'
                '<p>Hover a card and it rises toward you as its shadow deepens and '
                'turns pink: three pixels of lift, four of shadow, in just over a '
                'tenth of a second. Anyone who asks for less motion gets none.</p>'
                '<div class="grid grid-3">'
                '<div class="card"><h4>A card at rest</h4>'
                '<p>Six pixels of hard shadow, square corners.</p></div>'
                '<div class="card"><h4>Hover this one</h4>'
                '<p>The lift and the pink shadow are the system\'s signature.</p></div>'
                '<div class="card"><h4>And this one</h4>'
                '<p>Both are the same component; nothing is special-cased.</p></div>'
                '</div></div>')

    body.append('<div class="card"><h3>Progress</h3>'
                '<p>A two pixel box with a white track and a blue fill. No rounding.</p>'
                '<div class="meter"><progress value="9" max="25"></progress></div>'
                '<p class="note">9 of 25 weeks</p></div>')

    body.append('<div class="card"><h3>Status chips</h3>'
                '<p>Background and ink travel together, so a chip never needs a rule '
                'about its own text.</p>'
                f'<p><span class="sticker {bg("status-live-bg")} {fg("status-live-ink")}">'
                f'live</span> '
                f'<span class="sticker {bg("status-archive-bg")} {fg("status-archive-ink")}">'
                f'archive</span> '
                f'<span class="sticker {bg("status-caveat-bg")} {fg("status-caveat-ink")}">'
                f'caveat</span></p></div>')

    body.append('<div class="callout"><h3>Callout</h3>'
                '<p>The soft blue notice tint is one token, shared by callouts, table '
                'heads, code blocks and the current row. Ink on it measures just under '
                'fifteen to one.</p></div>')

    body.append('<div class="card table-card"><h3>Table</h3>'
                '<div class="scroller"><table>'
                '<caption class="eyebrow">A table with its caption</caption>'
                '<thead><tr><th scope="col">Week</th><th scope="col">Focus</th>'
                '<th scope="col" class="num">Hours</th></tr></thead><tbody>'
                '<tr><td>0</td><td>Set up</td><td class="num">2</td></tr>'
                '<tr class="is-next"><td>1</td><td>What HR is</td><td class="num">5</td></tr>'
                '<tr class="is-done"><td>2</td><td>The function</td><td class="num">5</td></tr>'
                '</tbody></table></div></div>')

    body.append('<div class="card"><h3>Stamp</h3>'
                '<p>Every content page carries one. It is the family\'s promise that a '
                'fact has a date on it.</p>'
                f'<p class="stamp"><span class="stamp-dot" aria-hidden="true"></span>'
                f'{STAMP}</p></div>')

    body.append('<div class="card"><h3>Motion</h3>'
                '<p>Motion is confirmation, not decoration: it tells you a card is '
                'interactive or that a bar moved. Nothing animates on load, and the '
                'durations come from the tokens rather than from habit.</p>'
                '<div class="scroller"><table>'
                '<caption class="eyebrow">Durations and easing</caption>'
                '<thead><tr><th scope="col">Token</th><th scope="col">Value</th>'
                '<th scope="col">Used for</th></tr></thead><tbody>'
                f'<tr><td><code>--fn-duration-quick</code></td>'
                f'<td class="num">{esc(val("duration-quick"))}</td>'
                f'<td>transform, box-shadow, background</td></tr>'
                f'<tr><td><code>--fn-duration-bar</code></td>'
                f'<td class="num">{esc(val("duration-bar"))}</td>'
                f'<td>the progress fill</td></tr>'
                f'<tr><td><code>--fn-ease-out</code></td>'
                f'<td class="num">{esc(val("ease-out"))}</td><td>everything</td></tr>'
                '</tbody></table></div></div>')

    body.append('<div class="card"><h3>Focus</h3>'
                '<p>A three pixel blue ring at two pixels offset, never removed. Tab to '
                'any control on this page to see it. Controls that already sit on a '
                'coloured ground take a yellow fill as well, so the ring is never lost '
                'against what is behind it.</p>'
                '<p class="actions"><button type="button" class="btn btn-paper">'
                'Tab to me</button></p></div>')

    # Only now is the class list complete, so only now can it be emitted.
    seen, sheet = set(), []
    for rule in rules:
        if rule not in seen:
            seen.add(rule)
            sheet.append(rule)
    extra_head = "<style>" + "".join(sheet) + "</style>"

    page("style-guide", "Style guide", "\n".join(body),
         lead="Every colour, size, space and component in the Fieldnotes system, "
              "read live from the stylesheet this site ships.",
         extra_head=extra_head)


def main(argv):
    global SITE_URL, _og_ext
    import os
    url = os.environ.get("HR_SITE_URL", "")
    for arg in argv:
        if arg.startswith("--site-url="):
            url = arg.split("=", 1)[1]
    SITE_URL = url.rstrip("/")
    # Probe once, before any page is written: og:image is baked into the head
    # and cannot be patched afterwards. The test draws a real card rather than
    # asking whether a binary exists, because ImageMagick is often installed
    # without a working SVG delegate and would promise PNGs it cannot make.
    _og_ext = _og_probe()
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
    build_style_guide()
    write_crawl_files()
    precached = write_service_worker(weeks)
    og = write_og_cards()
    pages = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("index.html"))
    print(f"built {len(pages)} routes; weeks={len(weeks)} cards={len(cards())} "
          f"precached={precached} og={og} ({_og_ext})")
    if _og_ext == "svg":
        print("NOTE  share cards are SVG only - no rasteriser (rsvg-convert, inkscape "
              "or ImageMagick) was found. Most social platforms reject SVG, so cards "
              "will not appear when a page is shared until PNGs are made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
