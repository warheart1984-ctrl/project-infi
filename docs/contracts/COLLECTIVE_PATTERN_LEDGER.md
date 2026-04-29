# Collective Pattern Ledger

## Purpose

This file admits the Collective Pattern Ledger into active AAIS law.

The ledger exists to preserve governed evidence about:

- success
- failure
- near miss
- recovered failure
- unresolved evidence
- pending review

Its purpose is twofold:

- Hall of Shame feeds defense
- Hall of Fame feeds guidance

Neither is allowed to bypass governing law.

## Core Law

The Collective Pattern Ledger is governed by these rules:

1. no silent failure
2. no unearned fame
3. no guidance without repeatable verification
4. no defensive evidence may bypass law
5. no constructive evidence may override stronger defensive evidence
6. local truth remains authoritative
7. collective sharing is signature-only, never raw experience

## Evidence States

The primary ledger classifications are:

- `success`
  - verified acceptable outcome within governing law
- `failure`
  - verified incorrect, unsafe, misaligned, or law-violating outcome
- `near_miss`
  - failure was approached closely enough to matter, but containment or
    recovery prevented final harm
- `recovered_failure`
  - failure occurred, but the corrective path itself demonstrated reusable
    successful structure
- `unresolved`
  - evidence is incomplete or contradictory
- `pending_review`
  - withheld for higher-order or operator review

## Event Sources

The ledger accepts candidates only from defined sources.

Approved source classes:

- `runtime`
- `law_gate`
- `verifier`
- `evaluator`
- `mutation_engine`
- `operator_override`
- `recovery_subsystem`
- `routing_subsystem`
- `immune_system`
- `guidance_system`
- `external_contractor_result`

Minimum candidate requirements:

- source identifier
- timestamp
- event type
- evidence reference or trace bundle
- confidence basis
- governing context

If source identity or evidence shape is missing, the candidate fails closed.

## Severity Model

Hall of Shame evidence uses this severity ladder:

- `S1`
  - minor inefficiency
- `S2`
  - incorrect but harmless
- `S3`
  - repeated degraded behavior or significant near miss
- `S4`
  - law breach, safety breach, or strong containment risk
- `S5`
  - severe containment event, privacy threat, control threat, or critical
    governance failure

## Admission Rules

### Hall of Shame

- verified `failure` -> mandatory Hall of Shame entry
- `near_miss` -> warning-form shame evidence by default
- `recovered_failure` -> shame entry for the original failure remains mandatory

Law:

If a verified failure occurs and no Hall of Shame entry is created, that
missing record is itself a governance problem.

### Hall of Fame

- verified `success` -> fame candidate
- repeatable, stable, low-risk success -> fame progression
- guidance promotion requires repeatability, stable law compliance, and low
  contradiction pressure

Hall of Fame is guidance evidence.

It is not law.

## Conflict Order

When Hall of Fame and Hall of Shame appear to disagree, the priority order is:

1. governing law
2. Hall of Shame defensive evidence
3. Hall of Fame guidance evidence
4. heuristic preference

Law always wins.

Known-dangerous patterns block merely helpful patterns.

## Immune Integration

The ledger is not isolated from immune posture.

Mandatory immune routing rules:

- `S1`
  - local record only
- `S2`
  - local record, trend/watch eligible
- `S3`
  - immune review eligible
- `S4`
  - mandatory immune escalation
- `S5`
  - immediate immune escalation and containment flow

Core escalation rule:

- severe shame evidence or repeated shame evidence must route into the immune
  system

This aligns with:

- [`src/immune_system.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_system.py>)
- [`src/immune_protocol.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_protocol.py>)

## Guidance And Evolution Integration

The strongest live runtime mapping today is in EvolveEngine.

Active runtime evidence:

- [`evolve_engine/trace_store.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/evolve_engine/trace_store.py>)
  - `hall_of_fame`
  - `hall_of_shame`
- [`evolve_engine/service.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/evolve_engine/service.py>)
  - evolve results, violations, and hall counts
- [`src/api.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/api.py>)
  - hall query routes for evolve traces

Ledger guidance rules:

- Hall of Shame feeds rejection signatures, anti-regression seeds, defensive
  evaluator context, and containment heuristics
- Hall of Fame feeds bounded guidance, safe seeds, and reusable
  low-risk structures

No Fame-derived seed may bypass:

- law gate
- evaluator review
- bounded mutation policy
- operator authority

## Export And Sharing Rules

The ledger may contribute to collective improvement only through sanitized
signatures.

What may not leave the local system:

- raw prompts
- raw chat logs
- raw code
- raw traces
- raw documents
- private workflow history
- reconstructable user or organization structure

What may leave the local system:

- approved abstracted signatures
- normalized failure or success classes
- severity bands
- mitigation categories
- guidance categories
- version-compatibility metadata

Collective sharing is signature-only.

This aligns with the ARIS non-copy clause:

- raw outside proposals stay local
- raw private runs stay local
- only abstracted or signature-only forms may move into collective guidance

Local truth remains authoritative.

## Current AAIS Status

The Collective Pattern Ledger is now active AAIS law.

That does not mean every runtime lane already writes into one universal shared
ledger.

Current truth:

- the law is admitted
- EvolveEngine already provides the strongest live Hall of Fame / Hall of Shame
  runtime surface
- broader repo-wide ledger coverage remains incomplete and should grow through
  governed integration rather than ad hoc logging

## Source Lineage

This contract is admitted from:

- [Collective Pattern Ledger — Integration Contract.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/Collective Pattern Ledger — Integration Contract.docx>)

Related lineage:

- [hall of fame_shame demo version.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/hall of fame_shame demo version.docx>)
- [hall of fame_shame real world feature.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/hall of fame_shame real world feature.docx>)

The raw files remain archive material.

This markdown file is the active admitted AAIS law surface.
