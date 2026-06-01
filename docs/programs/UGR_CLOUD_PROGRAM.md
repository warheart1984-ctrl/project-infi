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

## Program Phases

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
| UGR-D5 | Cross-physical-machine / cross-OS trust bundle matrix | medium | operator | **open** — CI workflow added; attach artifact evidence to close |

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
py -3.12 -m pytest tests/test_ugr_runtime.py tests/test_unified_pattern_ledger.py tests/test_invariant_engine.py tests/test_ugr_cloud.py tests/test_ugr_ingestion.py tests/test_ugr_llm_lane.py tests/test_ugr_cloud_forge_bridge.py tests/test_ugr_graph_index.py tests/test_ugr_embryo.py tests/test_ugr_causal_graph.py tests/test_ugr_governed_llm_executor.py tests/test_ugr_cogos_pattern_bridge.py tests/test_ugr_graph_backend.py -q
```

Proof bundle: attach pytest output + sample `/api/ugr/deliberate` trace after Phase 0 acceptance.
