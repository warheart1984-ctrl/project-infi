# Trust Root Measurement Chain (UCR v0.1)

**Engineering module:** `src/ucr/trust_root.py`, `src/ucr/kernel_boot.py`  
**Mythic label:** Boot Trust Root (comments/docs only)

## Purpose

Bind kernel image, law spine, corridor registry, and boot manifest into a single sealed **H_TRUST_ROOT** digest. UCR governed mode refuses unless kernel and UCR views agree on this chain.

## Hash algorithm

All measurements use **sha3-256** (256-bit digests). Wire format:

```
sha3-256:<lowercase_hex_64_chars>
```

## Individual measurements

### H_KERNEL_IMAGE

| Field | Value |
|-------|-------|
| Input | Exact kernel binary bytes as loaded by bootloader |
| Formula | `H_KERNEL_IMAGE = HASH(kernel_image_bytes)` |
| Manifest line | `H_KERNEL_IMAGE=sha3-256:<hex>` |

### H_LAW_SPINE

| Field | Value |
|-------|-------|
| Input | Canonical serialized law spine bundle |
| Formula | `H_LAW_SPINE = HASH(canonical_pack(modules))` |
| Manifest line | `H_LAW_SPINE=sha3-256:<hex>` |

`canonical_pack` sorts modules by stable `module_id`, then for each module emits:

```
module_id UTF-8 | 0x00 | len(content) u32 BE | content bytes
```

Default module IDs (v0.1):

- `LAW_CONS_v1` → `docs/contracts/AAES_OS_V1_FORMAL_SPEC.md`
- `LAW_SPINE_UCR_v0.1` → `docs/contracts/AAES-OS_LAW_SPINE_UCR_v0.1.md`
- `BLK_UCR_V0` → `docs/contracts/BLK_UCR_V0.md`

Implementation: `src/ucr/law_spine_pack.py`

### H_CORRIDORS

| Field | Value |
|-------|-------|
| Input | Canonical JSON of `TrustedCorridorSet` |
| Formula | `H_CORRIDORS = HASH(canonical_json_bytes)` |
| Manifest line | `H_CORRIDORS=sha3-256:<hex>` |

See `H_CORRIDORS_BOOT_MANIFEST.md` and `CORRIDOR_LOADER_SPEC_v0.1.md`.

### H_BOOT_MANIFEST

| Field | Value |
|-------|-------|
| Input | Boot manifest bytes **excluding** the `H_BOOT_MANIFEST` line |
| Formula | Two-pass: assemble pre-manifest lines, hash, append self line |
| Manifest line | `H_BOOT_MANIFEST=sha3-256:<hex>` (last measurement line) |

Pre-manifest lines (v0.1 order):

1. `H_KERNEL_IMAGE=...`
2. `H_LAW_SPINE=...`
3. `H_CORRIDORS=...`
4. `BOOT_TIMESTAMP=...` (optional metadata)
5. `REGISTRY_VERSION=...` (optional metadata)

Lines joined with `\n`, UTF-8 encoded, then hashed.

Implementation: `src/ucr/boot_manifest.py`

## Trust Root digest

```text
trust_root_bytes = concat(
    b"AAES-TRUST-ROOT-v1", b"\x00",   # domain separator
    H_KERNEL_IMAGE_raw_32_bytes,
    H_LAW_SPINE_raw_32_bytes,
    H_CORRIDORS_raw_32_bytes,
    H_BOOT_MANIFEST_raw_32_bytes,
)
H_TRUST_ROOT = HASH(trust_root_bytes)
```

**Normative concat order:** KERNEL → LAW_SPINE → CORRIDORS → BOOT_MANIFEST (each as 32 raw digest bytes, not hex strings).

`H_TRUST_ROOT` is **not** stored in the boot manifest file; it is computed at seal time and exposed via `get_trust_root()` / `get_trust_root_syscall()`.

## Exposure structs

```python
@dataclass
class TrustRoot:
    hash_alg: str          # "sha3-256"
    h_kernel_image: str
    h_law_spine: str
    h_corridors: str
    h_boot_manifest: str
    h_trust_root: str

@dataclass
class UCRTrustContext:
    hash_alg: str
    h_law_spine: str
    h_corridors: str
    h_trust_root: str
```

- `to_ucr_context(trust_root)` — UCR-facing subset
- `get_trust_root()` — read-only after boot seal
- `get_trust_root_syscall()` — privileged syscall stub in `kernel_boot.py`

## Boot flow

`run_early_boot()` in `kernel_boot.py`:

1. Load kernel image (configurable path; stub `aaes-kernel-image-stub-v0.1` for tests)
2. Pack law spine → `H_LAW_SPINE`
3. `CorridorLoader.load_and_seal()` → `TrustedCorridorSet` + `H_CORRIDORS`
4. Build manifest without self-line → `H_BOOT_MANIFEST`
5. Compute `H_TRUST_ROOT` → `seal_trust_root()`
6. Expose via `get_trust_root()`

## Governed-mode invariant

UCR MUST refuse governed mode unless:

- `H_TRUST_ROOT` present and matches kernel value
- `H_LAW_SPINE` and `H_CORRIDORS` match UCR's own law/corridor views

`require_governed_mode()` in `src/ucr/ucr_governed.py` returns refusal code **1006** (`ERR_TRUST_ROOT_MISMATCH`) on mismatch. Wired into `cog_act_commit`.

## Example manifest (test fixtures)

Kernel stub bytes: `aaes-kernel-image-stub-v0.1`  
Boot timestamp: `2026-06-18T10:00:00Z`  
Corridors: Nova-Dev + Prod-Ops fixtures (`src/ucr/corridor.py`)

```text
H_KERNEL_IMAGE=sha3-256:abc2aee9cede321211c8b44c9de4ebd6cb0c1c68fb28856d8bc6b59f0be7b47f
H_LAW_SPINE=sha3-256:46a999f755cc230d207b3e6a293e2558d144f3121d79b3e03406b569edcb77df
H_CORRIDORS=sha3-256:732b66373c6d66281ff95fa69fe3ff1a0d8c8fa70cc2ae13245e6d1890372cda
BOOT_TIMESTAMP=2026-06-18T10:00:00Z
REGISTRY_VERSION=1
H_BOOT_MANIFEST=sha3-256:a2b3c3606b1491f4c353a273d2c8b59e2acc34d6417fb2c86f07d77943b996ab
```

**Example H_TRUST_ROOT:** `sha3-256:219f4b87499c39ff82e07ca5d524ff2e158404c12e272b25472dcd61e15fac3e`

> Note: `H_LAW_SPINE` depends on law spine source files under `docs/contracts/`. If those files change, recompute fixtures.

## Tests

`tests/test_trust_root.py` — individual hashes, order sensitivity, domain separator, self-excluding manifest hash, governed-mode refusal, end-to-end boot.
