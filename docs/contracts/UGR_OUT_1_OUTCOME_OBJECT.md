# UGR-OUT-1 — Outcome Object

**Class:** Constitutional Object

## OUT-1.1 — Purpose

Encode what reality actually did in response to a lawful decision, and feed variance and lessons back into the constitutional spine.

## OUT-1.2 — Domain

- Let **D** be the set of DecisionObjects.
- Let **O** be the set of OutcomeObjects.
- Each **o ∈ O** links to exactly one **d ∈ D**.

## OUT-1.3 — Structure

An OutcomeObject MUST contain:

- Unique `id`
- `decision_id ∈ D`
- `expected` (description + metrics)
- `observed` (description + metrics)
- `variance` (metric deltas + classification)
- `lessons[]`
- `epoch`
- `timestamp`
- `status ∈ {recorded, disputed, superseded}`

## OUT-1.4 — Invariants

**Linkage:** Every OutcomeObject MUST reference a valid DecisionObject.

**Immutability:** `expected` and `observed` MUST NOT be mutated after recording except via explicit supersession.

**Variance classification:** Every outcome MUST be classified as `acceptable`, `concerning`, or `critical`.

## OUT-1.5 — Role

OutcomeObjects are the sole canonical record of reality in the constitutional runtime.

**Implementation:** `src/continuity/outcome_ledger.py`, schema `fixtures/continuity/outcome_record.schema.json`
