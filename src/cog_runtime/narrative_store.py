"""Durable Nova Narrative store — identity-bound persistence across sessions."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.cog_runtime.narrative import (
    NOVA_CORE_IDENTITY,
    NARRATIVE_VERSION,
    validate_narrative_artifact,
)

NARRATIVE_STORE_VERSION = "1.0"
MAX_SESSION_HISTORY = 12
DEFAULT_WOLF_STORE = Path("/opt/cogos/memory/operator/nova_narrative")
DEFAULT_DEV_STORE = Path(".runtime/nova_narrative")
NARRATIVE_ID_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_narrative_store_root(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    env_path = os.getenv("COGOS_NARRATIVE_STORE")
    if env_path:
        return Path(env_path)
    if DEFAULT_WOLF_STORE.is_dir() or os.getenv("COGOS_RUNTIME") == "wolf":
        return DEFAULT_WOLF_STORE
    return DEFAULT_DEV_STORE


def resolve_narrative_id(
    metadata: dict[str, Any] | None,
    *,
    nova_face: dict[str, Any] | None = None,
) -> str:
    meta = dict(metadata or {})
    explicit = str(meta.get("nova_narrative_id") or "").strip()
    if explicit:
        return _sanitize_narrative_id(explicit)
    face = dict(nova_face or meta.get("nova_face") or {})
    for key in ("narrative_id", "scope", "face_id", "profile_id"):
        candidate = str(face.get(key) or "").strip()
        if candidate:
            return _sanitize_narrative_id(candidate)
    companion = str(meta.get("companion_identity") or meta.get("persona_mode") or "").strip()
    if companion:
        return _sanitize_narrative_id(companion)
    return "default"


def _sanitize_narrative_id(value: str) -> str:
    cleaned = NARRATIVE_ID_RE.sub("-", str(value or "").strip().lower()).strip("-")
    return (cleaned or "default")[:64]


def narrative_store_path(narrative_id: str, *, store_root: Path | None = None) -> Path:
    root = resolve_narrative_store_root(store_root)
    return root / f"{_sanitize_narrative_id(narrative_id)}.json"


def load_narrative_store(
    narrative_id: str,
    *,
    store_root: Path | None = None,
) -> dict[str, Any] | None:
    path = narrative_store_path(narrative_id, store_root=store_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        return None
    narrative = payload.get("narrative")
    if not isinstance(narrative, dict):
        return None
    validation = validate_narrative_artifact(narrative)
    if not validation["valid"]:
        return None
    return payload


def save_narrative_store(
    narrative_id: str,
    narrative: dict[str, Any],
    *,
    store_root: Path | None = None,
    session_id: str = "",
    prior_record: dict[str, Any] | None = None,
) -> Path:
    validation = validate_narrative_artifact(narrative)
    if not validation["valid"]:
        raise ValueError(f"narrative store save invalid: {validation['issues']}")

    prior = dict(prior_record or {})
    history = list(prior.get("session_history") or [])
    if session_id:
        history.append({"session_id": session_id, "persisted_at": _utc_now()})
    history = history[-MAX_SESSION_HISTORY:]

    record = {
        "store_version": NARRATIVE_STORE_VERSION,
        "narrative_id": _sanitize_narrative_id(narrative_id),
        "updated_at": _utc_now(),
        "core_identity": NOVA_CORE_IDENTITY,
        "narrative_version": str(narrative.get("version") or NARRATIVE_VERSION),
        "narrative": dict(narrative),
        "session_history": history,
        "turn_count": int(prior.get("turn_count") or 0) + 1,
    }
    path = narrative_store_path(narrative_id, store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def rehydrate_nova_narrative(
    session,
    *,
    store_root: Path | None = None,
    nova_face: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Load durable narrative into session.metadata before a cognitive turn."""
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    narrative_id = resolve_narrative_id(metadata, nova_face=nova_face)
    metadata["nova_narrative_id"] = narrative_id
    record = load_narrative_store(narrative_id, store_root=store_root)
    if not record:
        return None
    narrative = dict(record.get("narrative") or {})
    metadata["nova_narrative"] = narrative
    metadata["nova_narrative_store"] = {
        "narrative_id": narrative_id,
        "path": str(narrative_store_path(narrative_id, store_root=store_root)),
        "rehydrated_at": _utc_now(),
        "turn_count": record.get("turn_count"),
        "updated_at": record.get("updated_at"),
    }
    return narrative


def flush_nova_narrative_store(
    session,
    narrative: dict[str, Any] | None,
    *,
    store_root: Path | None = None,
    nova_face: dict[str, Any] | None = None,
) -> Path | None:
    """Persist session narrative artifact to the durable store."""
    if not isinstance(narrative, dict):
        return None
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return None
    narrative_id = resolve_narrative_id(metadata, nova_face=nova_face)
    prior = load_narrative_store(narrative_id, store_root=store_root)
    session_id = str(metadata.get("session_id") or getattr(session, "session_id", "") or "")
    path = save_narrative_store(
        narrative_id,
        narrative,
        store_root=store_root,
        session_id=session_id,
        prior_record=prior,
    )
    metadata["nova_narrative_store"] = {
        "narrative_id": narrative_id,
        "path": str(path),
        "flushed_at": _utc_now(),
        "turn_count": (prior or {}).get("turn_count", 0) + 1 if prior else 1,
    }
    return path


def reset_narrative_store(
    narrative_id: str,
    *,
    store_root: Path | None = None,
) -> bool:
    """Operator fail-safe: remove one identity-bound narrative record."""
    path = narrative_store_path(narrative_id, store_root=store_root)
    if not path.is_file():
        return False
    path.unlink()
    return True
