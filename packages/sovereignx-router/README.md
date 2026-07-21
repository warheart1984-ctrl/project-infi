# SovereignX Router

Governed compute router for the AAES-OS workspace.

## What it proves

- CPU governs scheduling, continuity, and policy
- GPU receives only work that the router allows
- CIEMS-style constraints can throttle, delay, quarantine, or drop work

## Who it is for

- developers building governed compute substrates
- operators who need explicit resource fairness
- reviewers who need a machine-readable proof surface

## How to verify it works

```bash
corepack pnpm --filter @aaes-os/sovereignx-router test
corepack pnpm --filter @aaes-os/sovereignx-router build
```

## Proof surface

This package exposes a proof surface at `src/proofSurface.ts` and validates it with the shared AAES proof-surface law.

## Constitutional Execution Contract

SovereignX execution paths now emit an execution proof surface and carry the same constitutional fields used by the governance layer:

- Execution Authority
- Execution Evidence
- Execution Verification
- Execution Compliance
- Execution Truth Boundary

The emitted execution proof surface is linked to the receipt that produced it, so operator tooling, docs, and scorecards can resolve the same execution instance deterministically.

## Hardware governance

The package also includes a deterministic SovereignX hardware governor that models the concept PDF directly:

- telemetry validation with constitutional invariants
- promotion bursts when headroom and utilization are high
- automatic retraction when thermal or power limits are near breach
- replayable event records with hashed telemetry evidence
- a machine-readable constitutional contract for the hardware router

## Failure path

If governance detects hot GPU, VRAM exhaustion, intent mismatch, or budget violation, the router degrades to CPU, delays the work, or drops/quarantines it.
