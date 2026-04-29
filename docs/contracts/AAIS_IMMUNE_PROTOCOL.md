# AAIS Immune Protocol

## Purpose

This file defines the active immune contract for AAIS.

The immune protocol exists to inspect governed traffic, classify anomalies or
violations, and apply bounded protective action before unsafe traffic is
treated as normal runtime flow.

It is not a general autonomous authority surface.

It is a governed defensive layer.

## Runtime Role

The active immune path currently spans two cooperating layers:

- [`src/immune_protocol.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_protocol.py>)
  - packet-traffic inspection and bounded corrective action
- [`src/immune_system.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_system.py>)
  - posture, incidents, quarantine state, and durable immune event history

In live AAIS terms, the protocol sits between:

- governed packet traffic
- security or protocol signals
- operator-visible incident state

## Core Law

The immune protocol is governed by these rules:

1. traffic is inspected before it is treated as safe
2. anomalies and violations must be classified, never ignored
3. protective action must remain bounded and explainable
4. no silent immune mutation is allowed
5. operator visibility is required for meaningful posture change
6. immune action may constrain runtime flow but does not replace Jarvis or
   Project Infi authority

## Immune Responses

The active response ladder is:

- `ALLOW`
- `CLAMP`
- `REROUTE`
- `REJECT`
- `QUARANTINE`

Meaning:

- `ALLOW`
  - traffic is clean enough to continue
- `CLAMP`
  - traffic is allowed after bounded reduction or cleanup
- `REROUTE`
  - traffic is pushed onto the safer lane or safer boundary
- `REJECT`
  - traffic fails closed and does not continue
- `QUARANTINE`
  - the threat is severe enough that components or paths are isolated

## What The Protocol Inspects

Current live packet-law checks include:

- invalid packet structure
- invalid packet shape
- fast-lane packet bloat
- tool bleed into the direct cognitive lane
- authority bypass attempts that skip `GB` or `Jarvis`
- memory/context leak keys on the direct lane

These checks are active in
[`src/immune_protocol.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_protocol.py>).

## What The Immune System Tracks

The controller persists and exposes:

- system mode
- isolated modules
- quarantined modules
- blacklisted modules
- quarantined resources
- disabled tools
- caller overrides
- recent immune events
- incidents and active incident state

This state is managed by
[`src/immune_system.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/immune_system.py>).

## Signal Families

The immune system currently accepts three main classes of signals:

- security events through `observe_security_event`
- module-governance events through `observe_module_signal`
- protocol-boundary events through `observe_protocol_signal`

Protocol-boundary observation is the important bridge for:

- reasoning exchange
- governed event chain
- Super Nova bounded immune observation
- other governed boundary checks that need posture effects without jumping
  directly to module quarantine by default

## Integration Surfaces

The immune protocol already participates in live AAIS through:

- [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
- [`src/governed_event_chain.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_event_chain.py>)
- [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
- [`src/api.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/api.py>)
- Nova guarded boundary documentation in
  [`docs/contracts/seams/SEAM-SN-001-super-nova-governance-boundary.md`](./seams/SEAM-SN-001-super-nova-governance-boundary.md)

## Operator Rule

Immune posture is part of operator truth.

That means:

- immune events must be recorded
- posture changes must be visible
- incidents must be inspectable
- protective actions must remain attributable

AAIS may defend itself, but it may not hide the fact that it did so.

## Current Scope Limits

The immune protocol is live, but not yet complete across every subsystem.

Current limits:

- broader predictor/invariant-driven immune automation remains incomplete
- Super Nova coupling remains observe-only rather than full immune autonomy
- cross-system incident choreography is still more code-local than
  subsystem-contract local

## Source Lineage

This contract is admitted from live code plus archive lineage:

- [AAIS Immune Protocol.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/AAIS Immune Protocol.docx>)

The raw source remains lineage material.

This markdown file is the active immune contract for AAIS.

