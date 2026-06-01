# Forge Warden Stage Execution Playbook

## Canonical Definition

Forge Warden is a governed supply-chain reconstruction engine that enforces
truth, rebuilds environments, and preserves identity under constitutional law.

Claim posture for this playbook: `asserted` until cross-machine proof replay is
recorded in `docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md`.

## Authority

Precedence: Law > Blueprint > Contract > Implementation > Pipeline > Tool.

Authoritative references:

- `META_ARCHITECT_LAWBOOK.md`
- `REPO_PROOF_LAW.md`
- `FORGEKEEPER_BLUEPRINT.md`
- `FORGEKEEPER_CLI_CONTRACT.md`
- `BUMBLEBEE_FORGE_ROADMAP.md`

## Eight-Job Operating Model

| Role | Primary responsibility | Stage focus |
|---|---|---|
| Architect | Law-to-design mapping, interfaces, acceptance criteria | 0-4 |
| Coder | Safe implementation with dry-run defaults | 1-3 |
| Debugger | Reproduce failures, minimal fixes, regression tests | 1-4 |
| Inspector | Behavior vs contract and output correctness | 1-4 |
| Meta-Inspector | Proof quality, claim taxonomy integrity | 0-4 |
| Operator | Controlled execution, approvals, rollback tokens | 3-4 |
| Seam Checker | Boundary checks across OS/package/workflow/proof | 2-4 |
| Chaos User | Adversarial drills for fail-safe behavior | 4 |

## Stage Ladder (00-04)

### Stage 00 - Lock Constitution and Scope

- Freeze lawbook, safety constraints, threat model, non-destructive defaults.
- Exit gate: one canonical authority chain for all later stages.

Role checklist:

- Architect: publish scope boundaries and non-goals.
- Meta-Inspector: verify claim taxonomy is present in all stage docs.
- Operator: no execution lane admission.

### Stage 01 - Observe and Judge Safely

- Read-only scanning, policy verdicts, claim taxonomy.
- Exit gate: risk classification without environment mutation.

Role checklist:

- Coder: maintain `observe` and `judge` modes.
- Inspector: validate ledger append-only behavior.
- Debugger: gate failures return contract errors, not silent mutation.

Commands:

```bash
py -3.12 -m forge.forgekeeper --mode observe --plan-id <id> --scope .
py -3.12 -m forge.forgekeeper --mode judge --plan-id <id> --decision reject --reason "preflight"
```

### Stage 02 - Generate Reversible Forge Plans

- Deterministic dry-run plans, rollback token placeholders, attestation preflight.
- Exit gate: replayable plan artifacts with hash evidence.

Role checklist:

- Coder: keep `--allow-apply` blocked.
- Seam Checker: verify plan schema compatibility with proof bundle format.
- Inspector: confirm attestation hooks label `proven/asserted/rejected`.

Commands:

```bash
py -3.12 -m forge.forgekeeper --mode plan --plan-id <id> --scope . --goal "bounded map" --write-plan docs/proof/bumblebee-forge/stage2_dry_run_plan.json
```

### Stage 03 - Execute Controlled Rebuild Apply (Scaffold Phase)

Current posture: non-destructive scaffolding only (`report`, `snapshot`,
`snapshot-index`, query modes, `verify`). Apply lane remains blocked.

- Exit gate for scaffold: traceability and reconciliation produce actionable,
  read-only remediation hints with claim labels.

Role checklist:

- Operator: run reconcile hints; never bypass apply block.
- Seam Checker: validate hash linkage across ledger/report/snapshot/index.
- Chaos User: run `chaos-check` before promoting readiness claims.

Commands:

```bash
py -3.12 -m forge.forgekeeper --mode report --plan-id <id>
py -3.12 -m forge.forgekeeper --mode snapshot --plan-id <id>
py -3.12 -m forge.forgekeeper --mode snapshot-index --plan-id <id>
py -3.12 -m forge.forgekeeper --mode reconcile-query --plan-id <id>
py -3.12 -m forge.forgekeeper --mode verify --plan-id <id>
```

### Stage 04 - Activate Runtime Immune System

- Continuous enforcement, seam checks, chaos drills, cross-machine attestation.
- Exit gate: repeatable proof replay on second machine with reviewer sign-off.

Cross-machine replay is **built in** (`CROSS_MACHINE_REPLAY.md`, `scripts/forgekeeper/`)
but **inactive** until `FORGE_CROSS_MACHINE_REPLAY_ACTIVE=1` and a filled manifest.
Do not promote cross-machine claims to `proven` while inactive.

Role checklist:

- Meta-Inspector: reject promotion when proof bundle lacks cross-machine section.
- Chaos User: `chaos-check` must pass all scenarios before weekly sign-off.
- Operator: maintain drift-window review cadence and escalation SOP.

Commands:

```bash
py -3.12 -m forge.forgekeeper --mode drift-window-query --plan-id <id>
py -3.12 -m forge.forgekeeper --mode chaos-check --plan-id <id>
py -3.12 -m forge.forgekeeper --mode verify --plan-id <id>
py -3.12 -m unittest tests.test_forgekeeper -v
```

## Promotion Rules

- `asserted`: design or local-only evidence exists.
- `proven`: required artifacts, tests, and cross-machine replay evidence exist.
- `rejected`: verification failed or safety gate was bypassed.

No proof, no claim.

## Failsafe and Rollback

- Default safety state: `dry_run_only`.
- Kill switch: deny `--allow-apply` in all modes.
- Recovery: regenerate `report` -> `snapshot` -> `snapshot-index` using
  `reconcile-query` command templates when drift is detected.

## Weekly Operator Loop

Detailed commands: `OPERATIONAL_RUNBOOK.md`. Optional driver:
`scripts/forgekeeper/weekly-operator-loop.ps1`.

1. Architect reviews open debt in `BASELINE_CHECKLIST.md`.
2. Operator runs `verify --write-report` (with `--fixed-timestamp`) and archives output in proof bundle.
3. Seam Checker runs `trace-query` and `reconcile-query`.
4. Chaos User runs `chaos-check`.
5. Meta-Inspector runs `bundle-export` and confirms CI gate:
   `python3 .github/scripts/check-forgekeeper-governance.py`.
6. Meta-Inspector updates claim labels in proof bundle and roadmap.
