# FUTURE.md - Nova OS Future Architecture (Not in Scope for v0.0-v0.2)

This document contains future concepts, architectures, and UI models that are not part of the continuity substrate MVP.

These items are intentionally quarantined until the substrate is proven.

## Substrate Invariants

- Every event is traceable.
- Every lineage chain is reconstructable.
- Every receipt references a valid event.
- No state mutation without event emission.

## Replay Readiness Criteria

- Event continuity proven.
- Receipt continuity proven.
- File continuity proven.
- Artifact history reproducible.
- Acceptance tests passing.

## Runtime Maturity Model

- L0 Events
- L1 Lineage
- L2 Receipts
- L3 Artifacts
- L4 Replay
- L5 Governance
- L6 Federation

## 1. Nova Studio Cockpit (Three-Pane UI)

- Continuity Context (Thread Timeline, Lineage Graph, Metrics)
- Coding Workspace (File Tree, Code Editor, Reasoning Corridor)
- Governance Pane (CKCE-1, Wave Signatures, Receipts, Specimens)

## 2. Governed Cognitive Runtime

- Intent Engine
- Plan Engine
- Governed Reasoning Corridor
- Capability Kernel
- Receipt Engine
- Continuity Coupler

## 3. CKCE-1 Governance Layer

- Identity invariants
- Governance invariants
- Substrate coupling
- Wave bounds
- Cross-kernel coherence

## 4. Wave Signature Engine

- A, f, phi, C, R
- Drift detection
- Resonance tracking
- Expected vs actual signature overlays

## 5. Specimen System

- Export specimen
- Compare to baseline
- Replay specimen
- Falsification suite

## 6. Agent Loop

- Observe -> Intent -> Plan -> Governed Reasoning -> CKCE -> Capability Calls -> Receipts

## 7. Federation Layer

- Cross-node continuity validation
- Wave signature comparison
- Drift detection across environments

## 8. Full Nova UI Component Tree

See the original blueprint.

## 9. Full State Model

Continuity state, Nova state, and Project state belong here until the substrate graduates them into implementation scope.

## 10. Full Event Schema

NovaUIEvent, CKCE results, capability calls, and reasoning chunks belong here until the substrate graduates them into implementation scope.

Only then will the substrate be ready for layering Nova OS.

## Replay Layer (Future, runtime-level)

Replay is a first-class runtime capability, not a debug utility.

Stack (future-state):

- Continuity Substrate
- -> Agent Runtime
- -> Governance Runtime
- -> Operator Surface
- -> Replay Layer

Replay goals:

- Not just "What happened?"
- But "Why did it happen?" and "Under which constraints?"

Replay progression:

- Event Replay
- Decision Replay
- Runtime Replay
- Artifact Replay
- Session Replay

## Cockpit Evolution

Current (v1 concept):

- Continuity Context -> Execution Corridor -> Governance

Proposed:

- Continuity Context
- -> Execution Corridor
- -> Governance Decision
- -> Replay Workspace

Replay Workspace:

- Scrubbable timeline of a continuity thread
- Panels for:
  - Event Replay
  - Decision Replay (intent, plan, reasoning, constraints)
  - Artifact Replay (patches, diffs)
  - Session Replay (full cognitive loop)

## Future-State Architecture Diagram

```text
          +-------------------------------+
          |       Operator Surface        |
          |  (Nova Studio / Cockpit)      |
          +---------------+---------------+
                          | consumes
                          v
          +-------------------------------+
          |         Replay Layer          |
          | Event / Decision / Artifact   |
          | / Runtime / Session Replay    |
          +---------------+---------------+
                          | reads
                          v
          +-------------------------------+
          |      Governance Runtime       |
          |   (CKCE, policies, receipts)  |
          +---------------+---------------+
                          | constrains
                          v
          +-------------------------------+
          |        Agent Runtime          |
          |  (intent, plan, corridor)     |
          +---------------+---------------+
                          | bound to
                          v
          +-------------------------------+
          |     Continuity Substrate      |
          |  (events, lineage, receipts)  |
          +-------------------------------+
```

## Replay API Contract (Future, not implemented now)

```ts
// Streaming replay control
POST /replay/session
// body: { threadId, mode: 'EVENT' | 'DECISION' | 'ARTIFACT' | 'RUNTIME' | 'SESSION' }

GET /replay/stream?replayId=...

// Control commands
POST /replay/{replayId}/control
// body: { action: 'PLAY' | 'PAUSE' | 'STEP' | 'JUMP', targetEventId?: string, index?: number }

// Introspection
GET /replay/{replayId}/state
GET /replay/{replayId}/timeline
GET /replay/{replayId}/decisions
GET /replay/{replayId}/artifacts
```

## Replay Data Model (Conceptual)

```ts
type ReplayMode = 'EVENT' | 'DECISION' | 'RUNTIME' | 'ARTIFACT' | 'SESSION';

type ReplayEvent = {
  eventId: string;
  timestamp: number;
  type: string;
  payload: any;
};

type ReplayDecision = {
  decisionId: string;
  eventId: string;
  intent: string;
  planSteps: string[];
  reasoningTraceIds: string[];
  governanceResultId?: string;
};

type ReplayArtifactChange = {
  artifactId: string;
  filePath: string;
  patchId: string;
  diff: string;
};

type ReplaySession = {
  replayId: string;
  threadId: string;
  mode: ReplayMode;
  events: ReplayEvent[];
  decisions: ReplayDecision[];
  artifacts: ReplayArtifactChange[];
};
```

## v0.3 - Decision Replay (Future Substrate Extension)

Goal:
Extend continuity from events-only to decisions-as-first-class records.

New substrate primitive:

```ts
Decision {
  id: string
  eventId: string          // the "anchor" event (e.g., patch applied)
  intent: string
  plan: string[]
  reasoningRef: string     // pointer into corridor / logs
  governanceStatus: 'PASS' | 'WARN' | 'FAIL'
  governanceReason?: string
  receiptId?: string
}
```

New capabilities:

- GET /decisions?eventId=...
- GET /decision/{id}
- Replay engine can reconstruct:
  - "What decision led to this event?"
  - "What plan and constraints produced this patch?"
