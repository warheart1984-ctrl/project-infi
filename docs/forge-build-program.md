# Forge Build Program

Status: active canonical build program for Forge delivery under `docs/`.

## Scope and authority

- This program governs Forge implementation sequencing and cutover decisions under:
  - `META_ARCHITECT_LAWBOOK.md`
  - `docs/forge-iso-design.md`
  - `docs/forge-backlog.md`
  - `docs/forge-risk-register.md`
- Precedence for conflicts remains: **Law > Blueprint > Contract > Implementation > Pipeline > Tool**.

## Current milestone state

- P0 through P4-1 automation are complete per `docs/forge-backlog.md`.
- **Gate F ship decision remains pending** Meta Architect approval after live RC + promotion dry-run evidence.
- Evidence packets:
  - `docs/proof/forge/P2-3_GOVERNANCE_LEDGER_PREAPPROVAL_PROOF.md`
  - `docs/proof/forge/P3-3_PROMOTION_DRY_RUN_PROOF.md`
  - `docs/proof/forge/P4-1_SHIPPABLE_GATE_PROOF.md`
- Canonical Gate F checklist: `docs/forge-shippable-gate.md`

## P4-1 Shippable gate (active)

Local/CI gate command:

```bash
make forge-shippable-gate
```

Gate report artifact:

- `ci-artifacts/forge-shippable-gate-report.json`

Gate F closure requires Meta Architect explicit approval once live RC + release dry-run URLs are attached.

## P2-3 execution policy (active)

### Objective

Governance-ledger enforcement defaults to `fail` across Forge-relevant workflows, with explicit dispatch override to `warn` for audit-only runs.

### Cutover status

| Item | Status |
|---|---|
| Meta Architect approval | Approved (2026-05-27) |
| Workflow dispatch default | `fail` |
| Env fallback default | `fail` |
| Explicit `warn` override | Supported via dispatch input |

### Workflow enforcement contract

- Relevant workflows accept `workflow_dispatch` input `governance_ledger_mode` with allowed values `warn` or `fail`.
- Default is **`fail`**.
- Governance preflight executes:
  - `python3 .github/scripts/validate-governance-ledger.py --mode "$GOVERNANCE_LEDGER_MODE" --summary-only`

## P3-2 Forge ISO CI smoke (active)

Self-hosted workflow behavior when Forge profile is active:

1. Build rootfs with Forge profile packages and staged `/forge` layout.
2. Run `forge-iso-smoke.sh` against rootfs.
3. Build ISO tree.
4. Emit `ci-artifacts/forge-build-state.json`.
5. Enforce installer matrix scenarios `1,3,4,6`.

Nightly schedule sets `COGOS_FORGE_PROFILE=forge-selfhosted` for end-to-end validation.

## P3-3 Promotion dry-run (active)

Local and workflow dry-run path:

1. Validate RC artifact bundle identity (`validate-promotion-source.py`).
2. Require Forge promotion artifacts when profile expected (`profile-*`, `forge-build-state.json`).
3. Emit `promotion-dry-run-report.json` in release dry-run mode.
4. Upload dry-run evidence artifact from `cogos-release.yml`.

Local proof command:

```bash
bash wolf-cog-os/scripts/test/promotion-dry-run.sh --skip-verify
```

## Verification commands

- `python3 .github/scripts/validate-governance-ledger.py --mode fail --summary-only`
- `bash wolf-cog-os/scripts/test/forge-iso-smoke.sh`
- `python3 wolf-cog-os/scripts/emit-forge-build-state.py --profile forge-selfhosted --output ci-artifacts/forge-build-state.json`

## Change-of-reality notes

- P2-3: default governance enforcement changed from `warn` to `fail` (approval-gated change now executed).
- P3-2: self-hosted Forge ISO smoke path and evidence emission added to CI.
