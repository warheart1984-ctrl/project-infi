# URG Cloud Platform (v1.9)

**Unified Governed Runtime** — governed composite missions across provider organs with cryptographic cloud invariants, multi-tenant isolation, cost-aware routing, governed marketplace, and bilateral federation.

Repository: [Project-Infinity1](https://github.com/warheart1984-ctrl/Project-Infinity1)  
Release tags: **`urg-cloud-platform-v1.9`** (latest federation) · [`v1.6`](https://github.com/warheart1984-ctrl/Project-Infinity1/releases/tag/urg-cloud-platform-v1.6) (trilogy baseline)

---

## What this is

URG is not a model. It is the **lawbook and switchboard** that routes missions through admitted provider organs under cloud invariants, execution policy, and signed MissionReceipts.

| Layer | Role |
|-------|------|
| **Cloud invariants (v1.5)** | Frozen \(I_{cloud}\), \(B_{cloud}\), ledger causality, governance mutations |
| **Execution lifecycle** | `execution_planned` → `execution_dispatched` → `execution_committed` |
| **Tenant isolation (v1.6)** | Partitioned ledger/receipts; tenant manifold; federation grants |
| **Cost routing (v1.6)** | `mission_budget` soft/hard ceilings; organ `cost_contract` |
| **Marketplace (v1.6)** | `organ_admit` / `suspend` / `evict`; trust-gated LIVE vs SHADOW |
| **Federation (v1.7–1.9)** | Bilateral grants; federated steps; paired receipts; cross-tenant governance |

Doctrine: [URG_STACK_DOCTRINE.md](contracts/URG_STACK_DOCTRINE.md) · Program: [UGR_CLOUD_PROGRAM.md](programs/UGR_CLOUD_PROGRAM.md)

---

## Quick start

```powershell
cd project-infi
pip install -r requirements.txt   # or your env setup

# Keys for signed receipts (demo)
$env:URG_OPERATOR_RECEIPT_KEY = "your-operator-key"
$env:URG_RECEIPT_SIGNING_KEY = "your-urg-key"
$env:AAIS_RUNTIME_DIR = ".runtime"

# Gate + tests
py -3.12 -m pytest tests/test_ugr_tenant_isolation.py tests/test_ugr_cost_routing.py `
  tests/test_ugr_marketplace.py tests/test_ugr_cloud_invariants.py `
  tests/test_ugr_mission_demo.py tests/test_ugr_execution_policy.py `
  tests/test_ugr_federation_v17_acceptance.py tests/test_ugr_federation_v18_acceptance.py `
  tests/test_ugr_federation_v19_acceptance.py -q
py -3.12 wolf-cog-os/scripts/validate-ugr-mission-manifest.py
py -3.12 tools/proof/run_ugr_mission_demo.py

# Optional live provider (requires API keys + UGR_LLM_EXECUTE=1)
# $env:UGR_LLM_EXECUTE = "1"
# $env:URG_EXECUTION_MODE = "SHADOW_EXECUTION"
# py -3.12 tools/proof/run_ugr_mission_demo.py --healthcheck
```

---

## Execution modes

| Mode | Provider calls | Downstream results | Receipt `shadow` |
|------|----------------|-------------------|------------------|
| `DRY_RUN` (default) | No (bridge plans; simulated ack) | Discarded | false |
| `SHADOW_EXECUTION` | Yes | Discarded | true |
| `LIVE_EXECUTION` | Yes | May flow | false |

| Environment variable | Purpose |
|---------------------|---------|
| `URG_EXECUTION_MODE` | `DRY_RUN` / `SHADOW_EXECUTION` / `LIVE_EXECUTION` |
| `URG_MISSION_KILL_SWITCH=1` | Reject new missions |
| `UGR_LLM_EXECUTE=1` | Legacy → `LIVE_EXECUTION` |
| `URG_GOVERNANCE_APPLY=1` | Write tenant organ overlay on governance ops |
| `URG_RECEIPT_ADMIN=1` | Cross-tenant receipt reads (ops only) |
| `UGR_CLOUD_FORGE_ENABLED` | `1` (default) — schedule Cloud Forge rail on deliberate/mission paths |
| `UGR_CLOUD_FORGE_OBSERVED` | `1` — observed scheduler + `rail-decisions.jsonl` ledger (tenant_id + trace_id) |
| `UGR_SUBSYSTEM_DISCOVERY_ENABLED` | `1` (default) — Proof-of-Subsystem discovery API |
| `UGR_DISCOVERY_SHADOW_ONLY` | `1` (default) — discovery receipts + catalog only; block `promote` writes |
| `UGR_OPERATOR_REWARDS_ENABLED` | `1` (default) — Proof-of-Subsystem operator incentives |
| `UGR_REWARDS_SHADOW_ONLY` | `1` (default) — validate rewards; no balance writes unless `URG_GOVERNANCE_APPLY=1` path clears shadow |
| `UGR_REWARDS_AUDIT_ONLY` | `0` (default) — compute reward preview without ledger append |
| `UGR_RAIL_CREDIT_SPEND_ENABLED` | `1` (default) — rail credit spend + Cloud Forge boost hook |

---

## Cloud Forge binding (v2.0–v2.1)

All URG → Cloud Forge traffic goes through `src/ugr/cloud_forge_bridge.py` (no separate Forge federation API).

| Phase | Behavior |
|-------|----------|
| **v2.0 tenant binding** | Optional `cloud_forge` block in `deploy/ugr/tenants.json`; `build_forge_profile_from_tenant()` maps `cost_ceiling` + biases to `PerformanceProfile`. Mission open and `POST /api/ugr/deliberate` pass `tenant_manifold` into `schedule_rail_for_ugr()`. Ingress carries `cloud_forge_tenant_digest` + `cloud_forge_binding_version: "2.0"`. |
| **v2.1 federated step** | Steps with `federation_peer_tenant` re-schedule on **peer** tenant profile; `step_outcomes[].cloud_forge` + `federation_digest` includes `mission_rail` / `peer_rail`. Mission-level `cloud_forge` remains **home** tenant. |

Contract cross-link: [cloud-forge-rail-contract.md](contracts/cloud-forge-rail-contract.md)

Gate: `make ugr-mission-gate` includes `test_ugr_cloud_forge_tenant_binding.py` and `test_ugr_federation_forge_peer_rail.py`.

Release tags: **`urg-cloud-forge-v2.0`** (tenant binding) · **`urg-cloud-forge-v2.1`** (federated peer rail) · **`urg-cloud-forge-v2.2`** (boundary + observed) · **`urg-cloud-platform-v3.0`** / **`urg-cloud-forge-v3.0`** (invariants 9–11, receipt 1.4, profile governance).

| v2.2 | Federated `B_cloud` extend, observed ledger tests, operator snapshot binding |
| v3.0 | Invariant families 9–11, `cloud_forge_profile_update`, receipt schema **1.4**, trust `forge_federation_boundary` |

---

## Multi-tenant layout

| Artifact | Path |
|----------|------|
| Tenant registry | `deploy/ugr/tenants.json` |
| Tenant organ overlay | `deploy/ugr/tenants/tenant-acme/provider-organs.json` |
| Mission ledger (per tenant) | `{AAIS_RUNTIME_DIR}/collective-pattern-ledger/tenants/{slug}/missions.jsonl` |
| Receipts (per tenant) | `{AAIS_RUNTIME_DIR}/urg/receipts/{slug}/receipts.jsonl` |
| Federation grants | `{AAIS_RUNTIME_DIR}/urg/federation/grants.jsonl` |

Receipt fetch: `GET /api/ugr/mission/receipt/<mission_id>?tenant_id=tenant:acme`

---

## API surfaces

| Endpoint | Description |
|----------|-------------|
| `POST /api/ugr/mission/run` | Run governed composite mission |
| `POST /api/ugr/mission/governance` | Governance mutation mission |
| `GET /api/ugr/mission/receipt/<id>?tenant_id=` | Tenant-scoped receipt |
| `GET /api/ugr/marketplace/organs?tenant_id=` | Public organ catalog |
| `POST /api/ugr/federation/issue` | Issue pending bilateral grant |
| `POST /api/ugr/federation/accept` | Grantee accepts grant |
| `GET /api/ugr/federation/grants?tenant_id=` | List grants for tenant |
| `POST /api/ugr/discover/subsystem` | Proof-of-Subsystem discovery (validate or bounded search) |
| `GET /api/ugr/discover/subsystem/<subsystem_id>?tenant_id=` | Subsystem discovery receipt by hash |
| `GET /api/ugr/discover/subsystems?tenant_id=` | Shadow catalog of discovered specs |
| `GET /api/ugr/rewards/operator/<id>?tenant_id=` | Operator reputation, rail credits, adoption multipliers |
| `GET /api/ugr/rewards/ledger?tenant_id=` | Reward event ledger |
| `POST /api/ugr/rewards/spend` | Spend rail credits for EXPRESS forge boost |

---

## Demo missions

| File | Purpose |
|------|---------|
| `deploy/ugr/mission-demo.json` | Three explicit organs |
| `deploy/ugr/mission-demo-auto.json` | Auto-assign by tier/cost |
| `deploy/ugr/mission-demo-live.json` | Single-step live (needs `UGR_LLM_EXECUTE=1`) |
| `deploy/ugr/mission-demo-healthcheck-embedding.json` | No-risk healthcheck (tiny, SAFE rail) |
| `deploy/ugr/mission-demo-federation-v17.json` | Bilateral federated step (after issue/accept) |

Federation proof: `py -3.12 tools/proof/run_ugr_mission_demo.py --federation-v17`

---

## Core modules

```
src/ugr/invariants/          # I_cloud, B_cloud, cloud_* checks
src/ugr/mission/
  mission_runtime.py         # GCM orchestration (v1.6)
  tenant_manifold.py         # Tenant gate + federation
  cost_routing.py            # MissionBudget, rank organs
  organ_matcher.py           # Auto-assign + cost rank
  execution_policy.py        # DRY / SHADOW / LIVE
  step_execution.py          # execution_committed lifecycle
  marketplace.py             # organ_admit / suspend / evict
  organ_trust.py             # Trust EMA + LIVE gate
  governance_mission.py      # Governance mutations
  federation_grants.py       # Bilateral grant store + digest (v1.7+)
```

---

## Production-credible receipt

A completed mission receipt (schema **1.3**) includes:

- `cloud_identity_hash`, `boundary_digest`, `invariant_version`
- `tenant_manifold_digest`, `tenant_normalized_id`
- `budget_digest`, `soft_ceil_breached` (when budget used)
- `federation_digest`, `counterparty_receipt_ref` (when federated steps ran)
- `ledger_root` (Merkle over all ledger rows including phase transitions)
- `execution_mode`, `shadow`
- Dual HMAC: `operator_sig`, `receipt_sig`

Phase ledger: `mission_ingress` → `organ_assignment` → `provider_dispatch` → `provider_ack`

---

## Verify locally

```powershell
make ugr-mission-gate
```

---

## License

Same as the parent repository: [Apache 2.0](../LICENSE).
