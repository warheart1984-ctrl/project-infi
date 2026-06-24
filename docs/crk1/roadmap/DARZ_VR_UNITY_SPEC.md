# DARZ-VR Unity Specification

**Spatial continuity browser** — Phase 4–7 deliverable.

Strict rule: Unity is a **renderer**, not a source of truth. All objects come from Continuity API v0.1.

---

## Unity hierarchy (conceptual)

```
SceneRoot
├── GraphRoot
│   ├── IdentityLayer
│   │   └── IdentityNode_{id}     (prefab)
│   ├── DecisionLayer
│   │   └── DecisionNode_{id}
│   ├── OutcomeLayer
│   │   └── OutcomeNode_{id}
│   ├── EvidenceLayer
│   │   └── EvidenceNode_{id}
│   ├── InterpretationLayer
│   │   └── InterpretationNode_{id}
│   └── EdgesRoot
│       └── Edge_{fromId}_{toId}  (line/beam)
├── UIRoot
│   └── InspectorPanel
│       ├── TitleText
│       ├── IdField
│       ├── TypeField
│       ├── ReceiptField
│       ├── ProvenanceList
│       └── ChainList
├── CameraRig
│   ├── MainCamera
│   └── (later) XR Rig
└── InteractionRoot
    ├── Raycaster
    ├── SelectionController
    └── EventListener          (WebSocket → /events/stream)
```

---

## Key behaviors

### GraphController

- Subscribes to `WS /events/stream`
- Instantiates node prefabs on `graph_delta.nodes`
- Positions nodes by type layer + simple layout
- Creates edges from `graph_delta.edges`

### NodeController

- Stores `crkId`, `type`
- On click → `InspectorController.Show(crkId)`

### InspectorController

- `GET /graph/node/{id}`
- `GET /receipt/{receipt_id}`
- Populates panel fields

---

## Governed actions (Phase 5+)

| Action | API |
|--------|-----|
| Add interpretation | `POST /action/interpretation` |
| Attach evidence | `POST /action/evidence` |
| Propose decision | `POST /action/decision` |

All governed actions require receipt issuance server-side before graph update event.

---

## Parity with CRK-Explorer

| Capability | CRK-Explorer | DARZ-VR |
|------------|--------------|---------|
| Graph source | Continuity API | Same API |
| Live updates | WebSocket | Same WebSocket |
| Inspector | Right pane | UI panel |
| Receipt view | Inspector tab | ReceiptField + provenance |
| Layout | 2D layered | 3D layered by Y-axis |

---

## Implementation status

| Piece | Status | Path |
|-------|--------|------|
| Unity project | Not started | — |
| DAR-Z cognition kernel | Exists (non-VR) | `darz-kernel/` |
| DAR-Z node bridge | Exists | `src/darz_kernel_bridge.py` |
| WebView2 operator host | Exists | `desktop/webview2/` |

**Exit (Phase 7):** User walks through a live continuity chain in spatial VR with the same object IDs as CRK-Explorer.
