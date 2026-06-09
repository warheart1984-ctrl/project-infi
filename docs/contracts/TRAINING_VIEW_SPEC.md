# Training View Spec Contract

Status: **active contract** (compilable projection stubs)

## Purpose

Project Governance IR into authority-conditioned training/eval records. Batch generation and eval harness ship in Phase 8; trainers remain out of scope.

Schema id: `nova.training_view_spec.v1`

Module: `src/training_view_spec.py`

Taxonomy: `docs/contracts/GOVERNANCE_TAXONOMY.md`

## TrainingViewRecord fields

| Field | Type | Required |
|-------|------|----------|
| `view_id` | string (hash) | yes |
| `ir_fingerprint` | string | yes |
| `input_text` | string | yes (or `conversation_window`) |
| `conversation_window` | list of `{role, content}` | optional |
| `governance_ir_snapshot` | dict (canonical subset) | yes |
| `label` | `COMPLIANT` \| `VIOLATION` \| `BORDERLINE` \| `ESCALATE` | yes |
| `action_type` | taxonomy action type | optional |
| `resource_class` | taxonomy resource class | optional |
| `authority_delta` | `{verbs_added, verbs_removed, resources_added}` | optional |
| `source` | `odl_trace` \| `synthetic_compliant` \| `synthetic_violation` \| `fuzzed_envelope` | yes |
| `usage_mode` | `fine_tuning` \| `reward_model` \| `eval_harness` | yes |

## Generation sources

| Source | Function | Input |
|--------|----------|-------|
| ODL traces | `project_from_odl(odl_anchor, ir)` | `execution_context.odl_anchor` + optional ledger row |
| Synthetic compliant | `project_synthetic(ir, label=COMPLIANT)` | IR with envelope inside bounds |
| Synthetic violating | `project_synthetic(ir, label=VIOLATION, violation_kind=...)` | IR + deliberate envelope breach |
| Fuzzed envelope | `project_fuzzed(ir, seed)` | Mutate `allowed_verbs` / resources deterministically |

Entry: `project_training_view(ir, *, source, usage_mode, ...)`.

## Label inference

`infer_label_from_mask(ir, action_type, verb, resource_class)` compares a proposed action against `get_authority_mask` constraints:

- `COMPLIANT` — within allowed verbs/resources/action class
- `VIOLATION` — denied site or forbidden verb/resource
- `BORDERLINE` — propose-cap envelope with execute-class verb
- `ESCALATE` — reserved for operator/OTEM paths (not auto-inferred in v2 slice)

## Usage modes (metadata only)

| Mode | Consumption |
|------|-------------|
| `fine_tuning` | Input text + IR snapshot → supervised label |
| `reward_model` | Preference pairs from compliant vs violating projections |
| `eval_harness` | Stress cases from fuzzed/synthetic violating records |

## TrainingViewSpec bundle fields

Compiler emits (via `build_training_view_spec(ir)` — single example only):

```json
{
  "schema_id": "nova.training_view_spec.v1",
  "status": "compilable_target",
  "ir_fingerprint": "sha256-16",
  "taxonomy_fingerprint": "sha256-16",
  "generation_sources": ["odl_trace", "synthetic_compliant", "synthetic_violation", "fuzzed_envelope"],
  "usage_modes": ["fine_tuning", "reward_model", "eval_harness"],
  "example_record": {}
}
```

## Batch generation (`build_training_examples`)

Explicit batch API (not part of compiler output size):

```python
def build_training_examples(
    governance_ir: dict[str, Any],
    training_view_spec: dict[str, Any],
) -> list[TrainingViewRecord]:
```

Config keys on `training_view_spec`:

| Key | Purpose |
|-----|---------|
| `generation_sources` | Subset of `TRAINING_SOURCES` to materialize |
| `examples_per_source` | Count per source (default `1`) |
| `fuzz_seeds` | Deterministic seeds for `fuzzed_envelope` |
| `usage_mode` | `fine_tuning` \| `reward_model` \| `eval_harness` |
| `odl_anchors` / `ledger_rows` | Optional ODL projection inputs |

Returns deduplicated `TrainingViewRecord` list ordered by source then index.

## Eval harness

`src/governance_eval_harness.py` closes the loop:

- `replay_label` / `assert_label_parity` — mask label vs stored label
- `run_eval_suite(..., include_runtime=True)` — optional `reference_mock` decode replay

See `GOVERNED_TRAINING_PIPELINES.md` for SFT / reward / RLAIF integration modes (design only).

## Related contracts

- `GOVERNANCE_IR.md` — compiler input
- `GOVERNANCE_TAXONOMY.md` — shared vocabulary
- `AUTHORITY_MASK_SPEC.md` — label inference source
- `INVARIANT_DECODE_GOVERNANCE.md` — bundle consumer
- `GOVERNED_TRAINING_PIPELINES.md` — training integration modes
