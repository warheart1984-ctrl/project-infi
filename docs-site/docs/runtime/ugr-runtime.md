---
title: UGR Runtime
description: Live UGR / UGQL / UPL / CRF runtime surface for governed knowledge, query, packaging, and replay.
---

# UGR Runtime

The UGR Runtime is the live surface for the unified knowledge substrate, UGQL query language, UPL package language,
and CRF replay artifact family.
It implements the stack described in the UGR / UGQL / UPL / CRF specification as a concrete workspace package.

## Package source

- [packages/ugr-runtime/src/index.ts](../../../packages/ugr-runtime/src/index.ts)

## Runtime contract

- Ingest and resolve governed knowledge objects and worlds
- Execute deterministic UGQL-style queries over the live collections
- Register UPL modules with constitution and evidence bindings
- Validate and replay CRF artifacts and constitutional change entries
- Preserve lineage, mesh links, and replayable state snapshots

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [UGR, UGQL, UPL, and CRF Specification](../specifications/ugr-ugql-upl-crf-specification.md)
- [UGR, UGQL, UPL, and CRF v1 Conformance](../crk1/release/ugr-ugql-upl-crf-v1-conformance.md)
