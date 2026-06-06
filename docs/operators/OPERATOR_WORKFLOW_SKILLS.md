# Operator Workflow Skills — Project Infinity 1

Status: **active operator guide**

CISIV stage: **structure**

## Purpose

This guide documents every **skill library** and **workflow library** admitted into AAIS for operator workflows, how they mount through the Plug Adapter Runtime, and how operators use them with Organs, Brain sessions, and governed chain execution.

Related:

- [AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md](../runtime/AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md) — full capability map
- [AAIS_WORKFLOW_ABILITY_CATALOG.md](../runtime/AAIS_WORKFLOW_ABILITY_CATALOG.md) — ability taxonomy by organ
- [AAIS_ANATOMICAL_LAYERS.md](../runtime/AAIS_ANATOMICAL_LAYERS.md) — Nervous system → Organs → Brain → Brainstem
- Registry: [governance/aais_library_registry.v1.json](../../governance/aais_library_registry.v1.json)

## Authority model

| Layer | May | Must not |
|-------|-----|----------|
| **Brain** (Nova Cortex) | Interpret intent, rank organs/chains, deliberate, propose | Execute plugs, run chains, self-authorize |
| **Operator** | Inspect proposals, accept/reject/defer, manually run chains | Assume accept auto-executes |
| **Jarvis / OTEM** | Authorize material actions, enforce checkpoints | Bypass ledger receipts |

Skills and workflows are **plugs** in the nervous system. They become actionable only after operator approval paths (OTEM checkpoint, workflow approvals, or explicit chain run).

## Operator surfaces

| Surface | URL / API | Use |
|---------|-----------|-----|
| Plugins + Organs | `/operator/plugins` | Browse plugs, libraries, workflow bundles; run governed chains when ready |
| Brain Sessions | `/operator/brain` | Inspect proposals, organ/chain fitness, deliberation timeline; accept/reject/defer |
| Workflow Approvals | `/workflows/approvals` | OTEM Level 10 execution approvals |
| Operator Ledger | `/operator/ledger` | Decision and execution receipts |

## Skill library classes

AAIS admits three skill-related library classes plus governed workflow bundles:

| Class | Adapter | Discovery |
|-------|---------|-----------|
| `cursor_skill` | `src/skill_adapter.py` | Cursor Agent Skills (`SKILL.md` descriptors) |
| `hf_agent_skill` | `src/skill_adapter.py` | Hugging Face Hub agent skills |
| `workflow` | `src/workflow_plugin_catalog.py` | Linear workflow bundle chains |

List live catalogs:

```bash
curl -s http://127.0.0.1:8000/legacy_api/api/operator/plugins/libraries | python -m json.tool
curl -s http://127.0.0.1:8000/legacy_api/api/operator/plugins/workflows | python -m json.tool
curl -s http://127.0.0.1:8000/legacy_api/api/operator/organs | python -m json.tool
```

---

## Cursor Skills (`cursor_skill`)

Cursor skills provide **assist-level** guidance for editor, automation, canvas, config, and subagent patterns. They mount as `skill.*` plugs.

### lib_skill_editor — Knowledge Work

| Field | Value |
|-------|-------|
| **Display name** | Cursor Skills — Editor |
| **Organ** | Knowledge Organ (`knowledge_work`) |
| **Authority** | `assist` |
| **Genome** | `plugin_skill_editor` |
| **Plug patterns** | `skill.sdk`, `skill.create_rule`, `skill.create_skill`, `skill.split_to_prs`, `skill.statusline` |

Use when authoring SDK integrations, Cursor rules, agent skills, PR splits, or CLI status lines.

### lib_skill_automation — Operational Workflows

| Field | Value |
|-------|-------|
| **Display name** | Cursor Skills — Automation |
| **Organ** | Ops Organ (`operational_workflows`) |
| **Authority** | `assist`, `execute` |
| **Genome** | `plugin_skill_automation` |
| **Plug patterns** | `skill.automate`, `skill.loop`, `skill.babysit`, `skill.shell` |

Use for automations, recurring loops, CI babysitting, and shell guidance. `execute` paths require OTEM/operator approval.

### lib_skill_canvas — Creative / Data Workflows

| Field | Value |
|-------|-------|
| **Display name** | Cursor Skills — Canvas |
| **Organ** | Creative Organ, Data Organ |
| **Authority** | `assist` |
| **Genome** | `plugin_skill_canvas` |
| **Plug patterns** | `skill.canvas` |

Use for live React canvas artifacts (analyses, billing views, timelines, interactive explorations).

### lib_skill_config — Operational Workflows

| Field | Value |
|-------|-------|
| **Display name** | Cursor Skills — Config |
| **Organ** | Ops Organ (`operational_workflows`) |
| **Authority** | `assist`, `admin` |
| **Genome** | `plugin_skill_config` |
| **Plug patterns** | `skill.update_cursor_settings`, `skill.update_cli_config`, `skill.migrate_to_skills` |

Use for Cursor/CLI settings and skill migration. `admin` posture requires explicit operator consent.

### lib_skill_subagent — Operational Workflows

| Field | Value |
|-------|-------|
| **Display name** | Cursor Skills — Subagent |
| **Organ** | Ops Organ (`operational_workflows`) |
| **Authority** | `assist` |
| **Genome** | `plugin_skill_subagent` |
| **Plug patterns** | `skill.create_subagent` |

Use for subagent creation and dispatch patterns within governed boundaries.

---

## Hugging Face Agent Skills (`hf_agent_skill`)

HF skills mount ML Hub workflows: datasets, training, evaluation, jobs, and demos. All default to **assist** authority on data/knowledge organs.

| Library ID | Display name | Primary organ | Capability summary |
|------------|--------------|---------------|-------------------|
| `lib_hf_cli` | HF Agent Skill — CLI | Data, Knowledge | Hub download/upload via `hf` CLI |
| `lib_hf_datasets` | HF Agent Skill — Datasets | Data, Knowledge | Dataset repo create/manage |
| `lib_hf_dataset_viewer` | HF Agent Skill — Dataset Viewer | Data, Knowledge | Paginated row search and stats |
| `lib_hf_evaluation` | HF Agent Skill — Evaluation | Data, Knowledge | Model card eval tables |
| `lib_hf_jobs` | HF Agent Skill — Jobs | Data, Knowledge | Cloud GPU jobs and UV scripts |
| `lib_hf_model_trainer` | HF Agent Skill — Model Trainer | Data, Knowledge | TRL fine-tuning on HF Jobs |
| `lib_hf_paper_publisher` | HF Agent Skill — Paper Publisher | Data, Knowledge | Research paper pages on Hub |
| `lib_hf_tool_builder` | HF Agent Skill — Tool Builder | Data, Knowledge | Reusable HF API scripts |
| `lib_hf_trackio` | HF Agent Skill — Trackio | Data, Knowledge | Training metrics dashboards |
| `lib_hf_gradio` | HF Agent Skill — Gradio | Data, Knowledge | Demo UIs and Spaces |

Governance for all HF skills: `receipts: per_plug`, `replay_required: true`, `operator_approval: otem_checkpoint`.

---

## Workflow Bundles (`workflow`)

Workflow libraries are **linear plug chains** admitted per organ. Execute via Organs tab or `POST /api/operator/workflows/<workflow_id>/execute` with `operator_approved: true`.

### Knowledge Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_research_brief` | `research_brief` | Research → summarize → cite → report |
| `lib_workflow_editor_skill_assist` | `editor_skill_assist` | Editor skill assist lane |
| `lib_workflow_research_to_slides` | `research_to_slides` | Research → slides export |
| `lib_workflow_support_knowledge_article` | `support_knowledge_article` | Ticket → knowledge article |
| `lib_workflow_compliance_memo` | `compliance_memo` | Contract → compliance memo |
| `lib_workflow_documentation_update` | `documentation_update` | Docs inspect → draft → verify |

### Business Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_support_resolution` | `support_resolution` | Ticket → draft → status → summary |
| `lib_workflow_contract_redline` | `contract_redline` | Contract review → redline |
| `lib_workflow_sales_proposal` | `sales_proposal` | CRM → proposal draft |
| `lib_workflow_lead_follow_up` | `lead_follow_up` | CRM → email → schedule |
| `lib_workflow_finance_report` | `finance_report` | Ledger → spreadsheet → chart |

### Creative Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_creative_asset_package` | `creative_asset_package` | Brief → assets → archive |
| `lib_workflow_campaign_visual` | `campaign_visual` | Storyboard → image → export |
| `lib_workflow_video_cut` | `video_cut` | Clips → transcript → render |
| `lib_workflow_audio_cleanup` | `audio_cleanup` | Ingest → denoise → export |

### Data Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_pdf_to_chart` | `pdf_to_chart` | PDF → table → chart |
| `lib_workflow_data_quality_run` | `data_quality_run` | Validate → anomaly report |
| `lib_workflow_metrics_dashboard` | `metrics_dashboard` | Query → chart → dashboard |
| `lib_workflow_data_cleanup` | `data_cleanup` | CSV normalize → export |

### Ops Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_incident_triage` | `incident_triage` | Alert → logs → mitigation plan |
| `lib_workflow_safe_deploy` | `safe_deploy` | Build → verify → deploy draft |
| `lib_workflow_spatial_reasoning_lane` | `spatial_reasoning_lane` | Spatial reasoning assist |
| `lib_workflow_cloud_incident_response` | `cloud_incident_response` | Cloud incident playbook |
| `lib_workflow_file_archive` | `file_archive` | File archive pipeline |

### Personal Organ

| Library ID | Workflow ID | Chain purpose |
|------------|-------------|---------------|
| `lib_workflow_weekly_plan` | `weekly_plan` | Weekly planning lane |
| `lib_workflow_journal_to_knowledge` | `journal_to_knowledge` | Journal → knowledge capture |
| `lib_workflow_habit_review` | `habit_review` | Habit review lane |

---

## Brain layer — proposals, scoring, sessions, deliberation

The Brain layer ranks and proposes; it never executes skills or workflows directly.

| Contract | Doc | API |
|----------|-----|-----|
| `brain_proposal.v1` | [BRAIN_PROPOSAL_CONTRACT.md](../contracts/BRAIN_PROPOSAL_CONTRACT.md) | `POST /api/operator/brain/propose` |
| `brain_session.v1` | [BRAIN_SESSION_CONTRACT.md](../contracts/BRAIN_SESSION_CONTRACT.md) | `GET/POST /api/operator/brain/sessions` |
| `brain_deliberation.v1` | [BRAIN_DELIBERATION_CONTRACT.md](../contracts/BRAIN_DELIBERATION_CONTRACT.md) | `POST /api/operator/brain/deliberate` |

### Typical operator flow

1. **Create brain session** with operator intent text.
2. **Inspect** `organ_rankings` and `chain_rankings` (fitness-sorted).
3. **Optional:** open Deliberation tab for `options → tradeoffs → commit` trace.
4. **Accept** the proposal (records consent + ledger receipt).
5. **Manually run** the top-ranked chain from Organs tab (`operator_approved: true`).

```bash
# Propose routing with fitness rankings
curl -s -X POST http://127.0.0.1:8000/legacy_api/api/operator/brain/propose \
  -H "Content-Type: application/json" \
  -d '{"text":"research a topic and draft a brief"}' | python -m json.tool

# Create session with proposal + optional deliberation
curl -s -X POST http://127.0.0.1:8000/legacy_api/api/operator/brain/sessions \
  -H "Content-Type: application/json" \
  -d '{"text":"Should we use plan A or plan B?", "include_deliberation": true}' | python -m json.tool

# Accept session (consent only — does not auto-run chain)
curl -s -X POST http://127.0.0.1:8000/legacy_api/api/operator/brain/sessions/<session_id>/decide \
  -H "Content-Type: application/json" \
  -d '{"decision":"accept"}' | python -m json.tool
```

---

## Verification gates

```bash
make workflow-family-gate
make brain-proposal-gate
make library-gate
```

Proof packets:

- [BRAIN_SCORING_SESSIONS_V1_PROOF.md](../proof/platform/BRAIN_SCORING_SESSIONS_V1_PROOF.md)
- [BRAIN_DELIBERATION_V1_PROOF.md](../proof/platform/BRAIN_DELIBERATION_V1_PROOF.md)

---

## Quick reference — six workflow-family organs

| Organ | `family_id` | Typical skills / workflows |
|-------|-------------|---------------------------|
| Knowledge | `knowledge_work` | Editor skills, research brief, compliance memo, HF datasets |
| Business | `business_workflows` | Support resolution, sales proposal, contract redline |
| Creative | `creative_workflows` | Canvas skill, campaign visual, video cut |
| Data | `data_workflows` | HF jobs/trainer, PDF to chart, metrics dashboard |
| Ops | `operational_workflows` | Automation skill, incident triage, safe deploy |
| Personal | `personal_workflows` | Weekly plan, journal to knowledge, habit review |
