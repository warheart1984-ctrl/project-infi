# UGR, UGQL, UPL, and CRF Specification

## Status

Draft companion specification for the Project Infi constitutional runtime.

## 1. Purpose

This specification defines the unified knowledge substrate, query language, package language, and portable replay artifact used by the sovereign control plane and ULX cockpit.

The specification has four normative surfaces:

- UGR, the Unified General Repository
- UGQL, the cross-domain query language
- UPL, the Universal Policy Language for worlds, rules, agents, arenas, and evidence
- CRF, the Constitutional Replay File for portable replay and optional adoption

This specification also defines the Constitutional Change Ledger as the replayable memory of governance itself.

## 2. Constitutional principles

The system that implements this specification MUST:

- keep every enduring concept in one authoritative home
- preserve lineage for every replayable artifact
- keep knowledge, governance, and replay separately addressable
- require evidence for claims that mutate governance or authority
- keep UGR neutral with respect to truth claims
- keep CRF portable without mutating local governance silently
- treat UGR as governed institutional memory rather than a generic document store
- prefer replay of validated experience over repeating a known experiment

UGR preserves validated knowledge, successful patterns, failed experiments, and their evidence. The Constitutional Knowledge Layer governs what knowledge is admissible; UGR preserves what has already been admissibly learned.

## 3. UGR data model

UGR is the governed substrate for worlds, documents, metrics, concepts, rules, agents, arenas, lineages, and mesh links. It is also the institutional memory layer beneath the Constitutional Knowledge Layer.

### 3.1 Knowledge object

Each knowledge object MUST have:

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

### 3.2 World

A world extends the knowledge object with:

- `constitutionRef`
- `rules`
- `agents`
- `arenas`
- `state`
- `historyRef`

### 3.3 Mesh

The mesh connects worlds with similarity and stability metadata.

### 3.4 Lineage

Lineage is a replayable graph of relationships such as:

- `EVOLVES_FROM`
- `JUSTIFIED_BY`
- `SUPERSEDES`
- `RESPONDS_TO`
- `PRECEDES`
- `FOLLOWS`

### 3.5 Institutional memory and replay

UGR MUST preserve:

- admissible knowledge that has been validated by evidence
- successful patterns that can be replayed instead of rediscovered
- failed experiments with their full evidence and lineage
- constitutional context sufficient to distinguish one replay from another

UGR MUST support questions of the form:

- has this experiment already been performed
- under what constitutional context did it succeed or fail
- what evidence supported that conclusion
- can it be replayed instead of repeated
- is there a proven pattern that satisfies the objective

#### Replay-vs-repeat invariant

An implementation claiming conformance MUST NOT repeat a replayable, evidence-backed experiment for the same objective and constitutional context unless the requester explicitly declares a reason for divergence.

This invariant does not forbid exploration. It prevents unnecessary rediscovery when a replayable result already exists and the constitutional context has not changed.

#### Institutional-learning rule

UGR functions as a governed institutional-learning layer. When a replayable result exists, the default action is to reuse the replayable record and its evidence lineage rather than rerun the experiment. A new execution is only justified when the objective differs, the constitutional context differs, the evidence base has materially changed, or the requester states an explicit divergence reason.

In this model, UGR is not merely a knowledge store. It is the preserved record of institutional experience, including successful patterns, failed attempts, and the evidence needed to replay either one safely.

## 4. UGQL grammar

UGQL is a declarative, cross-domain query language.

### 4.1 Forms

- `SELECT <target> FROM <scope> WHERE <conditions> WITH <options>`
- `SEARCH <target> FROM <scope> WHERE <conditions> WITH <options>`
- `TRACE <target> FROM <scope> WHERE <conditions> WITH <options>`
- `AGGREGATE <target> FROM <scope> WHERE <conditions> WITH <options>`
- `COMPARE <target> FROM <scope> WHERE <conditions> WITH <options>`

### 4.2 Conditions

UGQL conditions MAY use:

- equality and ordering comparisons
- `CONTAINS`
- semantic match `~`
- time windows with `BETWEEN`

### 4.3 Options

UGQL options MAY include:

- `LIMIT`
- `ORDER BY`
- `GROUP BY`
- `INCLUDE`

## 5. UPL

UPL is the package language for worlds, domains, governance packs, rules, agents, and arenas.

UPL MUST support:

- typed identifiers
- module composition
- constitution and governance bindings
- evidence policies
- replayable world definitions

UPL MUST NOT allow:

- a rule without a domain
- a constitution without a change process
- a cross-world reference without lineage
- a silent promotion into a runtime with weaker evidence than declared

## 6. CRF

CRF is a portable constitutional replay artifact.

A CRF MUST contain:

- header metadata
- timeline
- governance state
- impact graph
- lineage
- evidence bundle
- signatures

A CRF MAY be:

- replayed visually
- replayed for simulation
- applied to a target environment only after local validation

## 7. Constitutional Change Ledger

The ledger is the self-governance memory of the system.

Each ledger entry MUST contain:

- `entry_id`
- `timestamp`
- `change_type`
- `artifact_ref`
- lineage with justification evidence
- council vote summary
- before/after governance state

The ledger MUST be replayable, deterministic, and immutable once promoted.

## 8. Runtime APIs

Implementations SHOULD expose:

- `/ugr/query`
- `/ugr/world/:id`
- `/ugr/object/:id`
- `/ugr/lineage/:id`
- `/ugr/mesh/neighbors`
- `/ugr/replay/check`
- `/governance/change-ledger`
- `/governance/replay-state`
- `/governance/replay-change/:entryId`
- `/governance/diff`
- `/governance/impact/:entryId`
- `/upl/modules`
- `/crf/artifacts`

## 9. Conformance

An implementation claiming conformance MUST:

- implement the UGR data model
- implement UGQL parsing and execution
- implement UPL package modeling
- implement CRF validation and replay surfaces
- implement the Constitutional Change Ledger query and replay APIs
- expose deterministic test coverage for the above
