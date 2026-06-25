# CRK-1 × DARZ-VR Engineering Roadmap (v0.1 → v1.0)

Minimal, structural, falsifiable path from constitutional runtime to spatial continuity browser.

## Milestone 0 — CRK-1 Runtime (Foundational Substrate)

**Goal:** Running CRK-1 producing real continuity chains.

**Deliverables:** Object registry, governance engine, CE(S)/SE(S), receipts, persistence, append-only event log.

**Success:** Full continuity chain through CRK-1 with receipts stored.

## Milestone 1 — Continuity API (Truth Interface)

**Goal:** Governed API for all CRK-1 objects and events.

**Endpoints:** `/identity/*`, `/decision/*`, `/outcome/*`, `/evidence/*`, `/interpretation/*`, `/receipt/*`, `/graph/*`, `/events/stream`.

**Rules:** Canonical IDs only; no VR abstractions; no client-side interpretation layers.

**Success:** Client queries entire continuity graph with live updates.

## Milestone 2 — CRK-Explorer (Web Continuity Browser)

**Goal:** Prove graph renderability before VR.

**Features:** Identity → Decision → Outcome → Evidence → Interpretation; provenance + receipts; WebSocket live updates; clarity over styling.

**Success:** Navigate live continuity chain in a browser.

## Milestone 3 — First End-to-End Demo (Proof of Life)

**Demo:** Identity → Decision → Outcome → Evidence → Interpretation → Receipt; live CRK-Explorer walkthrough.

**Success:** Complete chain created, visualized, inspected in real time.

## Milestone 4 — Unity Minimal Renderer (Spatial Graph)

**Goal:** Same graph as CRK-Explorer, spatially.

**Features:** Identity/decision nodes, evidence trails, interpretation frames, receipt panel, live updates.

**Constraints:** No avatars, physics, world, social, or client governance.

**Success:** Unity matches CRK-Explorer truth boundary.

## Milestone 5 — Governed Actions from VR

**Actions:** Add Interpretation, Attach Evidence, Propose Decision, Inspect Receipt, Governance Review (if authorized).

**Success:** VR write → CRK-1 → CRK-Explorer → VR round-trip.

## Milestone 6 — Multi-User Presence (Optional)

**Features:** Shared graph view, shared receipt inspection, shared navigation (cursors/markers OK).

**Success:** Two users walk the same chain simultaneously.

## Milestone 7 — DARZ-VR v0.1 (Spatial Continuity Browser)

**Goal:** First full DARZ-VR — spatial graph, provenance, receipts, governed actions, multi-user, live updates, zero divergence from CRK-1.

**Success:** Walk a live continuity chain; inspect every governance artifact that created it.

---

## Pattern

1. Define the invariant  
2. Build the substrate  
3. Expose the truth boundary  
4. Render the truth  
5. Test the truth  
6. Let reality challenge it  

See also: [DARZ-VR-v0.1-unity-blueprint.md](DARZ-VR-v0.1-unity-blueprint.md), [DARZ-VR-architecture.md](DARZ-VR-architecture.md).
