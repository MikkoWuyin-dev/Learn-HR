#!/usr/bin/env python3
"""Markdown -> themed .docx and self-contained .html for a learning library.

Supported markdown subset: #..#### headings, pipe tables, - / 1. lists,
> callout quotes, ```code```, --- rules, **bold**, *italic*, [text](url) links,
and [SHORTKEY] tags (stripped from the output, useful for cross-referencing).

Public API:  parse(md) -> blocks ; build_docx(blocks, path, title=, subtitle=,
             skip_first_h1=, hero_meta=) ; build_html(blocks, path) ;
             slug(text) ; subst(text, values)

Blocks carry three extra fields the site build needs; the .docx path ignores them,
so the Word output stays byte-comparable:

  heading  "id"     stable anchor, unique in the document, deduped with -2, -3 …
                    A `#### Title 【KEY】` heading becomes id="card-key".
  table    "keys"   one `data-k` per row: "<table>-r<n>", n counting from 1
                    within that table. <table> is the enclosing heading's key —
                    "w13" when the heading says "Week 13", otherwise its slug —
                    plus the slug of a bold label directly above the table when
                    one is there ("support-a-courses-and-credentials"), so adding
                    a row never moves another row's key and a saved tick is not
                    orphaned (PRD R9). A repeat table in one section gets "-t2".
  any      "vars"   the {{names}} found in the block, for subst() to fill.


Titles: override TITLE/SUBTITLE/META by passing them to the builders, or set
LIB_TITLE / LIB_SUBTITLE / LIB_META in the environment for a standalone run:
    python3 docx_render.py <part1.md> <part2.md> ... -o out_dir --name My_Library
"""
import re, html, json, os, pathlib, sys

TITLE = os.environ.get("LIB_TITLE", "My Learning Library")
SUBTITLE = os.environ.get("LIB_SUBTITLE", "A free, self-paced path from zero to job-ready")
META = os.environ.get("LIB_META", "Compiled today · verify every free tier on its enrolment page")

KEY_RE = re.compile(r"\s*【[^】]*】")
KEY_TAG_RE = re.compile(r"【([^】]+)】")
VAR_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
WEEK_RE = re.compile(r"\bweek\s+(\d+)\b", re.I)
BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*[.:]?$")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITAL_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
URL_RE = re.compile(r"(?<!\()\b(https?://[^\s|)<>]+)")


def clean_text(s):
    s = KEY_RE.sub("", s)
    s = LINK_RE.sub(lambda m: m.group(1), s)
    return s.strip()


def slug(text):
    """Stable anchor from heading text: lowercase, non-alphanumerics to '-', max 60."""
    s = re.sub(r"[^a-z0-9]+", "-", clean_text(text).lower()).strip("-")
    return s[:60] or "sec"


def subst(text, values):
    """Fill {{name}} from a mapping; an unknown name is left visible, never blanked."""
    return VAR_RE.sub(lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0), text)


def vars_in(text):
    return sorted(set(VAR_RE.findall(text)))


def week_key(text):
    """'Week 13 · …' -> 'w13'. None when the heading is not a week."""
    m = WEEK_RE.search(clean_text(text))
    return f"w{m.group(1)}" if m else None


def bold_label(text):
    """'**Courses and credentials**' -> 'courses-and-credentials', else None.

    A table's bold lead-in is a better identity than its position: rows can be
    added without moving the keys of a table further down the same section.
    """
    m = BOLD_ONLY_RE.match(text.strip())
    if not m:
        return None
    return slug(m.group(1))[:24].rstrip("-") or None


def inline(s):
    """-> list of (text, {'b':bool,'i':bool,'a':url}) runs, for docx."""
    s = KEY_RE.sub("", s)
    runs = []

    def push(txt, style):
        if not txt:
            return
        if runs and runs[-1][1] == style:
            runs[-1] = (runs[-1][0] + txt, style)
        else:
            runs.append([txt, style])

    pos = 0
    for m in LINK_RE.finditer(s):
        push(s[pos:m.start()], {})
        push(m.group(1), {"a": m.group(2)})
        pos = m.end()
    push(s[pos:], {})
    # second pass: promote any remaining bare URLs into links
    expanded = []
    for txt, st in runs:
        if "a" in st or not txt:
            expanded.append((txt, st)); continue
        pos = 0
        for m in URL_RE.finditer(txt):
            expanded.append((txt[pos:m.start()], st))
            expanded.append((m.group(1), {**st, "a": m.group(1)}))
            pos = m.end()
        if pos < len(txt):
            expanded.append((txt[pos:], st))
    runs = [list(x) for x in expanded]
    out = []
    for txt, st in runs:
        i = 0
        while i < len(txt):
            mb = BOLD_RE.match(txt, i)
            mi = ITAL_RE.match(txt, i) if not mb else None
            if mb:
                st2 = dict(st); st2["b"] = True
                out.append((mb.group(1), st2)); i = mb.end()
            elif mi:
                st2 = dict(st); st2["i"] = True
                out.append((mi.group(1), st2)); i = mi.end()
            else:
                nxt = len(txt)
                for pat in (BOLD_RE, ITAL_RE):
                    m2 = pat.search(txt, i)
                    if m2 and m2.start() < nxt:
                        nxt = m2.start()
                out.append((txt[i:nxt], st)); i = nxt
    return [(t, s2) for t, s2 in out if t]


def inline_html(s):
    s = html.escape(KEY_RE.sub("", s), quote=False)
    # Anchors are parked behind placeholders while bare URLs are linkified.
    # Without this, the URL inside href="…" is matched again and the anchor is
    # nested inside its own href (a dead link that still looks like markup).
    anchors = []

    def park(m):
        anchors.append(f'<a href="{m.group(2)}">{m.group(1)}</a>')
        return f"\x00{len(anchors) - 1}\x00"

    s = LINK_RE.sub(park, s)
    s = URL_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', s)
    s = BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = ITAL_RE.sub(r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: anchors[int(m.group(1))], s)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse(md):
    blocks, lines = [], md.split("\n")
    i = 0
    used_ids = {}
    used_bases = {}
    section = ["doc", 0]          # current heading key, tables emitted under it

    def register(candidate):
        n = used_ids.get(candidate, 0) + 1
        used_ids[candidate] = n
        return candidate if n == 1 else f"{candidate}-{n}"

    def register_base(candidate):
        n = used_bases.get(candidate, 0) + 1
        used_bases[candidate] = n
        return candidate if n == 1 else f"{candidate}-{n}"
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if not st:
            i += 1; continue
        if st == "---":
            blocks.append({"t": "rule"}); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", st)
        if m:
            txt = m.group(2).strip()
            tag = KEY_TAG_RE.search(txt)
            hid = register("card-" + slug(tag.group(1))) if tag else register(slug(txt))
            section = [week_key(txt) or hid, 0]
            blocks.append({"t": "h", "l": len(m.group(1)), "text": txt,
                           "id": hid, "vars": vars_in(txt)})
            i += 1; continue
        if st.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1].strip()):
            header = split_row(st)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i].strip())); i += 1
            prev = blocks[-1] if blocks else None
            label = bold_label(prev["text"]) if prev and prev["t"] == "p" else None
            section[1] += 1
            if label:
                key_base = f"{section[0]}-{label}"
            elif section[1] > 1:
                key_base = f"{section[0]}-t{section[1]}"
            else:
                key_base = section[0]
            key_base = register_base(key_base)
            keys = [f"{key_base}-r{n}" for n in range(1, len(rows) + 1)]
            blocks.append({"t": "table", "head": header, "rows": rows,
                           "key_base": key_base, "keys": keys}); continue
        if st.startswith("```"):
            buf = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i].rstrip()); i += 1
            i += 1
            blocks.append({"t": "code", "lines": buf if buf else [""]}); continue
        if st.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip())); i += 1
            qtext = " ".join(x for x in buf if x)
            blocks.append({"t": "quote", "text": qtext, "vars": vars_in(qtext)}); continue
        m = re.match(r"^(\s*)[-*]\s+(.*)$", ln)
        if m:
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not mm or mm.group(3).startswith("|"):
                    break
                items.append({"ind": len(mm.group(1)), "text": mm.group(3),
                              "ordered": mm.group(2)[0].isdigit(),
                              "vars": vars_in(mm.group(3))})
                i += 1
            blocks.append({"t": "list", "items": items}); continue
        m = re.match(r"^\s*(\d+)\.\s+(.*)$", ln)
        if m:
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)(\d+)\.\s+(.*)$", lines[i])
                if not mm:
                    break
                items.append({"ind": len(mm.group(1)), "text": mm.group(3), "ordered": True,
                              "vars": vars_in(mm.group(3))})
                i += 1
            blocks.append({"t": "list", "items": items}); continue
        buf = [st]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*([-*]\s|\d+\.\s|#|\||>|```)", lines[i]) and lines[i].strip() != "---":
            buf.append(lines[i].strip()); i += 1
        ptext = " ".join(buf)
        blocks.append({"t": "p", "text": ptext, "vars": vars_in(ptext)})
    return blocks


# ---------------------------------------------------------------- DOCX
PALETTE = {
    "acc": "0B3D5C", "acc_mid": "12628F", "acc_soft": "E8F0F7", "line": "D8E0E8",
    "zebra": "F6FAFD", "code_bg": "F4F7FA", "strong": "0E2B3D", "link": "1A5C8A",
    "muted": "5B6B7A", "white": "FFFFFF",
    "tip_bg": "FFF8E6", "tip_bar": "F0DCA3", "tip_tx": "5B4A12",
}
CALL = {
    "note": ("EEF6FB", "9DC3E6", "0B3D5C"),
    "tip": (PALETTE["tip_bg"], "F0DCA3", PALETTE["tip_tx"]),
    "warn": ("FDF1EE", "F0BFB4", "7B2A1A"),
}

def build_docx(blocks, path, title=None, subtitle=None, skip_first_h1=False, hero_meta=None):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    ACCENT = RGBColor.from_string(PALETTE["acc"])
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.7); sec.bottom_margin = Inches(0.8)
    sec.left_margin = sec.right_margin = Inches(0.85)
    CX, CM = "w:tblPr", "w:tcPr"

    def rgb(k):
        return RGBColor.from_string(PALETTE[k])

    # ---- low-level helpers ----
    def shade_par(p, fill, pad=110):
        pPr = p._p.get_or_add_pPr()
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
        pPr.append(sh)
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:before"), "60"); sp.set(qn("w:after"), "60")
        for side in ("left", "right"):
            sp.set(qn("w:" + side), str(pad))
        pPr.append(sp)

    def border_par(p, color, sides=("left",), sz=26, space=6, val="single"):
        pPr = p._p.get_or_add_pPr()
        pbdr = OxmlElement("w:pBdr")
        for side in sides:
            el = OxmlElement("w:" + side)
            el.set(qn("w:val"), val); el.set(qn("w:sz"), str(sz))
            el.set(qn("w:space"), str(space)); el.set(qn("w:color"), color)
            pbdr.append(el)
        pPr.append(pbdr)

    def shade_cell(cell, fill):
        tcPr = cell._tc.get_or_add_tcPr()
        el = OxmlElement("w:shd")
        el.set(qn("w:val"), "clear"); el.set(qn("w:color"), "auto"); el.set(qn("w:fill"), fill)
        tcPr.append(el)

    def cell_margins(cell, top=70, bottom=70, left=100, right=100):
        tcPr = cell._tc.get_or_add_tcPr()
        mar = OxmlElement("w:tcMar")
        for tag, v in (("top", top), ("start", left), ("bottom", bottom), ("end", right)):
            e = OxmlElement("w:" + tag); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa")
            mar.append(e)
        tcPr.append(mar)

    def table_borders(tbl, color, sz=4):
        tblPr = tbl._tbl.tblPr
        b = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement("w:" + side)
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz))
            e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
            b.append(e)
        tblPr.append(b)

    def _hyperlink(paragraph, url, text, size=None):
        part = paragraph.part
        r_id = part.relate_to(
            url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True)
        hl = OxmlElement("w:hyperlink"); hl.set(qn("r:id"), r_id)
        r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
        c = OxmlElement("w:color"); c.set(qn("w:val"), PALETTE["link"]); rPr.append(c)
        u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
        if size:
            szel = OxmlElement("w:sz"); szel.set(qn("w:val"), str(int(size * 2))); rPr.append(szel)
        r.append(rPr)
        t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
        r.append(t); hl.append(r); paragraph._p.append(hl)

    def runs(p, text, base=None, force_color=None):
        for t, st in inline(text):
            if st.get("a"):
                _hyperlink(p, st["a"], t, size=(base or {}).get("size"))
                continue
            r = p.add_run(t)
            r.bold = bool(st.get("b")) or bool(base and base.get("b"))
            r.italic = bool(st.get("i"))
            if (base or {}).get("size"):
                r.font.size = Pt(base["size"])
            if force_color is not None:
                r.font.color.rgb = force_color
            elif st.get("b"):
                r.font.color.rgb = rgb("strong")
            if (base or {}).get("font"):
                r.font.name = base["font"]

    # ---- theme ----
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string("20262C")
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12
    for lvl, sz in ((1, 21), (2, 15), (3, 12.5), (4, 11.5)):
        st = doc.styles[f"Heading {lvl}"]
        st.font.name = "Calibri"
        st.font.size = Pt(sz); st.font.bold = True
        st.font.color.rgb = ACCENT if lvl < 4 else RGBColor.from_string("12628F")
        st.paragraph_format.space_before = Pt(18 if lvl < 3 else 12)
        st.paragraph_format.space_after = Pt(6)
    try:
        doc.styles["Title"].font.color.rgb = rgb("white")
    except Exception:
        pass

    def add_footer():
        ftr = sec.footer
        p = ftr.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        border_par(p, PALETTE["acc_soft"], sides=("top",), sz=6, space=4)
        pPr = p._p.get_or_add_pPr()
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear")
        sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), PALETTE["acc_soft"])
        pPr.insert(0, sh)
        r = p.add_run("  " + (title or TITLE) + "  ·  page ")
        r.font.size = Pt(8); r.font.color.rgb = RGBColor.from_string(PALETTE["muted"])
        r2 = p.add_run()
        fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE")
        r2._r.addnext(fld)

    # ---- hero ----
    def hero():
        for txt, sz, bold, italic in ((title or TITLE, 22, True, False),
                                      (subtitle if subtitle is not None else SUBTITLE, 12, False, True)):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4 if txt == (title or TITLE) else 0)
            p.paragraph_format.space_after = Pt(3)
            runs(p, txt, base={"size": sz}, force_color=rgb("white"))
            for r in p.runs:
                r.bold, r.italic = bold, italic
            shade_par(p, PALETTE["acc"], pad=160)
        if hero_meta:
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(14)
            runs(p, hero_meta, base={"size": 8.5}, force_color=RGBColor.from_string("CFE3F2"))
            for r in p.runs:
                r.font.size = Pt(8.5)
            shade_par(p, PALETTE["acc"], pad=160)

    # ---- body ----
    skipped_src_h1 = False
    for b in blocks:
        t = b["t"]
        if t == "rule":
            continue
        if t == "h":
            lvl, txt = b["l"], b["text"]
            if skip_first_h1 and lvl == 1 and not skipped_src_h1:
                skipped_src_h1 = True
                hero()
                h = doc.add_heading("", level=1)
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                runs(h, txt, base={"size": 13}, force_color=rgb("white"))
                for r in h.runs:
                    r.font.size = Pt(13); r.bold = True
                    r.font.color.rgb = rgb("white")
                shade_par(h, PALETTE["acc_mid"], pad=140)
                continue
            if lvl == 1 and not skipped_src_h1:
                skipped_src_h1 = True
                hero()
            h = doc.add_heading("", level=lvl)
            runs(h, txt, base={"b": True})
            for r in h.runs:
                r.font.color.rgb = ACCENT if lvl < 4 else RGBColor.from_string(PALETTE["acc_mid"])
            if lvl == 1:
                shade_par(h, PALETTE["acc_soft"], pad=90)
                border_par(h, PALETTE["acc"], sides=("left",), sz=40)
            elif lvl == 2:
                border_par(h, PALETTE["acc"], sides=("bottom",), sz=12, space=3)
            elif lvl == 4:
                shade_par(h, PALETTE["acc_soft"], pad=70)
            continue
        if t == "p":
            p = doc.add_paragraph(); runs(p, b["text"]); continue
        if t == "code":
            for i, line in enumerate(b["lines"]):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.14)
                p.paragraph_format.right_indent = Inches(0.05)
                p.paragraph_format.space_after = Pt(0 if i < len(b["lines"]) - 1 else 8)
                p.paragraph_format.line_spacing = 1.0
                r = p.add_run(line if line.strip() else " ")
                r.font.name = "Consolas"; r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor.from_string(PALETTE["strong"])
                shade_par(p, PALETTE["code_bg"], pad=120)
                sides = ("left", "top", "right") if i == 0 else ("left", "right")
                if i == len(b["lines"]) - 1:
                    sides = sides + ("bottom",)
                border_par(p, PALETTE["line"], sides=sides, sz=6, space=4)
            continue
        if t == "quote":
            kind = "note"
            low = b["text"].lower()
            if low.startswith("accuracy rule") or "warning" in low[:60] or "never pay" in low:
                kind = "warn"
            elif "don't" in low[:40] or "why this week" in low or "don’t" in low[:40]:
                kind = "tip"
            bg, bar, tx = CALL[kind]
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.14)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(10)
            runs(p, b["text"], force_color=RGBColor.from_string(tx))
            for r in p.runs:
                r.italic = not r.bold
            shade_par(p, bg, pad=130)
            border_par(p, bar, sides=("left", "top", "bottom", "right"), sz=10, space=6)
            continue
        if t == "list":
            for it in b["items"]:
                style = "List Number" if it["ordered"] else "List Bullet"
                try:
                    p = doc.add_paragraph(style=style)
                except KeyError:
                    p = doc.add_paragraph()
                if it["ind"] >= 2:
                    p.paragraph_format.left_indent = Inches(0.58)
                p.paragraph_format.space_after = Pt(3)
                runs(p, it["text"])
            continue
        if t == "table":
            head, rows = b["head"], b["rows"]
            tbl = doc.add_table(rows=1, cols=len(head))
            try:
                tbl.style = "Table Grid"
            except KeyError:
                pass
            tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
            table_borders(tbl, PALETTE["line"])
            for j, cell in enumerate(tbl.rows[0].cells):
                cell.text = ""
                p = cell.paragraphs[0]
                r = p.add_run(clean_text(head[j])); r.bold = True; r.font.size = Pt(9)
                r.font.color.rgb = rgb("white")
                shade_cell(cell, PALETTE["acc"])
                cell_margins(cell)
                p.paragraph_format.space_after = Pt(1)
            for n, row in enumerate(rows):
                cells = tbl.add_row().cells
                for j in range(len(head)):
                    val = row[j] if j < len(row) else ""
                    cells[j].text = ""
                    p = cells[j].paragraphs[0]
                    runs(p, val)
                    for r in p.runs:
                        r.font.size = Pt(9)
                    p.paragraph_format.space_after = Pt(1)
                    cell_margins(cells[j])
                    if n % 2 == 1:
                        shade_cell(cells[j], PALETTE["zebra"])
            doc.add_paragraph()
            continue
    add_footer()
    doc.save(path)
    return len(doc.paragraphs)


# ---------------------------------------------------------------- HTML
def build_html(blocks, path):
    out = []
    anchors = []

    body = []
    first_h1 = True
    for b in blocks:
        t = b["t"]
        if t == "rule":
            continue
        if t == "h":
            txt = inline_html(b["text"])
            plain = clean_text(b["text"])
            a = b.get("id") or slug(b["text"])
            if b["l"] == 1 and first_h1:
                first_h1 = False
                body.append(f'<h1 id="top-of-library">{txt}</h1>')
                continue
            if b["l"] <= 3:
                anchors.append((b["l"], plain, a))
            if b["l"] <= 2:
                body.append(f'<h{min(b["l"],4)} id="{a}">{txt}</h{min(b["l"],4)}>')
            else:
                body.append(f'<h{min(b["l"],4)} id="{a}">{txt}</h{min(b["l"],4)}>')
            continue
        if t == "p":
            body.append(f"<p>{inline_html(b['text'])}</p>"); continue
        if t == "quote":
            body.append(f'<aside><p>{inline_html(b["text"])}</p></aside>'); continue
        if t == "list":
            tag = "ol" if b["items"][0]["ordered"] else "ul"
            items = "".join(
                f'<li class="{"sub" if it["ind"]>=2 else ""}">{inline_html(it["text"])}</li>'
                for it in b["items"])
            body.append(f"<{tag}>{items}</{tag}>"); continue
        if t == "table":
            th = "".join(f"<th>{inline_html(c)}</th>" for c in b["head"])
            trs = "".join("<tr>" + "".join(f"<td>{inline_html(row[j] if j < len(row) else '')}</td>"
                                           for j in range(len(b["head"]))) + "</tr>"
                          for row in b["rows"])
            body.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue

    nav = []
    for lvl, plain, a in anchors:
        cls = "n2" if lvl <= 2 else "n3"
        nav.append(f'<a class="{cls}" href="#{a}">{html.escape(plain)}</a>')

    css = """
:root{--acc:#0b3d5c;--acc2:#1a5c8a;--bg:#f7f9fb;--tx:#20262c;--mut:#5b6b7a;--line:#d8e0e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,Calibri,sans-serif}
.wrap{display:flex;align-items:flex-start;gap:28px;max-width:1320px;margin:0 auto;padding:0 20px}
nav{position:sticky;top:0;flex:0 0 280px;max-height:100vh;overflow:auto;padding:26px 6px 60px;
font-size:13px;border-right:1px solid var(--line)}
nav a{display:block;color:var(--acc2);text-decoration:none;padding:3px 8px;border-radius:6px}
nav a.n2{font-weight:700;margin-top:9px;color:var(--acc)}
nav a.n3{padding-left:18px;color:var(--mut);font-size:12.5px}
nav a:hover{background:#e8f0f7}
main{flex:1 1 auto;min-width:0;padding:26px 0 90px;background:#fff;border-radius:0;
box-shadow:0 1px 3px rgba(11,61,92,.06)}
article{max-width:900px;margin:0 auto;padding:0 34px}
header.hero{background:linear-gradient(135deg,#0b3d5c,#12628f);color:#fff;padding:44px 34px 38px;
margin-bottom:26px}
header.hero .in{max-width:900px;margin:0 auto}
header.hero h1{font-size:clamp(26px,4.2vw,40px);line-height:1.15;margin:0 0 10px;font-weight:800}
header.hero p.sub{font-size:clamp(15px,2.1vw,19px);opacity:.94;margin:0 0 14px;font-style:italic}
header.hero p.meta{font-size:13px;opacity:.8;margin:0}
h2{font-size:26px;line-height:1.25;color:var(--acc);margin:44px 0 12px;padding-top:10px;
border-top:3px solid var(--acc)}
h3{font-size:20px;color:var(--acc);margin:32px 0 8px}
h4{font-size:16.5px;color:#123f5e;margin:24px 0 6px}
p{margin:9px 0}
a{color:var(--acc2);word-break:break-word}
ul,ol{margin:9px 0 9px 22px;padding:0}
li{margin:5px 0}
li.sub{margin-left:16px}
strong{color:#0e2b3d}
aside{background:#eef6fb;border-left:4px solid #9dc3e6;padding:12px 16px;margin:18px 0;border-radius:0 8px 8px 0}
aside p{margin:0}
.tw{overflow-x:auto;margin:16px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--acc);color:#fff;text-align:left;padding:8px 10px;font-weight:700;vertical-align:bottom}
td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;background:#fff}
tbody tr:nth-child(even) td{background:#f6fafd}
code{background:#eef2f6;padding:1px 5px;border-radius:4px;font-size:13.5px}
.tip{background:#fff8e6;border:1px solid #f0dca3;border-radius:10px;padding:14px 18px;margin:22px 0;font-size:14.5px}
footer{max-width:900px;margin:40px auto 0;padding:0 34px;color:var(--mut);font-size:13px}
@media(max-width:1000px){nav{display:none}.wrap{padding:0}article{padding:0 20px}}
@media print{nav,header.hero{display:none}body{background:#fff}main{box-shadow:none}}
"""
    doc_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(TITLE)}</title>
<meta name="description" content="Free 24-week roadmap and resource library to job-ready HR / talent acquisition, built for Nigeria and portable globally.">
<style>{css}</style></head>
<body>
<header class="hero"><div class="in">
<h1>{html.escape(TITLE)}</h1>
<p class="sub">{html.escape(SUBTITLE)}</p>
<p class="meta">{html.escape(META)}</p>
</div></header>
<div class="wrap">
<nav id="toc">{''.join(nav)}</nav>
<main><article>
{''.join(body)}
<div class="tip"><strong>Working rule:</strong> platforms change their free tiers. Before planning a week around any course,
open its enrolment page and apply the three free tests from §1.5. Figures quoted for Nigeria (fees, minimum wage, law sections)
were checked on 20 October 2026 — re-verify before you cite them in an interview.</div>
</article></main>
</div>
<footer>Compiled 20 October 2026. Self-contained HTML — no external assets, no scripts, works offline.
Print to PDF from your browser if you want a paper copy.</footer>
</body></html>"""
    pathlib.Path(path).write_text(doc_html, encoding="utf-8")
    return len(doc_html)


def main(argv):
    parts, out_dir, name = [], pathlib.Path("."), "Library"
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("-o", "--out"):
            out_dir = pathlib.Path(args.pop(0))
        elif a in ("-n", "--name"):
            name = args.pop(0)
        elif a == "--no-write":
            print("[dry run] nothing written; import parse()/build_docx()/build_html() to reuse")
            return
        elif a.endswith(".md"):
            parts.append(pathlib.Path(a))
    if not parts:
        print(__doc__); return
    md = "\n\n".join(p.read_text(encoding="utf-8") for p in parts)
    blocks = parse(md)
    (out_dir / f"{name}.docx").parent.mkdir(parents=True, exist_ok=True)
    n = build_docx(blocks, out_dir / f"{name}.docx", hero_meta=META)
    size = build_html(blocks, out_dir / f"{name}.html")
    kinds = {}
    for b in blocks:
        kinds[b["t"]] = kinds.get(b["t"], 0) + 1
    print(f"blocks={len(blocks)} {kinds} docx_paragraphs={n} html_bytes={size}")
    print("NOTE: build_html rebuilds the .html next to the .docx — never run this "
          "against a file the user asked you to leave untouched (see SKILL.md, "
          "frozen-artefact rule).")


if __name__ == "__main__":
    main(sys.argv[1:])
