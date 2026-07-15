"""Durable Nova Intent store — commitments survive narrative story change."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.cog_runtime.intent_core import INTENT_VERSION, validate_intent_artifact
from src.cog_runtime.narrative_store import resolve_narrative_id, resolve_narrative_store_root

INTENT_STORE_VERSION = "1.0"
DEFAULT_WOLF_INTENT_STORE = Path("/opt/cogos/memory/operator/nova_intent")
DEFAULT_DEV_INTENT_STORE = Path(".runtime/nova_intent")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_intent_store_root(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    env_path = os.getenv("COGOS_INTENT_STORE")
    if env_path:
        return Path(env_path)
    if DEFAULT_WOLF_INTENT_STORE.is_dir() or os.getenv("COGOS_RUNTIME") == "wolf":
        return DEFAULT_WOLF_INTENT_STORE
    return DEFAULT_DEV_INTENT_STORE


def resolve_intent_id(
    metadata: dict[str, Any] | None,
    *,
    nova_face: dict[str, Any] | None = None,
) -> str:
    meta = dict(metadata or {})
    explicit = str(meta.get("nova_intent_id") or "").strip()
    if explicit:
        return resolve_narrative_id({"nova_narrative_id": explicit})
    return resolve_narrative_id(meta, nova_face=nova_face)


def intent_store_path(intent_id: str, *, store_root: Path | None = None) -> Path:
    root = resolve_intent_store_root(store_root)
    safe_id = resolve_narrative_id({"nova_narrative_id": intent_id})
    return root / f"{safe_id}.intent.json"


def load_intent_store(intent_id: str, *, store_root: Path | None = None) -> dict[str, Any] | None:
    path = intent_store_path(intent_id, store_root=store_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    intent = dict(payload.get("intent") or {})
    if not validate_intent_artifact(intent)["valid"]:
        return None
    return payload


def save_intent_store(
    intent_id: str,
    intent: dict[str, Any],
    *,
    store_root: Path | None = None,
    prior_record: dict[str, Any] | None = None,
) -> Path:
    if not validate_intent_artifact(intent)["valid"]:
        raise ValueError("intent store save invalid")
    prior = dict(prior_record or {})
    record = {
        "store_version": INTENT_STORE_VERSION,
        "intent_id": resolve_narrative_id({"nova_narrative_id": intent_id}),
        "updated_at": _utc_now(),
        "intent_version": str(intent.get("version") or INTENT_VERSION),
        "intent": dict(intent),
        "turn_count": int(prior.get("turn_count") or 0) + 1,
    }
    path = intent_store_path(intent_id, store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def rehydrate_nova_intent(
    session,
    *,
    store_root: Path | None = None,
    nova_face: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    intent_id = resolve_intent_id(metadata, nova_face=nova_face)
    metadata["nova_intent_id"] = intent_id
    record = load_intent_store(intent_id, store_root=store_root)
    if not record:
        return None
    intent = dict(record.get("intent") or {})
    metadata["nova_intent"] = intent
    metadata["nova_intent_store"] = {
        "intent_id": intent_id,
        "path": str(intent_store_path(intent_id, store_root=store_root)),
        "rehydrated_at": _utc_now(),
        "turn_count": record.get("turn_count"),
    }
    return intent


def flush_nova_intent_store(
    session,
    intent: dict[str, Any] | None,
    *,
    store_root: Path | None = None,
    nova_face: dict[str, Any] | None = None,
) -> Path | None:
    if not isinstance(intent, dict):
        return None
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    intent_id = resolve_narrative_id(metadata, nova_face=nova_face)
    prior = load_intent_store(intent_id, store_root=store_root)
    path = save_intent_store(intent_id, intent, store_root=store_root, prior_record=prior)
    metadata["nova_intent_store"] = {
        "intent_id": intent_id,
        "path": str(path),
        "flushed_at": _utc_now(),
        "turn_count": (prior or {}).get("turn_count", 0) + 1 if prior else 1,
    }
    return path
