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

## Persistence (phase 2 — durable substrate store)

**Implemented at v1.26.1+ (phase 2).**

- Substrate workflow records persist under `AAIS_DATA_DIR/otem-execution/` (override: `AAIS_OTEM_EXECUTION_STORE_DIR`).
- Process restart rehydrates workflows from the durable store on `approve()` / `apply()` / `get_workflow()`.
- **Operator caveat:** If both memory and durable store lack the workflow id, reject the stale approval and re-run the OTEM handoff. Approve on a missing workflow returns **409** with an explicit message.

## Capability level (default 10)

- `AAIS_OTEM_CAPABILITY_LEVEL` (1–10, default **10**) sets OTEM ceiling and plan depth.
- Level **10** (`v10_governed`): chat lane stays **proposal-only**; execution ingress is **only** via workflow approvals (auto-enqueue when `workflow_handoff` is present).
- Levels below 10 disable auto-enqueue of execution approvals; level 5 maps to legacy `v5_frozen` ceiling.

## Hard Rules

- Operator approval required before apply
- Verification gate must pass
- No autonomous apply without Project Infi disposition
- Execution contexts are phase-gated separately from proposal contexts
