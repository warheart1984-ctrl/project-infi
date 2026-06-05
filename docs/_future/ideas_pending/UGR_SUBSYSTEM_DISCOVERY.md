# UGR Subsystem Discovery

CISIV stage: **concept**

Status: pending — not yet integrated into active AAIS doc tree or backed by runtime.

## 1. Purpose

**Mythic:** UGR Subsystem Discovery — entry point that registers subsystem contributions, issues signed discovery receipts, and enables the rest of the Proof-of-Subsystem custody chain.

**Engineering:** `SubsystemDiscoveryEngine` — service for build/validate/issue of subsystem_discovery_receipts, query, and governance handoff.

## 2. Authority And Precedence

See UGR Operator Rewards Contract and sibling discovery contract for the full chain. Discovery is the first link; no downstream reward without a valid receipt.

## 3. Non-Goals

Does not decide governance status or issue rewards (defers to mission runtime + reward engine).

## 4. Core Contract

Schema: [schemas/ugr_subsystem_discovery.v1.json](./schemas/ugr_subsystem_discovery.v1.json)

## 5-7. Implementation

See src/ugr/discovery/ and the contracts. Receipt is the canonical artifact for later attribution.

## 8. Proof Posture (Concept)

| Claim | Label | Evidence |
|-------|-------|----------|
| Schema + receipt model | `asserted` | Schema + contract |
| Discovery service + receipt issuance | `proven` | src/ugr/discovery + tests |

Target proof packet: docs/proof/ugr/UGR_SUBSYSTEM_DISCOVERY_V1_PROOF.md

## 9. CISIV Path

Concept → ... → Verification via ugr gates and flagship audit.

## 10. Related

- UGR Operator Reward Engine, UGR Mission Runtime
- Genome: ugr_subsystem_discovery.genome.v1.json

## 11. Activation Order Notes

Foundational for rewards batch; activate early in UGR waves. Depends on platform tenant and graph for multi-tenant discovery.
