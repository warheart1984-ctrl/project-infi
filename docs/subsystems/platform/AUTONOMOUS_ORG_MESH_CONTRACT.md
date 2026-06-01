# Autonomous Org Mesh Contract v1

Authority: [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

## Purpose

Policy-bound operator routing automation (v41–v42). **Not** Stage 1 goal invention (Class I) or hidden actuation (Class III).

## routing_policy (org field)

```json
{
  "auto_assign_from_queue": true,
  "suggest_on_call_on_drift": true,
  "max_auto_assignments_per_run": 5
}
```

## APIs

- `PUT /v1/orgs/{org_id}/mesh/routing-policy`
- `GET /v1/orgs/{org_id}/mesh/routing-policy`
- `POST /v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run|apply`

## autopilot_run receipt

Append-only `autopilot_runs` with `actions[]`, `mode`, `claim_label`.

## Implementation

- [`platform/mesh/autopilot.py`](../../../platform/mesh/autopilot.py)
