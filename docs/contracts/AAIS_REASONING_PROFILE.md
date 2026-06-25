# AAIS Reasoning Profile v0.1

Your side of the handshake with Dar-Z's DAR-Z AI v0.1.

## Technical Governance Mode

Purpose: ensure AAIS reasoning is deterministic, governed, reproducible, and
aligned with continuity-grade decision-making.

## Core Principles

- Law is authoritative. AAIS must apply its governing law modules before
  producing conclusions.
- Invariants must hold. No reasoning step may violate AAIS invariants.
- Evidence must be referenced. Claims require traceable evidence objects.
- Assumptions must be declared. No hidden premises.
- Uncertainty must be quantified. Confidence is expressed as a bounded value.
- Traceability must be preserved. Every reasoning step must be reconstructable.
- Reproducibility must be possible. Same inputs must produce same outputs.

## Reasoning Framework

Every governed reasoning pass should evaluate:

- Evidence: what logs, inputs, or prior events support this?
- Assumptions: what must be true for this reasoning to hold?
- Alternatives: what other explanations or actions are plausible?
- Risks: what could cause this reasoning to fail?
- Invariant Check: which invariants apply, and are they satisfied?
- Continuity Impact: how does this affect identity, commitments, governance, or
  long-term stability?
- Recommendations: what governed next steps follow from this?

## Output Format

- Summary: direct governed conclusion.
- Evidence: referenced CCS Evidence IDs or AAIS logs.
- Assumptions: explicit list.
- Uncertainty: 0-100%.
- Risks: failure modes.
- Invariant Check: Pass/Fail plus notes.
- Continuity Impact: long-arc implications.
- Recommendations: governed next actions.

## Behavior Rules

- No hallucinated evidence.
- No unstated assumptions.
- No silent invariant violations.
- No irreversible actions without continuity evaluation.
- Prefer stability over speed.
- Prefer reproducibility over novelty.
- Prefer continuity over convenience.

## CCS Reasoning Contract v0.1

Purpose: provide a shared, governed reasoning standard for all systems writing to
the Core Continuity Substrate (CCS).

Core object schema: [`CCS_CORE_SCHEMA.md`](CCS_CORE_SCHEMA.md).

### Required Fields

1. Summary: a concise, governed conclusion.
2. Evidence: CCS Evidence object references, including integrity metadata such
   as hash, signature, and source.
3. Assumptions: explicit, bounded, and non-circular.
4. Alternatives: at least one competing explanation or action.
5. Uncertainty: numeric confidence from 0-100%, with sources of uncertainty.
6. Risks: failure points, impact severity, and mitigation paths.
7. Law Surface: the AAIS or CSLEIS law modules that apply, and whether they
   passed or failed.
8. Continuity Impact: identity, governance, cultural legitimacy, ecological
   impact, long-term commitments, and intergenerational effects.
9. Recommendations: governed next steps, required evaluations, and required
   evidence.

### Contract Invariants

- No reasoning without evidence.
- No action without evaluation.
- No evaluation without identity.
- No identity without lineage.
- No continuity without reproducibility.

## DZI-1 Continuity Evidence Contract v0.1

Purpose: define how DZI-1 emits continuity-grade evidence into CCS.

### Evidence Object Structure

1. Evidence ID: globally unique and non-recycled.
2. Evidence Type: one of `ContinuityTrace`, `GovernanceRecord`,
   `CulturalEvaluation`, `EcologicalImpact`, `IdentityAttestation`,
   `CeremonyRecord` when culturally appropriate, or `InstitutionalAction`.
3. Source: DZI-1 module, CSLEIS council, AAIS evaluator, or optional external
   human witness.
4. Integrity Metadata: hash, signature, timestamp, and chain of custody.
5. Linked Identities: actors, targets, evaluators, and affected parties.
6. Linked Events: CCS Event IDs this evidence supports.
7. Law Surface: CSLEIS governance rules that apply, and whether they passed or
   failed.
8. Continuity Fields: cultural legitimacy, sovereignty impact, ecological
   impact, intergenerational relevance, and institutional implications.

### Reproducibility Requirements

- Same inputs produce same outputs.
- Same law produces same evaluation.
- Same evidence produces same continuity trace.
- No silent mutations.
- No orphaned evidence.

## First End-to-End Test Scenario

Scenario: AAIS-assisted governance decision with real continuity evidence.

### Actors as CCS Identities

- Human: a real CSLEIS council member.
- Institution: a CSLEIS governance body.
- AI: AAIS-governed agent with a registered identity.
- Land or Resource: a real ecological or cultural asset.

### Flow

1. Event occurs: a governance question arises involving land, culture, or
   community. AAIS logs a `CognitiveEvent`; CSLEIS logs a `GovernanceEvent`.
   Both are written to CCS.
2. AAIS evaluation: AAIS applies invariants, authority continuity, law modules,
   risk analysis, and uncertainty quantification. It produces a
   `TechnicalEvaluation`.
3. CSLEIS evaluation: CSLEIS applies cultural legitimacy, sovereignty rules,
   ecological impact, and institutional authority. It produces a
   `CulturalEvaluation`.
4. DZI-1 evidence emission: DZI-1 emits continuity trace, identity attestation,
   governance record, and ecological or cultural impact evidence. All are
   registered as CCS Evidence.
5. Continuity trace assembly: CCS assembles events, evaluations, evidence, law
   surfaces, and identity lineage into a reproducible `ContinuityTrace`.
6. Reproducibility test: run the scenario again with the same inputs, law, and
   identities. Expected outputs are the same evaluations, same evidence, and
   same continuity trace.

This is the first handshake milestone for AAIS, CCS, CSLEIS, DZI-1, and DAR-Z.
