---
title: UL Verb Language
description: First-class verb language for AAIS and Project Infi, positioned in front of ISL and ULX.
---

# UL Verb Language

UL is the verb language used to express imperative actions in AAIS and Project Infi.
In this repository, UL is now formalized as a live runtime surface so the command vocabulary can be parsed, validated, and named explicitly before it is normalized into governed intent.

## Relation to ISL and ULX

- `UL` is the verb language: the direct action phrasing.
- `ISL` is the intent layer: it normalizes and governs the action before execution.
- `ULX` is the executable substrate: it validates and runs the governed result.

Working sequence in this repository:

`UL` -> `ISL` -> `ULX`

That sequence is the naming convention used by the ULX registry and the ULX cockpit docs.

## Where it appears

- [UL Runtime](../runtime/ul-runtime.md)
- [ULX Language Registry](./ulx-language-registry.md)
- [ULX IDE Integration Map](./ulx-ide-integration.md)
- [ISL Runtime](../runtime/isl-runtime.md)

## Status

UL is live as `@aaes-os/ul-runtime`.
It keeps the same UL -> ISL -> ULX chain rather than bypassing ISL or ULX governance.
