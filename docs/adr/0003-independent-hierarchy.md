# ADR-0003: Preserve constitutional layer independence

- Status: ACCEPTED
- Date: 2026-07-14
- Decision owners: Constitutional governance
- Constitutional review: Required for amendment

## Problem

A reference implementation could accidentally become the de facto normative authority.

## Decision

Preserve Constitution → Standards → Specifications → CCS → Reference Runtime → Certified Implementations, with CCS independent of candidate code.

## Alternatives considered

Golden-output testing against CRK-1; runtime-owned certification; AAES-OS-specific standards.

## Evidence

Constitutional Hierarchy Standard and CCS Independence Requirements.

## Trade-offs

Independent fixtures and a second implementation cost more but prevent circular validation.

## Impact analysis

Certification cannot be self-issued by CRK-1. Candidate diversity is explicitly supported.

## Supersession

None.

## Constitutional principle

Conformance derives from the Constitution and specifications, not implementation identity.

## Standards affected

Constitutional hierarchy v1.

## Specifications affected

CCS Independence Requirements.

## Runtime impact

None; separation constrains test and certification architecture.

## Conformance impact

CCS cannot import reference-runtime implementation code.
