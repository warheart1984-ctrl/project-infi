---
title: Nova Substrate
description: Rust NovaCoda socket substrate that implements the live protocol surface behind the typed client.
---

# Nova Substrate

The Nova Substrate is the Rust socket runtime that backs the NovaCoda protocol.
It is the lowest-level live substrate in the NovaCoda stack and provides the framed protocol responses that the typed client consumes.

## Package source

- [packages/nova-substrate/Cargo.toml](../../../packages/nova-substrate/Cargo.toml)
- [packages/nova-substrate/src/main.rs](../../../packages/nova-substrate/src/main.rs)

## Runtime contract

- Bind the NovaCoda socket path
- Decode protocol frames and checksums
- Serve arena, fiber, inference, syscall, plugin, and constitutional check responses
- Hold the runtime state required for the client and facade layers above it

## Related pages

- [Live Surfaces](./live-surfaces.md)
- [Nova Substrate Client](./nova-substrate-client.md)
- [NovaCoda](./nova-coda.md)
