# Nova Control Tower — Multi-Agent Orchestration Layer

**Version:** 1.0  
**Purpose:** Distributed orchestration for multi-agent Nova clusters.

Implementation: `control-tower/`

---

## 1. Architecture

Control Tower provides:

- Multi-agent orchestration
- Cross-agent continuity and ledger coherence
- Drift detection and correction
- Cluster-wide invariants and goals
- Distributed PIT-band alignment
- Cluster-wide constitutional enforcement

---

## 2. Module Layout

```
control-tower/
  orchestrator/
    cluster-manager.ts
    agent-registry.ts
    drift-detector.ts
    consensus-engine.ts
  protocols/
    heartbeat.ts
    continuity-sync.ts
    ledger-sync.ts
    pit-sync.ts
  replay/
    cluster-replay.ts
  drift/
    drift-simulator.ts
```

UI: `cockpit/src/flight-deck/` (Flight Deck mode)

---

## 3. Core Algorithms

### Drift Detection

```ts
function detectDrift(agentA, agentB) {
  const receiptsA = ledger.get(agentA)
  const receiptsB = ledger.get(agentB)
  return diff(receiptsA, receiptsB)
}
```

### Continuity Sync

```ts
function syncContinuity(agentA, agentB) {
  const snapsA = continuity.list(agentA)
  const snapsB = continuity.list(agentB)
  return reconcile(snapsA, snapsB)
}
```

### Consensus

```ts
function consensus(goal, agents) {
  const plans = agents.map((a) => a.plan(goal))
  return mergePlans(plans)
}
```

---

## 4. Cluster-Level Invariants

- No cross-agent divergence
- No conflicting plans
- No ledger forks
- No continuity mismatches
- PIT-band alignment required

---

## 5. Operator Workflow

Select cluster → set goal → generate cross-agent plan → validate coherence → execute governed steps → monitor drift → resolve divergence → validate continuity and ledger → sign off.

---

## Related

- [Control Tower Consensus](./NOVA-CONTROL-TOWER-CONSENSUS.md)
- [Flight Deck React](../operator/NOVA-FLIGHT-DECK-REACT.md)
