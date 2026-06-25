# Runtime Law Spine (RLS) — Engineering Contract

**Engineering name:** Runtime Law Spine (`RuntimeLawSpineLayer`)  
**Mythic (docs only):** Law envelope between invariant engine and cognitive OS  
**Contract version:** `RLS_CONTRACT_VERSION` = 1.0.0

## Purpose

The Runtime Law Spine is the **law envelope** between the invariant engine and the cognitive operating system. It enforces that no action, mutation, or external expression occurs outside measured boot, corridor admission, and adjudication under canonical law.

## Disambiguation: RLS-01 vs Runtime Law Spine

| Term | Meaning | Location |
|------|---------|----------|
| **Runtime Law Spine (RLS)** | Measured boot, trust root, corridor law envelope, conformance L1–L3 | This document, `runtime_law_spine/` |
| **RLS-01** | Redundant pipeline layer removal (Story Forge) | `docs/rebuild/story_forge_pipeline_stub.md` |

These are unrelated. Do not use RLS-01 to refer to Runtime Law Spine.

## Axioms (constitutional)

| ID | Statement |
|----|-----------|
| A1 | **Law primacy** — Law precedes code; runtime cannot override sealed law spine |
| A2 | **Non-self-authorizing code** — Code cannot grant itself capabilities or mutate law |
| A3 | **No raw execution** — External effects require adjudicated corridor path |
| A4 | **Measurement before trust** — Trust root is sealed only after measured boot |
| A5 | **Receipt discipline** — Material state changes produce append-only receipts |
| A6 | **Identity continuity** — Fork without ledger continuity yields new identity scope |

## Seven canonical laws

| Law | Admission | Adjudication | L3 immune extension |
|-----|-----------|--------------|---------------------|
| **Boundary** | Identity + attestation at corridor gate | `cog_act_commit` / spine pipeline stages | Quarantine on boundary breach |
| **Non-copy** | Trust root lineage | Fork detection via ledger monotonicity | — |
| **Speech** | `substrate_ok` + sealed root | `wolf_check`, generation gate | Block external expression when unsealed |
| **Capability** | Capability vector in attestation | Action ⊆ granted capabilities | Revoke on violation |
| **Measurement / receipt** | Boot manifest hash | Ledger append per corridor run | Anomaly → quarantine |
| **Mutation** | Propose-only patches | Adjudicate then commit | Law evolution corridor only |
| **Delegation** | Parent attestation | Child caps ⊆ parent caps | — |

## Task spec (Jon Safety Net)

| Field | Content |
|-------|---------|
| **Inputs** | `UCR_CORRIDOR_REGISTRY`, `UCR_LAW_SPINE`, `UCR_KERNEL_IMAGE`; corridor attestations; optional `RLS_STRICT`, `RLS_CONFORMANCE_LEVEL` |
| **Outputs** | `EarlyBootResult`; sealed `TrustRoot`; corridor receipts; `conformance_level` 1 \| 2 \| 3 |
| **Constraints** | Law primacy; no raw execution; non-self-authorizing code; fail-closed when `RLS_STRICT=true` (default) |
| **Failure modes** | `BootResult.HALT`; `CorridorLoaderError`; quarantine; law inconsistency freeze; `substrate_ok=false` blocks external expression |

## Conformance levels

| Level | Requirements |
|-------|----------------|
| **L1** | Measured boot wired at entry; receipts stub; `wolf_check` fail-closed; no external expression without sealed root |
| **L2** | Full boundary loop: admission → adjudication → commit; capability + delegation law |
| **L3** | Anomaly hooks, auto-quarantine, governed law-evolution corridor only |

## Cross-links

- [TRUST_ROOT_SPEC.md](./TRUST_ROOT_SPEC.md)
- [RUNTIME_INITIALIZATION_CONTRACT.md](../governance/RUNTIME_INITIALIZATION_CONTRACT.md)
- [CUOS_FOUNDATION_LAWS.md](./CUOS_FOUNDATION_LAWS.md)
- [RLS_GAP_MATRIX.md](./RLS_GAP_MATRIX.md)
- `governance/agent_change_manifests/2026-06-18-ucr-trust-root-measurement-chain.v1.json`

## Environment

| Variable | Description |
|----------|-------------|
| `UCR_CORRIDOR_REGISTRY` | Path to corridor registry directory |
| `UCR_LAW_SPINE` | Law spine binary key (integer) |
| `UCR_KERNEL_IMAGE` | Kernel image path for measurement |
| `RLS_STRICT` | `true` (default): halt on boot failure; `false`: degraded dev mode |
| `RLS_CONFORMANCE_LEVEL` | Target level `1`, `2`, or `3` (assertion in tests) |
| `RLS_LAW_EVOLUTION_CORRIDOR_ID` | Sole corridor allowed to mutate law spine (L3) |

## Integration entry points

- `aais/launcher.py` — `RuntimeLawSpineGate.require_sealed()` before serving
- `operator_kernel/main.py` — same gate at process start
- `src/cog_runtime/formal/spine_pipeline.py` — `wolf_check` fail-closed
- `runtime_law_spine/` — standalone package facade over `src/ucr/`
