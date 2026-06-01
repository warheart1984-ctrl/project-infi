# Platform v29–v30 Proof Bundle (Sovereign Control Plane)

**Claim:** Compliance CSV exports and tenant summary API — **asserted**.

## Verification

```bash
make platform-v29-gate
pytest tests/test_platform_v2130.py -q -k sovereign
python -m platform export compliance --org acme --kind audit
```

## Evidence

- `platform/sovereign/exports.py`, `platform/sovereign/tenant.py`
- Routes: exports audit/attestations, tenant summary
