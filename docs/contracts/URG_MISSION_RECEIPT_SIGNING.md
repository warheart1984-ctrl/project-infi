# URG Mission Receipt Signing

Status: **v1.3.1 / runtime v1.4** (dual signing + MissionReceipt schema v1.1)

Authority: `docs/contracts/URG_MISSION_CONTRACT.md`, `docs/contracts/URG_STACK_DOCTRINE.md`, `docs/contracts/URG_MISSION_RECEIPT_SCHEMA.md`.

## MissionReceipt v1.3

Structured receipt: `mission_receipt_schema` on API responses. See [URG_MISSION_RECEIPT_SCHEMA.md](URG_MISSION_RECEIPT_SCHEMA.md).

| Signature | Key | Covers |
|-----------|-----|--------|
| `operator_sig.operator_mac` | Operator (`URG_OPERATOR_RECEIPT_KEY`) | operator identity + `goal_hash` + `operator_key_id` |
| `receipt_sig` | URG (`URG_RECEIPT_SIGNING_KEY`) | full MissionReceipt minus `receipt_sig` |

```python
from src.ugr.mission.receipt_signing import verify_mission_receipt_v2

ok, reason = verify_mission_receipt_v2(
    receipt_schema,
    gcm=gcm,
    ingress=ingress,
    ledger_rows=ledger_rows,
    operator_key=op_key,
    urg_key=urg_key,
)
```

## Legacy v1.2 flat receipt

## Algorithms

| Algorithm | When | Fields |
|-----------|------|--------|
| `hmac-sha256` | Operator receipt key configured | `content_digest`, `receipt_mac`, `receipt_signature` (= mac) |
| `sha256-content-only` | No key (dev fallback) | `content_digest`, `receipt_signature` (= digest) |

## Key resolution

**Operator**

1. `URG_OPERATOR_RECEIPT_KEY` environment variable
2. `.runtime/operators/{operator_id}/receipt-secret.json`

**URG authority**

1. `URG_RECEIPT_SIGNING_KEY` environment variable
2. `.runtime/urg/receipt-signing-secret.json`

## Canonical payload

Signed body includes: GCM version, mission_id, status, goal, constraints, participating_organs, invariant verdict, ledger action ids, ingress stamp hash, and `aais_step_summaries_digest` when AAIS bridge ran.

## Verification

```python
from src.ugr.mission.receipt_signing import verify_mission_receipt

ok, reason = verify_mission_receipt(receipt, gcm, ingress=ingress, key=test_key)
```

Fail closed: any digest or MAC mismatch returns `False`.

## Implementation

`src/ugr/mission/receipt_signing.py`
