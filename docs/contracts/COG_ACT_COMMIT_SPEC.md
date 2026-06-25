# Cognitive Act Commit Syscall Specification v0.1 (DRAFT)

**Status:** DRAFT  
**Engineering module:** `src/ucr/cog_act_commit.py`  
**Syscall:** `cog_act_commit(act_id, law_key, authority_token, act_payload, ledger_ref, metadata) -> CommitResult`  
**Related:** [UCR_ATTESTATION_SPEC.md](UCR_ATTESTATION_SPEC.md), [TRUST_ROOT_SPEC.md](TRUST_ROOT_SPEC.md), [CORRIDOR_LOADER_SPEC_v0.1.md](CORRIDOR_LOADER_SPEC_v0.1.md), `BLK_UCR_V0`

## Purpose

`cog_act_commit` is the sole governed boundary for committing a cognitive act into kernel state. Every admission path validates law key, authority envelope, corridor permissions, act/ledger integrity, producer trust, and safety veto before incrementing `state_version` and emitting a `DecisionRecord`.

## Types

### `CommitResult`

| Field | Type | When set |
|-------|------|----------|
| `outcome` | `CommitOutcome` | `OK`, `REFUSED`, or `ESCALATED` |
| `receipt_id` | UUID | `OK` |
| `state_version` | int | `OK` — monotonic post-commit version |
| `reason_code` | int | `REFUSED` / `ESCALATED` |
| `reason_detail` | string | `REFUSED` / `ESCALATED` |
| `escalation_id` | UUID | `ESCALATED` (reserved) |
| `metadata` | dict | `OK` — corridor refs |

### `DecisionRecord`

Append-only audit row per commit attempt (including refusals).

## `cog_act_commit` contract

| | |
|---|---|
| **Inputs** | `act_id: UUID`, `law_key: int`, `authority_token: bytes`, `act_payload: bytes`, `ledger_ref: bytes`, `metadata: bytes` |
| **Outputs** | `CommitResult` |
| **Constraints** | Corridor loader and trust root MUST be sealed; governed mode MUST align; UCR instance MUST be registered via `ucr_register`; authority envelope MUST validate against corridor; act MUST match `act_id` and `ledger_ref`; producer MUST be trusted; safety veto MUST be clear |
| **Failure modes** | Refusal with numeric `reason_code` (no exception on governed refusal) |

### Validation order

1. Sealed corridors + trust root → `1006` (`ERR_TRUST_ROOT_MISMATCH`)
2. Non-zero law key + `validate_law_key` → `1001` (`INVALID_LAW_KEY`)
3. `require_governed_mode` alignment → `1006`
4. Registered UCR handle present (`get_registered_ucr_handle`) → `1012` (`UCR_NOT_REGISTERED`)
5. Authority token decode + `validate_envelope` → `1002` (`INVALID_AUTHORITY`)
6. Corridor lookup + envelope/corridor rules → `1005` / `1002`
7. Act payload deserialize + `act_id` / `ledger_ref` match → `1003` (`ACT_LEDGER_MISMATCH`)
8. Trusted producer → `1004` (`UNTRUSTED_PRODUCER`)
9. Safety veto → `2001` (`SAFETY_VETO`)
10. Tool/memory/risk permissions vs admission → `1002`

### Refusal codes

| Code | Symbol | Meaning |
|------|--------|---------|
| `1001` | `INVALID_LAW_KEY` | Zero or BLK_UCR_V0 validation failure |
| `1002` | `INVALID_AUTHORITY` | Envelope decode/validation or permission denial |
| `1003` | `ACT_LEDGER_MISMATCH` | Act id or ledger ref mismatch |
| `1004` | `UNTRUSTED_PRODUCER` | Producer not in trusted set |
| `1005` | `ERR_CORRIDOR_NOT_FOUND` | Envelope corridor id absent from sealed set |
| `1006` | `ERR_TRUST_ROOT_MISMATCH` | Boot not sealed or governed-mode measurement mismatch |
| `1012` | `UCR_NOT_REGISTERED` | No successful `ucr_register` for this boot session |
| `2001` | `SAFETY_VETO` | Act or admission flagged vetoed |

## Supporting operations

| Function | Purpose |
|----------|---------|
| `require_sealed_corridors()` | Pre-check; returns `CommitResult` refusal or `None` |
| `register_trusted_producer(producer_id)` | Extend trusted producer set (v0.1 default: `ucr.default`) |
| `get_decision_records()` | Read audit trail |
| `reset_commit_state_for_tests()` | Reset version, records, producers |

## Trust integration

```
run_early_boot → seal TrustRoot → ucr_register (required)
                                      ↓
                            cog_act_commit requires:
                              - is_sealed() + is_trust_root_sealed()
                              - require_governed_mode(kernel, UCR views)
                              - get_registered_ucr_handle() is not None
```

Both `ucr_register` and `cog_act_commit` depend on the same sealed trust root; commit is refused until registration succeeds.

## v0.1 assumptions

- Authority tokens are JSON-encoded envelopes (`authority_envelope.py`).
- Act payloads are JSON with admission metadata (`act_codec.py`).
- In-process trusted producer registry; no persistent store.
- `ESCALATED` outcome reserved; not emitted in v0.1 reference implementation.
