# Platform V19–V20 Proof Bundle (Proof Federation)

**Claim:** k-of-n attestation registry and quorum promotion are **asserted** locally; **proven** when CI quorum gate is green.

```bash
python .github/scripts/check-platform-proof-federation-governance.py
pytest tests/test_platform_v1520.py -q -k attestation
```
