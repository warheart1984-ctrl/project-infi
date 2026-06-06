"""Tests for jarvis_lora_training_validator."""

from __future__ import annotations

import json
from pathlib import Path

from src.jarvis_lora_training_validator import (
    evaluate_adapter_load_gate,
    validate_adapter_metadata,
    validate_eval_report,
    validate_promotion_record,
    validate_training_run,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance" / "fixtures" / "training"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_training_run_sample_passes():
    doc = _load("jarvis_lora_training_run_sample.v1.json")
    assert validate_training_run(doc) == []


def test_adapter_metadata_sample_passes():
    doc = _load("jarvis_lora_adapter_metadata_sample.v1.json")
    assert validate_adapter_metadata(doc) == []


def test_promoted_without_eval_fails():
    doc = _load("jarvis_lora_adapter_metadata_sample.v1.json")
    doc["promotion_status"] = "promoted"
    doc["eval_report_path"] = None
    errors = validate_adapter_metadata(doc)
    assert any("eval_report_path" in error for error in errors)


def test_external_without_admission_fails():
    doc = _load("jarvis_lora_training_run_sample.v1.json")
    doc["dataset"] = {
        "path": "training/out/jarvis_train_messages.jsonl",
        "example_count": 10,
        "sources": ["external"],
        "admission_ids": [],
    }
    errors = validate_training_run(doc)
    assert any("admission_ids" in error for error in errors)


def test_invalid_base_model_fails():
    doc = _load("jarvis_lora_training_run_sample.v1.json")
    doc["base_model"] = "meta-llama/Llama-3.2-1B-Instruct"
    errors = validate_training_run(doc)
    assert any("base_model" in error for error in errors)


def test_prepare_messages_dataset_builds_manifest(tmp_path):
    from training.prepare_messages_dataset import build_dataset, build_dataset_manifest

    seed_path = ROOT / "training" / "data" / "jarvis_seed_messages.jsonl"
    examples, source_files = build_dataset(seed_path, [])
    output_path = tmp_path / "jarvis_train_messages.jsonl"
    output_path.write_text(
        "\n".join(json.dumps(example, ensure_ascii=True) for example in examples) + "\n",
        encoding="utf-8",
    )

    manifest_path = build_dataset_manifest(output_path, source_files, len(examples))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["example_count"] == len(examples)
    assert manifest["sources"] == ["seed"]
    assert manifest["manifest_version"] == "jarvis_lora_dataset_manifest.v1"


def test_eval_report_sample_passes():
    doc = _load("jarvis_lora_eval_report_sample.v1.json")
    assert validate_eval_report(doc) == []


def test_promotion_record_sample_passes():
    doc = _load("jarvis_lora_promotion_record_sample.v1.json")
    assert validate_promotion_record(doc) == []


def test_promoted_metadata_requires_promotion_record():
    doc = _load("jarvis_lora_adapter_metadata_sample.v1.json")
    doc["promotion_status"] = "promoted"
    doc["eval_report_path"] = ".runtime/evals/test.json"
    errors = validate_adapter_metadata(doc)
    assert any("promotion_record" in error for error in errors)


def test_evaluate_adapter_load_gate_base_model_mismatch():
    doc = _load("jarvis_lora_adapter_metadata_sample.v1.json")
    doc["promotion_status"] = "eval_passed"
    doc["eval_report_path"] = ".runtime/evals/test.json"
    allowed, reason, _ = evaluate_adapter_load_gate(doc, "Qwen/Qwen2.5-0.5B-Instruct")
    assert allowed is False
    assert reason == "base_model_mismatch"


def test_prepare_messages_dataset_marks_external_source(tmp_path):
    from training.prepare_messages_dataset import build_dataset, build_dataset_manifest

    seed_path = ROOT / "training" / "data" / "jarvis_seed_messages.jsonl"
    supplement_path = ROOT / "training" / "data" / "hf_sft_supplement.jsonl"
    if not supplement_path.exists():
        return

    examples, source_files = build_dataset(seed_path, [supplement_path])
    output_path = tmp_path / "jarvis_train_messages.jsonl"
    output_path.write_text(
        "\n".join(json.dumps(example, ensure_ascii=True) for example in examples) + "\n",
        encoding="utf-8",
    )
    manifest_path = build_dataset_manifest(output_path, source_files, len(examples))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "external" in manifest["sources"]
    assert "jarvis-lora-hf-ultrachat-200k-v1" in manifest["admission_ids"]
