# Continuity API v0.1

**Truth interface** — the only source of objects for CRK-Explorer and DARZ-VR.

All clients must treat this API as authoritative. No synthetic objects. No client-side invention of continuity nodes.

---

## Truth boundary invariant

Every object returned must include:

```json
{
  "id": "I-0001",
  "type": "Identity | Decision | Outcome | Evidence | Interpretation | Receipt",
  "created_at": "ISO8601",
  "created_by": "A-001",
  "epoch": 1,
  "receipt_id": "R-1001",
  "payload": {},
  "links": {}
}
```

Schemas: `fixtures/crk1/v01/*.v01.schema.json` — validator: `CRK1WireV01Validator`.

---

## REST endpoints

### Identity

```
GET  /identity/{id}
POST /identity
GET  /identity/{id}/graph
```

### Decision

```
GET  /decision/{id}
POST /decision
GET  /decision/{id}/graph
```

### Outcome

```
GET  /outcome/{id}
POST /outcome
```

### Evidence

```
GET  /evidence/{id}
POST /evidence
```

### Interpretation

```
GET  /interpretation/{id}
POST /interpretation
```

### Receipt

```
GET  /receipt/{id}
GET  /receipt/{id}/provenance
```

### Graph

```
GET  /graph/node/{id}
GET  /graph/chain/{id}
GET  /graph/full
```

### Governed actions

```
POST /action/interpretation
POST /action/evidence
POST /action/decision
```

Governed actions route through `CRK1GovernanceEngine.commit_action` — receipt required before state mutation.

---

## WebSocket events

```
WS /events/stream
```

### Message shape

```json
{
  "event_type": "OBJECT_CREATED",
  "object": {
    "id": "E-3333",
    "type": "Evidence",
    "receipt_id": "R-7777"
  },
  "graph_delta": {
    "nodes": [
      {
        "id": "E-3333",
        "type": "Evidence",
        "receipt_id": "R-7777"
      }
    ],
    "edges": [
      {
        "from_id": "O-2222",
        "to_id": "E-3333",
        "relation_type": "documented_by"
      }
    ]
  }
}
```

---

## Implementation notes

| Concern | Reference |
|---------|-----------|
| CRK-1 runtime backing store | `src/crk1/runtime_facade.py` |
| Governance gate | `src/crk1/crk1_governance_engine.py` |
| Receipt schema | `fixtures/crk1/governance_receipt_header.schema.json` |
| Graph contract | [CRK1_GRAPH_DATA_CONTRACT.md](CRK1_GRAPH_DATA_CONTRACT.md) |
| Existing partial API | `src/constitutional_cockpit_routes.py` (law spine — not CRK-shaped) |
| Substrate events (v0) | `app/main.py` `/events`, `/api/continuity/events` |

**Planned package:** `src/crk1/continuity_api/` (not yet implemented).

---

## Error semantics

| Code | Meaning |
|------|---------|
| 400 | Invalid object or missing receipt on governed action |
| 403 | Constitutional rejection (invariant / drift / red-team) |
| 404 | Unknown object ID |
| 409 | Duplicate ID or conflicting state |

Constitutional failures return `ConstitutionalError` message in response body.
