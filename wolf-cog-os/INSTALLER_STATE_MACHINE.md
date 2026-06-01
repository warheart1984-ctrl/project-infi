# CoGOS Installer State Machine

This document defines the crash-safe installer flow used by `cogos-installer`.

Governance reference:
- Meta Architect lawbook (supreme authority): `META_ARCHITECT_LAWBOOK.md`
- Repository proof law: `REPO_PROOF_LAW.md`
- Proof bundle template: `templates/PROOF_BUNDLE_TEMPLATE.md`

## Step Pipeline

```text
pending
  -> in_progress
     -> completed
     -> failed
```

Per run, the installer executes steps in this order:

```text
disk -> copy -> bootloader -> identity -> network -> firstboot
```

## Metal baseline vs surprise Calamares

| | **Metal installer** (`build-metal-installer.sh`) | **Surprise installer** (`build-surprise-installer.sh`) |
|---|---|---|
| Live PID1 | systemd (stock) | systemd (stock) |
| Live GRUB | `nomodeset quiet` only | stock Debian menu |
| Install path | `cogos-install apply` from live terminal | Calamares graphical install |
| Disk PID1 | after rsync, before `update-grub` | Calamares hook after initramfs (fragile) |
| initramfs | `update-initramfs` after PID1 swap | often stale (hook runs late) |
| First boot | `FIRST_BOOT_PENDING` + fast handoff | same (when hook runs) |

## Unified single-ISO profile

`build-universal-installer.sh` produces one image with both installer entry paths:

- Live defaults stay metal-compatible (`nomodeset quiet`, no `findiso` dependency).
- Primary install path remains terminal-driven `cogos-install apply`.
- Secondary install path exposes Calamares and runs `cogos-install-finish` via `shellprocess@cogos-finish` when Calamares assets are present.
- If Calamares assets are missing (`install_start.cfg`, `install.cfg`, or rootfs Calamares config), GRUB shows a non-dead-end fallback entry and keeps metal path primary.

Expected boot entries:
- `Wolf CoG OS — Live (metal baseline, recommended)`
- `Install Wolf CoG OS (Metal path - primary) ...`
- `Install Wolf CoG OS (Surprise path - Calamares)` (when available)
- `Install Wolf CoG OS (Surprise path unavailable - use Metal path)` (fallback)

Operator commands (metal path):

```text
sudo cogos-install plan --target /dev/sdX
sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX
```

Metal worked because live boot never touched `cognitive_init`, and disk install
refreshed initramfs **after** swapping init — the surprise path did the opposite.

Resume behavior:

```text
start/resume
  -> skip any step already marked completed
  -> run first non-completed step
  -> continue forward
```

Failure behavior:

```text
step N failed
  -> mark step N = failed
  -> write failure event + checkpoint
  -> run rollback in reverse order:
       firstboot <- network <- identity <- bootloader <- copy <- disk
  -> preserve logs/state for postmortem + resume
```

## Canonical Proof Path (Installer Contract)

Use this contract proof path for installer verification and gate evidence:

1. `checkpoints/<step>.status` shows per-step completion/failure markers.
2. `events.log` shows ordered execution and failure/resume events.
3. `state.json` is the canonical machine-readable summary for gates and CI tooling.
4. `validate-installer-state.py --require-proof --state <state.json>` is the canonical proof command.

Rule: proof and acceptance decisions must not depend on a live `target-root` mount after teardown/unmount; mounted-path inspection is optional diagnostics only.

## State Files

Installer state directory (default):
- Plan mode: `/tmp/cogos-installer`
- Apply mode: `/var/log/cogos-installer`

Primary artifacts:
- `checkpoints/<step>.status` step checkpoint files
- `events.log` append-only event stream
- `plan.txt` expanded execution plan
- `install-<mode>-<timestamp>.log` full installer run log
- `state.json` structured export for CI/postmortem tooling

## `state.json` Shape

`state.json` includes:

- `run` metadata: `system_hostname`, `target_disk`, `rootfs_source`, `cogos_tag`, `installer_version`, and timestamps
- `steps[]`: `name`, `status`, `started_at`, `finished_at`, `error`

This file is updated whenever checkpoints change, so external tooling can ingest it continuously.

## Operator Runbook Notes: Scenario 3 (Resume Path)

Scenario 3 validates resume behavior after an injected failure:

1. Run matrix Scenario 3 (`INSTALLER_TEST_SCENARIOS=3`) to force a `bootloader` failure.
2. Re-run installer with `--resume` using the same state directory.
3. Validate canonical proof from `state.json` using `validate-installer-state.py --require-proof`.
4. Confirm completed steps are skipped and execution starts at first non-completed step.
5. Record Scenario 3 evidence pointer in the program tracker before closing gate.

## Universal Boot Profile

Ship ISO: `Wolf-CoG-OS-universal-installer.iso` tag `universal-installer-1.0`.

Live session invariants (must hold on any machine):
- GRUB: `nomodeset quiet` only — no KMS, no findiso
- `cognitive_init` NOT active in live session (`COGOS_ENABLE_PID1=0` at build time)
- PID1 in live = stock systemd
- Boot replay from `debian-live-13.5.0-amd64-cinnamon.iso` → clean hybrid GPT (MBR + UEFI)

Install path:
```
sudo cogos-install plan --target /dev/sdX   # dry-run
sudo cogos-install apply --target /dev/sdX --yes --confirm-erase sdX
```
Preflight requirement: HAC v1 must be emitted and leak checks must pass before install commit.

Disk invariants (set by `cogos-install apply` + `cogos-install-finish`):
1. `/sbin/init` → `cognitive_init` (PID1 chain)
2. `update-initramfs -u` runs **after** step 1
3. `FIRST_BOOT_PENDING` marker dropped
4. `cogos-first-boot.service` fires once, then disables itself

## Runtime Freeze

Payload frozen at `metal-installer-1.0`. No runtime changes until `BOOT_PROOF.md` Gate A
(A1–A4) and Gate B (HP EliteDesk checklist) both pass. See `BOOT_PROOF.md` for full
proof gate, ISO inventory, and exact commands.

## Release proof gate (required)

Release-ready requires all of:
1. Successful universal ISO build (`build-universal-installer.sh`) with BIOS/UEFI replay preserved.
2. Successful QEMU smoke against the produced universal ISO.
3. Real-hardware sign-off checklist completed for:
   - Legacy BIOS desktop
   - UEFI desktop/laptop
   - Secure Boot off path

Flashing standard:
- Primary: Rufus DD mode.
- Fallback: balenaEtcher or Linux `dd` with sync.

## Universal Adapter Spec Link

For host adaptation contracts (probe/profile schema, kernel-family policy matrix,
GRUB/initramfs policy rules, and phased rollout), see:

- `wolf-cog-os/docs/UNIVERSAL_ADAPTER_IMPLEMENTATION_SPEC.md`
- `wolf-cog-os/docs/hac.schema.json`
