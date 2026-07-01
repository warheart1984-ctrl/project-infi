## Summary

Add a **CI-friendly smoke** target that runs the smallest civilizational arc pytest subset (fast PR signal for co-builders).

## Scope (bite-sized)

- Extend Makefile or document a one-liner already in `docs/audit/CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md`
- Optional: wire into an existing workflow as a non-blocking job or document as required local check

## Acceptance criteria

- [ ] `make civilizational-arc-smoke` (or equivalent) runs ≤2 min on laptop
- [ ] CONTRIBUTING.md lists when to run it
- [ ] Does not duplicate full flagship verification on every PR unless agreed

## Labels

`good first issue`, `help wanted`, `python`, `governance`
