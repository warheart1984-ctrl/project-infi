# AAIS Workflow Ability Catalog

Status: **active architecture catalog**

CISIV stage: **structure**

## Doctrine

AAIS does not replace agent ecosystems; it governs their admission, authority, execution,
receipts, replay, and operator trust boundaries.

This catalog defines the workflow abilities AAIS should be able to admit, compose, and govern
through the Plug Adapter Runtime, MCP Bridge, native capability adapters, UL substrate, OTEM,
Operator Decision Ledger, subsystem genomes, and replay.

## Workflow Admission Rule

Every workflow ability enters AAIS as a governed capability. It must have:

- a stable identity
- source provenance
- authority level
- input/output contract
- operator-visible risk posture
- receipt emission
- replay path
- verification gate or documented limitation

## 1. Knowledge Work

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| Research | Knowledge Authority + browser/search plugs + live research lane | `assist` | sources, query trail, retrieved artifacts |
| Summarization | UL substrate + provider route + output integrity | `assist` | source set, prompt shape, final summary |
| Analysis | Reasoning lane + knowledge authority + optional spreadsheet/data plugs | `assist` | assumptions, evidence, derived findings |
| Drafting | Prompt assembly + document generation plug | `assist` | draft inputs, version, claim posture |
| Editing | Document plug + patch/rewrite lane | `assist` | before/after delta, operator acceptance |
| Planning | OTEM + planning lane + workflow runtime | `assist` | plan, constraints, next action boundary |
| Reporting | Knowledge/data plugs + document/slides/export plugs | `assist` or `execute` | report inputs, generated artifact, delivery path |
| Documentation | Forge/doc lane + subsystem genome references | `assist` | changed files, proof links, validation commands |
| Compliance | Policy gate + contract docs + audit ledger | `assist` | checklist, exceptions, accepted risks |

### Knowledge Work Chains

| Chain | Steps | Required controls |
|---|---|---|
| Research brief | browser/search -> source capture -> summarize -> cite -> save report | source provenance, output integrity, ledger receipt |
| Compliance memo | contract corpus -> checklist -> gap analysis -> remediation plan | policy gate, evidence links, human acceptance |
| Documentation update | inspect code/docs -> draft changes -> verify links -> emit proof notes | patch review, doc lint, governance notes |

## 2. Business Workflows

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| CRM updates | SaaS/MCP plug + Operator Decision Ledger | `execute` | record id, field delta, approval |
| Ticketing | issue tracker plug + project workflow runtime | `execute` | ticket id, status transition, assignee |
| Project management | task graph + scheduling plug + reporting lane | `assist` or `execute` | plan delta, task creation/update receipt |
| Scheduling | calendar plug + operator approval | `execute` | attendees, time, conflict scan |
| Customer support | inbox/helpdesk plug + knowledge authority | `assist` or `execute` | customer context, suggested reply, sent receipt |
| Sales workflows | CRM + email + proposal/doc plugs | `execute` | prospect state, sent artifacts, follow-up task |
| HR workflows | HRIS/document/signature plugs | `execute` or `admin` | personnel boundary, redacted receipt |
| Finance workflows | accounting/spreadsheet/banking plugs | `execute` or `admin` | amount, account boundary, dual-control when needed |

### Business Chains

| Chain | Steps | Required controls |
|---|---|---|
| Lead follow-up | CRM query -> draft email -> operator approval -> send -> schedule follow-up | CRM provenance, send receipt, calendar receipt |
| Support resolution | ticket ingest -> knowledge lookup -> draft answer -> apply status -> log summary | customer data boundary, reply approval |
| Finance report | export ledger -> transform -> spreadsheet -> chart -> archive -> notify | finance authority cap, redacted receipts |

## 3. Creative Workflows

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| Design tools | image/design plug + asset pipeline | `assist` or `execute` | prompt, input assets, output asset id |
| Image generation | image generation plug + asset governance | `assist` | prompt, seed/settings if available, output path |
| Video editing | video tool plug + render lane | `execute` | source clips, edit manifest, render artifact |
| Audio tools | audio processor plug + media family | `execute` | source audio, transform, output artifact |
| Storyboarding | planning + image/doc plugs | `assist` | scene list, visual refs, storyboard artifact |
| Asset pipelines | file manager + media tools + storage plug | `execute` | asset ids, transform receipts, storage path |

### Creative Chains

| Chain | Steps | Required controls |
|---|---|---|
| Campaign visual | brief -> storyboard -> image generation -> edit -> export -> archive | prompt provenance, asset lineage |
| Video cut | ingest clips -> transcript -> cut plan -> render -> QA -> publish draft | media receipts, human publish approval |
| Audio cleanup | ingest -> denoise -> normalize -> export -> attach to project | source/output hash, transform manifest |

## 4. Data Workflows

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| ETL | data connectors + transformation plug + workflow runtime | `execute` | source, transform version, destination |
| Querying | database/MCP plug + knowledge authority | `assist` or `execute` | query text, result scope, redaction |
| Transformation | spreadsheet/script/dataframe plug | `execute` | input hash, transform code, output hash |
| Visualization | chart/spreadsheet/dashboard plug | `assist` or `execute` | dataset id, chart spec, artifact |
| Spreadsheet automation | spreadsheet plug + formulas/scripts | `execute` | sheet id, cell/range delta |
| Dashboards | BI/dashboard plug + scheduled refresh | `execute` | source bindings, refresh receipt |

### Data Chains

| Chain | Steps | Required controls |
|---|---|---|
| PDF to chart | PDF ingest -> extract table -> spreadsheet -> chart -> storage -> notify | extraction proof, sheet receipt, storage receipt |
| Metrics dashboard | query warehouse -> transform -> chart -> dashboard publish | query scope, dashboard version |
| Data cleanup | load CSV -> normalize -> validate -> export -> report anomalies | transform replay, anomaly report |

## 5. Operational Workflows

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| File management | file/native capability adapter + change scope | `execute` | path delta, hash, rollback path |
| Cloud operations | cloud MCP/API plug + platform membrane | `execute` or `admin` | tenant, resource id, policy decision |
| Deployment | deploy plug + verification gate + release approval | `admin` | build id, environment, rollback notes |
| Monitoring | metrics/log plug + alert workflow | `observe` or `assist` | query, alert id, incident link |
| Automation tasks | workflow shell + scheduler + plug runtime | `execute` | schedule, trigger, last run receipt |

### Operational Chains

| Chain | Steps | Required controls |
|---|---|---|
| Safe deploy | build -> test -> approval -> deploy -> smoke -> monitor -> rollback checkpoint | release approval, deployment receipt |
| Incident triage | alert -> logs -> summarize -> assign ticket -> monitor recovery | source trace, ticket receipt |
| File archive | scan folder -> classify -> move/archive -> index -> report | file delta, rollback manifest |

## 6. Personal Workflows

| Ability | AAIS fit | Authority | Receipts / replay |
|---|---|---:|---|
| Reminders | automation/reminder plug + operator profile | `execute` | reminder id, time, recurrence |
| Planning | OTEM + calendar/task plugs | `assist` or `execute` | plan, task/calendar deltas |
| Journaling | memory board + document plug | `assist` | entry path, privacy boundary |
| Habit tracking | personal tracker plug + dashboard | `execute` | event id, streak/status delta |
| Personal knowledge management | memory/notes/RAG plugs | `assist` or `execute` | source note, link graph, index version |

### Personal Chains

| Chain | Steps | Required controls |
|---|---|---|
| Weekly plan | calendar -> tasks -> priorities -> schedule blocks -> reminders | operator approval, calendar/task receipts |
| Journal to knowledge | journal entry -> summarize -> tag -> index -> surface reminders | privacy boundary, memory governance |
| Habit review | pull tracker -> summarize trend -> suggest adjustment -> schedule reminder | personal data boundary |

## 7. Multi-Step, Multi-Tool Workflows

These are first-class AAIS workflows. They are not toy demos. Each step is a governed action or observation with a receipt.

| Workflow | AAIS chain | Required gates |
|---|---|---|
| PDF to chart | document vision/PDF extraction -> data transform -> spreadsheet plug -> chart plug -> storage plug -> notification plug | extraction validation, spreadsheet receipt, storage receipt, notification receipt |
| Contract redline | draft generator -> legal review plug -> redline apply -> export PDF -> file storage -> ledger receipt | legal plug authority cap, human acceptance before export |
| Research to slides | browser/search -> source capture -> summary -> slide generator -> project folder storage -> operator notification | source provenance, output integrity, storage receipt |
| Support knowledge article | ticket cluster -> summarize issue -> draft article -> review -> publish to knowledge base -> notify support team | customer data redaction, publish approval |
| Sales proposal | CRM context -> pricing/finance check -> draft proposal -> legal/compliance review -> PDF export -> CRM update | finance boundary, legal approval, CRM receipt |
| Creative asset package | brief -> storyboard -> generate assets -> edit -> export variants -> archive -> dashboard update | asset lineage, output hashes, archive receipt |
| Data quality run | ingest source -> validate schema -> transform -> anomaly report -> ticket creation -> dashboard refresh | schema gate, anomaly receipt, ticket receipt |
| Cloud incident response | alert -> logs -> analysis -> mitigation plan -> approval -> action -> monitor -> postmortem | OTEM checkpoint, admin approval, replay bundle |

## Workflow Execution Envelope

Every multi-step workflow should emit a UL envelope with:

- workflow id
- operator id or session id
- step list
- plug ids and source kinds
- authority level per step
- approval checkpoints
- receipts
- artifacts
- replay pointer
- final outcome
- unresolved governance notes

## Promotion Path

1. Catalog workflow as `concept`.
2. Assign stable workflow id and owner.
3. Map every step to a plug, native capability, or internal subsystem.
4. Define authority and approval checkpoints.
5. Define receipts and replay expectations.
6. Add a workflow template or operator UI surface.
7. Test with fixture inputs.
8. Record proof.
9. Promote to guarded runtime.
10. Promote to live runtime only after operator acceptance.

## Non-Negotiable Boundary

If the workflow touches money, credentials, legal documents, HR data, deployment, customer records,
or destructive file/cloud operations, AAIS must require explicit operator approval and a replayable receipt.

## Library Families
### MCP — Hugging Face (`lib_mcp_huggingface`)

- **Library:** `lib_mcp_huggingface`
- **Family:** data_workflows
- **Capabilities:** Hub search, papers, docs, and generative HF tools via MCP bridge.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### MCP — Linear (`lib_mcp_linear`)

- **Library:** `lib_mcp_linear`
- **Family:** business_workflows
- **Capabilities:** Issue tracking, assignments, and project ops via Linear MCP.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### MCP — Firetiger (`lib_mcp_firetiger`)

- **Library:** `lib_mcp_firetiger`
- **Family:** operational_workflows
- **Capabilities:** Observability investigations and agent runs via Firetiger MCP.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### MCP — Datadog (`lib_mcp_datadog`)

- **Library:** `lib_mcp_datadog`
- **Family:** operational_workflows
- **Capabilities:** Metrics, logs, and monitors via Datadog MCP (pending healthy server).
- **Authority:** observe, assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Cursor Skills — Editor (`lib_skill_editor`)

- **Library:** `lib_skill_editor`
- **Family:** knowledge_work
- **Capabilities:** SDK, rules, skills, PR split, and statusline authoring.
- **Authority:** assist
- **Receipts:** per_plug
- **Replay:** True
### Cursor Skills — Automation (`lib_skill_automation`)

- **Library:** `lib_skill_automation`
- **Family:** operational_workflows
- **Capabilities:** Automations, loops, babysit CI, and shell execution guidance.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Cursor Skills — Canvas (`lib_skill_canvas`)

- **Library:** `lib_skill_canvas`
- **Family:** creative_workflows
- **Capabilities:** Live React canvas artifacts for analytical deliverables.
- **Authority:** assist
- **Receipts:** per_plug
- **Replay:** True
### Cursor Skills — Config (`lib_skill_config`)

- **Library:** `lib_skill_config`
- **Family:** operational_workflows
- **Capabilities:** Cursor settings, CLI config, and skill migration.
- **Authority:** assist, admin
- **Receipts:** per_plug
- **Replay:** True
### Cursor Skills — Subagent (`lib_skill_subagent`)

- **Library:** `lib_skill_subagent`
- **Family:** operational_workflows
- **Capabilities:** Subagent creation and dispatch patterns.
- **Authority:** assist
- **Receipts:** per_plug
- **Replay:** True
### HF Agent Skill — CLI (`lib_hf_cli`)

- **Library:** `lib_hf_cli`
- **Family:** data_workflows
- **Capabilities:** Hub CLI download/upload operations.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Datasets (`lib_hf_datasets`)

- **Library:** `lib_hf_datasets`
- **Family:** data_workflows
- **Capabilities:** Dataset repo creation and row streaming.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Dataset Viewer (`lib_hf_dataset_viewer`)

- **Library:** `lib_hf_dataset_viewer`
- **Family:** data_workflows
- **Capabilities:** Dataset Viewer API pagination and filters.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Evaluation (`lib_hf_evaluation`)

- **Library:** `lib_hf_evaluation`
- **Family:** data_workflows
- **Capabilities:** Eval tables and model card scores.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Jobs (`lib_hf_jobs`)

- **Library:** `lib_hf_jobs`
- **Family:** data_workflows
- **Capabilities:** Cloud GPU jobs and UV scripts.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Model Trainer (`lib_hf_model_trainer`)

- **Library:** `lib_hf_model_trainer`
- **Family:** data_workflows
- **Capabilities:** TRL SFT/DPO/GRPO training on HF Jobs.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Paper Publisher (`lib_hf_paper_publisher`)

- **Library:** `lib_hf_paper_publisher`
- **Family:** data_workflows
- **Capabilities:** Research paper pages on the Hub.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Tool Builder (`lib_hf_tool_builder`)

- **Library:** `lib_hf_tool_builder`
- **Family:** data_workflows
- **Capabilities:** Reusable HF API tool scripts.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Trackio (`lib_hf_trackio`)

- **Library:** `lib_hf_trackio`
- **Family:** data_workflows
- **Capabilities:** Training metrics and alerts.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### HF Agent Skill — Gradio (`lib_hf_gradio`)

- **Library:** `lib_hf_gradio`
- **Family:** data_workflows
- **Capabilities:** Gradio demo UIs.
- **Authority:** assist
- **Receipts:** none
- **Replay:** False
### Native — Jarvis Spatial (`lib_native_jarvis`)

- **Library:** `lib_native_jarvis`
- **Family:** operational_workflows
- **Capabilities:** Spatial reasoning, mystic, v9/v10, recipe, imagine lanes.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Native — Forge (`lib_native_forge`)

- **Library:** `lib_native_forge`
- **Family:** operational_workflows
- **Capabilities:** Forge build, patch, document vision, UI vision.
- **Authority:** execute, admin
- **Receipts:** per_plug
- **Replay:** True
### Native — Media (`lib_native_media`)

- **Library:** `lib_native_media`
- **Family:** creative_workflows
- **Capabilities:** Audio, video, image, beatbox, speakers, story forge.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Native — Governance (`lib_native_governance`)

- **Library:** `lib_native_governance`
- **Family:** knowledge_work
- **Capabilities:** Action, memory, narrative trust, forensic triangulation.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Native — Operator (`lib_native_operator`)

- **Library:** `lib_native_operator`
- **Family:** operational_workflows
- **Capabilities:** Ledger, replay, and operator decision surfaces.
- **Authority:** observe, assist, admin
- **Receipts:** per_plug
- **Replay:** True
### Native — Workspace (`lib_native_workspace`)

- **Library:** `lib_native_workspace`
- **Family:** business_workflows
- **Capabilities:** Workspace projects, game front door, world pack.
- **Authority:** assist, execute
- **Receipts:** per_plug
- **Replay:** True
### Workflow — Research Brief (`lib_workflow_research_brief`)

- **Library:** `lib_workflow_research_brief`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Research Brief.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — PDF to Chart (`lib_workflow_pdf_to_chart`)

- **Library:** `lib_workflow_pdf_to_chart`
- **Family:** data_workflows
- **Capabilities:** Governed workflow bundle: PDF to Chart.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Incident Triage (`lib_workflow_incident_triage`)

- **Library:** `lib_workflow_incident_triage`
- **Family:** operational_workflows
- **Capabilities:** Governed workflow bundle: Incident Triage.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Support Resolution (`lib_workflow_support_resolution`)

- **Library:** `lib_workflow_support_resolution`
- **Family:** business_workflows
- **Capabilities:** Governed workflow bundle: Support Resolution.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Creative Asset Package (`lib_workflow_creative_asset_package`)

- **Library:** `lib_workflow_creative_asset_package`
- **Family:** creative_workflows
- **Capabilities:** Governed workflow bundle: Creative Asset Package.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Safe Deploy (`lib_workflow_safe_deploy`)

- **Library:** `lib_workflow_safe_deploy`
- **Family:** operational_workflows
- **Capabilities:** Governed workflow bundle: Safe Deploy.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Editor Skill Assist (`lib_workflow_editor_skill_assist`)

- **Library:** `lib_workflow_editor_skill_assist`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Editor Skill Assist.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Spatial Reasoning Lane (`lib_workflow_spatial_reasoning_lane`)

- **Library:** `lib_workflow_spatial_reasoning_lane`
- **Family:** operational_workflows
- **Capabilities:** Governed workflow bundle: Spatial Reasoning Lane.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Contract Redline (`lib_workflow_contract_redline`)

- **Library:** `lib_workflow_contract_redline`
- **Family:** business_workflows
- **Capabilities:** Governed workflow bundle: Contract Redline.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Research to Slides (`lib_workflow_research_to_slides`)

- **Library:** `lib_workflow_research_to_slides`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Research to Slides.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Support Knowledge Article (`lib_workflow_support_knowledge_article`)

- **Library:** `lib_workflow_support_knowledge_article`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Support Knowledge Article.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Sales Proposal (`lib_workflow_sales_proposal`)

- **Library:** `lib_workflow_sales_proposal`
- **Family:** business_workflows
- **Capabilities:** Governed workflow bundle: Sales Proposal.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Data Quality Run (`lib_workflow_data_quality_run`)

- **Library:** `lib_workflow_data_quality_run`
- **Family:** data_workflows
- **Capabilities:** Governed workflow bundle: Data Quality Run.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Cloud Incident Response (`lib_workflow_cloud_incident_response`)

- **Library:** `lib_workflow_cloud_incident_response`
- **Family:** operational_workflows
- **Capabilities:** Governed workflow bundle: Cloud Incident Response.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Compliance Memo (`lib_workflow_compliance_memo`)

- **Library:** `lib_workflow_compliance_memo`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Compliance Memo.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Documentation Update (`lib_workflow_documentation_update`)

- **Library:** `lib_workflow_documentation_update`
- **Family:** knowledge_work
- **Capabilities:** Governed workflow bundle: Documentation Update.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Lead Follow Up (`lib_workflow_lead_follow_up`)

- **Library:** `lib_workflow_lead_follow_up`
- **Family:** business_workflows
- **Capabilities:** Governed workflow bundle: Lead Follow Up.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Finance Report (`lib_workflow_finance_report`)

- **Library:** `lib_workflow_finance_report`
- **Family:** business_workflows
- **Capabilities:** Governed workflow bundle: Finance Report.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Campaign Visual (`lib_workflow_campaign_visual`)

- **Library:** `lib_workflow_campaign_visual`
- **Family:** creative_workflows
- **Capabilities:** Governed workflow bundle: Campaign Visual.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Video Cut (`lib_workflow_video_cut`)

- **Library:** `lib_workflow_video_cut`
- **Family:** creative_workflows
- **Capabilities:** Governed workflow bundle: Video Cut.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Audio Cleanup (`lib_workflow_audio_cleanup`)

- **Library:** `lib_workflow_audio_cleanup`
- **Family:** creative_workflows
- **Capabilities:** Governed workflow bundle: Audio Cleanup.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Metrics Dashboard (`lib_workflow_metrics_dashboard`)

- **Library:** `lib_workflow_metrics_dashboard`
- **Family:** data_workflows
- **Capabilities:** Governed workflow bundle: Metrics Dashboard.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Data Cleanup (`lib_workflow_data_cleanup`)

- **Library:** `lib_workflow_data_cleanup`
- **Family:** data_workflows
- **Capabilities:** Governed workflow bundle: Data Cleanup.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — File Archive (`lib_workflow_file_archive`)

- **Library:** `lib_workflow_file_archive`
- **Family:** operational_workflows
- **Capabilities:** Governed workflow bundle: File Archive.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Weekly Plan (`lib_workflow_weekly_plan`)

- **Library:** `lib_workflow_weekly_plan`
- **Family:** personal_workflows
- **Capabilities:** Governed workflow bundle: Weekly Plan.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Journal to Knowledge (`lib_workflow_journal_to_knowledge`)

- **Library:** `lib_workflow_journal_to_knowledge`
- **Family:** personal_workflows
- **Capabilities:** Governed workflow bundle: Journal to Knowledge.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True
### Workflow — Habit Review (`lib_workflow_habit_review`)

- **Library:** `lib_workflow_habit_review`
- **Family:** personal_workflows
- **Capabilities:** Governed workflow bundle: Habit Review.
- **Authority:** assist, execute
- **Receipts:** full_chain
- **Replay:** True

