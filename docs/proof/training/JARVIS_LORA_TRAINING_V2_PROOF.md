# Jarvis LoRA Training v2 — Proof Packet

Status: **verified by `make jarvis-lora-training-gate`**

## Scope

1. Implementation enforcement for training envelopes and runtime adapter load gate
2. Base-vs-adapter eval acceptance with `jarvis_lora_eval_report.v1`
3. Operator promotion via API, CLI, and Operator Console card

## Components

| Artifact | Path |
|----------|------|
| Contract v2 | `docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md` |
| Eval report schema | `schemas/jarvis_lora_eval_report.v1.json` |
| Promotion record schema | `schemas/jarvis_lora_promotion_record.v1.json` |
| Adapter eval | `evals/run_adapter_eval.py` |
| Promotion store | `src/jarvis_lora_promotion_store.py` |
| Promote CLI | `tools/ops/promote_jarvis_adapter.py` |
| Runtime guard | `src/models.py` (`adapter_governance`) |
| API routes | `/api/operator/training/adapters*` |

## Verification

```bash
make jarvis-lora-training-gate
```

v2 gate checks:

- Contract v2 tokens (runtime load law, eval acceptance, promotion record)
- Eval report + promotion record fixtures validate
- Runtime adapter guard unit tests pass
- Promotion store + API tests pass
- `operator-workflow-stack-gate` includes `jarvis-lora-training-gate`

## Authority boundary

- Training never sets `promoted`
- Eval sets `eval_passed` only when acceptance passes
- Promotion API/CLI sets `promoted` and writes ledger event
- Runtime loads only `eval_passed` / `promoted` adapters when metadata exists

## Operator promotion proof

```powershell
py -3 evals/run_adapter_eval.py --adapter-metadata training/out/jarvis-qwen-lora/final/adapter_metadata.json --mock-model
py -3 tools/ops/promote_jarvis_adapter.py --run-id <uuid> --print-env
```
