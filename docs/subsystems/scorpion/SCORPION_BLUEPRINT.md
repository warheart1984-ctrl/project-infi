# Scorpion Blueprint

## Canonical Definition

Project Scorpion is a governed OS-level anomaly extractor that detects,
classifies, and reconstructs bugs by enforcing behavioral invariants.

It is the runtime immune forensics layer for operating systems: syscall flows,
scheduler rhythms, memory lifecycle, file descriptors, IPC, privilege transitions,
entropy signatures, and timing deltas are classified under law, then extracted
into a sandboxed replay chamber with a deterministic reconstruction plan—not
reactive debugging or signature scanning.

## Purpose

Scorpion converts OS behavioral traces into bounded anomaly claims, governed
extraction, and dry-run invariant restoration plans.

## Authority And Precedence

Constitutional precedence is enforced:

Law > Blueprint > Contract > Implementation > Pipeline > Tool

Scorpion cannot bypass repository law.

## Five Components

| Component | Responsibility |
|-----------|----------------|
| **Sentinel** | Ingest normalized invariant-flow events (adapter: fixture, future kernel) |
| **Ledger** | Every anomaly becomes a claim (`asserted`, `proven`, `rejected`) |
| **Extractor** | Pull anomaly context into an isolated replay chamber |
| **Reconstructor** | Emit deterministic plan to restore invariant (dry-run only) |
| **Historian** | Append-only health-drift map over time |

## Core Responsibilities

- Ingest scoped behavioral traces without host mutation.
- Evaluate constitutional invariant catalog (`os_invariants.v1.json`).
- Classify drift as ledger claims with hash-linked evidence.
- Sandbox extraction and deterministic reconstruction plans.
- Record longitudinal drift in historian index.

## Non-Goals

- Not an antivirus or signature scanner.
- Not a kernel debugger UX.
- No hidden auto-apply or host mutation.
- No direct imports from `src/*` in core package (isolation parity with Forge contractor).

## System Model

### Inputs

- Trace fixture or Sentinel adapter stream (`scorpion.event.v1`).
- Invariant catalog and scope metadata.
- Governance context: laws, contracts, proof constraints.

### Outputs

- Scan report with drift candidates.
- Gate decision record (judge mode).
- Extraction bundle path (sandbox temp).
- Reconstruction plan artifact (dry-run).
- Proof report, snapshot, snapshot index, health drift index.

## Failsafe And Rollback

- Default mode is observe/scan only.
- `apply` mode is blocked in Stage 1–2.
- Kill switch: all mutating host paths denied at CLI contract level.
- Rollback token on every reconstruction plan for operator replay.

## Wolf CoG Integration (Stage 3)

Build-time substrate invariants in `wolf-cog-os/forge/governance/substrate-invariants.json`
gain `runtime_scorpion_invariants` cross-references. Post-build boot trace ingest
is optional and inactive until operator activation (see `CROSS_MACHINE_REPLAY.md`).

## Change-Of-Reality Requirement

Any behavior change in Scorpion must update:

1. Blueprint (this file)
2. Contract (`SCORPION_CLI_CONTRACT.md`)
3. Verification path (tests/commands/proof bundle)
4. Failsafe documentation

## Proof Policy

- Missing evidence means the claim is `asserted`.
- Contradictory evidence means the claim is `rejected`.
- Only traceable evidence may promote a claim to `proven`.
