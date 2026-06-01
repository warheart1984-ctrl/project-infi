# Forge Backlog

Status: actionable planning backlog  
Priority model: P0 (must do now), P1 (next), P2 (after first shippable milestone)

## Program Tracker - Installer Scenario Gates

| Scenario | Gate status | Evidence pointer | Verification command |
|---|---|---|---|
| 1 (CleanDiskInstall_Core) | YELLOW | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario1`) | `INSTALLER_TEST_SCENARIOS="1" make installer-integration` |
| 3 (ResumeAfterInjectedFailure) | GREEN | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario3`) + `wolf-cog-os/INSTALLER_STATE_MACHINE.md` canonical proof/runbook notes | `INSTALLER_TEST_SCENARIOS="3" make installer-integration` |
| 6 (QemuIsoBootSmoke) | YELLOW | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario6`) | `INSTALLER_TEST_SCENARIOS="6" make installer-integration` |
| 4 (RollbackPathFailure) | YELLOW (tracked gate) | `wolf-cog-os/scripts/test/installer-matrix.py` (`scenario4`) | `INSTALLER_TEST_SCENARIOS="4" make installer-integration` |

## P0 - Execute now

### P0-1 Define Forge profile contract skeleton

- **Owner role:** Architect + Coder
- **Paths:** `wolf-cog-os/profiles/forge/`, `wolf-cog-os/scripts/lib/profile-loader.sh`, `wolf-cog-os/scripts/validate-profile.py`
- **Definition of Done**
  - Forge profile schema stub and `forge-selfhosted` sample exist.
  - Profile precedence rules are documented and testable.
  - No existing profile path behavior regresses.
- **Verification command(s)**
  - `python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only`
  - `bash -n wolf-cog-os/scripts/build.sh`
  - `bash -n wolf-cog-os/scripts/build-rootfs.sh`

### P0-2 Add governance ledger entries for Forge command surfaces

- **Owner role:** Seam Hunter
- **Paths:** `.github/governance/command-ledger.json`, `.github/scripts/validate-governance-ledger.py`
- **Definition of Done**
  - New/changed Forge-related commands and consumers are represented in ledger.
  - Ledger validator reports zero errors in fail mode for updated entries.
- **Verification command(s)**
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`

### P0-3 Add Forge dry-run evidence path in CI public/self-hosted

- **Owner role:** Operator + Coder
- **Paths:** `.github/workflows/cogos-ci-public.yml`, `.github/workflows/cogos-ci-selfhosted.yml`
- **Definition of Done**
  - Workflows emit profile validation/attestation skeleton artifacts for Forge.
  - New checks are non-enforcing (warn/audit-first).
  - Existing installer smoke and artifact upload behavior remains intact.
- **Verification command(s)**
  - `python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only`
  - `make installer-smoke INSTALLER_ARGS="--state-dir /tmp/cogos-installer-state-local"`

## P1 - Next wave

### P1-1 Wire Forge profile into build orchestration

- **Owner role:** Coder
- **Paths:** `Makefile`, `wolf-cog-os/scripts/build.sh`, `wolf-cog-os/scripts/build-rootfs.sh`
- **Definition of Done**
  - Build path can resolve Forge profile inputs without breaking existing metal/universal/surprise modes.
  - Build emits Forge attestation metadata to `ci-artifacts/`.
- **Verification command(s)**
  - `make rootfs`
  - `ISO=/tmp/debian-live-amd64-cinnamon.iso make iso-tree`

### P1-2 Add Forge profile-aware matrix requirements

- **Owner role:** Bug Hunter + Inspector
- **Paths:** `wolf-cog-os/scripts/test/installer-matrix.py`
- **Definition of Done**
  - Forge required scenarios (`1,3,6`) are enforced for milestone path.
  - Matrix summary includes profile identifier and gate set.
- **Verification command(s)**
  - `INSTALLER_TEST_SCENARIOS="1,3,6" make installer-integration`

### P1-3 Enable Forge RC signed artifact path

- **Owner role:** Operator
- **Paths:** `.github/workflows/cogos-rc.yml`, `.github/scripts/sign-artifacts.sh`, `.github/scripts/verify-artifacts.sh`
- **Definition of Done**
  - Forge RC artifacts are signed with `SIGNING_REQUIRED=1`.
  - Signature and manifest verify passes in RC flow.
- **Verification command(s)**
  - `SIGNING_REQUIRED=1 make sign-artifacts ARTIFACT_DIR="ci-artifacts"`
  - `make verify-artifacts ARTIFACT_DIR="ci-artifacts"`

## P2 - After first shippable milestone

### P2-1 Promotion hardening for Forge channel

- **Owner role:** Drift Watcher + Operator
- **Paths:** `.github/workflows/cogos-release.yml`, `.github/scripts/update-build-index.py`
- **Definition of Done**
  - Promotion path validates Forge artifact identity (`source_run_id`, profile/channel metadata).
  - Dry-run to publish transition checklist is approved.
- **Verification command(s)**
  - Release workflow dispatch dry-run with `dry_run=true` and valid `source_run_id`

### P2-2 Rollback scenario enforcement for Forge

- **Owner role:** Bug Hunter
- **Paths:** `wolf-cog-os/scripts/test/installer-matrix.py`
- **Definition of Done**
  - Scenario `4` rollback gate required for Forge promotion readiness.
  - Failures open automatic P0 defects.
- **Verification command(s)**
  - `INSTALLER_TEST_SCENARIOS="4" make installer-integration`

### P2-3 Tighten drift policy from warn to fail

- **Owner role:** Meta Architect (decision), Drift Watcher (execution)
- **Paths:** `.github/scripts/validate-governance-ledger.py`, workflow `--mode` usage
- **Definition of Done**
  - Criteria for fail-mode cutover documented and approved.
  - Target workflows updated with explicit enforcement policy.
- **Verification command(s)**
  - `python3 .github/scripts/validate-governance-ledger.py --mode fail`
