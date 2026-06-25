# UGR-RTC-1 — Runtime Contract

**Class:** Constitutional Contract

## RTC-1.1 — Purpose

Define conditions under which state transitions (epoch steps) are admissible.

## RTC-1.2 — Domain

- Let **Σ_t** be constitutional state at epoch t.
- Let **T** be admissible transitions Σ_t → Σ_{t+1}.

## RTC-1.3 — Admissible transition

A transition τ is admissible iff:

1. **Decision legitimacy** — executed decisions satisfy the Governance Contract.
2. **Evidence integrity** — evidence satisfies EIT-1/EIT-2.
3. **Outcome recording** — executed decisions produce OutcomeObjects.
4. **Spine health** — H_spine(Σ_{t+1}) ≥ Θ_spine (CIT, MIT, EIT, SIT, GIT, PIT, OIT).

## RTC-1.4 — Blocking

If any condition fails, τ MUST be rejected; the epoch MUST NOT advance.

## RTC-1.5 — Role

The Runtime Contract is the gate between “we tried” and “history changed.”

**Implementation:** `src/continuity/constitutional_runtime.py` (`ConstitutionalRuntime.advance_epoch()`)
