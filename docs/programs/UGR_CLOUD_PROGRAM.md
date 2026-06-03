# Unified Governed Runtime (UGR) Cloud Program

Status: **Operator console v1** — UGR + Cloud Forge advisory readouts on `/operator` and Jarvis side panel.

Authority: `META_ARCHITECT_LAWBOOK.md`, `docs/contracts/UGR_RUNTIME_CONTRACT.md`, `docs/contracts/UGR_CLOUD_MESH_CONTRACT.md`.

## Purpose

Scale the existing AAIS governed runtime (Cognitive Bridge + Jarvis authority +
Immune Protocol + Collective Pattern Ledger) into a cloud-ready cognitive organism
without replacing constitutional law.

The novelty is the **runtime**, not a bigger model.

## What Already Exists (proven)

| Capability | Repo surface |
|---|---|
| Lawful ingress | `src/cognitive_bridge.py`, `docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md` |
| Live bridge invariant gate | `InvariantEngine.validate_bridge_packet` in `src/invariant_engine.py` |
| Immune layer | `src/immune_protocol.py`, `src/immune_system.py` |
| Unified pattern ledger v0.5 | `src/ugr/unified_pattern_ledger.py`, `docs/contracts/PATTERN_LEDGER_SCHEMA_V0_5.md` |
| UGR orchestration | `src/ugr/unified_runtime.py`, `POST /api/ugr/deliberate` |
| Cloud mesh (Phase 2) | `src/ugr/cloud/`, `deploy/ugr/`, `make ugr-cloud-gate` |
| Governed ingestion (Phase 3) | `src/ugr/ingestion/`, `POST /api/ugr/ingest`, `make ugr-ingestion-gate` |
| Platform scale (Phase 4) | `src/ugr/platform/`, `POST /api/ugr/platform/cicd/evaluate`, `make ugr-platform-gate` |
| Graph index v1 | `src/ugr/graph_index/`, `UGR_GRAPH_ENABLED=1`, `make ugr-graph-index-gate` |
| Governed LLM seam | `src/aais_governed_llm_module.py` (proposal-only) |
| Governed LLM lane v1 | `src/ugr/llm_lane.py`, wired via `run_llm_lane` |
| Cloud Forge rail hook | `src/ugr/cloud_forge_bridge.py`, `rail_decision` on UGR traces |
| Embryo v0 gateway | `src/ugr/embryo/`, `/api/ugr/v0/*`, `make ugr-embryo-gate` |
| Embryo v1 causal graph | `src/ugr/causal_graph/`, `/api/ugr/v1/*`, `make ugr-causal-graph-gate` |
| Trust bundle organ | `src/ugr/trust_bundle/`, `make ugr-trust-bundle-gate` |
| Operator console | `src/ugr/operator_console/`, `/operator`, `make ugr-operator-console-gate` |
| Substrate orchestration | Forge platform gate (`make forge-platform-gate`) |
| OS host | Wolf CoG / cogos runtime |

## Stack naming (URG vs AAIS)

| Layer | Role |
|-------|------|
| **AAIS** | Governed cognitive runtime — per-turn bridge, lanes, operator shell |
| **URG** | Unified runtime governance — lawbook + switchboard for many AAIS instances and LLM providers (**not a model**) |

Doctrine: [URG_STACK_DOCTRINE.md](../contracts/URG_STACK_DOCTRINE.md)

## Program Phases

### Mission v1 — Governed super-router demo (current slice)

**Goal:** Prove mission-level governance: one mission, three provider organs, cost + risk + region constraints, fully ledgered.

Deliverables:

- [x] Stack doctrine + cloud invariant lift ([URG_STACK_DOCTRINE.md](../contracts/URG_STACK_DOCTRINE.md), [URG_CLOUD_INVARIANTS.md](../contracts/URG_CLOUD_INVARIANTS.md))
- [x] Provider organ registry \(O_i = (I,E,F,K)\) — `deploy/ugr/provider-organs.json`, `src/ugr/mission/provider_organ.py`
- [x] Ingress law — `src/ugr/mission/ingress.py`
- [x] Mission runtime — `src/ugr/mission/mission_runtime.py`, `POST /api/ugr/mission/run`
- [x] Demo config — `deploy/ugr/mission-demo.json`, `tools/proof/run_ugr_mission_demo.py`
- [x] Gate: `make ugr-mission-gate`

Acceptance:

- Three steps route to `local`, `openrouter`, `openai` organs (proposal-only)
- `missions.jsonl` records `action_id` chain with `prior_action_id`
- Wrong region or cost budget blocks mission with `status: blocked`

### Mission v1.2 — AAIS bridge, auto-assign, HMAC receipt

**Goal:** GCM drives real AAIS work per step; organs auto-matched; operator-bound receipt MAC.

Deliverables:

- [x] `src/ugr/mission/aais_step_bridge.py` — `llm_bridge` (default) + `full_deliberate`
- [x] `src/ugr/mission/organ_matcher.py` — tier/cost/region auto-assign
- [x] `src/ugr/mission/receipt_signing.py` — HMAC + `verify_mission_receipt`
- [x] `deploy/ugr/mission-demo-auto.json`
- [x] Contract [URG_MISSION_RECEIPT_SIGNING.md](../contracts/URG_MISSION_RECEIPT_SIGNING.md)

Acceptance:

- Default mission steps include `aais_deliberation.bridge` with ALLOW/DEGRADE
- Auto demo assigns three providers without explicit `organ_id`
- `mission_receipt.receipt_mac` when `URG_OPERATOR_RECEIPT_KEY` set

### Mission v1.3 — MissionReceipt schema

**Goal:** Formal forensic receipt with goal_hash, Merkle ledger_root, dual operator/URG signatures, UUID mission_id.

Deliverables:

- [x] `docs/contracts/URG_MISSION_RECEIPT_SCHEMA.md`, `schemas/urg_mission_receipt.v1.json`
- [x] `src/ugr/mission/mission_receipt.py`, `src/ugr/mission/ledger_merkle.py`
- [x] Dual signing: `URG_RECEIPT_SIGNING_KEY` + `URG_OPERATOR_RECEIPT_KEY`
- [x] API field `mission_receipt_schema` alongside legacy `mission_receipt`

### Phase 0 — Walking skeleton

**Goal:** Prove UGR + MLCA + convergence locally on one machine.

Deliverables:

- [x] Program plan (this document)
- [x] Runtime contract (`docs/contracts/UGR_RUNTIME_CONTRACT.md`)
- [x] `src/ugr/` package: pattern ledger store, lane manager, convergence engine, unified runtime
- [x] Tests (`tests/test_ugr_runtime.py`)
- [x] API surface (`POST /api/ugr/deliberate`)

### Phase 1 — Admit + unify (current)

**Goal:** Wire invariant engine into live path; unify ledger schema across AAIS + Wolf CoG.

Deliverables:

- [x] Admit `src/invariant_engine.py` to bridge deliberation/generation path
- [x] Unified pattern ledger schema v0.5 (`docs/contracts/PATTERN_LEDGER_SCHEMA_V0_5.md`)
- [x] Unified ledger implementation + detachment guard integration
- [x] Wolf CoG adapter (`normalize_cogos_pattern_record`)
- [x] Blueprint admission entries for invariant engine + UGR

Acceptance:

- Deliberation/generation packets include `bridge_invariant` in bridge trace when checked
- Detachment events write to unified ledger and legacy mirror path
- Tenant-scoped claim queries do not leak across tenants

### Phase 2 — Cloud factor (Forge lift)

**Goal:** Same behavior as separate services on one Forge-managed node cluster.

Deliverables:

- [x] Service decomposition (`src/ugr/cloud/services.py`)
- [x] Mesh config + HTTP clients (`deploy/ugr/mesh.local.json`)
- [x] Distributed runtime (`src/ugr/cloud/distributed_runtime.py`)
- [x] Docker compose single-node cluster (`deploy/ugr/docker-compose.yml`)
- [x] Forge pipeline (`wolf-cog-os/forge/pipelines/ugr-cloud-cluster.yaml`)
- [x] Gate: `make ugr-cloud-gate`

Acceptance:

- `UGR_DEPLOYMENT_MODE=distributed` matches monolith belief output
- All mesh services expose `/health`
- Manifest validator passes

### Phase 3 — Governed senses

**Goal:** Curated ingestion without raw internet touching models.

Deliverables:

- [x] Ingestion pipeline (`src/ugr/ingestion/`)
- [x] Curated sources config (`deploy/ugr/ingestion.sources.json`) — arXiv, GitHub releases, RSS
- [x] Invariant gate before ledger writes
- [x] Mesh ingestion service (:8095) + API (`POST /api/ugr/ingest`)
- [x] Gate: `make ugr-ingestion-gate`

Acceptance:

- Disabled sources fail closed
- Secret-like payloads quarantined
- Accepted claims include provenance and `source_lane=ingestion`
- Dry run produces proposals without ledger writes

### Phase 4 — Platform scale

**Goal:** Multi-tenant overlays, graph DB sharding, shadow runtime CI/CD for cognition.

Deliverables:

- [x] Tenant registry + overlay queries (`src/ugr/platform/tenant_registry.py`, `deploy/ugr/tenants.json`)
- [x] Graph shard router + sharded ledger (`src/ugr/platform/graph_shard.py`, `deploy/ugr/graph-shards.json`)
- [x] Shadow runtime comparison (`src/ugr/platform/shadow_runtime.py`)
- [x] Cognition CI/CD promotion pipeline (`src/ugr/platform/cognition_cicd.py`, `deploy/ugr/cognition-promotion.json`)
- [x] Platform mesh service (:8096) + API (`/api/ugr/platform/*`)
- [x] Gate: `make ugr-platform-gate`

Acceptance:

- Tenant overlay reads include global + tenant claims without cross-tenant leakage
- Claims route to shard-specific storage directories
- Shadow vs prod deliberation comparison emits promotion decision
- Manifest validator passes

### Embryo v0 — Cloud super-LLM gateway

**Goal:** One operable governed organism surface: orchestrator + model pool + ingestion + ledger + invariants + immune + API gateway.

Deliverables:

- [x] Model pool router (`src/ugr/embryo/model_pool.py`, `deploy/ugr/model-pool.json`)
- [x] Embryo gateway (`src/ugr/embryo/gateway.py`, mesh `:8099`)
- [x] Component health probes (`src/ugr/embryo/health.py`)
- [x] API gateway v0 (`/api/ugr/v0/*`)
- [x] Runtime attaches `model_pool` on every deliberation
- [x] Gate: `make ugr-embryo-gate`

Acceptance:

- Deliberation returns `embryo`, `rail_decision`, `model_pool`, lane bundle
- Model pool remains proposal-only with temperature 0
- Health endpoint reports all v0 components

### Embryo v1 — Persistent causal graph

**Goal:** Durable causal graph backend over canonical JSONL with provenance sync and region health overlays.

Deliverables:

- [x] Causal graph store (`src/ugr/causal_graph/`, `UGR_CAUSAL_GRAPH_ENABLED=1`)
- [x] Persistent edge log (`collective-pattern-ledger/causal-graph-v1/edges.jsonl`)
- [x] Provenance materialization from `provenance.jsonl` + claim `evidence_refs`
- [x] Region health registry (`deploy/ugr/regions.json`)
- [x] Embryo v1 gateway (`src/ugr/embryo/gateway_v1.py`, `/api/ugr/v1/*`)
- [x] Mesh services `causal_graph` (:8100), `embryo_v1_gateway` (:8101)
- [x] Gate: `make ugr-causal-graph-gate`

Acceptance:

- Causal walk returns edges from provenance and subject/object chains
- Region health snapshot resolves tenant overlays
- Rebuild syncs from JSONL without mutating canonical claim logs

### Trust bundle organ — Cross-profile proof

**Goal:** Doctrine XI proof pipeline for UGR — hashed proof bundles, cross-profile parity, CI matrix.

Deliverables:

- [x] Trust bundle organ (`src/ugr/trust_bundle/`)
- [x] Proof scenarios: mesh parity, causal rebuild, LLM execution smoke, manifest gate
- [x] CLI `tools/proof/run_ugr_trust_bundle.py`
- [x] Doctrine XI bundle `docs/trust_bundles/2026-05-28-ugr-trust-bundle-organ.md`
- [x] Gate: `make ugr-trust-bundle-gate`
- [x] CI matrix: `.github/workflows/ugr-trust-bundle-gate.yml` (ubuntu + windows)

Acceptance:

- machine-a vs machine-b payload hashes match for deterministic scenarios
- `proof_bundle.json` + `proof_bundle.sha256` emitted under `.runtime/trust-bundles/latest/`
- Cross-OS matrix evidence closes UGR-D5

### Operator console — UGR + Cloud Forge

**Goal:** Jarvis-style advisory console for rails, mesh health, trust bundle, and debt register.

Deliverables:

- [x] Operator snapshot (`src/ugr/operator_console/`)
- [x] API `GET /api/operator/console` + workbench key
- [x] UI `/operator` + Jarvis side panel card
- [x] Gate: `make ugr-operator-console-gate`

Acceptance:

- Readouts are `runtime_effect: readout_only`
- Trust bundle status reflects local `proof_bundle.json` when present
- Debt register lists UGR-D* and CF-D5 with claim labels

### Mission v1.5 — Cloud invariant layer

**Goal:** Super-cloud manifold \(I_{cloud}\), \(B_{cloud}\), fail-closed ledger, governance mutations, execution lifecycle.

Deliverables:

- [x] `src/ugr/invariants/` — `cloud_manifold.py`, `cloud_invariants.py`, `execution_safety.py`
- [x] Phase ledger: `mission_ingress`, `organ_assignment`, `provider_dispatch`, `provider_ack`
- [x] Execution modes: `DRY_RUN`, `SHADOW_EXECUTION`, `LIVE_EXECUTION`
- [x] `tests/test_ugr_cloud_invariants.py`, `tests/test_ugr_execution_policy.py`

### Mission v1.6 — URG Cloud Platform trilogy

**Goal:** Multi-tenant isolation, cost-aware routing, governed provider marketplace.

Deliverables:

- [x] [URG_CLOUD_PLATFORM.md](../URG_CLOUD_PLATFORM.md) — operator README for this release
- [x] `src/ugr/mission/tenant_manifold.py` — tenant gate, federation grants, partitioned stores
- [x] `src/ugr/mission/cost_routing.py` — `MissionBudget`, organ cost rank, `BUDGET_EXCEEDED`
- [x] `src/ugr/mission/marketplace.py`, `organ_trust.py` — admit/suspend/evict, trust-gated execution
- [x] `tests/test_ugr_tenant_isolation.py`, `test_ugr_cost_routing.py`, `test_ugr_marketplace.py`
- [x] Runtime **1.6**, GCM **1.6**

Acceptance:

- Two tenants: isolated ledger/receipt paths under `tenant:acme` / `tenant:contoso`
- Auto-assign minimizes estimated cost within `mission_budget` and tenant ceiling
- `URG_GOVERNANCE_APPLY=1` + `organ_admit` writes tenant overlay; low trust forces SHADOW for LIVE

Tag: **`urg-cloud-platform-v1.6`**

### Mission v1.7 — Bilateral federation grants + federated step

**Goal:** Tenant-A issues grant to Tenant-B; B accepts; mission from A routes a step through B manifold; both ledgers record it.

Deliverables:

- [x] `src/ugr/mission/federation_grants.py` — `FederationGrantStore` (issue/accept/revoke), runtime `urg/federation/grants.jsonl`
- [x] API `POST /api/ugr/federation/issue`, `POST /api/ugr/federation/accept`, `GET /api/ugr/federation/grants`
- [x] Merged accepted grants in `tenant_manifold`; federated step via `federation_peer_tenant` + `federation_grant_id`
- [x] Dual ledger phases `federation_step` / `federation_inbound`
- [x] `tests/test_ugr_federation_v17_acceptance.py` (no mocks on grant/ledger paths)
- [x] `deploy/ugr/mission-demo-federation-v17.json`

Acceptance:

- Real bilateral issue + accept; federated step writes acme + contoso `missions.jsonl`
- Pending grant blocks federated step

Tag: **`urg-cloud-platform-v1.7`**

### Mission v1.8 — Paired MissionReceipt

**Goal:** Home receipt binds peer ledger via `federation_digest` and resolvable `counterparty_receipt_ref`.

Deliverables:

- [x] Receipt schema **1.3** — `federation_digest`, `counterparty_receipt_ref`
- [x] `compute_federation_digest`, peer `federation_counterparty_stub` in receipt store
- [x] `tests/test_ugr_federation_v18_acceptance.py`

Acceptance:

- Recomputed digest from both ledger files matches receipt
- Counterparty ref resolves peer stub without `URG_RECEIPT_ADMIN`

Tag: **`urg-cloud-platform-v1.8`**

### Mission v1.9 — Cross-tenant governance + proof witness

**Goal:** Federation governance ops with dual ledger; trust bundle attests `federation_dual_ledger`.

Deliverables:

- [x] `federation_organ_admit` / `federation_organ_suspend` (requires `governance_cosign` grant)
- [x] Dual governance ledger rows; invariant family `cloud_federation_governance`
- [x] Trust scenario `federation_dual_ledger` (`URG_TRUST_BUNDLE_FEDERATION=1` optional in CI)
- [x] `tests/test_ugr_federation_v19_acceptance.py`

Acceptance:

- Governance mission with bilateral grant writes both tenant ledgers
- `TrustBundleOrgan` scenario `federation_dual_ledger` passes

Tag: **`urg-cloud-platform-v1.9`**

**Deferred post-v1.9:** Nova/Forge federated operator UI (display-only receipts); Platform Membrane IMXP HTTP (v45–46).

### Mission cloud-forge-v2 — Tenant binding + federated peer rail

**Goal:** Align URG `TenantSpec` with Cloud Forge `PerformanceProfile` / actor weights; federated steps schedule on peer tenant only.

Deliverables:

- [x] `TenantSpec.cloud_forge` + optional block in `deploy/ugr/tenants.json`
- [x] `build_forge_profile_from_tenant`, `resolve_tenant_manifold_for_forge`, `tenant_manifold` on `schedule_rail_for_ugr` (mission, deliberate, distributed)
- [x] Federated step peer rail + `steps[].cloud_forge`; `federation_digest` forge entries
- [x] `tests/test_ugr_cloud_forge_tenant_binding.py`, `tests/test_ugr_federation_forge_peer_rail.py`
- [x] `make ugr-mission-gate` includes forge binding tests

Acceptance:

- Acme vs contoso profiles differ (`wL_express_threshold` / biases)
- Bilateral federated mission: peer step carries `cloud_forge`; ingress `federation_context` has `mission_rail` / `peer_rail`

Tags: **`urg-cloud-forge-v2.0`** (tenant binding) · **`urg-cloud-forge-v2.1`** (federated peer rail)

### Mission cloud-forge-v2.2 — Forge–invariant closure

**Goal:** Federated peer rails lawful inside `B_cloud`; observed ledger + operator readout.

Deliverables:

- [x] `extend_boundary_for_federation_step` + `federation_boundary_extend` ledger phase
- [x] Invariant family **cloud_forge_rail** (wired in `evaluate_step`)
- [x] `tests/test_ugr_cloud_forge_observed.py`, operator snapshot `binding_version`
- [x] `CLOUD_FORGE_BINDING_VERSION` **3.0**

Tag: **`urg-cloud-forge-v2.2`**

### Mission cloud-platform-v3.0 — Invariants + governance + receipt 1.4

**Goal:** Platform contract generation without per-step Forge everywhere or Forge federation API.

Deliverables:

- [x] Invariant families **9–11** (`cloud_forge_rail`, `cloud_federation_policy`, `cloud_observed_promotion`)
- [x] `invariant_version` **3.0** on manifold ingress
- [x] Governance `mutation_op` **`cloud_forge_profile_update`** on `tenant_config`
- [x] Grant capabilities `forge_peer_rail`, `forge_profile_read`
- [x] Receipt schema **1.4**: `federation_forge_digest`, `observed_rail_ledger_ref`, `cloud_forge_binding_version`
- [x] Trust scenario **`forge_federation_boundary`** (`URG_TRUST_BUNDLE_FORGE=1`)
- [x] `tests/test_ugr_cloud_invariants_v2.py`, `tests/test_ugr_cloud_forge_governance.py`

Tags: **`urg-cloud-platform-v3.0`** · **`urg-cloud-forge-v3.0`**

## v1 Invariants (non-negotiable)

1. Single path of authority — all UGR traffic through Cognitive Bridge
2. Models never direct I/O — LLM lanes emit proposals only
3. Lane isolation — lanes cannot read each other's intermediate state
4. Convergence deterministic — same inputs → same merge
5. Provenance on accepted beliefs — every accepted claim cites lane + evidence refs
6. Fail closed — missing policy, invariants, or trace context blocks execution
7. No self-modification — UGR v1 cannot change its own code or policies

## v1 Metrics

| Metric | Target signal |
|---|---|
| Invariant violation rate | Low but non-zero (gate is working) |
| Lane agreement rate | Track per intent class |
| Convergence latency p95 | Baseline after Phase 0 |
| Quarantine volume | Spikes indicate drift or attack |
| Answer stability | Same question, stable domain → low variance unless ledger changed |

## Debt register

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| UGR-D1 | Cloud output formats remain stubs (`forge-cloud-output-contract.md`) | medium | operator | open |
| UGR-D2 | Graph DB not chosen; JSONL ledger is Phase 0 only | medium | architect | **partial** — SQLite query projection selected (`UGR_GRAPH_QUERY_BACKEND=sqlite`); Neo4j reserved for scale |
| UGR-D3 | LLM lane uses bounded stub until governed provider wiring | low | runtime | **closed** — governed LLM lane v1 + execution commit (`UGR_LLM_EXECUTE=1`) |
| UGR-D4 | Wolf CoG + AAIS ledger unification incomplete | high | runtime | **partial** — cogos write-path bridge + mesh endpoints; daemon hook deferred to deploy |
| UGR-D5 | Cross-physical-machine / cross-OS trust bundle matrix | medium | operator | **partial** — `federation_dual_ledger` scenario + CI matrix; attach cross-OS artifact to close |

## Verification

```bash
make ugr-cloud-gate
make ugr-ingestion-gate
make ugr-platform-gate
make ugr-graph-index-gate
make ugr-embryo-gate
make ugr-causal-graph-gate
make ugr-llm-provider-gate
make ugr-cogos-write-path-gate
make ugr-graph-backend-gate
make ugr-trust-bundle-gate
make ugr-operator-console-gate
make ugr-mission-gate
py -3.12 -m pytest tests/test_ugr_tenant_isolation.py tests/test_ugr_cost_routing.py tests/test_ugr_marketplace.py tests/test_ugr_cloud_invariants.py tests/test_ugr_mission_demo.py tests/test_ugr_execution_policy.py tests/test_ugr_federation_v17_acceptance.py tests/test_ugr_federation_v18_acceptance.py tests/test_ugr_federation_v19_acceptance.py -q
py -3.12 -m pytest tests/test_ugr_runtime.py tests/test_unified_pattern_ledger.py tests/test_invariant_engine.py tests/test_ugr_cloud.py tests/test_ugr_ingestion.py tests/test_ugr_llm_lane.py tests/test_ugr_cloud_forge_bridge.py tests/test_ugr_graph_index.py tests/test_ugr_embryo.py tests/test_ugr_causal_graph.py tests/test_ugr_governed_llm_executor.py tests/test_ugr_cogos_pattern_bridge.py tests/test_ugr_graph_backend.py -q
```

Proof bundle: attach pytest output + sample `/api/ugr/deliberate` trace after Phase 0 acceptance.
