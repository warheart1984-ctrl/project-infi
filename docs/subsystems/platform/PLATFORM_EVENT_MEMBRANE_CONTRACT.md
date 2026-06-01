# Platform Event Membrane Contract v1

Authority: [PLATFORM_MEMBRANE_V4_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V4_SPEC.md).

## Purpose

Outbound operator-configured notifications for job, proof, and mesh state changes. **Observe/notify only** (MA-13 Class III if cross-org delivery).

## Subscription

Schema: `platform/schemas/webhook_subscription.v1.json`.

| Field | Required | Notes |
|-------|----------|-------|
| `subscription_id` | yes | Stable id |
| `org_id` | yes | Owning org |
| `url` | yes | HTTPS recommended |
| `event_types` | yes | Subset of allowed types |
| `secret` | stored hashed | HMAC signing key |

### Allowed event types (v31)

- `job.status`
- `proof.status`
- `mesh.event`

## Delivery (v32)

- POST JSON body to `url`
- Header `X-Platform-Signature: sha256=<hmac hex>` over raw body
- Ledger: `webhook_deliveries` with `status`, `attempt`, `response_code`
- Max **3** attempts with exponential backoff (1s, 4s, 16s)

## APIs

- `POST /v1/orgs/{org_id}/webhooks`
- `GET /v1/orgs/{org_id}/webhooks`
- `DELETE /v1/orgs/{org_id}/webhooks/{subscription_id}`

## Implementation

- [`platform/events/subscriptions.py`](../../../platform/events/subscriptions.py)
- [`platform/events/dispatch.py`](../../../platform/events/dispatch.py)
