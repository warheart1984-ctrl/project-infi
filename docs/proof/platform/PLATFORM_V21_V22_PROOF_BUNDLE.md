# Platform v21–v22 Proof Bundle (Mesh v2)

**Claim:** Operator Mesh v2 (SSE stream, mesh policy API, runbook refs) — **asserted**.

## Verification

```bash
make platform-v21-gate
pytest tests/test_platform_v2130.py -q -k mesh
```

## Evidence

- Routes: `GET /v1/orgs/{org_id}/mesh/events/stream`, `PUT/GET .../mesh/policy`
- Modules: `platform/mesh/stream.py`, `platform/mesh/policy.py`
