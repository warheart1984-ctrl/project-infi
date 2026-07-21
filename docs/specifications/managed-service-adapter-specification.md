# Managed Service Adapter Specification

Version: 1.0.0
Status: Draft

## Purpose

This specification defines the canonical constitutional contract for every managed service adapter exposed through the Constitutional Operations Console and any future operator surface that speaks the same control-plane language.

An adapter is a governed bridge between the console and a managed service. It is not a dashboard widget, and it is not a service-specific one-off. It MUST expose the same operator semantics, the same evidence semantics, and the same readiness semantics as every other adapter.

## Canonical adapter set

The initial canonical set is:

- Dropbox
- ULX
- CORI Alpha
- Sovereign X Runtime
- Nova
- AI Factory
- Research OS

Additional services MAY be added later, but they MUST conform to this specification before they are treated as production adapters.

## Constitutional principles

- Observe before execute
- Verify before promote
- Evidence before claim
- Receipt before trust
- Replay before launch
- Conformance before production
- One contract, many adapters

## Adapter contract

Every managed service adapter MUST define:

- Runtime responsibility
- Required operator actions
- Health model
- Conformance model
- Replay model
- Evidence model
- Constitutional Receipt schema
- Evidence Package schema
- Operator Timeline schema
- Diagnostics schema
- Acceptance criteria
- Required verification tests

Every adapter MUST expose machine-readable status and action results. UI text alone is insufficient.

## Runtime responsibility

The runtime responsibility clause describes what the adapter is allowed to observe and control.

An adapter SHOULD declare:

- The service or workspace it governs
- The runtime boundary it reads from
- The control boundary it writes to
- Any external systems it depends on
- Any fallback path it may use when the primary runtime is unavailable

The runtime responsibility MUST be explicit enough that a reviewer can tell whether the adapter is operating over a live service, a local workspace snapshot, or a read-only evidence store.

## Required operator actions

Every adapter MUST support the following core operator actions where the runtime allows it:

- Start
- Stop
- Restart
- Verify
- Replay
- Generate Evidence
- Export Diagnostics

An adapter MAY support additional service-specific actions, but the core action names MUST remain stable.

## Health model

Every adapter MUST expose a health state from the following canonical set:

- `healthy`
- `degraded`
- `warning`
- `offline`
- `recovery-required`

Health MUST summarize runtime viability, not just service presence.

## Conformance model

Every adapter MUST expose a conformance snapshot with at least:

- Build status
- Runtime status
- Service status
- Conformance status
- Replay readiness
- Launch readiness

Conformance status MUST be one of:

- `passing`
- `warning`
- `degraded`
- `blocked`
- `unknown`

## Replay model

Every adapter MUST provide replay metadata sufficient to reconstruct the operator decision path.

Replay metadata SHOULD include:

- Triggering action
- Observed status
- Conformance state
- Generated artifacts
- Launch readiness
- Recovery guidance when replay fails

Replay is not only for historical inspection. It is a launch gate and a change gate.

## Evidence model

Every adapter MUST emit machine-readable evidence artifacts for governed actions.

The evidence model MUST support:

- Constitutional Receipt
- Evidence Package
- Audit Record
- Replay Metadata
- Diagnostics

Evidence MUST be written in deterministic, parseable formats. JSON is the canonical baseline.

## Constitutional Receipt schema

A Constitutional Receipt MUST at minimum include:

- Receipt identifier or derivation path
- Adapter identifier
- Action name
- Timestamp
- Snapshot of service status
- Snapshot of conformance state
- Result status
- Artifact references

The receipt is the canonical acknowledgement that an operator action was observed and recorded.

## Evidence Package schema

An Evidence Package MUST at minimum include:

- Adapter identifier
- Action name
- Runtime state
- Health state
- Conformance state
- Timeline references
- Supporting evidence references

The evidence package is the reviewable bundle used to justify the operator action.

## Operator Timeline schema

An Operator Timeline entry MUST at minimum include:

- Timestamp
- Event kind
- Title
- Detail
- Severity
- Action name
- Artifact references

The timeline MUST be append-only. It MUST preserve commands, state transitions, evidence generation, errors, recovery actions, and receipts.

## Diagnostics schema

Diagnostics MUST include enough data to reproduce the current operator context without requiring the UI.

At minimum, diagnostics SHOULD include:

- Adapter identity
- Runtime identity
- Backend mode
- Selected fallback path
- Health snapshot
- Conformance snapshot
- Timeline excerpt
- Recent artifact paths

## Acceptance criteria

No adapter is considered production-ready until it demonstrates all of the following:

1. Build Verification
1. Test Verification
1. Runtime Verification
1. Conformance Verification
1. Replay Verification
1. Evidence Generation
1. Constitutional Receipt Generation
1. Launch Readiness

An adapter MAY be usable before it is production-ready, but it MUST be labeled accordingly.

## Required verification tests

Every adapter MUST have tests that prove:

- The adapter appears in the registry
- The adapter exposes the required action set
- The adapter returns a status snapshot
- The adapter emits a constitutional receipt for governed actions
- The adapter emits an evidence package
- The adapter emits an operator timeline entry
- The adapter emits diagnostics
- The adapter reports launch readiness consistently
- The adapter does not claim production readiness without passing conformance

The test suite SHOULD include both positive and negative cases.

## Production gating

Before an adapter may be promoted to production, the following gates MUST pass:

- Build Verification
- Test Verification
- Runtime Verification
- Conformance Verification
- Replay Verification
- Evidence Generation
- Constitutional Receipt Generation
- Launch Readiness

Promotion MUST be denied if any gate fails.

## Canonical operator surface

The Constitutional Operations Console is the primary operator surface for managed services in this repository.

Its job is to:

- Observe managed services
- Verify managed services
- Execute governed actions
- Generate receipts
- Update evidence
- Produce conformance snapshots
- Support replay

The console MUST not invent adapter-specific semantics that are not backed by this specification.

## Adapter ordering

The current preferred ordering for the console registry is:

1. Dropbox
1. ULX
1. CORI Alpha
1. Sovereign X Runtime
1. Nova
1. AI Factory
1. Research OS

AI Factory and Research OS MUST join the same contract when they are implemented.

## Change rule

Any future change to this specification MUST preserve the adapter contract, the artifact contract, and the production gate semantics.
