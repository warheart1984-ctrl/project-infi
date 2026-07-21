---
title: CML/Voss Runtime
description: Live runtime surface for CML-2, CVM-1, and The Voss Binding corpus families.
---

# CML/Voss Runtime

The CML/Voss Runtime is the live corpus surface for `CML-2`, `CVM-1`, and `The Voss Binding`.
It preserves the three named families as governed records and exposes the Voss binding between meaning constraints and verification models.

## Package

- `@aaes-os/cml-voss-runtime`
- Source: `packages/cml-voss-runtime/src/index.ts`
- Tests: `packages/cml-voss-runtime/src/index.test.ts`

## Runtime responsibilities

- Register CML/CVM/Voss corpus family records
- Preserve aliases and canonical source references
- Validate purpose, traceability, and source metadata
- Register bindings between corpus families
- Expose deterministic hashes and runtime snapshots for audit evidence

## Boundary

This package makes the named corpus families live without pretending the entire historical CML/CVM universe is implemented.
The live claim covers `CML-2`, `CVM-1`, and `The Voss Binding` as named governed surfaces in this checkout.

## Related surfaces

- [ULX Language Registry](../ulx/ulx-language-registry.md)
- [Live Surfaces](./live-surfaces.md)
- [COE Runtime](./coe-runtime.md)
