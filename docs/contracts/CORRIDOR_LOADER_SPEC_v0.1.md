# Corridor Loader Spec (CRG_LOADER v0.1)

**Engineering module:** `src/ucr/corridor_loader.py`  
**Registry layout:** `aaes/kernel/corridors/` (filesystem)  
**Mythic label:** Trusted Corridor Gate (comments/docs only)

## Purpose

At boot, discover corridor JSON fixtures, validate schema and law keys, resolve version supersession, compute `H_CORRIDORS`, and **seal** an immutable `TrustedCorridorSet` for the session.

Post-seal, `cog_act_commit` and UCR governed mode read only the sealed set.

## Boot result

| Value | Meaning |
|-------|---------|
| `OK` | Corridors loaded and sealed |
| `HALT` | Fatal validation error — boot must not proceed to governed mode |
| `SAFE_MAINTENANCE` | Reserved — degraded corridor set |

## Validation

1. At least one corridor (`ERR_NO_CORRIDORS`)
2. JSON schema / required fields (`ERR_CORRIDOR_MALFORMED`)
3. All law keys pass `validate_law_key()` (`ERR_LAW_KEY_INVALID`)
4. Supersession chain consistent (`ERR_CORRIDOR_VERSION_CHAIN`)

## Seal API

```python
loader = CorridorLoader()
trusted = loader.load_and_seal(
    registry_path,
    law_spine_key=0x010229CAFF000000000000005532534F,
    registry_version=1,
    boot_timestamp="2026-06-18T10:00:00Z",
)
# trusted.corridor_hash == H_CORRIDORS line value
```

After seal:

- `get_trusted_corridors()` — read-only tuple
- `is_sealed()` — bool
- Re-seal raises `RuntimeError`

## Trust root integration

`kernel_boot.run_early_boot()` invokes the loader before building the boot manifest:

1. Loader seals corridors → `H_CORRIDORS`
2. Manifest builder includes `H_CORRIDORS` line
3. `build_trust_root(manifest)` binds corridors into `H_TRUST_ROOT`
4. `seal_trust_root()` — parallel immutability to corridor seal

`get_trust_root_syscall()` reports both `corridors_sealed` and `trust_root_sealed`.

## Fixture helpers (tests)

`write_corridor_fixture(registry_path, corridor)` writes one JSON file per corridor for isolated test registries.

`reset_corridor_loader_for_tests()` clears seal state between tests.

## Default fixtures

Built-in builders in `src/ucr/corridor.py`:

| Name | corridor_id | max_risk |
|------|-------------|----------|
| Nova-Dev | `11111111-1111-4111-8111-111111111101` | high |
| Prod-Ops | `22222222-2222-4222-8222-222222222201` | critical |

## Related contracts

- `H_CORRIDORS_BOOT_MANIFEST.md` — canonical serialization
- `TRUST_ROOT_MEASUREMENT_CHAIN.md` — full measurement chain
- `BLK_UCR_V0.md` — law key validation
