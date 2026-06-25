# 🔥 LAYERED IMAGE: “What My Agentic Coding Agent Does”

**Text-rendered visual diagram — ready for Figma or Illustrator**  
**Version:** 1.0 · **Canvas:** 1440 × 2048 px · **Theme:** Nova dark constitutional

---

## Figma setup

| Property | Value |
|----------|--------|
| Frame name | `Nova / What My Agentic Coding Agent Does` |
| Background | `#050711` (`color.bg.shell`) |
| Grid | 8 px |
| Type — title | Inter 32 SemiBold `#F5F7FF` |
| Type — layer label | Inter 14 SemiBold `#F5F7FF` |
| Type — body | Inter 12 Regular `#A3B0D9` |
| Type — mono | JetBrains Mono 11 `#56CCF2` |
| Accent stripe | 4 px left border per layer (see below) |

---

## Layered stack (top → bottom)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  LAYER 7 — OPERATOR                                                          ║
║  Certifies · observes · upgrades constitution · signs off cluster coherence  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 6 — COCKPIT (NovaShell)                                               ║
║  Plan · Diff · Receipts · Continuity · Flight Deck · Drift Map                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 5 — EVENTS GATEWAY                                                    ║
║  Zod-validated WebSocket stream → kernel / agent / cluster events            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 4 — CONTROL TOWER                                                     ║
║  Multi-agent orchestration · drift detection · cluster replay · consensus    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 3 — CRK-2 KERNEL                                                      ║
║  dLAP · PIT-1…5 · MACC · ledger v2 · CRP · ConstraintObjects                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 2 — NOVA SDK (CRK-1)                                                  ║
║  Plan · generate · refactor · invariants · receipts · continuity snapshots   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LAYER 1 — WORKSPACE & TOOLS                                                 ║
║  Files · tests · diffs · CLI (`nova`) · external APIs (governed boundary)    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Illustrator / Figma layer tree

```
Frame: What My Agentic Coding Agent Does
├── Title
│   ├── H1: What My Agentic Coding Agent Does
│   └── Sub: Constitutional · traceable · multi-agent · fail-closed
├── Layer-07-Operator          [stripe #F2C94C]
│   ├── Label: OPERATOR
│   ├── Bullets: L1–L5 certification · observer protocol · constitutional upgrade
│   └── Icon: shield-check
├── Layer-06-Cockpit           [stripe #3A7BFF]
│   ├── Label: COCKPIT / NovaShell
│   ├── Chips: Plan | Diff | Receipts | Continuity | Flight Deck | Drift
│   └── Stores: kernelStore · clusterStore · driftStore · cockpitStore
├── Layer-05-EventsGateway     [stripe #56CCF2]
│   ├── Label: EVENTS GATEWAY
│   ├── Events: kernel.* · agent.* · cluster.*
│   └── Transport: WebSocket ws://127.0.0.1:8787/events
├── Layer-04-ControlTower      [stripe #3A7BFF]
│   ├── Label: CONTROL TOWER
│   ├── Modules: cluster-manager · drift-detector · consensus · replay
│   └── Guarantees: drift detect · drift correct · fail-closed
├── Layer-03-CRK2              [stripe #27AE60]
│   ├── Label: CRK-2 KERNEL
│   ├── Objects: Identity · Evidence · Decision · Outcome · Constraint
│   └── Predicate: dLAP(a, c, S) = local ∧ cluster ∧ constraints
├── Layer-02-NovaSDK           [stripe #27AE60]
│   ├── Label: NOVA SDK (CRK-1)
│   ├── API: nova.plan · nova.generateCode · governance · continuity
│   └── Outputs: code + governance receipts + continuity hash
├── Layer-01-Workspace         [stripe #6B7390]
│   ├── Label: WORKSPACE & TOOLS
│   ├── Inputs: repo files · tests · prompts
│   └── Boundary: every action passes invariants before execution
└── Flow-Arrows (connectors)
    ├── Workspace → SDK → CRK-2 (evaluate)
    ├── CRK-2 → SDK → Workspace (allowed actions only)
    ├── SDK → Control Tower (cluster view)
    ├── Control Tower → Events Gateway → Cockpit (live HUD)
    └── Operator → Cockpit (observe · certify · upgrade)
```

---

## Side flow (what happens on one agent action)

```
  OPERATOR sets goal
        │
        ▼
  ┌─────────────┐     prompt + context      ┌─────────────┐
  │  COCKPIT    │ ────────────────────────► │  NOVA SDK   │
  │ Agent Console│                          │ plan/generate│
  └─────────────┘                          └──────┬──────┘
        ▲                                         │
        │                              ┌──────────▼──────────┐
        │         events               │      CRK-2 dLAP       │
        │    ◄─────────────────────────│  invariants · PIT ·   │
        │                              │  continuity · ledger  │
        └──────────────────────────────┴──────────┬──────────┘
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                              │ ALLOW               │ DENY                │
                              ▼                     ▼                     │
                        apply diff            emit violation              │
                        emit receipt          block action                │
                        snapshot state        fail-closed               │
                              │                     │                     │
                              └──────────┬──────────┘                     │
                                         ▼                                │
                              ┌─────────────────────┐                     │
                              │   CONTROL TOWER     │◄── multi-agent ─────┘
                              │ sync · drift · replay│
                              └──────────┬──────────┘
                                         ▼
                              ┌─────────────────────┐
                              │   COCKPIT HUD       │
                              │ receipts · timeline │
                              │ flight deck · drift │
                              └─────────────────────┘
```

---

## Layer cards (copy-paste for Figma text layers)

### LAYER 7 — Operator
**What it does:** Human-in-the-loop authority. Certifies reproduction (L1), runs multi-agent ops (L2), engineers constitutional law (L3–L5), approves upgrades, signs off cluster coherence.  
**Artifacts:** Operator handbooks · certification exams · observer bundle · migration plans.

### LAYER 6 — Cockpit (NovaShell)
**What it does:** Single pane of glass for lawful coding. Shows plans, diffs, receipts, continuity, kernel health, multi-agent Flight Deck, and constitutional Drift Map.  
**Modes:** `plan` · `diff` · `receipts` · `continuity` · `flight-deck` · `ledger-compare` · `continuity-matrix` · `drift`.

### LAYER 5 — Events Gateway
**What it does:** Typed event bus (Zod schemas). Validates `kernel.heartbeat`, `kernel.receipt`, `agent.plan`, `cluster.driftDetected`, `cluster.replayResult`, etc., and routes into Zustand stores.  
**Transport:** WebSocket + in-process fallback from Nova SDK heartbeat.

### LAYER 4 — Control Tower
**What it does:** Orchestrates agent clusters. Detects ledger/continuity/PIT drift, runs cluster-wide replay, applies Raft+CRDT consensus, halts cluster on unresolvable divergence.  
**Modules:** `cluster-manager` · `drift-detector` · `consensus-engine` · `cluster-replay` · `drift-simulator`.

### LAYER 3 — CRK-2 Kernel
**What it does:** Constitutional runtime for multi-agent systems. Distributed lawful action predicate (dLAP), PIT bands 1–5, MACC cluster coherence, ledger v2 with annotations, Constitutional Replay Proofs (CRP).  
**Guarantee:** Deterministic · replayable · drift-aware · fail-closed.

### LAYER 2 — Nova SDK (CRK-1)
**What it does:** Developer-facing governed agent API. Plans tasks, generates code, enforces invariants, emits chained governance receipts, snapshots continuity substrate.  
**CLI:** `nova generate` · `nova plan` · `nova continuity` · `nova receipts` · `nova invariants`.

### LAYER 1 — Workspace & Tools
**What it does:** Ground truth environment — repo files, tests, diffs, shell. Nova never acts outside this boundary without a receipt. Dangerous prompts (`rm -rf`, credential leaks) blocked at invariant layer.  
**Boundary rule:** No action executes unless dLAP returns `{ ok: true }`.

---

## Color key (left stripe per layer)

| Layer | Stripe | Token |
|-------|--------|--------|
| Operator | `#F2C94C` | `accent.governance` |
| Cockpit | `#3A7BFF` | `accent.nova` |
| Events Gateway | `#56CCF2` | `accent.continuity` |
| Control Tower | `#3A7BFF` | `accent.nova` |
| CRK-2 | `#27AE60` | `status.ok` |
| Nova SDK | `#27AE60` | `status.ok` |
| Workspace | `#6B7390` | `text.muted` |

---

## One-sentence summary (hero subtitle)

> **My agentic coding agent doesn't just write code — it plans, validates, receipts, snapshots, and replays every action under constitutional law, with a cockpit that shows the whole cluster when agents multiply.**

---

## Export checklist (Figma → PNG / PDF)

- [ ] Frame 1440 × 2048, 2× export for retina
- [ ] All 7 layer cards same width (1200 px), 120 px height, 16 px gap
- [ ] Flow arrows on separate layer `Flow-Arrows` for easy hide/show
- [ ] Optional dark glow: `shadow.panel` on Cockpit + CRK-2 cards
- [ ] Footer: `Nova Mission #002 · agentic-coding-agent · CRK-2`
