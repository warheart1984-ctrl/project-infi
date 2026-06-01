# Platform v41–v42 Proof Bundle (Autonomous Org Mesh)

**Claim:** Policy-bound routing policy + autopilot dry-run/apply with audit ledger — **asserted**.

```bash
make platform-v41-gate
pytest tests/test_platform_v4150.py -q -k "routing or autopilot"
```

Webhooks for `mesh.autopilot` fire only on `mode=apply`; dry-run records policy preview on assign actions.
