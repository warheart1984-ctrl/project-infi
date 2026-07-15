# ADR-0001: Freeze the Constitutional Runtime core

- Status: ACCEPTED
- Date: 2026-07-14
- Decision owners: Runtime architecture
- Constitutional review: Required for amendment

## Problem

Ongoing conceptual expansion prevented a stable implementation and conformance target.

## Decision

Freeze the constitutional execution loop and core modules. New capability enters through adapters/extensions unless evidence demonstrates an engineering necessity for a reviewed core change.

## Alternatives considered

Continue open-ended module expansion; freeze only product-facing APIs; allow runtime-specific forks.

## Evidence

Constitutional Runtime Specification, deployment blueprint, CEIP reference workflow, and existing conformance tests.

## Trade-offs

The freeze constrains short-term design freedom but enables compatibility, independent implementations, replay, certification, and production hardening.

## Impact analysis

All runtime and product work must implement existing contracts, harden qualities, or proceed through ADR and constitutional review.

## Supersession

None.

## Constitutional principle

Authority derives from the constitutional execution loop; capability does not imply authority.

## Standards affected

Constitutional hierarchy v1.

## Specifications affected

Constitutional Runtime Specification v1.0.

## Runtime impact

CRK-1 and AAES-OS remain non-normative implementations.

## Conformance impact

CCS evaluates the frozen contracts independently of runtime implementation.
