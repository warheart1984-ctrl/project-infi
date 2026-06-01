# Platform API Contract v5

Authority: [PLATFORM_BLUEPRINT.md](./PLATFORM_BLUEPRINT.md), [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

Includes all v4 routes. Sixth arc additions:

### Autonomous Org Mesh (v41–v42)

- `PUT/GET /v1/orgs/{org_id}/mesh/routing-policy`
- `POST /v1/orgs/{org_id}/mesh/autopilot/run?mode=dry_run|apply`

### Global Proof Network (v43–v44)

- `POST /v1/proof/witnesses/enroll`
- `GET /v1/proof/witnesses`
- `GET /v1/proof/network/graph?job_id=`

### Inter-Membrane Exchange (v45–v46)

- `POST /v1/tenants/{tenant_id}/exchange/listings/{listing_id}/transfer`
- `POST /v1/exchange/outbound`
- `POST /v1/exchange/inbound`
- `GET /v1/exchange/peers`

### Platform Ledger v2 (v47–v48)

- `GET /v1/orgs/{org_id}/ledger/query`
- `GET /v1/orgs/{org_id}/ledger/verify`
- `GET /v1/orgs/{org_id}/ledger/cognition-overlay` (read-only UGR claims)

### Sovereign Runtime (v49–v50)

- `GET/PUT /v1/orgs/{org_id}/sovereign/profile`
- `POST /v1/orgs/{org_id}/sovereign/export-pack`

See v4 contract sections for mesh, marketplace, proof, events, sovereign v1 routes.

## Errors

| Code | Meaning |
|------|---------|
| 401 | Invalid credentials |
| 403 | Forbidden / MA-13 |
| 404 | Not found |
| 422 | Validation error |
