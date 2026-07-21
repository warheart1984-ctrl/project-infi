---
title: CCC Runtime
description: Live Constitutional Continuity Contract runtime for replay contracts, timelines, and lineage invariants.
---

# CCC Runtime

The CCC Runtime is the live Constitutional Continuity Contract surface.
It preserves replay contracts, lineage invariants, and timeline evidence so constitutional truth can be checked across time.

Working chain:

`CSL` -> `ISL` -> `CIC` -> `CCC` -> `COE`

## Package

- `@aaes-os/ccc-runtime`
- Source: `packages/ccc-runtime/src/index.ts`
- Tests: `packages/ccc-runtime/src/index.test.ts`

## Runtime responsibilities

- Register constitutional continuity contracts
- Validate invariant, scope, replay contract, timeline, ledger references, and traceability
- Emit deterministic replay IDs, timeline hashes, and ledger hashes
- Track accepted, rejected, and replayed continuities
- Preserve replay evidence for downstream release and audit packets

## Boundary

CCC defines continuity and replay.
It does not route or execute workflows directly.
Instead, it gives COE and release packaging a deterministic continuity proof surface.

## Related surfaces

- [CSL Runtime](./csl-runtime.md)
- [CIC Runtime](./cic-runtime.md)
- [ULX Language Registry](../ulx/ulx-language-registry.md)
