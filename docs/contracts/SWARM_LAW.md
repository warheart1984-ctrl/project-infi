# Swarm Law

## Purpose

This file admits Swarm Law into active AAIS doctrine.

Swarm Law governs bounded multi-agent coordination when multiple AAIS instances
or agent-like runtimes must share space, negotiate role priority, or degrade
without improvisation.

It exists to ensure:

- deterministic yielding
- lawful disagreement resolution
- verified role transfer
- graceful degradation
- no hidden improvisation under pressure

## Core Law

Swarm coordination is governed by these rules:

1. priority decides yield before force decides outcome
2. disagreement must resolve through declared arbitration, not improvisation
3. role transfer requires capability, clearance, and record
4. uncertainty triggers hold or degrade, not confident bluffing
5. partial failure must degrade lawfully instead of cascading silently

## Swarm Coordination Rules

### Yielding

In single-lane or constrained paths:

- the lower-priority role yields
- if roles are equal, the agent farther from destination yields
- yielding must happen through a bounded stop or standoff action

### Disagreement

When two units disagree:

1. exchange spatial-state packets
2. compute a declared arbitration basis
3. the higher-cost or lower-priority side yields
4. repeated unresolved disagreement escalates to full stop and supervision

### Mapping Conflict

When two agents report conflicting occupancy for the same space:

- confidence-weighted merge applies
- motion stops until the merged map is acknowledged

### No Improvisation

If safety envelope, uncertainty, or comms thresholds are crossed:

- halt
- broadcast hold or degraded state
- wait for verified reroute or supervisory resolution

Swarm law prefers stoppage over unsafe improvisation.

## Identity And Role Enforcement

Role transitions are not free.

They require:

1. capability verification
2. lane or corridor clearance confirmation
3. durable handoff logging

If an agent attempts unverified takeover:

- the system must treat it as a governance violation
- the offender is restricted rather than trusted

## Degradation Doctrine

Partial failure must be routed through lawful degraded modes.

Canonical degraded forms from the source doctrine are:

- `retreat`
- `relay_only`
- `mapping_only`
- `freeze_request_reroute`
- `observer_only`

Meaning:

- degraded units do not improvise new authority
- degraded units preserve collective safety first
- healthy peers may ratify or route around the degraded state

## AAIS Runtime Interpretation

The raw source was written for a physically constrained multi-agent field
setting.

AAIS admits the law more generally as:

- bounded multi-agent negotiation law
- role-transfer law
- degrade-before-improvise law
- hold-state law under uncertainty

This means the doctrine applies beyond mining or robotics wording whenever AAIS
coordinates multiple bounded agents or bounded agent-like lanes.

## Current Live Scope In AAIS

Swarm Law is admitted as active doctrine, but the full physical multi-agent
runtime described in the source is not installed as a live AAIS subsystem.

Current live coverage is partial and mainly visible through:

- [`src/cognitive_bridge.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/cognitive_bridge.py>)
  - `swarm` is treated as a model-only source and cannot self-execute
- [`src/governed_direct_pipeline.py`](</C:/Users/randj/Desktop/project infi/AAIS-main/src/governed_direct_pipeline.py>)
  - swarm-originated deliberation is routed as a governed bridge hop

Current truth:

- swarm-originated cognition is bounded
- swarm may deliberate or contribute strategy context
- swarm may not bypass bridge, approval, or governed execution

## What Is Not Yet Live

The following are not yet installed as full active runtime features in this
repo:

- full peer-to-peer spatial swarm arbitration
- live corridor clearance verification
- live distributed handoff ledger quorum
- live degraded swarm field controller

So the law is active now, while the broader field-runtime embodiment remains a
partial or future integration surface.

## Relationship To Other Laws

Swarm Law does not override:

- Jarvis authority
- Project Infi admission law
- immune protocol
- phase gate
- operator sovereignty

Swarm coordination remains subordinate to higher governing law.

## Source Lineage

This contract is admitted from:

- [swarm law (2).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/swarm law (2).docx>)

Related lineage:

- [swarm law (1).docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/swarm law (1).docx>)
- [swarm law.docx](</C:/Users/randj/Desktop/project infi/AAIS-main/docs/_archive/workspace_pull/project-infi-root/swarm law.docx>)

The raw files remain archive material.

This markdown file is the active admitted Swarm Law surface for AAIS.

