# AIOS Constitutional Node Runtime v1

**Purpose:** smallest sovereign unit of constitutional administrative intelligence.

AIOS constitutional node runtime v1 defines the smallest governed runtime surface in the stack. It is the constitutional unit that hosts identity, evidence, truth, knowledge, sovereignty, continuity, institutional memory, and optional reality integration through explicit APIs only.

## 1. Runtime Planes

The node is organized into constitutional runtimes:

- Identity Runtime: manages identities, authority, delegation, and consent.
- Evidence Runtime: ingests, validates, stores, and exposes evidence artifacts.
- Truth Runtime: produces interpretive truth evaluations from evidence without overriding ledger neutrality.
- Knowledge Runtime: maintains ontology, knowledge graph, and traceability.
- Sovereignty Runtime: enforces constitutional rules, tiers, authority boundaries, and node-level governance.
- Continuity Runtime: preserves lineage, invariants, replayability, and constitutional evolution.
- Institutional Memory Runtime: records decisions, receipts, relationships, and institutional workflows.
- Reality Runtime: optional in v1, used to integrate external signals into constitutional context.

All runtimes are accessed only through constitutional APIs. No runtime may bypass the node ledger.

## 2. Constitutional API Envelope

The node exposes runtime-specific API families:

- Identity, Authority, Relationship
- Evidence, Provenance, Traceability
- Knowledge, Conformance
- Governance, Conformance
- Relationship, Evidence, Traceability
- Identity, Evidence, Knowledge

The API boundary is authoritative: callers invoke runtime operations through the node, not by mutating internal state.

## 3. Trust Ledger Schema v1

The ledger preserves evidence, provenance, relationships, trust, and constitutional decisions, but never declares truth.

### Core entities

- Identity
  - `identity_id`
  - `type`
  - `attributes`
  - `created_at`
  - `provenance_id`
- Evidence
  - `evidence_id`
  - `identity_id`
  - `type`
  - `content_ref`
  - `provenance_id`
  - `timestamp`
- Provenance
  - `provenance_id`
  - `parent_id`
  - `source`
  - `lineage_chain`
  - `timestamp`
- Relationship
  - `relationship_id`
  - `subject_identity_id`
  - `object_identity_id`
  - `relationship_type`
  - `provenance_id`
  - `temporal_bounds`
  - `steward_identity_id`
- Trust Assertion
  - `trust_id`
  - `relationship_id`
  - `issuer_identity_id`
  - `trust_score`
  - `confidence_band`
  - `context`
  - `evidence_ids[]`
  - `timestamp`
- Constitutional Decision
  - `decision_id`
  - `node_id`
  - `inputs`
  - `result`
  - `governance_clauses[]`
  - `conformance_status`
  - `receipt_id`
  - `timestamp`
- Constitutional Receipt
  - `receipt_id`
  - `decision_id`
  - `ledger_entry_id`
  - `hash`
  - `signature`
  - `timestamp`

All entries are immutable, hash-chained, and replayable.

## 4. Relationship Intelligence Specification v1

Relationship intelligence treats relationships as constitutional primitives.

- Every relationship has its own `relationship_id` and provenance.
- Relationship types are ontology-defined, not application ad hoc.
- Trust is attached to relationships, not only identities.
- Each relationship records stewardship, consent, scope, and authority limits where applicable.
- Relationships remain traceable across decisions, documents, evidence, and institutional memory.

## 5. Governance Engine v3

Governance Engine v3 reasons across multiple tiers:

- Tier 1: policy evaluation
- Tier 2: trust-aware reasoning
- Tier 3: constitutional clause reasoning
- Tier 4: cross-plane conformance
- Tier 5: replay-integrated governance

The engine returns a governed decision packet, not a simple yes/no.

## 6. Continuity OS v1

Continuity OS v1 preserves constitutional continuity across the node:

- Lineage Service
- Invariant Service
- Replay Service
- Evolution Service
- Conformance Service
- Institutional Memory Service

Continuity OS is the substrate that keeps AIOS, CORI, and CIEMS coherent over time.

## 7. Conformance

An implementation claiming AIOS constitutional node conformance must:

- implement the runtime planes
- implement the trust ledger schema
- enforce constitutional API boundaries
- preserve replayability and hash chaining
- surface governing decisions as receipts
- expose continuity and institutional memory records
- pass the AIOS runtime and ledger test suite

## 8. Project Infi Surface Mapping

The canonical implementation surface for v1 is:

- runtime module: `constitutional/aios_node_runtime.py`
- docs surface: this specification
- conformance artifacts: `docs/crk1/release/AIOS_CONSTITUTIONAL_NODE_RUNTIME_V1.spec.json`
- test surface: `tests/test_aios_node_runtime.py`

