# OTEM Execution Substrate Contract

Status: **active contract** (special review)

## Purpose

Durable OTEM workflow binding proposals to governed coding-organ apply stack.

## Workflow

`proposal` → `operator_approval` → `execution_preview` → `verification_gate` → `apply` → `ledger_record`

## Operator approval ingress (workflow shell)

- Session-bound OTEM turns with a `workflow_handoff` auto-enqueue a pending row on `GET /workflows/approvals`.
- Approval rows use `step_type: otem_execution_substrate` and payload `otem_execution_workflow_id` (substrate workflow id).
- Operator approves or rejects via existing `POST /workflows/approvals/{id}`; approve runs `substrate.approve()` then `substrate.apply()` without Celery resume.
- Shell workflow id: `otem-execution-substrate` (synthetic paused run for approval UI compatibility).

## Level 10 activation (no durable substrate required)

Safe activation means operators can complete the governed path in a **single running API process**:

1. OTEM chat turn produces `workflow_handoff` (proposal-only lane).
2. Pending approval row is created in the workflow DB.
3. Operator approves at `/workflows/approvals` in the **same process** that enqueued the handoff.
4. Substrate `approve()` + `apply()` run in memory.

Substrate workflow objects are **not** required to survive process restart for activation to be safe. Approval rows persist in the workflow DB; only the in-memory substrate graph is ephemeral until phase 2.

## Persistence (phase 2 — durable substrate)

**Release 31 (Body Completeness):** OTEM substrate workflows persist in SQLite (`otem_substrate_workflows` table, co-located with `JARVIS_DB_PATH`). Startup reconciliation rehydrates pending approvals; orphan rows are marked **stale** (fail-closed).

- Enable with `AAIS_OTEM_SUBSTRATE_USE_DB=1` (default)
- Approve after restart succeeds when durable record or `proposal_snapshot` in approval payload exists
- Missing substrate + missing snapshot → approval marked stale; approve returns **409**

**Operator caveat:** If reconciliation marks an approval stale, reject the row and re-run the OTEM handoff.

## Capability level (default 10)

- `AAIS_OTEM_CAPABILITY_LEVEL` (1–10, default **10**) sets OTEM ceiling and plan depth.
- Level **10** (`v10_governed`): chat lane stays **proposal-only**; execution ingress is **only** via workflow approvals (auto-enqueue when `workflow_handoff` is present).
- Levels below 10 disable auto-enqueue of execution approvals; level 5 maps to legacy `v5_frozen` ceiling.

## Hard Rules

- Operator approval required before apply
- Verification gate must pass
- No autonomous apply without Project Infi disposition
- Execution contexts are phase-gated separately from proposal contexts
