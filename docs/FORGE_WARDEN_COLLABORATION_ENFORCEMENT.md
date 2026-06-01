# Forge Warden Collaboration Enforcement

Status: Governance bridge.

No explicit Forge Warden runtime module is currently present in the repository root governance stack.
This document defines enforceable Forge Warden collaboration checkpoints at the governance and CI layers.

## Constitutional Anchors

- `META_ARCHITECT_LAWBOOK.md` (Doctrine XI is a constitutional invariant)
- `REPO_PROOF_LAW.md` (operational proof law)
- `HUMAN_AI_CO_COLLABORATION_CHARTER.md` (human-AI constitutional companion)
- `docs/TRUST_BUNDLE_SPEC.md` (Trust Bundle normative schema)

## Enforceable Checkpoints (Current)

1. Workflow: `.github/workflows/documentation-baseline-gate.yml`
   - Runs `.github/scripts/validate-documentation-baseline.py`
   - Runs `.github/scripts/validate-trust-bundle.py`
2. Scope trigger (paths):
   - `docs/**`, `templates/**`, `.cursor/rules/**`
   - `.github/workflows/documentation-baseline-gate.yml`
   - `.github/scripts/validate-documentation-baseline.py`
   - `.github/scripts/validate-trust-bundle.py`
   - `META_ARCHITECT_LAWBOOK.md`, `REPO_PROOF_LAW.md`, `README.md`
3. Significant AI-driven change detection:
   - Derived from changed paths in governance/docs/rules/CI surfaces.
4. Trust Bundle requirement:
   - At least one changed Trust Bundle in `docs/trust_bundles/*.md` for significant AI-driven changes.
   - Each changed bundle must satisfy `docs/TRUST_BUNDLE_SPEC.md` schema checks.

## Mandatory vs Advisory

Mandatory:

- Doctrine XI invariant language in constitutional layer.
- Claim taxonomy label (`asserted`/`proven`/`rejected`) in Trust Bundles.
- `why_short` (<=5 lines).
- Proof mode (`proof_links` or `none_yet`) with valid exclusivity.
- `override_command` present.
- `debt_ticket_ref` required when override breaks blueprint.
- UTC timestamps, author, and context fields.
- CI check execution in documentation baseline gate.

Advisory:

- Additional subsystem-specific Warden adapters.
- Richer semantic checks beyond field/schema validation.
- Expanded artifact quality scoring.

## Pipeline Placement

- PR and push to `main` governance paths trigger the Documentation Baseline Gate.
- Trust Bundle enforcement runs as a second validation step in the same job.
- Failure blocks merge until a compliant bundle is present.

## Gaps to Full Automated Enforcement

- No runtime-level Forge Warden policy engine hook yet (this bridge is CI-governance layer enforcement).
- Significant AI-driven detection is path-based, not semantic/intent-aware.
- Cross-machine proof quality and deep evidence integrity are not fully machine-validated by the lightweight hook.
