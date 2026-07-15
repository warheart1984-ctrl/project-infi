---
title: ISL Runtime
description: Live Intent Specification Layer runtime for governed intents, evidence, and authority.
---

# ISL Runtime

The ISL Runtime is the live Intent Specification Layer surface for governed intents, evidence, authority, and
traceability.

## Package source

- [packages/isl-runtime/src/index.ts](../../../packages/isl-runtime/src/index.ts)

## Runtime contract

- Normalize intents deterministically
- Validate the actor, target, purpose, evidence, authority, and traceability fields
- Hash normalized intents into stable identifiers
- Track accepted and rejected intents in runtime snapshots

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [CodaDoc](./coda-doc.md)
- [GCRE-SYSMIN-001](./gcre-sysmin.md)

