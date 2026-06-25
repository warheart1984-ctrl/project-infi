"""Validate jarvis_lora_training_run.v1 and jarvis_lora_adapter_metadata.v1 envelopes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

TRAINING_RUN_VERSION = "jarvis_lora_training_run.v1"
ADAPTER_METADATA_VERSION = "jarvis_lora_adapter_metadata.v1"
EVAL_REPORT_VERSION = "jarvis_lora_eval_report.v1"
PROMOTION_RECORD_VERSION = "jarvis_lora_promotion_record.v1"
ADMITTED_BASE_MODELS = frozenset({"Qwen/Qwen2.5-1.5B-Instruct"})
RUN_STATUSES = frozenset({"proposed", "running", "completed", "rejected"})
PROMOTION_STATUSES = frozenset({"draft", "eval_passed", "promoted"})
LOADABLE_PROMOTION_STATUSES = frozenset({"eval_passed", "promoted"})
DATASET_SOURCES = frozenset({"seed", "private", "external"})
NOVA_LAWFUL_EXPORT_ADMISSION_ID = "nova-lawful-turns-export-v1"
HYPERPARAM_KEYS = frozenset(
    {
        "epochs",
        "learning_rate",
        "max_length",
        "lora_rank",
        "lora_alpha",
        "lora_dropout",
        "per_device_batch_size",
        "gradient_accumulation_steps",
        "use_4bit",
    }
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(str(value or "").strip()))


def _validate_dataset_block(dataset: Any, label: str, errors: list[str]) -> None:
    if not isinstance(dataset, dict):
        errors.append(f"{label}:dataset must be an object")
        return

    path = str(dataset.get("path") or "").strip()
    if not path:
        errors.append(f"{label}:dataset.path is required")

    example_count = dataset.get("example_count")
    if not isinstance(example_count, int) or example_count < 1:
        errors.append(f"{label}:dataset.example_count must be integer >= 1")

    sources = dataset.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{label}:dataset.sources must be a non-empty array")
    else:
        invalid_sources = [source for source in sources if source not in DATASET_SOURCES]
        if invalid_sources:
            errors.append(f"{label}:dataset.sources has invalid values: {invalid_sources}")
        if len(sources) != len(set(sources)):
            errors.append(f"{label}:dataset.sources must be unique")

    admission_ids = dataset.get("admission_ids") or []
    if "external" in (sources or []) and not admission_ids:
        errors.append(f"{label}:dataset.admission_ids required when external source is present")


def _validate_hyperparams(hyperparams: Any, label: str, errors: list[str]) -> None:
    if not isinstance(hyperparams, dict):
        errors.append(f"{label}:hyperparams must be an object")
        return

    missing = sorted(HYPERPARAM_KEYS - set(hyperparams.keys()))
    if missing:
        errors.append(f"{label}:hyperparams missing keys: {missing}")

    epochs = hyperparams.get("epochs")
    if not isinstance(epochs, (int, float)) or epochs <= 0:
        errors.append(f"{label}:hyperparams.epochs must be > 0")

    learning_rate = hyperparams.get("learning_rate")
    if not isinstance(learning_rate, (int, float)) or learning_rate <= 0:
        errors.append(f"{label}:hyperparams.learning_rate must be > 0")

    max_length = hyperparams.get("max_length")
    if not isinstance(max_length, int) or max_length < 64:
        errors.append(f"{label}:hyperparams.max_length must be integer >= 64")

    for key in ("lora_rank", "lora_alpha", "per_device_batch_size", "gradient_accumulation_steps"):
        value = hyperparams.get(key)
        if not isinstance(value, int) or value < 1:
            errors.append(f"{label}:hyperparams.{key} must be integer >= 1")

    lora_dropout = hyperparams.get("lora_dropout")
    if not isinstance(lora_dropout, (int, float)) or lora_dropout < 0 or lora_dropout > 1:
        errors.append(f"{label}:hyperparams.lora_dropout must be between 0 and 1")

    if not isinstance(hyperparams.get("use_4bit"), bool):
        errors.append(f"{label}:hyperparams.use_4bit must be boolean")


def validate_dataset_manifest(doc: dict[str, Any], label: str = "dataset_manifest") -> list[str]:
    """Return validation errors for a jarvis_lora_dataset_manifest.v1 sidecar."""
    errors: list[str] = []

    if doc.get("manifest_version") != "jarvis_lora_dataset_manifest.v1":
        errors.append(f"{label}:invalid manifest_version")

    admission_ids = list(doc.get("admission_ids") or [])
    if NOVA_LAWFUL_EXPORT_ADMISSION_ID in admission_ids:
        if not str(doc.get("export_manifest_sha256") or "").strip():
            errors.append(
                f"{label}:export_manifest_sha256 required when {NOVA_LAWFUL_EXPORT_ADMISSION_ID} is admitted"
            )
        if not str(doc.get("export_manifest_path") or "").strip():
            errors.append(
                f"{label}:export_manifest_path required when {NOVA_LAWFUL_EXPORT_ADMISSION_ID} is admitted"
            )

    for entry in doc.get("source_files") or []:
        path = str(entry.get("path") or "").replace("\\", "/")
        if "nova_lawful_turns.jsonl" in path and NOVA_LAWFUL_EXPORT_ADMISSION_ID not in admission_ids:
            errors.append(
                f"{label}:admission_ids must include {NOVA_LAWFUL_EXPORT_ADMISSION_ID} for nova lawful corpus"
            )
            break

    return errors


def validate_training_run(doc: dict[str, Any], label: str = "training_run") -> list[str]:
    """Return validation errors for a training run envelope."""
    errors: list[str] = []

    if doc.get("jarvis_lora_training_run_version") != TRAINING_RUN_VERSION:
        errors.append(f"{label}:invalid jarvis_lora_training_run_version")

    run_id = str(doc.get("run_id") or "")
    if not _is_uuid(run_id):
        errors.append(f"{label}:run_id must be UUID")

    if not str(doc.get("created_at") or "").strip():
        errors.append(f"{label}:created_at is required")

    status = doc.get("status")
    if status not in RUN_STATUSES:
        errors.append(f"{label}:invalid status")

    base_model = doc.get("base_model")
    if base_model not in ADMITTED_BASE_MODELS:
        errors.append(f"{label}:base_model not admitted: {base_model!r}")

    _validate_dataset_block(doc.get("dataset"), label, errors)
    _validate_hyperparams(doc.get("hyperparams"), label, errors)

    if not str(doc.get("output_dir") or "").strip():
        errors.append(f"{label}:output_dir is required")

    authority = doc.get("authority")
    if not isinstance(authority, dict) or not str(authority.get("proposed_by") or "").strip():
        errors.append(f"{label}:authority.proposed_by is required")

    return errors


def validate_adapter_metadata(doc: dict[str, Any], label: str = "adapter_metadata") -> list[str]:
    """Return validation errors for adapter metadata."""
    errors: list[str] = []

    if doc.get("jarvis_lora_adapter_metadata_version") != ADAPTER_METADATA_VERSION:
        errors.append(f"{label}:invalid jarvis_lora_adapter_metadata_version")

    run_id = str(doc.get("run_id") or "")
    if not _is_uuid(run_id):
        errors.append(f"{label}:run_id must be UUID")

    if not str(doc.get("created_at") or "").strip():
        errors.append(f"{label}:created_at is required")

    base_model = doc.get("base_model")
    if base_model not in ADMITTED_BASE_MODELS:
        errors.append(f"{label}:base_model not admitted: {base_model!r}")

    _validate_dataset_block(doc.get("dataset"), label, errors)
    _validate_hyperparams(doc.get("hyperparams"), label, errors)

    if not str(doc.get("output_dir") or "").strip():
        errors.append(f"{label}:output_dir is required")

    promotion_status = doc.get("promotion_status")
    if promotion_status not in PROMOTION_STATUSES:
        errors.append(f"{label}:invalid promotion_status")

    eval_report_path = doc.get("eval_report_path")
    if promotion_status == "promoted" and not str(eval_report_path or "").strip():
        errors.append(f"{label}:eval_report_path required when promotion_status is promoted")

    admission_ids = doc.get("admission_ids") or []
    dataset = doc.get("dataset") or {}
    sources = dataset.get("sources") or []
    if "external" in sources and not admission_ids:
        errors.append(f"{label}:admission_ids required when external source is present")

    promotion_record = doc.get("promotion_record")
    if promotion_status == "promoted":
        if not isinstance(promotion_record, dict):
            errors.append(f"{label}:promotion_record required when promotion_status is promoted")
        else:
            errors.extend(
                validate_promotion_record(promotion_record, label=f"{label}.promotion_record")
            )

    return errors


def validate_promotion_record(doc: dict[str, Any], label: str = "promotion_record") -> list[str]:
    errors: list[str] = []

    if doc.get("jarvis_lora_promotion_record_version") != PROMOTION_RECORD_VERSION:
        errors.append(f"{label}:invalid jarvis_lora_promotion_record_version")

    if not str(doc.get("promoted_at") or "").strip():
        errors.append(f"{label}:promoted_at is required")

    if not str(doc.get("promoted_by") or "").strip():
        errors.append(f"{label}:promoted_by is required")

    promotion_env = doc.get("promotion_env")
    if not isinstance(promotion_env, dict):
        errors.append(f"{label}:promotion_env must be an object")
        return errors

    for key in ("AAIS_TEXT_MODEL_NAME", "AAIS_ENABLE_TEXT_ADAPTERS", "AAIS_TEXT_ADAPTER_PATH"):
        if not str(promotion_env.get(key) or "").strip():
            errors.append(f"{label}:promotion_env.{key} is required")

    return errors


def validate_eval_report(doc: dict[str, Any], label: str = "eval_report") -> list[str]:
    errors: list[str] = []

    if doc.get("jarvis_lora_eval_report_version") != EVAL_REPORT_VERSION:
        errors.append(f"{label}:invalid jarvis_lora_eval_report_version")

    if not _is_uuid(str(doc.get("run_id") or "")):
        errors.append(f"{label}:run_id must be UUID")

    if not str(doc.get("generated_at") or "").strip():
        errors.append(f"{label}:generated_at is required")

    if not str(doc.get("adapter_metadata_path") or "").strip():
        errors.append(f"{label}:adapter_metadata_path is required")

    if not str(doc.get("acceptance_profile") or "").strip():
        errors.append(f"{label}:acceptance_profile is required")

    acceptance = doc.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append(f"{label}:acceptance must be an object")
    else:
        if not isinstance(acceptance.get("passed"), bool):
            errors.append(f"{label}:acceptance.passed must be boolean")
        if not isinstance(acceptance.get("failures"), list):
            errors.append(f"{label}:acceptance.failures must be an array")

    return errors


def evaluate_adapter_load_gate(
    metadata: dict[str, Any] | None,
    runtime_base_model: str,
    *,
    label: str = "adapter_load",
) -> tuple[bool, str, dict[str, Any]]:
    """Return whether runtime may load an adapter path with this metadata."""
    if not metadata:
        return True, "metadata_missing_legacy_allowed", {
            "allowed": True,
            "reason": "metadata_missing_legacy_allowed",
            "promotion_status": None,
            "base_model": None,
            "run_id": None,
        }

    errors = validate_adapter_metadata(metadata, label=label)
    if errors:
        return False, "metadata_invalid", {
            "allowed": False,
            "reason": "metadata_invalid",
            "errors": errors,
            "promotion_status": metadata.get("promotion_status"),
            "base_model": metadata.get("base_model"),
            "run_id": metadata.get("run_id"),
        }

    promotion_status = str(metadata.get("promotion_status") or "draft")
    if promotion_status not in LOADABLE_PROMOTION_STATUSES:
        return False, "promotion_status_not_loadable", {
            "allowed": False,
            "reason": "promotion_status_not_loadable",
            "promotion_status": promotion_status,
            "base_model": metadata.get("base_model"),
            "run_id": metadata.get("run_id"),
        }

    base_model = str(metadata.get("base_model") or "")
    if base_model != str(runtime_base_model or "").strip():
        return False, "base_model_mismatch", {
            "allowed": False,
            "reason": "base_model_mismatch",
            "promotion_status": promotion_status,
            "base_model": base_model,
            "runtime_base_model": runtime_base_model,
            "run_id": metadata.get("run_id"),
        }

    return True, "allowed", {
        "allowed": True,
        "reason": "allowed",
        "promotion_status": promotion_status,
        "base_model": base_model,
        "run_id": metadata.get("run_id"),
    }


def validate_training_run_file(path: Path) -> list[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return validate_training_run(doc, label=path.name)


def validate_adapter_metadata_file(path: Path) -> list[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return validate_adapter_metadata(doc, label=path.name)


def load_schema(name: str) -> dict[str, Any]:
    path = _repo_root() / "schemas" / name
    return json.loads(path.read_text(encoding="utf-8"))
