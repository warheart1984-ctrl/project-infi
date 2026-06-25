# RLS Gap Matrix

Maps Runtime Law Spine axioms and laws to modules, status, and conformance tests.

**Status:** `enforced` | `partial` | `doc_only` | `missing`

## Axioms

| Axiom | Module | Status | L1 test | L2 test | L3 test |
|-------|--------|--------|---------|---------|---------|
| A1 Law primacy | `src/ucr/binary_law_key.py`, `kernel_boot` | partial | Boot rejects invalid law key | Corridor rejects wrong LK | Law file change outside evolution corridor → reject |
| A2 Non-self-authorizing | `runtime_law_spine/envelope.py` | partial | — | Mutation without adjudication → reject | — |
| A3 No raw execution | `spine_pipeline`, `RuntimeLawSpineGate` | partial | Unsealed launcher → HALT or no external emit | Corridor executor only path | Quarantine blocks admission |
| A4 Measurement before trust | `kernel_boot.run_early_boot` | partial | `test_rls_conformance_l1` sealed boot | TS span guard + Python boot align | Boot manifest in proof artifact |
| A5 Receipt discipline | `runledger`, `distributed_ledger` | partial | Receipt on halt | Ledger row per corridor run | Anomaly receipt → quarantine |
| A6 Identity continuity | `distributed_ledger` merge | partial | Monotonic merge test | Fork flag in receipt | — |

## Seven laws

| Law | Module | Status | L1 test | L2 test | L3 test |
|-----|--------|--------|---------|---------|---------|
| Boundary (admission) | `ucr_attestation`, `CorridorLoader` | partial | `test_ucr_attestation` boot seal | `CorridorExecutor.admit` | Quarantine flag in registry |
| Boundary (adjudication) | `cog_act_commit`, `spine_pipeline` | partial | `substrate_ok=False` halts | Envelope adjudicate before commit | Invariant engine rejects |
| Non-copy | `project_infi_law`, trust root | partial | — | Ledger merge monotonicity | — |
| Speech | `spine_pipeline.wolf_check` | **enforced** (fail-closed) | Missing `substrate_ok` → deny | Generation gate + sealed check | — |
| Capability | `runtime_law_spine/envelope.py` | partial | Stub deny missing capability | `test_rls_conformance_l2` | — |
| Measurement/receipt | `runledger`, `tri-core-protocol` | partial | Boot receipt in gate | RunStore per corridor | Proof stage2 attestation |
| Mutation | `ucr-runtime` patches, envelope | partial | — | propose → adjudicate → commit | Non-evolution corridor cannot mutate law |
| Delegation | `runtime_law_spine/contracts/delegate_attestation.json` | partial | Schema exists | Child caps ⊆ parent | — |

## Immune runtime (L3 only)

| Capability | Module | Status | Test |
|------------|--------|--------|------|
| Anomaly detection | `aaes-governance` fault journal + `runtime_law_spine/immune.py` | partial | `test_rls_conformance_l3` fault threshold |
| Auto-quarantine | `corridor_loader` quarantine set | partial | Quarantined corridor → admission denied |
| Law evolution corridor | `RLS_LAW_EVOLUTION_CORRIDOR_ID` | partial | Wrong corridor for law patch → reject |

## Exit criteria by level

- **L1:** Gap matrix shows Speech + boot path `enforced` or `partial` with passing L1 tests; no live entry without gate.
- **L2:** Boundary, Capability, Mutation, Delegation not `missing`; L2 tests green.
- **L3:** Immune row not `missing`; L3 tests green; `docs/proof/bumblebee-forge/stage2_attested_plan.json` updated.
