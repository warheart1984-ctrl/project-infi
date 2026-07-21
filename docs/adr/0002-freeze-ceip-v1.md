# ADR-0002: Freeze CEIP v1.0

- Status: ACCEPTED
- Date: 2026-07-14
- Decision owners: CEIP maintainers
- Constitutional review: Recorded by freeze manifest

## Problem

The integration lifecycle required a stable cross-runtime target.

## Decision

Freeze the 19 CEIP stages, transition semantics, human-approval boundary, receipt/replay/conformance/admission ordering, and terminal audit rule at version 1.0.0.

## Alternatives considered

Keep the lifecycle draft; allow implementation-specific stage order; merge human and constitutional approval.

## Evidence

CEIP reference tests and hash-bound freeze manifest.

## Trade-offs

Compatible 1.x additions must be optional; breaking improvements require 2.0 and migration evidence.

## Impact analysis

Enterprise expansions map into frozen stages rather than rewriting them.

## Supersession

Only a constitutionally approved CEIP major version may supersede this ADR.

## Constitutional principle

No execution without scoped human approval; no institutional-memory promotion without replay, conformance, and admission.

## Standards affected

CEIP lifecycle standard.

## Specifications affected

CEIP v1.0 Reference Runtime.

## Runtime impact

Implementations must preserve CEIP v1 compatibility.

## Conformance impact

CCS fixtures pin the 19-stage ordering and negative gates.
