# Nova Flight-Deck UI — Figma-Ready Mockup Specification

**Version:** 1.0  
**Purpose:** Visual blueprint for the multi-agent cockpit ("Flight Deck"). Defines frames, layout, and component constraints for designers and UI engineers.

**Companion:** Single-agent cockpit spec in `cockpit/src/styles/tokens.json` and [Figma design spec](../../cockpit/README.md).

---

## 1. Top-Level Frames

### Frame: `FlightDeck / Shell`

**Layout:** 3-column grid + bottom band

```
┌──────────────────────────────────────────────────────────────────┐
│ TOP: Cluster identity | Aggregate kernel status | Active agents   │
├──────────────┬───────────────────────────────┬───────────────────┤
│ LEFT         │ CENTER                        │ RIGHT             │
│ Agent        │ Multi-Agent Canvas              │ Cluster Health    │
│ Selector     │ (mode-switchable)               │ Rail              │
├──────────────┴───────────────────────────────┴───────────────────┤
│ BOTTOM: Cluster Timeline (multi-agent continuity + divergence)    │
└──────────────────────────────────────────────────────────────────┘
```

| Region | Width | Background token |
|--------|-------|------------------|
| Agent Selector | 280px fixed | `bg.rail` (#070914) |
| Multi-Agent Canvas | flex 1 | `bg.panel` (#0B0E1A) |
| Cluster Health Rail | 320px fixed | `bg.rail` (#070914) |
| Bottom band | 80px height | `bg.panel` (#0B0E1A) |

---

### Frame: `FlightDeck / AgentCard`

**Variants:**

- `status` = `nominal` | `drift` | `violation` | `offline`
- `mode` = `compact` | `expanded`

**Auto-layout:** vertical, padding 16, gap 12

**Fields:**

| Field | Typography | Notes |
|-------|--------------|-------|
| Agent ID | Mono 13px | Truncate with ellipsis |
| Kernel status | UI 12px + status pill | ok / warn / error |
| Active goal | UI 14px secondary | Max 2 lines |
| Recent receipts | Mono 11px chips | Last 3 receipt IDs |

**Status colors:**

| State | Color | Token |
|-------|-------|-------|
| Nominal | #27AE60 | `status.ok` |
| Drift | #F2C94C | `status.warn` |
| Violation | #EB5757 | `status.error` |
| Offline | #6B7390 | `text.muted` |

---

### Frame: `FlightDeck / ClusterMap`

**Visualization:** Directed node graph

- **Nodes:** agents (AgentCard compact embedded or icon + label)
- **Edges:** shared goals, dependencies, or receipt propagation
- **Node states:** green = nominal, yellow = drift, red = violation, gray = offline

**Constraints:**

- Min node width: 120px
- Edge stroke: 1px `border.soft`
- Canvas: scrollable both axes
- Padding: 24px

---

### Frame: `FlightDeck / LedgerCompare`

**Layout:** Two-column receipt diff

- **Auto-layout:** horizontal
- **Column min width:** 45%
- **Scroll:** independent per column
- **Header row:** Agent A ID | Agent B ID
- **Rows:** receipt ID, action type, invariants checked, continuity hash, ledger hash, timestamp

**Highlight rules:**

- Mismatch cells: `status.error` background 15% opacity
- Match cells: no fill
- Missing receipt: dashed border + "missing" label

---

### Frame: `FlightDeck / ContinuityMatrix`

**Grid:** agents (rows) × snapshots (columns)

| Cell state | Visual | Meaning |
|------------|--------|---------|
| `match` | Green dot | Hash matches canonical |
| `mismatch` | Red dot | Hash diverges |
| `missing` | Gray dash | No snapshot for agent at step |

**Cell size:** 32×32px hit target  
**Selected cell:** 2px `accent.nova` ring

---

## 2. Component Library

### Agent Selector

- Scrollable list of `AgentCard` (compact)
- Status pill per agent
- Kernel heartbeat indicator (pulsing dot when nominal)
- "Add agent" affordance (secondary button)

### Cluster Health Rail

Sections (vertical stack, gap 16):

1. **Aggregate CRK-1** — invariant engine, ledger, continuity (cluster rollup)
2. **Per-agent kernel** — mini grid 2×N
3. **Violations** — last 10 cluster-wide, grouped by invariant ID
4. **Drift alerts** — agents in `drift` state with link to LedgerCompare

### Multi-Agent Canvas Modes

| Mode ID | Component | Primary use |
|---------|-----------|-------------|
| `cluster-map` | ClusterMap | Topology overview |
| `ledger-compare` | LedgerCompare | Receipt divergence |
| `continuity-matrix` | ContinuityMatrix | Cross-agent replay audit |
| `plan-diff` | Plan graph side-by-side | Cognition divergence |

Mode switch: left rail tabs or top bar segmented control.

### Cluster Timeline

- Horizontal scroll, combined agent continuity
- Node types: snapshot (cyan), receipt (gold), violation (red), divergence (orange diamond)
- Spacing between nodes: 48px
- Connector line: `border.soft`

---

## 3. Visual Language

### Colors (extend cockpit tokens)

| Token | Hex | Use |
|-------|-----|-----|
| `accent.nova` | #3A7BFF | Selection, cognition |
| `accent.governance` | #F2C94C | Receipts |
| `accent.continuity` | #56CCF2 | Snapshots |
| `status.ok` | #27AE60 | Nominal |
| `status.warn` | #F2C94C | Drift |
| `status.error` | #EB5757 | Violation |
| `bg.shell` | #050711 | Shell |
| `bg.panel` | #0B0E1A | Canvas |
| `bg.rail` | #070914 | Side rails |
| `border.soft` | #1C2238 | Dividers |

### Typography

- **UI:** Inter — Title 20px, Section 16px, Body 14px
- **Mono:** JetBrains Mono — Receipts, diffs, logs 13px

### Spacing

- Base grid: **16px**
- Sub-grid: **8px**
- Panel padding: **16px**
- Panel radius: **8px**
- Panel shadow: `0 12px 40px rgba(0,0,0,0.45)`

---

## 4. Interaction Rules

| Action | Result |
|--------|--------|
| Click agent in selector | Highlight agent path in cluster map; filter timeline |
| Click divergence marker | Open `ledger-compare` for involved agents |
| Click matrix mismatch cell | Open continuity replay for that agent + snapshot |
| Hover heartbeat dot | Tooltip: invariant engine, ledger, continuity, violations/min |
| Double-click AgentCard | Expand to `expanded` variant in selector |
| Receipt chip click | Open receipt detail; optional cross-link to peer agent |

**Animations (align with single-agent cockpit):**

- Violation: `flash-red` 600ms on Cluster Health Rail
- New receipt: `pulse-gold` 800ms on bottom band
- Drift detected: yellow border pulse on AgentCard 1.2s

---

## 5. Figma File Structure (recommended)

```
Nova / FlightDeck
├── Shell
├── AgentCard (variants: status × mode)
├── ClusterMap
├── LedgerCompare
├── ContinuityMatrix
├── AgentSelector
├── ClusterHealthRail
├── ClusterTimeline
└── Tokens
    ├── Color styles
    └── Text styles (UI/Body, UI/Label, Mono/Receipt)
```

**Hand-off:** Export `tokens.json` from `cockpit/src/styles/tokens.json` as Figma variables where possible.

---

## 6. Implementation mapping

| Figma frame | React target (future) |
|-------------|------------------------|
| FlightDeck / Shell | `cockpit/src/flightdeck/FlightDeckShell.tsx` |
| AgentCard | `flightdeck/AgentCard.tsx` |
| ClusterMap | `flightdeck/ClusterMap.tsx` |
| LedgerCompare | `flightdeck/LedgerCompare.tsx` |
| ContinuityMatrix | `flightdeck/ContinuityMatrix.tsx` |

**Event source:** `MultiAgentBridge` (WebSocket) + per-agent `NovaEventBridge` instances.

---

## Related documents

- [Level 2 Certification](./OPERATOR-LEVEL-2-CERTIFICATION.md)
- [CRK-1 Kernel Integrity Test Suite](../integrity/CRK-1-KERNEL-INTEGRITY-TEST-SUITE.md)
- Cockpit tokens: `cockpit/src/styles/tokens.json`
