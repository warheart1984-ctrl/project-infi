# Infinity Pilot — Early Adopter Guide

Governed full-stack pilot: **Platform Membrane** (ops) + **UGR** (cognition/proof) + **AAIS/Jarvis** (operator executive).

## Prerequisites

- Docker 24+, Docker Compose v2
- Python 3.10+ (for local gates)
- 8 GB RAM recommended for compose stack

## 15-minute bootstrap

```bash
cd deploy/pilot
cp .env.example .env
# Edit PLATFORM_MASTER_API_KEY
docker compose up --build -d
python ../../scripts/pilot_compose_smoke.py --base-url http://127.0.0.1:8090 --api-key <your-key>
```

AAIS UI: http://127.0.0.1:8000  
Platform API: http://127.0.0.1:8090  
Platform console (if frontend built): `/platform`

## Org + API key

1. `POST /v1/orgs` with master key (`X-Api-Key`).
2. `POST /v1/orgs/{org_id}/api-keys` for operator key.
3. Map `ugr_tenant_id` on org for cognition overlay reads.

## MA-13 (customer-facing)

- **Autopilot** is policy-bound routing only; use `mode=dry_run` first. Webhooks fire on `apply` only.
- **Jarvis** remains executive for cognition; Platform is observe/actuate for ops jobs — not goal invention.
- **Sovereign export pack** (`POST /v1/orgs/{id}/sovereign/export-pack`) delivers audit + ledger + usage ZIP for compliance review.

## Customer audit deliverables

| Artifact | How |
|----------|-----|
| Usage CSV | `GET /v1/orgs/{id}/usage?format=csv` |
| Sovereign pack | Console or export-pack API |
| Ledger chain | `GET .../ledger/verify` + `python -m platform ledger export --org X` |
| UGR cognition overlay | `GET .../ledger/cognition-overlay` (read-only) |

## Verification gates

```bash
make stack-pilot-gate
```

## Support

See [INFINITY_PILOT_SLA_ORIENTATION.md](./INFINITY_PILOT_SLA_ORIENTATION.md). Escalation: platform ops owner + constitutional review for MA-13 class violations.

## Debt (known limits)

- Not GA — see [INFINITY_PILOT_BASELINE_CHECKLIST.md](../baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md)
- PLAT-D8 OIDC partial; PLAT-PILOT-D1 K8s multi-tenant hardening open
- UGR-D5 cross-machine matrix open
