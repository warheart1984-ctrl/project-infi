# Scorpion Roadmap

## Mission

Deliver Project Scorpion as a governed OS anomaly extractor: fixture Sentinel first,
then historian queries, Wolf CoG seam, then native kernel Sentinel.

## Claim Posture

- `asserted`: idea exists but evidence is incomplete.
- `proven`: required evidence exists and is traceable.
- `rejected`: evidence disproves or fails to support a claim.

No proof, no claim.

## Current Implementation Snapshot (2026-05-29)

- Stage 0 foundation docs: `proven` (artifacts in repository).
- Stage 1 runtime skeleton: `proven` (fixture + audit sentinels, eight fixtures, CI gate).
- Stage 2 historian queries: `proven` locally (supersession index, snapshot-query, weekly loop).
- Stage 3 Wolf CoG seam: `asserted` (substrate cross-ref + inactive ingest script).
- Stage 4 kernel Sentinel: `asserted` (audit adapter + NDJSON kernel bridge; eBPF out of tree).

## Stage 0 — Governance Foundation

- Subsystem docs under `docs/subsystems/scorpion/`.
- Proof bundle `docs/proof/scorpion/STAGE0_PROOF_BUNDLE.md`.
- AAIS subsystem spec entry (`concept` → `partial`).

## Stage 1 — Contracted Observation Lane

- `scorpion` package with FixtureSentinel and evaluators.
- CLI modes: observe, ingest, scan, judge, extract, reconstruct, report, snapshot, verify, chaos-check.
- Trace fixtures per invariant family.
- CI `scorpion-governance-gate`.

## Stage 2 — Historian And Drift Queries

- `health_drift_index.jsonl`, drift-window-query, trace-query, reconcile-query.
- `scripts/scorpion/` operator loop.

## Stage 3 — Wolf CoG OS Seam

- `runtime_scorpion_invariants` in substrate-invariants.json.
- Optional post-build trace ingest script (inactive flag).

## Stage 4 — Kernel Sentinel

- See `KERNEL_SENTINEL_DESIGN.md`.
- Promotion to `proven` requires VM/hardware replay evidence.
