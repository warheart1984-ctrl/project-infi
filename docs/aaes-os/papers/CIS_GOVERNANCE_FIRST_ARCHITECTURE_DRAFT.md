# Constitutional Intelligence Systems: A Governance-First Architecture for Drift-Free Cognitive Runtimes

Alternate title: **AAES-OS: A Constitutional Operating System for Governed AI Cognition**

## Abstract

Intelligent systems lack traceability, drift control, and governed evolution. We introduce **Constitutional Intelligence Systems (CIS)**: architectures in which cognition, execution, and evolution are constrained by explicit constitutional law. We present AAES-OS, a constitutional runtime architecture for machine cognition, built on proposal-only cognition, governance-first execution, and evidence-before-complexity.

AAES-OS formalizes invariants, multi-registry governance, amendment processes, and deterministic evidence pipelines. On a production communication substrate (57 ledgered ticks, 5 lanes, sealed canon v1.0.0), we observe mean composite drift of 0.036 against a fail-closed threshold of 0.50, 100% drift-violation logging, and zero unlogged fail-closed events.

This paper's primary contribution is architectural. It does not claim to solve AI governance universally. It introduces a constitutional operating model, a reference implementation, and an evidence model that others can independently evaluate, reproduce, and extend.

## 1. Introduction

Agentic systems drift and lose lineage. OS kernels govern hardware; protocols govern transport; production AI stacks increasingly govern tool access and orchestration. What remains under-specified is the runtime governance of intelligent behavior as constitutional law.

We contribute CIS as a systems field, AAES-OS as a constitutional runtime architecture, CRK-1 as an execution gate, and a multi-registry substrate with amendment and freeze algebra implemented in Continuity OS v1.0.

### 1.1 Claim Taxonomy

This paper distinguishes three claim classes:

| Claim class | Meaning | Evidence treatment |
|-------------|---------|--------------------|
| Architectural claim | Property guaranteed by the specification, including layer separation, provenance model, constitutional contracts, and governance model | Cite normative clauses, contracts, registries, or conformance requirements |
| Implementation result | Measured outcome demonstrated by AAES-OS v1.0, including test results, replay determinism, freeze mechanics, drift measurements, and ledger integrity | Cite executable tests, receipts, replay artifacts, benchmark outputs, release gates, or ledger entries |
| Research hypothesis | Broader claim requiring validation across multiple implementations or production deployments | Label explicitly as hypothesis and keep outside conformance language |

This distinction is part of the evidence-first architecture itself: specifications define intended behavior, implementations demonstrate one realization, evidence establishes what has been achieved, and replication determines confidence.

## 2. Background and Related Work

We organize related work by what each tradition governs, and why none subsumes CIS.

### 2.1 Operating Systems and Kernels

Classic OS research defines protection domains, capabilities, and kernels as the locus of authority [1-8]. seL4 [6] demonstrates formal verification of kernel correctness; Singularity [7] and Capsicum [8] refine capability-safe process models. These systems mediate hardware and address spaces, not semantic proposals from LLM cognition or multi-agent dialogue.

**Gap:** No mainstream OS exposes corridor drift, altitude violations, or amendment-gated constitution mutation as kernel primitives.

**CIS position:** CRK-1 is a normative kernel: an execution gate over evidence-backed state transitions, not over syscalls alone.

### 2.2 Microkernels, Exokernels, and Policy/Kernel Split

Exokernel [2] and microkernel designs [3-5] separate policy from mechanism. CIS adopts this split explicitly.

| Exokernel split | CIS split |
|-----------------|-----------|
| libOS policy | Cognitive runtime proposals |
| exokernel mechanism | CRK-1 authorized transitions |
| untrusted apps | Agents, operators, models |

**Gap:** Exokernels do not require receipts, canon freeze ticks, or Requirements Registry traceability for every policy change.

### 2.3 Formal Methods and Verified Systems

Formal verification [6, 9-11] proves properties of code and protocols. TLA+ [9] and CompCert [10] anchor correctness in logic; IronFleet [11] verifies distributed systems.

**Gap:** LLM outputs are not generally verifiable at the semantic level. CIS does not claim to prove model correctness; it contains runtime behavior via invariants, budgets, and fail-closed gates, empirically evidenced rather than formally proven end-to-end.

### 2.4 Distributed Systems, Consensus, and Audit Logs

Paxos [12], Raft [13], and Spanner [14] provide replication and ordering. Audit logging and provenance [15, 16] support forensic reconstruction.

**Gap:** Consensus orders events; it does not encode normative authority, such as who may change lane contracts and under which amendment.

**CIS position:** Ledgers are governance evidence, not merely replication logs. `communicationTick` and `communicationCanonFreezeTick` are constitutional objects with schema validation.

### 2.5 AI Alignment, Safety, and Constitutional AI

Alignment surveys [17, 18] and RLHF [19] shape model behavior at training time. Constitutional AI [20] uses model self-critique against written principles. CIS uses similar vocabulary at a different layer.

| Anthropic Constitutional AI | CIS / AAES-OS |
|-----------------------------|---------------|
| Training / critique time | Runtime enforcement |
| Soft preference | Hard gate and fail-closed |
| Model-internal | Multi-registry external law |
| No amendment algebra | Lambda amendments and freeze ticks |

**Gap:** Prompt- or training-time constitutions can mutate silently when prompts, tools, or operators change.

### 2.6 Agent Frameworks and Tool-Use Runtimes

Agent orchestration (ReAct, tool-use APIs, and multi-agent frameworks) [21-23] prioritizes capability and latency over lineage and evolution under law.

**Gap:** No standard agent runtime treats canon freeze or cross-lane invariants as first-class governance objects.

### 2.7 Observability, Provenance, and MLOps

Dapper [24], OpenTelemetry [25], and ML metadata stores [26] trace operations and experiments.

**Gap:** Traces are descriptive. CIS adds prescriptive law: execution is blocked when drift envelopes are exceeded.

### 2.8 Software Architecture, ADRs, and Institutional Governance

ADRs [27] document decisions; institutional economics [28, 29] explains charters and amendment costs.

**Gap:** ADRs are not enforced by a kernel. CIS operationalizes charters as runtime artifacts, including `communication-governance-v1.json` and `COMM-CANON.md`, with mutation guards.

### 2.9 Workflow Governance and Consulting Methodology

Continuity OS WMS-1.0 mirrors CRK-1 in organizational workflow space [30]. The CRK-1 x WMS equivalence table shows one semantic grammar across runtime and process.

**Gap:** Workflow models do not execute code. CIS unifies organizational and runtime governance.

### 2.10 Summary: The Unification Gap

No prior system simultaneously provides:

- Proposal-only cognition with kernel-gated execution
- Multi-registry traceability from principle to requirement, spec, test, and receipt
- Constitutional amendment and freeze with cryptographic anchoring
- Drift budgets with epoch containment and cross-lane invariants
- Deterministic replay of governed communication

CIS / AAES-OS is designed to fill this architectural gap. Continuity OS v1.0 is the reference implementation evaluated here.

## 3. Model, Substrate, Architecture, and Amendment

The full model includes:

- 12 governance objectives across 6 axes, including `GOV.PLAN.PROPOSAL_ONLY` and `GOV.GOV.FAILED_INVARIANTS_FAIL_CLOSED`
- CRK-1 loop: evidence -> interpretation -> policy evaluation -> outcome -> drift envelope
- 5 communication lanes, 8 COMM-CANON sections, and cross-lane invariants X-1, X-2, X-3
- Amendments AAIS-COMM-Lambda-001 and AAIS-COMM-Lambda-002; post-freeze unlock requires AAIS-COMM-Lambda-003
- `communicationCanonFreezeTick` with SHA-256 over sealed markdown

## 4. Evaluation Frame

We evaluate AAES-OS around three systems questions.

### 4.1 Can the Architecture Be Implemented?

Demonstrated through the reference implementation, deterministic replay, freeze mechanics, conformance tests, and release gates.

### 4.2 Can the Architecture Be Independently Verified?

Demonstrated through deterministic replay, provenance, content-addressed receipts, COR/CAR/CAV-style registries, and the conformance ecosystem.

### 4.3 Can the Architecture Evolve Without Losing Constitutional Integrity?

Demonstrated through amendments, governance receipts, canonical freeze, and founder-independent stewardship.

These questions separate architectural feasibility, implementation evidence, and long-term governance claims. They also prevent measured outcomes from the reference implementation from being mistaken for universal guarantees about all future intelligent systems.

## 5. Evaluation

Data come from `.runtime/` ledgers (evaluation snapshot 2026-06-27) and the CI test suite. The evaluated substrate is the Nova Studio communication governance stack: lane registry, epoch manager, drift engine, continuity fold, canon generator/diff engine, and Semantic Bridge reply guard.

### 5.1 Experimental Setup

Workloads:

- Live operator traffic through the `communicationTick` append path
- CI governance tests for corridor/identity drift injection, amendment flow, and canon freeze isolation
- Continuity fold over runtime, governance, cockpit, and communication drift

Thresholds in COMM-CANON v1.0.0: warn 0.05, notify 0.15, containment epoch 0.30, fail-closed 0.50.

### 5.2 Drift Reduction and Containment

**Table 1: Communication drift statistics (N = 57 communicationTick records)**

| Metric | Value | Threshold | Headroom |
|--------|-------|-----------|----------|
| Mean composite drift | 0.036 | fail-closed 0.50 | 92.8% |
| p95 composite drift | 0.125 | notify 0.15 | 16.7% |
| Max composite drift | 0.250 | containment 0.30 | 16.7% |
| Ticks with `corridor_status = ok` | 39 (68.4%) | n/a | n/a |
| Identity drift detections | 14 (24.6%) | n/a | all logged |
| Corridor drift detections | 2 (3.5%) | n/a | all logged |

**Table 2: Drift containment actions (N = 14 communicationDriftTick records)**

| Action | Count | fail-closed |
|--------|-------|-------------|
| warning | 13 | 0 |
| notify_operator | 1 | 0 |
| containment_epoch | 0 | n/a |
| fail_closed | 0 | 0 |

Interpretation: under live load, the substrate operated below containment epoch. This demonstrates budgeted headroom and full violation logging, not absence of drift.

**Table 3: Per-lane drift**

| Lane | Ticks | Mean composite | Max |
|------|-------|----------------|-----|
| jon-darz-architecture | 40 | 0.047 | 0.250 |
| jon-darz-human | 12 | 0.000 | 0.000 |

The architecture lane carries semantic load; the human sink lane shows zero drift, supporting the lane-isolation implementation result.

### 5.3 Epoch and Budget Enforcement

**Table 4: Communication epochs (N = 8)**

| Status | Count |
|--------|-------|
| ACTIVE | 6 |
| CONTAINED | 2 |

Two epochs reached `CONTAINED` under budget rules, demonstrating automatic epoch termination.

### 5.4 Multi-Agent Safety: Reroute and Invariants

| Mechanism | Count / status |
|-----------|----------------|
| Auto-reroute events (`reroutes.jsonl`) | 24 |
| Cross-lane invariants X-1, X-2, X-3 | 3/3 pass in CI |
| Spec-lane human-bandwidth reroute test | pass |

The reroute path shows pre-execution correction when messages violate lane corridors, such as human-category traffic entering a spec-only lane.

### 5.5 Unified Continuity Fold

**Table 5: Continuity containment events (N = 72 continuityContainmentTick)**

| State | Count |
|-------|-------|
| NOTIFY | 48 |
| OK | 12 |
| HALTED | 12 |

The fold merges runtime, governance, cockpit, and communication drift into one `continuity_score`. HALTED events correspond to kill-switch or fail-closed paths.

### 5.6 Governance and Amendment Overhead

**Table 6: Governance ticks (N = 28)**

| decision_type | Count |
|---------------|-------|
| propose-amendment | 14 |
| approve-amendment | 14 |

Amendment propose/approve pairs complete with `comm_constitution_version: 1.0.0` on all 57 communication ticks, producing 100% version stamping in the evaluation snapshot.

### 5.7 Deterministic Replay and Reproducibility

| Artifact | Role |
|----------|------|
| `ticks.jsonl` (57 records) | Replay communication decisions |
| `canonDiffEngine` + frozen baseline | Structural diff vs `COMM-CANON@1.0.0` |
| `communicationCanonFreezeTick` | SHA-256 anchor |
| Schema validators | Reject malformed ticks at ingest |

**CI reproducibility**

| Suite | Tests | Pass |
|-------|-------|------|
| Semantic bridge + communication governance | 42 | 42 |
| Constitutional audit | 5 | 5 |
| Canon freeze isolation | 5 | 5 |

Replay procedure: load JSONL ticks, re-run `enforceCommunicationTick`, then compare `drift_vector.composite` and containment action. CI tests confirm stable corridor/identity classification.

### 5.8 Case Study: COMM-CANON v1.0.0 Freeze

Procedure: `freezeCommunicationCanon("jon", "1.0.0")`

Results:

- Sealed markdown: `Status: SEALED`, `Canon State: FROZEN`
- Baseline ID: `COMM-CANON@1.0.0`
- Ledger entry: `communicationCanonFreezeTick` with SHA-256 hash
- Runtime lock-in: all lanes stamped with `comm_constitution_version: 1.0.0` and `canon_state: FROZEN`
- Mutation guard: `writeCommunicationCanon`, `splitLane`, and `applyConstitutionUpdate` blocked without AAIS-COMM-Lambda-003
- UI: Canon Viewer FROZEN banner; Regenerate disabled
- Post-freeze strict mode: ticks stamped `canon_state: FROZEN`; drift thresholds use strict comparison; reply guard enforces session budget headroom

This is the paper's central systems result: one operator action produces an immutable constitutional baseline and stricter enforcement without silent substrate reshape.

### 5.9 Limitations

- Evaluation period is initial deployment, not months of production scale.
- Semantic drift metrics are proxy composites, not formal semantic equivalence.
- Freeze state in dev `.runtime/` can be cleared by test isolation; freeze mechanics are validated by dedicated tests, not only by live freeze file presence.
- No head-to-head latency comparison against agent frameworks is claimed; CIS optimizes governed correctness over raw throughput.

## 6. Discussion

AAES-OS is best understood as a new OS class: authority over cognition, not just resources. The evaluated implementation shows that this class is implementable and measurable with systems metrics such as drift distributions, containment rates, replay, and test gates.

The contribution is not merely a collection of mechanisms. It is a coherent constitutional model whose architectural properties are observable, reproducible, and independently auditable. Prompts are not law; governance must be represented as runtime artifacts, receipts, registries, and mutation protocols.

The broader research hypothesis is that constitutional runtime governance can support long-lived intelligent systems. AAES-OS v1.0 provides one reference implementation and evidence model, not a universal proof of AI governance.

## 7. Contributions

- Field: Constitutional Intelligence Systems
- Model: proposal-only cognition, governance-first execution, evidence-before-complexity
- System: AAES-OS / Continuity OS v1.0 reference implementation
- Substrate: multi-registry governance, including CAR/COR/GL/COMM-CANON
- Pipeline: deterministic evidence, ledger ticks, freeze anchors
- Mechanism: constitutional amendment algebra for AI systems
- Architecture: CRK-1, cognitive runtime, institutional memory, and intent compiler

## 8. Conclusion

Constitutional governance is necessary for long-lived intelligent systems. AAES-OS demonstrates feasibility with measured drift headroom, full violation logging, deterministic replay, and sealed canon enforcement. The systems contribution is architectural: a normative kernel, canon freeze, lane epochs, amendment governance, and evidence model that make cognitive-runtime governance inspectable and independently auditable.

## References

References follow the working bibliography in `AAES_OS_V1_NEURIPS.tex` and the COR/COMM-CANON standards bundle.
