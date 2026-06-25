# Trust Root Specification v0.1 (DRAFT)

**Status:** DRAFT  
**Engineering modules:** `src/ucr/trust_root.py`, `src/ucr/kernel_boot.py`, `src/ucr/boot_manifest.py`, `src/ucr/law_spine_pack.py`, `src/ucr/corridor_loader.py`  
**Normative detail:** [TRUST_ROOT_MEASUREMENT_CHAIN.md](TRUST_ROOT_MEASUREMENT_CHAIN.md) (measurement formulas, examples, fixture hashes)

## Purpose

Bind kernel image, law spine, corridor registry, and boot manifest into a single sealed **H_TRUST_ROOT** digest. UCR governed mode and attestation registration refuse unless kernel and UCR views agree on this chain.

## Types

### `TrustRoot`

| Field | Type | Description |
|-------|------|-------------|
| `hash_alg` | `HashAlg` | `sha3-256` (default) or `blake3-256` |
| `h_kernel_image` | measurement string | Kernel binary digest |
| `h_law_spine` | measurement string | Law spine pack digest |
| `h_corridors` | measurement string | Trusted corridor set digest |
| `h_boot_manifest` | measurement string | Self-excluding boot manifest digest |
| `h_trust_root` | measurement string | Composite trust root digest |

### `UCRTrustContext`

UCR-facing subset: `hash_alg`, `h_law_spine`, `h_corridors`, `h_trust_root`.

## Measurement wire format

```
sha3-256:<lowercase_hex_64_chars>
```

## `compute_h_trust_root` contract

| | |
|---|---|
| **Inputs** | `h_kernel_image`, `h_law_spine`, `h_corridors`, `h_boot_manifest` (measurement strings), optional `hash_alg` |
| **Outputs** | `h_trust_root` measurement string |
| **Constraints** | Concat order fixed: KERNEL → LAW_SPINE → CORRIDORS → BOOT_MANIFEST as 32 raw bytes each; prefixed by domain `AAES-TRUST-ROOT-v1\x00` |
| **Failure modes** | `ValueError` on invalid measurement format |

## `run_early_boot` contract

| | |
|---|---|
| **Inputs** | `registry_path: Path`, optional `kernel_image_path`, `law_spine_path`, `boot_timestamp`, `registry_version`, `law_spine_key`, `hash_alg` |
| **Outputs** | `EarlyBootResult` with `boot_result=OK` and sealed `TrustRoot`, or `boot_result=HALT` with `detail` |
| **Constraints** | On success: corridor loader sealed, trust root sealed exactly once; kernel image defaults to stub `aaes-kernel-image-stub-v0.1` when path absent |
| **Failure modes** | `CorridorLoaderError` → HALT; double seal → `RuntimeError` |

## Seal and read syscalls

| Function | Inputs | Outputs | Constraints |
|----------|--------|---------|-------------|
| `seal_trust_root(trust_root)` | Built `TrustRoot` | None | Single seal per boot; raises if already sealed |
| `get_trust_root()` | — | `TrustRoot` | Raises `RuntimeError` if not sealed |
| `is_trust_root_sealed()` | — | `bool` | Read-only probe |
| `to_ucr_context(trust_root)` | `TrustRoot` | `UCRTrustContext` | Pure projection |
| `get_trust_root_syscall()` | — | `dict[str, str]` | Privileged stub; includes seal flags |

## Governed-mode invariant

`require_governed_mode()` in `src/ucr/ucr_governed.py` refuses when:

- `H_TRUST_ROOT` missing or mismatched between UCR context and kernel
- `H_LAW_SPINE` or `H_CORRIDORS` mismatched between UCR views and kernel

Refusal code **1006** (`ERR_TRUST_ROOT_MISMATCH`). Wired into `cog_act_commit` and attestation registration.

## Cross-references

- **H_CORRIDORS** canonical JSON: [H_CORRIDORS_BOOT_MANIFEST.md](H_CORRIDORS_BOOT_MANIFEST.md), [CORRIDOR_LOADER_SPEC_v0.1.md](CORRIDOR_LOADER_SPEC_v0.1.md)
- **H_BOOT_MANIFEST** two-pass self hash: [TRUST_ROOT_MEASUREMENT_CHAIN.md](TRUST_ROOT_MEASUREMENT_CHAIN.md)
- **UCR registration:** [UCR_ATTESTATION_SPEC.md](UCR_ATTESTATION_SPEC.md)

## Test hooks

- `reset_trust_root_for_tests()` — clears sealed state for unit tests

## v0.1 assumptions

- `H_TRUST_ROOT` is not stored in the on-disk boot manifest; computed at seal time only.
- Law spine module content hashes depend on files under `docs/contracts/`; fixture recomputation required when law sources change.
