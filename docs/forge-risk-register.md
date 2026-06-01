# Forge Risk Register

Status: active canonical risk register for Forge implementation.

## Active risks

| Risk ID | Risk | Severity | Trigger | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| FR-004 | Post-cutover CI failure under default `fail` governance mode | Medium | First workflow run after P2-3 cutover surfaces ledger drift | Monitor first CI runs; use dispatch `warn` override only for bounded audit windows | Drift Watcher + Inspector | Active |
| FR-005 | Nightly Forge profile build increases self-hosted runtime/cost | Medium | Scheduled runs always use `forge-selfhosted` | Track perf history; revert schedule profile default if burn-in shows instability | Operator | Active |
| FR-006 | Incomplete post-cutover workflow-run evidence in P2-3 packet | Low | Proof packet missing CI run links after merge | Append first green workflow run IDs to proof packets after CI executes | Inspector | Active |
| FR-007 | Live GitHub promotion dry-run not yet executed | Medium | No workflow-run artifact for release dry-run dispatch | Run `CoGOS Stable Release` dry-run with Forge RC source and capture artifact links | Operator | Active |
| FR-008 | Gate F Meta Architect ship decision pending | High | Automated gate passes locally but live RC/promotion URLs missing | Complete Gate F checklist in `docs/forge-shippable-gate.md` and record APPROVE in P4-1 proof packet | Meta Architect | Active |

## Closed risks (P2-3 cutover)

| Risk ID | Risk | Resolution | Closed |
|---|---|---|---|
| FR-001 | Governance drift catches stay warn-only longer than intended | Meta Architect approved default `fail` cutover (2026-05-27) | 2026-05-27 |
| FR-002 | Premature fail-mode default breaks existing pipelines | Pre-cutover dual-mode validation passed; approval recorded before default change | 2026-05-27 |
| FR-003 | Incomplete cutover evidence for P2-3 decision | Meta Architect decision recorded; local post-cutover validation green; CI run links pending | 2026-05-27 |

## Policy record

- **P2-3 status:** APPROVED and ACTIVE (Meta Architect, 2026-05-27)
- **Default governance mode:** `fail`
- **Audit override:** dispatch input `governance_ledger_mode=warn`
- **Evidence path:** `docs/proof/forge/P2-3_GOVERNANCE_LEDGER_PREAPPROVAL_PROOF.md`
