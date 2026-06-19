# Continuity Proof and CVR Contract v1

This contract formalizes the governance stack:

```text
UGR (invariants)
  ↓
ContinuitySubstrate (POD + CCS + Trace)
  ↓
ContinuityTrace (replay-stable continuity object)
  ↓
Proof (trace-backed validity)
  ↓
CVR (continuity-validated reputation)
```

Machine-readable schema:
[`../../schemas/continuity_governance.v1.json`](../../schemas/continuity_governance.v1.json)

CCS core objects remain defined in
[`CCS_CORE_SCHEMA.md`](CCS_CORE_SCHEMA.md) and
[`../../schemas/ccs_core_objects.v1.json`](../../schemas/ccs_core_objects.v1.json).

Executable harness:
[`../../tests/test_ccs_continuity_harness.py`](../../tests/test_ccs_continuity_harness.py)

Example fixtures:
[`../../fixtures/continuity/`](../../fixtures/continuity/)

Link to formal v1 spec: [`CONTINUITY_REPUTATION_V1.md`](CONTINUITY_REPUTATION_V1.md)

## I. Proof → ContinuityTrace binding

Proof is not a label. Proof is a trace.

A discovery is **proven** iff it has a valid, replay-stable `ContinuityTrace`.

### Proof object

| Field | Type | Purpose |
|-------|------|---------|
| `proof_id` | string | Unique proof identifier |
| `subject_ref` | string | Discovery / claim / result reference |
| `continuity_trace_ref` | string | `ContinuityTrace.id` |
| `law_surfaces` | string[] | e.g. `ugr.continuity`, `aais.proof` |
| `status` | `PROVEN` \| `REVOKED` \| `PENDING` | Proof lifecycle |
| `created_at` | timestamp | Creation time |
| `updated_at` | timestamp | Last mutation time |

### Validity rule

```text
Valid(Proof) ⇔
  Valid(ContinuityTrace)
  ∧ Replay(ContinuityTrace) == ContinuityTrace
  ∧ All(UGR invariants satisfied)
```

Revoking proof invalidates the proof object. The underlying trace may be
superseded separately.

Implementation: `src/continuity/proof.py` — `create_proof()`, `valid_proof()`,
`revoke_proof()`.

## II. Continuity-grade reputation

Reputation is continuity-anchored, not social.

```text
derived_score = f(
  proofs_count,
  proofs_replay_stable,
  revoked_proofs,
  continuity_score_avg,
  evidence_integrity_avg,
  authority_chain_strength_avg
)
```

Properties:

- No proof → `derived_score = 0`
- Revoked proofs reduce score
- Replay-stable proofs increase score
- Evidence and authority quality shape the score

`ContinuityValidatedReputation` (CVR) is the first-class object. `ContinuityReputation`
is an alias for the same structure.

Implementation: `src/continuity/reputation.py` — `compute_cvr()`,
`compute_derived_score()`.

## III. UGR inside the proof pipeline

Pipeline stages:

```text
Discovery → Evidence → Evaluation → ContinuityTrace → Proof → CVR
```

UGR enforcement attaches at each stage. ContinuityTrace validity is the gate
for Proof:

```text
Valid(ContinuityTrace) ⇔
  IdentityContinuity(CT)
  ∧ AuthorityContinuity(CT)
  ∧ Duality(CT)
  ∧ SymmetricConstraints(CT)
  ∧ EvidenceIntegrity(CT)
  ∧ LawSurfaceBinding(CT)
  ∧ ContinuityUnifier(CT)

Valid(Proof) ⇔ Valid(ContinuityTrace)
```

Implementation: `src/continuity/ugr_trace.py`, `src/continuity/pipeline.py`.

## IV. ContinuitySubstrate

Three layers unify into one substrate:

| Layer | Contents |
|-------|----------|
| POD | Lived decisions (`PODDecision`) |
| CCS | Identity, Event, Evaluation, Evidence |
| Trace | ContinuityTrace references |

Binding rule:

```text
POD.Decision
  → CCS.Event + CCS.Evaluation + CCS.Evidence
  → ContinuityTrace(decision)
```

Substrate rule: every POD decision that matters must have CCS representation and
at least one ContinuityTrace.

Implementation: `src/continuity/substrate.py` — `ContinuitySubstrate`,
`bind_pod_decision()`, `validate_substrate()`.

## V. CVR definition

CVR = the portion of contributions that remain replay-stable, evidence-anchored,
authority-consistent, and continuity-valid.

CVR properties:

- Evidence-anchored (explicit Proof and ContinuityTrace basis)
- Replay-sensitive (recomputed when replay fails)
- Revocation-aware
- Domain-scoped
- Non-social (no likes, follows, or popularity)
- Continuity-governed (`ugr.continuity`, `aais.reputation`)

## VI. Relationship to lawful Nova

The lawful Nova slice (`nova/governance/ugr_invariants.py`) enforces the same
seven UGR invariants on per-turn receipts. This contract extends that spine to
CCS `ContinuityTrace` objects, Proof binding, and CVR aggregation.

Scope boundary: this contract does not wire the full `src/ugr/` mission runtime
to lawful Nova or CCS stores. It provides the formal objects and Python runtime
for empirical validation.

## Verification

From repo root:

```bash
pytest tests/test_ccs_continuity_harness.py -q
```

Expected: all tests pass, including proof validity, revocation, CVR scoring, and
end-to-end pipeline stages.
