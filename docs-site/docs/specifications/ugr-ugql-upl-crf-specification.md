---
title: UGR, UGQL, UPL, and CRF Specification
---

# UGR, UGQL, UPL, and CRF Specification

This page mirrors the unified knowledge, query, package, and replay substrate specification for the sovereign control plane and ULX cockpit.

## Scope

- **UGR** is the governed knowledge substrate for worlds, documents, metrics, concepts, rules, agents, arenas, lineages, and mesh links.
- **UGQL** is the cross-domain query language for selecting, searching, tracing, aggregating, and comparing knowledge.
- **UPL** is the typed package language for worlds, constitutions, rules, agents, arenas, concepts, and evidence policies.
- **CRF** is the portable constitutional replay artifact for replay, inspection, and optional adoption.
- **Constitutional Change Ledger** records governance evolution with lineage, replay, impact, and justification.

## Constitutional principles

- Every enduring concept has one authoritative home.
- Knowledge, governance, and replay remain separately addressable.
- Evidence is required for claims that mutate governance or authority.
- UGR stays neutral with respect to truth claims.
- CRF remains portable without silently mutating local governance.

## Core objects

### Knowledge objects

Knowledge objects carry:

- `id`
- `kind`
- `name`
- `domain`
- `summary`
- `tags`
- `concepts`
- `stabilityScore`
- `riskProfile`
- `lineage`
- `metadata`

### Worlds

Worlds extend knowledge objects with:

- `constitutionRef`
- `rules`
- `agents`
- `arenas`
- `state`
- `historyRef`

### Mesh and lineage

The mesh connects worlds with similarity and stability metadata. Lineage is a replayable graph of relationships such as:

- `EVOLVES_FROM`
- `JUSTIFIED_BY`
- `SUPERSEDES`
- `RESPONDS_TO`
- `PRECEDES`
- `FOLLOWS`

## UGQL forms

- `SELECT <target> FROM <scope> WHERE <conditions> WITH <options>`
- `SEARCH <target> FROM <scope> WHERE <conditions> WITH <options>`
- `TRACE <target> FROM <scope> WHERE <conditions> WITH <options>`
- `AGGREGATE <target> FROM <scope> WHERE <conditions> WITH <options>`
- `COMPARE <target> FROM <scope> WHERE <conditions> WITH <options>`

## UPL

UPL supports:

- typed identifiers
- module composition
- constitution and governance bindings
- evidence policies
- replayable world definitions

UPL must not permit a rule without a domain, a constitution without a change process, or an untracked cross-world reference.

## CRF

CRF is replayable and inspectable. A valid CRF exposes:

- metadata
- timeline
- governance states
- impact graph
- lineage
- evidence bundle
- visualization data
- signatures

## Constitutional Change Ledger

The ledger records governance changes with:

- entry identity
- change type
- artifact reference
- lineage
- justification evidence
- related incidents
- council vote

This ledger is the system's governance memory and the source of replayable constitutional history.
