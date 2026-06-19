# Continuity Reputation v1 — Formal Specification

This document is the canonical v1 specification for continuity-grade reputation.
Runtime implementation lives in [`../../src/continuity/`](../../src/continuity/).

Related contracts:

- [`CONTINUITY_PROOF_CVR.md`](CONTINUITY_PROOF_CVR.md) — implementation contract
- [`CCS_CORE_SCHEMA.md`](CCS_CORE_SCHEMA.md) — CCS object schema
- [`CAB_CONTINUITY_ARCHITECTURE_BLUEPRINT.md`](CAB_CONTINUITY_ARCHITECTURE_BLUEPRINT.md) - CAB lineage layer above CCS / Proof / CVR
- [`../../schemas/continuity_governance.v1.json`](../../schemas/continuity_governance.v1.json)
- [`../../schemas/cab.v1.json`](../../schemas/cab.v1.json)

Executable harness:

- [`../../tests/test_continuity_reputation_v1.py`](../../tests/test_continuity_reputation_v1.py)
- [`../../tests/test_ccs_continuity_harness.py`](../../tests/test_ccs_continuity_harness.py)
- [`../../tests/test_cab_blueprint.py`](../../tests/test_cab_blueprint.py)

Fixtures:

- River bend scenario: [`../../fixtures/ccs/river_bend_scenario.v1.json`](../../fixtures/ccs/river_bend_scenario.v1.json)
- Chiwere lexeme scenario: [`../../fixtures/ccs/chiwere_lexeme_scenario.v1.json`](../../fixtures/ccs/chiwere_lexeme_scenario.v1.json)
- CVR examples: [`../../fixtures/continuity/cvr_researcher_a.v1.yaml`](../../fixtures/continuity/cvr_researcher_a.v1.yaml), [`../../fixtures/continuity/cvr_contributor_b.v1.yaml`](../../fixtures/continuity/cvr_contributor_b.v1.yaml)

## 1. Purpose

Define a continuity-grade reputation system where:

1. **Proof is a trace**, not a label.
2. **Reputation** is derived from replay-stable continuity evidence, not social signals.
3. **UGR invariants** govern the entire proof pipeline.
4. **POD, CCS, and ContinuityTrace** form a single continuity substrate.

## 2. Core objects

### 2.1 ContinuityTrace (v1 projection)

Formal v1 fields (projected from CCS `ContinuityTrace` via `project_trace_v1()`):

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | string | Canonical trace identifier |
| `subject_ref` | string | Discovery / claim / decision / lexeme |
| `identity_refs` | string[] | Referenced identities |
| `event_refs` | string[] | Referenced events |
| `evaluation_refs` | string[] | Referenced evaluations |
| `evidence_refs` | string[] | Referenced evidence |
| `metrics_ref` | string | ContinuityMetrics identifier |
| `law_surfaces` | string[] | Flattened law surface refs |
| `trace_hash` | string | SHA-256 of canonical trace payload |
| `created_at` | timestamp | Trace creation time |

**Validity:**

```text
Valid(ContinuityTrace) ⇔
  IdentityContinuity(CT)
  ∧ AuthorityContinuity(CT)
  ∧ Duality(CT)
  ∧ SymmetricConstraints(CT)
  ∧ EvidenceIntegrity(CT)
  ∧ LawSurfaceBinding(CT)
  ∧ ContinuityUnifier(CT)
```

Implementation: `src/continuity/ugr_trace.py` — `valid_continuity_trace()`.

### 2.2 Proof

| Field | Type |
|-------|------|
| `proof_id` | string |
| `subject_ref` | string |
| `continuity_trace_ref` | string |
| `law_surfaces` | string[] — must include `ugr.continuity` and `aais.proof` |
| `status` | `PROVEN` \| `REVOKED` \| `PENDING` |
| `created_at` | timestamp |
| `updated_at` | timestamp |

**Validity:**

```text
Valid(Proof) ⇔
  Valid(ContinuityTrace)
  ∧ Replay(ContinuityTrace) == ContinuityTrace
  ∧ Proof.law_surfaces ⊇ {ugr.continuity, aais.proof}
```

Implementation: `src/continuity/proof.py` — `valid_proof()`.

### 2.3 ContinuityValidatedReputation (CVR)

| Field | Type |
|-------|------|
| `cvr_id` | string |
| `subject_id` | string |
| `scope.from` / `scope.to` | timestamp |
| `scope.domains` | string[] |
| `basis.proofs` | string[] |
| `basis.traces` | string[] |
| `metrics.*` | counts and averages |
| `derived_score` | number |
| `law_surfaces` | string[] |
| `last_recomputed_at` | timestamp |

**Reputation function (governance-tunable):**

```text
derived_score =
  α * (proofs_replay_stable / max(1, proofs_count))
+ β * continuity_score_avg
+ γ * evidence_integrity_avg
+ δ * authority_chain_strength_avg
- ε * revoked_proofs
```

Default weights (`ReputationWeights`): α=0.35, β=0.25, γ=0.25, δ=0.15, ε=0.05.

Example preset (`EXAMPLE_REPUTATION_WEIGHTS`): α=0.32, β=0.25, γ=0.25, δ=0.15, ε=0.05 — calibrates toward formal worked examples (researcher A ≈ 0.92, contributor B < researcher).

Implementation: `src/continuity/reputation.py` — `compute_derived_score()`, `compute_cvr()`.

`ContinuityReputation` is an alias for `ContinuityValidatedReputation`.

## 3. Pipeline and binding

```text
Discovery → Evidence → Evaluation → ContinuityTrace → Proof → CVR
```

UGR enforcement at each stage. UGR is the **gate**, not commentary.

Implementation: `src/continuity/pipeline.py` — `run_proof_pipeline()`.

## 4. Substrate unification

```yaml
ContinuitySubstrate:
  pod_layer:
    decisions: [POD.DecisionRef]
  ccs_layer:
    identities: [IdentityRecordRef]
    events: [EventRef]
    evaluations: [EvaluationRef]
    evidence: [EvidenceRef]
  trace_layer:
    traces: [ContinuityTraceRef]
  invariants:
    - ugr.identity_continuity
    - ugr.authority_continuity
    - ugr.evidence_integrity
    - ugr.law_surface_binding
    - ugr.continuity_unifier
```

**Rule:** Every POD decision that matters must have CCS Event + Evaluation + Evidence and at least one valid ContinuityTrace.

Implementation: `src/continuity/substrate.py`.

## 5. Governance stack

```text
[ POD Layer ] → decisions, actions, discoveries
[ CCS Layer ] → Identities, Events, Evaluations, Evidence, Metrics
[ ContinuityTrace ] → UGR enforced, replay-stable
[ Proof ] → PROVEN / REVOKED / PENDING
[ CVR ] → continuity-grade reputation
```

UGR invariants wrap the entire vertical stack.

## 6. Worked example — Chiwere lexeme LEX-0001

End-to-end scenario: [`../../fixtures/ccs/chiwere_lexeme_scenario.v1.json`](../../fixtures/ccs/chiwere_lexeme_scenario.v1.json)

Pipeline:

1. **Discovery** — `disc.chiwere.lexeme.0001` / subject `LEX-0001`
2. **Evidence** — recording + transcription with SHA-256 hashes
3. **CCS** — speaker, collector, cultural council, AAIS law engine identities
4. **ContinuityTrace** — `ct.lexeme.chiwere.0001` with metrics `metrics.lexeme.chiwere.0001`
5. **Proof** — `proof.lexeme.chiwere.0001`, status `PROVEN`
6. **CVR** — Researcher A reputation updated via `compute_cvr()`

Test: `test_chiwere_lexeme_end_to_end` in `test_continuity_reputation_v1.py`.

## 7. Substrate invariant test suite

| ID | Category | Test |
|----|----------|------|
| IC-1 | Identity | Display name change does not break trace |
| IC-2 | Identity | Duplicate identity ID rejected |
| IC-3 | Identity | Removed identity invalidates trace |
| AC-1 | Authority | Missing evaluator fails authority continuity |
| AC-2 | Authority | Conflicting evaluations remain distinct |
| AC-3 | Authority | Superseding trace preserves historical trace |
| DS-1 | Duality | Evidence ref normalization roundtrip |
| DS-2 | Duality | Replay preserves evidence IDs |
| DS-3 | Duality | Forward/reverse provenance same fingerprint |
| EI-1 | Evidence | Tampered hash detectable |
| EI-2 | Evidence | Removed evidence breaks trace |
| EI-3 | Evidence | Stored hash matches canonical value |
| LS-1 | Law surface | Evaluation without law surface fails |
| LS-2 | Law surface | Law surface change alters trace hash |
| LS-3 | Law surface | Proof without `ugr.continuity` invalid |
| CU-1 | Unifier | All invariants pass → PROVEN |
| CU-2 | Unifier | Single failure blocks PROVEN |
| CU-3 | Unifier | Fix + replay → valid proof |

Run:

```bash
pytest tests/test_continuity_reputation_v1.py -q
```

## 8. CVR example objects

- Researcher A (stable proofs): [`cvr_researcher_a.v1.yaml`](../../fixtures/continuity/cvr_researcher_a.v1.yaml) — `derived_score ≈ 0.92`
- Contributor B (revoked proof): [`cvr_contributor_b.v1.yaml`](../../fixtures/continuity/cvr_contributor_b.v1.yaml) — `derived_score ≈ 0.63`

Tests verify these against `EXAMPLE_REPUTATION_WEIGHTS`.

## 9. Nova lawful-turn CVR recompute

Every successful `LawfulLLM.ask()` turn runs the proof pipeline and recomputes CVR before the Voss receipt is signed:

```text
RSL + Nova Cortex + UGR invariants
  → CVRRegistry.record_lawful_turn()
  → ContinuityTrace + Proof + CVR
  → continuity_governance on signed receipt
```

Implementation: [`../../nova/governance/cvr_recompute.py`](../../nova/governance/cvr_recompute.py), wired in [`../../nova/lawful_llm.py`](../../nova/lawful_llm.py).

Receipt field `continuity_governance` contains:

| Key | Object |
|-----|--------|
| `proof` | Trace-backed `Proof` for this turn |
| `cvr` | Recomputed `ContinuityValidatedReputation` for the Nova instance |
| `continuity_trace` | v1 `ContinuityTrace` projection |
| `continuity_metrics` | Per-turn `ContinuityMetrics` |

Environment:

- `NOVA_CVR_STORE` — optional JSONL path for durable proof accumulation (default: `data/nova_cvr_store.jsonl` under `LAWFUL_NOVA_REPO_ROOT`, else `~/.nova/cvr_store.jsonl`)

Tests: `test_lawful_turn_recomputes_cvr`, `test_cvr_accumulates_across_turns` in `test_lawful_nova_lsg.py`.

Schema: `ContinuityGovernanceReceipt`, `ContinuityTraceV1`, and `ContinuityMetrics` in [`../../schemas/continuity_governance.v1.json`](../../schemas/continuity_governance.v1.json).

## 10. CAB lineage layer

CAB (Continuity Architecture Blueprint) is the fifth pillar above the existing CCS -> Proof -> CVR stack. It does not replace trace, proof, or reputation objects; it preserves reconstructable lineage around them.

```text
CCS -> ContinuityTrace -> Proof -> CVR
  -> CAB ledger: IntentRecord -> DecisionRecord -> EvidenceChain -> ContinuityReceipt -> ReconstructionPlan
```

Runtime and adapter bindings:

| Source | CAB object(s) | Entry point |
|--------|---------------|-------------|
| Nova lawful turns | `ContinuityReceipt` | `ingest_nova_continuity_governance()` |
| CIEMS governed transforms | `EvidenceChain`, `DecisionRecord` | `ingest_ciems_transformation_event()` |
| NeoMundi measurements | `EvidenceChain` | `ingest_neomundi_measurement()` |
| ControlTower telemetry | CAB summary and invariants | ops-console `/telemetry` field `cab` |

Environment:

- `CAB_AUTO_INGEST` - when `1`, `true`, or `yes`, Nova CVR recompute appends lawful-turn CAB receipts.
- `CAB_STORE` - optional JSONL path for durable CAB ledger storage; default `~/.cab/ledger.jsonl`.

CAB invariants:

- `RC` reconstructability
- `CL` causal linkage
- `TI` temporal integrity
- `SU` succession
- `NE` non-erasure

Implementation: [`../../src/continuity/cab.py`](../../src/continuity/cab.py), [`../../src/continuity/cab_invariants.py`](../../src/continuity/cab_invariants.py).
