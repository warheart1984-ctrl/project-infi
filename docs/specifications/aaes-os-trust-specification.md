# AAES-OS Trust Specification

## Purpose

This companion specification defines the constitutional trust model used by AAES-OS implementations.

Trust is not a hidden heuristic and not an application-local convention. It is a governed primitive that sits between evidence, authority, policy, routing, and audit.

## Architectural distinction

- Relationship Ledger records relationships and their evidence.
- Trust Policy defines how trust is evaluated.
- Trust Engine applies the policy to evidence, authority, and provenance.
- Router consumes trust decisions.
- Audit records the evidence, policy, and resulting decision.

That separation keeps trust explainable, replayable, and independently verifiable.

## Core terminology

- Relationship Identity: the stable constitutional identity of a relationship artifact.
- Trust Evidence: the evidence set used to justify a trust assertion or trust evaluation.
- Trust Assertion: a recorded claim about trust, confidence, and authority.
- Trust Policy: the versioned rules and thresholds used to evaluate trust.
- Trust Engine: the deterministic evaluator that applies policy to trust inputs.
- Trust Decision: the evaluated result produced by the trust engine.
- Constitutional Receipt: the signed or signed-equivalent record of a trust decision or evaluation.
- Replay: deterministic reconstruction of a trust artifact lifecycle from the ledger.
- Conformance: verification that an implementation follows the trust specification.

## Trust evidence model

Trust evidence is immutable input to the trust system. Evidence MAY include:

- Evidence identifiers
- Artifact references
- Provenance links
- Authority chain links
- Standards traceability links
- Replay references

Evidence does not prove truth by itself. It preserves the material required for independent verification.

## Trust assertions

A trust assertion records:

- The asserted trust score
- The trust band
- The evidence used
- The authority chain used
- The steward or actor responsible for the assertion
- The provenance context that produced it

Assertions MAY be created from direct observation, delegation, derivation, or governance review.

## Trust evaluation model

The trust engine SHALL evaluate trust using a policy-defined model.

At minimum, the evaluation model MUST support:

- Confidence input
- Authority input
- Evidence input
- Versioned weights
- Trust score output
- Trust band output
- Governance threshold evaluation

Implementations MAY choose the precise weighting function, but equal inputs and equal policy MUST produce equal outputs.

## Trust levels and confidence

Trust levels are constitutional categories.

Minimum standard levels:

- `low`
- `medium`
- `high`

Trust confidence is a normalized value in the inclusive range `0..1`.

Implementations MAY expose additional internal tiers, but they MUST map to the constitutional trust bands above for conformance.

## Policy interfaces

Trust Policy MUST define:

- Policy identity and version
- Governance level
- Minimum trust score
- Required trust band
- Evidence requirements
- Authority-chain requirements
- Replay requirements
- Conformance requirements

Trust policies MUST be versioned, diffable, and replayable.

## Constitutional receipts

Every trust-bearing evaluation, assertion, or decision SHOULD emit a constitutional receipt.

A receipt MUST include:

- Receipt identity
- Relationship identity
- Policy identity and version
- Trust outcome
- Ledger reference
- Replay index or replay sequence position
- Hash of the canonical artifact
- Signature or equivalent integrity proof

## Replay requirements

The trust ledger MUST be replayable.

Replay MUST be able to reconstruct:

- The original evidence set
- The original trust policy
- The trust assertion or decision
- The resulting trust score and band
- The ledger chain
- The receipt chain

Replay SHOULD be deterministic for the same ledger and the same policy version.

## Conformance requirements

An implementation conforms when it can:

- Record trust evidence immutably
- Preserve relationship lineage
- Apply the published trust policy model
- Emit receipts for trust-bearing actions
- Replay the trust lifecycle deterministically
- Produce the same trust outcome from the same evidence and policy

## Relationship to other ledgers

### Relationship Ledger

The Relationship Ledger stores:

- Relationship identity
- Relationship type
- Evidence references
- Stewardship context
- Temporal continuity

### Evidence Ledger

The Evidence Ledger stores:

- Evidence objects
- Provenance
- Integrity data
- Replay references

### Trust Ledger

The Trust Ledger stores:

- Trust assertions
- Trust decisions
- Trust policy versions
- Trust receipts
- Replay links

The Trust Ledger does not replace the Evidence Ledger or Relationship Ledger. It composes with them.

## Companion-spec inheritance rule

All implementations of trust MUST inherit this specification vocabulary and MAY extend it only without redefining the constitutional terms.

## Trust Debugger requirements

Implementations exposing a Trust Debugger SHOULD show:

- Inputs collected
- Algebra computed
- Governance evaluated
- Routing scored
- Final decision
- Receipt and ledger links

## Control-plane relationship

The Control Plane MAY expose trust state, trust timelines, trust policies, trust receipts, and trust debugger surfaces, but it MUST not redefine trust semantics.
