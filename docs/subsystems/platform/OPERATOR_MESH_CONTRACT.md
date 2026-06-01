# Operator Mesh Contract v1

Authority: [PLATFORM_MEMBRANE_V3_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V3_SPEC.md).

## Purpose

Coordinate multiple human operators per org on platform jobs without usurping Stage 1 authority (MA-13).

## Entities

| Entity | Schema | API |
|--------|--------|-----|
| Presence | `platform/schemas/operator_presence.v1.json` | `POST /v1/orgs/{org_id}/mesh/presence` |
| Assignment | `platform/schemas/job_assignment.v1.json` | `POST /v1/jobs/{job_id}/assign?org_id=`, `DELETE .../assign` |
| Mesh event | `platform/schemas/mesh_event.v1.json` | `GET /v1/orgs/{org_id}/mesh/events`, `GET .../mesh/events/stream` (v21 SSE) |
| On-call | `platform/schemas/on_call_schedule.v1.json` | `PUT /v1/orgs/{org_id}/on-call`, `GET .../on-call/current` |
| Handoff | `platform/schemas/handoff_bundle.v1.json` | `POST /v1/orgs/{org_id}/mesh/handoff`, `GET .../handoff/{bundle_id}` |
| Mesh policy | org field `mesh_policy` | `PUT /v1/orgs/{org_id}/mesh/policy` (v22) |

## Rules

1. Assignment **does not** call `JobRegistry.create_job`.
2. Mesh events are **append-only**.
3. Presence heartbeat TTL default **300s** (`list_online_operators`).
4. Cross-org assignment is **forbidden** (Class III).
5. Handoff may include `runbook_ref` (v22) — documentation pointer only, no actuation.

## v21 — SSE stream

`GET /v1/orgs/{org_id}/mesh/events/stream` returns `text/event-stream` with JSON event payloads.

## v22 — Mesh policy

Org `mesh_policy` JSON:

```json
{
  "max_assignments_per_operator": 10,
  "require_on_call_for_drift_investigation": true
}
```

Evaluated at admission for `slingshot.launch` via `mesh_blocks_slingshot`.

## v3 — Retention and assignment queue (v37–v38)

### Event retention

`mesh_policy.event_retention_days` (default 30). Compaction via [`platform/mesh/retention.py`](../../../platform/mesh/retention.py).

### Cursor pagination

`GET /v1/orgs/{org_id}/mesh/events?cursor=<event_id>&limit=50` — events after cursor.

### Assignment queue

Org field `assignment_queue`: ordered `principal_id` list.

- `PUT /v1/orgs/{org_id}/mesh/queue` — set queue
- `GET /v1/orgs/{org_id}/mesh/queue`
- Assign without `assignee_principal_id` dequeues next principal

## Implementation

- [`platform/mesh/`](../../../platform/mesh/)
