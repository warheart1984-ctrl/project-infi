# Nova Law Kernel v1.0

**Codename:** K_LAW  
**Target:** Nova v0.1 constitutional execution spine

## 1. Introduction

Nova Law Kernel (K_LAW) is the constitutional execution spine for Nova. Law is a **kernel**, not a policy layer: every intent must pass through governed evaluation before any substrate action occurs.

### Design goals

- **Governance-first** — no ungoverned actions (KLAW-1)
- **Fail-closed** — uncertainty defaults to deny or panic (KLAW-2)
- **Lineage-anchored** — every decision emits a lineage event (KLAW-5)
- **T5-bound** — every decision carries a reference signal hash and invariant proof (KLAW-4)

## 2. Architecture

```
Intent → LawContextResolver → LawKernel → LawEvalPayload
                ↓                              ↓
         T5ReferenceSignal              LineageStore (LAW_EVAL)
                ↓                              ↓
         LawfulIntentRouter ──→ admit | deny | transform | panic
                                      ↓
                            LawKernelPanicHandler (fail-closed)
```

### Core components

| Component | Module | Responsibility |
|-----------|--------|----------------|
| LawLedger | `law_ledger.py` | Append-only law store (KLAW-3) |
| LawContextResolver | `context_resolver.py` | Build `LawContext` with T5 + lineage binding |
| LawKernel | `kernel.py` | Evaluate laws; admit/deny/transform/panic |
| LawfulIntentRouter | `router.py` | No direct intent→substrate path (KLAW-1) |
| LawKernelPanicHandler | `panic_handler.py` | Freeze lane, emit panic lineage event |
| T5 Binding | `t5_binding.py` | `T5ReferenceSignal`, `InvariantLedger`, proofs |
| Lineage Integration | `lineage.py` | `LAW_EVAL` / `LAW_PANIC` events |

## 3. Invariants

### Kernel invariants (KLAW)

| ID | Statement |
|----|-----------|
| KLAW-1 | No ungoverned action — every substrate execution follows LawKernel evaluation |
| KLAW-2 | Fail-closed on uncertainty — inconclusive evaluation → deny or panic |
| KLAW-3 | Immutable law history — LawLedger is append-only |
| KLAW-4 | Reference-anchored decisions — every `LawEvalPayload` includes `t5_ref_signal_hash` |
| KLAW-5 | Lineage-anchored execution — every evaluation emits a lineage event |

### T5 law invariants

| ID | Statement |
|----|-----------|
| T5-LAW-1 | Law decisions reproducible under the same context |
| T5-LAW-2 | No admitted decision may contradict admitted laws |
| T5-LAW-3 | Law fitness changes must be lineage-anchored |

## 4. Schemas

### LawRecord

- `id`, `code` (e.g. SIT-1, PIT-2), `text`, `status` (`admitted` | `experimental` | `revoked`)
- `fitness` (0–1), `created_at`, `epoch`, `proof_ref` (optional)

### LawContext

- `actor_id`, `domain`, `epoch`, `lineage_contract_id`, `lineage_event_id` (optional)
- `t5_ref_signal_hash` — required on every context

### LawEvalPayload

- `context`, `candidate_intent`, `applicable_laws`, `decision` (`admit` | `deny` | `transform` | `panic`)
- `reasons`, `t5_ref_signal_hash`, `invariant_proof_id`, `transformed_intent` (optional)

### Intent

- `id`, `kind` (ASK, PLAN, WRITE, ACT), `payload`, `origin`

### LineageEvent

- `kind`: `LAW_EVAL` | `LAW_PANIC` | `LAW_STATUS_CHANGE`
- `ref_signal_hash`, `invariant_proof_id`, `payload`

## 5. Execution flows

### 5.1 Intent admission

1. Receive intent from Nova Cortex / operator / agent
2. `LawContextResolver.resolve()` — bind actor, domain, epoch, lineage, T5 ref
3. `LawKernel.evaluate()` — select applicable laws, decide outcome
4. Attach T5 invariant proof via `InvariantLedger.issue()`
5. Emit `LAW_EVAL` lineage event
6. `LawfulIntentRouter` routes:
   - **admit** → substrate executor
   - **deny** → operator feedback (denied list)
   - **transform** → modified intent (e.g. PIT-2 `:pit2`, PIT-3 `:pit3`)
   - **panic** → `LawKernelPanicHandler`

### 5.2 Panic flow

Triggered by: invariant violation, T5 mismatch, lineage inconsistency, law ambiguity.

1. Freeze execution lane (`domain:actor_id`)
2. Emit `LAW_PANIC` lineage event
3. Log full context + proofs
4. Require operator or governance intervention

## 6. Founding laws (v1.0 seed)

| Code | Role | Status |
|------|------|--------|
| UGR-C8 | Lawful Creation Invariant | admitted |
| PIT-2 | Persistence under reality feedback | admitted |
| PIT-3 | Planning integrity under evidence | admitted |

### PIT band activation

**PIT-2** transforms when `pit_evidence_fitness ≥ 0.8`, domain ∈ `{cognition, governance}`, `pit_mode=PIT-2`.

**PIT-3** transforms when `pit_evidence_fitness ≥ 0.8`, domain ∈ `{planning, cognition}`, `pit_mode=PIT-3`.

Otherwise: lawful **ADMIT** (original intent executed).

## 7. Proof sketches

### Reproducibility (T5-LAW-1)

`InvariantLedger.issue()` hashes the full `LawEvalPayload` canonical JSON. Re-evaluating the same intent under the same context reproduces the same proof blob.

### Non-contradiction (T5-LAW-2)

`LawKernel.applicable_laws()` only selects **admitted** laws with fitness above threshold. Deny path blocks execution when explicit violation flags are set.

### Immutability (KLAW-3)

`LawLedger.append()` rejects duplicate codes; status changes append new rows without mutating prior records.

## 8. Integration

- **T5 / CRK-T5:** `T5ReferenceSignal.current()` bridges to `src.kernel.reference_service`
- **Lineage:** `LineageStore` emits events for cockpit and replay validation
- **Nova Cortex:** routes all intents through `LawfulIntentRouter.route()`

## 9. Roadmap (v1.1)

- Formal proof obligations for all founding laws
- zk-style law proofs on `InvariantProof.proof_blob`
- Multi-tenant law partitions
- Steward ratification workflow for experimental → admitted promotions

## 10. Usage

```python
from nova.law_kernel import make_law_kernel_stack, new_intent

router = make_law_kernel_stack()
intent = new_intent(kind="ASK", payload={"query": "status"}, origin="operator")
result = router.route(
    intent,
    actor_id="actor-1",
    domain="cognition",
    epoch="EPOCH:0:T0",
    lineage_contract_id="lc-1",
)
```

Tests: `tests/test_pit_band_activation.py`, `tests/test_nova_law_kernel_v1.py`
