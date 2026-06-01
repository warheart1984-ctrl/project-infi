# Full Stack Pilot Integration

## Ports and services

| Service | Default port | Module |
|---------|--------------|--------|
| Platform Membrane API | 8090 | `python -m platform serve` |
| AAIS / Jarvis shell | 8000 | `uvicorn app.main:app` |
| Postgres | 5432 (internal) | compose |
| Redis | 6379 (internal) | job queue |

## Authority boundaries

- **Jarvis** (`src/api.py`, `app/main.py`): single executive for operator cognition.
- **Platform** (`platform/`): ops ingress only — jobs, mesh, proof, ledger, sovereign exports.
- **UGR Ledger Bridge** (`src/ugr/ledger_bridge/`): cognition claim elevation; no Stage 3 repo apply.

Jarvis may **consult** Platform with operator API key (read jobs, audit) — observe-only. No cognition routes inside `platform/`.

## Typical flow

1. Operator opens AAIS/Jarvis (8000) for governed chat and directives.
2. Operator dispatches subsystem work via Platform (8090): Mechanic scan, Lab session, etc.
3. Proof attestations and witness policy (optional) run on Platform proof federation.
4. UGR claims traverse `LedgerBridge` when cognition programs emit ledger claims.
5. Compliance officer downloads sovereign export pack from Platform console.

## Compose

[`deploy/pilot/docker-compose.yml`](../../deploy/pilot/docker-compose.yml) wires Platform + AAIS + data plane.

## Proof

- `make stack-pilot-gate`
- [`PLATFORM_PILOT_DEPLOY_PROOF_BUNDLE.md`](../proof/platform/PLATFORM_PILOT_DEPLOY_PROOF_BUNDLE.md)
- [`UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md`](../proof/ugr/UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md)
