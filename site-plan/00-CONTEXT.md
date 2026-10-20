# Master Context — "HR Library" website

Read this first. Then `01-PRODUCT-REQUIREMENTS.md`, then `02-BUILD-ROADMAP.md`. Everything here is measured from files on disk, so you can re-verify any number in one command.

## 1. The situation in six lines

A complete, free, 24-week learning path for someone in Nigeria starting from zero in Human Resources, aimed at a first job as a recruiter or HR assistant. It exists today as five documents (`.docx` + `.html`) plus a longer research archive. The job now is to turn the five documents into a public website that keeps the same purpose and the same voice. No content will be invented for the site; it is transformed from what is already written.

## 2. The content, by the numbers

| File | Words | Structure | Downloads |
|---|---|---|---|
| `docs/src/doc1.md` — Start Here | 1,382 | 26-term glossary table (33 rows incl. other tables), study method, account setup | `HR_Doc1_Start_Here.docx` 42,970 B |
| `docs/src/doc2.md` — The 24-Week Plan | 4,973 | Week 0 + Weeks 1–24, 25 tables, 182 table rows, ≈84 study blocks | `HR_Doc2_The_24_Week_Plan.docx` 56,112 B |
| `docs/src/doc3.md` — Resource Library | 3,271 | 20 resource cards as `####` headings, 19 table rows | `HR_Doc3_Resource_Library.docx` 49,864 B |
| `docs/src/doc4.md` — Nigeria: Labour Law & CIPM | 3,013 | Statute provisions table, statute list, 20 job tasks, 10 myths, one-page law card | `HR_Doc4_Nigeria_Labour_Law_CIPM.docx` 49,051 B |
| `docs/src/doc5.md` — Getting the Job | 3,211 | 15 interview questions, 12-story brief, CV rules, copyable templates | `HR_Doc5_Getting_The_Job.docx` 48,455 B |
| `HR_Library_Overview.md` — the compass | 904 | The front-page copy. Use it nearly verbatim. | — |
| `hr-library/part1-5.md` | ~20,100 | The archived full research (115 URLs, non-HR platforms, aid-gated courses). **Not for the site**, only as a downloadable file. | `HR_Roadmap_Library.docx` / `.html` |

Unique external URLs across the five documents: **47**. All were live-checked on 20 October 2026.

## 3. The two sources of truth, and their rules

**Markdown.** `docs/src/doc*.md`. Edit here, never in the HTML or the .docx. Both outputs come from one renderer.

**The design system** (the owner supplies a ZIP). Described as: `tokens.json` with 183 tokens in 20 groups, each carrying evidence and usage counts; seven dependency-free generator scripts in `tools/`; artefacts in `artifacts/` — `wakeout.css` (197 `--wk-*` custom properties, framework-free), `wakeout.theme.css` (Tailwind v4 bridge: 198 `@theme` mappings, 15 `@utility`, 6 keyframes, 21 `.wk-*` classes), DTCG JSON, `tokens.js`, a v3 preset, `standalone.html` (114 kB offline preview); docs: a 2,546-line React style guide, `DESIGN.md`, `ref/` evidence, two checksum-verified zips. Style: sticker neo-brutalism — cream paper, ink borders, zero-blur offsets.

Until the ZIP is in hand, treat every token name below as a placeholder and every colour value as unspecified. **Never invent a hex, a radius, a shadow or a font size.** If a needed value has no matching token, write a `/* TODO: no token for … */` comment and raise it.

## 4. Facts already settled — do not re-litigate, do not restate loosely

- **Free-tier rules baked into the content:** Coursera removed free auditing on 8 August 2025, so full access there needs a written per-course financial-aid application (~150-word minimum, up to ~16 days) — which is why no Coursera resource is in the five documents. Google Interview Warmup was retired in April 2026. HubSpot's Inbound Recruiting course is retired. Great Learning charges ₹299 for certificates. IBM SkillsBuild is free but has no HR course and no HR credential. There is no public free certification for Workday, SAP SuccessFactors, Oracle or ADP.
- **Nigerian law, read from the primary text** (`https://lawsofnigeria.placng.org/laws/L1.pdf`, the Federal Ministry of Justice PDF, 80 pages): s.7 written particulars within three months; s.11 notice of 1 day (≤3 months' service), 1 week (>3 months to <2 years), 2 weeks (2–<5 years), 1 month (≥5 years), written where a week or more; s.13 hours set by agreement/collective bargaining/wages board; s.16 sick leave up to 12 working days of paid wages a year on a medical certificate; s.18 at least 6 working days' full pay after 12 months (12 days if under 16); s.20 redundancy = involuntary permanent loss from excess manpower, inform the union or workers' reps, "last in, first out" subject to relative merit, skill, ability and reliability, best endeavours on payments; s.54 maternity — leave on a 6-week medical certificate, no work for 6 weeks after confinement, not less than 50% of wages with 6+ months' service, 30 minutes twice daily for nursing. Part II (ss.23–33) regulates recruiting and licences recruiters; ss.68–71 cover employer registration, labour schemes, employment exchanges and fee-charging agencies.
- **Minimum wage:** ₦70,000 a month under the National Minimum Wage (Amendment) Act 2024 (signed 29 July 2024); next statutory review due 1 June 2027; as of October 2026 no new national figure was agreed. State rates above it bind only those states' own civil servants.
- **CIPM fees** (from `cipmnigeria.org` membership-routes and exam pages): about ₦10,000 application, ₦12,000 on acceptance, then per-paper/professional fees roughly ₦20k–₦70k. Third-party blog totals disagree; the institute's own pages win.
- **Pension:** the 2014 Pension Reform Act formula is 8% employee + 10% employer; rates have been under public discussion since 2024, so the documents tell readers to confirm. Do not hard-code a "current" rate in new copy.
- Alison is free to study with a paid certificate; Saylor and OpenLearn issue their certificates free; FutureLearn access to the CIPD MOOCs is time-limited with no certificate; AIHR's Academy is a paid subscription with a rotating set of free courses — the docs flag this one as "check before you commit".

**The site must not soften any of this.** If a rewrite makes a hedged figure sound certain, that is a defect.

## 5. Voice — enforced in CI, not by taste

Written for someone with no background in the subject and possibly a small phone and limited data.

- No throat-clearing ("it's worth noting", "before we begin", "let's dive in"), no puffed-up adjectives ("comprehensive", "robust", "seamless", "transformative", "unlock"), no "it's not X, it's Y" turns, no consultant speak ("stakeholder", "leverage", "empower", "foster a culture").
- No rule-of-three rhythms except where the list is genuinely that long (e.g. four named providers, six statute sections). Real lists are fine; decorative triples are not.
- Concrete over encouraging: name the hour, the fee, the section number, the output. Sentences short enough to read at arm's length on a bus.
- Numbers are spelled out in running prose and digits in tables, matching the existing documents.

Run `python3 skills/resource-learning-library/scripts/style_audit.py` over every page string in the build; a non-zero exit blocks the merge. `validate_build.py` in the same folder checks the generated files.

## 6. Hard constraints

1. **No content fork.** The site is generated from `docs/src/doc*.md`. Do not paste copy into a template; do not maintain a second copy of the tracker or the resource list.
2. **The design system owns all appearance.** Site code adds layout classes and structure only. No new colours, no new type scale, no blur, no gradients.
3. **No Tailwind build.** Use `wakeout.css` custom properties directly in a small handwritten `site.css`. The Tailwind bridge is optional for the owner's other projects; the site does not need a Node toolchain.
4. **`HR_Roadmap_Library.html` and `.docx` are frozen.** They are offered as downloads and left byte-identical. Never run the docx/HTML renderer over them.
5. **No accounts, no server, no tracking of people.** Progress lives in `localStorage` on the visitor's device and never leaves it. A site about hiring should not collect jobseekers' data.
6. **Every fact and every link carries a date.** Pages render "checked 20 October 2026" from a build-time value, not a typed string.
7. **Hosted statically**, HTTPS, canonical URLs, no build secrets.

## 7. Vocabulary used in the other two documents

- **compass** — the home page, from `HR_Library_Overview.md`.
- **week block** — one row of a week table: minutes, activity, output.
- **card** — one `####` resource entry in Doc 3.
- **stamp** — the "checked on" date rendered on every content page.
- **sticker** — the rotated bordered label pattern from the design system, used for cost verdicts.
- **artifact/ artefact** — a piece of work the learner produces; the tracker's 16 items.
