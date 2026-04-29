# AAIS Cognitive Bridge Runtime Law

This file is the active runtime contract for the Cognitive Bridge layer.

The bridge is the lawful ingress between incoming intent and live AAIS runtime
behavior. It is not a convenience helper. It is the declared boundary where
meaning is normalized, law is attached, and unsafe motion is stopped.

## Core Rule

The Cognitive Bridge is the only legal ingress for governed cognitive packets.

No proposal, lane, swarm packet, provider request, or reasoning ingress may
become runtime motion unless it first resolves into the bridge packet shape and
receives a bridge decision.

## Runtime Law

The bridge layer must enforce all of the following:

1. no execution without governance
2. no mutation outside declared contracts
3. all transitions pre-declared
4. all actions traceable
5. fail closed on uncertainty

## Bridge Duties

The bridge must:

- normalize input into one bounded packet shape
- derive doctrine path and invariant expectations
- route the packet through the governed event chain
- classify whether the packet is allowed, degraded, or blocked
- expose a structured trace that explains the decision

## Governed LLM Seam

Provider routing sits behind the bridge.

The governed LLM layer may only operate as:

- proposal-only
- bounded-envelope
- no direct execution authority
- no undeclared output shape
- no mutation authority

This means provider selection, provider model choice, and response-mode routing
must first appear as a governed proposal before any downstream runtime decides
to execute them.

## Swarm Rule

Swarm is downstream of the bridge, not parallel to it.

Swarm packets must emit normalized bridge-compatible packets and may not create
an alternate execution ingress around bridge law.

## Required Trace Path

The minimum governed trace path is:

`input -> bridge -> law gate -> execution or proposal -> validator -> commit or block`

If execution is not yet allowed, the proposal path must still be visible and
bounded.

## Failure Rule

If packet shape, doctrine attachment, invariants, provider resolution, or trace
context are missing or uncertain, the bridge path must fail closed.

Missing context is not a soft warning. It is a block condition.
