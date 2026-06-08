# Multi-Organism Governance Membrane Contract (Beyond the Body)

Status: **active contract** (Mythic Stage 14 / Anatomical Layer 16 / Release 44)

Not session memory_governance_membrane replacement, not platform IMXP fork, not UGR execution gates.

## Purpose

Governed **permeability policies** unifying what may cross organism boundaries (memory cues, exchange envelopes, mesh handoffs, ledger federation rows) under adopted ecosystem charters — admitted to Memory Board membrane overlay (slot_10) only after operator promotion and Jarvis authorization.

## Membrane policy envelope

Schema: [schemas/operator_membrane_policy.v1.json](../../schemas/operator_membrane_policy.v1.json)

## Governance membrane coordination classes

| Class | Meaning |
|-------|---------|
| MGM-0 | Observe membrane drift (leaks, unsigned exchange, charter violations) |
| MGM-1 | Membrane policy proposal |
| MGM-2 | Adopted policy (operator + Jarvis slot_10 overlay) |
| MGM-3 | Membrane-governed admission elevation at ingress (never bypass UGR/OTEM/mesh execution) |

## Rules

1. Nova may interpret permeability context; Jarvis must authorize slot_10 admission ([jarvis_membrane_authority.py](../../src/jarvis_membrane_authority.py))
2. MGM-3 is admission-only; execution still through OTEM/mesh/UGR gates
3. Platform IMXP implementation is wrapped, not forked ([INTER_MEMBRANE_EXCHANGE_PROTOCOL.md](../subsystems/platform/INTER_MEMBRANE_EXCHANGE_PROTOCOL.md))
4. memory_governance_membrane consults MGM-2 before federated board attach

## APIs

- `GET /api/operator/governance-membrane`
- `POST /api/operator/governance-membrane/observe`
- `GET /api/operator/governance-membrane/policies`
- `POST /api/operator/governance-membrane/policies/adopt`
