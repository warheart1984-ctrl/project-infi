# Constitutional Release Receipt

This document defines the standardized Constitutional Release Receipt that every repository release should emit.
It is one required artifact inside the reusable Constitutional Release Record (CRR) bundle.

## Purpose

Give each release the same evidence package so maturity claims can be compared objectively.
The receipt is not the whole release record; it is one signed evidence artifact within that record.

## Required Fields

- Proof Surface Level (P0-P5)
- Proof & Challenge Surface
- Build Evidence
- Test Evidence
- Lint Status
- Replay Status
- Audit Status
- Verification Date
- Known Limitations
- Truth Boundary
- Failure Contracts
- Observability
- Constitutional Maturity

## Generated Artifacts

- Root receipt: `release/constitutional-release-receipt.json`
- Bundled receipt: `release/bundle/constitutional-release-receipt.json`

## How It Is Produced

The release pipeline writes the receipt during build, copies it into the release bundle during packaging, attaches the release signature during signing, and stamps the verification date during release verification.

## Truth Boundary

The receipt proves the release bundle was built, packaged, signed, and verified against the selected artifacts. It does not claim production readiness for unfinished surfaces.

## Evidence Rule

No release may claim more constitutional maturity than the evidence recorded in its receipt.

## Challenge Rule

Each release receipt should state both the evidence that supports the release claim and the evidence that could invalidate it.
