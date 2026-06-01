# CoGOS Universal Boot — Proof Gate

**Freeze tag:** `universal-installer-1.0`  
**Primary ship ISO:** `Wolf-CoG-OS-universal-installer.iso`  
**Status:** Runtime frozen. No new runtime features until proof gate passes.

Governance reference:
- Meta Architect lawbook (supreme authority): `META_ARCHITECT_LAWBOOK.md`
- Repository proof law: `REPO_PROOF_LAW.md`
- Proof bundle template: `templates/PROOF_BUNDLE_TEMPLATE.md`
- Project baseline checklist: `templates/PROJECT_BASELINE_CHECKLIST.md`

---

## 0. Release Gate (Enforced)

Release is **not ready** unless all items below are complete and attached to the release notes:

- [ ] Universal ISO build succeeded from `wolf-cog-os/scripts/build-universal-installer.sh`.
- [ ] QEMU smoke passed against the **produced universal ISO** (not only baseline Debian ISO).
- [ ] ISO proof attached: `sha256sum`, `sha256sum -c`, and file size (`ls -lh`).
- [ ] Real hardware checklist signed off for BIOS + UEFI + Secure Boot off path.

Mandatory commands (run in WSL):

```bash
cd /mnt/e/project-infi
export COGOS_PAYLOAD=$HOME/.cogos-payload-cache
bash wolf-cog-os/scripts/build-universal-installer.sh

ISO=/home/nullzero/Wolf-CoG-OS-universal-installer.iso \
COGOS_QEMU_WORK=/tmp/cogos-qemu-universal \
COGOS_QEMU_WAIT=75 \
bash wolf-cog-os/scripts/test/installer-qemu-smoke.sh

sha256sum /home/nullzero/Wolf-CoG-OS-universal-installer.iso
sha256sum -c /home/nullzero/Wolf-CoG-OS-universal-installer.iso.sha256
ls -lh /home/nullzero/Wolf-CoG-OS-universal-installer.iso
```

Current WSL proof (2026-05-27):
- Build: **PASS** (`Built with xorriso boot replay`, size check OK)
- Smoke: **PASS** (`QEMU smoke boot stayed alive for 75 seconds.`)
- SHA/size: **PASS** (`bda9ae72...`, 4.0G, `.sha256` validates)

---

## 1. ISO Inventory (current truth)

| File | Size | SHA256 | Built | Status |
|------|------|--------|-------|--------|
| `Wolf-CoG-OS-metal-installer.iso` | 4.0 GB | `316b1899642f0e8ad50ca19a81bb661b257cea239309cfbbcc4e92f45714ea95` | 2026-05-26 22:36 UTC | **PRIMARY SHIP ISO** |
| `Wolf-CoG-OS-daily-driver-surprise.iso` | 3.8 GB | `f55952aa70dd87ebb73a8621f40f8fe00f69829acfeeee5780925a16c3e669b5` | 2026-05-26 19:11 UTC | Secondary (Calamares) |
| `Wolf-CoG-OS-metal-fixed.iso` | 4.0 GB | `f77638110eb1ecf97202302594ad5e5e19d6a0469f56ed1516a04d7a464cb615` | 2026-05-24 08:17 UTC | Baseline archive |

All three files are at `~/` in WSL (nullzero) and mirrored under `E:\project-infi\`.

---

## 2. Universal Boot Spec — Single Profile

**Product name:** `Wolf-CoG-OS metal-installer-1.0`  
**Build script:** `wolf-cog-os/scripts/build-metal-installer.sh`

### Unified installer ISO (single artifact, metal + surprise)

Use this build when you need one bootable ISO that exposes both installation paths:

```bash
cd /mnt/e/project-infi
bash wolf-cog-os/scripts/build-universal-installer.sh
```

Output artifact:
- `Wolf-CoG-OS-universal-installer.iso`

Expected GRUB menu shape:
- `Wolf CoG OS — Live (metal baseline, recommended)`
- `Install Wolf CoG OS (Metal path - primary) ...`
- `Install Wolf CoG OS (Surprise path - Calamares) ...`

Install commands / path selection:
- **Metal path (primary):** boot live, then run:
  - `sudo cogos-install plan --target /dev/sdX`
  - `sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX`
- **Surprise path (secondary):** choose `Install Wolf CoG OS (Surprise path - Calamares) ...`, complete Calamares, then reboot from disk; `cogos-install-finish` is executed via Calamares hook.

### Live session (on any machine)
| Property | Value | Why |
|----------|-------|-----|
| GRUB entry | `nomodeset quiet` only | avoids GPU/KMS hangs on unknown hardware |
| findiso | **disabled** (`COGOS_LIVE_FINDISO=0`) | no Ventoy dependency, plain boot works |
| Live PID1 | systemd (stock Debian) | cognitive_init does NOT run in live session |
| Live cognitive_init | disabled on live | enabled on disk by `cogos-install-finish` |
| Boot media | Rufus DD mode **or** Ventoy | xorriso replay from debian-live produces clean hybrid GPT |

### Install path (primary)
```
# From live terminal on the booted machine:
sudo cogos-install plan --target /dev/sdX          # dry run, see steps
sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX
```
Steps: `disk → copy → bootloader → identity → network → firstboot`  
PID1 chain and `update-initramfs` run **after** rsync, before `update-grub` — this is the proven order.

### Disk (after install)
| Step | Script | Effect |
|------|--------|--------|
| PID1 swap | `cogos-install-finish` | `/sbin/init` → `cognitive_init` chain |
| initramfs regen | `update-initramfs -u` | bakes new init path into ramdisk |
| First-boot marker | `FIRST_BOOT_PENDING` flag | `cogos-first-boot.service` fires once after login |
| Subsequent boots | `cognitive_init` fast handoff | passes to systemd immediately |

### Boot media requirements
| Tool | Mode | Notes |
|------|------|-------|
| Rufus | **DD Image** mode | preserves MBR + GPT hybrid; do NOT use ISO mode |
| Ventoy | Works out of box | no findiso needed; ISO is self-contained |
| `dd` / `cp` | `sudo dd if=Wolf-CoG-OS-metal-installer.iso of=/dev/sdX bs=4M status=progress` | direct flash |

### Calamares (surprise) — secondary only
- Graphical installer, more user-friendly but more fragile post-install
- `cogos-install-finish` runs as a Calamares shellprocess hook — verified in payload
- Use if: GUI installer experience needed; test before shipping
- Do NOT use as primary for "any machine" until scenario 5 (build + smoke) passes in matrix

---

## 3. Proof Gate — Pass/Fail Criteria

### Gate A — Automated (runnable in WSL today)

| ID | Test | Command | Passes Today? |
|----|------|---------|---------------|
| A1 | QEMU smoke: Debian live stays alive 60s | `INSTALLER_TEST_SCENARIOS=6 COGOS_MATRIX_WORK=~/cogos-build/matrix ISO=~/debian-live-13.5.0-amd64-cinnamon.iso python3 wolf-cog-os/scripts/test/installer-matrix.py` | **YES** — matrix run `local-20260527T033854Z-836`, 62s |
| A2 | QEMU smoke: CoGOS metal-installer stays alive 60s | `ISO=~/Wolf-CoG-OS-metal-installer.iso COGOS_QEMU_WORK=~/cogos-build/cogos-smoke bash wolf-cog-os/scripts/test/installer-qemu-smoke.sh` | **YES** — 60s alive, exit 0 (2026-05-27 04:14Z) |
| A3 | Payload release gate | `bash wolf-cog-os/scripts/verify-surprise-release.sh` | **YES** — all 5 checks OK (cogos-install-finish, cogos-first-boot, cognitive_init, first_boot_fast_handoff, WantedBy=graphical.target) |
| A4 | Installer loopback (scenario 1 — clean disk) | `INSTALLER_TEST_SCENARIOS=1 COGOS_MATRIX_WORK=~/cogos-build/matrix COGOS_ROOTFS_SRC=~/cogos-build/rootfs-12-22-0-wolf-os python3 wolf-cog-os/scripts/test/installer-matrix.py` | IN PROGRESS (terminal active, disk.img formatting) |
| A5 | Init chain: disk has cognitive_init at /sbin/init | (see command below) | NOT YET — needs post-install loopback mount |
| A6 | ISO size sanity (>3GB, <5GB) | `wsl bash -lc "ls -lh ~/Wolf-CoG-OS-metal-installer.iso"` | **YES** — 4.0 GB |
| A7 | SHA256 stability | `wsl bash -lc "sha256sum ~/Wolf-CoG-OS-metal-installer.iso"` | **YES** — `316b1899...` matches freeze tag |

**A5 command (run after scenario 1 loopback completes):**
```bash
wsl bash -lc "
  WORK=~/cogos-build/matrix/scenario1-core
  sudo mount \${WORK}/disk.img \${WORK}/target-root -o loop,offset=\$((2048*512)) 2>/dev/null || true
  ls -la \${WORK}/target-root/sbin/init
  cat \${WORK}/target-root/proc/1/comm 2>/dev/null || echo 'not mounted'
  sudo umount \${WORK}/target-root 2>/dev/null || true
"
```

### Gate B — Real Metal Checklist

Run this matrix on **at least 2 physical machines** before release:

| Target | Firmware path | Required result |
|---|---|---|
| Legacy desktop | BIOS/CSM boot | USB boots, live works, metal install path works |
| Modern desktop/laptop | UEFI boot | USB boots, live works, metal install path works |
| UEFI device (same machine allowed) | Secure Boot **OFF** | Boot + install path confirmed with SB disabled |

Checklist:

- [ ] Flash ISO using Rufus DD mode to USB
- [ ] Boot from USB — GRUB menu appears within 30s
- [ ] Live desktop loads (Cinnamon) — no black screen or KMS hang
- [ ] Run `sudo cogos-install plan --target /dev/sdX` — exits 0, prints steps
- [ ] Run `sudo cogos-install apply --target /dev/sdb --yes --confirm-erase sdb` (test disk)
- [ ] Reboot — OS boots from disk without USB
- [ ] `ps aux | grep -E 'PID.*init'` shows cognitive_init or systemd (not initramfs shell)
- [ ] `cat /proc/1/comm` → `systemd` (cognitive_init fast-hands off)
- [ ] First-boot service runs and exits cleanly: `systemctl status cogos-first-boot`
- [ ] Second reboot — boots normally, no first-boot re-trigger

**HP EliteDesk status:** Live boot ✓ — install ✓ — disk boot ✓ — PID1 chain ✓ (confirmed prior session)

### Flashing guidance (required)

- **Primary:** Rufus -> select ISO -> choose **DD Image mode** (do not use ISO mode).
- **Fallback flasher:** [balenaEtcher](https://etcher.balena.io/) default write/verify flow.
- **Linux fallback:** `sudo dd if=Wolf-CoG-OS-universal-installer.iso of=/dev/sdX bs=4M status=progress conv=fsync`.

---

## Gate Decision

Go/No-Go:
- **GO** only when Gate A is fully pass and Gate B matrix items are checked and signed off.
- **NO-GO** if any matrix row is missing, or if installer path can dead-end on tested hardware.

### Gate C — UEFI vs BIOS (missing, needs OVMF)

```bash
# UEFI smoke (needs ovmf package in WSL)
sudo apt-get install -y ovmf 2>/dev/null
ISO=~/Wolf-CoG-OS-metal-installer.iso
qemu-system-x86_64 -m 4096 -bios /usr/share/ovmf/OVMF.fd \
  -cdrom "$ISO" -boot d -nographic -serial file:/tmp/uefi-serial.log \
  -no-reboot &
QPID=$!; sleep 60; kill -0 $QPID && echo "UEFI PASS" || echo "UEFI FAIL"
```

Status: **NOT YET RUN**

---

## 4. Runtime Freeze

**Effective immediately:** no new runtime features, Python governance changes, or cognitive_init modifications until Gate A (A1–A4) + Gate B (HP EliteDesk) all pass.

### Frozen components
| Component | Frozen version | Location |
|-----------|---------------|----------|
| `cognitive_init` | as baked into metal-installer-1.0 squashfs | payload/opt/cogos/bin/ |
| `cogos-install` | current tree | payload/usr/local/bin/ |
| `cogos-install-finish` | current tree | payload/usr/local/bin/ |
| `cogos-first-boot` | current tree | payload/usr/local/bin/ |
| `cogos-first-boot.service` | current tree | payload/etc/systemd/system/ |
| GRUB config | `nomodeset quiet`, no findiso | baked into metal-installer-1.0 |
| Release manifest | `metal-installer-1.0` / `12.22.0-wolf-os` | payload/opt/cogos/config/ |

### What is NOT frozen
- Build scripts (`build-metal-installer.sh`, `build_iso.sh`, etc.) — fix as needed
- Test/CI scripts — can be improved
- Documentation

---

## 5. Exact Commands to Build + Verify + Flash

### Build (unified single ISO)
```bash
# In WSL (nullzero), from E:/project-infi:
cd /mnt/e/project-infi

# Ensure CRLF-free scripts (Windows drvfs writes CRLF):
python3 -c "
from pathlib import Path
for f in Path('wolf-cog-os/scripts').glob('**/*.sh'):
    t = f.read_bytes()
    if b'\r\n' in t:
        f.write_bytes(t.replace(b'\r\n', b'\n'))
        print('fixed:', f)
"

# Build unified installer (uses debian-live as boot replay source):
export COGOS_PAYLOAD=$HOME/.cogos-payload-cache
bash wolf-cog-os/scripts/build-universal-installer.sh \
  2>&1 | tee /tmp/cogos-metal-installer-build.log

# Output: ~/Wolf-CoG-OS-universal-installer.iso + *.sha256
```

### Verify
```bash
# SHA256 check:
sha256sum ~/Wolf-CoG-OS-universal-installer.iso
# Expected: 316b1899642f0e8ad50ca19a81bb661b257cea239309cfbbcc4e92f45714ea95
# (only if rebuilt from same squashfs; new builds will have different hash)

# Payload gate:
bash wolf-cog-os/scripts/verify-surprise-release.sh

# QEMU smoke (CoGOS ISO):
ISO=~/Wolf-CoG-OS-universal-installer.iso \
COGOS_QEMU_WORK=~/cogos-build/cogos-smoke \
COGOS_QEMU_WAIT=60 \
bash wolf-cog-os/scripts/test/installer-qemu-smoke.sh

# Installer loopback (needs rootfs at ~/cogos-build/rootfs-12-22-0-wolf-os):
INSTALLER_TEST_SCENARIOS=1 \
COGOS_MATRIX_WORK=~/cogos-build/matrix \
COGOS_ROOTFS_SRC=~/cogos-build/rootfs-12-22-0-wolf-os \
python3 wolf-cog-os/scripts/test/installer-matrix.py
```

### Flash + Test
```bash
# Flash to USB (replace /dev/sdX with your USB device):
sudo dd if=~/Wolf-CoG-OS-universal-installer.iso of=/dev/sdX bs=4M status=progress conv=fsync
# OR copy to Windows and use Rufus in DD Image mode

# Windows: copy ISO from WSL to Windows:
cp ~/Wolf-CoG-OS-universal-installer.iso /mnt/e/project-infi/
```

---

## 6. Recommended Ship Path

**Ship: `Wolf-CoG-OS-metal-installer.iso`** (`metal-installer-1.0`)

Rationale:
- Minimal GRUB — no findiso, no Ventoy dependency, works on plain USB boot
- Live PID1 = stock systemd — cognitive_init never runs in live, no interference
- Install = `cogos-install apply` (terminal) — proven on HP EliteDesk, deterministic
- Boot replay from clean debian-live GPT — eliminates overlapping GPT issue from metal-fixed
- Calamares surprise ISO (`daily-driver-surprise.iso`) is secondary: more user-friendly but requires `cogos-install-finish` hook to fire correctly in Calamares context

**Surprise ISO status:** Built (3.8 GB, `f55952aa...`). `cogos-install-finish` hook is in payload. Not promoted to primary until scenario 5 (matrix surprise build + smoke) passes.

---

## 7. Current Build Status

| Item | Status |
|------|--------|
| `Wolf-CoG-OS-metal-installer.iso` | Built, SHA256 verified, at `~/` in WSL and `E:\project-infi\` |
| `Wolf-CoG-OS-daily-driver-surprise.iso` | Built (multiple attempts, one succeeded at 19:11), at `~/` |
| Surprise build (1.6-surprise) attempt | Multiple WSL crashes during squashfs; final good build at 19:11 |
| Matrix scenario 6 (QEMU smoke, Debian live) | **PASSED** (62s, run `local-20260527T033854Z-836`) |
| Matrix scenario 1 (loopback install) | IN PROGRESS (disk.img formatting, terminal active) |
| Matrix scenario 6 on CoGOS ISO | NOT YET RUN |
| UEFI QEMU test | NOT YET RUN |
| Real metal: non-HP machine | NOT YET DONE |

**Next action:** Wait for scenario 1 loopback (terminal active) to complete → run init chain check (A5). Then flash to a second machine for Gate B.

---

## 8. Universal Adapter Policy Spec

Universal Adapter OS implementation contracts are documented in:

- `wolf-cog-os/docs/UNIVERSAL_ADAPTER_IMPLEMENTATION_SPEC.md`
- `wolf-cog-os/docs/hac.schema.json`

Use these docs for `host_probe -> host_profile` flow, legacy-vs-modern kernel family
selection policy, GRUB/initramfs policy rules, governance/attestation hooks, and phased rollout gates.
