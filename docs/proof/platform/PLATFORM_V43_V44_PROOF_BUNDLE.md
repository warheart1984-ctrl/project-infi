# Platform v43–v44 Proof Bundle (Global Proof Network)

**Claim:** Witness enrollment, witness attestations, proof graph API, and `witness_policy_satisfied` gating — **asserted** local; CI witness quorum **proven** when `platform-cross-machine-gate` tertiary is green (witness inline script + `pytest -k witness`).

**Operator:** After a green tertiary run, record the GitHub Actions run URL here for PLAT-D31 **proven**.

```bash
make platform-v43-gate
pytest tests/test_platform_v4150.py -q -k witness
```
