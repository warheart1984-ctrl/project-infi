"""Fine-tune a small Jarvis adapter with LoRA/QLoRA."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.jarvis_lora_training_validator import validate_training_run

import torch
from datasets import load_dataset
from huggingface_hub import snapshot_download
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer


DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_METADATA_VERSION = "jarvis_lora_adapter_metadata.v1"
TRAINING_RUN_VERSION = "jarvis_lora_training_run.v1"


def _should_prefer_local_files():
    """Return whether training should prefer cached Hugging Face files."""
    return os.getenv("AAIS_HF_LOCAL_ONLY", "").strip().lower() in {"1", "true", "yes"}


def _with_local_fallback(loader, model_name: str, **kwargs):
    """Retry model/tokenizer loading from the local cache after network failures."""
    prefer_local = _should_prefer_local_files()
    load_kwargs = dict(kwargs)
    if prefer_local:
        load_kwargs["local_files_only"] = True

    try:
        return loader(model_name, **load_kwargs)
    except Exception:
        if load_kwargs.get("local_files_only"):
            raise
        load_kwargs["local_files_only"] = True
        return loader(model_name, **load_kwargs)


def _resolve_model_source(model_name: str):
    """Prefer an existing local Hugging Face snapshot when available."""
    try:
        return snapshot_download(repo_id=model_name, local_files_only=True)
    except Exception:
        return model_name


def _load_tokenizer(model_source: str):
    tokenizer = _with_local_fallback(AutoTokenizer.from_pretrained, model_source)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def _resolve_precision_flags():
    use_cuda = torch.cuda.is_available()
    use_bf16 = bool(use_cuda and torch.cuda.is_bf16_supported())
    use_fp16 = bool(use_cuda and not use_bf16)
    return use_bf16, use_fp16


def _load_model(model_source: str, use_4bit: bool):
    load_kwargs = {"low_cpu_mem_usage": True}

    if torch.cuda.is_available():
        compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        load_kwargs["torch_dtype"] = compute_dtype
        if use_4bit:
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=compute_dtype,
            )
            load_kwargs["device_map"] = "auto"

    model = _with_local_fallback(AutoModelForCausalLM.from_pretrained, model_source, **load_kwargs)
    model.config.use_cache = False

    if use_4bit and torch.cuda.is_available():
        model = prepare_model_for_kbit_training(model)

    return model


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _git_commit_best_effort() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    commit = completed.stdout.strip()
    return commit or None


def _load_dataset_manifest(dataset_path: Path) -> dict:
    manifest_path = dataset_path.with_name("dataset_manifest.json")
    if not manifest_path.exists():
        return {
            "sources": ["seed"],
            "admission_ids": [],
        }
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_run_envelope(path: Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_training_run_envelope(
    *,
    run_id: str,
    args,
    dataset_path: Path,
    example_count: int,
    manifest: dict,
    hyperparams: dict,
    status: str,
) -> dict:
    admission_ids = list(manifest.get("admission_ids") or [])
    return {
        "jarvis_lora_training_run_version": TRAINING_RUN_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": status,
        "base_model": args.base_model,
        "dataset": {
            "path": str(dataset_path),
            "example_count": example_count,
            "sources": list(manifest.get("sources") or ["seed"]),
            "admission_ids": admission_ids,
        },
        "hyperparams": hyperparams,
        "output_dir": args.output_dir,
        "authority": {
            "proposed_by": "operator",
            "executed_by": "train_jarvis_lora.py",
        },
    }


def _validate_training_run_envelope(envelope: dict) -> None:
    errors = validate_training_run(envelope, label="training_run")
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid training run envelope: {joined}")


def _build_hyperparams(args, use_4bit: bool) -> dict:
    return {
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "lora_rank": args.lora_rank,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "per_device_batch_size": args.per_device_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "use_4bit": use_4bit,
    }


def _build_adapter_metadata(
    *,
    run_id: str,
    args,
    dataset_path: Path,
    example_count: int,
    manifest: dict,
    hyperparams: dict,
) -> dict:
    admission_ids = list(manifest.get("admission_ids") or [])
    return {
        "jarvis_lora_adapter_metadata_version": ADAPTER_METADATA_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "base_model": args.base_model,
        "dataset": {
            "path": str(dataset_path),
            "example_count": example_count,
            "sources": list(manifest.get("sources") or ["seed"]),
            "admission_ids": admission_ids,
        },
        "hyperparams": hyperparams,
        "output_dir": args.output_dir,
        "dataset_checksum": _sha256_file(dataset_path),
        "git_commit": _git_commit_best_effort(),
        "promotion_status": "draft",
        "eval_report_path": None,
        "admission_ids": admission_ids,
    }


def main():
    parser = argparse.ArgumentParser(description="Train a Jarvis LoRA adapter.")
    parser.add_argument(
        "--dataset",
        default="training/out/jarvis_train_messages.jsonl",
        help="Prepared JSONL dataset with a messages column.",
    )
    parser.add_argument(
        "--base-model",
        default=DEFAULT_BASE_MODEL,
        help="Base chat model to fine-tune.",
    )
    parser.add_argument(
        "--output-dir",
        default="training/out/jarvis-qwen-lora",
        help="Where to save checkpoints and the final adapter.",
    )
    parser.add_argument(
        "--run-envelope",
        default=None,
        help="Optional jarvis_lora_training_run.v1 envelope JSON path.",
    )
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--per-device-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--disable-4bit",
        action="store_true",
        help="Disable 4-bit loading even on NVIDIA GPUs.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. "
            "Run training/prepare_messages_dataset.py first."
        )

    dataset = load_dataset("json", data_files=str(dataset_path), split="train")
    manifest = _load_dataset_manifest(dataset_path)
    use_4bit = not args.disable_4bit
    hyperparams = _build_hyperparams(args, use_4bit=use_4bit)

    run_envelope = _load_run_envelope(Path(args.run_envelope)) if args.run_envelope else None
    run_id = str((run_envelope or {}).get("run_id") or uuid.uuid4())
    if run_envelope is None:
        run_envelope = _build_training_run_envelope(
            run_id=run_id,
            args=args,
            dataset_path=dataset_path,
            example_count=len(dataset),
            manifest=manifest,
            hyperparams=hyperparams,
            status="proposed",
        )
    _validate_training_run_envelope(run_envelope)

    model_source = _resolve_model_source(args.base_model)
    tokenizer = _load_tokenizer(model_source)
    model = _load_model(model_source, use_4bit=use_4bit)
    use_bf16, use_fp16 = _resolve_precision_flags()

    peft_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    training_args = SFTConfig(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.per_device_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        logging_steps=5,
        save_strategy="epoch",
        eval_strategy="no",
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        optim="adamw_torch",
        gradient_checkpointing=True,
        max_length=args.max_length,
        report_to="none",
        bf16=use_bf16,
        fp16=use_fp16,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        peft_config=peft_config,
        args=training_args,
    )

    trainer.train()

    output_dir = Path(args.output_dir)
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)

    metadata = _build_adapter_metadata(
        run_id=run_id,
        args=args,
        dataset_path=dataset_path,
        example_count=len(dataset),
        manifest=manifest,
        hyperparams=hyperparams,
    )
    with (final_dir / "adapter_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    completed_envelope = dict(run_envelope)
    completed_envelope["status"] = "completed"
    with (final_dir / "training_run.json").open("w", encoding="utf-8") as handle:
        json.dump(completed_envelope, handle, indent=2)

    print(f"Saved final adapter to {final_dir}")
    print(f"Saved training run envelope to {final_dir / 'training_run.json'}")
    print("Promotion requires eval, operator approval, and env vars.")
    print("Set AAIS_TEXT_MODEL_NAME to match base_model before loading the adapter.")
    print(f"Example: $env:AAIS_TEXT_MODEL_NAME=\"{args.base_model}\"")
    print(f"Example: $env:AAIS_TEXT_ADAPTER_PATH=\"{final_dir}\"")


if __name__ == "__main__":
    main()
