# Continuity OS — Runtime Specification

**Version:** 1.0  
**Status:** Normative

---

## 1. Core runtime objects

### Evidence

| Field | Type | Notes |
|-------|------|-------|
| `evidence_id` | string | Unique |
| `timestamp` | ISO-8601 | Capture time |
| `channel_id` | string | Source reality channel |
| `payload` | object | Normalized observation |
| `hash` | hex | Content address |
| `signature` | string | Optional cryptographic sign |

**Schema:** `fixtures/crk1/evidence_object.schema.json`, `v01/evidence.v01.schema.json`

### Expectation

| Field | Type |
|-------|------|
| `model_id` | string |
| `input_state` | object |
| `predicted_outcome` | any |
| `confidence` | number \| string |

### Contradiction

| Field | Type |
|-------|------|
| `contradiction_id` | string |
| `expectation_ref` | ref |
| `evidence_ref` | ref |
| `delta` | any |
| `surprise_intensity` | number \| string |

### Decision

| Field | Type |
|-------|------|
| `decision_id` | string |
| `steward_id` | string |
| `values` | object |
| `options` | array |
| `chosen_action` | string |
| `expected_outcomes` | array |

**Schema:** `fixtures/crk1/decision_object.schema.json`

### Outcome

| Field | Type |
|-------|------|
| `outcome_id` | string |
| `decision_ref` | ref |
| `observed_effects` | object |
| `time_horizon` | string |

### GRR-1

Governance Reconstruction Receipt — decision reconstruction.

**Schema:** `fixtures/crk1/governance_reconstruction_receipt.schema.json`

### CRR-1

Calibration Reconstruction Receipt — calibration reconstruction.

**Schema:** `fixtures/crk1/calibration_reconstruction_receipt.schema.json`

### CalibrationEvent

| Field | Type |
|-------|------|
| `crr_ref` | ref |
| `calibration_delta` | number \| string |
| `affected_models` | array |
| `invariant_implications` | array |

### Steward

| Field | Type |
|-------|------|
| `steward_id` | string |
| `role` | string |
| `authority_scope` | object |
| `SCT_scores` | object |
| `lineage_refs` | array |

---

## 2. Runtime loops

### Loop A — Reality → Evidence → Contradiction

1. `RealityChannel.observe()` → raw payload (via RIA)
2. ECE normalizes → **Evidence** (timestamp, hash, sign)
3. CD matches Evidence vs **Expectation** → **Contradiction** if delta exceeds threshold

### Loop B — Contradiction → Correction → Calibration

1. Contradiction triggers update in **Judgment Engine**
2. Generate **CRR-1** + **CalibrationEvent**
3. Update models, assumptions, confidence
4. Ingest into **CLG-1**

### Loop C — Decision → Outcome → GRR

1. JE + CRK-1 produce **Decision** (governed, receipted)
2. Outcome observed → **Outcome**
3. Generate **GRR-1** linking decision, outcome, values, tradeoffs

### Loop D — Lineage & Continuity

1. CTE ingests GRR-1 + CRR-1 → CLG-1
2. CME computes RAI, CFE, drift metrics
3. CFM monitors for continuity failure regimes

---

## 3. Governance commit loop (CRK-1)

```
verify(receipt) → anchor(index, merkle) → apply(action)
```

No constitutional mutation without valid receipt. Reference: `src/crk1/crk1_governance_engine.py`.

---

## 4. Implementation anchors

| Loop | Reference code |
|------|----------------|
| A | `runtime_facade.create_evidence`, consequence lattice |
| B | CRR schema (normative); partial — judgment trace |
| C | `governance_engine`, GRR schema |
| D | `governance_receipt_merkleizer`, drift simulator |

See: [../CRK1_MINIMAL_RUNTIME_RFC.md](../CRK1_MINIMAL_RUNTIME_RFC.md)
