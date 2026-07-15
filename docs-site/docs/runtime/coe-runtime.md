---
title: COE Runtime
description: Live Constitutional Operating Environment runtime for governed routes, schedules, promotion workflows, and execution receipts.
---

# COE Runtime

The COE Runtime is the live Constitutional Operating Environment surface.
It routes governed intents, schedules constrained workflows, promotes artifacts under authority, and emits deterministic execution receipts.

Working chain:

`CSL` -> `ISL` -> `CIC` -> `CCC` -> `COE`

## Package

- `@aaes-os/coe-runtime`
- Source: `packages/coe-runtime/src/index.ts`
- Tests: `packages/coe-runtime/src/index.test.ts`

## Runtime responsibilities

- Register governed execution routes
- Schedule workflows with triggers and constraints
- Promote artifact types with evidence and authority
- Validate traceability for every execution subject
- Emit deterministic execution receipts with evidence and traceability hashes
- Track accepted routes, schedules, promotions, rejected subjects, and receipts

## Boundary

COE defines governed execution.
It does not replace CSL schemas, ISL intent authority, CIC inference, or CCC replay.
Instead, it enforces those layers at the execution edge and emits receipt material for audit and release evidence.

## Related surfaces

- [CSL Runtime](./csl-runtime.md)
- [ISL Runtime](./isl-runtime.md)
- [CIC Runtime](./cic-runtime.md)
- [CCC Runtime](./ccc-runtime.md)
- [ULX Language Registry](../ulx/ulx-language-registry.md)
