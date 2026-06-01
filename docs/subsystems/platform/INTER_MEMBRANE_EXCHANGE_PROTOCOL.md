# Inter-Membrane Exchange Protocol (IMXP) v1

Authority: [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

## Envelope (`platform.membrane_envelope.v1`)

Signed payload: `{ envelope_version, tenant_id, source_org_id, target_org_id, kind, body, consent_id, signature }`.

Signing: HMAC-SHA256 with `PLATFORM_EXCHANGE_SECRET` or org `exchange_secret`.

## v45 — Intra-tenant

- `POST /v1/tenants/{tenant_id}/exchange/listings/{listing_id}/transfer`
- Body: `{ target_org_id, consent_by }`
- Same `ugr_tenant_id` only

## v46 — Peer membranes

Table `platform_peers`: `{ peer_id, base_url, public_key, status }`.

- `POST /v1/exchange/outbound` — push to peer
- `POST /v1/exchange/inbound` — verify + apply (platform_admin)
- Cross-tenant requires `dual_consent` on envelope

## Implementation

- [`platform/exchange/`](../../../platform/exchange/)
