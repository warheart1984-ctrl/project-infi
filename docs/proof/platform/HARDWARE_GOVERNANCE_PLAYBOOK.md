# Hardware Governance Playbook (Sovereign OS)

This is the operating playbook for hardware governance in Sovereign OS. It is the canonical guide for stewards who need to understand how CPU, GPU, replay, benchmarking, routing, ProofSurface, and the Hardware Console fit together.

## 1. Constitutional principles

- No routing without evidence: every hardware routing decision must reference at least one hardware artifact.
- Safety over performance: thermal, memory, and error safety constraints override latency and throughput gains.
- Hardware as a governed surface: CPU and GPU state, routing, replay, and benchmarks must be visible in the Hardware Console.
- Explainability: ProofSurface must reconstruct the chain `workload -> route -> evidence -> decision`.
- Replayability: high-impact workloads must have counterfactual replays for route changes.

## 2. Core artifacts and ledger

- `HardwareNodeSnapshot`: live node state, including utilization, temperature, memory, backend, and quarantine.
- `RoutingDecisionArtifact`: chosen route plus scores and evidence IDs.
- `HardwareBenchmarkArtifact`: standardized workload metrics per route.
- `HardwareReplayEvidenceArtifact`: current vs counterfactual metrics plus deltas.
- `HardwareEvidenceLedger`: chronological record of all hardware constitutional artifacts.

Use the ledger as the single source of truth for the Temporal Ribbon and ProofSurface.

## 3. Hardware Governor algorithm

Operational loop:

1. Collect context
   - `hardwareSnapshot = telemetry.getSnapshot()`
   - `benchmarks = cepStore.getHardwareBenchmarksFor(workload)`
   - `replays = cepStore.getHardwareReplaysFor(workload)`
2. Apply safety filters
   - Remove quarantined, thermally unsafe, or memory-overloaded nodes.
3. Score routes
   - `BenchmarkScore(route)` from benchmark metrics.
   - `ReplayScore(route)` from recent replay deltas.
   - `SafetyPenalty(route)` from residual risk.
   - `ConstitutionalScore(route) = BenchmarkScore + ReplayScore - SafetyPenalty`.
4. Choose route
   - Pick the highest constitutional score that passes safety constraints.
5. Persist decision
   - Create a `RoutingDecisionArtifact` with chosen route, considered routes, and the evidence IDs used.
   - Append it to the `HardwareEvidenceLedger`.

This is the governor's one true way to route workloads.

## 4. Replay DSL and Replay Studio

Replay DSL JSON v1.0.0:

- `scenarioId`
- `workloadId`
- `fromRoute`
- `toRoute`
- `options`
  - `concurrency`
  - `durationSec`
  - `payloadOverride`
- `metadata`

Replay Studio layout:

- Left: author scenario (workload, routes, parameters).
- Right: show metrics comparison, deltas, artifact ID, and "View in ProofSurface".

Auto-suggestions:

- Triggered by thermal risk, memory pressure, error spikes, throttling, benchmark drift, or high-impact route changes.
- Pre-filled scenarios with an accept / edit / dismiss banner.
- Suggestions are logged as ledger entries and surfaced in Replay Studio.

Replay turns "what if" into governed evidence.

## 5. Hardware Console, Temporal Ribbon, and ProofSurface

Hardware Console in ops-console:

- Summary strip for cluster health
- Node grid for per-node metrics and quarantine
- Replay panel for quick counterfactuals
- Benchmark console for run specs
- Hardware artifact viewer for recent decisions, benchmarks, and replays

Temporal Ribbon in the IDE:

- Data contract: `TemporalRibbonResponse { workloads: RibbonWorkloadEntry[] }`
- Each workload strand shows routing, benchmark, and replay events over time.
- Hover for summary; click to open ProofSurface.

ProofSurface:

- Sections: Routing Decision, Constitutional Evidence, Hardware Evidence
- Hardware Evidence shows the benchmark and replay artifacts used in the decision
- The decision must always be traceable back to artifacts and scenarios

These three surfaces are how operators see and trust hardware governance.

## 6. Temporal replay invariants

- Temporal integrity: replay artifacts must reflect actual execution time; ledger order cannot be falsified.
- Scenario fidelity: executed replay must match its DSL definition.
- Decision traceability: any decision citing replay must have a traversable chain to the scenario.
- Non-destructive history: replays annotate, never rewrite, past decisions.
- High-impact replay requirement: route changes for critical workloads must have at least one replay scenario.

This playbook is the hardware chapter of the Codex Eternal: a governed, visible, replayable hardware substrate with no magic and no hidden heuristics.
