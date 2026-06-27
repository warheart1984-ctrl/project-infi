# AAES-OS v1.0: A Constitutional Runtime Architecture for Governed Intelligence

**Authors:** Jon Halstead, Dar-z Morris, et al. - **2026**

## Abstract

We introduce AAES-OS v1.0, a constitutional runtime architecture for governed AI systems. AAES-OS unifies three mathematical layers - Wave Math (micro-level judgment dynamics), Continuity Failure Theory (macro-level consequence propagation), and Reconstruction Sufficiency (meta-level reconstructability) - into a deterministic reference implementation for enforcing constitutional constraints on model-mediated behavior. The system includes CAS 1.0, a formal object model; CRK-1, a constitutional runtime kernel; CTS, a conformance test suite; CDP-1, a reproducible continuity benchmark; and CEP, an experimental platform enabling independent replication.

Version 1.0 separates architectural claims, implementation results, and research hypotheses so evidence can be evaluated without overclaiming. Architectural claims describe properties guaranteed by the specification, implementation results describe measured outcomes demonstrated by the AAES-OS v1.0 reference implementation, and research hypotheses identify broader claims that require additional validation across independent implementations or production deployments.

## 1. Introduction

Modern AI systems exhibit drift, nondeterminism, and opaque internal reasoning. These properties undermine safety, reproducibility, and scientific evaluation. Existing governance approaches rely on post-hoc analysis or heuristic constraints that cannot guarantee constitutional compliance.

AAES-OS addresses this gap by introducing a constitutional architecture: a system where governance is enforced at runtime through deterministic rules, invariant validation, and content-addressed receipts. The paper's primary contribution is architectural: it defines a constitutional operating model, a reference implementation, and an evidence model that others can evaluate, reproduce, and extend. It does not claim to solve AI governance universally.

**Contributions:**

1. Normative contribution: constitutional specification, governance model, and architectural contracts.
2. Engineering contribution: CRK-1 runtime, ledger, receipts, cockpit, CTS, CDP-1, CEP, and tooling.
3. Research contribution: hypotheses about continuity, reconstruction, and semantic boundaries evaluated through evidence and replication rather than assumed universal.

### 1.1 Claim Taxonomy

AAES-OS v1.0 uses the following evidence taxonomy throughout the paper:

| Claim class | Meaning | Evidence treatment |
|-------------|---------|--------------------|
| Architectural claim | Property guaranteed by the specification, such as layer separation, provenance model, constitutional contracts, or governance model | Tie to a normative clause, contract, or conformance requirement |
| Implementation result | Measured outcome demonstrated by the AAES-OS v1.0 reference implementation, such as test results, replay determinism, freeze mechanics, drift measurements, or ledger integrity | Tie to executable tests, receipts, replay artifacts, benchmark outputs, or release gates |
| Research hypothesis | Broader claim about governed intelligence that requires validation across multiple implementations or production deployments | Label explicitly as hypothesis and keep outside conformance language |

## 2. Related Work

Constitutional AI, formal verification, deterministic runtimes, reproducibility in ML, AI governance frameworks, and drift measurement. AAES-OS differs by providing a complete, executable, constitutional runtime rather than a policy layer or training-time constraint.

## 3. Mathematical Foundations

### 3.1 Wave Math

Defines micro-level judgment dynamics and local decision stability.

### 3.2 Continuity Failure Theory

Models macro-level consequence propagation and drift under perturbation.

### 3.3 Reconstruction Sufficiency

Ensures that all system states are reconstructable from receipts and evidence.

## 4. Constitutional Architecture

### 4.1 Invariants

Frozen set (K-infinity, K0-K15, KOmega) governing all transitions.

### 4.2 Object Model

CAS 1.0: Identity, Decision, Outcome, Evidence, Interpretation, Receipt, DriftObservation, KernelChallenge.

### 4.3 Allowed Transitions

Deterministic and constitutionally validated.

### 4.4 Deterministic Behavior Rules

No hidden state, no nondeterministic branches, no side-effects outside receipts.

## 5. CRK-1 Runtime

Constitutional boot, proof gate, capability gate, receipt generation, drift detection, deterministic execution engine.

## 6. CAS 1.0

Formal object model, reference implementation, CTS.

## 7. CDP-1 Benchmark

Dataset, metrics, thresholds, reproduction scripts, continuity graphs.

## 8. CEP Platform

Experiment execution, logging, deterministic replay, trace capture.

## 9. Evaluation Frame

We frame evaluation around three systems questions:

1. Can the architecture be implemented?
   Demonstrated through the reference implementation, deterministic replay, freeze mechanics, conformance tests, and release gates.
2. Can the architecture be independently verified?
   Demonstrated through provenance, content-addressed receipts, COR/CAR/CAV-style registries, deterministic replay, and the conformance ecosystem.
3. Can the architecture evolve without losing constitutional integrity?
   Demonstrated through amendment protocols, governance receipts, canonical freeze, and founder-independent stewardship.

This framing separates architectural feasibility, implementation evidence, and long-term governance claims. It also prevents measured reference-implementation results from being mistaken for universal guarantees about all future intelligent systems.

## 10. Independent Replication

External teams can run CAS, CRK-1, CTS, and CDP-1, publish results, and challenge conclusions.

Replayability means the reference implementation reproduces the same result from the same recorded evidence. Independent verifiability means a separate implementation reaches the same result using only the specification and recorded artifacts. AAES-OS treats these as distinct evidentiary thresholds.

## 11. Discussion

The primary contribution of AAES-OS v1.0 is architectural. The paper presents a constitutional runtime model with inspectable governance, reproducible evidence, and founder-independent stewardship. It does not claim that constitutional runtime governance alone solves model alignment, semantic truth, or all production governance problems. Instead, it shows that governance can be made observable, replayable, and auditable at the runtime boundary.

Specifications define intended behavior. Implementations demonstrate one realization. Evidence establishes what has been achieved. Replication determines confidence.

## 12. Conclusion

AAES-OS v1.0 presents a constitutional runtime architecture for governed AI systems. Its contribution is not a priority claim about being first, nor a universal claim about solving AI governance. It is a coherent constitutional model whose architectural properties are specified, whose implementation results are measured, and whose broader research hypotheses remain open to independent validation. Its scientific posture is evidence-first: guarantees are specified, implementations are tested, empirical claims are backed by artifacts, and confidence grows through independent replication.
