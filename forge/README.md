# Forge Contractor Service

This folder contains the bounded Forge contractor service.

It is governed by the Forge contractor contract and does not own Jarvis runtime
authority.

## Main Files

- [`main.py`](./main.py)
  - service entry surface
- [`service.py`](./service.py)
  - contractor service logic
- [`schemas.py`](./schemas.py)
  - request and response schemas
- [`forgekeeper.py`](./forgekeeper.py)
  - Forge Warden dry-run CLI (`observe`, `judge`, `plan`, `status`, `report`, `snapshot`,
    `snapshot-index`, query modes, `verify`, `chaos-check`, `bundle-export`)
  - CI gate: `.github/scripts/check-forgekeeper-governance.py`
  - Ops: `docs/subsystems/bumblebee_forge/OPERATIONAL_RUNBOOK.md`
  - Weekly: `scripts/forgekeeper/weekly-operator-loop.ps1` / `.sh`
  - Reconcile: `scripts/forgekeeper/reconcile-artifacts.ps1` / `.sh`

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside contractor or code-review proposals may be compared here, but they do
not become Forge truth unless project law has filtered them and the admitted
form is documented.

## Read Next

1. [../docs/contracts/FORGE_CONTRACTOR.md](../docs/contracts/FORGE_CONTRACTOR.md)
2. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
3. [../src/README.md](../src/README.md)
