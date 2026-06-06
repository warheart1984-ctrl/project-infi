"""API tests for operator training adapter routes."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("flask_cors")
import src.api as api


def _write_eval_passed_adapter(tmp_path: Path):
    run_id = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
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
        "promotion_status": "eval_passed",
        "eval_report_path": ".runtime/evals/adapter-eval-test.json",
        "admission_ids": [],
    }
    (adapter_dir / "adapter_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return run_id


def test_operator_training_adapter_routes(tmp_path, monkeypatch):
    run_id = _write_eval_passed_adapter(tmp_path)
    monkeypatch.setattr("src.jarvis_lora_promotion_store._repo_root", lambda: tmp_path)
    monkeypatch.setattr("src.jarvis_lora_promotion_store._training_out_root", lambda root=None: tmp_path / "training" / "out")
    monkeypatch.setattr("src.jarvis_lora_promotion_store._ledger_path", lambda root=None: tmp_path / ".runtime" / "training" / "jarvis_lora_promotions.jsonl")

    client = api.app.test_client()

    list_response = client.get("/api/operator/training/adapters")
    assert list_response.status_code == 200
    payload = list_response.get_json()
    assert len(payload["adapters"]) == 1

    detail_response = client.get(f"/api/operator/training/adapters/{run_id}")
    assert detail_response.status_code == 200
    assert detail_response.get_json()["run_id"] == run_id

    promote_response = client.post(
        f"/api/operator/training/adapters/{run_id}/promote",
        json={"promoted_by": "test_api"},
    )
    assert promote_response.status_code == 200
    body = promote_response.get_json()
    assert body["promotion_status"] == "promoted"
    assert body["promotion_env"]["AAIS_TEXT_MODEL_NAME"] == "Qwen/Qwen2.5-1.5B-Instruct"
