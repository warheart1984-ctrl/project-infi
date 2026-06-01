# Ground-Up Debian Cinnamon Rebuild Plan

Status: `asserted` (design + scaffold only, full rebuild proof pending)  
Scope: clean-room pipeline scaffold from pristine Debian live ISO to Wolf CoG OS artifact  
Primary objective: minimize regressions seen in prior in-place mutation pipelines

Governance authority and proof requirements:
- `META_ARCHITECT_LAWBOOK.md`
- `REPO_PROOF_LAW.md`
- `templates/PROOF_BUNDLE_TEMPLATE.md`
- `docs/TRUST_BUNDLE_SPEC.md`

## 1) Goals

- Rebuild from a known Debian Cinnamon live ISO baseline each run (no hidden mutable state).
- Separate runtime-plane customization from hardware adapter-plane behavior.
- Enforce strict boot-path invariants before artifact promotion.
- Produce deterministic replay evidence (source ISO hash + stage manifests + command logs).
- Gate progression on proof artifacts, not on assumptions.

## 2) Architecture Plane Separation

### Runtime Plane (governed payload)

Contains payload and policy-controlled runtime changes that must remain stable across hardware:
- rootfs payload overlay,
- runtime identity files and controlled init handoff policy,
- runtime manifests and governance metadata.

Rules:
- no hardware probing decisions mutate runtime payload content directly,
- no ad-hoc bootloader branching from runtime stage scripts,
- runtime-plane outputs are content-addressed and hashed.

### Hardware Adapter Plane

Contains hardware-compatibility and boot wiring:
- bootloader entries and kernel cmdline policy,
- initramfs compatibility assumptions,
- BIOS/UEFI boot replay and ISO boot metadata handling.

Rules:
- hardware adapter stage may not rewrite runtime payload manifests,
- all adapter outcomes must still mount the same squashfs path contract.

## 3) Build Stages (Pristine ISO -> Final Artifact)

All stages are mapped to scaffold flags in `scripts/rebuild-debian-cinnamon-ground-up.sh`.

1. `preflight`
   - Host tooling checks, source ISO existence, path safety checks, LF normalization checks.
   - Emits `stage-preflight/manifest.json` and `stage-preflight/commands.log`.

2. `extract`
   - Extract ISO into isolated work tree.
   - Capture replay metadata and source ISO digest for deterministic rebuild proof.
   - Emits `stage-extract/source-iso.sha256`, `stage-extract/manifest.json`.

3. `rootfs`
   - Locate and extract live squashfs to working rootfs tree.
   - Preserve baseline rootfs hash markers before payload merge.
   - Emits `stage-rootfs/squashfs-source.txt`, `stage-rootfs/manifest.json`.

4. `payload`
   - Merge payload in controlled overlay phase (no host-destructive actions).
   - Record merged file manifest and changed-path list.
   - Emits `stage-payload/changed-paths.txt`, `stage-payload/manifest.json`.

5. `boot`
   - Apply boot-critical policy wiring (init path contract and GRUB consistency hooks).
   - Capture boot config diffs and invariants report.
   - Emits `stage-boot/boot-policy-report.txt`, `stage-boot/manifest.json`.

6. `pack`
   - Repack squashfs and ISO in isolated output directory.
   - Hash output artifact and record tool versions.
   - Emits `stage-pack/artifact.sha256`, `stage-pack/manifest.json`.

7. `verify`
   - Run boot-critical integrity checks via
     `scripts/validate-live-boot-integrity.sh`.
   - Generate machine-readable verification report and status marker.
   - Emits `stage-verify/validation.json`, `stage-verify/summary.txt`.

## 4) Strict Invariants

1. LF normalization invariant
   - Build-critical shell/config files must be LF normalized before stage execution.
   - CRLF detection failure blocks progression beyond preflight.

2. Init path invariant
   - `/usr/sbin/init` target in live rootfs must resolve to approved target:
     - `/lib/systemd/systemd`, or
     - `/opt/cogos/bin/cognitive_init` (if explicitly configured in pipeline policy).

3. Plymouth dependency invariant
   - If init/boot scripts reference `/usr/bin/plymouth`, policy must explicitly define:
     - `required` (missing binary blocks),
     - `optional` (missing binary warns),
     - `forbidden` (reference itself blocks).

4. Squashfs path invariant
   - GRUB entries must consistently reference `/live/filesystem.squashfs` unless
     contract is intentionally versioned and documented.

5. Deterministic replay source invariant
   - Every build run records:
     - source ISO absolute path,
     - SHA256 digest,
     - toolchain versions,
     - stage manifests.

## 5) Proof Gates and Hardware Matrix

Claim taxonomy for release claims (mandatory):
- `asserted`: evidence incomplete; cannot promote.
- `proven`: evidence complete; can promote.
- `rejected`: evidence disproves claim or proof is invalid.

### Stage Proof Gate

A stage is promotable only when all are present:
- stage manifest,
- exact command transcript or command log,
- exit status and interpretation,
- relevant artifact hashes.

### Minimum Hardware Matrix for promotion

- Old/known-problem machine path (BIOS or legacy-firmware leaning) - required.
- Independent modern machine path (UEFI) - required.
- Secure Boot off path (if applicable) - required for current baseline.
- At least one previously failing environment included.

Single-machine proof remains `asserted`, not `proven`.

## 6) Rollback and Recovery Paths

- Stage-level rollback:
  - Keep immutable stage directories under `wolf-cog-os/artifacts/ground-up/<run-id>/`.
  - Re-run from latest successful stage without deleting prior proof artifacts.

- Artifact rollback:
  - Preserve previous known-good ISO hash manifest.
  - If verify stage fails, keep previous promoted artifact untouched.

- Safety rollback:
  - No default host-level destructive actions.
  - `--dry-run` default prevents unintentional writes while validating pipeline wiring.

## 7) Required Artifact Bundle Outputs (Per Run)

Run root:
- `wolf-cog-os/artifacts/ground-up/<timestamp>/`

Required files:
- `run-metadata.json` (operator, host, timestamps, policy knobs),
- `source-iso.sha256`,
- `stage-*/manifest.json` for each executed stage,
- `stage-*/commands.log`,
- `stage-verify/validation.json`,
- `stage-verify/summary.txt`,
- `proof-bundle.md` (instantiated from `templates/PROOF_BUNDLE_TEMPLATE.md`).

## 8) Starter Execution Contract (Tonight)

1. run preflight in dry-run mode,
2. confirm proof artifact scaffolding exists,
3. run `extract` + `rootfs` only on a clean workdir,
4. execute `verify` against extracted assets before any full repack.

This keeps early work in low-risk, high-signal mode and minimizes regression surface.
