# Forge Rootfs Backend Contract

Status: canonical rootfs construction backend contract (P6).

Authority: `docs/forge-platform-program.md`, `docs/forge-substrate-contract.md`.

## Purpose

Forge separates **replay substrate** (ISO input) from **rootfs backend** (how the target root tree is bootstrapped). Substrate selection is OS-agnostic; rootfs backend selection defines which bootstrap tool creates the tree before chroot customization.

## Canonical environment variables

| Variable | Role |
|---|---|
| `COGOS_ROOTFS_BACKEND` | Backend id (`debootstrap`, `pacstrap`, `dnfroot`, `apkroot`) |
| `COGOS_ROOTFS_BACKEND_REGISTRY` | Backend registry JSON path |
| `COGOS_DEBIAN_SUITE` | Debian suite (debootstrap backend) |
| `COGOS_MIRROR` | Debian mirror (debootstrap backend) |
| `COGOS_ARCH` | Target architecture |

## Backend registry

Path: `wolf-cog-os/forge/backends/registry.json`

| Backend | Status | Package manager |
|---|---|---|
| `debootstrap` | production | apt |
| `pacstrap` | stub | pacman |
| `dnfroot` | stub | dnf |
| `apkroot` | stub | apk |

## Bootstrap dispatcher

`wolf-cog-os/scripts/lib/rootfs-bootstrap.sh` loads `wolf-cog-os/scripts/lib/backends/<backend>.sh` and calls `backend_bootstrap "$ROOTFS_OUT"`.

`build-rootfs.sh` uses the dispatcher at step `[1/7]`.

## Validation

Registry-only (CI-safe):

```bash
python3 wolf-cog-os/scripts/validate-rootfs-backend.py \
  --backend debootstrap \
  --registry-only \
  --mode fail
```

Host tool check (Linux build hosts):

```bash
python3 wolf-cog-os/scripts/validate-rootfs-backend.py \
  --backend debootstrap \
  --mode fail
```

## Profile field

```yaml
rootfs:
  backend: debootstrap
  package_sets:
    - base
    - forge
```

## Explicit non-goals (P6)

- Production pacstrap/dnf/apk implementations (stubs only)
- Non-Debian chroot package installation paths (post-bootstrap still apt-based today)
- Multi-arch matrix enforcement (planned P8)
