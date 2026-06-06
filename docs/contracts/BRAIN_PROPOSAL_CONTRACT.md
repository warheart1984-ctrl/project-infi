# Brain Proposal Contract v1

Status: **active contract**

CISIV stage: **structure**

## Purpose

Normative JSON envelope for what Nova Cortex may emit outward to Jarvis, OTEM, and operator surfaces.
Cortex proposes; Jarvis/OTEM/operator authorize execution.

Related:

- [NOVA_CORTEX_FORMAL_SPEC.md](../runtime/NOVA_CORTEX_FORMAL_SPEC.md) — Theorem 5.1 (ArtifactType only)
- [AAIS_ANATOMICAL_LAYERS.md](../runtime/AAIS_ANATOMICAL_LAYERS.md) — Brain layer boundary
- Schema: [brain_proposal.v1.json](../../schemas/brain_proposal.v1.json)
- Engine: [brain_proposal_validator.py](../../src/brain_proposal_validator.py)

## Placement

```text
Nova Cortex lobes → ArtifactType (internal ledger)
Brain adapter     → brain_proposal.v1 (outward, proposal_only)
Jarvis / OTEM     → ActionType (execution authority only)
```

## Required envelope

Every proposal MUST include:

| Field | Constraint |
|-------|------------|
| `brain_proposal_version` | `brain_proposal.v1` |
| `proposal_id` | UUID |
| `emitted_at` | ISO8601 UTC |
| `status` | `proposal_only` (only allowed value) |
| `proposal_kind` | See enum below |
| `source` | Cortex identity block |
| `intent` | Bounded task interpretation |
| `utterances` | 1–8 items — what Cortex is allowed to say |
| `authority_boundary` | nova_may / nova_must_not / jarvis_must |

## proposal_kind

| Value | Use |
|-------|-----|
| `routing_recommendation` | Workflow-family, chain, cortex runtime suggestions |
| `cognitive_interpretation` | Artifact-backed reading of operator intent |
| `workflow_handoff` | Proposes organ chain without executing |
| `clarification_request` | Cortex asks for missing context |
| `continuance_summary` | Multi-turn arc / narrative continuity |
| `deliberation_recommendation` | Commit-stage recommendation from deliberation trace |

## utterance_class (allowed speech acts)

| Class | Cortex may |
|-------|------------|
| `interpretation` | Restate or classify operator intent |
| `recommendation` | Suggest family, chain, or runtime |
| `question` | Ask for missing context |
| `summary` | Summarize artifacts or prior turns |
| `evidence_cite` | Cite artifact pointers or ledger stages |

**Forbidden:** `command`, `execute`, `authorize`, `approve`, `tool_invoke`

## cognitive_artifacts keys

Only `ARTIFACT_TYPE_MEMBERS` from `output_type_governance.py`:

`focus_artifact`, `memory_artifact`, `decision_object`, `reflection_artifact`,
`planning_artifact`, `execution_artifact`, `intent_artifact`, `narrative_artifact`,
`cognitive_arc`, `invariant_tuning_artifact`, `retrieved_cues`, `focus_signals`

Each value: `{ artifact_type, summary (max 512), pointer }`.

## operator_next_steps.step_class

Allowed: `review`, `select`, `inspect`, `defer`, `approve`

Forbidden: `execute`, `deploy`, `tool_call`, `chain_run`

## Deliberation composition

`brain_proposal.v1` MAY include:

- `deliberation_id` — UUID pointer to sibling `brain_deliberation.v1`
- `proposal_kind: deliberation_recommendation` — when `cognitive.deliberation` activates

See [BRAIN_DELIBERATION_CONTRACT.md](./BRAIN_DELIBERATION_CONTRACT.md). Deliberation enriches inspection; it does not grant execution authority.

## Brain → Organ → Chain scoring

Cortex ranks fitness only; it never executes chains or plugs.

`routing` MAY include:

| Field | Constraint |
|-------|------------|
| `organ_rankings[]` | Up to 6 scored workflow-family organs |
| `chain_rankings[]` | Up to 12 scored workflow bundles |
| `suggested_workflow_chain` | Top `chain_rankings[0]` candidate |

Each ranking item includes `fitness_score` in `0..1`, unique `rank`, and known `family_id` / `workflow_id`.
Scoring is deterministic (intent overlap, organ readiness, chain step coverage, chain readiness bonus).
Engine: `src/brain_chain_scorer.py`.

## Hard rejects

Validator MUST fail proposals containing:

- `status` != `proposal_only`
- Any `ACTION_TYPE_MEMBERS` key (`tool_call`, `shell_command`, etc.)
- Top-level `authorized: true`, `execute: true`, `approved: true`
- `utterances[].text` longer than `max_chars` (default 2048)
- Unknown `artifact_type` in `cognitive_artifacts`
- `routing.suggested_workflow_chain.workflow_id` not in workflow bundles registry

## API

| Route | Purpose |
|-------|---------|
| `POST /api/operator/brain/propose` | Generate validated proposal from operator text |
| `GET /api/operator/brain` | Brain-layer status (not a proposal) |
| `GET /api/operator/brain/sessions` | List operator brain sessions |
| `POST /api/operator/brain/sessions` | Create session with initial proposal |
| `POST /api/operator/brain/sessions/<id>/decide` | Accept, reject, or defer (ledger receipt) |

See [BRAIN_SESSION_CONTRACT.md](./BRAIN_SESSION_CONTRACT.md) for session lifecycle.

## Example

```json
{
  "brain_proposal_version": "brain_proposal.v1",
  "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
  "emitted_at": "2026-06-05T12:00:00Z",
  "status": "proposal_only",
  "proposal_kind": "routing_recommendation",
  "source": {
    "layer_id": "aais.brain.nova_cortex",
    "cortex_family_id": "nova.cortex",
    "cortex_version": "1.2.0",
    "emitter": "brain_layer_runtime"
  },
  "intent": {
    "restated_task": "Research this topic and draft a brief with citations.",
    "frame_kind": "companion",
    "confidence": 0.82
  },
  "utterances": [
    {
      "utterance_id": "u1",
      "utterance_class": "interpretation",
      "text": "This looks like Knowledge Work: research, synthesis, and report drafting.",
      "artifact_refs": ["focus_artifact"],
      "max_chars": 512
    }
  ],
  "routing": {
    "suggested_workflow_family": [
      {
        "family_id": "knowledge_work",
        "display_name": "Knowledge Work",
        "mythic_label": "Knowledge Organ",
        "match_score": 2,
        "matched_signals": ["research", "brief"],
        "default_authority_cap": "assist"
      }
    ],
    "suggested_cortex_runtimes": ["cognitive.attention", "cognitive.planning"]
  },
  "authority_boundary": {
    "nova_may": ["interpret operator intent", "recommend workflow-family routing"],
    "nova_must_not": ["self-authorize tool execution", "emit ActionType fields"],
    "jarvis_must": ["authorize tool/action paths", "enforce policy gates"]
  },
  "governance": {
    "cisiv_stage": "structure",
    "claim_label": "asserted",
    "replay_pointer": null
  }
}
```

## Non-goals

- Cortex self-execution or auto chain-run
- Replacing Speaking Runtime speak body
- Multi-agent delegation graphs
