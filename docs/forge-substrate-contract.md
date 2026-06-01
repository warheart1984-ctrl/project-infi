# Forge Substrate Contract (OS-Agnostic Replay)

Status: canonical substrate contract for Forge ISO factory behavior.

Contract versions: `forge-substrate.v1` (legacy), **`forge-substrate.v2`** (active).

Platform program: `docs/forge-platform-program.md`.

## Purpose

Forge is **OS-agnostic at the replay substrate layer**. Any compatible hybrid live ISO can be used as input for squashfs extract + boot replay.

Rootfs construction may still use a specific backend (currently Debian/debootstrap). That is separate from replay substrate selection.

## Canonical environment variables

| Variable | Role |
|---|---|
| `COGOS_SUBSTRATE_ISO` | Canonical replay/base ISO path |
| `COGOS_SUBSTRATE_ID` | Substrate type (`auto`, `debian-live`, `cogos-replay`, `generic-live-squashfs`, ...) |
| `COGOS_BOOT_REPLAY_ISO` | Legacy alias (still supported) |
| `COGOS_DEBIAN_ISO` | Legacy alias (still supported) |

Precedence for resolution:

1. CLI path argument
2. `COGOS_SUBSTRATE_ISO`
3. `COGOS_BOOT_REPLAY_ISO`
4. `COGOS_DEBIAN_ISO`
5. `DEBIAN_BASE_ISO`

## Substrate contract (minimum)

A valid substrate ISO must provide:

- hybrid bootable ISO readable by `xorriso`
- squashfs root under `live/` (e.g. `live/filesystem.squashfs`)
- live boot files (`live/vmlinuz*`, `live/initrd*`)

## Registry

Substrate types are declared in:

- `wolf-cog-os/forge/substrates/registry.json` (`substrate-registry.v2`)
- Schema: `wolf-cog-os/forge/substrates/schema/substrate-registry.v2.json`

### Substrate classes (v2)

| Id | Family | Replay adapter |
|---|---|---|
| `generic-live-squashfs` | generic | debian-live-layout |
| `debian-live` | debian | debian-live-layout |
| `ubuntu-live` | ubuntu | debian-live-layout |
| `arch-live` | arch | archiso-layout |
| `fedora-live` | fedora | fedora-liveos-layout |
| `alpine-live` | alpine | alpine-modloop-layout |
| `opensuse-live` | opensuse | fedora-liveos-layout |
| `cogos-replay` | cogos | debian-live-layout |
| `trixie-live` | puppy | debian-live-layout |

Non-Debian replay adapters are **classification-ready**; full replay support in `build.sh` is tracked per substrate evolution ledger status.

## Automatic classification (v2)

`validate-substrate.py` emits:

- `classification.substrate_id` — best match
- `classification.confidence` — score separation vs runner-up
- `classification.candidates` — top ranked ids

```bash
python3 wolf-cog-os/scripts/validate-substrate.py \
  --iso /path/to/any.iso \
  --substrate-id auto \
  --mode fail
```

## Substrate evolution ledger

Governance for substrate class changes:

- `.github/governance/substrate-evolution-ledger.json`
- Validator: `.github/scripts/validate-substrate-evolution-ledger.py`

New substrate classes require an evolution ledger entry before `status: active`.

## Legacy examples

Examples:

- `debian-live` — Debian live ISO
- `cogos-replay` — CoGOS-built ISO (e.g. `Wolf-CoG-OS-full.iso`)
- `generic-live-squashfs` — fallback auto-detect profile

## Validation

```bash
python3 wolf-cog-os/scripts/validate-substrate.py \
  --iso /path/to/any.iso \
  --substrate-id auto \
  --mode fail
```

Forge build entrypoints validate substrate automatically:

- `bash wolf-cog-os/scripts/build-forge-installer.sh /path/to/any.iso`
- `forge-run-pipeline.sh /forge/pipelines/daily-driver.yaml` with `COGOS_SUBSTRATE_ISO` set

## Pipeline spec fields

```yaml
substrate:
  id: auto          # or cogos-replay, debian-live, generic-live-squashfs
  iso: /optional/path/to/substrate.iso
```

## Explicit non-goals

- Non-live ISO formats (data-only images, Windows installers, etc.)
- Substrates without squashfs live root layout
- Guaranteed support for non-amd64 without explicit arch/toolchain config
