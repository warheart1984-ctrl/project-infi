# Evidence Claim Discipline

AAES-OS v1.0 uses evidence-first language. Project documents, release gates, cockpit indicators, and paper claims must distinguish what the architecture is designed to enable from what the specification requires, what the implementation has demonstrated, and what remains a research hypothesis.

## Claim Classes

| Class | Meaning | Required treatment |
|-------|---------|--------------------|
| Architectural objective | What the system is designed to enable | State as intent or design scope, not proof |
| Specified guarantee | Behavior a conforming Version 1.0 implementation is required to provide | Tie to a normative spec clause, CTS case, or release gate |
| Empirical claim | Behavior actually demonstrated by CTS, replay validation, reproducibility tests, or implementation evidence | Cite source artifacts, runs, receipts, and test results |
| Research hypothesis | Architectural pattern that appears promising but is still being evaluated across domains | Label as hypothesis and keep out of conformance language |

This separation is normative for AAES-OS v1.0 documentation. A document may discuss all four classes, but it must not collapse them into a single undifferentiated "claim."

## Replayability and Independent Verifiability

Replayability means the reference implementation reproduces the same result from the same recorded evidence.

Independent verifiability means a separate implementation reaches the same result using only the specification and recorded artifacts.

Replayability is necessary evidence for determinism in the reference implementation. It is not, by itself, independent verification. Independent verification requires an implementation boundary: the verifier must not rely on hidden behavior, private code paths, or undocumented assumptions from the reference implementation.

## Cockpit Indicator Reproducibility

Each cockpit indicator shown in the Evidence Inspector must have a reproducibility contract with three parts:

1. Normative definition: the specification-level meaning of the indicator.
2. Reference implementation: the code path that computes the displayed value.
3. Independent verifier: a separate checker capable of recomputing or validating the value from recorded artifacts.

The cockpit remains observational. It may display status, provenance, and verification state, but it must not silently convert an observation into a guarantee.

## Evidence Inspector Provenance

Every displayed indicator must carry provenance metadata:

| Field | Meaning |
|-------|---------|
| Source artifacts | Receipts, traces, ledger entries, tests, or benchmark outputs used to compute the value |
| Transformation specification | Normative rule or documented algorithm that maps artifacts to the displayed value |
| Implementation version | Reference implementation version, commit, package version, or build identifier |
| Verification status | `Replay Verified` or `Independently Verified` when established; otherwise explicitly pending or unverified |

## Contribution Taxonomy

AAES-OS v1.0 separates its contribution language into three categories:

| Contribution | Scope |
|--------------|-------|
| Normative contribution | Constitutional specification, governance model, and architectural contracts |
| Engineering contribution | Runtime, ledger, receipts, cockpit, CTS, and tooling |
| Research contribution | Hypotheses evaluated through evidence and replication rather than assumed universal |

## Operating Rule

Specifications define intended behavior.

Implementations demonstrate one realization.

Evidence establishes what has been achieved.

Replication determines confidence.
