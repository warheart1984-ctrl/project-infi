---
title: UL Runtime
description: Live verb-language runtime for compiling Universal Language actions into ISL-compatible intent.
---

# UL Runtime

The UL Runtime is the live Universal Language verb surface.
It turns direct action phrasing into deterministic, evidence-bearing command records before those records are normalized into ISL intent and passed toward ULX governance.

Working chain:

`UL` -> `ISL` -> `ULX`

## Package

- `@aaes-os/ul-runtime`
- Source: `packages/ul-runtime/src/index.ts`
- Tests: `packages/ul-runtime/src/index.test.ts`

## Runtime responsibilities

- Parse operator verb phrases such as `verify sovereign/kernel for release readiness as alice`
- Normalize structured verb commands into deterministic UL command records
- Validate actor, verb, target, evidence, authority, and traceability requirements
- Compile accepted UL commands into ISL-compatible intent drafts
- Preserve UL provenance in the generated intent context
- Emit runtime snapshots for accepted and rejected command compilation

## Boundary

UL is the action-language entry point.
It does not replace ISL authority normalization or ULX execution governance.
Instead, UL keeps the original verb command visible so downstream intent, replay, and audit surfaces can prove exactly which action phrase was promoted.

## Related surfaces

- [UL Verb Language](../ulx/ul-verb-language.md)
- [ULX Language Registry](../ulx/ulx-language-registry.md)
- [ISL Runtime](./isl-runtime.md)
- [ULX Governance](../ulx/ulx-governance.md)
