"""Fine-tune a small Jarvis adapter with LoRA/QLoRA."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from datasets import load_dataset
from huggingface_hub import snapshot_download
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer


DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


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
    model_source = _resolve_model_source(args.base_model)
    tokenizer = _load_tokenizer(model_source)
    model = _load_model(model_source, use_4bit=not args.disable_4bit)
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

    metadata = {
        "base_model": args.base_model,
        "dataset": str(dataset_path),
        "examples": len(dataset),
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
    }
    with (final_dir / "adapter_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Saved final adapter to {final_dir}")
    print("To use it in AAIS, set AAIS_TEXT_ADAPTER_PATH to that folder.")


if __name__ == "__main__":
    main()
