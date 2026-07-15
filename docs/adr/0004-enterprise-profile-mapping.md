# ADR-0004: Express enterprise expansion as a CEIP profile

- Status: ACCEPTED
- Date: 2026-07-14
- Decision owners: CEIP maintainers
- Constitutional review: Compatible extension review

## Problem

CTOS, COM, CRM, CTCM, CTL, universal CCR, and continuous improvement added useful detail but risked changing frozen CEIP stages.

## Decision

Map these operations into the existing CEIP Enterprise Intelligence Profile. Continuous improvement emits a new Intent; it does not mutate completed workflows.

## Alternatives considered

Expand CEIP to 24 stages; fork an enterprise lifecycle; allow direct UGR promotion.

## Evidence

CEIP Enterprise Intelligence Profile v1 and successful CEIP freeze-integrity verification.

## Trade-offs

Profiles add mapping work but protect interoperability and frozen hashes.

## Impact analysis

No core contract changes. Products and corpora may select compatible profiles.

## Supersession

None.

## Constitutional principle

Extensions cannot bypass human approval, evidence, replay, conformance, admission, or audit.

## Standards affected

CEIP v1 and constitutional hierarchy v1.

## Specifications affected

CEIP Enterprise Intelligence Profile v1.

## Runtime impact

Adapter and projection work only.

## Conformance impact

Profile-specific CCS fixtures supplement but do not replace core CEIP fixtures.
