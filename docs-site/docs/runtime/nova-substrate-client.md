---
title: Nova Substrate Client
description: Typed protocol client for the NovaCoda socket substrate.
---

# Nova Substrate Client

The Nova Substrate Client is the typed socket client for the NovaCoda substrate.
It encodes and decodes framed JSON protocol messages and handles the structured substrate responses.

## Package source

- [packages/nova-substrate-client/src/NovaCodaClient.ts](../../../packages/nova-substrate-client/src/NovaCodaClient.ts)

## Runtime contract

- Encode the NovaCoda frame header
- Decode the response header and checksum
- Speak the structured socket protocol
- Expose typed helper surfaces for arena, fiber, inference, syscall, plugin, and constitutional checks

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [Nova Substrate](./nova-substrate.md)
- [NovaCoda](./nova-coda.md)
