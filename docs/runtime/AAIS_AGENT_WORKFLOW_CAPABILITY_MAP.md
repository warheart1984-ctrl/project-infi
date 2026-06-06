# AAIS Agent Workflow Capability Map

Status: **active architecture map**

CISIV stage: **structure**

## Doctrine

AAIS does not replace agent ecosystems; it governs their admission, authority, execution,
receipts, replay, and operator trust boundaries.

## Purpose

This map places known agent and workflow abilities inside AAIS. External ecosystems such as
LangChain, LlamaIndex, MCP servers, CrewAI, AutoGen, HuggingFace Agents, Cursor, Claude Code,
Copilot, Grok tools, local scripts, and cloud APIs may provide useful capabilities. AAIS defines
where those capabilities are admitted, governed, executed, recorded, and replayed.

This is not a product comparison. It is an adapter placement map.

Companion catalog: [AAIS_WORKFLOW_ABILITY_CATALOG.md](AAIS_WORKFLOW_ABILITY_CATALOG.md).

## AAIS Control Surfaces

| AAIS surface | Role |
|---|---|
| UL substrate | Normalizes payloads, visible structure, traces, receipts, and operator-readable envelopes |
| Plug Adapter Runtime | Discovers, catalogs, enables, disables, and executes external plugs |
| MCP Bridge | Translates MCP server descriptors and stdio tools into AAIS plug contracts |
| Capability Service Bridge | Routes admitted native and external capabilities into Jarvis-accessible lanes |
| OTEM | Holds bounded planning/checkpoint authority before execution with meaningful blast radius |
| Operator Decision Ledger | Records decisions, approvals, executions, receipts, and governance posture |
| Subsystem Genomes | Stores identity, phase, invariant, dependency, and admission metadata |
| CISIV | Moves concepts through identity, structure, implementation, and verification |
| Replay / Temporal Replay | Reconstructs execution context, receipts, deltas, and outcomes |
| Operator UI | Makes discovery, enablement, receipts, and risk posture visible to the human operator |

## Ecosystem Mount Points

| Ecosystem | What AAIS mounts | Primary AAIS fit | Required governance |
|---|---|---|---|
| MCP servers | Tools, resources, prompts, schemas, server launch descriptors | MCP Bridge -> Plug Adapter Runtime | descriptor validation, disabled-by-default, ledger receipts |
| LangChain | Tools, chains, retrievers, agents, memory adapters | Plug Adapter Runtime or native Capability Service Bridge provider | authority cap per tool, chain receipts, prompt/context provenance |
| LlamaIndex | Data connectors, indexes, query engines, graph/query tools | Plug Adapter Runtime + Knowledge Authority lane | data-source provenance, retrieval scope, memory membrane |
| CrewAI | Crews, tasks, role agents, delegation workflows | Workflow Runtime + Plug Adapter Runtime | role boundary, delegation receipts, human approval for execute/admin |
| AutoGen | Agent conversations, tool use, human-in-loop loops | Conversation governance + Plug Adapter Runtime | speaker provenance, tool authority caps, replayable transcript |
| HuggingFace Agents | Tools, pipelines, model-backed functions | Plug Adapter Runtime + Provider Route | model/tool identity, execution sandbox, output integrity |
| Cursor / editor agents | File tools, code actions, skills, local commands | Skill Adapter + Patch/Forge lanes | patch review, verification gate, contributor provenance |
| Claude / Copilot / Grok tool ecosystems | Editor tools, search, code actions, hosted tools | Plug Adapter Runtime or provider route | bounded authority, no silent cross-tool execution |
| Local scripts and CLIs | Shell commands, repo tools, build/test/deploy helpers | Native Capability Adapter + OTEM when needed | command allowlist, blast radius, rollback notes |
| Cloud APIs and SaaS tools | Issues, tickets, CRM, storage, deployment, notifications | MCP Bridge or HTTP native plug | auth visibility, secret redaction, tenant boundary |

## Workflow Ability Placement

| Workflow ability | Examples | Where it fits in AAIS | Governance notes |
|---|---|---|---|
| Tool discovery | MCP tools, Cursor skills, native routes | `src/plug_discovery.py` | discovery never equals activation |
| Tool schema normalization | MCP descriptors, JSON schemas, OpenAPI-like specs | `schemas/plug_adapter.v1.json` | validate before genome or execution |
| Tool enable/disable | plugin toggles, operator approvals | `/operator/plugins`, Plug Adapter Runtime | default disabled, operator-visible state |
| Tool execution | function calls, MCP stdio calls, local helpers | `src/plug_adapter_runtime.py` | emit receipt, fail closed when disabled |
| Structured actions | JSON tool calls, forms, command args | UL substrate + plug IO contract | reject malformed or authority-escalating args |
| Retrieval / RAG | vector search, doc search, knowledge bases | Knowledge Authority + LlamaIndex/LangChain plugs | source provenance required |
| Indexing | vector indexes, graph indexes, file catalogs | Knowledge Authority + Subsystem Genome | index build must record source and version |
| Data connectors | databases, SaaS, files, APIs | MCP Bridge or native HTTP plugs | tenant and credential membrane required |
| Memory read | long-term memory, session state, archives | Memory Board / Knowledge Authority | live memory reads stay gateway-bound |
| Memory write | notes, persistent facts, operator state | Memory Board + Operator Decision Ledger | no direct ungoverned writes |
| Agent planning | ReAct, plan-and-execute, task graphs | OTEM + Planning/Reasoning lanes | plans are not execution authority |
| Reason/act/observe loops | ReAct, AutoGen conversations | Jarvis protocol + OTEM + Replay | each act/observe emits traceable delta |
| Multi-agent roles | CrewAI roles, AutoGen speakers | Workflow Runtime + Conversation Governance | role authority cannot exceed plug authority |
| Delegation | agent-to-agent task assignment | Operator Decision Ledger + Workflow Runtime | delegation needs provenance and receipt |
| Human-in-the-loop | approvals, review, manual checkpoint | Operator UI + OTEM + Ledger | human approval must be explicit and replayable |
| Chains | LangChain chains, sequential pipelines | Workflow Runtime + UL envelope | chain steps need per-step receipts |
| DAG workflows | task graphs, build/deploy graphs | Workflow Runtime + Replay | graph node identity and retry policy required |
| Scheduling | cron, monitors, recurring jobs | Workflow Shell / Runtime | scheduled execution needs operator-owned policy |
| Event triggers | webhooks, file changes, queue events | Platform membrane + Event Chain | ingress must pass boundary checks |
| Streaming | token streams, event streams, tool progress | UL substrate + Tracing Spine | streamed outputs must still finalize with receipt |
| Browser / web actions | browser-use, Playwright, web automation | UI Vision / Native Capability Adapter | screenshot/proof and domain scope required |
| File operations | read/write/move/delete, patch application | Patch/Forge lanes + Change Scope | destructive changes require bounded approval |
| Code generation | patches, modules, docs, tests | PatchForge / Forge Contractor | verification plan before apply |
| Code execution | tests, scripts, notebooks, sandboxes | Native Capability Adapter + OTEM | command scope and timeout required |
| Build/test gates | pytest, npm, make, governance checks | Verification Gate | report skips and environment limits |
| Deployment | Docker, cloud deploy, package publish | Execute/Admin plug lane | dual-control or explicit release approval |
| Secrets/auth | tokens, API keys, OAuth, MCP auth | Security Protocol + MCP Bridge snapshot | receipt may show auth state, never secret values |
| Rate limits/budgets | provider quotas, API cost routing | Provider Budgeting + Ledger | cost and quota state must be visible |
| Model routing | OpenAI, Anthropic, local, HF models | Provider Route + Model Routing | provider identity and fallback reason recorded |
| Output integrity | scaffold stripping, final reply guards | Output Integrity + Project Infi Law | visible output cannot leak hidden scaffolds |
| Safety policy | allow/deny, blast radius, invariants | Policy Gate + Safety Envelope | policy denial is a governed outcome |
| Provenance | sources, contributors, tool lineage | UL substrate + Ledger + provenance charter | no claim without proof or posture |
| Receipts | tool calls, decisions, approvals, executions | Operator Decision Ledger | every material action should be receipt-backed |
| Replay | reconstruct turns, tool calls, state transitions | Temporal Replay | replay verifies causality, not vibes |
| Evaluation | rubrics, IO tests, regression gates | ForgeEval + Verification Gate | eval result must link to tested artifact |
| Observability | traces, logs, runtime status | Tracing Spine + Operator UI | trace IDs bind UI, API, and ledger |
| Error recovery | retries, fallbacks, compensating actions | Workflow Runtime + State Hygiene | fallback reason must be visible |
| Rollback | revert patches, disable plugs, restore state | Patch Apply + Runtime enablement state | rollback path recorded before risky execution |
| Marketplace/catalog | plug list, workflow templates, capability registry | Operator UI + Plug Adapter Runtime | cataloged entries remain disabled until admitted |
| Federation | remote agents, remote proof networks | Platform membrane + Proof Federation | external proof must be admitted, not trusted by default |

## Admission Path For Any New Workflow Ability

1. Discover the ability as a descriptor, file, route, MCP server, or human-provided spec.
2. Assign a stable identity and source kind.
3. Generate or validate `plug_adapter.v1` structure.
4. Create or update the subsystem genome.
5. Set authority level: `observe`, `assist`, `execute`, or `admin`.
6. Keep it disabled until operator enablement or gate-promoted observe-only admission.
7. Execute only through UL-wrapped runtime paths.
8. Emit operator ledger receipts.
9. Make the run replayable.
10. Promote only after verification gates pass.

## Current AAIS Fit

| Capability family | Current AAIS status | Notes |
|---|---|---|
| MCP tools | prototype | `src/mcp_bridge.py`, `governance/mcp_server_manifest.v1.json` |
| Cursor skills | prototype | `src/skill_adapter.py` discovers skill descriptors |
| Native AAIS routes | prototype | `src/native_capability_adapter.py` maps AAIS capabilities into plugs |
| Operator plugin UI | implementation | `/operator/plugins` shows registry, toggles, details, receipts |
| Ledger receipts | implementation | plug execution emits governed receipts |
| Subsystem genomes | structure | platform and per-plugin genomes exist for the adapter wave |
| External ecosystem adapters | concept/structure | LangChain, LlamaIndex, CrewAI, AutoGen, HF agents mount through plug contracts |

## Rule

If a workflow ability can act, write, decide, route, retrieve, spend, deploy, or influence operator state,
AAIS must govern it before Jarvis may rely on it.

## Library Routing Registry

| Library | Class | Mount | Workflow category | Status |
|---------|-------|-------|-------------------|--------|
| lib_mcp_huggingface | mcp | src.mcp_bridge | data_workflows,knowledge_work,creative_workflows | prototype |
| lib_mcp_linear | mcp | src.mcp_bridge | business_workflows,operational_workflows | prototype |
| lib_mcp_firetiger | mcp | src.mcp_bridge | operational_workflows | prototype |
| lib_mcp_datadog | mcp | src.mcp_bridge | operational_workflows | concept |
| lib_skill_editor | cursor_skill | src.skill_adapter | knowledge_work | prototype |
| lib_skill_automation | cursor_skill | src.skill_adapter | operational_workflows | prototype |
| lib_skill_canvas | cursor_skill | src.skill_adapter | creative_workflows,data_workflows | prototype |
| lib_skill_config | cursor_skill | src.skill_adapter | operational_workflows | prototype |
| lib_skill_subagent | cursor_skill | src.skill_adapter | operational_workflows | prototype |
| lib_hf_cli | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_datasets | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_dataset_viewer | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_evaluation | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_jobs | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_model_trainer | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_paper_publisher | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_tool_builder | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_trackio | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_hf_gradio | hf_agent_skill | src.skill_adapter | data_workflows,knowledge_work | prototype |
| lib_native_jarvis | native_capability | src.native_capability_adapter | operational_workflows,creative_workflows | prototype |
| lib_native_forge | native_capability | src.native_capability_adapter | operational_workflows,data_workflows | prototype |
| lib_native_media | native_capability | src.native_capability_adapter | creative_workflows | prototype |
| lib_native_governance | native_capability | src.native_capability_adapter | knowledge_work,business_workflows | prototype |
| lib_native_operator | native_capability | src.native_capability_adapter | operational_workflows | prototype |
| lib_native_workspace | native_capability | src.native_capability_adapter | business_workflows | prototype |
| lib_workflow_research_brief | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_pdf_to_chart | workflow | src.workflow_plugin_catalog | data_workflows | prototype |
| lib_workflow_incident_triage | workflow | src.workflow_plugin_catalog | operational_workflows | prototype |
| lib_workflow_support_resolution | workflow | src.workflow_plugin_catalog | business_workflows | prototype |
| lib_workflow_creative_asset_package | workflow | src.workflow_plugin_catalog | creative_workflows | prototype |
| lib_workflow_safe_deploy | workflow | src.workflow_plugin_catalog | operational_workflows | prototype |
| lib_workflow_editor_skill_assist | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_spatial_reasoning_lane | workflow | src.workflow_plugin_catalog | operational_workflows | prototype |
| lib_workflow_contract_redline | workflow | src.workflow_plugin_catalog | business_workflows | prototype |
| lib_workflow_research_to_slides | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_support_knowledge_article | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_sales_proposal | workflow | src.workflow_plugin_catalog | business_workflows | prototype |
| lib_workflow_data_quality_run | workflow | src.workflow_plugin_catalog | data_workflows | prototype |
| lib_workflow_cloud_incident_response | workflow | src.workflow_plugin_catalog | operational_workflows | prototype |
| lib_workflow_compliance_memo | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_documentation_update | workflow | src.workflow_plugin_catalog | knowledge_work | prototype |
| lib_workflow_lead_follow_up | workflow | src.workflow_plugin_catalog | business_workflows | prototype |
| lib_workflow_finance_report | workflow | src.workflow_plugin_catalog | business_workflows | prototype |
| lib_workflow_campaign_visual | workflow | src.workflow_plugin_catalog | creative_workflows | prototype |
| lib_workflow_video_cut | workflow | src.workflow_plugin_catalog | creative_workflows | prototype |
| lib_workflow_audio_cleanup | workflow | src.workflow_plugin_catalog | creative_workflows | prototype |
| lib_workflow_metrics_dashboard | workflow | src.workflow_plugin_catalog | data_workflows | prototype |
| lib_workflow_data_cleanup | workflow | src.workflow_plugin_catalog | data_workflows | prototype |
| lib_workflow_file_archive | workflow | src.workflow_plugin_catalog | operational_workflows | prototype |
| lib_workflow_weekly_plan | workflow | src.workflow_plugin_catalog | personal_workflows | prototype |
| lib_workflow_journal_to_knowledge | workflow | src.workflow_plugin_catalog | personal_workflows | prototype |
| lib_workflow_habit_review | workflow | src.workflow_plugin_catalog | personal_workflows | prototype |

## Workflow Family Routing

Workflow-family organs aggregate libraries and bundles into six domain functions. Registry engine: `src/workflow_family_registry.py`. Operator API: `GET /api/operator/organs`.

| Family | Mythic label | family_id | Genome gene | API route | Status |
|--------|--------------|-----------|-------------|-----------|--------|
| Knowledge Work | Knowledge Organ | knowledge_work | workflow_family_knowledge | GET /api/operator/organs/knowledge_work | prototype |
| Business Workflows | Business Organ | business_workflows | workflow_family_business | GET /api/operator/organs/business_workflows | prototype |
| Creative Workflows | Creative Organ | creative_workflows | workflow_family_creative | GET /api/operator/organs/creative_workflows | prototype |
| Data Workflows | Data Organ | data_workflows | workflow_family_data | GET /api/operator/organs/data_workflows | prototype |
| Operational Workflows | Ops Organ | operational_workflows | workflow_family_ops | GET /api/operator/organs/operational_workflows | prototype |
| Personal Workflows | Personal Organ | personal_workflows | workflow_family_personal | GET /api/operator/organs/personal_workflows | prototype |

## Brain Layer Routing

Nova Cortex is wired as the bounded Brain layer through `src/brain_layer_runtime.py`.
It reads organ readiness, produces proposal-only workflow-family recommendations, and exposes
operator-visible status at `GET /api/operator/brain`.

| Brain layer component | Role | Authority boundary |
|---|---|---|
| Nova Cortex runtime | Cognitive lobes, turn pipeline, inspectable artifacts | May interpret; may not execute |
| Brain-layer adapter | Binds Cortex to six workflow-family organs | Proposal-only self-routing |
| Brain proposal contract | `brain_proposal.v1` outward envelope | ArtifactType utterances only; no ActionType |
| Jarvis / OTEM / Operator | Execution authorization and checkpoints | Required for material action |

## Brain Proposal Routing

Canonical outward envelope: `brain_proposal.v1`. Validator: `src/brain_proposal_validator.py`.
Contract: `docs/contracts/BRAIN_PROPOSAL_CONTRACT.md`.

| Surface | Mount | API route | Status |
|---------|-------|-----------|--------|
| Brain proposal builder | src.brain_proposal_validator | POST /api/operator/brain/propose | prototype |
| Brain chain scorer | src.brain_chain_scorer | routing.organ_rankings / chain_rankings | prototype |
| Brain session store | src.brain_session_store | GET/POST /api/operator/brain/sessions | prototype |
| Brain session decisions | src.brain_session_store | POST /api/operator/brain/sessions/<id>/decide | prototype |
| Brain sessions UI | frontend OperatorBrainSessions | /operator/brain | prototype |
| Brain deliberation contract | src.brain_deliberation_validator | POST /api/operator/brain/deliberate | prototype |
| Brain deliberation adapter | src.brain_deliberation_runtime | stage_chain from cognitive.deliberation | prototype |
| Brain session deliberation | src.brain_session_store | POST /api/operator/brain/sessions/<id>/deliberate | prototype |
| Brain layer status | src.brain_layer_runtime | GET /api/operator/brain | prototype |
| OTEM trace pointer | src.otem_runtime | brain_proposal_id on enrich | prototype |
