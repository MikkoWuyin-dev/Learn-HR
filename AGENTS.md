# AGENTS.md — [PROJECT_NAME]

<!--
TEMPLATE NOTES (delete this block once filled)
- Agents load this file at the start of every session, so every line costs tokens every time.
  Target: under 200 lines (~2.5k tokens).
- Put only facts here that change less than once a month. Anything with a number, a date,
  or "currently" goes in STATUS.md.
- Fill every [ ]. If a section would say nothing, delete it. Don't fill it with "UNKNOWN".
- Claude Code reads CLAUDE.md. Add a one-line CLAUDE.md containing `@AGENTS.md` so every agent
  reads this same file.
-->

## What this is

[2–3 sentences: what the product does, who it's for, and the one outcome that matters.]

Project class: [prototype | product | critical]. This sets how much documentation is required (see Knowledge upkeep).

## Commands

- Install: `[ ]`
- Dev server: `[ ]`
- **Gate:** `[e.g. npm run verify]`. It must exit 0 before any work is called done. It runs: [typecheck, tests, lint, build, ...].
- Narrow test: `[e.g. npx vitest run path/to/file]`
- Environment: [OS, runtime version, quirks such as "Windows: file names are case-insensitive"]

## Where things live

Read only the rows your task needs.

| You need | Read |
|---|---|
| Current state, next step, open risks | `STATUS.md` (read it first, every session) |
| Product behaviour, scope, non-goals | `docs/PRD.md` |
| Architecture, contracts, schemas | `docs/MCD.md` |
| One feature's requirements and acceptance criteria | `docs/specs/NNNN-<feature>.md` |
| Planned order of work | `docs/ROADMAP.md` |
| Why a significant decision was made | the spec's Decisions section, or `docs/decisions/` |
| History | `git log` |

## Code map

```
[src/app/      UI and orchestration]
[src/engine/   pure logic. No DOM, React, or storage. Enforced by engine/purity.test.ts]
[src/state/    persistence]
[scripts/      tooling]
```

## Invariants (owner approval needed to change)

Product:
- [e.g. No accounts, no backend in V1]
- [ ]

Technical:
- [e.g. engine imports nothing from app/state/world (purity.test.ts)]
- [ ]

## When sources disagree

- Product behaviour: PRD. Architecture and contracts: MCD or the decision record. A feature's details: its spec. What exists now: the code and tests. Current state: STATUS.md, but check it against the code.
- Code doesn't prove what was intended, and a doc doesn't prove something was built.
- If resolving the conflict would change behaviour, architecture, data, security or scope, stop, show the conflict and the options, and ask. If it's just a wrong doc, fix the doc in the same task.

## Working rules

1. Do the task you were asked to do. Don't add unrequested features, dependencies, abstractions or refactors.
2. Before editing, run `git status` and keep any changes that aren't yours. Read the relevant spec, code and tests.
3. If something is unclear and costly to get wrong, ask. If it's unclear but cheap to redo, take the most reasonable reading and say which one you took.
4. A non-trivial feature with no spec needs a spec first (skill: `[architect]`), and the owner has to ratify it.
5. Run narrow tests while you work and the gate before you finish. Never report a check you didn't run. Never weaken a test to make it pass.
6. Re-read your full diff before you finish.

## Approval gates: ask first

- Commit: [allowed once the gate passes | ask every time]
- Push, merge, history rewrite, deploy, release
- Deleting data, or discarding changes you didn't make
- Adding a dependency, or upgrading a major dependency or tool version
- Changing an approved architecture decision, a data or persistence contract, a security boundary, or product scope

Everything else (reading, local edits, running tests and builds) needs no approval.

## Knowledge upkeep (keep it cheap)

- Each fact lives in exactly one file. Everywhere else, link to it.
- Never write down a number that a command can produce (test counts, bundle sizes, file or line counts). Write the command instead.
- Never record git state (committed, pushed, clean tree) in a doc. Git already knows it.
- At the end of a task, update only what has become false:
  - `STATUS.md`: always. Overwrite it, don't append. Keep it under 80 lines.
  - The spec: set its status, tick acceptance criteria, note any deviations.
  - `ROADMAP.md`: tick the step.
  - PRD or MCD: only if behaviour or a contract changed, and only with owner approval.
  - `AGENTS.md`: only if a command, invariant, gate, code-map entry or gotcha changed.
- Let commit messages carry the history. Don't keep changelog paragraphs in docs.
- If you hit a trap the next agent would also hit, add one line under Gotchas.

## Skills

Workflow skills live in `[.claude/skills/]`: [architect (spec), develop (build from spec), check (review), debug, remember (STATUS.md)]. Use a skill when the task matches its description, and read its SKILL.md before using it.
Reference packs ([e.g. threejs-*]) are for lookup only. Check which library version they target against ours.

## Gotchas

- [one line per trap, e.g. "Don't name a .ts file the same as a .tsx beside it: Windows treats them as one file"]

## Finish with

Outcome · files changed · checks run and their results · what isn't verified and why · next step, plus anything that needs approval.
