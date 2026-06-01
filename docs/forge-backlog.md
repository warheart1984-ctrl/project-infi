# Forge Backlog

Status: active canonical backlog for Forge implementation.
Priority model: P0 (must do now), P1 (next), P2 (post-milestone hardening)

## Program Tracker - Installer Scenario Gates

| Scenario | Gate status | Evidence pointer | Verification command |
|---|---|---|---|
| 1 (CleanDiskInstall_Core) | YELLOW | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario1`) | `INSTALLER_TEST_SCENARIOS="1" make installer-integration` |
| 3 (ResumeAfterInjectedFailure) | GREEN | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario3`) + `wolf-cog-os/INSTALLER_STATE_MACHINE.md` canonical proof/runbook notes | `INSTALLER_TEST_SCENARIOS="3" make installer-integration` |
| 6 (QemuIsoBootSmoke) | YELLOW | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario6`) | `INSTALLER_TEST_SCENARIOS="6" make installer-integration` |
| 4 (RollbackPathFailure) | YELLOW (promotion-required for Forge) | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario4`) | `INSTALLER_TEST_SCENARIOS="4" make installer-integration` |

## Execution Status

| Item | Status | Notes |
|---|---|---|
| P0-1 Define Forge profile contract skeleton | COMPLETE | Profile spec, loader, validator, and attestation scaffolding are present. |
| P0-2 Add governance ledger entries for Forge command surfaces | COMPLETE | Forge command surfaces are registered in `.github/governance/command-ledger.json`. |
| P0-3 Add Forge dry-run evidence path in CI public/self-hosted | COMPLETE | Public/self-hosted workflows emit `profile-resolution`, `profile-validation`, and dry-run `profile-attestation` artifacts. |
| P1-1 Wire Forge profile into build orchestration | COMPLETE | `Makefile`, `build-rootfs.sh`, and `build.sh` resolve Forge profile input and emit build metadata artifacts. |
| P1-2 Add Forge profile-aware matrix requirements | COMPLETE | Matrix summary includes Forge profile metadata and required-gate enforcement. |
| P1-3 Enable Forge RC signed artifact path | COMPLETE | RC workflow signs with `SIGNING_REQUIRED=1` and verifies artifacts. |
| P2-1 Promotion hardening for Forge channel | COMPLETE | Release promotion validates `source_run_id` plus optional profile identity via `validate-promotion-source.py`. |
| P2-2 Rollback scenario enforcement for Forge | COMPLETE | Promotion validation now requires Forge scenarios `1,3,4,6` and RC Forge required set includes rollback scenario `4`. |
| P2-3 Tighten drift policy from warn to fail | COMPLETE | Meta Architect approved 2026-05-27; workflow defaults and env fallbacks now use `fail`; dispatch can still select `warn` for audit runs. |
| P3-1 Forge ISO build path (GRUB + /forge layout + wrapper) | COMPLETE | Forge GRUB menu, `/forge` cockpit staging, package profile, pipeline specs, `build-forge-installer.sh`, and `make forge-installer` target are wired. |
| P3-2 Self-hosted Forge ISO CI smoke | COMPLETE | Self-hosted workflow runs forge layout smoke, emits `forge-build-state.json`, and enforces scenarios `1,3,4,6` when Forge profile is active; nightly schedule uses `forge-selfhosted`. |
| P3-3 Promotion readiness dry-run | COMPLETE | Local fixture dry-run, release workflow dry-run report emission, RC forge-rc channel metadata, and forge-build-state promotion checks are wired. |
| P4-1 First shippable Forge milestone gate | COMPLETE (Gate F decision pending) | Automated shippable gate (`make forge-shippable-gate`) wired to public CI + RC; Meta Architect ship approval and live workflow URLs still required to close Gate F. |
| P5 Substrate platform v2 | COMPLETE (asserted) | Multi-distro substrate classes, automatic classification, contract v2, substrate evolution ledger. |
| P6 Rootfs backend abstraction | COMPLETE (asserted, stubs) | Backend registry, bootstrap dispatcher, debootstrap production module, pacstrap/dnf/apk stubs. |
| P7 Variant pipelines + lineage | COMPLETE (asserted) | Pipeline v2 specs, emit/validate lineage, promotion wiring, dashboard. |
| P8 Multi-arch + cloud output | COMPLETE (asserted, stubs) | Arch matrix, cloud output registry, emit-cloud-image dispatcher stubs. |
| P9 Platform gate + nightly evolution | COMPLETE (Gate G **APPROVED** 2026-05-28) | `make forge-platform-gate`, dashboard, evolution ledgers. Live CI URL debt tracked. |
| P10 Replay adapters (multi-distro) | COMPLETE (asserted) | debian + ubuntu production adapters, dispatcher in build.sh, validate-replay-adapter. |
| P11 Second rootfs backend (pacstrap) | COMPLETE (asserted) | pacstrap production registry, arch-base.txt, daily-driver-arch pipeline, chroot dispatcher. |
| P12 Lineage reproducibility | COMPLETE (asserted) | git_commit/replay_adapter provenance, reproducibility validator, stable `--expected-lineage-id`. |
| P13 Nightly variant build mode | COMPLETE (asserted) | variant-matrix.json, `--build` mode, forge-nightly-build.sh. |
| P14 Cloud output production | COMPLETE (asserted) | raw-img + qcow2 modules, emit-pipeline-outputs.sh, registry production status. |
| P15 Universal substrate (Windows/macOS/Android) | COMPLETE (asserted, experimental) | Replay adapters, inject backends, invariants, pipelines, validators. |

## Latest Completed Task

### P4-1 First shippable Forge milestone gate automation

- **Owner role:** Inspector + Meta Architect
- **Paths:** `.github/scripts/check-forge-shippable-gate.py`, `docs/forge-shippable-gate.md`, `Makefile`, `.github/workflows/cogos-ci-public.yml`, `.github/workflows/cogos-rc.yml`, `docs/proof/forge/P4-1_SHIPPABLE_GATE_PROOF.md`
- **Definition of Done status:** Completed (automation); Gate F ship decision remains pending
  - Consolidated B-E checks into one gate report artifact.
  - Optional RC artifact validation path for Gate F bundle checks.
  - Public CI and RC workflow invoke shippable gate checks.
- **Verification command(s)**
  - `make forge-shippable-gate`
  - `python3 -m unittest tests.test_forge_shippable_gate`
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P3-3 Promotion readiness dry-run

- **Owner role:** Operator + Inspector
- **Paths:** `.github/workflows/cogos-release.yml`, `.github/workflows/cogos-rc.yml`, `.github/scripts/validate-promotion-source.py`, `.github/scripts/emit-promotion-dry-run-report.py`, `wolf-cog-os/scripts/test/promotion-dry-run.sh`, `wolf-cog-os/scripts/test/fixtures/promotion-forge-rc/`
- **Definition of Done status:** Completed
  - Forge promotion validation requires `forge-build-state.json` when profile is expected.
  - Local fixture dry-run passes promotion source validation for scenarios `1,3,4,6`.
  - Release workflow emits/uploads promotion dry-run report in `dry_run=true` mode.
  - RC artifacts include `channel=forge-rc` metadata when Forge profile is active.
- **Verification command(s)**
  - `bash wolf-cog-os/scripts/test/promotion-dry-run.sh --skip-verify`
  - `python3 -m unittest tests.test_validate_promotion_source`
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P3-2 Self-hosted Forge ISO CI smoke

- **Owner role:** Operator + Inspector
- **Paths:** `.github/workflows/cogos-ci-selfhosted.yml`, `wolf-cog-os/scripts/test/forge-iso-smoke.sh`, `wolf-cog-os/scripts/emit-forge-build-state.py`, `.github/workflows/cogos-ci-public.yml`
- **Definition of Done status:** Completed
  - Forge layout smoke runs after `make rootfs` when Forge profile is active.
  - `ci-artifacts/forge-build-state.json` is emitted after ISO build.
  - Forge profile runs enforce installer matrix scenarios `1,3,4,6`.
  - Nightly schedule activates `forge-selfhosted` profile for end-to-end validation.
- **Verification command(s)**
  - `bash wolf-cog-os/scripts/test/forge-iso-smoke.sh`
  - `python3 wolf-cog-os/scripts/emit-forge-build-state.py --profile forge-selfhosted --output ci-artifacts/forge-build-state.json`
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P2-3 Governance ledger default fail cutover

- **Owner role:** Meta Architect (approval), Drift Watcher (execution)
- **Paths:** `.github/workflows/cogos-ci-public.yml`, `.github/workflows/cogos-ci-selfhosted.yml`, `.github/workflows/cogos-rc.yml`, `.github/workflows/cogos-release.yml`, `docs/proof/forge/P2-3_GOVERNANCE_LEDGER_PREAPPROVAL_PROOF.md`
- **Definition of Done status:** Completed
  - Meta Architect approval recorded in proof packet.
  - Workflow dispatch defaults changed from `warn` to `fail`.
  - Env fallback `GOVERNANCE_LEDGER_MODE` changed from `warn` to `fail`.
- **Verification command(s)**
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P3-1 Forge ISO build path scaffolding

- **Owner role:** Coder + Architect
- **Paths:** `wolf-cog-os/scripts/patch_grub_merge.sh`, `wolf-cog-os/scripts/build.sh`, `wolf-cog-os/scripts/build-rootfs.sh`, `wolf-cog-os/scripts/build-forge-installer.sh`, `wolf-cog-os/scripts/lib/stage-forge-layout.sh`, `wolf-cog-os/forge/`, `wolf-cog-os/config/packages/forge.txt`, `Makefile`
- **Definition of Done status:** Completed
  - Forge boot menu exposes Run CoGOS / Enter Forge Mode / Recovery.
  - `/forge` cockpit layout is staged into rootfs on Forge profile builds.
  - Host-side entrypoint: `make forge-installer` or `bash wolf-cog-os/scripts/build-forge-installer.sh`.
  - Sample pipeline specs exist under `wolf-cog-os/forge/pipelines/`.
- **Verification command(s)**
  - `bash wolf-cog-os/scripts/test/test-forge-grub.sh`
  - `bash -n wolf-cog-os/scripts/build-forge-installer.sh`
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P2-2 Rollback scenario enforcement for Forge promotion readiness

- **Owner role:** Bug Hunter
- **Paths:** `wolf-cog-os/scripts/test/installer-matrix.py`, `.github/workflows/cogos-rc.yml`, `.github/workflows/cogos-release.yml`, `.github/scripts/validate-promotion-source.py`
- **Definition of Done status:** Completed
  - Forge promotion checks fail if required scenarios are missing/non-passing.
  - Required Forge promotion gate set now includes scenario `4` rollback path.
  - RC Forge runs enforce required gate set `1,3,4,6`.
- **Verification command(s)**
  - `python3 -m unittest tests/test_validate_promotion_source.py`
  - `python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only`
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

## Current Increment (In Progress)

### P10–P14 groundbreaking factory (asserted locally)

- **Verification**
  - `make forge-platform-gate`
  - `make forge-nightly-evolution`
  - `make forge-nightly-build` (requires `Wolf-CoG-OS-full.iso` or `COGOS_SUBSTRATE_ISO`)
  - `python3 -m unittest tests.test_replay_adapter tests.test_lineage_reproducibility tests.test_cloud_output tests.test_rootfs_backend`

### Gate F closure (Meta Architect action required)

- **Owner role:** Meta Architect + Operator
- **Pending**
  - Run Forge RC with `forge_profile=forge-selfhosted` and capture run URL/id.
  - Run stable release dry-run with that RC `source_run_id`.
  - Record Meta Architect **APPROVE** in `docs/forge-shippable-gate.md` and `docs/proof/forge/P4-1_SHIPPABLE_GATE_PROOF.md`.

### Gate G closure — COMPLETE

- **Decision:** **APPROVE** (2026-05-28)
- **Evidence:** `docs/forge-platform-gate.md`, `docs/proof/forge/P9_PLATFORM_GATE_PROOF.md`, `ci-artifacts/forge-platform-gate-report.json`
- **Debt:** attach public CI + RC lineage workflow URLs post-merge
