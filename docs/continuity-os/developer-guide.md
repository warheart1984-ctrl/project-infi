# Continuity OS Developer Guide

**Audience:** Engineers integrating models, agents, or systems into Continuity OS.  
**Goal:** Make corrigibility and lineage a **runtime property**, not an afterthought.

---

## 1. Overview

Continuity OS wraps judgment in a constitutional loop:

1. Emit **expectations** and **governance receipts** before acting.
2. Admit **evidence** from reality channels without insulation.
3. Route **contradictions** through CE-1 (surprise → correction).
4. Preserve **CRR-1** receipts and ingest into **CLG-1** lineage.

If any step is skipped, future stewards cannot reconstruct why judgment changed.

**Prerequisites:** Python 3.11+, `project-infi` installed (`uv sync` or `pip install -e .`).

---

## 2. Core Concepts

| Symbol | Role |
|--------|------|
| **K-∞** | Prime directive — reality must always be able to recalibrate future judgment |
| **CK-1** | Continuity Kernel — six invariants (evidence, contradiction, corrigibility, correction, lineage, reality channels) |
| **CRK-1** | Constitutional runtime — governance gate, GRR-1, challenge surfaces (KΩ) |
| **CE-1** | Correction engine — F1 contradiction → F2 surprise → F3–F5 correction + calibration delta |
| **CLG-1** | Calibration lineage graph — persistent tree of `CalibrationEvent` nodes |
| **GRR-1** | Governance receipt — *why we thought this* (decision / expectation commitment) |
| **CRR-1** | Calibration reconstruction receipt — *why we stopped thinking this* |
| **Steward** | Any entity (human, LLM, agent) bound to emit honestly and accept correction |

Deep specs: [Book of Invariants](invariants/book-of-invariants.md) · [Architecture index](architecture/ck1-kernel.md)

---

## 3. Minimal Integration Path

### Step 1 — Wrap your model with `LawfulLLMAdapter`

```python
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(
    FallingObjectModel(),
    steward_id="my_service_v1",
    channel_id="gravity.local",
)
```

The adapter routes all interactions through CRK-1 (GRR header), CK-1 calibration, and CLG-1 ingest.

### Step 2 — Emit expectations and evidence as objects

```python
exp = adapter.predict("Predict fall time for 2m drop.")
# ExpectationObject: expected_outcome, expected_confidence, assumptions, id

evidence = adapter.observe({
    "value": 0.3,
    "strength": 1.0,
    "channel": "gravity.local",
})
# EvidenceObject: observed_outcome, channel_id, evidence_strength, id
```

Never pass raw floats alone — always wrap in typed objects so CE-1 can link refs.

### Step 3 — Route contradictions through CE-1

```python
correction, crr1 = adapter.correct(exp, evidence)
```

Internally: `CorrectionEngineCE1.run_from_objects()` → contradiction, surprise, correction delta.

### Step 4 — Build CRR-1 via `build_crr1()`

`adapter.correct()` already returns a wire-format CRR-1 dict. To build from pipeline output explicitly:

```python
from src.crk1.crr1_builder import build_crr1

crr1 = build_crr1(ce1_result)  # CE1PipelineResult or CalibrationResult
```

Validate against `fixtures/crk1/calibration_reconstruction_receipt.schema.json`.

### Step 5 — Ingest into CLG-1 via `CLG1Ingestion`

```python
from src.crk1.clg1_store import CLG1Store
from src.crk1.clg1_ingestion import CLG1Ingestion

store = CLG1Store()
ingestion = CLG1Ingestion(store)
event_id = ingestion.ingest_crr1(crr1)
```

Or use the high-level graph (adapter does this automatically):

```python
from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1

clg = CalibrationLineageGraphCLG1()
clg.ingest_crr(crr1, event=calibration_event)
```

**One-liner demo:**

```bash
continuity demo falling-object
```

---

## 4. Data Structures

| Type | Purpose | Key fields |
|------|---------|------------|
| `ExpectationObject` | Committed prediction | `expected_outcome`, `expected_confidence`, `assumptions`, `id` |
| `EvidenceObject` | Reality observation | `observed_outcome`, `channel_id`, `evidence_strength`, `expectation_ref` |
| `ContradictionObject` | Mismatch record | `contradiction_delta`, `prediction_error_vector` |
| `SurpriseObject` | Magnitude of mismatch | `surprise_magnitude` |
| `CorrectionObject` | Applied shift | `model_shift`, links to contradiction |
| `CalibrationResult` | Pipeline bundle | expectation + evidence + correction + event |
| **CRR-1** | Wire receipt (flat dict) | `receipt_type`, `steward_id`, `expected_outcome`, `observed_outcome`, `contradiction_delta`, `calibration_delta`, `links` |

Reference: [Data Structures](../reference/data-structures.md) · [Receipts](../reference/receipts.md)

---

## 5. Governance Hooks

### Where to emit GRR-1

Emit a governance receipt **before** any externally visible decision:

```python
decision, grr = adapter.ask("What action should we take?")
# grr: GovernanceReceiptHeader — attach to audit log, API response meta, or CLG decision node
```

In custom agents: call `GovernanceReceiptHeader.from_decision()` after every tool invocation that affects the world.

### Steward IDs

- Use stable, namespaced IDs: `org/service/instance` (e.g. `acme/ranking/v3`).
- Never reuse IDs across principals — lineage queries depend on steward identity.
- Human stewards: tie to auth subject; agents: tie to deployment revision.

### Challenge surfaces (KΩ)

Expose:

- Expectation + confidence at decision time
- Evidence refs and channel IDs at observation time
- CRR-1 hash or ID after correction

Third parties (or future you) must be able to challenge without privileged logs.

---

## 6. Lineage Queries

CLG-1 supports steward-, decision-, and time-scoped queries. See [Lineage Queries](../reference/lineage-queries.md).

| Question | Approach |
|----------|----------|
| All corrections for this steward | `CalibrationLineageGraphCLG1.query_by_steward(steward_id)` |
| All corrections for this decision | Filter `CalibrationEvent` nodes with `links.decision_id` |
| Calibration history over time | Order events by `timestamp_utc` on steward branch |

Mission #005 stress test (multi-steward shared graph):

```bash
continuity mission 005
```

---

## 7. Patterns & Anti-Patterns

### Good

- **Explicit expectations** — always emit `ExpectationObject` before observing.
- **Explicit evidence** — one channel per observation; no blended “ground truth.”
- **Explicit corrections** — every contradiction produces CRR-1 + CLG ingest.
- **Fail visible** — contradiction surfaces to steward UI, not silent weight nudges.

### Bad

- **Hidden heuristics** — post-hoc rules that never emit receipts.
- **Silent failures** — swallowing contradiction without CE-1.
- **Unlogged overrides** — human “fix” without CRR-1.
- **Erasing errors** — mutating or deleting lineage nodes (violates CK-1.5).

---

## 8. Example: Lawful LLM (end-to-end)

```python
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter, FallingObjectModel

adapter = LawfulLLMAdapter(FallingObjectModel(), steward_id="tutorial_steward")

# MVCD — full cycle in one call
correction, crr1 = adapter.run_falling_object_scenario()

print(crr1["contradiction_delta"])   # 0.7
print(crr1["calibration_delta"])     # 0.7
print(correction.correction_object.correction.model_shift)
```

Equivalent SDK import:

```python
from continuity_sdk.demos import run_falling_object_scenario

correction, crr1 = run_falling_object_scenario()
```

---

## Next steps

| Doc | Topic |
|-----|-------|
| [LawfulLLMAdapter](../continuity-sdk/lawful-llm-adapter.md) | SDK facade and CLI |
| [Building a Lawful Agent](../tutorials/building-a-lawful-agent.md) | Agent integration pattern |
| [Steward Certification](stewardship/steward-certification.md) | Level 1 literacy test |
| [Steward's Oath](stewardship/stewards-oath.md) | Constitutional commitment |
| [Your First Correction VR](../darz-vr/YOUR-FIRST-CORRECTION-VR-SCRIPT.md) | Narrative / DARZ-VR script |
