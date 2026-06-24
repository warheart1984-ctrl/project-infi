# CRK-1 Graph Data Contract

CRK-1 → API → Graph → VR — canonical mapping and wire formats.

---

## 1. Canonical CRK-1 objects (v0.1 wire)

All API objects use the **common envelope** (`id`, `type`, `created_at`, `created_by`, `epoch`, `receipt_id`, `payload`, `links`).

| Object | Schema (v0.1) | Legacy runtime schema |
|--------|---------------|------------------------|
| Identity | `fixtures/crk1/v01/identity.v01.schema.json` | `fixtures/crk1/identity_object.schema.json` |
| Decision | `fixtures/crk1/v01/decision.v01.schema.json` | `fixtures/crk1/decision_object.schema.json` |
| Outcome | `fixtures/crk1/v01/outcome.v01.schema.json` | `fixtures/crk1/outcome_object.schema.json` |
| Evidence | `fixtures/crk1/v01/evidence.v01.schema.json` | `fixtures/crk1/evidence_object.schema.json` |
| Interpretation | `fixtures/crk1/v01/interpretation.v01.schema.json` | `fixtures/crk1/interpretation_object.schema.json` |
| Receipt | `fixtures/crk1/v01/receipt.v01.schema.json` | `fixtures/crk1/governance_receipt_header.schema.json` |

Sample walkthrough bundle: `fixtures/crk1/v01/samples/continuity_walkthrough.json`

---

## 2. Graph node types

| Node type | Source object | Primary edges |
|-----------|---------------|---------------|
| IdentityNode | Identity | → Decision (`initiated_by`) |
| DecisionNode | Decision | → Outcome (`results_in`), → Evidence (`supported_by`, optional) |
| OutcomeNode | Outcome | → Evidence (`documented_by`) |
| EvidenceNode | Evidence | → Interpretation (`interpreted_by`) |
| InterpretationNode | Interpretation | → Decision (`influences`, future) |
| ReceiptNode | Receipt | Inspector-only (optional graph node) |

### Node fields (all types)

```json
{
  "id": "D-1234",
  "type": "Decision",
  "receipt_id": "R-5678"
}
```

### Edge fields

```json
{
  "from_id": "I-1111",
  "to_id": "D-1234",
  "relation_type": "initiated_by"
}
```

**Relation types:** `initiated_by`, `results_in`, `documented_by`, `supported_by`, `interpreted_by`, `influences`

---

## 3. CRK-1 internal → API representation

### Internal (runtime)

```json
{
  "id": "D-1234",
  "type": "Decision",
  "created_at": "2026-06-24T11:00:00Z",
  "created_by": "A-999",
  "payload": {},
  "receipt_id": "R-5678",
  "links": {
    "identity_id": "I-1111",
    "outcome_id": "O-2222",
    "evidence_ids": ["E-3333"]
  }
}
```

### API `GET /decision/D-1234`

Same shape as internal wire format (no synthetic fields).

### API `GET /graph/node/D-1234`

```json
{
  "node": {
    "id": "D-1234",
    "type": "Decision",
    "receipt_id": "R-5678"
  },
  "edges": [
    {
      "from_id": "I-1111",
      "to_id": "D-1234",
      "relation_type": "initiated_by"
    },
    {
      "from_id": "D-1234",
      "to_id": "O-2222",
      "relation_type": "results_in"
    },
    {
      "from_id": "D-1234",
      "to_id": "E-3333",
      "relation_type": "supported_by"
    }
  ]
}
```

---

## 4. Events stream → clients

`WS /events/stream` — see [CONTINUITY_API_V0_1.md](CONTINUITY_API_V0_1.md).

### CRK-Explorer consumption

1. Subscribe to `/events/stream`
2. Apply `graph_delta.nodes` and `graph_delta.edges` to graph view
3. Append to footer event ticker
4. On node click → fetch `/graph/node/{id}` + `/receipt/{receipt_id}`

### DARZ-VR consumption

1. `GraphController` applies same `graph_delta`
2. Instantiate prefab per node with `id`, `type`, `receipt_id`
3. `NodeController` on click → inspector API calls

---

## 5. UI/VR behavior

| Interaction | Behavior |
|-------------|----------|
| Hover | Show type + short label |
| Click | Open inspector with full CRK-1 metadata |
| Color | By node type |
| Shape/icon | By node type (Identity=circle, Decision=diamond, …) |

---

## 6. Truth boundary rules

1. Clients **never** create graph nodes locally without a matching API event or GET response.
2. Governed `POST` actions return receipt + object; graph update follows via WebSocket (not optimistic client graph).
3. `receipt_id` on every object links to governance receipt header for audit.
4. IDs are stable UUIDs (or `crk1_uuid()`-mapped identifiers in receipts).

---

## 7. Reference code (graph builder — planned)

```python
# Planned: src/crk1/continuity_graph.py
# build_node(object) -> GraphNode
# build_edges(object) -> list[GraphEdge]
# chain_from(identity_id) -> list[GraphNode]
```

Current partial lineage: `src/crk1/interpretive_lineage_tree.py` (semantic layer only).
