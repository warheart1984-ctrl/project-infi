# Platform Ledger v2 Contract

Authority: [PLATFORM_MEMBRANE_V5_SPEC.md](../../runtime/PLATFORM_MEMBRANE_V5_SPEC.md).

## Entry (`platform.platform_ledger_entry.v1`)

| Field | Notes |
|-------|-------|
| entry_id | Unique |
| org_id | Owner |
| kind | audit, mesh, webhook, attestation, usage, exchange, autopilot |
| prev_hash | Chain link |
| entry_hash | sha256(prev_hash + payload) |
| payload | Event body |
| created_at | ISO8601 |

## APIs (v48)

- `GET /v1/orgs/{org_id}/ledger/query?kind=&from=&to=&cursor=`
- `GET /v1/orgs/{org_id}/ledger/verify`

## CLI

`python -m platform ledger export --org X`

## Implementation

- [`platform/ledger/writer.py`](../../../platform/ledger/writer.py)
