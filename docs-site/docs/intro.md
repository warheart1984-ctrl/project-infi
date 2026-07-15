# Welcome to AAES-OS

AAES-OS is a governed, multi-backend cognitive runtime designed for stable, accountable, and vendor-agnostic AI systems.

This documentation covers:

- Governed Runtime Core
- Policy DSL
- Capability Graph
- Pattern Ledger
- Coding Assistant
- Nova Shell
- Infinity Agents
- Governance Dashboard
- Capability Graph Visualizer
- Runtime Lifecycle

## Start here

The first-class runtime entry point is now the [Live Surfaces](./runtime/live-surfaces.md) hub.
It links directly to the live package surfaces for CodaDoc, CodaRuntime, NovaCoda, the Nova substrate client,
ISL Runtime, and GCRE-SYSMIN-001.

- [Live Surfaces](./runtime/live-surfaces.md)
- [Runtime Core](./runtime/runtime-core.md)
- [UL Verb Language](./ulx/ul-verb-language.md)
- [ULX Language Registry](./ulx/ulx-language-registry.md)
- [NovaCoda](./runtime/nova-coda.md)
- [ISL Runtime](./runtime/isl-runtime.md)

## Quick Start

```bash
pnpm install
pnpm --filter @aaes-os/coding-assistant build
pnpm --filter aaes-os-docs start
```

## Coding Subsystem

The coding assistant unifies Codex, Cursor, Devin, DeepSeek-Coder, Groq, and local LLMs behind a single `CodingRouter` with policy-driven backend selection.

See [Coding Assistant Overview](./coding-assistant/overview.md) to get started.
