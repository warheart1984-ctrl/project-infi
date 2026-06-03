# URG MissionReceipt Schema (v1.2)

Status: **v1.5 / runtime 1.5**

Authority: `docs/contracts/URG_STACK_DOCTRINE.md`, `docs/contracts/URG_MISSION_CONTRACT.md`, `schemas/urg_mission_receipt.v1.json`.

## MissionReceipt record

```text
MissionReceipt {
  schema_version:     "1.2"
  urg_version:        URG mission runtime version (e.g. "1.5")
  invariant_version:  cloud invariant set version (e.g. "1.5")
  cloud_identity_hash: I_cloud(M)
  boundary_digest:    SHA256(B_cloud)
  mission_id:         UUID (URG-issued at ingress)
  mission_slug:       optional human-readable alias
  goal_hash:          SHA256(semantic goal + constraints)
  organs:             [{ organ_id, provider, contract_version, ceiling, region_id, rail }]
  invariant_digest:   SHA256(active cloud invariant set)
  ledger_root:        Merkle root of governed transitions
  operator_sig:       { operator_id, tenant_id, aais_instance_id, stamped_at, operator_mac, operator_key_id }
  outcome:            completed | failed | vetoed
  failure_reason:     diagnostic enum (required when outcome != completed)
  urg_key_id:         URG signing key identifier
  receipt_sig:        URG HMAC over canonical receipt (excluding receipt_sig)
  issued_at:          unix timestamp
}
```

## failure_reason

| Code | When |
|------|------|
| `UNFULFILLABLE_CONSTRAINTS` | Cloud invariant hard_fail on region, cost, risk, domain, rail |
| `NO_ADMISSIBLE_ORGAN` | No organ resolved for step (auto-assign miss) |
| `GATE_REJECTION` | Ingress rejected, empty mission, bypass denied |
| `OPERATOR_VETO` | Explicit `operator_veto` or `reject_reason=operator_veto` |
| `RUNTIME_ERROR` | AAIS bridge block, duplicate step_id, other runtime blocks |

## Relationship to GCM

| MissionReceipt field | GCM tuple |
|----------------------|-----------|
| `goal_hash` | Goal \(G\) + Constraints \(C\) |
| `organs` | Participating organs \(O\) |
| `invariant_digest` | Invariant set \(I\) |
| `ledger_root` | Ledger trail \(L\) |

GCM also exposes `participating_aais_instances[]` for multi-AAIS routing audit (not duplicated on MissionReceipt v1.1).

## Outcome mapping

| Runtime `status` | `outcome` |
|------------------|-----------|
| `ok` | `completed` |
| `blocked` | `failed` |
| `rejected` | `vetoed` |

## Dual signing

1. **operator_sig.operator_mac** — HMAC-SHA256 with operator key over operator-bound fields (`operator_id`, `tenant_id`, `aais_instance_id`, `stamped_at`, `goal_hash`, `operator_key_id`).
2. **receipt_sig** — HMAC-SHA256 with URG key over full MissionReceipt canonical body (excluding `receipt_sig` and `receipt_algorithm`).

Verification order (fail closed):

1. Recompute `goal_hash`, `invariant_digest`, `ledger_root` from source artifacts
2. Verify `operator_sig.operator_mac`
3. Verify `receipt_sig`
4. Recompute `cloud_identity_hash` and `boundary_digest` from ingress manifold

## Persistence (v1.4)

Signed receipts append to `{AAIS_RUNTIME_DIR}/urg/receipts.jsonl`. Retrieve via `GET /api/ugr/mission/receipt/{mission_id}`.

## API surface

`POST /api/ugr/mission/run` returns:

- `mission_receipt` — legacy v1.2 flat receipt (backward compatible)
- `mission_receipt_schema` — full MissionReceipt v1.1 object

## Implementation

| Module | Path |
|--------|------|
| Builders | `src/ugr/mission/mission_receipt.py` |
| Merkle | `src/ugr/mission/ledger_merkle.py` |
| Signing | `src/ugr/mission/receipt_signing.py` |
| Store | `src/ugr/mission/mission_receipt_store.py` |
| AAIS routing | `src/ugr/mission/aais_instance_registry.py` |

## Keys

| Key | Env | File | Key ID |
|-----|-----|------|--------|
| Operator | `URG_OPERATOR_RECEIPT_KEY` | `.runtime/operators/{id}/receipt-secret.json` | `key_id` field or `env:URG_OPERATOR_RECEIPT_KEY` |
| URG | `URG_RECEIPT_SIGNING_KEY` | `.runtime/urg/receipt-signing-secret.json` | `key_id` field or `env:URG_RECEIPT_SIGNING_KEY` |
