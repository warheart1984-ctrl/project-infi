# Jarvis LoRA Training v1 — Proof Packet

Status: **verified by `make jarvis-lora-training-gate`**

## Scope

1. Governed LoRA/QLoRA adapter training for Jarvis tone and operator style
2. Dataset admission law for seed, private, and external supplements
3. Adapter metadata and promotion protocol before runtime env swap

## Components

| Artifact | Path |
|----------|------|
| Contract | `docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md` |
| Run envelope schema | `schemas/jarvis_lora_training_run.v1.json` |
| Adapter metadata schema | `schemas/jarvis_lora_adapter_metadata.v1.json` |
| Validator | `src/jarvis_lora_training_validator.py` |
| Dataset prep | `training/prepare_messages_dataset.py` |
| Trainer | `training/train_jarvis_lora.py` |
| HF supplement import | `training/import_hf_sft_supplement.py` |
| Admission record | `governance/fixtures/training/hf_sft_supplement_admission.v1.json` |
| Genome | `governance/subsystem_genomes/jarvis_lora_training.genome.v1.json` |

## Verification

```bash
make jarvis-lora-training-gate
```

Gate checks:

- Contract, schemas, genome, proof, and fixtures exist
- Sample run envelope and adapter metadata validate
- Promoted-without-eval and external-without-admission cases fail closed
- Non-admitted base model rejected
- Canonical adapter path is `training/out/jarvis-qwen-lora/final`
- Pytest: `tests/test_jarvis_lora_training_validator.py`

## Authority boundary

- Training scripts write artifacts only; they do not set `AAIS_TEXT_ADAPTER_*` env vars
- Runtime loads adapters only when operator promotion env is set
- `AAIS_TEXT_MODEL_NAME` must match adapter `base_model` at load time

## Admission proof

External HF supplement `HuggingFaceH4/ultrachat_200k` is admitted as
`jarvis-lora-hf-ultrachat-200k-v1` in
`governance/fixtures/training/hf_sft_supplement_admission.v1.json` and cited in the
contract.
