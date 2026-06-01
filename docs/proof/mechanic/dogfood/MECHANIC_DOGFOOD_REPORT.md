# Mechanic Dogfood Report — project-infi

| Field | Value |
|-------|-------|
| **Case ID** | `infi-dogfood` |
| **Repo** | `.` (project-infi) |
| **Claim** | `asserted` |
| **Date** | 2026-05-31 |

## Commands run

```bash
python -m mechanic --mode scan --case-id infi-dogfood --repo-path . --write-json
python -m mechanic --mode diagnose --case-id infi-dogfood --write-json
python -m mechanic --mode rebuild --case-id infi-dogfood --write-json
```

## Summary

| Metric | Value |
|--------|-------|
| Genome nodes | 851 |
| Genome edges | 8 |
| Drift count | 35 |

## Top drift codes

| Code | Count | MA-13 relevance |
|------|-------|-----------------|
| GOV-01 | 19 | Class II — missing decision owner on workflows / agent configs |
| RNT-11 | 5 | Class III — model calls without audit hooks |
| CST-07 | 2 | Cost — redundant model call patterns |
| HUM-03 | 2 | Class II — automated chains without human_control |
| GOV-15 | 1 | Class II — ungoverned prompt asset |
| GOV-20 | 1 | Class II — shadow workflow duplicate label |
| GOV-25 | 1 | Class II — high-impact workflow missing rollback metadata |
| HUM-05 | 1 | Class II — high-impact CI without HITL |
| RNT-04 | 1 | Class III — cycle / loop risk |
| RNT-08 | 1 | Class II — missing output validation |
| RNT-22 | 1 | Class II — model chain missing validates edges |

## Notable findings (asserted)

1. **Governance ownership gap (GOV-01)** — majority of drifts; CI workflows and multi-model Python paths lack explicit `decision_owner` metadata.
2. **Audit hook debt (RNT-11)** — LLM call sites in `src/` and tooling paths missing trace/audit attrs at genome extraction time.
3. **Adapter overlap fixed during dogfood** — duplicate `prompt:*` nodes from `.cursor/` double-scan; filesystem adapter now skips `.cursor/` (handled by cursor_rules adapter).
4. **Human control (HUM-03/HUM-05)** — automated model chains and high-impact CI steps without HITL nodes in genome.

## Artifacts

- `.runtime/mechanic/infi-dogfood/process_genome.v1.json`
- `.runtime/mechanic/infi-dogfood/mechanic_scan.v1.json`
- `.runtime/mechanic/infi-dogfood/patch_plan.v1.json` (provisional, dry-run)

## Remediation posture

All rebuild outputs are **provisional** per MA-13. No customer-repo writes performed. Track remediation in [MECHANIC_DOGFOOD_DEBT.md](../../runtime/MECHANIC_DOGFOOD_DEBT.md).
