# Jarvis LoRA Training Contract v2

Status: **active contract**

CISIV stage: **implementation**

Verification stage: **verification** (adapter eval acceptance + promotion gate)

## Purpose

Normative contract for bounded LoRA/QLoRA adapter training that teaches Jarvis tone,
safety rules, and operator work style on top of admitted open chat models.

Training produces artifacts. Runtime load requires governed metadata and operator promotion.

This contract does **not** authorize foundation-model training from scratch.

Related:

- [EXTERNAL_SUGGESTION_ADMISSION_RULE.md](./EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
- [JARVIS_PROTOCOL.md](./JARVIS_PROTOCOL.md)
- [training/README.md](../../training/README.md)
- [evals/README.md](../../evals/README.md)
- Run envelope schema: [jarvis_lora_training_run.v1.json](../../schemas/jarvis_lora_training_run.v1.json)
- Adapter metadata schema: [jarvis_lora_adapter_metadata.v1.json](../../schemas/jarvis_lora_adapter_metadata.v1.json)
- Eval report schema: [jarvis_lora_eval_report.v1.json](../../schemas/jarvis_lora_eval_report.v1.json)
- Promotion record schema: [jarvis_lora_promotion_record.v1.json](../../schemas/jarvis_lora_promotion_record.v1.json)
- Validator: [jarvis_lora_training_validator.py](../../src/jarvis_lora_training_validator.py)
- Promotion store: [jarvis_lora_promotion_store.py](../../src/jarvis_lora_promotion_store.py)
- HF supplement admission: [hf_sft_supplement_admission.v1.json](../../governance/fixtures/training/hf_sft_supplement_admission.v1.json)

## Placement

```text
Seed / private / admitted external JSONL
  → prepare_messages_dataset.py (+ dataset_manifest.json)
  → jarvis_lora_training_run.v1 (validated envelope)
  → train_jarvis_lora.py (+ final/training_run.json)
  → jarvis_lora_adapter_metadata.v1 (final/adapter_metadata.json)
  → evals/run_adapter_eval.py (jarvis_lora_eval_report.v1)
  → operator promote API/CLI (jarvis_lora_promotion_record.v1)
  → operator env promotion (AAIS_TEXT_ADAPTER_*)
  → src/models.py runtime load gate
```

## Authority boundary

| Actor | May | Must not |
|-------|-----|----------|
| Training scripts | produce adapters, metadata, training_run.json | set runtime env vars or auto-promote |
| Eval runner | set `eval_passed` or keep `draft` | set `promoted` |
| Jarvis / operator | inspect artifacts, approve promotion | bypass eval acceptance |
| Runtime (`src/models.py`) | load adapter when governance gate passes | load `draft` adapters or mismatched base model |

## Authority ladder

| Level | May | Must not |
|-------|-----|----------|
| `observe` | inspect datasets, manifests, metadata, eval reports | run training or set adapter env |
| `assist` | prepare datasets, draft run envelope | promote adapter to runtime |
| `execute` | run training with admitted dataset + envelope | swap runtime without eval acceptance |
| `admin` | promote adapter via API/CLI / dual-adapter split | bypass admission for external data |

## Dataset law

Canonical conversational schema: one JSON object per line with a `messages` array.

| Role | Allowed |
|------|---------|
| `system` | optional Jarvis identity / safety preamble |
| `user` | operator or user turn |
| `assistant` | target Jarvis response |

### Dataset sources

| Source kind | Path pattern | Admission |
|-------------|--------------|-----------|
| `seed` | `training/data/jarvis_seed_messages.jsonl` | checked-in canonical examples |
| `private` | `training/data/private_messages*.jsonl` | operator-local only; never committed |
| `external` | admitted supplement files | requires `admission_ids[]` |

### Admitted external dataset

| Admission ID | Dataset | Use |
|--------------|---------|-----|
| `jarvis-lora-hf-ultrachat-200k-v1` | `HuggingFaceH4/ultrachat_200k` (`train_sft`) | optional SFT supplement |

## Admitted base models

| Model | Status |
|-------|--------|
| `Qwen/Qwen2.5-1.5B-Instruct` | primary admitted base |

**Runtime alignment rule:** promoted adapter `base_model` MUST equal `AAIS_TEXT_MODEL_NAME`.

## Runtime load law (v2)

When `{adapter_path}/adapter_metadata.json` exists, runtime MUST:

1. Validate metadata against `jarvis_lora_adapter_metadata.v1`
2. Allow load only when `promotion_status` is `eval_passed` or `promoted`
3. Reject load when `base_model` != `AAIS_TEXT_MODEL_NAME`
4. Emit `adapter_governance` trace metadata for operator visibility

Legacy adapters without metadata may still load with a logged legacy allowance.

## Eval acceptance law (v2)

`evals/run_adapter_eval.py` produces `jarvis_lora_eval_report.v1` and updates metadata:

| Check | Default threshold |
|-------|-------------------|
| HTTP completion | all prompt/mode pairs return 200 |
| Plan pass rate | adapter >= base - 0.1 per mode |
| Workspace grounding | adapter `avg_workspace_hits` >= base per mode |
| Latency ceiling | adapter `avg_latency_ms` <= base * 1.5 per mode |

On pass: `promotion_status: eval_passed` and `eval_report_path` set.
On fail: remain `draft`.

## Promotion record (v2)

Operator promotion via API or CLI writes `promotion_record` into metadata:

| Field | Constraint |
|-------|------------|
| `jarvis_lora_promotion_record_version` | `jarvis_lora_promotion_record.v1` |
| `promoted_at` | ISO8601 UTC |
| `promoted_by` | operator identity |
| `promotion_env` | `AAIS_TEXT_MODEL_NAME`, `AAIS_ENABLE_TEXT_ADAPTERS`, `AAIS_TEXT_ADAPTER_PATH` |

Promotion requires prior `eval_passed` and non-empty `eval_report_path`.

## Required artifacts

| Artifact | Path |
|----------|------|
| Training run envelope | `{output_dir}/final/training_run.json` |
| Adapter metadata | `{output_dir}/final/adapter_metadata.json` |
| Eval report | `.runtime/evals/adapter-eval-*.json` |
| Promotion ledger | `.runtime/training/jarvis_lora_promotions.jsonl` |

Canonical final adapter directory:

`training/out/jarvis-qwen-lora/final`

## Promotion protocol

1. **Prepare** — `prepare_messages_dataset.py`
2. **Train** — `train_jarvis_lora.py` (validated envelope, metadata `draft`)
3. **Eval** — `evals/run_adapter_eval.py --adapter-metadata <path>`
4. **Compare** — inspect eval report acceptance block
5. **Approve** — operator promotes via API/CLI
6. **Promote** — apply returned `promotion_env`
7. **Verify** — runtime load + Jarvis console `adapter_governance` trace

## Operator surfaces (v2)

| Surface | Path |
|---------|------|
| List adapters | `GET /api/operator/training/adapters` |
| Adapter detail | `GET /api/operator/training/adapters/<run_id>` |
| Promote | `POST /api/operator/training/adapters/<run_id>/promote` |
| CLI | `tools/ops/promote_jarvis_adapter.py` |
| Console | Operator Console training adapters card |

Browser console copies env only; it does not mutate process environment.

## Invariants

1. No foundation-model-from-scratch training under this contract.
2. Private operator JSONL MUST NOT be committed.
3. External datasets require documented admission IDs.
4. Training validates run envelope before GPU work begins.
5. Runtime blocks `draft` adapters when metadata is present.
5. `promoted` requires `promotion_record` and `eval_report_path`.
6. Eval acceptance MUST pass before promotion.
7. Training artifacts alone do not change runtime behavior.

## Enablement

| Variable | Purpose |
|----------|---------|
| `AAIS_TEXT_MODEL_NAME` | Base model; MUST match adapter `base_model` |
| `AAIS_TEXT_ADAPTER_PATH` | Single/default adapter directory |
| `AAIS_TEXT_ADAPTER_FAST_PATH` | Fast-mode adapter |
| `AAIS_TEXT_ADAPTER_THINK_PATH` | Think-mode adapter |
| `AAIS_ENABLE_TEXT_ADAPTERS` | `1` to enable adapter loading |
| `AAIS_HF_LOCAL_ONLY` | `1` for cache-only HF access |

## Verification

```bash
make jarvis-lora-training-gate
make operator-workflow-stack-gate
```

Proof packets:

- [JARVIS_LORA_TRAINING_V1_PROOF.md](../proof/training/JARVIS_LORA_TRAINING_V1_PROOF.md)
- [JARVIS_LORA_TRAINING_V2_PROOF.md](../proof/training/JARVIS_LORA_TRAINING_V2_PROOF.md)

## Non-goals (v2)

- Cloud HF Jobs training execution
- Automatic browser-side env mutation
- Multi-base-model admission beyond `Qwen/Qwen2.5-1.5B-Instruct`
- Human-preference quality scoring beyond mode-eval aggregates
