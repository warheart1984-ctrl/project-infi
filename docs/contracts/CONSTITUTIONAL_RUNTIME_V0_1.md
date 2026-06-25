# Constitutional Runtime v0.1

Frozen specification for the AAES OS constitutional kernel loop.

**Normative kernel spec:** [CRK-1 — Constitutional Runtime Kernel v0.1](CRK-1-Constitutional-Runtime-Kernel.md)  
**Kernel theorem:** [UGR-CRK-T1 — Constitutional Sufficiency](UGR-CRK-T1-Constitutional-Sufficiency.md)

## Core objects

| Object | Role |
|--------|------|
| **IdentityObject** | Mission, values, invariants, authority model |
| **EvidenceObject** | Claims backed by provenance (implemented as `EvidenceRecord`) |
| **DecisionObject** | Lawful intent with evidence refs and governance basis |
| **ResourceObject** | Allocations and attention as finite resources (`resource_ledger.py`) |
| **OutcomeObject** | Expected vs observed reality feedback |

## Core contracts

1. **Evidence Contract** — EIT-1/EIT-2 admissibility (`EvidenceContract`)
2. **Governance Contract** — authority + invariants (`GovernanceContract`)
3. **Resource Contract** — allocation realism + attention caps (`ResourceContract`)
4. **Runtime Contract** — spine health + epoch gating (`RuntimeContract`)

## Kernel loop

```
Identity → Evidence → Decision → Resource → Outcome → Epoch → fitness layers
```

Implementation: `src/continuity/constitutional_runtime.py`

## Spine health

`build_spine_health()` aggregates CIT, MIT, EIT, SIT, GIT, PIT, and **outcome drift (OIT)**.

Block reasons: `CIT-BLOCK`, `MIT-BLOCK`, `EIT-BLOCK`, `SIT-BLOCK`, `GIT-BLOCK`, `PIT-BLOCK`, `OIT-BLOCK`.

## Ledgers

| Ledger | Module | Fixture |
|--------|--------|---------|
| Decision | `decision_ledger.py` | `fixtures/continuity/decision_ledger.sql` |
| Outcome | `outcome_ledger.py` | `fixtures/continuity/outcome_ledger.sql` |
| Evidence | `evidence_ledger.py` | `fixtures/continuity/evidence_ledger.sql` |
| Law | `law_ledger.py` | `fixtures/continuity/law_ledger.sql` |

## UGR articles

- [CRK-1](CRK-1-Constitutional-Runtime-Kernel.md) — Constitutional Runtime Kernel (foundational)
- [UGR-OUT-1](UGR_OUT_1_OUTCOME_OBJECT.md) — OutcomeObject
- [UGR-PIT-2](UGR_PIT_2_PERSISTENCE_REALITY.md) — Persistence under reality feedback
- [UGR-RTC-1](UGR_RTC_1_RUNTIME_CONTRACT.md) — Runtime contract (epoch admissibility)

## Build order

1. Freeze object schemas (JSON in `fixtures/continuity/`)
2. Define contracts as code + UGR articles
3. Implement ledgers (SQLite)
4. Wire kernel state machine
5. Add spine health + cockpit surfaces
6. Hang agents and UI off the kernel

## Conformance

Property-based CRK-1 tests: `tests/crk1/`
