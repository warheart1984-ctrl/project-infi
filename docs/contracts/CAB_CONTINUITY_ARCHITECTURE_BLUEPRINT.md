# Continuity Architecture Blueprint (CAB)

Status: **active contract v1**

Authority: `docs/contracts/CONTINUITY_REPUTATION_V1.md`, `docs/contracts/URG_STACK_DOCTRINE.md`

## Constitutional clause

> No system is truly governed if its reasoning cannot survive its creators.

CAB is the **continuity engine** — not reasoning (DAR‑Z), transformation (CIEMS), measurement (NeoMundi), or governance (GOVERN). It preserves intent, decisions, assumptions, evidence, and organizational memory so reasoning and governance remain **reconstructable** across time, teams, and generations.

## Five-pillar stack

| Pillar | Role | CAB relationship |
|--------|------|------------------|
| **DAR‑Z** | Reasoning | Reasoning artifacts linked into IntentRecords and DecisionRecords |
| **CIEMS** | Transformation | Transformation decisions recorded with rationale and constraints |
| **NeoMundi** | Measurement | Measurements ingested as EvidenceChains |
| **GOVERN** | Governance | Policies referenced by DecisionRecords; runtime produces ContinuityReceipts |
| **CAB** | Continuity | Memory graph binding all pillars into reconstructable lineage |

## First-class objects

| Object | Purpose |
|--------|---------|
| `IntentRecord` | Structured capture of what we are trying to do and why |
| `DecisionRecord` | Chosen path with options, tradeoffs, and governance links |
| `AssumptionRecord` | Conditions believed true at decision time, with fragility and review |
| `EvidenceChain` | Linked measurements and analyses supporting or challenging beliefs |
| `ContinuityReceipt` | Runtime proof that a governed action occurred under identity and authority |
| `FounderKnowledgeSnapshot` | Tacit knowledge, mental models, and unwritten context |
| `SuccessionProtocol` | How stewardship and understanding transfer between generations |
| `ReconstructionPlan` | How a future team rebuilds reasoning from CAB alone |

Schema: `schemas/cab.v1.json`  
Implementation: `src/continuity/cab.py`, `src/continuity/cab_invariants.py`

## Continuity graph

CAB objects form a **time-layered, causally linked graph**:

```
IntentRecord ──► DecisionRecord ──► ContinuityReceipt (runtime)
       │                 │
       ▼                 ▼
AssumptionRecord ◄── EvidenceChain (NeoMundi)
       │
       ▼
FounderKnowledgeSnapshot ──► SuccessionProtocol ──► ReconstructionPlan
```

## Binding to existing continuity stack

| CAB layer | Existing implementation |
|-----------|-------------------------|
| Evidence / trace substrate | `src/continuity/ccs.py` (CCS) |
| Proof + replay | `src/continuity/proof.py`, `ugr_trace.py` |
| Reputation | `src/continuity/reputation.py` (CVR) |
| Runtime receipt | Nova `continuity_governance` on lawful turns |
| Point of decision | `src/continuity/pod.py` (`PODDecision`) |

Nova lawful turns emit `ContinuityGovernanceReceipt` (proof, CVR, trace). CAB ingests these as `ContinuityReceipt` objects linked to DecisionRecords and policies.

## Invariants

| ID | Name | Requirement |
|----|------|-------------|
| **RC** | Reconstructability | A `ReconstructionPlan` exists and references reachable intents and decisions |
| **CL** | Causal linkage | No orphan `DecisionRecord`; each links to at least one `IntentRecord` |
| **TI** | Temporal integrity | Ledger sequence is monotonic; `created_at` order preserved |
| **SU** | Succession | Steward transitions reference a `SuccessionProtocol` |
| **NE** | Non-erasure | Append-only ledger; supersede/deprecate, never delete |

## Processes

### Intent and decision lifecycle

1. Create or update `IntentRecord` when initiative or policy is proposed.
2. Create or update `AssumptionRecord` for explicit beliefs.
3. Link or create `EvidenceChain` from NeoMundi outputs.
4. Create `DecisionRecord` when a path is chosen; link GOVERN artifacts.
5. Runtime produces `ContinuityReceipt` on governed execution.

### Runtime integration

`ingest_nova_continuity_governance()` maps Nova lawful-turn `continuity_governance` bundles into CAB `ContinuityReceipt` entries.

`CAB_AUTO_INGEST=1` enables live Nova lawful-turn ingestion from the CVR recompute bridge. `CAB_STORE` selects the append-only JSONL ledger path; when unset it defaults to `~/.cab/ledger.jsonl`.

`ingest_ciems_transformation_event()` converts CIEMS governed transformation events, including CC-01 harness events, into linked `EvidenceChain` and `DecisionRecord` objects.

`ingest_neomundi_measurement()` converts NeoMundi measurement outputs into stable, deduplicated `EvidenceChain` objects using measurement IDs when available.

ControlTower / ops-console telemetry reads `CAB_STORE` and surfaces ledger availability, latest CAB links, and the RC/CL/TI/SU/NE invariant surface on `/telemetry`.

### Succession

On steward change: update `FounderKnowledgeSnapshot`, execute `SuccessionProtocol`, validate `ReconstructionPlan` for new stewards.

## Meta-governance

CAB is self-referential: CAB evolution, schema changes, and stewardship handoffs are themselves recorded as CAB objects.

## Implementation entry points

```python
from src.continuity.cab import (
    CABLedger,
    ingest_ciems_transformation_event,
    ingest_neomundi_measurement,
    ingest_nova_continuity_governance,
)
from src.continuity.cab_invariants import evaluate_cab_invariants
```

Bootstrap fixture: `fixtures/cab/governance_lineage_demo.v1.yaml`
