# Jarvis Model Training

This folder is the practical starting point for "your own LLM" inside AAIS.

For this project, the right first move is not training a foundation model from scratch. It is fine-tuning a small open chat model so it learns your Jarvis tone, safety rules, and work style.

## What We Are Building

The first version is a LoRA adapter on top of:

- `Qwen/Qwen2.5-1.5B-Instruct`

## Governed Contract

Normative law: [docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md](../docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md)

Verification:

```powershell
make jarvis-lora-training-gate
```

## External Suggestion Admission

This training folder inherits the project-wide external suggestion admission
law.

Outside model, dataset, or tuning proposals may be compared or pressure-tested
here, but they do not become canonical AAIS training truth unless project law
has filtered them and the admitted form is documented.

Admitted HF supplement (v1): `HuggingFaceH4/ultrachat_200k` via
`training/import_hf_sft_supplement.py` with admission ID
`jarvis-lora-hf-ultrachat-200k-v1`.

That gives you:

- a stronger small model that still fits your laptop in 4-bit mode
- a path that can still run locally later
- something AAIS can load with `AAIS_TEXT_ADAPTER_PATH`

## Files

- `training/data/jarvis_seed_messages.jsonl`
  Starter training examples that teach Jarvis the private/local/operator style.
- `training/prepare_messages_dataset.py`
  Combines the checked-in seed set with your private examples.
- `training/train_jarvis_lora.py`
  Runs SFT fine-tuning with LoRA/QLoRA.
- `training/import_hf_sft_supplement.py`
  Imports an admitted HF SFT supplement into Jarvis JSONL format.

## 1. Install Training Extras

```powershell
.\.venv\Scripts\python -m pip install -r requirements-training.txt
```

## 2. Add Your Private Examples

Create:

`training/data/private_messages.jsonl`

Use one JSON object per line in this format:

```json
{"messages":[
  {"role":"system","content":"You are Jarvis, a private local AI partner for one person only."},
  {"role":"user","content":"Help me plan the next step for my project."},
  {"role":"assistant","content":"The fastest next move is to lock the scope, choose one target, and ship the smallest working slice first."}
]}
```

Good examples are:

- how you want Jarvis to sound
- how direct or calm you want it to be
- how it should answer coding questions
- how it should handle uncertainty
- how it should treat privacy, approvals, and local-only work

## 3. Build the Training Dataset

```powershell
.\.venv\Scripts\python training\prepare_messages_dataset.py
```

That writes:

`training/out/jarvis_train_messages.jsonl`
`training/out/dataset_manifest.json`

Optional admitted HF supplement:

```powershell
.\.venv\Scripts\python training\import_hf_sft_supplement.py --limit 20
.\.venv\Scripts\python training\prepare_messages_dataset.py --private training/data/hf_sft_supplement.jsonl
```

You can also build mode-specific datasets:

```powershell
.\.venv\Scripts\python training\prepare_messages_dataset.py --private training/data/private_messages_fast.jsonl --output training/out/jarvis_fast_messages.jsonl
.\.venv\Scripts\python training\prepare_messages_dataset.py --private training/data/private_messages_think.jsonl --output training/out/jarvis_think_messages.jsonl
```

## 4. Train the Adapter

```powershell
.\.venv\Scripts\python training\train_jarvis_lora.py
```

Final adapter output goes to:

`training/out/jarvis-qwen-lora/final`

For split response modes, train separate adapters:

```powershell
.\.venv\Scripts\python training\train_jarvis_lora.py --dataset training/out/jarvis_fast_messages.jsonl --output-dir training/out/jarvis-fast-lora-1p5b --epochs 2 --max-length 256
.\.venv\Scripts\python training\train_jarvis_lora.py --dataset training/out/jarvis_think_messages.jsonl --output-dir training/out/jarvis-think-lora-1p5b --epochs 2 --max-length 384
```

## 5. Load It In AAIS

Base model alignment is required. Training uses `Qwen/Qwen2.5-1.5B-Instruct`, so
runtime must match before loading the adapter:

```powershell
$env:AAIS_TEXT_MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"
$env:AAIS_TEXT_ADAPTER_PATH="training/out/jarvis-qwen-lora/final"
.\start-personal.ps1
```

For split `Fast` / `Think` behavior:

```powershell
$env:AAIS_ENABLE_TEXT_ADAPTERS="1"
$env:AAIS_TEXT_ADAPTER_FAST_PATH="training/out/jarvis-fast-lora-1p5b/final"
$env:AAIS_TEXT_ADAPTER_THINK_PATH="training/out/jarvis-think-lora-1p5b/final"
.\start-personal.ps1
```

`.\start-personal.ps1 -UseAdapters` also auto-detects those split adapter folders if they already exist.

## 6. Evaluate It (v2 acceptance)

```powershell
$env:AAIS_MODEL_MODE="real"
$env:AAIS_MODEL_PROFILE="lite"
$env:AAIS_HF_LOCAL_ONLY="1"
.\.venv\Scripts\python evals\run_adapter_eval.py --adapter-metadata training/out/jarvis-qwen-lora/final/adapter_metadata.json --mock-model
```

`run_adapter_eval.py` compares base vs adapter on the same prompts and sets
`promotion_status: eval_passed` only when acceptance passes.

## 7. Promote It

```powershell
py -3 tools/ops/promote_jarvis_adapter.py --run-id <uuid> --print-env
```

Or use Operator Console → Training adapters → Promote (after eval_passed).

Recent reports are written under:

`.runtime/evals/`

## Realistic Notes

- Your laptop can handle small-adapter experiments better than full pretraining.
- Training from scratch needs far more data and compute.
- If your dataset grows and you want a stronger Jarvis later, we should move training to a cloud GPU and keep local inference private.

## Best Next Upgrade

Once you collect 50-200 good private examples, the next step is:

1. train this adapter
2. evaluate it against your old base model on the same prompts
3. swap it into AAIS and compare the feel inside the Jarvis console
