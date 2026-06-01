# Forgekeeper Blueprint

## Canonical Definition

Forge Warden is a governed supply-chain reconstruction engine that enforces
truth, rebuilds environments, and preserves identity under constitutional law.

It is the runtime immune system for developer environments: unverified packages,
drifting workflows, compromised states, and uncanonical artifacts are classified
under law, then rebuilt through governed, reversible, attested rebirth—not chaos.

## Purpose

Forgekeeper is the governance control layer for Bumblebee Forge Edition.
It converts requested reconstruction intent into a bounded, review-first plan.

## Authority And Precedence

Constitutional precedence is enforced:

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Forgekeeper cannot bypass repository law.

## Core Responsibilities

- Accept reconstruction intents as scoped requests.
- Produce non-destructive execution plans by default.
- Require explicit gate decisions before any mutating action.
- Record claim labels (`asserted`, `proven`, `rejected`) on major outcomes.
- Link claims to proof artifacts.

## Non-Goals

- No hidden auto-apply behavior.
- No destructive cleanup workflows.
- No silent mutation outside review handoff.

## System Model

### Inputs

- Operator request: target scope and intent.
- Governance context: laws, contracts, and policy constraints.
- Repository context: bounded files and directory limits.

### Outputs

- Plan artifact (dry-run default).
- Gate decision record.
- Claim statement with proof reference (or explicit assertion status).

## Command Semantics Summary

- Planning commands produce analysis and plan outputs only.
- Execution commands remain gated and must be explicit, logged, and reversible.
- Unsafe command combinations are denied with contract-level errors.

## Failsafe And Rollback

- Safe default mode is dry-run planning.
- Kill switch denies execution commands and returns contained status.
- Rollback path requires replayable operation log and recovery guidance.

## Change-Of-Reality Requirement

Any behavior change in Forgekeeper must update:

1. Blueprint (`this file`)
2. Contract (`FORGEKEEPER_CLI_CONTRACT.md`)
3. Verification path (tests/commands/proof bundle)
4. Failsafe documentation

No change is accepted as `proven` without all four updates.

## Proof Policy

- Missing evidence means the claim is `asserted`.
- Contradictory evidence means the claim is `rejected`.
- Only traceable evidence may promote a claim to `proven`.
