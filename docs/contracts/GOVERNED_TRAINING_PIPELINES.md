# Governed Training Pipelines Contract

Status: **design contract** (Phase 8 — no trainers wired)

## Purpose

Document how `TrainingViewRecord` batches produced from Governance IR integrate with supervised fine-tuning, reward modeling, and RLAIF — without coupling trainers into the compiler or runtime executors.

Modules:

- `src/training_view_spec.py` — projection + `build_training_examples`
- `src/governance_eval_harness.py` — label parity + optional runtime replay

## Data flow

```
Governance IR
    → build_training_view_spec(ir)     # compiler: metadata + one example_record
    → build_training_examples(ir, spec) # batch: explicit multi-source generation
    → TrainingViewRecord[]
    → (future) trainers / eval harness
```

`build_training_view_spec` stays on the compiler output path and remains small. Batch generation is an explicit second call so compile artifacts do not balloon.

## Integration modes (metadata only)

| Mode | Labels / pairs | Typical sources |
|------|----------------|---------------|
| Supervised fine-tuning | `COMPLIANT`, `VIOLATION`, `ESCALATE` | `synthetic_compliant`, `synthetic_violation`, `fuzzed_envelope`, `odl_trace` |
| Reward modeling | Scalar preference from label + `violation_kind` | Compliant vs violating pairs sharing `ir_fingerprint` |
| RLAIF | Chosen / rejected trajectories | Synthetic + fuzzed; preference = `infer_label_from_mask` outcome |

No trainer implementations ship in Phase 8. Existing `training/train_jarvis_lora.py` is noted as a future consumer only.

## Batch configuration (`build_training_examples`)

The second argument is a dict extending `training_view_spec` metadata:

| Field | Type | Default |
|-------|------|---------|
| `generation_sources` | list of source ids | all `TRAINING_SOURCES` |
| `examples_per_source` | int | `1` |
| `fuzz_seeds` | list of int | `range(examples_per_source)` |
| `usage_mode` | `fine_tuning` \| `reward_model` \| `eval_harness` | `fine_tuning` |
| `odl_anchors` | list (optional) | `[None]` for `odl_trace` |
| `ledger_rows` | list (optional) | per-anchor ledger context |

Behavior:

- Calls existing projectors (`project_from_odl`, `project_synthetic`, `project_fuzzed`, `project_training_view`).
- Deduplicates by `view_id`.
- Stable ordering: by `source`, then seed/index.
- Labels must be members of `TRAINING_LABELS`.

## Fingerprint parity

Training exports and runtime bundles must align on:

- `taxonomy_fingerprint`
- `ir_fingerprint`
- `view_id` (per record)

Eval and runtime replay use the same IR snapshot embedded in `governance_ir_snapshot` on each record.

## Eval harness

`src/governance_eval_harness.py`:

| API | Role |
|-----|------|
| `replay_label(record)` | Recompute label via `infer_label_from_mask` on snapshot |
| `assert_label_parity(record)` | Compare stored label vs replay; violation-family tolerance for `VIOLATION` |
| `run_eval_suite(examples, include_runtime=False, provider_id="reference_mock")` | Batch parity; optional runtime replay |

Default path is label-only (fast, no LLM). When `include_runtime=True`:

1. Compile IR snapshot → `decode_governance_bundle`
2. `execute_with_decode_governance` with `reference_mock` + `force_execute`
3. Assert terminal execution status aligns with label taxonomy (`COMPLIANT` → allow/execute, `VIOLATION` → block/rollback family)

## Related contracts

- `TRAINING_VIEW_SPEC.md` — record schema and projectors
- `AUTHORITY_MASK_SPEC.md` — label inference source
- `GOVERNANCE_PROVIDER_ADAPTERS.md` — `reference_mock` runtime replay surface
- `GOVERNANCE_TAXONOMY.md` — shared labels and sources

## Tests

- `tests/test_training_examples.py`
- `tests/test_governance_eval_harness.py`
