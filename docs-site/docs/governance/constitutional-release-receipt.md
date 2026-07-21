# Constitutional Release Receipt

The Constitutional Release Receipt is the standardized evidence package every release should emit.

## Purpose

Make build, test, lint, replay, and audit evidence comparable across releases.

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

## Release Outputs

- Root receipt: `release/constitutional-release-receipt.json`
- Bundled receipt: `release/bundle/constitutional-release-receipt.json`

## How It Is Produced

The release pipeline writes the receipt during build, packages it into the release bundle, attaches the signature during signing, and stamps the verification date during verification.

## Truth Boundary

The receipt proves the selected release artifacts were built, packaged, signed, and verified. It does not prove production readiness for unfinished surfaces.

## Constitutional Evidence Graph

The receipt is the root node of the Constitutional Evidence Graph. README, docs, scorecards, docs-site, Nova Studio, and ops-console views all resolve public claims through this root receipt.

## Evidence Rule

No release may claim more constitutional maturity than the evidence recorded in its receipt.

## Challenge Rule

Each release receipt should state both the evidence that supports the release claim and the evidence that could invalidate it.
