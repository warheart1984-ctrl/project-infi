# AGENTS.md

> Behavioral rules for agents operating in the AAES-OS / project-infi repository.

---

## Mission

Help build, test, maintain, and ship AAES-OS reliably, safely, and correctly — with claims bounded by evidence (Drive-G-1).

## AAES Crew

Lean crew pack (not Mandala 100):

- Foreman: `.cursor/skills/aaes-crew/SKILL.md` / `.cursor/agents/aaes-crew-foreman.md`
- Roles: architect → builder → coding/implementor → reviewer → inspector → **ESFR last**
- Pack: `.cursor/aaes-crew/` (phases, modes, vendor maps, IMPORT_SOURCES)
- Default ModeKey: `sage__navigator__evidence-strict`

Full Mandala 100+ESFR product surfaces remain in LineageStudio.

## Core Rules

### Always

- Read relevant source files completely before making any edit
- Run existing tests before AND after every change
- Use conventional commits: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`
- Prefer the smallest correct change — no unnecessary rewrites
- Rate readiness by Drive-G-2 dimensions (not one “production ready” adjective)

### Never

- Push directly to `main` or `master` — always open a PR
- Overwrite `.env`, `.env.local`, or Nova runtime credentials
- Commit secrets, tokens, or keys
- Claim *implements / enforces / complete* without matching tests or runtime gates
- Upgrade `pending-cluster-execution` baseline slots without real cluster artifacts

## Stack Defaults

| Layer | Technology |
|---|---|
| Runtime | Node.js 20 LTS |
| Language | TypeScript 5 |
| Tests | Vitest |
| Monorepo | packages/* (incl. `@aaes-os/cef-core`) |

## Continual learning

Use `.cursor/skills/continual-learning/SKILL.md` → `agents-memory-updater` to maintain the sections below.

## Learned User Preferences

- Prefer evidence-bound wording; treat Reality as the senior engineer (CEF axioms)
- Use lean AAES crew + vendor skills rather than cloning Mandala 100 into this repo
- Validate OEL/baseline artifacts through `@aaes-os/cef-core`; independent reproduction (digests/cluster/ACTIVE cert) is optional backlog — waived for ESFR 2026-07-31, not a current gate blocker
- Treat CREC, OEL, CEL, Security, and ModelEval as CEF profiles of one evidence architecture, not separate systems
- Keep deployment certificates DRAFT until promotion authority and live evidence fields are real

## Learned Workspace Facts

- Original AAES-OS monorepo lives at `G:\project-infi` (GitHub: warheart1984-ctrl/AAES-OS)
- Production Baseline v1.0 freezes the deploy stack at commit `7efa0c5f`; live cluster slots may remain pending
- Mythar AAES envelope pilot fits best at `G:\mythar-v0.2`
- LineageStudio holds the full Mandala crew + vendor skill inventory SoT
- CRE at `G:\cre` supplies the lean 6-role + ESFR crew pattern referenced by `.cursor/aaes-crew/`
- CEF charter/specs live under `docs/release/cef/`; OEL under `docs/release/operational-evidence-layer/`; schema validation is `@aaes-os/cef-core`
- ModeKey auto-apply in this repo is declared Cursor guidance, not a Node runtime enforcer
