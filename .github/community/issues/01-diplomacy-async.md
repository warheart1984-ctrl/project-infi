## Summary

Add **async** execution paths for one diplomacy workflow family so operator observe/adopt flows do not block the FastAPI event loop under concurrent load.

## Scope (bite-sized)

Pick **one** family first (suggested: inter-substrate diplomacy observe/adopt):

- `src/inter_substrate_diplomacy_runtime.py`
- Related tests: `tests/test_inter_substrate_diplomacy_observe.py`, `tests/test_inter_substrate_diplomacy_adopt.py`

## Acceptance criteria

- [ ] Async entry points (or `asyncio.to_thread` wrappers) for the chosen observe/adopt handlers used by operator API routes
- [ ] Existing pytest suite passes unchanged (behavior parity)
- [ ] `python tools/governance/run_inter_substrate_diplomacy_body_verification.py` → PASS
- [ ] PR notes any latency/concurrency assumptions

## Onboarding

- Mock mode: `.\scripts\start-infinity1.ps1` (see README **How to join in 10 minutes**)
- Arc context: `docs/runtime/AAIS_CIVILIZATIONAL_STAGES.md` (Stage 15)

## Labels

`good first issue`, `help wanted`, `python`, `governance`, `civilizational-arc`
