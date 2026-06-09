# Nova NorthStar CoG OS

Nova NorthStar CoG OS is the host layer for Project Infinity: custom PID 1 gatekeeper, profile-driven
rootfs/ISO forge, and staged `/opt/cogos` cognitive payload.

### Python selection

By default, the build uses `python3` (override with `PYTHON` in the Makefile):

```makefile
PYTHON ?= python3
```

You can override this per invocation, which is especially useful on Windows:

```powershell
make PYTHON="C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe" verify-artifacts
make PYTHON="C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe" forge-gates
```

All Python-based scripts and gates are wired through `$(PYTHON)`, so this single override is sufficient.

## Profile matrix

| Profile | Init | Host systemd | Desktop | Use case |
|---------|------|--------------|---------|----------|
| **metal** | Custom PID 1 only | None | No | Server / AAIS spine / QEMU proof |
| **daily-driver** | Custom PID 1 + hybrid helpers | User session helpers (not PID 1) | LightDM + Cinnamon after AAIS health | Operator workstation |

## Boot flow

```
kernel → /sbin/init (gatekeeper) → /etc/rc.sh → /etc/init.conf services → [desktop if profile]
```

Services log to `/var/log/cog/init.log`. Profile is read from `/etc/cog/profile` (or kernel
`cog.profile=`).

## Layout

```
cog-os/
  host/          PID 1, rootfs skeleton, install helpers
  payload/       Staged /opt/cogos (manifest, mind bundle, start-aais)
  forge/         Profiles, package lists, rootfs/ISO scripts
  scripts/test/  QEMU smoke + profile loader tests
```

## Build (from repo root)

```bash
make rootfs COG_PROFILE=metal
make rootfs COG_PROFILE=daily-driver
make iso-tree COG_PROFILE=metal
make cog-qemu-smoke COG_PROFILE=metal   # Linux/WSL + debootstrap + QEMU
```

Artifacts: `artifacts/cog-os/rootfs-<profile>/`, `artifacts/cog-os/disk-<profile>.img`.

## Hybrid init (daily-driver)

Custom C gatekeeper remains PID 1 on all profiles. The daily-driver profile installs systemd,
D-Bus, and desktop packages for **user/session** helpers only. The `desktop` service stanza in
`init.conf` starts LightDM after AAIS health passes; it does not replace PID 1 with systemd.

## AAIS, Nova UL, and operator shell

| Layer | On cog-os image | In monorepo |
|-------|-----------------|-------------|
| PID 1 / rc | Gatekeeper + profile-driven [`init.conf`](host/rootfs/etc/init.conf) services | — |
| AAIS spine | [`start-aais`](payload/opt/cogos/bin/start-aais) HTTP stub on `127.0.0.1:8765/health` | Full runtime in `src/` |
| Nova UL / operator | **Not on `metal` by default**; optional on `forge-selfhosted` via `payload_ul` | [`tools/ul/`](../../tools/ul/), Jarvis API, [`docs/runtime/UL_LINEAGE_CONSOLE.md`](../../docs/runtime/UL_LINEAGE_CONSOLE.md) |

Host verification (not image boot requirements for `metal`):

```bash
make lineage-gate
python3 -m tools.ul.smoke
```

Profile attestation evaluates `aais_health_200` when staged AAIS files exist. QEMU contract-boot additionally polls `/health` via host port forward and records the result in `ci-artifacts/qemu-contract-boot.json`.

## QEMU contract smoke

```bash
make cog-rootfs COG_PROFILE=metal          # WSL/Linux + debootstrap
make cog-qemu-smoke-contract COG_PROFILE=metal
make cog-qemu-smoke-contract-boot COG_PROFILE=metal
```

When the artifact path is on a Windows mount (`/mnt/c`, `/mnt/e`, …), debootstrap runs on a native Linux path (default `/var/tmp/cog-os/rootfs-<profile>`). The artifact directory holds `.cog-rootfs-staging` (pointer to the native tree) because 9p/drvfs cannot store symlinks or device nodes. QEMU and forge steps resolve the pointer automatically. Override the native path with `COG_ROOTFS_NATIVE=/path/on/ext4` if needed.

Artifacts:

- `ci-artifacts/qemu-contract-static.json` — static gatekeeper proof
- `ci-artifacts/qemu-contract-boot.json` — boot + AAIS HTTP gate
- `ci-artifacts/qemu-serial.log` — serial console (grep `"event":"contract"`)

Optional forge gate (Linux/WSL only, after rootfs build):

```bash
COG_CONTRACT_BOOT=1 make forge-gates COG_PROFILE=metal
```

Set `FORGE_SKIP_ROOTFS=1` to skip debootstrap during gates. Default CI keeps `COG_CONTRACT_BOOT` off until a Linux runner with QEMU is available.
