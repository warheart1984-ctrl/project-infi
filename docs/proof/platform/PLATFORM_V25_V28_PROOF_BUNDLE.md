# Platform v25–v28 Proof Bundle (Proof Federation v2)

**Claim:** Signed attestations, dispute→drift, runner registry, replay v2 — **asserted**; cross-machine CI quorum — **proven** when `platform-cross-machine-gate` tertiary job passes.

## Verification

```bash
make platform-v25-gate
pytest tests/test_platform_v2130.py -q -k proof
python -m platform replay --manifest docs/proof/platform/cross_machine/REPLAY_MANIFEST.v2.template.json
```

## Evidence

- `platform/proof/signing.py`, `platform/proof/runners.py`
- Hash mismatch sets `proof_status=disputed` and enqueues `drift_investigation` (Class II)
