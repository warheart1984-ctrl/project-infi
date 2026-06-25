# Constitutional Cockpit — Operator Guide

The cockpit is **constitutional application space (userland)**. It does not define kernel objects.

**Kernel (CRK-1):** Identity, Evidence, Decision, Resource, Outcome + four contracts + transitions.

**Userland (CRK-T1):** fitness projections, panels, dashboards, and operator tools expressed *over* those objects.

See [UGR-CRK-T1 — Constitutional Sufficiency](../../contracts/UGR-CRK-T1-Constitutional-Sufficiency.md).

---

## Fitness panels (not kernel objects)

| Panel | Former name | What it measures |
|-------|-------------|------------------|
| Comprehension Fitness | CITStrip | Explanation invariance over object graphs (Χ) |
| Meaning Fitness | MeaningStrip | Shared interpretation over evidence/outcomes (Μ) |
| Evidence Fitness | EITStrip | Provenance and convergence (Ω) |
| Outcome Variance | OutcomeStrip | Expected vs observed reality feedback |
| Attention Allocation Fitness | Attention Rail | ResourceObject allocations (especially attention) |
| Constitutional Fitness Summary | Spine Health / H= | Aggregated fitness gate for epoch commit |

Structural, generative, and proof panels (SIT, GIT, PIT) are additional **fitness functionals** in userland — not kernel primitives.

---

## API routes (CRK-T1 aligned)

| Fitness | Preferred route | Legacy alias |
|---------|-----------------|--------------|
| Comprehension | `GET /api/fitness/comprehension/law/<law_id>` | `GET /api/cit/law/<law_id>` |
| Meaning | `GET /api/fitness/meaning/law/<law_id>` | `GET /api/mit/law/<law_id>` |
| Evidence | `GET /api/fitness/evidence/law/<law_id>` | `GET /api/eit/law/<law_id>` |
| Evidence (by id) | `GET /api/fitness/evidence/evidence/<evidence_id>` | `GET /api/eit/evidence/<evidence_id>` |
| Outcome variance | `GET /api/fitness/outcome/<outcome_id>` | `GET /api/outcomes/<outcome_id>` |
| Outcome by decision | `GET /api/fitness/outcome/decision/<decision_id>` | `GET /api/outcome/decision/<decision_id>` |
| Attention allocation | `GET /api/fitness/attention` | — |

Kernel object routes (`/api/decisions`, `/api/laws`, `/api/evidence`, `/api/pods`) remain separate from fitness routes.

---

## Sufficiency test for new features

Before adding cockpit capability, ask:

> Can this be expressed purely in terms of the five objects + four contracts + transitions?

- **Yes** → implement as fitness, projection, or policy in userland.
- **No** → propose a CRK-2+ kernel amendment.

---

## Compliance

- Static: `python tools/check_crk1_compliance.py`
- Runtime: `check_crk1_invariants()` on `ConstitutionalRuntime` init (logs `CRK-1-COMPLIANT: true/false`)
- Tests: `tests/crk1_boundary/`
