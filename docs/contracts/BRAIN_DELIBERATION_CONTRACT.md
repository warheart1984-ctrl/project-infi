# Brain Deliberation Contract v1

Status: **active contract**

CISIV stage: **structure**

## Purpose

Structured, multi-utterance reasoning protocol for Nova Cortex deliberation.
Cortex may run multi-step cognitive chains (options → tradeoffs → commit); it may not grant execution authority.

Related:

- [BRAIN_PROPOSAL_CONTRACT.md](./BRAIN_PROPOSAL_CONTRACT.md) — sibling outward envelope
- [BRAIN_SESSION_CONTRACT.md](./BRAIN_SESSION_CONTRACT.md) — operator decision lifecycle
- [NOVA_CORTEX_FORMAL_SPEC.md](../runtime/NOVA_CORTEX_FORMAL_SPEC.md) — Theorem 5.1 (ArtifactType only)
- Schema: [brain_deliberation.v1.json](../../schemas/brain_deliberation.v1.json)
- Engine: [brain_deliberation_validator.py](../../src/brain_deliberation_validator.py)

## Placement

```text
Nova Cortex deliberation lobe → cognitive.deliberation (internal ledger)
Brain adapter                 → brain_deliberation.v1 (outward, proposal_only)
Brain proposal (optional)     → deliberation_id pointer
Brain session                 → deliberations[] history
Jarvis / OTEM / Operator      → ActionType (execution authority only)
```

## Required envelope

| Field | Constraint |
|-------|------------|
| `brain_deliberation_version` | `brain_deliberation.v1` |
| `deliberation_id` | UUID |
| `emitted_at` | ISO8601 UTC |
| `status` | `proposal_only` (only allowed value) |
| `operator_anchor` | Session + restated operator intent |
| `source` | Cortex identity block |
| `stage_chain` | 1–4 ordered deliberation stages |
| `authority_boundary` | nova_may / nova_must_not / jarvis_must |

## Stage protocol

| stage_kind | Required before commit | Typical utterance_class |
|------------|------------------------|-------------------------|
| `options` | yes | `interpretation` |
| `tradeoffs` | yes | `evidence_cite` |
| `commit` | terminal recommendation | `recommendation` |
| `revisit` | optional | `question` |

**Invariants:**

- `options` must precede `commit`
- `tradeoffs` must precede `commit`
- `revisit` only when `revisit_trigger` is set

## Bounds

| Limit | Value |
|-------|-------|
| Max stages | 4 |
| Max utterances per stage | 4 |
| Max total utterances | 16 |
| Summary fields | 512 chars |
| Allowed artifact keys | `focus_artifact`, `decision_object`, `cognitive_arc` |

## Composition with brain_proposal

`brain_proposal.v1` MAY include:

- `deliberation_id` — UUID pointer to a sibling deliberation envelope
- `proposal_kind: deliberation_recommendation` — when commit-stage recommendation is surfaced

Deliberation never replaces brain_proposal routing; it enriches operator inspection.

## Hard rejects

Validator MUST fail deliberations containing:

- `status` != `proposal_only`
- Any `ACTION_TYPE_MEMBERS` key
- Top-level `authorized: true`, `execute: true`, `approved: true`
- Forbidden `utterance_class` values (`command`, `execute`, `authorize`, `approve`, `tool_invoke`)
- Stage order violations (commit before options/tradeoffs)
- Unknown `artifact_type` in `cognitive_artifacts`
- Criteria scores outside 0..1 when present in `decision_summary.criteria_scores`

## API

| Route | Purpose |
|-------|---------|
| `POST /api/operator/brain/deliberate` | Generate validated deliberation from operator text |
| `POST /api/operator/brain/sessions/<id>/deliberate` | Append deliberation to open session |

## Non-goals

- Auto-commit or auto chain-run
- Tool invocation or ActionType emission
- Replacing internal `cognitive.deliberation` lobe logic
