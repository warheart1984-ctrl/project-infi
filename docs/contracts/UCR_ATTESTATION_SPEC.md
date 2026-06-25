# UCR Attestation Specification v0.1 (DRAFT)

**Status:** DRAFT  
**Engineering module:** `src/ucr/ucr_attestation.py`  
**Syscall:** `ucr_register(token: UCRAttestationToken) -> UCRRegisterResult`  
**Related:** [TRUST_ROOT_SPEC.md](TRUST_ROOT_SPEC.md), [TRUST_ROOT_MEASUREMENT_CHAIN.md](TRUST_ROOT_MEASUREMENT_CHAIN.md), [H_CORRIDORS_BOOT_MANIFEST.md](H_CORRIDORS_BOOT_MANIFEST.md), `BLK_UCR_V0`

## Purpose

Before UCR may enter governed custody, it must present an **UCRAttestationToken** that binds a runtime instance and build fingerprint to the kernel's sealed boot measurements (`H_TRUST_ROOT`, `H_CORRIDORS`, `H_LAW_SPINE`). `ucr_register` is the sole registration syscall; success yields an opaque `ucr_handle`.

## Types

### `UCRAttestationToken`

| Field | Wire type (v0.1) | Description |
|-------|------------------|-------------|
| `token_id` | UUID | Unique issuance id |
| `ucr_instance_id` | string | UCR runtime instance identifier |
| `build_fingerprint` | string | UCR build / artifact fingerprint |
| `law_key` | u128 (Python `int`) | BLK_UCR_V0 law spine key |
| `trust_root` | measurement string | `sha3-256:<hex>` — sealed `H_TRUST_ROOT` |
| `corridors_hash` | measurement string | `sha3-256:<hex>` — sealed `H_CORRIDORS` |
| `law_spine_hash` | measurement string | `sha3-256:<hex>` — sealed `H_LAW_SPINE` |
| `issued_at` | ISO8601 UTC | Issuance timestamp |
| `expires_at` | ISO8601 UTC | Expiry instant (registration refused at or after) |
| `nonce` | bytes | Replay resistance (spec u64; v0.1 accepts arbitrary bytes, default 32-byte digest) |
| `signature` | bytes | v0.1 placeholder HMAC-like digest over canonical fields |

### `UCRRegisterResult`

| Field | Type | When set |
|-------|------|----------|
| `outcome` | `RegisterOutcome` | Always: `OK` or `REFUSED` |
| `ucr_handle` | UUID (v0.1) | `OK` only — opaque registration handle |
| `reason_code` | int | `REFUSED` only |
| `reason_detail` | string | `REFUSED` only |
| `metadata` | dict | `OK` only — diagnostic refs |

## `ucr_register` contract

| | |
|---|---|
| **Inputs** | `token: UCRAttestationToken` |
| **Outputs** | `UCRRegisterResult` with `outcome=OK` and `ucr_handle`, or `outcome=REFUSED` with `reason_code` / `reason_detail` |
| **Constraints** | Kernel trust root and corridor loader MUST be sealed before registration; token measurements MUST match `get_trust_root()`; `validate_law_key` MUST pass; signature MUST match v0.1 placeholder |
| **Failure modes** | See refusal codes below; `TypeError` if `token` is not `UCRAttestationToken` |

### Validation order

1. Boot sealed — `is_trust_root_sealed()` and `is_sealed()` → `1007`
2. Expiry — `expires_at` ≤ now (UTC) → `1008`
3. Law key — `validate_law_key(law_key)` → `1001`
4. Signature — non-empty and matches `_placeholder_signature` → `1011`
5. Trust root — `token.trust_root == sealed.h_trust_root` → `1006`
6. Corridors — `token.corridors_hash == sealed.h_corridors` → `1009`
7. Law spine — `token.law_spine_hash == sealed.h_law_spine` → `1010`
8. UCR context — `to_ucr_context(sealed).h_trust_root == token.trust_root` → `1006`

### Refusal codes

| Code | Symbol | Meaning |
|------|--------|---------|
| `1001` | `LAW_KEY_INVALID` | BLK_UCR_V0 validation failed |
| `1006` | `TRUST_ROOT_MISMATCH` | Token trust root ≠ sealed `H_TRUST_ROOT` or context mismatch |
| `1007` | `BOOT_NOT_SEALED` | Trust root or corridor registry not sealed |
| `1008` | `TOKEN_EXPIRED` | `expires_at` in the past |
| `1009` | `CORRIDORS_HASH_MISMATCH` | Token corridors hash ≠ sealed `H_CORRIDORS` |
| `1010` | `LAW_SPINE_HASH_MISMATCH` | Token law spine hash ≠ sealed `H_LAW_SPINE` |
| `1011` | `SIGNATURE_INVALID` | Missing or incorrect v0.1 placeholder signature |

## Issuance helpers

| Function | Inputs | Outputs | Constraints |
|----------|--------|---------|-------------|
| `issue_attestation_token(...)` | Explicit measurements + metadata | `UCRAttestationToken` | All measurement fields must be `sha3-256:` prefixed; non-empty `ucr_instance_id`, `build_fingerprint` |
| `issue_attestation_from_sealed_trust(...)` | `ucr_instance_id`, `build_fingerprint`, `expires_at`, optional `law_key` | `UCRAttestationToken` | `get_trust_root()` MUST be sealed; reads `h_trust_root`, `h_corridors`, `h_law_spine` from sealed state |

## Signature (v0.1 placeholder)

Domain separator: `AAES-UCR-ATTEST-v1\x00`

Canonical payload: domain + `|`-joined UTF-8 segments:

`token_id`, `ucr_instance_id`, `build_fingerprint`, `law_key` (032x hex), `trust_root`, `corridors_hash`, `law_spine_hash`, `issued_at`, `expires_at`, `nonce` (raw bytes).

Signature = `sha3-256(payload)` (32 raw bytes). Not asymmetric crypto in v0.1.

## Boot integration

```
run_early_boot → seal TrustRoot → issue_attestation_from_sealed_trust → ucr_register
```

Post-registration, governed syscalls (e.g. `cog_act_commit`) require the same sealed trust root and `require_governed_mode` alignment.

## Test hooks

- `reset_ucr_registration_for_tests()` — clears in-process registration state
- `get_registered_ucr_handle()` — returns last successful handle or `None`

## Implementation notes (v0.1)

- `ucr_handle` is a UUID in the reference implementation; spec allows u64 (hash of UUID or monotonic int).
- `nonce` defaults to a 32-byte sha3-256 digest when omitted at issuance; wire u64 is representable as 8-byte big-endian in future revisions.
