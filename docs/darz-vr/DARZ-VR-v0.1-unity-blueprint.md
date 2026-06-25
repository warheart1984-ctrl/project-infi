# DARZ-VR v0.1 — Unity Scene Blueprint

Maps CRK-1 constitutional objects to a buildable Unity scene: **DARZ_ContinuitySpace.unity**.

## 1. High-level scene structure

| GameObject | Scripts | Role |
|------------|---------|------|
| **CRK1Backend** | `Crk1ApiClient`, `Crk1StateCache` | HTTP/WebSocket to CRK-1; in-memory continuity graph |
| **ContinuitySpaceRoot** | `ContinuitySpaceController` | Spawns all continuity entities (nodes, edges, frames) |
| **PlayerRig** | `PlayerController`, `SelectionRaycaster`, `UiInspectorController` | XR or FPS navigation + inspection |
| **UIRoot** | Canvas (world or screen space) | Details, receipts, filters |

## 2. Core prefabs (CRK-1 → VR entities)

### IdentityNode.prefab ← IdentityObject

- Visual: sphere/capsule, `MeshRenderer`, TextMeshPro label, optional exposure halo
- `IdentityNodeController`: `IdentityId`, `SetData(IdentityObject)`, click → identity panel

### DecisionNode.prefab ← DecisionObject

- Smaller node branching from IdentityNode, edge-connected
- `DecisionNodeController`: `DecisionId`, `ParentIdentityId`, click → decision + linked outcomes/evidence

### OutcomeShard.prefab ← OutcomeObject

- Crystal/fragment polyhedron; color/brightness = consequence severity
- `OutcomeShardController`: `OutcomeId`, `DecisionId`

### EvidenceTrail.prefab ← EvidenceObject

- `LineRenderer` or tube Outcome → Evidence; optional flow particles
- `EvidenceTrailController`: `EvidenceId`, `OutcomeId`, `InterpretationIds`

### InterpretationFrame.prefab ← InterpretationObject

- Ring/frame orbiting evidence; color = adversarial / supportive / neutral
- `InterpretationFrameController`: `InterpretationId`, `EvidenceId`, `Weight`, `IsAdversarial`

## 3. Data flow: CRK-1 → Unity

### Crk1ApiClient

- `FetchIdentities()` → `List<IdentityObject>`
- `FetchDecisions(identityId)` → `List<DecisionObject>`
- `FetchEvidence(decisionId)` → `List<EvidenceObject>`
- `FetchInterpretations(evidenceId)` → `List<InterpretationObject>`
- `PostInterpretation(...)` → governed write; receipt on backend

### Crk1StateCache

Dictionaries: `identities`, `decisions`, `evidence`, `interpretations`.

Lookup: `GetIdentity`, `GetDecisionsForIdentity`, `GetEvidenceForDecision`, `GetInterpretationsForEvidence`.

## 4. Spawning and layout

`ContinuitySpaceController` on **ContinuitySpaceRoot**:

1. `FetchIdentities()` → instantiate `IdentityNode` (radial/grid)
2. Per identity → decisions → `DecisionNode` local tree
3. Per decision → outcomes + `EvidenceTrail`
4. Per evidence → `InterpretationFrame` orbit

v0.1 layout: identities on a circle/grid; decisions in local trees; evidence/interpretations offset in 3D.

## 5. Interaction

**SelectionRaycaster**: ray from camera/controller → open panel by controller type.

**UiInspectorController**: metadata, governance receipts, related-object focus links.

## 6. Governed write path (v0.1)

From InterpretationFrame panel: **Add Interpretation** → text input → `PostInterpretation` on CRK-1 → governance + receipt → spawn new frame.

**No governance logic in Unity** — only in CRK-1.

## 7. v0.1 success criteria

- Enter scene (headset or desktop)
- See identity nodes, decision branches, outcome shards, evidence trails, interpretation frames
- Walk/fly; click for provenance and receipts from CRK-1
- Add interpretation via backend; see it appear after constitutional acceptance

This is the first **Virtual Reality for Reals**: walking inside a governed continuity graph.
