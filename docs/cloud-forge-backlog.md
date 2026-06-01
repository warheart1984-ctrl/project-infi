# Cloud Forge Backlog

Status: active canonical backlog for Cloud Forge governed accelerator (AAIS cognitive layer).

Authority: `docs/cloud-forge-governed-accelerator-program.md`, `docs/contracts/cloud-forge-rail-contract.md`.

**Not** Wolf-cog ISO Forge — see `docs/forge-backlog.md` for OS platform work.

Priority: **C0** (governance), **C1** (scheduler code), **C2** (observation), **C3** (caches), **C4** (cloud fabric).

## Phase 0 — Governance artifacts

| ID | Item | Status | Evidence |
|---|---|---|---|
| C0-1 | Program plan | **COMPLETE** | `docs/cloud-forge-governed-accelerator-program.md` |
| C0-2 | Rail contract | **COMPLETE** | `docs/contracts/cloud-forge-rail-contract.md` |
| C0-3 | Rail failsafe | **COMPLETE** | `docs/failsafe/cloud-forge-rail-failsafe.md` |
| C0-4 | Backlog (this file) | **COMPLETE** | `docs/cloud-forge-backlog.md` |
| C0-5 | AAIS blueprint cross-link | **COMPLETE** | `document/blueprints/PROJECT_BLUEPRINTS_MASTER.md` §1.6 |
| C0-6 | Contracts README entry | **COMPLETE** | `docs/contracts/README.md` |
| C0-7 | Phase 0 proof packet | **COMPLETE** | `docs/proof/cloud-forge/C0_PHASE0_PROOF.md` |

## Phase 1 — Rail scheduler library — **COMPLETE**

| ID | Item | Status | Verification |
|---|---|---|---|
| C1-1 | `src/cloud_forge/types.py` | **COMPLETE** | unittest |
| C1-2 | `src/cloud_forge/risk.py` | **COMPLETE** | unittest |
| C1-3 | `src/cloud_forge/rails.py` | **COMPLETE** | unittest |
| C1-4 | `src/cloud_forge/failsafe.py` | **COMPLETE** | unittest |
| C1-5 | `tests/test_cloud_forge_rails.py` | **COMPLETE** | 20 tests OK (py 3.12) |
| C1-6 | Pipeline `cloud_forge_context` hook | **COMPLETE** | `build_governed_turn_pipeline` |
| C1-7 | Proof bundle C1 | **COMPLETE** | `docs/proof/cloud-forge/C1_RAIL_SCHEDULER_PROOF.md` |

## Phase 2 — Observation + Pattern Ledger — **COMPLETE**

| ID | Item | Status |
|---|---|---|
| C2-1 | `rail-decisions.jsonl` adapter | **COMPLETE** — `src/cloud_forge/ledger.py` |
| C2-2 | Ledger promotion stub | **COMPLETE** — `src/cloud_forge/promotion.py` |
| C2-3 | EXPRESS template `forge/voss/os_architecture` | **COMPLETE** — `src/cloud_forge/templates.py` |
| C2-4 | Jarvis operator rail readout | **COMPLETE** — `readout.py` + `jarvis_modular.py` |
| C2-5 | Integration `schedule_request_observed` | **COMPLETE** — `integration.py` |
| C2-6 | Proof packet | **COMPLETE** — `docs/proof/cloud-forge/C2_OBSERVATION_PROOF.md` |

## Phase 3 — Law-scoped caches — **COMPLETE**

| ID | Item | Status |
|---|---|---|
| C3-1 | L0 tenant+law tool cache | **COMPLETE** — `cache.py`, `cache_bridge.py`, `app/tools.py` |
| C3-2 | L1 answer cache KV | **COMPLETE** — `l1_get` / `l1_set` |
| C3-3 | L2 pattern cache | **COMPLETE** — `l2_get` / `l2_set` |
| C3-4 | Integration resolve + persist | **COMPLETE** — `integration.py` |
| C3-5 | Proof packet | **COMPLETE** — `docs/proof/cloud-forge/C3_CACHE_PROOF.md` |

## Phase 4 — Cloud locality — **COMPLETE**

| ID | Item | Status |
|---|---|---|
| C4-1 | Domain slice layout | **COMPLETE** — `docs/cloud-forge-domain-slice-layout.md`, `configs/cloud-forge/domain-slices.json` |
| C4-2 | Priority mapping wL/wT/wI → K8s class | **COMPLETE** — `map_governance_to_priority()` |
| C4-3 | Session prewarm law + strategy | **COMPLETE** — `SessionPrewarmStore` |
| C4-4 | Background tempering dry-run | **COMPLETE** — `src/cloud_forge/tempering.py`, job doc |
| C4-5 | Proof packet | **COMPLETE** — `docs/proof/cloud-forge/C4_LOCALITY_PROOF.md` |

## Debt register

| ID | Gap | Severity | Status |
|---|---|---|---|
| CF-D1 | Rail contract | High | **CLOSED** (C0-2) |
| CF-D2 | Rail scheduler implementation | High | **CLOSED** (C1) |
| CF-D3 | Pattern Ledger wiring | Medium | **CLOSED** (C2) |
| CF-D4 | Cloud co-location / K8s | Low | **CLOSED** (C4 spec + resolver) |
| CF-D5 | Cross-machine latency benchmarks | Medium | OPEN → post C1 |

## Decisions (recorded)

| # | Decision | Value |
|---|---|---|
| D1 | Backlog file | Separate `docs/cloud-forge-backlog.md` |
| D2 | Phase 1 integration | Pipeline metadata first |
| D3 | Ledger storage | `docs/proof/cloud-forge/rail-decisions.jsonl` |
| D4 | First EXPRESS domain | `forge/voss/os_architecture` |
