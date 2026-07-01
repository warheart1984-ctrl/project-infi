## Summary

Review and **harden constitutional evolution** proof coverage — tighten tests, registry validation, and body verification gate so Stage 16 claims stay `proven` under regression.

## Scope (bite-sized)

- `src/constitutional_evolution_runtime.py`, `src/constitutional_evolution_registry.py`
- Tests: `tests/test_constitutional_evolution_observe.py`, `tests/test_constitutional_evolution_adopt.py`
- Gate: `tools/governance/run_constitutional_evolution_body_verification.py`
- Reference: `docs/audit/CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md`

## Acceptance criteria

- [ ] Add or strengthen negative tests (dual-gate blocks, invalid amendment schema)
- [ ] Document proof commands in PR body
- [ ] Body verification gate passes locally
- [ ] No weakening of `operator_approved` / Jarvis authority seams

## Onboarding

- Read `REPO_PROOF_LAW.md` and `META_ARCHITECT_LAWBOOK.md` before changing gates

## Labels

`help wanted`, `python`, `governance`, `civilizational-arc`
