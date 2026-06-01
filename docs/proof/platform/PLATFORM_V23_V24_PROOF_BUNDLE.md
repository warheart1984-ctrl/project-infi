# Platform v23–v24 Proof Bundle (Marketplace v2)

**Claim:** Workflow Marketplace lifecycle and analytics — **asserted**.

## Verification

```bash
make platform-v23-gate
pytest tests/test_platform_v2130.py -q -k marketplace
```

## Evidence

- `platform/marketplace/lifecycle.py`, `platform/marketplace/analytics.py`
- Routes: approve, deprecate, analytics
