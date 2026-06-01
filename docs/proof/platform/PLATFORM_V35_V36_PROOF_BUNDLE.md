# Platform v35–v36 Proof Bundle (Proof Federation v3)

**Claim:** Ed25519/HMAC attestations, attestation bundles, replay v3 POST — **asserted** locally; **proven** when CI tertiary quorum passes.

```bash
make platform-v35-gate
pytest tests/test_platform_v3140.py -q -k proof
```
