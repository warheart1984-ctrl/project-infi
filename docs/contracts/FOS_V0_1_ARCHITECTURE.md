# FOS v0.1 Architecture

Status: minimal kernel implemented

FOS (Founder Operating System) is the civilization memory substrate. It stores
continuity threads, evidence-bearing events, and versioned lineage so higher
systems can query memory, reconstruct decisions, and project CAB history without
treating documents as the source of truth.

## Minimal Kernel

The FOS v0.1 kernel lives at:

```text
src/fos/kernel.py
```

It provides:

- `ContinuityThread`
- `ContinuityEvent`
- `MemoryObjectRef`
- `FOSMemoryObject`
- `InMemoryStore`
- `FileStore`
- `FOSKernel`
- `DecisionReconstruction`

The substrate is intentionally small:

```text
Thread -> Event -> Lineage -> MemoryObject -> Reconstruction
```

Everything else is a view.

## Event Types

FOS supports the minimal event taxonomy:

- `Concept`
- `Invariant`
- `Architecture`
- `Governance`
- `Decision`
- `Evidence`
- `Note`
- `Custom`

## Memory Object Requirements

Every memory object must have:

- `id`
- `type`
- `definition`
- `evidence_refs`
- `lineage`
- `version`
- `continuity_thread`

Invariants:

- No object without evidence.
- No object without lineage.
- No object without version.
- No object without type and definition.
- All changes are continuity-anchored and versioned.

## Query Surface

The kernel exposes:

- `create_thread`
- `append_event`
- `get_event`
- `list_events_for_thread`
- `get_lineage_chain`
- `memory_ref`
- `memory_object_from_event`
- `validate_event_as_memory_object`
- `reconstruct_decision`
- `project_cab_ledger`

## Decision Reconstruction

`reconstruct_decision(decision_id)` returns:

- the decision event
- the continuity thread
- discussion events
- architecture events
- governance events
- evidence events
- alternative decisions
- outcome events

This turns "why did we choose this?" into a query over continuity history.

## CAB Projection

CAB remains the lineage layer for continuity architecture. FOS can project a
CAB ledger into a continuity thread:

```python
from src.fos import FOSKernel
from src.continuity.cab import CABLedger

kernel = FOSKernel()
thread = kernel.project_cab_ledger(CABLedger())
```

Projection rules:

- `DecisionRecord` -> `Decision`
- `EvidenceChain`, `ContinuityReceipt`, `ReconstructionPlan` -> `Evidence`
- `IntentRecord`, `AssumptionRecord`, `FounderKnowledgeSnapshot` -> `Concept`
- `SuccessionProtocol` -> `Governance`

## Rust Mirror

The primitive mirror lives at:

```text
fos-kernel/src/primitives.rs
```

It mirrors the FOS event/thread/memory-object shape for future Rust parity.

## Out Of Scope For v0.1

- Explorer UI
- Full Rust reconstruction parity
- Full graph visualization
- Consolidation to one authoritative continuity store
- Distributed storage

Those are views or deployment choices over the substrate.
