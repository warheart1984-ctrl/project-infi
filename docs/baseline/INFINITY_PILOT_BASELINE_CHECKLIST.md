# Infinity Pilot (Full Stack) — Baseline Checklist

Project: Infinity Pilot (Platform Membrane v6 + UGR + AAIS/Jarvis)  
Owner: platform + ugr  
Last updated (UTC): 2026-06-06  
Review cadence: monthly

## 1) Required Blueprint Documents

- [x] Master project blueprint exists — [PROJECT_BLUEPRINTS_MASTER.md](../document/blueprints/PROJECT_BLUEPRINTS_MASTER.md)
- [x] Platform architecture — [PLATFORM_BLUEPRINT.md](../subsystems/platform/PLATFORM_BLUEPRINT.md)
- [x] UGR Ledger Bridge — [UGR_LEDGER_BRIDGE_SPEC.md](../subsystems/ugr/UGR_LEDGER_BRIDGE_SPEC.md)
- [x] API contracts — [PLATFORM_API_CONTRACT.md](../subsystems/platform/PLATFORM_API_CONTRACT.md)
- [x] Integration — [FULL_STACK_PILOT_INTEGRATION.md](../operations/FULL_STACK_PILOT_INTEGRATION.md)

## 2) Required Operational Documentation

- [x] README MA-12 operations — [README.md](../../README.md)
- [x] Platform runbook — [OPERATIONAL_RUNBOOK.md](../subsystems/platform/OPERATIONAL_RUNBOOK.md)
- [x] Early adopter onboarding — [INFINITY_PILOT_EARLY_ADOPTER.md](../operations/INFINITY_PILOT_EARLY_ADOPTER.md)
- [x] Pilot deploy proof — [PLATFORM_PILOT_DEPLOY_PROOF_BUNDLE.md](../proof/platform/PLATFORM_PILOT_DEPLOY_PROOF_BUNDLE.md)
- [x] Monitoring/alerting — Infinity-1 dashboard `infinity1-monitoring-alerts` panel
- [x] Troubleshooting — OPERATIONAL_RUNBOOK failsafe section
- [x] Release procedure — pilot compose + `make stack-pilot-gate`

## 3) Fail-Safe Checklist

- [x] Safe defaults documented (witness off, autopilot dry-run default)
- [x] Rollback — compose down; restore Postgres volume snapshot
- [x] Kill-switch — stop workers; revoke API keys
- [x] Data integrity — ledger verify API; audit JSONL append-only
- [x] Escalation — INFINITY_PILOT_SLA_ORIENTATION.md

## 4) Documentation Debt Tracker

| Debt ID | Description | Owner | Severity | Due Date | Status |
|---------|-------------|-------|----------|----------|--------|
| PLAT-PILOT-D1 | Multi-tenant K8s hardening + isolation proof | ops | high | 2026-06-06 | closed |
| PLAT-D8 | Full OIDC IdP integration per org | platform | medium | TBD | partial |
| UGR-D5 | Cross-physical-machine trust matrix | ops | medium | TBD | open |
| UGR-D7 | Neo4j v2 graph backend | architect | low | TBD | open |

## 5) Sign-Off

- [ ] Not ready
- [ ] Pilot-ready (governed early adopter — not GA)
- [x] GA-ready (full general availability — see [INFINITY_PILOT_GA_SIGNOFF.md](../audit/INFINITY_PILOT_GA_SIGNOFF.md))

Notes: GA admitted 2026-06-06 after PLAT-PILOT-D1 closure and production deploy sign-off. Post-GA: PLAT-GA-D2 legacy bridge removal.
