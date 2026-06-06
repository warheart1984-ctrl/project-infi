"""Tests for jarvis_lora_promotion_store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.jarvis_lora_promotion_store import get_adapter, list_adapters, promote_adapter


def _write_metadata(tmp_path: Path, run_id: str, status: str, *, with_eval: bool = True):
    adapter_dir = tmp_path / "training" / "out" / "jarvis-qwen-lora" / "final"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "jarvis_lora_adapter_metadata_version": "jarvis_lora_adapter_metadata.v1",
        "run_id": run_id,
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
        "dataset_checksum": "sha256:abc",
        "git_commit": None,
        "promotion_status": status,
        "eval_report_path": ".runtime/evals/adapter-eval-test.json" if with_eval else None,
        "admission_ids": [],
    }
    (adapter_dir / "adapter_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return adapter_dir


def test_list_and_get_adapter(tmp_path):
    run_id = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    _write_metadata(tmp_path, run_id, "draft")

    adapters = list_adapters(root=tmp_path)
    assert len(adapters) == 1
    assert adapters[0]["run_id"] == run_id

    found = get_adapter(run_id, root=tmp_path)
    assert found is not None
    assert found["promotion_status"] == "draft"


def test_promote_requires_eval_passed(tmp_path):
    run_id = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    _write_metadata(tmp_path, run_id, "draft")

    with pytest.raises(ValueError, match="eval_passed"):
        promote_adapter(run_id, root=tmp_path)


def test_promote_eval_passed_adapter(tmp_path):
    run_id = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
    adapter_dir = _write_metadata(tmp_path, run_id, "eval_passed")
    metadata_path = adapter_dir / "adapter_metadata.json"

    result = promote_adapter(run_id, promoted_by="test_operator", root=tmp_path)
    assert result["promotion_status"] == "promoted"
    assert "AAIS_TEXT_ADAPTER_PATH" in result["promotion_env"]

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["promotion_status"] == "promoted"
    assert metadata["promotion_record"]["promoted_by"] == "test_operator"
