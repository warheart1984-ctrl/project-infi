---
title: CIC Runtime
description: Live Constitutional Inference Contract runtime for deterministic rules, bindings, and semantic conclusions.
---

# CIC Runtime

The CIC Runtime is the live Constitutional Inference Contract surface.
It evaluates deterministic constitutional rules against schema and intent context, then emits an audit-ready semantic graph.

Working chain:

`CSL` -> `ISL` -> `CIC` -> `CCC` -> `COE`

## Package

- `@aaes-os/cic-runtime`
- Source: `packages/cic-runtime/src/index.ts`
- Tests: `packages/cic-runtime/src/index.test.ts`

## Runtime responsibilities

- Register constitutional inference rules
- Validate conditions, conclusions, bindings, and traceability
- Evaluate simple deterministic operators over JSON-like context
- Preserve semantic bindings between artifact fields and constitutional concepts
- Emit semantic graph outputs with matched rules, conclusions, bindings, and evaluations
- Track accepted rules, rejected rules, and inference count for audit snapshots

## Boundary

CIC defines meaning.
It does not define artifact schemas directly, replace ISL authority checks, or execute workflows.
Instead, it consumes CSL/ISL-shaped context and produces deterministic reasoning that CCC and COE can replay or execute under governance.

## Related surfaces

- [CSL Runtime](./csl-runtime.md)
- [ISL Runtime](./isl-runtime.md)
- [ULX Language Registry](../ulx/ulx-language-registry.md)
