# Agent Safety Doctrine (Companion)

Status: **active companion** to [Doctrine XIV (MA-14)](../../META_ARCHITECT_LAWBOOK.md)

Mythic label (docs only): *Forge Warden collaboration envelope*

Engineering stem: `AgentSafetyDoctrine`

## Purpose

Coding agents are **builders under law**, not architects. This document restates MA-14 for operators and agents. If text here disagrees with `META_ARCHITECT_LAWBOOK.md`, the lawbook governs.

## Authority chain

1. [META_ARCHITECT_LAWBOOK.md](../../META_ARCHITECT_LAWBOOK.md)
2. [HUMAN_AI_CO_COLLABORATION_CHARTER.md](../../HUMAN_AI_CO_COLLABORATION_CHARTER.md)
3. Blueprints under `document/blueprints/`
4. Contracts under `docs/contracts/`
5. Implementation, pipelines, tools

## MUST NOT (agents)

A coding agent **MUST NOT**:

- Rewrite architecture without blueprint approval
- Merge constitutional, blueprint, or contract changes without explicit human acceptance
- Bypass governance gates, manifests, or proof requirements
- Treat CI green as permission to violate law
- Expand scope autonomously when uncertainty is high
- Collapse generator, judge, and executor into one undifferentiated step without documented boundaries

## MAY (agents)

A coding agent **MAY**:

- Implement approved specifications and contracts
- Add tests, receipts, and trust-bundle evidence for governed changes
- Propose diffs, manifests, and documentation updates for human review
- Refactor within an approved boundary when manifests and proof obligations are satisfied

## Change boundary

Governance-touching work requires an **Agent Safety Doctrine manifest** (see [template](../../templates/AGENT_SAFETY_DOCTRINE_MANIFEST_TEMPLATE.json)) when the change affects:

- `META_ARCHITECT_LAWBOOK.md`, `REPO_PROOF_LAW.md`, or the Human–AI Charter
- `docs/contracts/**` or `docs/governance/**`
- `.cursor/rules/**` or agent-safety CI scripts
- Constitutional runtime modules (`src/project_infi_law.py`, `src/safety_envelope.py`, governance gates)

Validation: `make agent-safety-doctrine-gate` or `.github/scripts/validate-agent-safety-doctrine.py`.

## Uncertainty rule

When uncertainty increases, **agent authority decreases** ([Swarm Law](../contracts/SWARM_LAW.md), MA-14 §14.5):

- Hold or degrade — do not improvise with high confidence
- Surface open questions to the operator
- Record `authority_delta` in manifests when applicable

## Enforcement

| Surface | Path |
|---------|------|
| CI gate | `.github/workflows/agent-safety-doctrine-gate.yml` |
| Validator | `.github/scripts/validate-agent-safety-doctrine.py` |
| Example manifest | `governance/agent_change_manifests/` |
| Unit tests | `tests/test_agent_safety_doctrine.py` |

## Failure modes

| Condition | Response |
|-----------|----------|
| Missing manifest on governed PR | CI reject |
| Manifest schema invalid | CI reject with validator reason |
| Lawbook drift without manifest | Human review required; do not merge silently |
