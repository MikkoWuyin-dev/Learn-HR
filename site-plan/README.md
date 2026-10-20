# Handoff — building the HR Library site

Read in this order, they are meant to be read once and then referenced:

1. 00-CONTEXT.md — the situation, the numbers, the settled facts, the hard constraints, the voice rules
2. 01-PRODUCT-REQUIREMENTS.md — R1–R28, routes, owner decisions, definition of done
3. 02-BUILD-ROADMAP.md — phases 0–5 with exit criteria, dependency order, risks

Files referenced: content/docs/src/doc1-5.md (source of truth for all copy), content/HR_Library_Overview.md (home copy),
skills/resource-learning-library/scripts/{docx_render,validate_build,style_audit}.py (pipeline you extend and checks you run),
HR_Doc1..5.docx/.html (current outputs, must stay unchanged), HR_Roadmap_Library.docx/.html (frozen archive). 

One input missing at handoff time: the design-system ZIP. Phase 0 step 0.1 starts with it.

The scripts run from `scripts/`; a full path map is in the archive root README. Start with `03-KICKOFF.md`.
