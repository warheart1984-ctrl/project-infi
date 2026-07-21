---
title: ULX Language Registry
description: Canonical registry of the named language, DSL, and adjacent surfaces represented under ULX.
---

# ULX Language Registry

The ULX governance layer now exposes a canonical registry for the named language, DSL, and adjacent surfaces already documented in this repository.
It is exported from `@aaes-os/ulx-governance` and mirrors the surfaces the ULX cockpit is expected to reason over.

UL is included here as the first-class verb-language surface used to express actions before ISL normalizes them into governed intent.

## Registry surfaces

| Name | Kind | Status | ULX role |
| --- | --- | --- | --- |
| UL | Verb language | Live | Live verb-language runtime for imperative action phrasing before intent is normalized by ISL |
| ULX | Source language | Live | Canonical source and bytecode format for constitutional execution |
| CSL | Constitutional layer | Live | Live constitutional schema layer for governed artifact schemas and evolution contracts |
| ISL | Constitutional layer | Live | Intent layer for governed requests and authority bindings |
| CIC | Constitutional layer | Live | Live inference layer for deterministic constitutional reasoning and semantic graphs |
| CCC | Constitutional layer | Live | Live continuity layer for replay contracts, lineage invariants, and time-bound governance |
| COE | Constitutional layer | Live | Live execution layer for constitutional routes, schedules, promotion workflows, and receipts |
| UGR | Runtime surface | Live | Unified general repository runtime for governed knowledge, queries, packages, and replay |
| UGQL | Query language | Live | Query facet of the live UGR runtime for selecting, tracing, and comparing knowledge |
| UPL | Package language | Live | Package facet of the live UGR runtime for worlds, constitutions, rules, agents, and arenas |
| CRF | Replay format | Live | Replay facet of the live UGR runtime for portable constitutional replay artifacts |
| Policy DSL | DSL | Live | Routing and guardrail rules for governed requests |
| Replay DSL | DSL | Live | Replay scenario language for deterministic recreation of governance runs |
| CML-2 | Spec family | Live | Live corpus family in the CML/Voss runtime surface for governed meaning constraints |
| CVM-1 | Spec family | Live | Live corpus family in the CML/Voss runtime surface for governed verification models |
| The Voss Binding | Spec family | Live | Live binding protocol between CML-2 meaning constraints and CVM-1 verification models |
| CodaDoc | Runtime surface | Live | Documentation catalog surface in the live Coda stack |
| CodaRuntime | Runtime surface | Live | Runtime facade that composes the Coda corpus with NovaCoda |
| NovaCoda | Runtime surface | Live | Runtime facade over the Nova substrate and typed socket client |
| GCRE-SYSMIN-001 | Runtime surface | Live | Registry surface for the GCRE family and related corpus members |

## How to use it

- Use the registry when you need the canonical inventory of named language surfaces under ULX.
- Use the registry output to drive cockpit menus, docs navigation, or validation filters without inventing a second source of truth.
- Treat `UL` as the live action-language entry point, `CSL` as the live governed schema layer, `ISL` as the governed intent layer, `CIC` as the live inference layer, `CCC` as the live replay/continuity layer, `COE` as the live execution layer, `CML-2 / CVM-1 / The Voss Binding` as the live CML/Voss corpus surface, `UGR / UGQL / UPL / CRF` as the governed knowledge and replay runtime, and `ULX` as the executable substrate.
- Treat any future `spec-only` entries as documented ULX-recognized surfaces, not as claims of a standalone production runtime.
