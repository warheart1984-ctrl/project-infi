# CRK-1 Objects v0.1 — Unity Prefab & Data Bindings

Wire format: `fixtures/crk1/v01/*.schema.json`  
Python helpers: `src/crk1/crk1_wire_v01.py`, `src/crk1/continuity_graph.py`

---

## Common envelope (all types)

```json
{
  "id": "string",
  "type": "Identity|Decision|Outcome|Evidence|Interpretation|Receipt",
  "created_at": "ISO-8601",
  "created_by": "string",
  "epoch": "integer",
  "receipt_id": "string",
  "payload": {},
  "links": {}
}
```

---

## Prefabs

| Prefab | Shape | NodeController.type | Label binding |
|--------|-------|---------------------|---------------|
| IdentityNodePrefab | sphere | Identity | `payload.label` |
| DecisionNodePrefab | diamond cube | Decision | `payload.label` |
| OutcomeNodePrefab | cube | Outcome | `payload.label` |
| EvidenceNodePrefab | cylinder | Evidence | `payload.label` |
| InterpretationNodePrefab | capsule | Interpretation | `payload.label` |
| EdgePrefab | LineRenderer | — | — |
| InspectorPanel | UI | — | API-driven |

### NodeController fields

- `string crkId` ← `id`
- `string type` ← `type`
- `TextMesh label` ← `payload.label`

### EdgeController fields

- `string fromId`
- `string toId`
- `string relationType`

### InspectorPanel fields

| UI element | Source |
|------------|--------|
| TitleText | `payload.label` or `type + " " + id` |
| IdField | `id` |
| TypeField | `type` |
| ReceiptField | `receipt_id` |
| EpochField | `epoch` |
| CreatedByField | `created_by` |
| ProvenanceList | parent/child edges from `GET /graph/node/{id}` |
| ChainList | `GET /graph/chain/{id}` |

---

## Event flow

```
WS /events/stream
  → GraphController.OnObjectCreated
  → choose prefab by type
  → instantiate + bind NodeController
  → apply graph_delta.edges → EdgePrefab

NodeController.OnClick
  → InspectorController.Show(crkId)
  → GET /graph/node/{id}
  → GET /receipt/{receipt_id}
```

---

## Relation types (edges)

| relation_type | Typical from → to |
|---------------|-------------------|
| initiated_by | Identity → Decision |
| results_in | Decision → Outcome |
| documented_by | Outcome → Evidence |
| supported_by | Decision → Evidence |
| interpreted_by | Evidence → Interpretation |
| influences | Interpretation → Decision |
| authorized_by | Receipt → object |

Built by `build_edges()` in `src/crk1/continuity_graph.py`.

---

## Sample dataset

Full DARZ-VR walkthrough chain: `fixtures/crk1/v01/samples/continuity_walkthrough.json`
