---
title: CodaRuntime
description: Live runtime facade that composes the Coda corpus with the NovaCoda substrate.
---

# CodaRuntime

CodaRuntime composes the live Coda corpus with the NovaCoda substrate and exposes a small snapshot API for
workspace-level runtime status.

## Package source

- [packages/coda-runtime/src/index.ts](../../../packages/coda-runtime/src/index.ts)

## Runtime contract

- Compose the corpus summary from CodaDoc
- Hold the live and doc-forward split in a runtime snapshot
- Bridge to the NovaCoda runtime facade
- Provide query helpers for surface lookup

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [CodaDoc](./coda-doc.md)
- [Nova Substrate](./nova-substrate.md)
- [NovaCoda](./nova-coda.md)
