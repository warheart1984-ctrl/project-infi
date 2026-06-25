# Operator Kernel — interim Coding Organs path

This document describes how **patch approval** works today. It is the interim
implementation of the Coding Organs surface: the agent proposes a diff, the
operator approves or rejects, and only then does the kernel write to the
workspace.

Full **Layer 3** (organs REST + ledger + recovery) is not implemented yet.

## Engineering vs mythic names

| Engineering | Mythic (docs only) |
|-------------|-------------------|
| `OperatorKernel` | Operator Surface / kernel |
| `write_patch` tool | patch organ |
| `patch_require_approval` | governed apply gate |
| `POST .../approve_patch` | operator approve |

## Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `OPERATOR_PATCH_REQUIRE_APPROVAL` | `1` (on) | Agent stops after `patch_preview`; disk apply waits for approve |
| `OPERATOR_PATCH_REQUIRE_APPROVAL=0` | off | Legacy auto-apply inside the agent loop (not recommended for Surface) |

Config is read in `operator_kernel/config.py` via `patch_require_approval_enabled()`.

## Agent loop (when approval is on)

1. Planner selects `write_patch`.
2. Governance allows the tool.
3. Kernel emits SSE:
   - `tool_called` (`write_patch`)
   - `patch_preview` (path + diff)
   - `tool_result` with `pending_approval: true`
4. Task meta: `status: awaiting_approval`, `pending_patch: { path, diff }`.
5. SSE `task_completed` with `status: awaiting_approval`.
6. **No** call to `apply_unified_diff` until approve.

## Operator actions

### HTTP API

| Method | Path | Body | Result |
|--------|------|------|--------|
| `POST` | `/agent/tasks/{task_id}/approve_patch` | — | Applies pending diff; `status: completed` |
| `POST` | `/agent/tasks/{task_id}/reject_patch` | `{ "reason": "..." }` optional | Clears pending; `status: rejected` |
| `POST` | `/agent/tasks/{task_id}/message` | — | **409** while `awaiting_approval` |
| `POST` | `/agent/tasks/{task_id}/cancel` | — | Clears pending; `status: cancelled` |

Implementation: `operator_kernel/patch_approval.py`, routes in `operator_kernel/main.py`.

### Operator Surface (Vite)

When the activity stream shows **Awaiting approval**, use **Approve** or **Reject**.
Those call the same endpoints as above (`operator-surface/src/lib/api.ts`).

## SSE event sequence (happy path)

```
task_started
assistant_message / plan_updated
tool_called (write_patch)
patch_preview
tool_result (pending_approval)
task_completed (awaiting_approval)
--- operator approves ---
patch_applied
tool_result (applied)
task_completed (completed)
```

Follow-up messages are allowed only after `completed` (or after reject/cancel).

## Validation

- Unit tests: `tests/operator_kernel/test_agent_api.py` (approve/reject/409/cancel)
- E2E: `python scripts/run_operator_e2e_validation.py` (approve before file check and follow-up)

## Related

- [Cursor MCP](./cursor-mcp.md) — expose kernel to Cursor via MCP
- Future: Layer 3 organs REST, ledger, and recovery (not in this interim path)
