# UCR Attestation Token (v0.1)

> **Normative spec:** [UCR_ATTESTATION_SPEC.md](UCR_ATTESTATION_SPEC.md)

**Engineering module:** `src/ucr/ucr_attestation.py`  
**Syscall:** `ucr_register(token: UCRAttestationToken) -> UCRRegisterResult`  
**Related:** `TRUST_ROOT_MEASUREMENT_CHAIN.md`, `H_CORRIDORS_BOOT_MANIFEST.md`, `BLK_UCR_V0`

## Purpose

UCR must present an attestation token before kernel registration (custody lock). The token binds a UCR build instance to the sealed boot measurement chain (`H_TRUST_ROOT`, `H_CORRIDORS`, `H_LAW_SPINE`).

## Token fields

| Field | Type | Description |
|-------|------|-------------|
| `token_id` | UUID | Unique attestation issuance id |
| `ucr_instance_id` | string | UCR runtime instance identifier |
| `build_fingerprint` | string | UCR build / artifact fingerprint |
| `law_key` | int (128-bit) | BLK_UCR_V0 law spine key |
| `trust_root` | string | `sha3-256:<hex>` — must equal sealed `H_TRUST_ROOT` |
| `corridors_hash` | string | `sha3-256:<hex>` — must equal sealed `H_CORRIDORS` |
| `law_spine_hash` | string | `sha3-256:<hex>` — must equal sealed `H_LAW_SPINE` |
| `issued_at` | ISO8601 UTC | Issuance timestamp |
| `expires_at` | ISO8601 UTC | Expiry; registration refused after this instant |
| `nonce` | bytes | Replay resistance nonce |
| `signature` | bytes | v0.1 placeholder digest over token fields |

## Validation pipeline

`ucr_register` evaluates in order:

1. **Boot sealed** — `is_trust_root_sealed()` and corridor loader `is_sealed()` → `1007` (`BOOT_NOT_SEALED`)
2. **Expiry** — `expires_at` > now (UTC) → `1008` (`TOKEN_EXPIRED`)
3. **Law key** — `validate_law_key(law_key)` per BLK_UCR_V0 → `1001` (`LAW_KEY_INVALID`)
4. **Signature** — non-empty and matches v0.1 placeholder digest → `1011` (`SIGNATURE_INVALID`)
5. **Trust root** — `token.trust_root == get_trust_root().h_trust_root` → `1006` (`TRUST_ROOT_MISMATCH`)
6. **Corridors** — `token.corridors_hash == sealed h_corridors` → `1009` (`CORRIDORS_HASH_MISMATCH`)
7. **Law spine** — `token.law_spine_hash == sealed h_law_spine` → `1010` (`LAW_SPINE_HASH_MISMATCH`)
8. **UCR context** — `to_ucr_context(sealed)` aligns with token trust root

On success: `RegisterOutcome.OK` with opaque `ucr_handle` (UUID).

On refusal: `RegisterOutcome.REFUSED` with numeric `reason_code` and `reason_detail`.

## Issuance helpers

- `issue_attestation_token(...)` — bind explicit measurements (tests, off-box issuer)
- `issue_attestation_from_sealed_trust(...)` — read measurements from `get_trust_root()` after early boot

## Trust root chain integration

```
Early boot → seal TrustRoot → issue UCRAttestationToken → ucr_register
                                      ↓
                            compare to get_trust_root()
                                      ↓
                         OK → ucr_handle (registration custody)
```

Post-registration, governed syscalls (e.g. `cog_act_commit`) continue to require sealed corridors and `require_governed_mode` alignment with the same trust root.

## Refusal codes

| Code | Symbol | Meaning |
|------|--------|---------|
| `1001` | `LAW_KEY_INVALID` | BLK_UCR_V0 validation failed |
| `1006` | `TRUST_ROOT_MISMATCH` | Token `trust_root` ≠ sealed `H_TRUST_ROOT` |
| `1007` | `BOOT_NOT_SEALED` | Trust root or corridor registry not sealed |
| `1008` | `TOKEN_EXPIRED` | `expires_at` in the past |
| `1009` | `CORRIDORS_HASH_MISMATCH` | Token `corridors_hash` ≠ sealed `H_CORRIDORS` |
| `1010` | `LAW_SPINE_HASH_MISMATCH` | Token `law_spine_hash` ≠ sealed `H_LAW_SPINE` |
| `1011` | `SIGNATURE_INVALID` | Missing or incorrect v0.1 placeholder signature |

## v0.1 assumptions

- Signature is a deterministic `sha3-256` digest over canonical token fields (`_placeholder_signature`); not asymmetric crypto yet.
- One successful registration stores `ucr_handle` in-process; tests use `reset_ucr_registration_for_tests()`.
