---
title: WOLF-1 Architecture Review Response Map
subtitle: Bradley Bates (SkillsMcGee) Critique Traceability
document: WOLF1_CopilotInOrbit_Architecture_v1.0 (post-review revision)
date: June 2026
---

# WOLF-1 Architecture Review Response Map

## Collaborator Credit

**Bradley Bates** (review handle: *SkillsMcGee*) contributed substantive architectural critique during the WOLF-1 / Copilot-in-Orbit v1.0 review cycle. The sections cited below were added or strengthened in direct response to his questions about meta-governance, invariant provenance, epistemic limits of receipts, graded degradation, anomaly discovery, and constitutional evolution.

This document maps each critique to the resolving architecture clause for formal attribution and audit trail purposes.

| Field | Value |
|-------|-------|
| Reviewer | Bradley Bates (SkillsMcGee) |
| Architecture baseline | WOLF-1 Copilot-in-Orbit Architecture v1.0 |
| Response sections | 4.9, 4.10, 6.4, 8.5, 12.4, 14 |
| Traceability purpose | Collaborator credit and constitutional audit |

---

## Side-by-Side Critique Resolution Table

| # | Bradley Bates Critique | Resolving Section | Key Clause / Mechanism | Resolution Status |
|---|------------------------|-------------------|------------------------|-------------------|
| 1 | **"Who watches CRK-1?"** — What if invariant evaluation succeeds incorrectly? Who governs the governor? | **Section 4.10** — Meta-Governance of CRK-1 | Dual evaluators: Primary Evaluator (PE) and Shadow Evaluator (SE). PE/SE mismatch triggers Class A fault, immediate SAFE-MODE, diagnostic receipts, ground notification. Invariant drift detection on evaluation order, timing, dependency graph, pass/fail distribution. Meta-Receipts (invariant set hash, evaluator signatures, divergence metrics). Ground-verifiable deterministic replay; replay mismatch = Class A fault. | **Resolved** — Shadow evaluator exists specifically to catch a systematically-wrong Primary. |
| 2 | **"Where do the 12 invariants come from?"** — Need empirical "why those twelve," not design preference. | **Section 4.9** — Invariant Promotion Criteria | Six-stage pipeline: Observation, Hypothesis (shadow-mode proto-invariant), Stress-Test (adversarial runs, telemetry perturbations, power/thermal edge cases, replay, fault journals), Redundancy and Coupling Analysis, Constitutional Review (unanimous cross-disciplinary panel), Adoption and Ledger Entry (ID, InvariantSet, Mutation Ledger). Demotion/retirement with same review process. Promotion criteria: preventive power, non-interference, stability. | **Resolved** — Invariants earn constitutional status through evidence, not assertion. |
| 3 | **"Receipt does not equal truth"** — Receipts prove lineage, not correctness. | **Section 6.4** — Epistemic Receipts | Separates Lineage Record (hashes, timestamps, identity, context) from Epistemic Metrics (uncertainty, baseline deviation, cross-model consistency, anomaly scores), Interpretation Set, and Correctness Signals (self/tool/historical consistency). Epistemic faults: EPI_DRIFT, EPI_UNCERTAINTY_SPIKE, EPI_CONSISTENCY_FAILURE — logged, contribute to anomaly discovery; do not block runs by default. | **Partially resolved** — Architecture explicitly does not claim to prove correctness; it flags deviation. Bradley's philosophical point (receipt cannot fully certify truth) remains valid and is now acknowledged in design. |
| 4 | **"Safe-mode should not be binary"** — Need graded degradation, not one switch. | **Section 8.5** — Graded Safe-Mode Profiles | Four profiles: S0 Full Operations, S1 Cognitive Degradation (LLM off, planning/simulation on), S2 Autonomy Degradation (planning off, limited simulation), S3 Governance-Only (CRK-1 + CAS, health checks, safe-pointing). Transitions: S0 to S1 to S2 to S3; recovery ground-authorized in reverse. | **Resolved** — Matches Bradley's sketched tiered model. |
| 5 | **"Where is anomaly discovery?"** — Unknown-unknowns need a framework beyond invariant fault codes. | **Section 12.4** — Anomaly Discovery Framework | Multi-channel detection: telemetry, power/thermal gradients, LLM output distributions, invariant timing, epistemic metrics, drift signatures. Baseline statistical models. Anomaly classes A0-A3; A2/A3 auto-escalate to ground. Dedicated anomaly receipts with type, score, subsystems, signals, recommended actions. | **Resolved** |
| 6 | **"No architecture for architectural evolution"** — How does the constitution change safely? | **Section 14** — Constitutional Evolution Protocol | Mutation types M0-M4 (policy update through CRK-1 evaluator update). Preconditions: ground-signed auth, invariant-set hash match, drift-free state, SAFE-MODE S3, evaluator quorum. Mutation Ledger with before/after sets, evidence, rollback path. Automatic rollback on increased fault/anomaly rate, evaluator divergence, constitutional drift. Safety: no mutation during burns or cognitive runs; all replayable on ground. | **Resolved** |
| 7 | **"Governance is non-optional, cognition is optional — rewrite the core principle"** — Autonomous execution optional; constitutional enforcement mandatory. | **Core principles** (wording not confirmed in uploaded v1.0 PDF) | Requested rewrite: *"Autonomous execution is optional; constitutional enforcement is mandatory."* | **Unconfirmed** — Not present in the v1.0 PDF upload reviewed; may appear in a later draft. Recommend explicit insertion in Section 1 (Design Principles) or Executive Summary. |

---

## Section Reference Summary

### Section 4.9 — Invariant Promotion Criteria
Constitutional invariants are not design preferences. Promotion pipeline: Observation, Hypothesis (shadow-mode), Stress-Test, Redundancy Analysis, Constitutional Review, Ledger Entry. Demotion follows the same process.

### Section 4.10 — Meta-Governance of CRK-1
Redundant evaluators (PE/SE), drift detection, Meta-Receipts, ground-verifiable determinism.

### Section 6.4 — Epistemic Receipts
Lineage vs epistemic metrics vs correctness signals. Epistemic faults feed anomaly discovery without default run blocking.

### Section 8.5 — Graded Safe-Mode Profiles
S0 through S3 spectrum with defined triggers and ground-authorized recovery.

### Section 12.4 — Anomaly Discovery Framework
Multi-channel detection, baseline models, severity classes A0-A3, anomaly receipts.

### Section 14 — Constitutional Evolution Protocol
Mutation types M0-M4, strict preconditions, ledger entries, automatic rollback.

---

## Attribution Statement (for publications and collaborator records)

> Architectural sections 4.9, 4.10, 6.4, 8.5, 12.4, and 14 of the WOLF-1 Copilot-in-Orbit Architecture were developed or materially strengthened in response to review feedback from **Bradley Bates** (SkillsMcGee), including questions on CRK-1 meta-governance, invariant provenance, epistemic receipt limits, graded safe-mode, anomaly discovery, and constitutional evolution.

---

*Generated for Project-Infinity1 / WOLF-1 governance traceability. Source architecture: WOLF1_CopilotInOrbit_Architecture_v1.0.*
