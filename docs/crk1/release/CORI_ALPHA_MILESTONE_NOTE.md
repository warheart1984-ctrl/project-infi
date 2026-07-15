# CORI Alpha Minimal Constitutional Proof Milestone

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Depends on:** CIS Core v1.0, CIS Standards Traceability Matrix, CIS Conformance Suite Specification, CIS Launch Readiness Specification, CORI Alpha Proof Chain  
**Stewardship:** CIS release maintainers  
**Constitutional sections:** 1-4  
**Informative sections:** 5

---

## 1. Purpose

This note records the current constitutional direction for CORI Alpha.

The next objective is a minimal constitutional proof rather than additional architectural expansion.
The smallest runtime of interest is the runtime that can demonstrate, end to end:

- Identity
- Evidence
- Constitutional State Record
- Constitutional Receipt
- Replay
- Conformance

## 2. Constitutional rule

Implementation should increasingly become the primary source of learning.

The specification family SHALL be driven by implementation needs rather than anticipated needs.
If a new specification does not materially improve implementation, conformance, or independent verification, its necessity SHOULD be challenged before it is added.

## 3. Execution backbone

The Standards Traceability Matrix remains the execution backbone for CORI Alpha.

Every implementation slice SHALL answer:

- Which CIS requirement does it implement?
- Which specification owns it?
- What evidence does it produce?
- Which conformance tests validate it?
- What replay path proves it?

## 4. Release expectation

CORI Alpha SHALL be treated as a governed proof milestone.

Its value is measured by the number of governed workflows that can be executed, replayed, inspected, and independently verified, not by the number of documents produced.
Longer term, each completed runtime slice SHOULD emit its own machine-readable Constitutional Receipt and Evidence Package so the full proof can be assembled from verified runtime artifacts.

## 5. Informative note

This note intentionally shifts emphasis from constitutional design expansion to executable constitutional proof.
