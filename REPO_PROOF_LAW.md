# Repository Proof Law

This law is mandatory for all projects and subprojects in this repository.
This document is subordinate to and implements `META_ARCHITECT_LAWBOOK.md` as the supreme governance authority.
`HUMAN_AI_CO_COLLABORATION_CHARTER.md` governs human-AI interaction semantics as a constitutional companion under the lawbook.
`docs/TRUST_BUNDLE_SPEC.md` defines the normative Trust Bundle schema required to operationalize Doctrine XI.

Constitutional precedence is binding: **Law > Blueprint > Contract > Implementation > Pipeline > Tool**.
No CI or process bypass is permitted for required proof-of-reality or baseline governance requirements.

## Non-Negotiable Principles

1. If it was not proven, it did not occur.
2. No proof, no claim.
3. Test outcomes must be backed by evidence that can be independently verified.
4. Acceptance cannot depend on a single machine, single operator view, or undocumented local state.
5. Trust language must describe evidence and verification status, not human-like traits of tools or models.

## Hard-Core Repo Law (Mandatory Project Baseline)

Every project and subproject must maintain a documented baseline of blueprint artifacts, operational documentation, fail-safe design/procedures, and tracked documentation debt.

Required baseline artifacts:

- **Blueprint artifact(s):** architecture and system intent documents that define project scope, components, interfaces, and constraints.
- **Operational documentation:** runbooks/SOPs that cover setup, operation, monitoring, troubleshooting, incident handling, and release flow.
- **Project-root README with How to Start Operations (MA-12):** for completed projects, a discoverable `README.md` with a **How to Start Operations** section meeting Doctrine XII minimum contents (prerequisites, initialization, entry point, verification, failsafe notes).
- **Fail-safe design and procedures:** explicit fail-safe behavior, rollback/recovery paths, escalation triggers, and operator override/stop conditions.
- **Documentation debt register:** a maintained record of known documentation gaps and stale docs.

Documentation debt register entries are required to include:

- Owner
- Severity
- Due date
- Status

Projects are **not ready** unless all five baseline artifact classes exist and the documentation debt register is present (or explicitly states no open debt).

CI enforcement: `.github/workflows/documentation-baseline-gate.yml` runs `.github/scripts/validate-documentation-baseline.py` to validate checklist sections, documentation debt register fields, and MA-12 operational primer requirements.

Agent Safety Doctrine enforcement: `.github/workflows/agent-safety-doctrine-gate.yml` runs `.github/scripts/validate-agent-safety-doctrine.py` to validate agent-authored change manifests for blueprint authority, bounded change explanation, evidence references, assumptions, reversal instructions, prohibited action denial, and the uncertainty rule.

## Required Evidence

Doctrine XI operational requirement:
- Significant AI-driven fix/test/release contributions MUST include a Doctrine XI-compliant Trust Bundle.
- Trust Bundles MUST follow `docs/TRUST_BUNDLE_SPEC.md` and SHOULD start from `templates/TRUST_BUNDLE_TEMPLATE.md`.
- Governance and CI enforcement surfaces for this requirement are defined in `docs/FORGE_WARDEN_COLLABORATION_ENFORCEMENT.md`.

### Per Fix

- Issue/incident identifier and scope.
- Claim taxonomy label: `asserted`, `proven`, or `rejected`.
- Short human-readable "Why" (decision rationale and assumptions).
- Root-cause statement with supporting reproduction context.
- Fix narrative: what changed, why this change was selected, and how it addresses root cause.
- Traceability to changed files, commands, and resulting artifacts.
- Agent-authored changes additionally require an Agent Safety Doctrine manifest when the change touches governance, validation, architecture, CI, templates, or proof surfaces.

### Per Test

- Claim taxonomy label: `asserted`, `proven`, or `rejected`.
- Short human-readable "Why" (what the result means and key caveats).
- Exact commands executed (including key environment assumptions).
- Raw outputs or stable references to stored outputs.
- Exit status and interpretation (pass/fail/retry).
- Artifact hashes for produced files when applicable.

### Per Release

- Consolidated "Trust Bundle" (proof bundle) index for all release-blocking tests.
- Cross-machine verification matrix for required hardware/firmware paths.
- Sign-off records for author and reviewer/approver.

## Acceptable Proof Artifacts

Acceptable proof artifacts include:

- Command transcripts and log files.
- Structured machine-readable state files (JSON/CSV) tied to test runs.
- Hash manifests (`sha256sum` output and verification records).
- Screenshot/video references for UI or hardware-only observations.
- Run metadata: timestamps, operator identity, machine profile, and tool versions.

Artifacts are unacceptable if they are incomplete, unverifiable, or disconnected from the claim they support.

## Cross-Machine Requirement

- Do not accept a fix or release based on one machine only.
- At minimum, provide evidence from:
  - one previously failing environment (old/known-problem machine), and
  - one independent environment (new/clean or different hardware/firmware path).
- For boot/installer/platform-sensitive work, evidence must include BIOS/legacy and UEFI paths when relevant.

## Claim Taxonomy (Required)

- `asserted`: a statement without sufficient evidence; cannot be used for acceptance.
- `proven`: a statement backed by required evidence and traceable artifacts; can be used for acceptance.
- `rejected`: a statement disproven by evidence or lacking required proof after review.

All significant fix, test, and release claims MUST carry one of these labels.

## Retention And Traceability

- Keep proof artifacts for each accepted fix/test/release in a durable location tracked by the repository.
- Each claim must link to its proof bundle and each proof bundle must link back to the claim/issue.
- Preserve timestamps, author identity, and approval metadata.
- Do not delete or overwrite prior proof records without an explicit supersession note.

## Operational Default

- If evidence is missing, the status is not complete.
- If evidence is ambiguous, status remains asserted until resolved.
- If evidence conflicts, mark the claim rejected until re-proven.
