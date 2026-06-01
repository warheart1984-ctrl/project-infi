# Bumblebee Forge Baseline Checklist

Use this checklist under `REPO_PROOF_LAW.md` and `META_ARCHITECT_LAWBOOK.md`.

Project: Bumblebee Forge Edition
Owner: TBD-Forge-Owner
Last updated (UTC): 2026-05-28T03:30:00Z
Review cadence: Weekly until Stage 2

## 1) Required Blueprint Documents

- [x] Master project blueprint exists and is discoverable.
- [x] System architecture overview is documented.
- [x] Component/module map is documented.
- [x] Interface/API contracts are documented.
- [x] Data flow and trust boundaries are documented.
- [x] Constraints, assumptions, and non-goals are documented.

Blueprint artifact references:

- `FORGEKEEPER_BLUEPRINT.md`
- `FORGEKEEPER_CLI_CONTRACT.md`
- `BUMBLEBEE_FORGE_ROADMAP.md`

## 2) Required Operational Documentation

- [x] Setup/install runbook exists (skeleton).
- [ ] Standard operating procedures (SOP) exist for normal operations (weekly loop skeleton only).
- [x] Monitoring/alerting and observability docs exist (outline in runbook §3.1).
- [x] Troubleshooting guide exists for common failures (outline in runbook §3.2).
- [x] Incident response/escalation runbook exists (outline in runbook §3.3).
- [x] Release/deployment procedure exists (outline in runbook §3.4 + CI gate).

Operational doc references:

- `asserted`: to be produced in Stage 2 and Stage 3.

## 3) Fail-Safe Checklist

- [x] Fail-safe design is documented (safe-default behavior).
- [x] Rollback procedure is documented and testable.
- [x] Recovery/restart procedure is documented.
- [x] Kill-switch/operator stop path is documented.
- [ ] Data integrity safeguards are documented.
- [ ] Failure-mode ownership and escalation paths are documented.

Fail-safe doc references:

- `FORGEKEEPER_BLUEPRINT.md`
- `BUMBLEBEE_FORGE_ROADMAP.md`

## 4) Documentation Debt Tracker

| Debt ID | Description | Owner | Severity | Due Date | Status | Linked Doc/Issue |
|---|---|---|---|---|---|---|
| BF-DOC-001 | Operational runbook skeleton exists; monitoring/incident/release SOPs still missing | TBD-Forge-Owner | High | 2026-06-10 | Skeleton | docs/subsystems/bumblebee_forge/OPERATIONAL_RUNBOOK.md |
| BF-DOC-002 | Missing data integrity and escalation ownership docs | TBD-Forge-Owner | Medium | 2026-06-17 | Open | TBD |
| BF-ENV-001 | Python runtime matrix mismatch risk (`.python-version` is 3.10 while validation currently passes on 3.12) | TBD-Forge-Owner | High | 2026-06-03 | Open | docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md |
| BF-OPS-001 | Missing retention and rotation SOP for append-only decision ledger at `.runtime/forgekeeper/decision_ledger.jsonl` | TBD-Forge-Owner | Medium | 2026-06-12 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-002 | Missing SOP for proof report publication cadence and immutable archival for `forgekeeper_report.json` | TBD-Forge-Owner | Medium | 2026-06-14 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-003 | Missing policy for when fixed timestamps may be used in governance exports vs live-time operational reporting | TBD-Forge-Owner | Low | 2026-06-16 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-004 | Missing snapshot retention/indexing SOP and supersession protocol for `forgekeeper_snapshot.json` lifecycle | TBD-Forge-Owner | Medium | 2026-06-18 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-005 | Missing verification SOP for snapshot-index claim transition audits and supersession chain review cadence | TBD-Forge-Owner | Medium | 2026-06-20 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-006 | Missing access/logging policy for snapshot-query filter usage and export review trace retention | TBD-Forge-Owner | Low | 2026-06-22 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-007 | Missing reconciliation SOP when `trace-query` reports hash drift between live ledger and previously emitted snapshot/index artifacts | TBD-Forge-Owner | Medium | 2026-06-24 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-008 | Missing operator decision SOP for `reconcile-query` remediation ordering (report->snapshot->snapshot-index) and rollback signaling | TBD-Forge-Owner | Medium | 2026-06-26 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-009 | Missing governance threshold policy for `drift-window-query` trend interpretation and alerting cutoffs (`improving/stable/degrading`) | TBD-Forge-Owner | Low | 2026-06-28 | Open | docs/subsystems/bumblebee_forge/FORGEKEEPER_CLI_CONTRACT.md |
| BF-OPS-010 | Missing weekly chaos-drill SOP and sign-off criteria for `chaos-check` before Stage 4 promotion | TBD-Forge-Owner | Medium | 2026-06-30 | Open | docs/subsystems/bumblebee_forge/STAGE_EXECUTION_PLAYBOOK.md |
| BF-XM-001 | Cross-machine replay scaffold built but inactive; activation and second-machine evidence pending operator decision | TBD-Forge-Owner | Medium | TBD | Built-Inactive | docs/subsystems/bumblebee_forge/CROSS_MACHINE_REPLAY.md |
| BF-CI-001 | CI gate runs `reconcile-artifacts` after tests with strict artifact-sync verify (use `--no-strict-verify-claim` only for debug) | TBD-Forge-Owner | Low | 2026-07-05 | Mitigated | .github/scripts/check-forgekeeper-governance.py |
| BF-OPS-011 | Index archival automation not implemented; pair-based trend policy documented in SNAPSHOT_INDEX_COMPACTION_POLICY.md | TBD-Forge-Owner | Low | 2026-07-12 | Open | docs/subsystems/bumblebee_forge/SNAPSHOT_INDEX_COMPACTION_POLICY.md |

## 5) Sign-Off

- Baseline completeness:
  - [x] Not ready (baseline gaps remain)
  - [ ] Ready (all baseline requirements satisfied)
- Blueprint reviewer: TBD
- Operations reviewer: TBD
- Governance/release reviewer: TBD
- Sign-off date (UTC): TBD
- Notes: Stage 0 docs are present. Stage 1/2 runtime scaffold is implemented with dry-run only safety posture.
