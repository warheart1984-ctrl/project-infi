# Jarvis Protocol

AAIS uses a shared Jarvis protocol to let the UI, memory, tools, specialists,
and model backends speak one common language.

## What It Is

The protocol is defined in [src/jarvis_protocol.py](../../src/jarvis_protocol.py).

It formalizes:

- normalized message roles
- context channels
- tool envelopes
- provider payload previews
- per-session turn envelopes

## Core Idea

Jarvis is not just a chat box. It is an orchestration layer.

That means one turn may contain:

- instruction context
- runtime state
- memory
- workspace evidence
- research evidence
- corrigibility guidance
- dialogue
- tool results

Instead of treating those as unrelated strings, AAIS now treats them as one
protocol with named channels.

## Roles

- `system`
- `user`
- `assistant`
- `tool`

## Channels

- `instruction`
- `runtime`
- `memory`
- `workspace`
- `research`
- `corrigibility`
- `browser`
- `specialist`
- `orchestration`
- `dialogue`
- `tool`

## Memory Board Alignment

The `memory` channel does not assume one flat undifferentiated memory bank.

Jarvis memory is now governed canonically by the
[JARVIS Memory Board Doctrine](JARVIS_MEMORY_BOARD_DOCTRINE.md), which treats
memory as:

- slot-based
- module-driven
- controller-governed
- trust-layered

Protocol implication:

- memory context may come from different slot roles instead of one flat pool
- slot purpose stays fixed even when a module is upgraded
- controller approval is required before install or swap
- lower-trust memory may inform a turn, but may not redefine doctrine,
  identity, or other higher-trust truth
- retrieval routing should respect controller and slot priority rather than
  treating every memory source as equal

Inspection route:

- `GET /api/jarvis/memory/board`

## Tool Envelope

```json
{
  "tool": "spatial_reason",
  "args": {
    "mode": "geo_distance",
    "space_id": "michigan_route",
    "from": "Grayling",
    "to": "TraverseCity"
  }
}
```

## Provider Payload

Internally AAIS keeps channel-aware protocol messages. For model calls, it can
collapse them into an OpenAI-style payload:

```json
{
  "model": "local-model",
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ],
  "stream": true,
  "temperature": 0.35,
  "max_tokens": 320,
  "mode": "builder"
}
```

## Why It Matters

This makes it easier to:

- swap model providers
- add richer tool calls
- audit what context shaped a reply
- route specialists and model profiles cleanly
- turn Jarvis into the explicit AAIS orchestration core

## API

AAIS exposes the protocol at:

- `GET /api/jarvis/protocol`
- `GET /api/jarvis/protocol?session_id=<session_id>`

The session form includes:

- protocol summary
- normalized envelope
- provider payload preview
