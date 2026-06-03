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

## Persistence

- Substrate workflow state remains **in-process** (phase 2: durable store). Restart between enqueue and approve loses the substrate workflow until persistence lands.

## Hard Rules

- Operator approval required before apply
- Verification gate must pass
- No autonomous apply without Project Infi disposition
- Execution contexts are phase-gated separately from proposal contexts
