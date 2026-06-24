# CRK-1.K0–K3 — Consequence Transmission Kernel

Formal kernel laws ensuring judgment remains structurally exposed to the consequences of its own decisions.

## CRK-1.K0 — Consequence Transmission Kernel

**Claim:** If Identity, Evidence, Decision, Resource, and Outcome objects exist with replayable transitions, then any constitutional system that (a) ingests Evidence, (b) commits Decisions, (c) allocates Resources, and (d) records Outcomes is necessarily a consequence transmission system — provided no transition can bypass Outcome→Evidence replay.

### Objects

| Object | Type |
|--------|------|
| Identity | `IdentityObject` |
| Evidence | `EvidenceObject` |
| Decision | `DecisionObject` |
| Resource | `ResourceObject` |
| Outcome | `OutcomeObject` |

### Required Transitions

| Transition | Signature |
|------------|-----------|
| ProposeDecision | `(Identity, Evidence) → Decision` |
| AllocateResource | `(Decision, Resource) → Resource` |
| ExecuteDecision | `(Decision, Resource) → Outcome` |
| ReplayOutcome | `(Outcome) → Evidence'` |

### Invariant K0.1

For every Decision `d`, if `d` is executed, there exists at least one Outcome `o` and at least one Evidence `e'` such that:

```
Execute(d) ⇒ ∃o,e': Outcome(o) ∧ Replay(o) ⇒ Evidence(e')
```

**No execution without a replayable consequence.**

Runtime: `validateK01()`, `runConsequencePipeline()`

## CRK-1.K1 — Immutable Exposure Constraint

**Claim:** A constitutional runtime preserves continuity only if no valid state transition can permanently sever:

```
Decision → Outcome → Evidence → Future Decision
```

### Constraint K1.1 (No-Severability)

For all valid transitions `T`:

```
T is valid ⇒ ¬Sever(Decision, Outcome, Evidence)
```

Where **Sever** means:

- Dropping Outcomes (unrecorded execution)
- Blocking Replay (Outcome not admissible as Evidence)
- Quarantining Evidence (Evidence not admissible to future Decisions)

If a proposed transition would do any of the above, it is **constitutionally invalid**, regardless of local policy.

Runtime: `validateTransitionK11()`, `validateObjectK11()`, throws in `executeDecision()` / `replayOutcome()` / `proposeDecision()`

## CRK-1.K2 — Judgment-Consequence Coupling Law

**Claim:** Judgment is only legitimate if it is structurally exposed to the consequences of its own Decisions.

### Coupling Law K2.1 (Cost Binding)

For every Decision `d` authorized by Identity `i`:

```
Authorize(i,d) ⇒ ∃o,e': Outcome(o,d) ∧ Replay(o) ⇒ Evidence(e') ∧ Affects(i, e')
```

Where **Affects(i, e')** means:

- `e'` is admissible as input to future Decisions by `i` or its successors in the Stewardship chain
- `i` (or its lineage) cannot mark `e'` as irrelevant, non-binding, or invisible

**Intuition:** You don't get to decide and then hide from what happened.

Runtime: `validateK21()`, `replayOutcome({ affectsLineageId })`

## CRK-1.K3 — Anti-Insulation Proof

**Goal:** Under K0, K1, and K2, no constitutional system can evolve a valid insulated state.

### Insulated State S*

A state where there exists Decision `d` such that `Execute(d) ⇒ Outcome(o)` but replayed evidence cannot affect the Judgment lineage that authorized `d`.

### Proof Sketch

1. By **K0**, `Replay(o)` must yield Evidence `e'`.
2. By **K1**, no valid transition can prevent `e'` from being admissible.
3. By **K2**, `e'` must affect the Judgment lineage that authorized `d`.

Therefore any insulated state violates K0, K1, or K2 — **insulation is logically outside the constitutional runtime**.

Runtime: `detectInsulatedDecisions()`, `proveAntiInsulation()`, `K3_PROOF_STEPS`

## Module Map

| Module | Purpose |
|--------|---------|
| `crk1/consequence-kernel.ts` | Objects + transition functions |
| `crk1/consequence-ledger.ts` | `ConsequenceLedger`, `InMemoryConsequenceLedger` |
| `crk1/consequence-invariants.ts` | K0, K1, K2 validators |
| `crk1/anti-insulation.ts` | K3 detection + proof |
| `crk1/consequence-pipeline.ts` | Full pipeline orchestration |

## Related

- [CRK-1 Legitimate Judgment](./CRK-1-WHITEPAPER-LEGITIMATE-JUDGMENT.md)
- [Constitutional Stack](./CONSTITUTIONAL-STACK.md)
- [Sound Judgment Cycle](./SOUND-JUDGMENT-CYCLE.md)
