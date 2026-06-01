# Forge Platform Gate (Gate G)

Status: **platform-tier approved** (automation green; live CI URL debt tracked).

Authority: `docs/forge-platform-program.md`, `META_ARCHITECT_LAWBOOK.md`.

## Command

```bash
make forge-platform-gate
```

Report: `ci-artifacts/forge-platform-gate-report.json`

## Scope

Superset of `make forge-shippable-gate` plus:

| Gate | Check |
|---|---|
| P7 | Pipeline v2 specs, lineage emit/validate |
| P8 | Arch matrix + cloud output registry |
| P9 | Evolution ledgers + nightly evolution dry-run |
| G | Meta Architect platform-tier approval |

## Dashboard

```bash
make forge-dashboard
make forge-dashboard FORGE_DASHBOARD_ARGS="--check"
```

## Gate G go/no-go checklist

- [x] `make forge-platform-gate` passes locally (WSL evidence)
- [x] Promotion dry-run fixture passes with `forge-lineage.json`
- [x] Platform dashboard `--check` green (substrate/backend/pipeline/lineage)
- [ ] Public CI workflow run URL attached (debt — post-merge)
- [ ] Live Forge RC with lineage artifacts attached (debt — operator)
- [x] Meta Architect records explicit **APPROVE** decision

## Meta Architect decision record

| Field | Value |
|---|---|
| Decision | **APPROVE** — platform-tier Forge channel authorized |
| Authority | Meta Architect (session directive) |
| Decision date | 2026-05-28 |
| Scope | P7 lineage, P8 arch/cloud contracts, P9 platform gate, dashboard |
| Evidence | `make forge-platform-gate`, `make forge-dashboard --check`, promotion dry-run with lineage |
| Live CI run URL | pending (attach after merge to main) |
| RC lineage bundle URL | pending (operator) |
| Notes | Gate G approves **platform-tier contracts and automation**. Gate F (first shippable ISO) remains separate. Cloud/replay stubs stay experimental until implementation milestones. |

## Proof artifact

- Gate report: `ci-artifacts/forge-platform-gate-report.json`
- Proof packet: `docs/proof/forge/P9_PLATFORM_GATE_PROOF.md`
