# Platform Membrane v1 Proof Bundle

| Field | Value |
|-------|-------|
| **Claim** | Platform membrane v1 contracts + API smoke (`asserted`) |
| **Subsystem** | `platform.membrane.v1` |
| **Last reviewed** | 2026-05-31 |

## Scope

- Multi-tenant ingress (`platform/` service port 8090)
- Identity (org, principal, API key hash)
- Job registry + inline/Redis worker dispatch
- Federated artifact index
- Operator UI at `/platform`
- Cross-machine replay scaffold

## Verification (single-machine)

```bash
make platform-gate
make platform-smoke
pytest tests/test_platform_schemas.py tests/test_platform_api_smoke.py -q
```

## Cross-machine

See [cross_machine/README.md](./cross_machine/README.md) and `platform/schemas/platform_replay_manifest.v1.json`.

Claim posture: **`asserted`** until second-machine CI matrix is active.

## Related

- [../../subsystems/platform/PLATFORM_BLUEPRINT.md](../../subsystems/platform/PLATFORM_BLUEPRINT.md)
- [../../runtime/PLATFORM_MEMBRANE.md](../../runtime/PLATFORM_MEMBRANE.md)
