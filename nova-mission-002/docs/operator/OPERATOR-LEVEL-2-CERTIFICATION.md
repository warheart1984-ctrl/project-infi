# Nova Operator Certification — Level 2 (Advanced Multi-Agent Ops)

**Version:** 1.0  
**Prerequisite:** Level 1 Certification (observer sign-off per `observer/CHECKLIST.md`)  
**Audience:** Operators responsible for multi-agent clusters, distributed CRK-1 kernels, and high-integrity governance environments.

---

## 1. Certification Objectives

A Level 2 Operator must demonstrate proficiency in:

- Managing multiple Nova agents concurrently
- Monitoring distributed CRK-1 kernel health
- Detecting and resolving agent drift
- Coordinating cluster-wide goals
- Performing cross-agent continuity audits
- Handling multi-agent incidents
- Executing cluster-level rollbacks
- Maintaining ledger integrity across nodes

---

## 2. Exam Structure

| Section | Content | Items | Weight |
|---------|---------|-------|--------|
| **A** | Multi-Agent Theory | 10 MCQs | 25% |
| **B** | Applied Governance | 10 short answers | 25% |
| **C** | Cluster Operations | 5 practical tasks | 30% |
| **D** | Incident Response | 2 scenario drills | 20% |

**Passing score:** 90%  
**Time limit:** 90 minutes (recommended)  
**Environment:** Flight Deck cockpit or CLI with multi-agent bridge enabled

---

## 3. Section A — Multi-Agent Theory (10 MCQs)

*Select the best answer for each question.*

**1.** Agent drift occurs when:

- A. Two agents produce different receipts or plans for the same goal under equivalent constraints
- B. Kernel heartbeat stops on a single node
- C. Invariants are disabled cluster-wide
- D. Continuity snapshots fail to serialize

**2.** Cross-agent continuity requires:

- A. Identical codebases on every host
- B. Equivalent actions produce reconcilable continuity hashes and ledger chains when constraints match
- C. Shared UI state in the cockpit
- D. A single shared operator session

**3.** A cluster-level violation is:

- A. Any violation on one agent in isolation
- B. A violation pattern replicated across multiple agents or indicating systemic failure
- C. A UI rendering bug in the Flight Deck
- D. A unit test failure in the workspace

**4.** The canonical ledger in a multi-agent cluster is:

- A. The union of all agent receipts without ordering
- B. The cryptographically chained receipt log that all agents must reconcile against
- C. The cockpit Zustand store
- D. The Git commit history

**5.** When two agents disagree on a plan, the operator should first:

- A. Force both agents to execute the longer plan
- B. Compare plans, receipts, and invariants checked, then designate or derive a canonical path
- C. Disable all invariants temporarily
- D. Delete continuity snapshots from the divergent agent

**6.** Agent isolation is appropriate when:

- A. The agent completes tasks faster than peers
- B. Ledger divergence, uncontrolled violation storms, or unrecoverable continuity mismatch are detected
- C. The operator prefers a different UI theme
- D. Heartbeat interval is below 2 seconds

**7.** Multi-agent kernel heartbeat is used to:

- A. Replace governance receipts
- B. Provide low-latency health signals per node (invariant engine, ledger, continuity)
- C. Train the LLM
- D. Bypass the invariant engine during peak load

**8.** A continuity matrix (agents × snapshots) helps operators:

- A. Edit CSS in the cockpit
- B. Detect cross-agent snapshot mismatches and missing replay points
- C. Increase receipt throughput
- D. Disable warning-level invariants

**9.** Cluster-wide rollback typically involves:

- A. Replaying from a last known-good shared snapshot and reconciling ledgers before resuming agents
- B. Restarting the browser only
- C. Clearing all invariants
- D. Merging diffs without receipts

**10.** Founder-independent reproduction in a cluster context means:

- A. Only the founder may verify receipts
- B. An external observer can verify behavior using bundle + protocol alone, including multi-agent scenarios
- C. Agents run without operators
- D. Continuity is optional

**Answer key (for proctors):** 1-A, 2-B, 3-B, 4-B, 5-B, 6-B, 7-B, 8-B, 9-A, 10-B

---

## 4. Section B — Applied Governance (10 Short Answers)

*Answer in 3–6 sentences each.*

**1.** Explain how to detect multi-agent divergence using receipts.

**2.** Describe the process for performing a cluster-wide rollback.

**3.** What is the role of the operator when two agents disagree on a plan?

**4.** How does CRK-1 ensure ledger consistency across nodes?

**5.** When should an operator isolate an agent?

**6.** What signals in the Flight Deck indicate agent drift vs. a single violation?

**7.** How do you audit cross-agent continuity without mutating live state?

**8.** What is the difference between a warning-level and error-level invariant in a cluster?

**9.** Why must blocked actions still emit receipts in multi-agent environments?

**10.** What artifacts should be exported after a Level 2 incident?

**Grading rubric:** Answers must reference receipts, continuity, invariants, ledger chain, and operator authority. Vague answers score partial credit only.

---

## 5. Section C — Practical Tasks

### Task 1 — Plan comparison

Launch two agents with the same goal (e.g. *"Refactor data access layer for clarity and testability"*). Compare plans in Flight Deck **plan-diff** mode. Document step count, ordering differences, and invariant coverage.

**Pass:** Written comparison with at least three concrete differences or an explicit "equivalent" justification with receipt IDs.

### Task 2 — Controlled divergence

Trigger a controlled divergence (e.g. different invariant sets or goals). Resolve using continuity replay from a shared snapshot. Record before/after ledger hashes.

**Pass:** Divergence identified, one agent replayed or rolled back, ledger reconciled.

### Task 3 — Cluster ledger audit

Export receipts from all agents. Validate `ledgerHash` chaining per agent and cross-check continuity hashes for equivalent actions.

**Pass:** Audit log showing chain validation PASS or documented exceptions with remediation.

### Task 4 — Multi-agent refactor

Execute a governed refactor on one agent while a peer observes. Verify cross-agent receipts appear in Flight Deck **ledger-compare** mode.

**Pass:** Receipt IDs cited; invariants checked listed; no silent actions.

### Task 5 — Kernel degradation recovery

Simulate kernel degradation on one node (e.g. stop heartbeat or inject ledger warn). Restore cluster health without data loss.

**Pass:** Degradation detected via heartbeat; node recovered; cluster status nominal.

---

## 6. Section D — Scenario Drills

### Scenario 1 — The Forked Ledger

**Situation:** Two agents produce conflicting ledger entries for the same logical action (mismatched `ledgerHash` or continuity hash).

**Operator must:**

1. Identify divergence point (receipt ID + timestamp)
2. Freeze affected agents
3. Reconcile receipts against canonical chain
4. Restore canonical ledger
5. Document root cause

**Pass:** Both agents frozen during reconciliation; canonical ledger restored; incident note filed.

### Scenario 2 — Distributed Violation Storm

**Situation:** Three agents simultaneously violate the same invariant (e.g. `no-dangerous-shell`).

**Operator must:**

1. Identify root cause (shared plan step, config, or prompt)
2. Halt cluster execution
3. Replay continuity from pre-storm snapshot
4. Patch invariant, plan, or goal as appropriate
5. Restart cluster with verification checklist

**Pass:** Cluster halted within one heartbeat cycle; replay successful; no repeat violation on re-run.

---

## 7. Certification Statement

> "I certify that I can safely operate Nova in multi-agent, distributed, and high-integrity environments, maintain CRK-1 kernel health, and resolve cluster-level incidents."

**Operator name:** ____________________  
**Signature:** ____________________  
**Date:** ____________________  
**Proctor / verifier:** ____________________

---

## Related documents

- [Flight Deck Mockup](./NOVA-FLIGHT-DECK-MOCKUP.md)
- [CRK-1 Kernel Integrity Test Suite](../integrity/CRK-1-KERNEL-INTEGRITY-TEST-SUITE.md)
- [Observer Reproduction Protocol](../../observer/REPRO_PROTOCOL.md)
- Level 1 prerequisite: operator sign-off per `observer/CHECKLIST.md`
