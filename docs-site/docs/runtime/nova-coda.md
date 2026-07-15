---
title: NovaCoda
description: Live runtime facade over the Nova substrate and typed socket client.
---

# NovaCoda

NovaCoda is the live runtime facade over the Nova substrate and typed socket client.
It now exposes real request/response operations instead of a write-only ping wrapper.

## Package source

- [packages/nova-coda/src/index.ts](../../../packages/nova-coda/src/index.ts)

## Runtime contract

- Connect to the Nova substrate client
- Ping the substrate and expose a runtime snapshot
- Allocate arenas, spawn fibers, infer, run syscalls, check constitutional state, and load plugins through typed operations
- Preserve operation counters and the last operation in the runtime snapshot

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [Nova Substrate](./nova-substrate.md)
- [Nova Substrate Client](./nova-substrate-client.md)
- [CodaRuntime](./coda-runtime.md)
