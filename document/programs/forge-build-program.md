# Forge Build Program

Status: planning + prep only  
Scope window: now through first shippable Forge milestone (`forge-selfhosted` RC-ready path)

## Mission

Build a first shippable Forge ISO path that reuses current CoGOS build and release controls, with explicit ownership, evidence, and user override authority.

## Constraints

- Reuse existing build and release entrypoints; do not create a parallel pipeline.
- Keep `make` targets and workflow contracts valid with governance checks.
- Keep signing/verification and RC->stable promotion controls intact.
- Default new Forge checks to warn/audit-first until Meta Architect approves fail mode.
- This iteration is documentation/process only; no broad feature coding in this package.

## Operating Model (9 Roles)

| Role | Primary charter | Decision rights | Escalation trigger | Escalates to |
|---|---|---|---|---|
| Coder | Implement approved Forge tasks in scripts/workflows | Can change code only within approved backlog item scope | Scope creep, blocked contract, unclear acceptance criteria | Architect, then Meta Architect |
| Inspector | Validate task output against phase exit criteria | Can reject completion claims and reopen items | Missing artifact evidence or failed gate | Operator + Meta Architect |
| Bug Hunter | Hunt regressions in build/test/release flows | Can create P0 defects and freeze merge of affected item | Any failing smoke/matrix/signature path | Operator + Meta Architect |
| Seam Hunter | Detect boundary breaks between scripts/workflows/ledger | Can require seam contract updates before merge | Mismatch across `Makefile`, workflows, scripts, ledger | Architect + Meta Architect |
| Drift Watcher | Track config/contract drift over time | Can flag drift debt and require correction tasks | Repeated warn-only findings, ledger mismatch, undocumented env precedence | Architect + Meta Architect |
| Operator | Run cadence, drive handoffs, maintain execution board | Can reprioritize within approved phase, assign owners, enforce stop-the-line | P0 blocker, cross-role deadlock, unmet entry criteria | Meta Architect |
| Coordinator | Keep program tracker state current and evidence-linked | Can update tracker state and request missing evidence before gate close | Scenario gate drift, stale tracker state, or missing evidence pointers | Operator + Meta Architect |
| Architect | Own technical design coherence and sequencing | Can approve implementation approach and phase gates | Contract ambiguity, sequencing risk, unresolved tradeoffs | Meta Architect |
| Meta Architect (User) | Final authority on scope, priorities, risk posture | Approve/reject go/no-go, freeze/unfreeze work, force re-plan | Any user-raised issue or confidence loss | N/A (final authority) |

## Repo-anchored Control Points

- Build orchestration: `Makefile`, `wolf-cog-os/scripts/build-rootfs.sh`, `wolf-cog-os/scripts/build.sh`
- Boot/profile seam: `wolf-cog-os/scripts/patch_grub_merge.sh`
- Installer validation: `wolf-cog-os/scripts/test/installer-matrix.py`, `wolf-cog-os/scripts/test/installer-qemu-smoke.sh`
- CI/public sanity: `.github/workflows/cogos-ci-public.yml`
- Heavy build + matrix/perf: `.github/workflows/cogos-ci-selfhosted.yml`
- RC signing path: `.github/workflows/cogos-rc.yml`
- Stable promotion path: `.github/workflows/cogos-release.yml`
- Governance contract: `.github/scripts/validate-governance-ledger.py`, `.github/governance/command-ledger.json`
- Signing/verify scripts: `.github/scripts/sign-artifacts.sh`, `.github/scripts/verify-artifacts.sh`

## Phase Plan to First Shippable Milestone

### Phase 0 - Program kickoff and contract freeze

**Entry criteria**
- `docs/forge-iso-design.md` accepted as baseline.
- Operator has role roster and owner assignments.

**Tasks**
- Freeze Forge profile precedence policy draft (profile file vs env overrides).
- Define first milestone boundary: "Forge RC-ready path, stable promotion dry-run proven."
- Create execution artifacts (`docs/forge-backlog.md`, `docs/forge-risk-register.md`).

**Owner role**
- Architect (primary), Operator (execution control)

**Artifacts**
- `docs/forge-build-program.md`
- `docs/forge-backlog.md`
- `docs/forge-risk-register.md`

**Exit criteria**
- All roles acknowledge charter and escalation path.
- Meta Architect approves phase map and first milestone definition.

**Go/No-Go checklist**
- [ ] Role ownership confirmed
- [ ] Milestone definition approved
- [ ] Change-control protocol approved by Meta Architect

### Phase 1 - Forge contract scaffolding

**Entry criteria**
- Phase 0 approved.
- No unresolved P0 in current CoGOS workflows.

**Tasks**
- Add Forge profile spec files under `wolf-cog-os/profiles/forge/` (planning backlog item).
- Add profile loader/validator/attestation stubs (`wolf-cog-os/scripts/lib/profile-loader.sh`, `wolf-cog-os/scripts/validate-profile.py`, `wolf-cog-os/scripts/emit-profile-attestation.py`).
- Register command consumers and new surfaces in `.github/governance/command-ledger.json`.

**Owner role**
- Coder (implementation), Seam Hunter (contract verification), Inspector (acceptance)

**Artifacts**
- Profile schema and sample `forge-selfhosted` definition
- Governance ledger entries and validation evidence
- Stub attestation JSON in `ci-artifacts/`

**Exit criteria**
- Governance validation runs clean in warn mode for new surfaces.
- Existing non-Forge flows (`make rootfs`, `make iso-tree`, installer paths) remain unchanged.

**Go/No-Go checklist**
- [ ] `python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only` passes
- [ ] No regression to current workflow commands
- [ ] Seam Hunter sign-off on profile/env precedence contract

### Phase 2 - CI/public + self-hosted non-enforcing Forge path

**Entry criteria**
- Phase 1 exits complete.
- Profile stubs and ledger entries merged.

**Tasks**
- Wire Forge profile selection into `.github/workflows/cogos-ci-selfhosted.yml` as non-enforcing path.
- Add public CI dry-run checks in `.github/workflows/cogos-ci-public.yml` for profile schema/attestation skeleton.
- Extend build scripts to emit `ci-artifacts/profile-validation.json` and `ci-artifacts/profile-attestation.json`.

**Owner role**
- Coder (workflow/script wiring), Drift Watcher (contract drift), Inspector (gate evidence)

**Artifacts**
- Workflow run logs with Forge dry-run evidence
- `ci-artifacts/profile-validation.json`
- `ci-artifacts/profile-attestation.json`

**Exit criteria**
- Forge dry-run evidence appears in CI artifacts.
- Warn-mode gates surface issues without blocking mainline.

**Go/No-Go checklist**
- [ ] Public CI includes Forge contract checks
- [ ] Self-hosted CI emits Forge evidence artifacts
- [ ] Drift Watcher reports no undocumented env overrides

### Phase 3 - First shippable Forge milestone (RC-ready)

**Entry criteria**
- Phase 2 evidence stable for at least 2 consecutive successful self-hosted runs.

**Tasks**
- Enable Forge build path in `.github/workflows/cogos-rc.yml`.
- Require signing and verification of Forge RC artifacts (`make sign-artifacts`, `make verify-artifacts`).
- Bind Forge matrix scenarios in `wolf-cog-os/scripts/test/installer-matrix.py` (minimum `1,3,6`; `4` as tracked gate).
- Validate release promotion dry-run in `.github/workflows/cogos-release.yml` with `source_run_id`.

**Owner role**
- Operator (release orchestration), Bug Hunter (regression gate), Inspector (milestone acceptance)

**Artifacts**
- Forge RC artifact bundle (`*-rc-artifacts`)
- Signed `artifact-manifest.json` + `.minisig` files
- Matrix summary with Forge profile metadata
- Stable release dry-run report

**Exit criteria**
- At least one signed + verified Forge RC run succeeds.
- Stable promotion dry-run from Forge RC artifacts succeeds with verify checks.

**Go/No-Go checklist**
- [ ] `make verify-artifacts ARTIFACT_DIR="ci-artifacts"` succeeds in RC flow
- [ ] Required installer scenarios pass for Forge
- [ ] Release promotion dry-run confirms correct artifact set and source run
- [ ] Meta Architect approves milestone ship decision

## Watchlists

### Bug watchlist (Bug Hunter)

- Installer smoke instability in `make installer-smoke` across public/self-hosted/RC workflows.
- Matrix regressions in `wolf-cog-os/scripts/test/installer-matrix.py` scenarios `1,3,6` (and `4` when enabled).
- Signing/verify failures in `.github/scripts/sign-artifacts.sh` and `.github/scripts/verify-artifacts.sh`.
- QEMU smoke flake in `wolf-cog-os/scripts/test/installer-qemu-smoke.sh`.

### Seam watchlist (Seam Hunter)

- `Makefile` target behavior diverging from workflow invocations.
- Profile precedence ambiguity between env vars (`COGOS_BOOT_PROFILE`, `ISO`, etc.) and Forge profile files.
- GRUB template branching in `patch_grub_merge.sh` drifting from profile-driven rules.
- Artifact naming/channel mismatch between RC (`cogos-rc`) and release promotion inputs.

### Drift watchlist (Drift Watcher)

- Ledger coverage drift in `.github/governance/command-ledger.json` after command/workflow edits.
- Warn-only findings repeating for 3+ runs without owner action.
- Performance gate assumptions diverging from `.github/perf/scenario-bands.json`.
- Ad hoc workflow env changes not captured in docs/backlog acceptance criteria.

## Mode Playbooks (Scenario 3 Focus)

### Inspector

Purpose: Ensure installer proof and resume evidence remain valid when mounts are torn down.

Checklist:
- [ ] Confirm no verification step depends on `target-root` content after teardown/unmount.
- [ ] Verify proof is sourced from durable artifacts (`state.json`, checkpoints, `events.log`), not transient mounts.
- [ ] Reject gate if post-teardown-only dependencies are found.

### Seam Hunter

Purpose: Detect mount-lifecycle seam breaks around disk metadata and boot handoff.

Checklist:
- [ ] Scan `fstab` persistence for expected target UUID and mountpoints after apply/resume.
- [ ] Scan bootloader outputs (`grub.cfg`/update-grub effects) for expected entries.
- [ ] Scan EFI copy seam to ensure EFI payloads persist across mount/unmount cycles.

### Drift Watcher

Purpose: Keep installer contract and verification path canonical and non-ambiguous.

Checklist:
- [ ] Ensure installer contract documents the canonical proof path in one place.
- [ ] Ensure scenario and runbook docs point to that canonical path, not ad hoc variants.
- [ ] Open drift item if alternate proof paths appear without contract update.

### Operator

Purpose: Execute and recover Scenario 3 runs using the documented resume path.

Checklist:
- [ ] Run Scenario 3 injected-failure flow and then `--resume` flow.
- [ ] Capture runbook evidence pointer for Scenario 3 in the tracker.
- [ ] Confirm resume-path behavior aligns with installer contract before gate close.

### Coordinator

Purpose: Keep Scenario 3 gate state accurate in the program tracker.

Checklist:
- [ ] Mark Scenario 3 green only when evidence pointer and verification command are attached.
- [ ] Keep status labels consistent (`GREEN` complete, `YELLOW` in progress, `RED` blocked).
- [ ] Reopen to `YELLOW` if evidence link or proof contract reference becomes stale.

## Daily Operating Cadence

- 09:00 planning standup (Operator-led, 15 min): confirm phase, blockers, ownership changes.
- 13:00 seam/bug/drift review (Inspector + specialty roles, 20 min): update watchlists and P0/P1 status.
- 17:00 acceptance gate (Inspector + Architect + Operator, 20 min): close tasks only with evidence links and verification output.
- End-of-day Meta Architect checkpoint: approve/reject gate decisions and reprioritization.

## Change-Control Protocol (Meta Architect Issue Callout)

1. **Interrupt and classify (Operator, immediate):** tag issue as `P0 stop-the-line`, `P1 critical`, or `P2 planned`.
2. **Freeze impacted lane (Operator):** pause only affected backlog items; keep unrelated lanes running.
3. **Root-cause pass (Bug/Seam/Drift role owner):** produce short impact memo with touched paths, failed checks, and proposed fix.
4. **Re-plan delta (Architect):** update phase tasks, owner, and exit criteria; highlight scope/time/risk changes.
5. **Meta Architect gate:** explicit approve/reject on revised path before execution resumes.
6. **Audit trail (Inspector):** append decision + rationale to backlog/risk register and note verification commands.

## First Shippable Milestone Definition

Forge milestone is considered shippable when:
- Forge RC path builds artifacts via existing RC workflow;
- RC artifacts are signed and verified successfully;
- Required installer scenarios pass with evidence artifacts;
- Stable promotion dry-run proves promotability from Forge RC `source_run_id`;
- Meta Architect explicitly approves go decision.
