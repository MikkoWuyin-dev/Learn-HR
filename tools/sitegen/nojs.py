#!/usr/bin/env python3
"""Phase 4 gate: prove the site's words are in the HTML, not built by script.

A reader with JavaScript turned off is not an edge case here. This is a study
site meant to be opened on a phone on a bad connection, where a script can fail
to load or be blocked outright. If the words only appear once a script runs,
that reader gets an empty page and no way to know anything is missing.

So this strips every <script> tag from every built page and checks what is
left, which is exactly what a browser with JS off renders.

Three things are checked.

1. Content survives. Every page must still carry an <h1> and real prose once
   its scripts are gone.

2. Source content is present, checked against content/ rather than against the
   build. Comparing the build to itself would pass no matter what was missing,
   so each week page is held against the week blocks parsed out of doc2, the
   glossary against its terms, and the library against the doc3 cards.

3. Nothing ships hidden without a reason. This is the guard that keeps the
   property true over time. Anything carrying the `hidden` attribute must name
   one of the known acceptable reasons below; a new hidden element fails the
   run until somebody decides whether a JS-off reader is now missing content.
   Decoratively hidden things (`aria-hidden`) are not the same thing and are
   ignored.

    python3 tools/sitegen/nojs.py

Exit 0 only if every page passes.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = ROOT / "_site"
sys.path.insert(0, str(ROOT / "tools/sitegen"))

# Why an element may legitimately be absent from a page with no JavaScript.
# Anything else carrying `hidden` fails until it is classified here.
HIDDEN_ALLOWED = {
    # Controls. These do something when clicked; with no script there is
    # nothing for them to do, so hiding them is honest.
    "data-tick": "tick button - a control, and there is nothing to save it to",
    "data-copy": "copy button - a control",
    "data-glossary": "glossary search box - a control",
    "data-lib-filter": "library filter - a control",
    "data-reset-confirm": "reset confirmation - a control",
    # Progress state. These describe ticks saved on this device. Without
    # localStorage there is no state to describe, so a JS-off reader is not
    # being denied anything that could exist for them.
    "data-resume": "resume line - depends on saved progress",
    "data-next": "next-up card - depends on saved progress",
    "data-progress": "progress summary - depends on saved progress",
    "data-week-progress": "per-week progress line - depends on saved progress",
}

MIN_WORDS = 40


def strip_scripts(html):
    """The page as a browser renders it with JavaScript disabled."""
    return re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S | re.I)


def visible_text(html):
    t = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'")
    t = t.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    return " ".join(t.split())


def plain(value):
    """Source cell text as the reader sees it: markdown rendered, tags gone.

    Cells in content/ are markdown (**bold**, `code`), while the built page is
    HTML. Comparing one against the other fails on every emphasised cell and
    says the page is missing words that are plainly there.
    """
    try:
        import sitegen
        value = sitegen.md(str(value))
    except Exception:
        value = str(value)
    # Tags become a space, exactly as visible_text() does. Replacing them with
    # nothing instead makes "</strong>:" -> ":" while the page renders " :",
    # and every bold cell then looks missing.
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&amp;", "&").replace("&#39;", "'").replace("&nbsp;", " ")
    value = value.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    return " ".join(value.split())


def rows_of(block):
    """The cell texts of a table block, as plain text."""
    out = []
    for r in block.get("rows", []):
        for c in r:
            s = plain(c)
            if s:
                out.append(s)
    return out


def hidden_elements(html):
    """Tags carrying a bare `hidden` attribute, with the first data-* attr."""
    out = []
    for m in re.finditer(r"<(\w+)([^>]*\bhidden\b[^>]*)>", html, re.I):
        tag, attrs = m.group(1).lower(), m.group(2)
        if re.search(r"aria-hidden\s*=", attrs, re.I):
            continue  # hidden from a screen reader, still on the page
        # A bare boolean attribute carries no "=", so `data-resume hidden`
        # matches only if the value is optional. Keying on "=" alone silently
        # passed every such element as unclassified.
        names = re.findall(r"(data-[a-z-]+)\s*(?:=|\s|$)", attrs, re.I)
        out.append((tag, names[0].strip().lower() if names else "", attrs.strip()))
    return out


def main():
    if not SITE.exists():
        raise SystemExit("no _site - build the site first")

    import sitegen

    pages = sorted(SITE.rglob("index.html"))
    failures, checked = [], 0
    words_min = (None, 10 ** 9)

    # --- source content each page must still contain -----------------------
    expectations = {}

    for w in sitegen.week_sections():
        page = SITE / "2" / "plan" / "week" / str(w["n"]) / "index.html"
        if not page.exists():
            continue
        want = [plain(w["title"])]
        for b in w["blocks"]:
            if b["t"] == "table":
                want += rows_of(b)[:40]
        expectations[page] = want

    # The glossary is the term table on Document 1, not on the library page:
    # build_doc("doc1", "1/start-here", ..., glossary=True).
    glossary_page = SITE / "1" / "start-here" / "index.html"
    if glossary_page.exists():
        terms = []
        for b in sitegen.blocks("doc1"):
            if b["t"] == "table" and b.get("head") and \
                    str(b["head"][0]).strip().lower().startswith("term"):
                for r in b.get("rows", []):
                    if r and str(r[0]).strip():
                        terms.append(plain(r[0]))
        if terms:
            expectations[glossary_page] = terms

    lib_page = SITE / "3" / "library" / "index.html"
    if lib_page.exists():
        titles = [plain(c["title"]) for c in sitegen.cards() if c.get("title")]
        expectations.setdefault(lib_page, []).extend(titles)
        print(f"  holding the glossary to {len(expectations.get(glossary_page, []))}"
              f" terms and the library to {len(titles)} resources")

    for page in pages:
        rel = page.relative_to(SITE)
        raw = page.read_text(encoding="utf-8")
        no_script = strip_scripts(raw)
        text = visible_text(no_script)

        # 1. the page still stands on its own
        if not re.search(r"<h1\b", no_script, re.I):
            failures.append(f"{rel}: no <h1> once scripts are stripped")
        if len(text.split()) < MIN_WORDS:
            failures.append(
                f"{rel}: only {len(text.split())} words without scripts "
                f"(floor {MIN_WORDS})")

        # 2. the source's words are actually in the page
        for want in expectations.get(page, []):
            want = " ".join(str(want).split())
            if want and want.lower() not in text.lower():
                failures.append(f"{rel}: missing without JS -> {want[:70]!r}")

        # 3. nothing is hidden without an accepted reason
        for tag, data_attr, attrs in hidden_elements(no_script):
            if data_attr not in HIDDEN_ALLOWED:
                failures.append(
                    f"{rel}: <{tag}> ships hidden with no accepted reason "
                    f"({attrs[:60]}) - add it to HIDDEN_ALLOWED in nojs.py "
                    f"and say why a JS-off reader may lose it")

        checked += 1
        n = len(text.split())
        if n < words_min[1]:
            words_min = (rel, n)

    print(f"checked {checked} pages with every <script> stripped")
    print(f"  thinnest page without JS: {words_min[0]} at {words_min[1]} words")
    print(f"  hidden elements allowed:  {len(HIDDEN_ALLOWED)} kinds, all "
          f"controls or saved-progress state")
    print()
    if failures:
        print(f"RESULT: {len(failures)} problem(s) with JavaScript off")
        for f in failures[:25]:
            print(f"  - {f}")
        if len(failures) > 25:
            print(f"  ... and {len(failures) - 25} more")
        return 1
    print("RESULT: every page carries its content with JavaScript off")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
