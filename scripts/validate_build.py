#!/usr/bin/env python3
"""Check a themed library build before you tell the user it's done.

  python3 validate_build.py FILE1 FILE2 ...        (each .docx or .html or .md)

.docx checks : every XML part parses; heading/section counts; tables; real Word
               hyperlinks (rels); whether the theme colours are actually in the file;
               markdown leftovers that leaked into text; word count.
.html checks : zero external assets (script/link/img/iframe/url()); balanced
               nav anchors; markdown leftovers.
.md checks   : markdown-link syntax well formed; unbalanced ** (leaks into output);
               【KEY】 tags present on both sides of a cross-reference pair.
"""
import re, sys, zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
THEME = ("0B3D5C", "12628F", "F6FAFD")     # hero, title strip, zebra row


def docx_report(path):
    out = []
    z = zipfile.ZipFile(path)
    bad = []
    for n in z.namelist():
        if n.endswith(".xml"):
            try:
                ET.fromstring(z.read(n))
            except Exception as e:
                bad.append(f"{n}: {e}")
    doc = z.read("word/document.xml").decode()
    rels = z.read("word/_rels/document.xml.rels").decode()
    paras = re.findall(r"<w:p[ >]", doc)
    heads = re.findall(r'w:pStyle w:val="Heading(\d)"', doc)
    tables = doc.count("<w:tbl>")
    links = rels.count("relationships/hyperlink")
    colours = {c: doc.count(f'w:fill="{c}"') + doc.count(f'w:color="{c}"') for c in THEME}
    text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", doc))
    leaks = re.findall(r"\*\*|\]\(http|【|```", text)
    words = len(text.split())
    out.append(f"docx  {path}")
    out.append(f"      xml_ok={'NO -> ' + '; '.join(bad) if bad else 'yes'}"
               f" | paras={len(paras)} tables={tables} links={links} words={words}")
    out.append(f"      headings={ {l: heads.count(l) for l in '1234' if heads.count(l)} }")
    out.append(f"      theme fills={colours} | markdown leaks={len(leaks)}"
               + (f" e.g. {leaks[:3]}" if leaks else ""))
    if links == 0 and tables == 0 and len(paras) > 400:
        out.append("      WARN: long document with no hyperlinks or tables — did the parser see your markdown?")
    return "\n".join(out), (not bad and not leaks)


def html_report(path):
    h = open(path, encoding="utf-8").read()
    ext = re.findall(r"<(script|link|img|iframe)[^>]*", h)
    css_url = h.count("url(")
    ids = set(re.findall(r'id="([^"]+)"', h))
    navs = set(re.findall(r'href="#([^"]+)"', h))
    dangling = navs - ids
    md = re.findall(r"\*\*|\]\(http|【", h)
    ok = not ext and not css_url and not dangling and not md
    print(f"html  {path}")
    print(f"      external_assets={len(ext)} css_url()={css_url} dangling_nav={len(dangling)}"
          f" markdown_leaks={len(md)} bytes={len(h):,} -> {'OK' if ok else 'FAIL'}")
    return ok


def md_report(path):
    t = open(path, encoding="utf-8").read()
    bad_links = re.findall(r"\[[^\]]*\]\([^)\s]*\s[^)]*\)", t)
    odd_bold = [i + 1 for i, ln in enumerate(t.split("\n")) if ln.count("**") % 2]
    keys = set(re.findall(r"【([^】]+)】", t))
    print(f"md    {path}")
    print(f"      words={len(t.split())} bad_link_syntax={len(bad_links)}"
          f" lines_with_unbalanced_bold={odd_bold[:6]} key_tags={len(keys)}"
          + ("  <- unbalanced ** will leak into the docx" if odd_bold else ""))
    return not bad_links and not odd_bold


def main(argv):
    ok = True
    for f in argv:
        if f.endswith(".docx"):
            rep, good = docx_report(f); print(rep); ok &= good
        elif f.endswith(".html"):
            ok &= html_report(f)
        else:
            ok &= md_report(f)
    print("\nRESULT:", "all checks passed" if ok else "FAILURES above — fix before reporting done")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
