---
id: ADR-0001
title: WOLF-1 v1.1 constitutional extensions
date: 2026-06-25
doc: wolf1-arch
status: accepted
principle: fail-safe-not-fail-silent
---

# ADR-0001: WOLF-1 v1.1 Constitutional Extensions

## Context

Architectural review (Bradley Bates / SkillsMcGee) identified gaps in meta-governance, invariant provenance, epistemic limits of receipts, binary safe-mode, anomaly discovery, and constitutional evolution.

## Decision

Adopt v1.1 extensions: invariant promotion (4.9), CRK-1 meta-governance (4.10), epistemic receipts (6.4), graded safe-mode S0–S3 (8.5), anomaly discovery (12.4), evolution protocol (14).

## Evidence

- Bradley Bates (SkillsMcGee) architectural review cycle (June 2026)
- `docs/wolf1/Bradley_Bates_Critique_Resolution_Map.md` — critique-to-section traceability
- Amendment `amendments/amendment-0001.md`
- Specification `specifications/wolf1-arch-v1.1.md`

## Consequences

- Ground can verify CRK-1 via redundant evaluators and replay.
- Safe-mode degradation is graduated, not binary.
- Unknown-unknowns have a detection path outside fixed fault codes.
