# Platform V8 Proof Bundle

**Claim:** Platform Membrane v8 (OIDC providers + billing gate) is **asserted** on this machine.

## Evidence

```bash
python .github/scripts/check-platform-v8-v14-governance.py
pytest tests/test_platform_v814.py -q -k billing
```

## Scope

- `platform/auth/oidc_providers.py` — Google/Microsoft/GitHub authorize URLs + stub token exchange
- `platform/billing/engine.py` — `evaluate_billing_gate` before job admission
- Org fields: `billing_status`, `billing_cycle_start`, `oidc_provider`

## Cross-machine

v12 hash consensus: see `PLATFORM_V2_PROOF_BUNDLE.md` when CI gate is green.
