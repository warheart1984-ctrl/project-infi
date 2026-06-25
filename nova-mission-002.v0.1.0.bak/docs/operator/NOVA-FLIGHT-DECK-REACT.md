# Nova Flight Deck — Full React Implementation (Skeleton)

**Version:** 1.0  
**Purpose:** Multi-agent cockpit UI for Nova clusters.

Implementation lives in `cockpit/src/flight-deck/` (cockpit is the unified frontend).

---

## 1. Directory Structure

```
cockpit/src/flight-deck/
  FlightDeckShell.tsx
  AgentSelector.tsx
  ClusterMap.tsx
  LedgerCompare.tsx
  ContinuityMatrix.tsx
  ClusterTimeline.tsx
  KernelStatusRail.tsx
  flightDeck.module.css
cockpit/src/state/
  clusterStore.ts
  driftStore.ts
  kernelStore.ts
cockpit/src/bridge/
  WebSocketBridge.ts
```

---

## 2. FlightDeckShell.tsx

```tsx
import { AgentSelector } from "./AgentSelector"
import { ClusterMap } from "./ClusterMap"
import { KernelStatusRail } from "./KernelStatusRail"
import { ClusterTimeline } from "./ClusterTimeline"
import styles from "./flightDeck.module.css"

export function FlightDeckShell() {
  return (
    <div className={styles.shell}>
      <div className={styles.left}><AgentSelector /></div>
      <div className={styles.center}><ClusterMap /></div>
      <div className={styles.right}><KernelStatusRail /></div>
      <div className={styles.bottom}><ClusterTimeline /></div>
    </div>
  )
}
```

---

## 3. clusterStore.ts (Zustand)

```ts
import { create } from "zustand"

export const useClusterStore = create((set) => ({
  agents: {} as Record<string, ClusterAgent>,
  selectedAgent: null as string | null,
  clusterEvents: [] as ClusterEvent[],
  replayWindow: null as { from?: string; to?: string } | null,
  actions: {
    updateAgentStatus: (id, patch) =>
      set((state) => ({
        agents: { ...state.agents, [id]: { ...state.agents[id], ...patch } },
      })),
    addClusterEvent: (event) =>
      set((state) => ({ clusterEvents: [event, ...state.clusterEvents] })),
    selectAgent: (id) => set({ selectedAgent: id }),
    setReplayWindow: (replayWindow) => set({ replayWindow }),
  },
}))
```

---

## 4. MultiAgentBridge / WebSocketBridge

Connects to `backend/events-gateway` WebSocket. On `heartbeat` → update agent kernel status. On `event` → append cluster events. On `drift` → update `driftStore`.

---

## 5. Center Canvas Integration

In `CenterCanvas.tsx`, when `centerMode === "flight-deck"` render `FlightDeckShell`. When `centerMode === "drift"` render `DriftVisualizer`.

---

## Related

- [Flight Deck Mockup (Figma)](./NOVA-FLIGHT-DECK-MOCKUP.md)
- [Control Tower](../NOVA-CONTROL-TOWER.md)
- [Architecture](../ARCHITECTURE.md)
