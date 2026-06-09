# Metal profile proof checklist

Use this checklist to verify that **cog-os** with profile `metal` meets the NorthStar forge proof bar: custom PID 1, network bring-up, staged cognitive runtime, AAIS health, and CI contract boot.

## Prerequisites

- Linux or WSL2 with `debootstrap`, `qemu-system-x86_64`, `python3`, `make`
- Repo checkout at `project-infi/` (monorepo root)
- Optional: `xorriso` + `DEBIAN_BASE_ISO` for ISO build proof

## Build

- [ ] Rootfs builds: `make cog-rootfs COG_PROFILE=metal` (or `bash cog-os/forge/scripts/build-rootfs.sh --profile metal`)
- [ ] Payload staged under `/opt/cogos` including `config/cognitive_runtime_family.json` and `lib/src/cog_runtime/`
- [ ] `/etc/init.conf` lists services: `platform`, `login`, `firstboot`, `aais`
- [ ] Attestation / forge gates pass: `make forge-gates COG_PROFILE=metal` (optional: `COG_CONTRACT_BOOT=1` for QEMU boot)

## QEMU contract boot (required)

- [ ] Contract boot passes:

```bash
make cog-qemu-smoke-contract-boot COG_PROFILE=metal
```

Expected markers in guest log / CI output:

- `[platform]` network configured (e.g. `10.0.2.15/24` on `ens3` in slirp)
- `[aais]` or AAIS health file written
- Host reaches `GET http://127.0.0.1:<hostfwd>/health` → `200` JSON

## Runtime validation (on built rootfs or live guest)

- [ ] Manifest validates:

```bash
PYTHONPATH=/opt/cogos/lib python3 -m src.cogos_runtime_bridge \
  --validate-config /opt/cogos/config/cognitive_runtime_family.json
```

- [ ] `start-aais` binds `0.0.0.0:8765` and serves `/health`

## Login path (metal)

- [ ] `login` service starts `agetty --autologin cogos` on `tty1` (and `ttyS0` when present)
- [ ] `/run/cog/login.started` exists after boot

## Installer (optional metal install proof)

- [ ] Installer smoke (no disk writes): `bash cog-os/scripts/cogos-installer.sh --smoke`
- [ ] Plan on target disk: `bash cog-os/scripts/cogos-installer.sh --plan --target-disk /dev/sdX --rootfs <path>`
- [ ] Apply creates GPT (EFI + root + data), fstab by UUID, `grub-install` UEFI

## Bootable ISO (optional)

- [ ] ISO tree: `bash cog-os/forge/scripts/build-iso.sh --profile metal --iso-tree-only`
- [ ] Bootable ISO when base image set: `DEBIAN_BASE_ISO=... bash cog-os/forge/scripts/build-iso.sh --profile metal`
- [ ] Artifact size check passes (see `scripts/lib/paths.sh` `verify_iso_size`)

## Sign-off

| Field | Value |
|-------|--------|
| Profile | `metal` |
| Rootfs path | |
| QEMU contract | pass / fail |
| AAIS `/health` | pass / fail |
| Runtime validate-config | pass / fail |
| Date | |
| Operator | |
