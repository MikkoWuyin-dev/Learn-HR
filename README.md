# HR Library — site build handoff

Unpack this first, then paste `site-plan/03-KICKOFF.md` into a fresh agent along with your design-system ZIP.

    README.md                        this file
    site-plan/00-CONTEXT.md          read first: facts, voice, constraints, vocabulary
    site-plan/01-PRODUCT-REQUIREMENTS.md   R1-R28, routes, owner decisions, done list
    site-plan/02-BUILD-ROADMAP.md    phases 0-5 with exit criteria, dependency order, risks
    site-plan/03-KICKOFF.md          the paste-ready first message, plus the verify-my-environment commands
    site-plan/README.md              what each spec contains
    content/docs/src/doc1.md .. doc5.md    the source of truth for all copy (never edit for layout)
    content/HR_Library_Overview.md         the home page copy
    scripts/docx_render.py           markdown parser + renderers; extend parse(), do not fork it
    scripts/validate_build.py        checks generated output (run from scripts/, or pass repo paths)
    scripts/style_audit.py           voice and markdown-integrity checks; run on generated page text
    downloads/HR_Doc1..5.docx        current outputs — regression baseline, must stay unchanged
    downloads/HR_Roadmap_Library.*   frozen research archive; download-only, do not rebuild

## Path translation

The specs were written inside the original workspace. In this tree:

| Spec says | Means |
|---|---|
| `docs/src/doc*.md` | `content/docs/src/doc*.md` |
| `HR_Library_Overview.md` | `content/HR_Library_Overview.md` |
| `skills/resource-learning-library/scripts/NAME.py` | `scripts/NAME.py` |
| `HR_Doc*.docx` / `HR_Roadmap_Library.*` | `downloads/` |
| `make check` | `make check` — builds, then runs the audit and the .docx gate |

## Content inventory, for a 30-second integrity check

words 1382 / 4973 / 3271 / 3013 / 3211 for doc1-5; overview 904; 20 `####` resource cards in doc3; 25 tables and 182 rows in doc2; 47 unique external URLs across the five docs; docx paragraph counts 51 / 100 / 142 / 87 / 118 with hyperlink rels 0 / 0 / 43 / 8 / 0.

## Sizes

Handoff archive: 23 files. Content is about 48,000 words in markdown; the site it generates is
52 routes (home, 5 documents, plan + 22 week pages, library + 20 cards, law card, templates,
check, downloads). Count them with `find _site -name index.html | wc -l`.
