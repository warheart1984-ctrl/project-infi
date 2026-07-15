# CIS Launch Readiness Specification

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Depends on:** CIS Core v1.0  
**Stewardship:** CIS release maintainers  
**Constitutional sections:** 1-7  
**Informative sections:** 8

---

## 1. Purpose

This specification defines the governed release lifecycle for CIS-aligned releases.

Its purpose is to ensure that every release produces evidence demonstrating conformance to the frozen constitutional baseline before publication.
Promotion to any later release state SHALL be evidence-based rather than subjective.

## 2. Release states

The governed release lifecycle SHALL use the following states:

1. Draft
2. Merge Candidate
3. Approved Constitutional Merge
4. Release Candidate Frozen
5. Release Verified
6. Published
7. Retired

These states SHALL be applied consistently across CIS release surfaces that claim constitutional alignment.

## 3. Release evidence

Each release SHALL produce, at minimum:

- Release Readiness Record
- Constitutional Requirements Matrix
- Companion Specification Traceability
- Build / Test / Smoke Evidence
- Conformance Report
- Replay Reference
- Constitutional Receipts
- Stewardship Approval
- Release Manifest
- Evidence Package

Each artifact in the release bundle SHALL be traceable to at least one CIS Core requirement through the Standards Traceability Matrix.
Each artifact SHALL be retained as objective evidence for the promotion gate that depends on it.

## 4. Evidence-based promotion rules

Release transitions SHALL be governed by evidence.

A release SHALL NOT advance without:

- a defined release boundary
- traceability to CIS Core requirements
- conformance evidence
- replay evidence where applicable
- stewardship approval

Subjective readiness claims SHALL NOT replace the required evidence artifacts.
Where evidence is missing, the lifecycle state SHALL remain partial.

## 5. Freeze rules

To advance to Release Candidate Frozen, a release SHALL have:

- a frozen boundary commit
- a finalized release manifest
- a signed Constitutional Release Receipt
- a reproducible evidence package
- a traceable receipt set linked to the governing release record

## 6. Verification rules

To advance to Release Verified, a release SHALL have:

- successful build verification
- successful test verification
- successful smoke verification
- successful receipt verification
- no unresolved blocking conformance failures
- replay evidence for the frozen boundary
- trust consistency evidence for the release record

Verification SHALL confirm that the release bundle is reproducible and consistent with the frozen baseline.

## 7. Publication rule

No release MAY claim readiness beyond the evidence recorded in its release record.

If evidence is partial, the release SHALL remain in the appropriate partial state.

Publication SHALL occur only after the release has passed through the governed freeze and verification stages.

## 8. Informative note

This specification is intentionally conservative.
It turns release readiness into a governed evidence process rather than a subjective judgment call.
