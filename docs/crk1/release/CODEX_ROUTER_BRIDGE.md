# Codex Router Bridge

This document defines the thin constitutional interface between `Sovereign Router X` and the Codex handoff orchestrator.

## Purpose

`Sovereign Router X` selects the reasoning surface and route policy before any model is invoked. The handoff orchestrator then uses that decision to write the request packet, ingest the reply packet, and record evidence.

This keeps the platform vendor-neutral:

- governance and routing live in the platform
- reasoning lives in the selected model or engine
- evidence and replay live in the runtime

## Core objects

- `RouterDecision`
- `RequestPacket`
- `ReplyPacket`
- `EvidenceReceipt`
- `ReplayRecord`

## Routing flow

1. The orchestrator assembles the request packet from the prompt and minimal task context.
2. `Sovereign Router X` evaluates the packet and chooses the model family.
3. The chosen reasoning engine receives only the scoped packet.
4. The reply is schema-validated before it can be ingested.
5. The runtime records the route, the reply, and the evidence trail.

## Bridge contract

The bridge exports a small route result with:

- `requestId`
- `promptTokens`
- `selectedModel`
- `backend`
- `modelDecision`
- `routeEvaluation`
- `reason`

## Evidence boundary

The bridge does not execute the model. It only decides:

- which model should reason
- whether the request should be delayed or dropped
- what route evidence should be attached to the orchestration record

## Replay boundary

Replays should be able to reconstruct:

- the request packet
- the route decision
- the reply packet
- the resulting ledger entry

