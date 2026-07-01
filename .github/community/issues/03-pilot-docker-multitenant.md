## Summary

Improve **Infinity Pilot Docker** setup for **multi-tenant** early adopters — clearer env vars, compose profiles, and smoke checks.

## Scope (bite-sized)

- `deploy/pilot/docker-compose.yml`
- Docs: `docs/operations/INFINITY_PILOT_EARLY_ADOPTER.md`, `docs/baseline/INFINITY_PILOT_BASELINE_CHECKLIST.md`
- Related: `docs/contracts/MEMORY_VECTOR_BACKEND_FIREBASE_ADMISSION.md` (`AAIS_VECTOR_TENANT_ID`)

## Acceptance criteria

- [ ] Document tenant isolation knobs (env + data dirs) in pilot guide
- [ ] Optional compose profile or example `.env.pilot.example` for second tenant
- [ ] Smoke command documented (health + operator dashboard)
- [ ] No secrets committed

## Onboarding

- Start locally in mock mode first; pilot path is optional follow-on

## Labels

`good first issue`, `help wanted`, `docker`, `documentation`
