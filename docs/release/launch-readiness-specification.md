# Launch Readiness Specification

This companion specification defines the governed release lifecycle for Project Infi.
It establishes the release states, the evidence required for each transition, and the
meaning of the formal promotion state `Approved Constitutional Merge`.

## Purpose

- Make release readiness evidence-first and replayable.
- Ensure every release produces the same core artifact bundle.
- Separate merge approval from release publication.
- Preserve a constitutional record of the release boundary.

## Standard Release Artifact Bundle

Every release should produce the following core artifacts:

1. Release Readiness Record
2. Constitutional Requirements Matrix
3. Companion Specification Traceability
4. Build / Test / Smoke Evidence
5. Conformance Report
6. Replay Reference
7. Constitutional Receipts
8. Stewardship Approval
9. Release Manifest
10. Evidence Package

## Release Lifecycle

| State | Meaning | Required evidence |
| --- | --- | --- |
| `Draft` | Release work is being assembled | Initial scope, candidate commit, and artifact plan |
| `Merge Candidate` | The slice is eligible for constitutional review | Build/test/smoke evidence and traceability draft |
| `Approved Constitutional Merge` | The merge has been constitutionally approved | Release Readiness Record, conformance evidence, stewardship approval |
| `Release Candidate Frozen` | The release boundary is frozen for packaging and verification | Frozen commit, manifest, checksum baseline, receipts |
| `Release Verified` | The bundle has been packaged, signed, and verified | Release manifest, evidence package, checksum and signature verification |
| `Published` | The release is available to consumers | Verified bundle, publication receipt, final manifest |
| `Retired` | The release is no longer active | Retirement record and archival evidence |

## Formal Promotion State: Approved Constitutional Merge

`Approved Constitutional Merge` is the formal state that records a constitutional approval of the merge boundary.
It means:

- The release slice has been reviewed against the governing evidence standard.
- Stewardship has approved the merge boundary.
- The merge may advance into freeze and packaging work.

It does not mean:

- The release is published.
- The bundle is signed.
- The release is operationally launched.
- All downstream environments are ready.

That distinction keeps merge approval separate from release publication and avoids
conflating code approval with operational launch readiness.

## Promotion Criteria

To enter `Approved Constitutional Merge`, a release must have:

- A release candidate version.
- A completed Release Readiness Record.
- Explicit build, test, and smoke evidence.
- A Conformance Report with no blocking gaps.
- A Replay Reference where replay is applicable.
- Stewardship Approval.
- A Release Manifest or a clear plan for generating one at freeze time.

## Freeze Criteria

To advance from `Approved Constitutional Merge` to `Release Candidate Frozen`, a release must have:

- A frozen boundary commit.
- A finalized Release Manifest.
- A signed Constitutional Release Receipt.
- A reproducible Evidence Package.

## Verification Criteria

To advance from `Release Candidate Frozen` to `Release Verified`, a release must have:

- Successful build verification.
- Successful test verification.
- Successful smoke verification.
- Successful receipt and signature verification.
- No unresolved blocking conformance failures.

## Release Governance Rule

No release may claim readiness beyond the evidence recorded in its release record.
If evidence is partial, the lifecycle state must remain partial.

## Companion Specifications

- [Constitutional Release Receipt](./constitutional-release-receipt.md)
- [ULX Merge Readiness Record](./ulx-merge-readiness-record.md)
- [Docs Hub](../README.md)

