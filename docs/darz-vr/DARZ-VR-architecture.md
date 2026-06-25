# DARZ-VR v0.1 — Architecture Diagram

```
                         ┌──────────────────────────────────────────┐
                         │              CRK‑1 BACKEND               │
                         │  (Authoritative Constitutional Runtime)   │
                         ├──────────────────────────────────────────┤
                         │  • Kernel Codex (K0–K12)                  │
                         │  • Governance Engine (commit gate)        │
                         │  • Ledgers (Kernel / Mutation / Semantic) │
                         │  • Reproduction Harness                   │
                         │  • Red‑Team Suite                         │
                         └───────────────▲──────────────────────────┘
                                         │
                                         │ REST / WebSocket API
                                         │
                         ┌───────────────┴──────────────────────────┐
                         │             Unity Client Layer            │
                         ├──────────────────────────────────────────┤
                         │  CRK1Backend (GameObject)                │
                         │   • Crk1ApiClient                        │
                         │   • Crk1StateCache                       │
                         └───────────────┬──────────────────────────┘
                                         │
                                         │ Local continuity graph
                                         │
┌────────────────────────────────────────┴────────────────────────────────────────┐
│                         CONTINUITY SPACE (Unity Scene)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌──────────────────────────────┐       ┌──────────────────────────────┐       │
│   │      IdentityNode.prefab     │       │      IdentityNode.prefab     │       │
│   │   (IdentityObject → VR)      │       │   (IdentityObject → VR)      │       │
│   └───────────────┬──────────────┘       └───────────────┬──────────────┘       │
│                   │                                      │                      │
│                   ▼                                      ▼                      │
│        ┌──────────────────────┐               ┌──────────────────────┐          │
│        │  DecisionNode.prefab │               │  DecisionNode.prefab │          │
│        │ (DecisionObject → VR)│               │ (DecisionObject → VR)│          │
│        └───────────┬──────────┘               └───────────┬──────────┘          │
│                    │                                       │                     │
│                    ▼                                       ▼                     │
│        ┌──────────────────────┐               ┌──────────────────────┐           │
│        │  OutcomeShard.prefab │               │  OutcomeShard.prefab │           │
│        │ (OutcomeObject → VR) │               │ (OutcomeObject → VR) │           │
│        └───────────┬──────────┘               └───────────┬──────────┘           │
│                    │                                       │                     │
│                    ▼                                       ▼                     │
│        ┌──────────────────────┐               ┌──────────────────────┐           │
│        │ EvidenceTrail.prefab │               │ EvidenceTrail.prefab │           │
│        │ (EvidenceObject → VR)│               │ (EvidenceObject → VR)│           │
│        └───────────┬──────────┘               └───────────┬──────────┘           │
│                    │                                       │                     │
│                    ▼                                       ▼                     │
│        ┌────────────────────────┐             ┌────────────────────────┐         │
│        │ InterpretationFrame    │             │ InterpretationFrame    │         │
│        │ (InterpretationObject) │             │ (InterpretationObject) │         │
│        └────────────────────────┘             └────────────────────────┘         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ Player interaction (select, inspect,
                                         │ add interpretation → governed write)
                                         │
                         ┌───────────────▼──────────────────────────┐
                         │               PlayerRig                  │
                         │   • XR Rig / FPS Controller              │
                         │   • SelectionRaycaster                   │
                         │   • UiInspectorController                │
                         └──────────────────────────────────────────┘
                                         │
                                         │ User actions → CRK‑1 API
                                         ▼
                         ┌──────────────────────────────────────────┐
                         │           CRK‑1 GOVERNANCE GATE          │
                         │   (Receipt Verifier + Merkle Spine)      │
                         └──────────────────────────────────────────┘
```

## How to read this diagram

**CRK-1 is the authoritative backend** — all truth and governance live there; every mutation requires receipts.

**Unity is a spatial renderer** — visualizes continuity; never decides truth or bypasses governance.

**Continuity Space** — identity nodes, decision branches, outcome shards, evidence trails, interpretation frames.

**PlayerRig** — navigation, selection, inspection, governed writes.

## Governed write path

```
Unity → CRK-1 API → Governance Engine → Receipt → Merkle Root → Unity update
```

No shortcuts. No god mode. No founder override.
