# AAIS Anatomical Layers

Status: **active architecture map**

CISIV stage: **structure**

## Doctrine

AAIS is built body-before-brain. Each anatomical layer maps to concrete modules, registries, and API surfaces in `project-infi`. Mythic labels (Organ, Brainstem) appear in docs only; engineering identifiers follow [AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md](../contracts/AAIS_CODEX_CURSOR_NAMING_PROTOCOL.md).

## Layer Map

| Layer | Mythic stage | Mythic name | Engineering surface | Status |
|-------|--------------|-------------|---------------------|--------|
| 1 | — | Senses | MCP bridge, skill adapter, plug discovery | built |
| 2 | — | Memory | Operator ledger, run ledger, temporal replay, genomes | built |
| 3 | — | Muscles | Plug adapter runtime, native capability adapter, OTEM | built |
| 4 | — | Nervous system | Library registry, workflow catalog, Jarvis routing | built |
| 5 | — | Organs | Workflow family registry + readiness rollups + governed organ mesh | integrated mesh |
| 6 | — | Brainstem | UL substrate, constitutional law, governance gates | built |
| 7 | — | Brain | Nova Cortex runtime, proposal-only workflow-family routing | wired bounded |
| 8 | — | Culture | Habit mining, adoption, preference-slot overlay | integrated habits |
| 9 | — | Identity | Self-model drift, foundation claim adoption, anchor validation | integrated identity |
| 10 | — | Narrative Continuity | Life-story drift fusion, session beat adoption, Nova bridge | integrated narrative |
| 11 | — | Autobiographical Agency | Ongoing-work drift fusion, operational episode adoption, intent bridge | integrated agency |
| 12 | — | Social Continuity | Relational drift fusion, archive bond adoption, federation bridge | integrated social |
| 13 | **11** | Multi-Being Continuity | Cross-organism drift fusion, federation-slot pact adoption, UGR graph bridge | integrated federation |
| 14 | **12** | Culture-of-Beings | Shared norm drift fusion, slot_09 norm adoption, MBC-grounded cluster posture | integrated culture-of-beings |
| 15 | **13** | Constitutional Ecosystem | Charter drift fusion, slot_08 ecosystem adoption, tier-5 federation law | integrated ecosystem |
| 16 | **14** | Governance Membrane | Permeability policy fusion, slot_10 membrane adoption, IMXP/memory wrapper | meta-body membrane |
| 17 | **15** | Inter-Substrate Diplomacy | Cross-substrate accord drift, diplomacy overlay, IMXP/memory membrane fusion | civilizational arc |
| 18 | **16** | Norm Federations | Treaty drift fusion, norm federation overlay, COB-2 treaty ladders | civilizational arc |
| 19 | **17** | Constitutional Evolution | Charter amendment drift, tier-5 contextual gates, evolution overlay | civilizational arc |
| 20 | **18** | Governed Civilization | Civilization charter envelope, federation-scope constitution, coherence elevation | civilizational arc |

**Body completeness:** See [AAIS_BODY_COMPLETENESS_MATRIX.md](./AAIS_BODY_COMPLETENESS_MATRIX.md) (Releases 31–48+). Layers 14–16 are the **Beyond the Body** tier; Layers 17–20 are the **Civilizational** tier ([AAIS_CIVILIZATIONAL_STAGES.md](./AAIS_CIVILIZATIONAL_STAGES.md)).

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
| Constitutional lawbook | `META_ARCHITECT_LAWBOOK.md` (repo root) |
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

## 11. Autobiographical Agency

Ongoing operator partnership threads — operational slot (`slot_02`) under dual gate.

| Component | Path |
|-----------|------|
| Autobiographical agency runtime | `src/autobiographical_agency_runtime.py` |
| Autobiographical registry | `governance/operator_autobiographical_registry.v1.json` |
| Jarvis autobiographical authority | `src/jarvis_autobiographical_authority.py` |
| Episode adoption bridge | `src/autobiographical_episode_adoption_bridge.py` |
| Contract | `docs/contracts/AUTOBIOGRAPHICAL_AGENCY_CONTRACT.md` |
| Operator API | `GET/POST /api/operator/autobiographical`, `/episodes`, `/episodes/adopt` |
| Operator UI | `frontend/src/pages/OperatorPlugins.jsx` (Autobiographical tab) |
| Governance gate | `make autobiographical-agency-body-gate` |

## 12. Social Continuity

Stable relational bonds across time and context — archive slot (`slot_04`) under dual gate.

| Component | Path |
|-----------|------|
| Social continuity runtime | `src/social_continuity_runtime.py` |
| Social registry | `governance/operator_social_registry.v1.json` |
| Jarvis social authority | `src/jarvis_social_authority.py` |
| Bond adoption bridge | `src/social_bond_adoption_bridge.py` |
| Social continuity organ | `src/social_continuity_organ.py` |
| Contract | `docs/contracts/SOCIAL_CONTINUITY_CONTRACT.md` |
| Operator API | `GET/POST /api/operator/social`, `/bonds`, `/bonds/adopt` |
| Operator UI | `frontend/src/pages/OperatorPlugins.jsx` (Social tab) |
| Governance gate | `make social-continuity-body-gate` |

## 13. Multi-Being Continuity

Lawful continuity between multiple governed organisms — federation slot (`slot_07`) under dual gate.

| Component | Path |
|-----------|------|
| Multi-being continuity runtime | `src/multi_being_continuity_runtime.py` |
| Multi-being registry | `governance/operator_multi_being_registry.v1.json` |
| Jarvis multi-being authority | `src/jarvis_multi_being_authority.py` |
| Pact adoption bridge | `src/multi_being_pact_adoption_bridge.py` |
| Multi-being continuity organ | `src/multi_being_continuity_organ.py` |
| Contract | `docs/contracts/MULTI_BEING_CONTINUITY_CONTRACT.md` |
| Operator API | `GET/POST /api/operator/multi-being`, `/pacts`, `/pacts/adopt` |
| Operator UI | `frontend/src/pages/OperatorPlugins.jsx` (Multi-Being tab) |
| Governance gate | `make multi-being-continuity-body-gate` |

## 14. Culture-of-Beings

Shared cross-organism norms — culture-of-beings overlay (`slot_09`) under dual gate.

| Component | Path |
|-----------|------|
| Culture-of-beings runtime | `src/culture_of_beings_runtime.py` |
| Registry | `governance/operator_culture_of_beings_registry.v1.json` |
| Jarvis authority | `src/jarvis_culture_of_beings_authority.py` |
| Shared norm adoption bridge | `src/shared_norm_adoption_bridge.py` |
| Organ | `src/culture_of_beings_organ.py` |
| Operator API | `GET/POST /api/operator/culture-of-beings`, `/norms`, `/norms/adopt` |
| Governance gate | `make culture-of-beings-body-gate` |

## 15. Constitutional Ecosystem

Ecosystem charters binding multiple adopted pacts — ecosystem overlay (`slot_08`).

| Component | Path |
|-----------|------|
| Constitutional ecosystem runtime | `src/constitutional_ecosystem_runtime.py` |
| Registry | `governance/operator_ecosystem_registry.v1.json` |
| Jarvis ecosystem authority | `src/jarvis_ecosystem_authority.py` |
| Organ | `src/constitutional_ecosystem_organ.py` |
| Operator API | `GET/POST /api/operator/ecosystems`, `/charters`, `/charters/adopt` |
| Governance gate | `make constitutional-ecosystem-body-gate` |

## 16. Governance Membrane (Beyond the Body)

Unified permeability policy — membrane overlay (`slot_10`).

| Component | Path |
|-----------|------|
| Membrane runtime | `src/multi_organism_governance_membrane_runtime.py` |
| IMXP wrapper | `src/imxp_governance_wrapper.py` |
| Memory membrane hook | `src/memory_governance_membrane.py` |
| Jarvis membrane authority | `src/jarvis_membrane_authority.py` |
| Operator API | `GET/POST /api/operator/governance-membrane`, `/policies`, `/policies/adopt` |
| Governance gate | `make governance-membrane-body-gate` |

## 17. Inter-Substrate Diplomacy (Civilizational)

Cross-substrate diplomatic accords — diplomacy overlay (`civilizational_tier` 15).

| Component | Path |
|-----------|------|
| Diplomacy runtime | `src/inter_substrate_diplomacy_runtime.py` |
| Registry | `governance/operator_diplomatic_registry.v1.json` |
| Jarvis diplomacy authority | `src/jarvis_diplomacy_authority.py` |
| Adoption bridge | `src/diplomatic_accord_adoption_bridge.py` |
| Operator API | `GET/POST /api/operator/diplomacy`, `/accords`, `/accords/adopt` |
| Governance gate | `make inter-substrate-diplomacy-body-gate` |

## 18. Norm Federations (Civilizational)

Treaty ladders linking COB-2 norms — norm federation overlay (`civilizational_tier` 16).

| Component | Path |
|-----------|------|
| Norm federation runtime | `src/norm_federation_runtime.py` |
| Registry | `governance/operator_norm_federation_registry.v1.json` |
| Jarvis norm federation authority | `src/jarvis_norm_federation_authority.py` |
| Operator API | `GET/POST /api/operator/norm-federations`, `/treaties`, `/treaties/adopt` |
| Governance gate | `make norm-federation-body-gate` |

## 19. Constitutional Evolution (Civilizational)

Tier-5 charter amendments — evolution overlay (`civilizational_tier` 17).

| Component | Path |
|-----------|------|
| Evolution runtime | `src/constitutional_evolution_runtime.py` |
| Registry | `governance/operator_constitutional_evolution_registry.v1.json` |
| Jarvis evolution authority | `src/jarvis_constitutional_evolution_authority.py` |
| Operator API | `GET/POST /api/operator/constitutional-evolution`, `/amendments`, `/amendments/adopt` |
| Governance gate | `make constitutional-evolution-body-gate` |

## 20. Governed Civilization (Civilizational)

Federation-scope civilization envelope — civilization overlay (`civilizational_tier` 18).

| Component | Path |
|-----------|------|
| Civilization runtime | `src/governed_civilization_runtime.py` |
| Registry | `governance/operator_civilization_registry.v1.json` |
| Jarvis civilization authority | `src/jarvis_civilization_authority.py` |
| Operator API | `GET/POST /api/operator/civilizations`, `/charters`, `/charters/adopt` |
| Governance gate | `make governed-civilization-body-gate` |
| Aggregate gate | `make civilizational-arc-gate` |
