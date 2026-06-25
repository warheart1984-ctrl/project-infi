# UGR-PIT-2 — Persistence Under Reality Feedback

**Class:** Constitutional Invariant (Persistence Layer)

## PIT-2.1 — Purpose

Ensure law and policy persistence is conditioned on performance in reality, not only internal coherence.

## PIT-2.2 — Domain

- Let **L** be laws.
- Let **O** be outcomes.
- Let **F_p(ℓ, t)** be persistence fitness for law ℓ at epoch t.

## PIT-2.3 — Statement

**Outcome-conditioned fitness:**

F_p(ℓ, t+1) = f(F_p(ℓ, t), { o ∈ O : o depends on ℓ })

where **f** incorporates variance classification from OutcomeObjects.

**Persistence threshold:** A law remains admissible only if F_p(ℓ, t) ≥ Θ_PIT.

**Reality supremacy:** Repeated contradiction of intended effect forces review or retirement.

## PIT-2.4 — Role

PIT-2 binds law persistence to reality feedback via OutcomeObjects and `compute_outcome_drift()`.

**Implementation:** `src/continuity/outcome_fitness.py`, integrated in `build_spine_health()`
