# AAIS Operating Governance

Status: **active companion layer**

Canonical supreme law remains at repo root: [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md).

This folder holds **human-readable operating contracts** that translate constitutional law into inspectable engineering practice. When anything here conflicts with the lawbook, the lawbook wins.

## Precedence (unchanged)

Law → Blueprint → Contract → Implementation → Pipeline → Tool

CI and pipelines **enforce**; they do **not** authorize. Passing a gate does not override constitutional requirements ([Doctrine VII](../../META_ARCHITECT_LAWBOOK.md)).

## Documents

| Document | Engineering role | Canonical law anchor |
|----------|------------------|----------------------|
| [AGENT_SAFETY_DOCTRINE.md](./AGENT_SAFETY_DOCTRINE.md) | Coding-agent boundary companion | MA-14 |
| [EVIDENCE_RECEIPT_MODEL.md](./EVIDENCE_RECEIPT_MODEL.md) | Five receipt classes for proof | Doctrine I, [REPO_PROOF_LAW.md](../../REPO_PROOF_LAW.md) |
| [COGNITIVE_KERNEL_BOUNDARY_MAP.md](./COGNITIVE_KERNEL_BOUNDARY_MAP.md) | Role separation map (no collapse) | Blueprint Layer 2, Nova Cortex |
| [RUNTIME_INITIALIZATION_CONTRACT.md](./RUNTIME_INITIALIZATION_CONTRACT.md) | Boot / genesis admission contract | MA-12, runtime law |
| [AAES_OS_V1_FORMAL_SPEC.md](../contracts/AAES_OS_V1_FORMAL_SPEC.md) | Governed span trace layer (AAES-OS mythic) | Contract § span primitive |
| [AAES_OS_ARCHITECTURE_V1.md](../contracts/AAES_OS_ARCHITECTURE_V1.md) | Cognitive pipeline + module contracts for coding agents | Companion to formal spec |

## Related surfaces (outside this folder)

- [HUMAN_AI_CO_COLLABORATION_CHARTER.md](../../HUMAN_AI_CO_COLLABORATION_CHARTER.md) — human–AI constitutional interface
- [document/law/REPO_LAWBOOK.md](../../document/law/REPO_LAWBOOK.md) — law index
- [docs/contracts/](../contracts/) — active contracts and protocols
- [governance/agent_change_manifests/](../../governance/agent_change_manifests/) — agent change manifests (JSON)

## When to update

Update these docs when you change:

- agent safety rules or manifest schema
- proof / trust bundle requirements
- cognitive ingress or kernel boundaries
- launcher or initialization admission paths

Pair doc changes with a Trust Bundle or Agent Safety manifest when touching governed surfaces (see [FORGE_WARDEN_COLLABORATION_ENFORCEMENT.md](../contracts/FORGE_WARDEN_COLLABORATION_ENFORCEMENT.md)).
