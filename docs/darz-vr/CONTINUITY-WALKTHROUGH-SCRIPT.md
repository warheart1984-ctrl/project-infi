# DARZ-VR Continuity Walkthrough — First Live Demo Script

Scene: **DARZ-VR v0.1**, single user, minimal environment.  
Data: `fixtures/crk1/v01/samples/continuity_walkthrough.json`  
API: [CONTINUITY_API_V0_1.md](../crk1/roadmap/CONTINUITY_API_V0_1.md)

Unity is a **renderer only** — every node is a real CRK-1 object from the Continuity API.

---

## Spawn / Orientation

> You're standing inside a live continuity graph. Every object you see is a real CRK-1 object, not a mock.

Layers (top → bottom):

| Layer | Prefab | Shape |
|-------|--------|-------|
| IdentityLayer | `IdentityNodePrefab` | sphere |
| DecisionLayer | `DecisionNodePrefab` | diamond (rotated cube) |
| OutcomeLayer | `OutcomeNodePrefab` | cube |
| EvidenceLayer | `EvidenceNodePrefab` | cylinder |
| InterpretationLayer | `InterpretationNodePrefab` | capsule |

---

## Step 1 — Identity (`I-0001`)

Walk to Identity node. Label: **Continuity Lab**. Select to open Inspector.

| Field | Value |
|-------|-------|
| Type | Identity |
| ID | I-0001 |
| Receipt | R-1001 |
| Epoch | 1 |

> This identity was created through a governed action. You can see the receipt that authorized its existence.

---

## Step 2 — Decision (`D-0001`)

Follow highlighted edge Identity → Decision.

| Field | Value |
|-------|-------|
| Type | Decision |
| Label | Enable feature X |
| Linked Identity | I-0001 |
| Receipt | R-1002 |

> This decision is structurally linked to the identity that made it. The governance receipt checked kernel invariants before commit.

---

## Step 3 — Outcome (`O-0001`)

Edge: Decision → Outcome (`results_in`).

Inspector shows `state_change.before/after`, `metrics.ce_delta`, `metrics.se_delta`.

> This outcome records what actually changed. It also records how consequence exposure metrics shifted.

---

## Step 4 — Evidence (`E-0001`)

Edge: Outcome → Evidence (`documented_by`).

| Field | Value |
|-------|-------|
| Label | Experiment log #42 |
| Kind | Log |
| URI | s3://bucket/logs/42.json |
| Hash | sha256:… |

> Evidence is a pointer to reality — logs, metrics, documents — cryptographically bound to this continuity chain.

---

## Step 5 — Interpretation (`T-0001`)

Edge: Evidence → Interpretation (`interpreted_by`).

Shows statement, confidence (0.87), assumptions, invariant checks K3/K7/K9.

> This is where judgment enters — explicitly tied to assumptions and invariants.

---

## Step 6 — Full chain

Chain tab (`GET /graph/chain/I-0001`):

**Identity → Decision → Outcome → Evidence → Interpretation**

---

## Step 7 — Live update

Operator `POST /interpretation` outside VR.

New `InterpretationNode` appears linked to same Evidence via WebSocket `OBJECT_CREATED` + `graph_delta`.

> VR didn't invent it. CRK-1 accepted it, issued a receipt, and updated the graph. VR only renders it.

---

## Closing

> What you've seen is not a visualization of a document. It's a spatial view of a live constitutional runtime. Every node is governed. Every link is traceable. Every artifact is consequence-exposed.

---

## Unity bindings (v0.1)

### GraphController

On `OBJECT_CREATED`:

1. `prefab = PrefabFor(object.type)` — see `prefab_for_type()` in `src/crk1/crk1_wire_v01.py`
2. Instantiate under `layer_for_type(object.type)`
3. `NodeController.crkId = object.id`
4. `NodeController.type = object.type`
5. `label.text = object.payload.label`

On `graph_delta.edges`: instantiate `EdgePrefab`, bind `fromId`, `toId`, `relationType`.

### NodeController

On click → `InspectorController.Show(crkId)`

### InspectorController

- `GET /graph/node/{id}`
- `GET /receipt/{receipt_id}`
- Populate TitleText, IdField, TypeField, ReceiptField, EpochField, CreatedByField, ProvenanceList, ChainList

See also: [DARZ_VR_UNITY_SPEC.md](../crk1/roadmap/DARZ_VR_UNITY_SPEC.md), [CRK1-OBJECTS-V01-UNITY-BINDINGS.md](CRK1-OBJECTS-V01-UNITY-BINDINGS.md).
