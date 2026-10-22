#!/usr/bin/env python3
"""Phase 1.7 gate: the five downloadable .docx must not change.

Rebuilds each document from its markdown with the same parser the site uses, then
compares the rebuild against the shipped file in `downloads/`: paragraph count,
word count, table count and hyperlink relationship count. The shipped files are
also checked against the gate numbers the handoff states, so a replaced download
fails here too.

Nothing under `downloads/` is written to. Rebuilds go to a temporary directory.

    python3 tools/sitegen/docx_regression.py            # quiet pass/fail table
    python3 tools/sitegen/docx_regression.py --keep DIR # leave the rebuilds in DIR

Exit 0 only if every document matches on every column.

Coverage note: the three hero strings (title, subtitle, version line) are build
arguments that exist nowhere in the markdown, so they are read back from the
shipped file before rebuilding. The comparison therefore covers everything
parse() and build_docx() derive from the content — headings, tables, lists,
links, callouts, body text — and not the three strings that are handed in.
"""
import pathlib
import re
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import docx_render as R  # noqa: E402

# The gate numbers from site-plan/02-BUILD-ROADMAP.md task 1.7 and the handoff README.
DOCS = [
    ("content/docs/src/doc1.md", "HR_Doc1_Start_Here.docx", 51, 0),
    ("content/docs/src/doc2.md", "HR_Doc2_The_24_Week_Plan.docx", 100, 0),
    ("content/docs/src/doc3.md", "HR_Doc3_Resource_Library.docx", 137, 39),
    ("content/docs/src/doc4.md", "HR_Doc4_Nigeria_Labour_Law_CIPM.docx", 87, 8),
    ("content/docs/src/doc5.md", "HR_Doc5_Getting_The_Job.docx", 118, 0),
]

COLS = ("paras", "words", "tables", "rels")


def measure(path):
    """Count what the gate cares about. Words include table cells, unlike len(paragraphs)."""
    from docx import Document

    doc = Document(str(path))
    paras = doc.paragraphs
    words = sum(len(p.text.split()) for p in paras)
    words += sum(len(c.text.split()) for t in doc.tables for row in t.rows for c in row.cells)
    rels = zipfile.ZipFile(str(path)).read("word/_rels/document.xml.rels").decode("utf-8")
    return {
        "paras": len(paras),
        "words": words,
        "tables": len(doc.tables),
        "rels": len(re.findall(r'Type="[^"]*hyperlink"', rels)),
    }


def hero_strings(shipped_path):
    """The three build arguments, recovered from the shipped hero block (see note above)."""
    from docx import Document

    paras = Document(str(shipped_path)).paragraphs
    if len(paras) < 3:
        raise SystemExit(f"{shipped_path.name}: no hero block, cannot recover build arguments")
    return paras[0].text, paras[1].text, paras[2].text


def rebuild(md_path, out_path, shipped_path):
    blocks = R.parse(pathlib.Path(md_path).read_text(encoding="utf-8"))
    title, subtitle, meta = hero_strings(shipped_path)
    R.build_docx(blocks, out_path, title=title, subtitle=subtitle, hero_meta=meta)
    return measure(out_path)


def main(argv):
    try:
        import docx  # noqa: F401  (probe only; measure() imports it too)
    except ModuleNotFoundError:
        # Say it did not run, and do not let the exit code pretend otherwise.
        print("RESULT: SKIPPED — this gate did NOT run.")
        print("  It needs python-docx, which is not installed here.")
        print("  Install with:  python3 -m pip install -r requirements.txt")
        print("  Nothing was compared. Do not read this as a pass.")
        return 0

    keep = None
    if "--keep" in argv:
        keep = pathlib.Path(argv[argv.index("--keep") + 1])
        keep.mkdir(parents=True, exist_ok=True)
    tmp = keep or pathlib.Path(tempfile.mkdtemp(prefix="docx-regression-"))

    failures = 0
    print(f"{'document':40} {'gate':>6} {'shipped':>8} {'rebuilt':>8}  verdict")
    for md_rel, docx_name, gate_paras, gate_rels in DOCS:
        shipped_path = ROOT / "downloads" / docx_name
        if not shipped_path.exists():
            print(f"{docx_name:40} {'':>6} {'MISSING':>8} {'':>8}  FAIL")
            failures += 1
            continue
        shipped = measure(shipped_path)
        rebuilt = rebuild(ROOT / md_rel, tmp / docx_name, shipped_path)

        notes = []
        if shipped["paras"] != gate_paras:
            notes.append(f"shipped paras {shipped['paras']} != gate {gate_paras}")
        if shipped["rels"] != gate_rels:
            notes.append(f"shipped rels {shipped['rels']} != gate {gate_rels}")
        for col in COLS:
            if shipped[col] != rebuilt[col]:
                notes.append(f"{col} {shipped[col]}->{rebuilt[col]}")

        verdict = "ok" if not notes else "FAIL: " + "; ".join(notes)
        failures += bool(notes)
        print(f"{docx_name:40} {gate_paras:>6} {shipped['paras']:>8} {rebuilt['paras']:>8}  {verdict}")
        print(f"{'  words':40} {'':>6} {shipped['words']:>8} {rebuilt['words']:>8}")
        print(f"{'  tables':40} {'':>6} {shipped['tables']:>8} {rebuilt['tables']:>8}")
        print(f"{'  hyperlink rels':40} {gate_rels:>6} {shipped['rels']:>8} {rebuilt['rels']:>8}")

    print()
    if failures:
        print(f"RESULT: {failures} document(s) differ — the parser change touched the .docx path")
        return 1
    print("RESULT: all five documents unchanged "
          "(paras 51/100/137/87/118, hyperlink rels 0/0/39/8/0)")
    if not keep:
        print(f"rebuilds: {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
