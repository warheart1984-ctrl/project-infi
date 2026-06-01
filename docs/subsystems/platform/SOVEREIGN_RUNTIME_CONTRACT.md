# Sovereign Runtime Contract v1

Authority: [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

## sovereign_profile (org field)

```json
{
  "mode": "hosted",
  "data_residency": "us",
  "export_bundle_schedule": "",
  "runner_endpoint": ""
}
```

Modes: `hosted` | `self_hosted`.

## APIs (v49–v50)

- `GET/PUT /v1/orgs/{org_id}/sovereign/profile`
- `POST /v1/orgs/{org_id}/sovereign/export-pack`

Export pack: JSON manifest + CSV blobs (audit, ledger, attestations, usage) with HMAC manifest signature.

## Residency

Enforced in admission policy when profile.data_residency set.

## Implementation

- [`platform/sovereign/profile.py`](../../../platform/sovereign/profile.py)
- [`platform/sovereign/export_pack.py`](../../../platform/sovereign/export_pack.py)
