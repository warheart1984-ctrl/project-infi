"""Tests for runtime adapter governance guard."""

from __future__ import annotations

import json
from pathlib import Path
from src.jarvis_lora_training_validator import evaluate_adapter_load_gate
from src.models import MultiModalAI


def test_evaluate_adapter_load_gate_blocks_draft():
    metadata = {
        "jarvis_lora_adapter_metadata_version": "jarvis_lora_adapter_metadata.v1",
        "run_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "created_at": "2026-06-05T14:30:00Z",
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "dataset": {
            "path": "training/out/jarvis_train_messages.jsonl",
            "example_count": 8,
            "sources": ["seed"],
            "admission_ids": [],
        },
        "hyperparams": {
            "epochs": 3.0,
            "learning_rate": 0.0002,
            "max_length": 512,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "use_4bit": True,
        },
        "output_dir": "training/out/jarvis-qwen-lora",
        "promotion_status": "draft",
        "eval_report_path": None,
        "admission_ids": [],
    }
    allowed, reason, _ = evaluate_adapter_load_gate(
        metadata,
        "Qwen/Qwen2.5-1.5B-Instruct",
    )
    assert allowed is False
    assert reason == "promotion_status_not_loadable"


def test_evaluate_adapter_load_gate_allows_eval_passed():
    metadata = {
        "jarvis_lora_adapter_metadata_version": "jarvis_lora_adapter_metadata.v1",
        "run_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "created_at": "2026-06-05T14:30:00Z",
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "dataset": {
            "path": "training/out/jarvis_train_messages.jsonl",
            "example_count": 8,
            "sources": ["seed"],
            "admission_ids": [],
        },
        "hyperparams": {
            "epochs": 3.0,
            "learning_rate": 0.0002,
            "max_length": 512,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "use_4bit": True,
        },
        "output_dir": "training/out/jarvis-qwen-lora",
        "promotion_status": "eval_passed",
        "eval_report_path": ".runtime/evals/test.json",
        "admission_ids": [],
    }
    allowed, reason, _ = evaluate_adapter_load_gate(
        metadata,
        "Qwen/Qwen2.5-1.5B-Instruct",
    )
    assert allowed is True
    assert reason == "allowed"


def test_filter_adapter_paths_by_governance(tmp_path):
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    metadata = {
        "jarvis_lora_adapter_metadata_version": "jarvis_lora_adapter_metadata.v1",
        "run_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "created_at": "2026-06-05T14:30:00Z",
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "dataset": {
            "path": "training/out/jarvis_train_messages.jsonl",
            "example_count": 8,
            "sources": ["seed"],
            "admission_ids": [],
        },
        "hyperparams": {
            "epochs": 3.0,
            "learning_rate": 0.0002,
            "max_length": 512,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "use_4bit": True,
        },
        "output_dir": "training/out/jarvis-qwen-lora",
        "promotion_status": "draft",
        "eval_report_path": None,
        "admission_ids": [],
    }
    (adapter_dir / "adapter_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    model = MultiModalAI(device="cpu")
    model.text_model_name = "Qwen/Qwen2.5-1.5B-Instruct"
    filtered = model._filter_adapter_paths_by_governance({"fast": str(adapter_dir)})
    assert filtered == {}
    assert model.adapter_governance["blocked"]
