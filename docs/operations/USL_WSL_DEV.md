# USL development on WSL

Slice 2 admission and broker tests run on WSL when the repo lives on a drvfs mount
(for example `/mnt/e/...`). Use Linux-native paths for ephemeral QEMU disks and
rootfs copies so `qemu-img` does not touch drvfs or prompt for `sudo`.

## One-time Python deps

Forge integration tests require `networkx` and `pytest` from the repo root:

```bash
wsl bash -lc 'cd /mnt/e/project-infi && python3 -m pip install -r requirements.txt'
```

## Recommended env (WSL)

```bash
export COG_ARTIFACT_NATIVE_DIR=/var/tmp/cog-os-artifacts
export COG_ROOTFS_NATIVE=/var/tmp/cog-os/rootfs
export COG_PAYLOAD_USL_LIFTED=1
export USL_SLICE2_REQUIRE_FORGE_INTEGRATION=1   # optional; matches CI metal/guest gates
```

## Run admission

```bash
# Wrapper sets native staging defaults
bash ci-artifacts/run-slice2-admit.sh

# Or Makefile (canonical script under cog-os/scripts/test/)
make usl-slice2-admit COG_PROFILE=metal

# Guest profile (Tier A only, no QEMU)
make usl-slice2-admit COG_PROFILE=usl-lifted-guest USL_SLICE2_ADMIT_ARGS="--skip-rootfs"
```

## See also

- [COG OS integration](../../cog-os/docs/deferred-lift-governance/COG_OS_INTEGRATION.md)
- [USL spec](../contracts/USL_SPEC.md)
