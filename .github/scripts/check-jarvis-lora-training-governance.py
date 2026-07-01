#!/usr/bin/env python3
"""Jarvis LoRA training governance gate (structure + implementation + verification)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md",
    "schemas/jarvis_lora_training_run.v1.json",
    "schemas/jarvis_lora_adapter_metadata.v1.json",
    "schemas/jarvis_lora_eval_report.v1.json",
    "schemas/jarvis_lora_promotion_record.v1.json",
    "src/jarvis_lora_training_validator.py",
    "src/jarvis_lora_promotion_store.py",
    "evals/run_adapter_eval.py",
    "tools/ops/promote_jarvis_adapter.py",
    "governance/fixtures/training/jarvis_lora_training_run_sample.v1.json",
    "governance/fixtures/training/jarvis_lora_adapter_metadata_sample.v1.json",
    "governance/fixtures/training/jarvis_lora_eval_report_sample.v1.json",
    "governance/fixtures/training/jarvis_lora_promotion_record_sample.v1.json",
    "governance/fixtures/training/hf_sft_supplement_admission.v1.json",
    "governance/subsystem_genomes/jarvis_lora_training.genome.v1.json",
    "docs/proof/training/JARVIS_LORA_TRAINING_V1_PROOF.md",
    "docs/proof/training/JARVIS_LORA_TRAINING_V2_PROOF.md",
    "training/import_hf_sft_supplement.py",
]

CANONICAL_ADAPTER_FINAL = "training/out/jarvis-qwen-lora/final"

V2_TEST_FILES = [
    "tests/test_jarvis_lora_training_validator.py",
    "tests/test_jarvis_lora_promotion_store.py",
    "tests/test_models_adapter_guard.py",
    "tests/test_api_operator_training_adapters.py",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    sys.path.insert(0, str(REPO))
    from src.jarvis_lora_training_validator import (
        validate_adapter_metadata,
        validate_eval_report,
        validate_promotion_record,
        validate_training_run,
    )

    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (REPO / rel).is_file():
            errors.append(f"missing:{rel}")

    contract = (REPO / "docs/contracts/JARVIS_LORA_TRAINING_CONTRACT.md").read_text(
        encoding="utf-8",
        errors="replace",
    )
    for token in (
        "Jarvis LoRA Training Contract v2",
        "CISIV stage: **implementation**",
        "jarvis_lora_eval_report.v1",
        "jarvis_lora_promotion_record.v1",
        "Runtime load law",
        "Eval acceptance law",
        "jarvis-lora-hf-ultrachat-200k-v1",
        CANONICAL_ADAPTER_FINAL,
        "/api/operator/training/adapters",
    ):
        if token not in contract:
            errors.append(f"contract:missing token {token!r}")

    makefile = (REPO / "Makefile").read_text(encoding="utf-8", errors="replace")
    if "jarvis-lora-training-gate" not in makefile:
        errors.append("makefile:missing jarvis-lora-training-gate target")
    if "operator-workflow-stack-gate:" in makefile and "jarvis-lora-training-gate" not in makefile.split(
        "operator-workflow-stack-gate:", 1
    )[1].split("\n", 1)[0]:
        errors.append("makefile:operator-workflow-stack-gate must include jarvis-lora-training-gate")

    run_sample = _load_json(
        REPO / "governance/fixtures/training/jarvis_lora_training_run_sample.v1.json"
    )
    metadata_sample = _load_json(
        REPO / "governance/fixtures/training/jarvis_lora_adapter_metadata_sample.v1.json"
    )
    eval_sample = _load_json(
        REPO / "governance/fixtures/training/jarvis_lora_eval_report_sample.v1.json"
    )
    promotion_sample = _load_json(
        REPO / "governance/fixtures/training/jarvis_lora_promotion_record_sample.v1.json"
    )
    admission = _load_json(
        REPO / "governance/fixtures/training/hf_sft_supplement_admission.v1.json"
    )

    errors.extend(validate_training_run(run_sample, "run_sample"))
    errors.extend(validate_adapter_metadata(metadata_sample, "metadata_sample"))
    errors.extend(validate_eval_report(eval_sample, "eval_sample"))
    errors.extend(validate_promotion_record(promotion_sample, "promotion_sample"))

    if admission.get("admission_id") != "jarvis-lora-hf-ultrachat-200k-v1":
        errors.append("admission_fixture:invalid admission_id")

    promoted_without_eval = dict(metadata_sample)
    promoted_without_eval["promotion_status"] = "promoted"
    promoted_without_eval["eval_report_path"] = None
    if not validate_adapter_metadata(promoted_without_eval, "promoted_without_eval"):
        errors.append("validator:failed to reject promoted without eval_report_path")

    external_without_admission = dict(run_sample)
    external_without_admission["dataset"] = {
        "path": "training/out/jarvis_train_messages.jsonl",
        "example_count": 10,
        "sources": ["external"],
        "admission_ids": [],
    }
    if not validate_training_run(external_without_admission, "external_without_admission"):
        errors.append("validator:failed to reject external source without admission_ids")

    invalid_base_model = dict(run_sample)
    invalid_base_model["base_model"] = "meta-llama/Llama-3.2-1B-Instruct"
    if not validate_training_run(invalid_base_model, "invalid_base_model"):
        errors.append("validator:failed to reject non-admitted base model")

    launcher = (REPO / "tools/ops/start-personal.ps1").read_text(encoding="utf-8", errors="replace")
    if "jarvis-qwen-lora-firstpass" in launcher:
        errors.append("launcher:still references jarvis-qwen-lora-firstpass")
    if CANONICAL_ADAPTER_FINAL.replace("/", "\\") not in launcher:
        errors.append("launcher:missing canonical adapter final path")

    api_source = "\n".join(
        [
            (REPO / "src/api.py").read_text(encoding="utf-8", errors="replace"),
            (REPO / "src/operator_api_routes.py").read_text(encoding="utf-8", errors="replace"),
        ]
    )
    for route in (
        "/api/operator/training/adapters",
        "/api/operator/training/adapters/<run_id>/promote",
    ):
        if route not in api_source:
            errors.append(f"api:missing route {route}")

    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *V2_TEST_FILES, "-q"],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        errors.append("pytest:jarvis lora v2 tests failed")
        errors.append(result.stdout[-2000:] if result.stdout else "")
        errors.append(result.stderr[-2000:] if result.stderr else "")

    if errors:
        print("[jarvis-lora-training-gate] FAIL")
        for err in errors:
            if err:
                print(f"  - {err}")
        return 1

    print("[jarvis-lora-training-gate] PASS (v2 contract + enforcement + eval + promotion)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
