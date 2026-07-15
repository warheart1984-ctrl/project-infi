---
title: CSL Runtime
description: Live Constitutional Schema Layer runtime for governed artifact schemas and evolution contracts.
---

# CSL Runtime

The CSL Runtime is the live Constitutional Schema Layer surface.
It defines governed artifact schemas, validates their required fields, and preserves deterministic identity for schema evolution.

Working chain:

`CSL` -> `ISL` -> `CIC` -> `CCC` -> `COE`

## Package

- `@aaes-os/csl-runtime`
- Source: `packages/csl-runtime/src/index.ts`
- Tests: `packages/csl-runtime/src/index.test.ts`

## Runtime responsibilities

- Register constitutional artifact schemas
- Validate artifact name, tier, kind, fields, dynamics, horizon, and traceability
- Preserve deterministic schema identity through content hashing
- Track accepted and rejected schema registrations
- Expose snapshots for audit and release evidence

## Boundary

CSL defines constitutional state and artifact evolution.
It does not replace ISL intent authority, CIC inference, CCC continuity, or COE execution.
Instead, it gives those later layers a stable schema substrate to reference.

## Related surfaces

- [UL Runtime](./ul-runtime.md)
- [ISL Runtime](./isl-runtime.md)
- [ULX Language Registry](../ulx/ulx-language-registry.md)
- [AAES-OS Constitutional Kernel Specification](../specifications/aaes-os-engineering-specification.md)
