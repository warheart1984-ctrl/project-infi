# Scorpion Baseline Checklist

Project: Project Scorpion  
Owner: TBD-Scorpion-Owner  
Last updated (UTC): 2026-05-29T00:00:00Z  
Review cadence: Weekly until Stage 2

## 1) Required Blueprint Documents

- [x] Master blueprint exists (`SCORPION_BLUEPRINT.md`).
- [x] CLI contract documented.
- [x] Roadmap with stage gates documented.
- [x] Non-goals documented.

## 2) Required Operational Documentation

- [x] Setup/runbook skeleton (`OPERATIONAL_RUNBOOK.md`).
- [ ] Full SOP for normal operations (weekly loop skeleton only).
- [x] CI gate reference documented.

## 3) Fail-Safe Checklist

- [x] Dry-run default documented.
- [x] Apply mode blocked in contract.
- [x] Chaos-check adversarial drills documented.
- [ ] Data integrity escalation ownership (open debt).

## 4) Documentation Debt Tracker

| Debt ID | Description | Owner | Severity | Due Date | Status |
|---|---|---|---|---|---|
| SC-DOC-001 | Operational runbook skeleton only | TBD-Scorpion-Owner | High | 2026-06-10 | Skeleton |
| SC-DOC-002 | Kernel Sentinel VM proof criteria pending | TBD-Scorpion-Owner | Medium | 2026-07-01 | Open |
| SC-XM-001 | Cross-machine replay inactive | TBD-Scorpion-Owner | Medium | TBD | Built-Inactive |
| SC-WOLF-001 | Wolf post-build ingest inactive | TBD-Scorpion-Owner | Low | TBD | Built-Inactive |

## 5) Sign-Off

- [x] Not ready (baseline gaps remain)
- [ ] Ready
