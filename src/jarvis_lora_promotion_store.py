"""List and promote governed Jarvis LoRA adapter artifacts."""

# Mythic: Jarvis Lora Promotion Store
# Engineering: JarvisLoraPromotionStoreEngine
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.jarvis_lora_training_validator import (
    PROMOTION_RECORD_VERSION,
    validate_adapter_metadata,
    validate_promotion_record,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _training_out_root(root: Path | None = None) -> Path:
    return (root or _repo_root()) / "training" / "out"


def _ledger_path(root: Path | None = None) -> Path:
    return (root or _repo_root()) / ".runtime" / "training" / "jarvis_lora_promotions.jsonl"


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _load_metadata(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _adapter_summary(metadata_path: Path, root: Path) -> dict[str, Any] | None:
    metadata = _load_metadata(metadata_path)
    if not metadata:
        return None

    adapter_dir = metadata_path.parent
    return {
        "run_id": metadata.get("run_id"),
        "base_model": metadata.get("base_model"),
        "promotion_status": metadata.get("promotion_status"),
        "example_count": (metadata.get("dataset") or {}).get("example_count"),
        "dataset_checksum": metadata.get("dataset_checksum"),
        "eval_report_path": metadata.get("eval_report_path"),
        "output_dir": metadata.get("output_dir"),
        "adapter_path": _relative_path(adapter_dir, root),
        "metadata_path": _relative_path(metadata_path, root),
        "promotion_record": metadata.get("promotion_record"),
        "validation_errors": validate_adapter_metadata(metadata, label=metadata_path.name),
    }


def list_adapters(root: Path | None = None) -> list[dict[str, Any]]:
    """Scan training/out for adapter metadata artifacts."""
    repo = root or _repo_root()
    out_root = _training_out_root(repo)
    if not out_root.exists():
        return []

    adapters: list[dict[str, Any]] = []
    for metadata_path in sorted(out_root.glob("**/final/adapter_metadata.json")):
        summary = _adapter_summary(metadata_path, repo)
        if summary:
            adapters.append(summary)

    adapters.sort(key=lambda item: str(item.get("run_id") or ""))
    return adapters


def get_adapter(run_id: str, root: Path | None = None) -> dict[str, Any] | None:
    for item in list_adapters(root=root):
        if str(item.get("run_id") or "") == str(run_id):
            return item
    return None


def build_promotion_env(metadata: dict[str, Any], adapter_path: str) -> dict[str, str]:
    base_model = str(metadata.get("base_model") or "Qwen/Qwen2.5-1.5B-Instruct")
    return {
        "AAIS_TEXT_MODEL_NAME": base_model,
        "AAIS_ENABLE_TEXT_ADAPTERS": "1",
        "AAIS_TEXT_ADAPTER_PATH": adapter_path,
    }


def promote_adapter(
    run_id: str,
    *,
    promoted_by: str = "operator",
    root: Path | None = None,
) -> dict[str, Any]:
    """Promote an adapter after eval_passed. Fails closed otherwise."""
    repo = root or _repo_root()
    adapters = list_adapters(root=repo)
    match = next((item for item in adapters if str(item.get("run_id") or "") == str(run_id)), None)
    if not match:
        raise ValueError(f"Adapter run_id not found: {run_id}")

    metadata_path = repo / str(match["metadata_path"])
    metadata = _load_metadata(metadata_path)
    if not metadata:
        raise ValueError(f"Could not read adapter metadata: {metadata_path}")

    status = str(metadata.get("promotion_status") or "draft")
    if status not in {"eval_passed", "promoted"}:
        raise ValueError(
            f"Promotion requires promotion_status eval_passed or promoted, got {status!r}"
        )
    if not str(metadata.get("eval_report_path") or "").strip():
        raise ValueError("Promotion requires eval_report_path on adapter metadata")

    adapter_path = str(match.get("adapter_path") or "")
    promotion_record = {
        "jarvis_lora_promotion_record_version": PROMOTION_RECORD_VERSION,
        "promoted_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promoted_by": promoted_by,
        "promotion_env": build_promotion_env(metadata, adapter_path),
    }
    record_errors = validate_promotion_record(promotion_record)
    if record_errors:
        raise ValueError("; ".join(record_errors))

    metadata["promotion_status"] = "promoted"
    metadata["promotion_record"] = promotion_record
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    ledger_path = _ledger_path(repo)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "event_kind": "jarvis_lora_adapter_promotion",
        "run_id": run_id,
        "promoted_at": promotion_record["promoted_at"],
        "promoted_by": promoted_by,
        "adapter_path": adapter_path,
        "metadata_path": str(match["metadata_path"]),
    }
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    return {
        "run_id": run_id,
        "promotion_status": "promoted",
        "promotion_record": promotion_record,
        "promotion_env": promotion_record["promotion_env"],
        "metadata_path": str(match["metadata_path"]),
    }
