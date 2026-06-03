# v1.26.0 — OTEM Execution Approval Bridge

## Summary

- Wires session-bound OTEM **workflow handoff** into existing **Workflow Approvals** (`/workflows/approvals`).
- **Approve** runs OTEM execution substrate `approve()` + `apply()` without Celery resume.
- Dashboard shows a link when execution approval is pending.
- Pauses automatic **AI Factory** and **CoGOS RC** GitHub workflows (`workflow_dispatch` only) to stop notification spam from failing runs.

## Verification

```bash
python -m pytest tests/test_otem_execution_approval_bridge.py -q
make otem-execution-substrate-gate
```

Full notes: [docs/releases/v1.26.0-release30-otem-execution-approval-bridge.md](v1.26.0-release30-otem-execution-approval-bridge.md) · [CHANGELOG.md](../../CHANGELOG.md) §1.26.0
