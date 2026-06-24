# CRK-1 Team Roles and Implementation Phases

Functional roles and dependency chain for CRK-1 × Continuity API × CRK-Explorer × DARZ-VR.

---

## 1. Team roles

These are **functional roles**, not corporate titles.

### A. Kernel Engineer (CRK-1 runtime)

**Responsibilities**

- Implement CRK-1 objects (Identity, Decision, Outcome, Evidence, Interpretation, Receipt)
- Implement invariants K0–K12 (K13–K15 in extension track)
- Implement governance engine + commit-refusing gate
- Implement drift metrics CE(S), SE(S)
- Implement event log + receipt issuance
- Maintain canonical state store

**Output:** A running CRK-1 substrate.  
**Anchor:** `src/crk1/`

### B. Continuity API engineer

**Responsibilities**

- Build REST + WebSocket API
- Map CRK-1 objects to API endpoints
- Enforce truth boundary (no synthetic objects)
- Implement graph and provenance queries
- Implement governed action submission

**Output:** The truth interface.  
**Spec:** [CONTINUITY_API_V0_1.md](CONTINUITY_API_V0_1.md)

### C. Graph engineer (continuity graph layer)

**Responsibilities**

- Build graph model from CRK-1 objects
- Maintain node/edge types and lineage traversal
- Maintain continuity chain queries
- Maintain live update propagation

**Output:** The continuity graph.  
**Spec:** [CRK1_GRAPH_DATA_CONTRACT.md](CRK1_GRAPH_DATA_CONTRACT.md)

### D. CRK-Explorer engineer (web continuity browser)

**Responsibilities**

- Render continuity graph in browser
- Node inspection, receipt viewer, provenance viewer
- Live updates, minimal UI

**Output:** The first continuity viewer.  
**Spec:** [CRK_EXPLORER_UI_SPEC.md](CRK_EXPLORER_UI_SPEC.md)

### E. Unity engineer (DARZ-VR renderer)

**Responsibilities**

- Render continuity graph spatially
- Node selection, receipt inspection panel
- Live graph updates, governed action submission
- Strict CRK-1 truth boundary (API-only)

**Output:** Spatial continuity browser.  
**Spec:** [DARZ_VR_UNITY_SPEC.md](DARZ_VR_UNITY_SPEC.md)

### F. Integration engineer

**Responsibilities**

- Align CRK-1 ↔ API ↔ Graph ↔ Explorer ↔ VR
- Object ID consistency across layers
- Receipt resolution end-to-end
- Live update propagation

**Output:** A coherent system.

### G. Red-team / validation engineer

**Responsibilities**

- Attempt insulation, semantic capture, governance bypass
- Founder-assumption detection
- CE(S)/SE(S) degradation attacks

**Output:** Empirical validation.  
**Anchor:** `src/crk1/attack_simulator.py`, `src/crk1/red_team_protocol.py`

---

## 2. Implementation order (critical path)

### Phase 0 — CRK-1 runtime ✅ (v1.0)

| Task | Status |
|------|--------|
| Objects | Done (`runtime_facade.py`, ledgers) |
| Invariants K0–K12 | Done |
| Governance engine + commit gate | Done |
| Receipts + Merkle spine | Done |
| Drift metrics CE/SE | Done |
| Unified event log | Partial (multiple ledgers) |

**Exit:** CRK-1 can produce a continuity chain in tests.

### Phase 1 — Continuity API

Identity, Decision, Outcome, Evidence, Interpretation, Receipt endpoints; graph endpoints; `WS /events/stream`.

**Exit:** A client can query and subscribe to the continuity graph.

### Phase 2 — CRK-Explorer

Render graph, inspect nodes/receipts/provenance, live updates.

**Exit:** User navigates a live continuity chain in a browser.

### Phase 3 — First end-to-end demo

See [PROOF_OF_LIFE_DEMO_SCRIPT.md](PROOF_OF_LIFE_DEMO_SCRIPT.md).

**Exit:** CRK-1 is proven alive.

### Phase 4 — Unity minimal renderer

Spatial graph, node selection, receipt panel, live updates.

**Exit:** VR renders the same truth as CRK-Explorer.

### Phase 5 — Governed VR actions

Add interpretation, attach evidence, propose decision, trigger governance review.

**Exit:** VR submits constitutional actions.

### Phase 6 — Multi-user presence

Shared graph, inspection, updates.

### Phase 7 — DARZ-VR v0.1

Spatial continuity browser with full provenance navigation, governed actions, multi-user presence, live updates.

**Exit:** User walks through a live continuity chain.

---

## 3. Current repo status (2026-06-24)

| Phase | Approx. completion |
|-------|-------------------|
| M0 CRK-1 runtime | ~70% |
| M1 Continuity API | ~15% (constitutional cockpit overlap only) |
| M2 CRK-Explorer | ~10% (static dashboard + law-spine UI) |
| M3 E2E demo | ~20% (tests, no wired demo) |
| M4–M7 DARZ-VR | 0% VR (DAR-Z kernel bridge exists) |

**Build from:** `src/crk1/runtime_facade.py`, `frontend/src/components/constitutional/EvidenceGraph.jsx`, `darz-kernel/`.
