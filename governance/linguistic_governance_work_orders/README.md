# Linguistic governance work orders

Wave 14 operator execution posture for prescriptive queue items. Work orders are **not** auto-executed.

## Status lifecycle

| Status | Meaning |
|--------|---------|
| `pending` | Synced from queue; awaiting operator |
| `acknowledged` | Operator has seen the item |
| `completed` | Operator finished triage |
| `deferred` | Explicitly deferred |

## Commands

```bash
make linguistic-work-order-sync
python3 tools/governance/linguistic_work_order.py --gene capability_service_bridge --status acknowledged
python3 tools/governance/linguistic_work_order.py --summary
make linguistic-work-order-gate
```

## Policy

Pending SLA for top-N urgent items: `governance/linguistic_governance_cadence_policy.v1.json` → `max_pending_work_order_days`.
