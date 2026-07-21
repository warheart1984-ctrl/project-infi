# AAES-OS Control Plane Specification

## Purpose

This companion specification defines the governed observation and control contract for AAES-OS.

The Control Plane is a constitutional window into the ecosystem. It does not contain business logic. It exposes discovery, state, governance hooks, replay hooks, and conformance surfaces.

## Core domains exposed

- Workspace discovery
- Runtime discovery
- Trust state
- Route evaluation
- CEP status
- Evidence and provenance
- Replay
- Conformance status
- Governance events
- Constitutional receipts
- System health

## Workspace discovery

The Control Plane MUST be able to list:

- Workspaces
- Repositories
- Services
- Models

Each discovered entity SHOULD include:

- Identity
- Type
- Domain
- Trust status
- Conformance status

## Runtime discovery

The Control Plane MUST be able to enumerate:

- Router X runtimes
- CEP workers
- Model hosts
- Pipelines

Each runtime SHOULD expose:

- Identity
- Capabilities
- Health
- Governance tier

## Trust state

The Control Plane MUST expose trust packets, trust timelines, trust bands, and trust anomalies.

Trust queries SHOULD be filterable by:

- Relationship identity
- Domain
- Governance tier
- Trust band

## Route evaluation

The Control Plane MUST support governed route evaluation requests and MUST return a decision packet containing:

- Trust evaluation
- Policy evaluation
- Evidence references
- Constitutional clauses
- Conformance status
- Signed receipt

## CEP status

The Control Plane MUST expose:

- Artifact counts
- Promotion queues
- Audit status
- Backlog status

These views SHOULD be queryable per domain and tier.

## Evidence and provenance

The Control Plane MUST provide query access to:

- Evidence artifacts
- Provenance chains
- Lineage graphs

Queries SHOULD be possible by artifact, decision, or relationship identity.

## Replay

The Control Plane MUST expose replay sessions and replay reports.

Replay surfaces SHOULD support:

- Historical replay
- Counterfactual replay
- Governance comparison
- Configuration diff inspection

## Conformance status

The Control Plane MUST expose whether a runtime, model, or pipeline is:

- conformant
- partial
- non-conformant

## Governance events

The Control Plane MUST expose governance decisions, proposals, amendments, and feedback artifacts.

Governance events SHOULD be streamable to clients through a governed event channel.

## Constitutional receipts

The Control Plane MUST expose signed receipts for:

- Decisions
- Replays
- Promotions
- Deployments

## System health

The Control Plane MUST expose health for:

- Governance Plane
- Knowledge Plane
- Execution Plane
- Trust Fabric
- Replay Engine
- CEP

## Control-plane rule

All consoles, IDEs, and CLIs MUST speak through the Control Plane for discovery and governance visibility.

They MUST NOT invent their own governance semantics.
