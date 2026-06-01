# Platform Membrane Runtime

| Field | Value |
|-------|-------|
| **Service ID** | `platform.membrane.v5` (v1–v40 + v41–v50 sixth arc) |
| **Port** | 8090 (default) |
| **Authority** | Subsystems remain constitutional engines; Jarvis consult-only |

## Subsystem registration

Subsystems register work through **adapters** (`platform/adapters/`), not by inlining engines into the API.

| Subsystem | Adapter module | Platform kinds |
|-----------|----------------|----------------|
| Mechanic | `adapters/mechanic.py` | `mechanic.scan` |
| Slingshot | `adapters/slingshot.py` | `slingshot.preload` |
| Lab | `adapters/lab.py` | `lab.session` |
| AI Factory | `adapters/ai_factory.py` | `ai_factory.build` |
| Forgekeeper | `adapters/forgekeeper.py` | `forgekeeper.plan` |

## Jarvis boundary

- Jarvis (`src/api.py`) remains **single executive** for cognition.
- Platform API is for **operations**: jobs, artifacts, audit.
- Optional consult: Jarvis may read platform snapshots with operator API key (observe-only).

## Runtime layout

| Path | Purpose |
|------|---------|
| `.runtime/platform/` | SQLite dev store, audit JSONL |
| `.runtime/platform/audit/platform_audit.jsonl` | Append-only audit |
| Subsystem trees | Unchanged (`.runtime/mechanic/`, etc.) |

## UGR tenant alignment

`org_id` may map to `ugr_tenant_id` (`tenant:<name>`) per [deploy/ugr/tenants.json](../../deploy/ugr/tenants.json). Platform owns operational tenancy; UGR owns cognition ledger overlays.

## Operator commands

```bash
python -m platform serve
python -m platform.worker
make platform-gate
make platform-smoke
```

## Related

- [PLATFORM_MEMBRANE_V5_SPEC.md](./PLATFORM_MEMBRANE_V5_SPEC.md) — canonical v5 specification
- [PLATFORM_MEMBRANE_V4_SPEC.md](./PLATFORM_MEMBRANE_V4_SPEC.md) — v4 / fifth arc reference
- [PLATFORM_MEMBRANE_V3_SPEC.md](./PLATFORM_MEMBRANE_V3_SPEC.md) — v3 / fourth arc reference
- [../subsystems/platform/PLATFORM_BLUEPRINT.md](../subsystems/platform/PLATFORM_BLUEPRINT.md)
- [../subsystems/platform/PLATFORM_API_CONTRACT.md](../subsystems/platform/PLATFORM_API_CONTRACT.md)
