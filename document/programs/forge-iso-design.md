# Forge ISO Self-Hosting Architecture Design

Status: pre-coding design  
Scope: add a self-hosting "Forge ISO" track that reuses current CoGOS build/release controls  
Out of scope: product/runtime feature implementation

## Goals

- Add a first-class Forge ISO variant that can build and validate itself through existing CoGOS CI/release paths.
- Reuse existing build primitives (`rootfs`, `iso-tree`, installer matrix, signing, release promotion) rather than introducing a parallel pipeline.
- Keep deterministic, reproducible artifacts with explicit profile contracts and governance checks.
- Add dry-run and evidence outputs so rollout can be staged safely.

## Non-goals

- No new runtime behavior in this phase.
- No replacement of existing metal/surprise/universal installers.
- No bypass of current signing, verification, and release promotion controls.
- No immediate enforcement-only rollout; design assumes warn/audit-first gates.

## Current Pipeline Map (Repository Discovery)

### CI and release entrypoints

1. `\.github\workflows\cogos-ci-public.yml`
   - Fast PR/main checks: governance preflight, installer smoke, artifact upload.
2. `\.github\workflows\cogos-ci-selfhosted.yml`
   - Heavy self-hosted flow: `make rootfs`, `make iso-tree`, installer matrix, performance gates, optional signing.
3. `\.github\workflows\cogos-rc.yml`
   - RC build/publish path: heavy build, matrix/perf history analysis, required signing and verify, prerelease metadata.
4. `\.github\workflows\cogos-release.yml`
   - Stable promotion path: download RC artifacts, verify signatures/checksums, release notes/index updates, publish.

### Build orchestration and variant logic

5. `\Makefile`
   - Canonical targets consumed by workflows: `rootfs`, `iso-tree`, `installer-smoke`, `installer-integration`, `sign-artifacts`, `verify-artifacts`.
6. `\wolf-cog-os\scripts\build-rootfs.sh`
   - Rootfs assembly and package profile application from `\wolf-cog-os\config\packages\base.txt` and `\wolf-cog-os\config\packages\daily-driver.txt`.
7. `\wolf-cog-os\scripts\build.sh`
   - Core ISO remaster state machine (extract ISO, stage rootfs/payload, profile patching, squashfs rebuild, ISO replay).
8. `\wolf-cog-os\scripts\build_iso.sh`
   - Boot replay and fallback logic (`xorriso` replay, mkisofs fallback, ISO size guards).

### Boot/profile templating and installer behavior

9. `\wolf-cog-os\scripts\patch_grub_merge.sh`
   - Profile-driven GRUB generation (`surprise`, `metal`, `universal`, default merge).
10. `\wolf-cog-os\scripts\patch_calamares_surprise.sh`
   - Optional Calamares post-install hook insertion.
11. `\wolf-cog-os\scripts\build-metal-installer.sh`, `build-surprise-installer.sh`, `build-universal-installer.sh`
   - Existing variant wrappers setting `COGOS_BOOT_PROFILE` and build-time flags.
12. `\wolf-cog-os\scripts\cogos-installer.sh`
   - Apply/plan installer state machine with resume/rollback checkpoints and state export.

### Governance, signing, and release evidence

13. `\.github\scripts\validate-governance-ledger.py` + `\.github\governance\command-ledger.json`
   - Contract drift checks across Make targets/scripts/workflow consumers.
14. `\.github\scripts\sign-artifacts.sh` and `\.github\scripts\verify-artifacts.sh`
   - Manifest generation + minisign signing/verification.
15. `\.github\scripts\generate-release-notes.py` and `update-build-index.py`
   - Release notes + index metadata updates.
16. `\wolf-cog-os\scripts\test\installer-matrix.py` and `installer-qemu-smoke.sh`
   - Current smoke and scenario matrix validation.

## Target Forge ISO Architecture

### Design intent

Introduce a new build profile family (`forge`) that is assembled by existing `build.sh` and promoted by existing RC/stable workflows with minimal structural change.

### High-level model

1. **Profile Spec Layer**
   - New declarative profile specs define forge variant behavior (boot menu shape, payload mode, installer behavior, test requirements, signing policy).
2. **Build Execution Layer**
   - Existing scripts consume profile spec and map to current env/branch behavior.
3. **Validation/Evidence Layer**
   - Existing matrix and QEMU smoke expanded with profile-specific required scenarios.
4. **Promotion Layer**
   - Existing RC/stable flows produce and verify Forge ISO artifacts with explicit channel metadata.

### Proposed new profile family

- `forge-selfhosted` (initial)
  - CI-selfhosted and RC build capable.
  - Uses existing metal-safe defaults unless stricter profile gates are enabled.
- `forge-dev` (optional later)
  - Local experimentation with relaxed enforcement but same schema.

## Connection Points to Existing Pipeline (Explicit)

The following are concrete extension seams to avoid creating a disconnected pipeline:

1. `\Makefile`
   - Extend with profile-aware targets (for example `iso-profile`, `installer-integration-profile`) that delegate to existing targets by env.
2. `\wolf-cog-os\scripts\build.sh`
   - Inject profile spec load/validation before step execution and emit profile attestation JSON.
3. `\wolf-cog-os\scripts\patch_grub_merge.sh`
   - Add `forge` branch for GRUB/menu policy while preserving existing `metal/universal/surprise`.
4. `\wolf-cog-os\scripts\build-rootfs.sh`
   - Add profile package overlays sourced from a new profile definition path (no hardcoded branch logic).
5. `\wolf-cog-os\scripts\test\installer-matrix.py`
   - Add profile-driven scenario requirements and summary fields (`profile_id`, `required_gate_set`).
6. `\.github\workflows\cogos-ci-selfhosted.yml`
   - Add matrix axis/profile input for forge build path and profile evidence upload.
7. `\.github\workflows\cogos-rc.yml` and `cogos-release.yml`
   - Include forge channel metadata and required artifact checks without changing signing core.
8. `\.github\governance\command-ledger.json`
   - Register new profile commands/consumers so governance drift is caught early.

### New components (proposed)

- `\wolf-cog-os\profiles\forge\forge-selfhosted.yaml`
- `\wolf-cog-os\profiles\forge\forge-dev.yaml` (optional phase 2)
- `\wolf-cog-os\scripts\lib\profile-loader.sh`
- `\wolf-cog-os\scripts\validate-profile.py`
- `\wolf-cog-os\scripts\emit-profile-attestation.py`
- `\.github\scripts\validate-profile-attestation.py`

## Pipeline Spec Schema Proposal

Store specs under `\wolf-cog-os\profiles\*.yaml`.

```yaml
schema_version: forge-iso.v1
profile_id: forge-selfhosted
extends: universal
channel: rc
artifact:
  output_name: Wolf-CoG-OS-forge-selfhosted.iso
  signing_required: true
  manifest_required: true
build:
  boot_profile: forge
  build_from_tree: true
  enable_pid1_live: false
  squashfs_comp: xz
  replay_iso_source: debian-live
rootfs:
  package_sets:
    - base
    - forge
  payload_mode: merge
installer:
  state_machine: disk-copy-bootloader-identity-network-firstboot
  rollback_enabled: true
  resume_enabled: true
grub:
  template: forge
  live_default: metal-safe
  include_surprise_path: false
governance:
  ledger_policy: warn
  required_checks:
    - governance-ledger
    - profile-schema
    - profile-attestation
validation:
  dry_run_required: true
  qemu_smoke_required: true
  matrix_required_scenarios: [1, 3, 6]
  reproducibility:
    checksum_stability_runs: 2
promotion:
  rc_artifact_group: forge-rc-artifacts
  stable_requires_signature_verify: true
```

## Boot UX / Menu Flow (Forge Profile)

1. Default entry: Forge live (metal-safe baseline).
2. Secondary entry: Forge governed live (if enabled by profile policy).
3. Install submenu:
   - Terminal-driven `cogos-install` path as primary.
   - Optional secondary path disabled by default unless explicitly enabled in profile.
4. Guidance submenu:
   - Profile-specific install commands and recovery hints.
5. Advanced submenu:
   - Existing firmware entry and diagnostics.

Design rule: Forge menu generation must remain template-driven from `patch_grub_merge.sh` with profile flags; no manual inline one-off editing in workflows.

## Execution Engine / State Machine

### Build engine states (new wrapper around existing scripts)

`init -> load_profile -> validate_profile -> build_rootfs -> remaster_iso -> emit_attestation -> sign -> verify -> publish_artifacts -> complete`

Failure path:

`any_state_failed -> collect_evidence -> mark_gate_failed -> stop`

### Installer state machine (existing, retained)

`disk -> copy -> bootloader -> identity -> network -> firstboot` with checkpoint/resume/rollback semantics from `cogos-installer.sh`.

### State/evidence outputs (proposed)

- `ci-artifacts/profile-attestation.json`
- `ci-artifacts/profile-validation.json`
- `ci-artifacts/forge-build-state.json`
- Existing `state.json`, `matrix-summary.json`, `performance-report.json`, `artifact-manifest.json`.

## Security and Governance Integration

### Existing controls to preserve

- Governance preflight in all relevant workflows via `validate-governance-ledger.py`.
- Minisign signing and verification for promotable artifacts.
- Artifact manifest hashing and verify checks.
- RC -> stable promotion requiring verify in `cogos-release.yml`.

### Forge-specific controls (proposed)

- Profile schema validation gate before build.
- Profile attestation binding profile digest to produced artifact digest.
- Deterministic build config capture (tool versions + inputs).
- Strict separation of profile data and script logic (no untracked env override precedence).

## Seam / Bug Risk Register (Pre-coding)

| Risk | Seam | Likelihood | Impact | Mitigation check |
|---|---|---:|---:|---|
| Profile drift between CI and local | env vars vs profile file precedence (`build.sh`, workflows) | High | High | Add single precedence contract + emit resolved profile JSON in artifacts |
| Non-idempotent state carryover | reused `/tmp` work dirs and stale matrix outputs | Medium | High | Per-run unique work dir + explicit cleanup contract + state hash in attestation |
| Reproducibility variance | host toolchain and replay source differences | High | High | Capture tool versions + replay ISO digest + dual-build checksum comparison gate |
| Signing bypass/misconfiguration | optional signing in nightly/selfhosted | Medium | High | For forge channel force `SIGNING_REQUIRED=1` in RC + release verify hard gate |
| Governance ledger staleness | new commands not added to ledger | High | Medium | Add ledger entries in same PR and fail CI on missing consumers in forge flows |
| Rollback inconsistencies | installer resume/rollback under profile-specific conditions | Medium | High | Mandatory matrix scenarios 3+4 for forge before RC promotion |
| Host contamination | build from mutable host state/tool cache | Medium | High | Record input digests and disallow untracked local payload paths in CI mode |
| Boot menu regressions | hand-edited GRUB branches diverge | Medium | High | Template branch tests + snapshot diff test on generated grub.cfg |
| Artifact promotion mismatch | wrong RC run promoted | Low | High | Require `source_run_id` + artifact prefix/profile-id match check before release |
| Perf gate blind spots | forge path not represented in baseline history | Medium | Medium | Separate profile-tagged history windows and burn-in before fail mode |

## Validation Strategy

### 1) Dry-run validation (mandatory first)

- Profile load + schema validate only, no ISO build.
- Output resolved profile and attestation skeleton.
- Validate governance ledger references for new commands.

### 2) Local smoke (developer path)

- `make rootfs` + profile-driven `make iso-tree`.
- `installer-smoke` with explicit state dir.
- Verify generated profile artifacts exist and are parseable.

### 3) QEMU smoke

- Reuse `installer-qemu-smoke.sh` for produced Forge ISO.
- Add both BIOS and UEFI smoke variants in profile gates (UEFI can remain warn-only initially).

### 4) Installer matrix

- Require at least scenarios `1,3,6` for phase 1.
- Add scenario `4` (rollback) as phase-2 promotion requirement.
- Persist matrix summary with `profile_id`.

### 5) CI gates

- Public CI: schema + governance + smoke.
- Self-hosted CI: full build + matrix + perf gate in warn mode initially.
- RC: required signing and verify.
- Stable release: promote only from verified RC artifacts.

## Rollout Phases (Dependency Order + Go/No-Go)

### Phase 0 - Infra contracts only

Dependencies:
1. Profile schema and file locations defined.
2. Governance ledger entries drafted for new commands.
3. Workflow wiring design reviewed.

Acceptance criteria:
- `docs/forge-iso-design.md` approved.
- Profile schema proposal accepted.
- No behavior changes merged yet.

Go/No-go:
- No-go if profile precedence rules are unresolved.

### Phase 1 - Non-enforcing plumbing

Dependencies:
1. Profile loader + validator in place.
2. CI/public checks run in warn mode.
3. Attestation artifacts emitted but non-blocking.

Acceptance criteria:
- Forge profile dry-run passes in CI.
- Existing metal/universal builds remain unchanged.
- Governance checks cover new command surfaces.

Go/No-go:
- No-go on any regression in current installer matrix scenarios.

### Phase 2 - Build + test enforcement

Dependencies:
1. Forge ISO build path active in self-hosted + RC.
2. QEMU/matrix gates bound to profile.
3. Signature verification required for forge RC outputs.

Acceptance criteria:
- Two consecutive successful RC runs for forge profile.
- Reproducibility check passes (same inputs -> matching digest expectations).

Go/No-go:
- No-go on checksum mismatch without explained input changes.

### Phase 3 - Promotion readiness

Dependencies:
1. Release workflow can promote forge-tagged RC artifacts.
2. Build index and release notes include forge channel metadata.
3. Rollback and recovery evidence complete.

Acceptance criteria:
- Stable promotion dry-run succeeds.
- Full signing/verify path validated end-to-end.

Go/No-go:
- No-go if promotion can select wrong profile artifacts.

## Recommended First Milestone (Design/Infra Prep Only)

Implement only the contract layer:

1. Add profile spec location + schema validator stubs.
2. Add governance ledger entries for planned forge commands/consumers.
3. Add non-executing workflow dry-run stage to parse profile and emit attestation skeleton.
4. Add documentation for precedence and gate contract.

This milestone creates safe seams for later coding while minimizing risk of breakage in existing CoGOS release flow.
