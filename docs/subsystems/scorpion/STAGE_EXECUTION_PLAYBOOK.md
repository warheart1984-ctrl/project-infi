# Scorpion Stage Execution Playbook

## Canonical Definition

Project Scorpion is a governed OS-level anomaly extractor that detects,
classifies, and reconstructs bugs by enforcing behavioral invariants.

Claim posture: `asserted` until cross-machine proof replay is recorded.

## Authority

Precedence: Law > Blueprint > Contract > Implementation > Pipeline > Tool.

Authoritative references:

- `META_ARCHITECT_LAWBOOK.md`
- `REPO_PROOF_LAW.md`
- `SCORPION_BLUEPRINT.md`
- `SCORPION_CLI_CONTRACT.md`
- `SCORPION_ROADMAP.md`

## Eight-Job Operating Model

| Role | Primary responsibility | Stage focus |
|---|---|---|
| Architect | Law-to-design mapping, interfaces, acceptance criteria | 0-4 |
| Coder | Safe implementation with dry-run defaults | 1-3 |
| Debugger | Reproduce failures, minimal fixes, regression tests | 1-4 |
| Inspector | Behavior vs contract and output correctness | 1-4 |
| Meta-Inspector | Proof quality, claim taxonomy integrity | 0-4 |
| Operator | Controlled execution, approvals, rollback tokens | 2-4 |
| Seam Checker | Boundary checks across OS/trace/proof seams | 2-4 |
| Chaos User | Adversarial drills for fail-safe behavior | 1-4 |

## Stage Ladder (00-04)

### Stage 00 — Lock Constitution and Scope

- Freeze blueprint, non-goals, invariant catalog schema.
- Exit gate: canonical authority chain documented.

### Stage 01 — Observe and Scan Safely

- Fixture Sentinel, evaluators, scan/judge/extract/reconstruct.
- Exit gate: deterministic scan on fixtures; chaos-check `proven` locally.

Commands:

```bash
py -3.12 -m scorpion.scorpion --mode observe --case-id sc-demo --trace-path scorpion/fixtures/traces/syscall_misuse.ndjson
py -3.12 -m scorpion.scorpion --mode scan --case-id sc-demo --trace-path scorpion/fixtures/traces/fd_leak.ndjson
py -3.12 -m scorpion.scorpion --mode chaos-check --case-id sc-ci-gate
```

### Stage 02 — Historian and Drift Queries

- health_drift_index.jsonl, query modes, weekly operator loop.

### Stage 03 — Wolf CoG Seam

- Substrate cross-ref; optional ingest inactive until activation.

### Stage 04 — Kernel Sentinel

- Native adapter per `KERNEL_SENTINEL_DESIGN.md`; VM proof required for `proven`.

## Weekly Operator Loop (Stage 2+)

See `OPERATIONAL_RUNBOOK.md` and `scripts/scorpion/weekly-loop.ps1`.
