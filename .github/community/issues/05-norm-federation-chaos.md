## Summary

Run and extend **chaos tests** on the **norm federation** layer — exercise observe/adopt abuse matrix and document results.

## Scope (bite-sized)

- Tests: `tests/test_norm_federation_observe.py`, `tests/test_norm_federation_adopt.py`
- Harness: `tools/stress/federation_chaos_hammer.py` (norm federation phases)
- Gate: `tools/governance/run_norm_federation_body_verification.py`

## Acceptance criteria

- [ ] Run chaos hammer with AAIS up (mock preset OK); capture output snippet in PR or `docs/audit/`
- [ ] Fix or file follow-ups for any unexpected 5xx / gate bypass
- [ ] Pytest + norm federation body gate pass

## Onboarding

```powershell
.\scripts\start-infinity1.ps1
python tools/stress/federation_chaos_hammer.py
```

## Labels

`help wanted`, `python`, `governance`, `chaos-testing`, `civilizational-arc`
