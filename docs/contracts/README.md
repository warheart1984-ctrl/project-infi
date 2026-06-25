# AAIS Contracts

This folder contains the active laws, doctrines, protocols, and contracts that
govern AAIS behavior.

Operating-governance companions (agent safety, evidence receipts, init contract): [docs/governance/README.md](../governance/README.md).

## What Lives Here

- document protocol and documentation law
- dependency gate and deterministic lock policy
- module governance and phase rules
- cognitive bridge ingress law
- unified governed runtime (UGR) and MLCA contract
- unified pattern ledger schema v0.5
- UGR cloud mesh contract (Phase 2 Forge lift)
- UGR governed ingestion contract (Phase 3 senses)
- embedded ARIS runtime and non-copy law
- immune protocol and collective pattern ledger law
- swarm coordination law
- Jarvis protocol and reasoning contracts
- AAIS reasoning profile and CCS/DZI-1 continuity-evidence handshake (`AAIS_REASONING_PROFILE.md`)
- CCS core object schema and AAIS/CSLEIS adapter contract (`CCS_CORE_SCHEMA.md`, `../../schemas/ccs_core_objects.v1.json`)
- Jarvis LoRA training contract (bounded adapter fine-tuning)
- reasoning exchange protocol for external packet admission
- memory doctrine
- tracing protocol and proof-layer contract
- AAES-OS v1.0 governed span formal spec (`AAES_OS_V1_FORMAL_SPEC.md`)
- AAES-OS language-agnostic interface contract (`AAES_OS_INTERFACE_V1.md`) — cognitive pipeline TS/Rust signatures; **coding agent starter:** `archive/cold-storage/reference/aaes-os-starter/` (live: `aaes-os/`)
- AAES-OS trace-layer stubs (`archive/cold-storage/reference/aaes_os_v1/`) — RFC `TraceEvent` / `TraceBus` TypeScript and Rust
- AAES-OS architecture coding-agent contract (`AAES_OS_ARCHITECTURE_V1.md`)
- ARIS runtime contract and non-copy clause
- ARIS standalone service admission spec (Phase 4 unblock path)
- seam law and seam checklist
- seam closure records
- evolve, forge, and capability contracts
- cloud forge rail scheduler (`cloud-forge-rail-contract.md`)
- subsystem summoner pattern for CISIV concept admission (`AAIS_SSP_PROTOCOL.md`)
- SSP Alt-4 promotion, retirement, mutation, and subsystem genome (`AAIS_SSP_PROMOTION_PROTOCOL.md`, `AAIS_SUBSYSTEM_RETIREMENT_PROTOCOL.md`, `AAIS_SUBSYSTEM_MUTATION_PATH.md`, `AAIS_SUBSYSTEM_GENOME.md`)

## Canonical Rule

These docs are active law surfaces.
They are not archive material.

If a contract doc conflicts with runtime code, runtime code still wins, but the
conflict should be treated as drift that needs correction.
