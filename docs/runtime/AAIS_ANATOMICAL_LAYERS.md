# AAIS Anatomical Layers

Status: **active architecture map**

CISIV stage: **structure**

## Doctrine

AAIS is built body-before-brain. Each anatomical layer maps to concrete modules, registries, and API surfaces in `project-infi`. Mythic labels (Organ, Brainstem) appear in docs only; engineering identifiers follow [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md).

## Layer Map

| Layer | Mythic name | Engineering surface | Status |
|-------|-------------|---------------------|--------|
| 1 | Senses | MCP bridge, skill adapter, plug discovery | built |
| 2 | Memory | Operator ledger, run ledger, temporal replay, genomes | built |
| 3 | Muscles | Plug adapter runtime, native capability adapter, OTEM | built |
| 4 | Nervous system | Library registry, workflow catalog, Jarvis routing | built |
| 5 | Organs | Workflow family registry | partial |
| 6 | Brainstem | UL substrate, constitutional law, governance gates | built |
| 7 | Brain | Nova Cortex runtime, proposal-only workflow-family routing | wired bounded |

## 1. Senses

Observation and perception tools.

| Component | Path |
|-----------|------|
| Plug discovery | `src/plug_discovery.py` |
| MCP bridge | `src/mcp_bridge.py` |
| Skill adapter | `src/skill_adapter.py` |
| UGR governed senses | `docs/contracts/UGR_INGESTION_CONTRACT.md` |

## 2. Memory

Structured recall — not raw storage.

| Component | Path |
|-----------|------|
| Operator Decision Ledger | `src/api.py` `/api/operator/ledger/*` |
| Run ledger | `src/run_ledger.py` |
| Temporal replay | `src/temporal_replay/service.py` |
| Subsystem genomes | `governance/subsystem_genomes/` |
| Jarvis Memory Board | `src/jarvis_memory_board.py` |
| UL substrate envelopes | `src/aais_ul_substrate.py` |

## 3. Muscles

Execution engines that apply force.

| Component | Path |
|-----------|------|
| Plug adapter runtime | `src/plug_adapter_runtime.py` |
| Native capability adapter | `src/native_capability_adapter.py` |
| Capability service bridge | `src/capability_service_bridge.py` |
| OTEM bounded execution | `src/otem_runtime.py` |
| Workflow shell runtime | `app/workflow_runtime.py` |

## 4. Nervous System

Routing layer connecting senses to muscles.

| Component | Path |
|-----------|------|
| Plug adapter runtime | `src/plug_adapter_runtime.py` |
| Library registry | `src/library_registry.py` + `governance/aais_library_registry.v1.json` |
| Workflow plugin catalog | `src/workflow_plugin_catalog.py` |
| Capability map | `docs/runtime/AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md` |
| Workflow ability catalog | `docs/runtime/AAIS_WORKFLOW_ABILITY_CATALOG.md` |
| Jarvis routing | `src/api.py`, `src/jarvis_operator.py` |

## 5. Organs

Workflow-family composition — specialized systems that combine tools into functions.

**Distinction:** The 162+ `*_organ.py` subsystem modules are governance infrastructure (brainstem-tier). Workflow-family organs are a separate layer that groups libraries, bundles, and abilities into domain functions.

| Family | Mythic label | family_id | Registry gene |
|--------|--------------|-----------|---------------|
| Knowledge Work | Knowledge Organ | `knowledge_work` | `workflow_family_knowledge` |
| Business Workflows | Business Organ | `business_workflows` | `workflow_family_business` |
| Creative Workflows | Creative Organ | `creative_workflows` | `workflow_family_creative` |
| Data Workflows | Data Organ | `data_workflows` | `workflow_family_data` |
| Operational Workflows | Ops Organ | `operational_workflows` | `workflow_family_ops` |
| Personal Workflows | Personal Organ | `personal_workflows` | `workflow_family_personal` |

| Component | Path |
|-----------|------|
| Family registry schema | `schemas/aais_workflow_family.v1.json` |
| Family registry | `governance/workflow_family_registry.v1.json` |
| Registry engine | `src/workflow_family_registry.py` |
| Chain executor | `src/workflow_chain_executor.py` |
| Operator API | `GET /api/operator/organs` |
| Operator UI | `frontend/src/pages/OperatorPlugins.jsx` (Organs tab) |

## 6. Brainstem

Governance substrate — authority, receipts, boundaries.

| Component | Path |
|-----------|------|
| UL substrate | `src/aais_ul_substrate.py` |
| Constitutional lawbook | `lawbook/META_ARCHITECT_LAWBOOK.md` |
| Governance gates | `Makefile` targets |
| Phase gates | `src/phase_gate.py` |
| Operator approvals | OTEM checkpoints, explicit approve |

## 7. Brain

Nova Cortex runtime wired as the bounded Brain layer.

**Boundary:** Nova Cortex may interpret, compose cognition, and recommend workflow-family routing.
Jarvis, OTEM, and the operator still authorize execution.

| Component | Path |
|-----------|------|
| Brain-layer adapter | `src/brain_layer_runtime.py` |
| Brain proposal validator | `src/brain_proposal_validator.py` |
| Proposal contract | `docs/contracts/BRAIN_PROPOSAL_CONTRACT.md` |
| Proposal schema | `schemas/brain_proposal.v1.json` |
| Nova Cortex runtime | `src/cog_runtime/` |
| Cortex constitution | `docs/runtime/NOVA_CORTEX.md` |
| Cortex family manifest | `docs/runtime/cognitive_runtime_family.v1.json` |
| Chain scorer | `src/brain_chain_scorer.py` |
| Brain session store | `src/brain_session_store.py` |
| Brain deliberation validator | `src/brain_deliberation_validator.py` |
| Brain deliberation adapter | `src/brain_deliberation_runtime.py` |
| Deliberation contract | `docs/contracts/BRAIN_DELIBERATION_CONTRACT.md` |
| Operator API | `GET /api/operator/brain`, `POST /api/operator/brain/propose`, `POST /api/operator/brain/deliberate`, `GET/POST /api/operator/brain/sessions` |
| Operator UI | `frontend/src/pages/OperatorBrainSessions.jsx` |
| Governance gates | `make brain-proposal-gate`, `make brain-layer-gate` |

Still deferred:

- autonomous self-routing
- multi-agent delegation graphs
- self-sequencing execution without explicit Jarvis/OTEM/operator authority

## API Surfaces

| Route | Layer | Purpose |
|-------|-------|---------|
| `GET /api/operator/plugins` | Nervous system | Plug registry snapshot |
| `GET /api/operator/plugins/workflows` | Nervous system | Workflow bundle catalog |
| `GET /api/operator/plugins/libraries` | Nervous system | Library family catalog |
| `GET /api/operator/organs` | Organs | Workflow-family organ catalog |
| `GET /api/operator/organs/<family_id>` | Organs | Single family detail |
| `GET /api/operator/brain` | Brain | Nova Cortex bounded Brain-layer status |
| `POST /api/operator/brain/propose` | Brain | Validated `brain_proposal.v1` envelope |
| `GET /api/operator/brain/sessions` | Brain | List operator brain sessions |
| `POST /api/operator/brain/sessions` | Brain | Create session + proposal |
| `POST /api/operator/brain/sessions/<id>/decide` | Brain | Accept/reject/defer with ledger receipt |
| `POST /api/operator/brain/deliberate` | Brain | Validated `brain_deliberation.v1` envelope |
| `POST /api/operator/brain/sessions/<id>/deliberate` | Brain | Append deliberation trace to session |
| `POST /api/operator/workflows/<id>/execute` | Organs | Governed chain execution |
