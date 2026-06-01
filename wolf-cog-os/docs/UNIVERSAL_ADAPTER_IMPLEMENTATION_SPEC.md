# Universal Adapter OS Implementation Spec

Status: Draft for implementation planning (docs + policy contracts only)  
Scope: `wolf-cog-os` universal ISO flow, no new runtime subsystem  
Compatibility target: one universal ISO, metal path primary, surprise path secondary

## 1) Objective

Adopt an explicit two-plane architecture and prevent cross-plane leaks:

1. separate **Governed Runtime Plane** from **Hardware Adapter Plane**,
2. probe hardware once in live session (`host_probe`) and normalize to `host_profile`,
3. select hardware adapter policy (`legacy-lts` or `modern-lts`) with evidence,
4. keep runtime blob immutable and shared across hardware selections,
5. gate releases on leak checks and old/new hardware proof.

This spec is docs + policy contracts only. It introduces no new always-on runtime subsystem.

## 2) Architecture Planes (Authoritative)

### 2.1 Governed Runtime Plane

Contains UL/ARIS/governance invariants and is treated as immutable runtime payload:

- UL and ARIS runtime components,
- invariant engine and ledger governance artifacts,
- halls/policy assets and governed runtime state contracts,
- packaged runtime blob target: `/system/runtime.ul` (logical contract artifact).

### 2.2 Hardware Adapter Plane

Contains machine-compatibility outputs:

- kernel artifacts and bootloader entries,
- initramfs images and module packs,
- firmware bundles and boot-mode-specific wiring,
- adapter outputs target paths:
  - `/boot/kernel-legacy`
  - `/boot/kernel-modern`

### 2.3 Architecture leak statement

Current instability patterns are treated as **architecture leaks** from plane mixing, for example:

- regenerating/changing governed runtime content as a side-effect of machine probing,
- adapter selection mutating runtime-plane assets,
- boot handoff selecting an adapter kernel but mounting an unintended runtime payload.

## 3) Contract Artifacts

- Schema: `wolf-cog-os/docs/hac.schema.json`
- Host profile output path (proposed): `/var/log/cogos-installer/host_profile.json`
- Policy decision output path (proposed): `/var/log/cogos-installer/policy_decision.json`
- Evidence log stream (proposed): `/var/log/cogos-installer/adapter-attestation.jsonl`
- Runtime blob manifest (proposed): `/var/log/cogos-installer/runtime_blob_manifest.json`

## 4) Three-Stage Build/Install Pipeline

### Stage A — Build immutable runtime blob first

- Build governed runtime once and freeze digest before adapter work.
- Output contract: `/system/runtime.ul` + digest manifest.
- No host-specific kernel/driver/firmware logic is allowed in this stage.

### Stage B — Build hardware adapter outputs

- Build adapter outputs independently:
  - `/boot/kernel-legacy`
  - `/boot/kernel-modern`
  - matched initramfs for each kernel family,
  - required firmware bundles,
  - GRUB boot entries for both families.
- Runtime blob must not be regenerated during this stage.

### Stage C — Bind runtime to adapter plane

- Bind both kernel families to the same runtime payload.
- Both boot paths must mount the same `/live/filesystem.squashfs`.
- No per-machine runtime regeneration is permitted at bind time.

## 5) `host_probe -> host_profile` Flow

### 5.1 Flow stages

1. **Probe** (live session, pre-apply and dry-run capable):
   - collect DMI, CPU flags, RAM size, storage bus type, GPU vendor hints, boot mode.
   - collect only inputs required for hardware adapter selection.
2. **Normalize**:
   - map probe output into HAC v1 structure.
   - validate against `hac.schema.json`.
3. **Score candidates**:
   - compute candidate scores for `legacy-lts` and `modern-lts`.
   - include reasons and risk flags.
4. **Emit decision**:
   - output selected family + kernel package + initramfs profile + grub profile.
   - mark decision mode (`report-only`, `dry-run`, or `enforced`).
5. **Attest**:
   - append immutable jsonl event with profile digest + policy digest + leak-check state + release-gate state.

### 5.2 Sample `host_profile.json`

```json
{
  "schema_version": "hac.v1",
  "profile_id": "hp-elitedesk-800g2-01",
  "generated_at": "2026-05-27T08:20:01Z",
  "plane_contract": {
    "runtime_plane": "governed-runtime",
    "adapter_plane": "hardware-adapter",
    "pipeline_stage": "stage-c-runtime-adapter-bind"
  },
  "probe": {
    "probe_version": "v0.1.0",
    "source": "live-session",
    "host_probe_sha256": "7cc3c5abf40dc2c23612ffcb98574b499de95cb3f7d4e58ea3fdd89a9a957d6f",
    "commands": [
      "dmidecode -s system-manufacturer",
      "lscpu",
      "lsblk -J",
      "lspci -nn",
      "test -d /sys/firmware/efi && echo uefi || echo bios"
    ]
  },
  "host": {
    "arch": "x86_64",
    "boot_mode": "uefi",
    "vendor": "HP",
    "product": "HP EliteDesk 800 G2",
    "cpu": {
      "vendor": "GenuineIntel",
      "model": "Intel(R) Core(TM) i5-6500 CPU",
      "cores": 4,
      "threads": 4,
      "flags": ["sse4_2", "avx2", "aes"]
    },
    "memory_mib": 16384,
    "storage": [
      { "name": "/dev/nvme0n1", "bus": "nvme", "size_gib": 476.9, "rotational": false }
    ],
    "graphics": [
      { "vendor": "intel", "device": "HD Graphics 530", "driver_hint": "safe-nomodeset" }
    ]
  },
  "compat": {
    "legacy_bias": 62,
    "modern_bias": 79,
    "risk_flags": ["uefi_secureboot_unknown"]
  },
  "policy_candidates": [
    {
      "family": "legacy-lts",
      "score": 620,
      "reasons": ["integrated intel gpu", "conservative fallback preference"],
      "kernel_package": "linux-image-amd64",
      "initramfs_modules_profile": "broad-compat",
      "grub_profile": "metal-safe"
    },
    {
      "family": "modern-lts",
      "score": 790,
      "reasons": ["nvme primary storage", "sufficient memory", "newer cpu generation"],
      "kernel_package": "linux-image-amd64",
      "initramfs_modules_profile": "standard",
      "grub_profile": "metal-default"
    }
  ],
  "selection": {
    "selected_family": "modern-lts",
    "selected_kernel_package": "linux-image-amd64",
    "selected_kernel_path": "/boot/kernel-modern",
    "selected_initramfs_path": "/boot/initramfs-modern.img",
    "selected_initramfs_modules_profile": "standard",
    "selected_grub_profile": "metal-default",
    "decision_mode": "dry-run",
    "decision_reasons": [
      "modern-lts score higher by 170",
      "no blocking risk flag for modern-lts"
    ]
  },
  "runtime_binding": {
    "runtime_blob_path": "/system/runtime.ul",
    "runtime_blob_sha256": "a4f877ab5d804c65ff5e15fa1908ef19fb678fbdce7975ec385ce55ed6ef89c2",
    "live_squashfs_path": "/live/filesystem.squashfs",
    "dual_kernel_same_runtime": true
  },
  "attestation": {
    "policy_version": "v0.1.0",
    "policy_digest_sha256": "30014d3702f4af7f782181194467ad41f404f5f7f42c8e58d3fd34490537f0fd",
    "stage_digests": {
      "stage_a_runtime_blob_sha256": "a4f877ab5d804c65ff5e15fa1908ef19fb678fbdce7975ec385ce55ed6ef89c2",
      "stage_b_adapter_bundle_sha256": "ad7de6ebfba1731f8f6853beea179b10c771a95835ce6f8fd0d00fb6e6b56af1",
      "stage_c_binding_sha256": "5cb162599b1ce0458cd0e2fb3b44d3eff5ea1f3f1cb7ce6d1139f065799a73d0"
    },
    "leak_checks": [
      { "check_id": "initramfs-mismatch", "status": "pass" },
      { "check_id": "module-version-drift", "status": "pass" },
      { "check_id": "policy-handoff-integrity", "status": "pass" },
      { "check_id": "squashfs-path-consistency", "status": "pass" }
    ],
    "evidence_log": "/var/log/cogos-installer/adapter-attestation.jsonl",
    "governance_mode": "audit-only",
    "release_gate": "candidate"
  }
}
```

## 6) Kernel Family Selection Matrix

| Signal | `legacy-lts` preference | `modern-lts` preference |
|---|---|---|
| Boot mode | BIOS legacy machine with older firmware behavior | UEFI host with clean firmware boot behavior |
| GPU hints | older iGPU/dGPU or unknown KMS reliability | newer iGPU/dGPU with no known KMS blocker |
| Storage | SATA-only, older controller quirks | NVMe/modern SATA controller, clean probe |
| Memory | low memory or constrained systems | >= 8 GiB typical desktop/laptop |
| Risk flags | any hard risk increases legacy score | no hard risk, modern score dominates |

Policy rules:

- always compute both candidates and log score rationale.
- if scores are tied or within tie band (`<= 50`), choose `legacy-lts` as compatibility default.
- if any hard blocker risk is set (e.g. `old_bios` + `legacy_gpu`), force `legacy-lts`.
- `modern-lts` becomes selectable only when no blocker risk and score margin exceeds tie band.

## 7) GRUB and Initramfs Generation Rules

### 7.1 Universal ISO invariants (unchanged from current direction)

- Live default remains metal-compatible (`nomodeset quiet`).
- Primary install path remains terminal `cogos-install plan/apply`.
- Surprise Calamares remains secondary menu path.
- If Calamares assets are missing, GRUB must expose fallback guidance, not fail build by default.

### 7.2 ISO dual-kernel GRUB contract

At build time:

- universal menu template remains driven by existing `patch_grub_universal_installer`.
- GRUB exposes dual kernel-family entries in the universal install path:
  - `legacy-lts` entry -> adapter target `/boot/kernel-legacy` (+ matched initramfs),
  - `modern-lts` entry -> adapter target `/boot/kernel-modern` (+ matched initramfs).
- both entries must resolve to the same runtime filesystem payload (`/live/filesystem.squashfs`).
- selected HAC grub profile maps to:
  - `metal-default` -> standard live + metal install submenu,
  - `metal-safe` -> safe-mode emphasis (`cogos.safe=1 governance=off`) for fallback entries,
  - `universal-fallback` -> no Calamares dependency and explicit install guidance entry.

Guardrails (required):

- fail build/release if GRUB entries point at different squashfs paths.
- fail build/release if kernel entry references wrong initramfs family.
- fail build/release if selected family handoff differs from policy decision artifact.
- do not allow ad-hoc path rewrites that drift from `/live/filesystem.squashfs`.

At install-time policy reporting:

- record which GRUB profile would be applied for this host.
- Phase 0/1: report-only (no mutation of shipped GRUB templates).
- Phase 2: enforce allowed profile-specific flags only via controlled template branches.

### 7.3 Initramfs generation contract

- Keep existing proven order in installer pipeline: disk -> copy -> bootloader -> identity -> network -> firstboot.
- For apply path, preserve invariant:
  1. set `/sbin/init` chain to `cognitive_init`,
  2. run `update-initramfs -u`,
  3. then `update-grub`.
- HAC adds policy metadata only:
  - `initramfs_modules_profile` selected (`minimal-safe`, `standard`, `broad-compat`),
  - evidence emitted with chosen profile and reason.
- No new initramfs runtime hooks are introduced by this spec.

## 8) Sample Policy Decision Output

`policy_decision.json` example:

```json
{
  "schema_version": "hac.v1",
  "profile_id": "hp-elitedesk-800g2-01",
  "decision_mode": "enforced",
  "selected_family": "modern-lts",
  "selected_kernel_package": "linux-image-amd64",
  "selected_kernel_path": "/boot/kernel-modern",
  "selected_initramfs_path": "/boot/initramfs-modern.img",
  "selected_initramfs_modules_profile": "standard",
  "selected_grub_profile": "metal-default",
  "family_scores": {
    "legacy-lts": 620,
    "modern-lts": 790
  },
  "runtime_binding": {
    "runtime_blob_path": "/system/runtime.ul",
    "runtime_blob_sha256": "a4f877ab5d804c65ff5e15fa1908ef19fb678fbdce7975ec385ce55ed6ef89c2",
    "live_squashfs_path": "/live/filesystem.squashfs"
  },
  "adapter_outputs": {
    "legacy_kernel_path": "/boot/kernel-legacy",
    "modern_kernel_path": "/boot/kernel-modern"
  },
  "leak_checks": [
    { "check_id": "squashfs-path-consistency", "status": "pass" },
    { "check_id": "initramfs-mismatch", "status": "pass" },
    { "check_id": "module-version-drift", "status": "pass" },
    { "check_id": "policy-handoff-integrity", "status": "pass" }
  ],
  "hard_blockers": [],
  "decision_reasons": [
    "modern-lts exceeded legacy-lts by 170 points",
    "no hard blockers present"
  ],
  "generated_at": "2026-05-27T08:22:00Z"
}
```

## 9) Architecture Leak Checks and Gates

Required leak checks for candidate and release builds:

1. **`initramfs-mismatch`**
   - detect mismatch between selected kernel family and initramfs module profile.
   - fail if legacy kernel is paired with modern-only module map (or inverse).
2. **`module-version-drift`**
   - detect module tree version mismatch against selected kernel artifact.
   - fail on unresolved module ABI/version drift.
3. **`policy-handoff-integrity`**
   - ensure chosen policy family equals actual GRUB/default handoff target.
   - fail when policy selects one family but boot entry points to the other.
4. **`squashfs-path-consistency`**
   - assert all boot entries mount the same squashfs path (`/live/filesystem.squashfs`).
   - fail if any entry diverges or path is rewritten inconsistently.

Gate behavior:

- any leak check failure blocks release (`release_gate=blocked`).
- dry-run mode may continue install flow but must emit blocking evidence.
- enforced mode must fail fast before final ISO promotion.

## 10) Proof Gates (Old/New Hardware Release Criteria)

Release approval for enforced selection requires all gates:

### Gate O (old hardware compatibility)

- at least 2 legacy-leaning systems (BIOS-capable and/or older GPU generation),
- successful live boot to desktop,
- successful `cogos-install plan` and `apply`,
- successful reboot from disk with expected PID1 handoff,
- no installer regressions versus current metal baseline.

### Gate N (new hardware compatibility)

- at least 2 modern systems (UEFI, NVMe, recent CPU generation),
- same success criteria as Gate O,
- at least 1 modern host selected to `modern-lts` in dry-run and later enforced mode.

### Gate M (matrix and CI)

- existing matrix smoke and loopback scenarios remain green,
- universal preflight must pass or emit controlled warning path,
- release verification scripts remain passing (`verify-surprise-release.sh` and existing proof checks),
- architecture leak checks must pass on matrix artifacts.

### Release criteria by phase

- Phase 0: docs complete, no enforcement.
- Phase 1: dry-run probe emits HAC artifacts + attestation logs, no install behavior change.
- Phase 2: enforced selection allowed only after Gate O + Gate N + Gate M pass for two consecutive release candidates.

## 11) Fail-safe and Governance Hooks

Fail-safe requirements:

- on schema validation failure: fallback to `legacy-lts`, `metal-safe`, `broad-compat`; log `release_gate=blocked`.
- on missing probe fields: mark decision as `audit-only`, keep default metal path behavior.
- on Calamares asset absence: keep metal primary and explicit surprise fallback guidance (current preflight behavior).
- on runtime binding mismatch: block release, preserve current default metal-safe entry behavior.

Governance requirements:

- all policy decisions appended to `adapter-attestation.jsonl`,
- each record includes profile id, policy digest, decision mode, selected family, and gate state,
- each record includes Stage A/B/C digests and leak-check results,
- records are append-only for release evidence and postmortem traceability,
- governance mode defaults:
  - Phase 0: `audit-only`
  - Phase 1: `audit-only`
  - Phase 2: `strict` for release builds, `audit-only` for developer builds.

## 12) Phased Rollout Plan

### Phase 0 — Documentation and schema

- land this spec + `hac.schema.json`,
- define sample artifacts and scoring policy,
- no script behavior changes required.

### Phase 1 — Dry-run host probe

- add non-blocking probe + normalization command in installer/test path,
- emit `host_profile.json` + `policy_decision.json` + attestation log,
- validate schema in CI and matrix runs,
- emit Stage A/B/C metadata and leak-check results,
- do not alter runtime payload generation behavior.

### Phase 2 — Enforced selection

- gate enforcement behind explicit build/install flag,
- apply selected family/profile rules in controlled build/install branches,
- enforce dual-kernel + single-runtime binding checks,
- require gate evidence before making enforcement default.

## 13) Mapping to Current Scripts (Practical)

This spec maps to current script boundaries:

- `scripts/build-universal-installer.sh`:
  - remains authoritative for universal ISO env/profile setup.
  - maps to Stage A/B/C orchestration metadata only in Phase 0/1.
- `scripts/preflight-universal-installer.sh`:
  - remains source of truth for Calamares asset checks and BIOS/UEFI replay checks.
  - adds leak checks for squashfs path consistency and handoff integrity reporting.
- `scripts/build.sh`:
  - already resolves `filesystem.squashfs` source candidates and rebuilds squashfs.
  - is the correct place to emit and validate single-runtime-path guardrails.
- `scripts/patch_grub_merge.sh` (`patch_grub_universal_installer`):
  - remains source of GRUB menu generation.
  - is the correct place to enforce dual-kernel entries and matched initramfs pairing rules.
- installer pipeline in `INSTALLER_STATE_MACHINE.md` and `cogos-install` flow:
  - proven step order remains unchanged.
  - HAC outputs become sidecar artifacts + policy evidence in Phase 1.
  - no per-machine runtime regeneration allowed in apply flow.

## 14) Non-goals

- no new always-on host agent,
- no replacement of existing universal build scripts,
- no modification to cognitive runtime behavior in live session,
- no branching product line into multiple ship ISOs,
- no per-machine regeneration of governed runtime blob.
