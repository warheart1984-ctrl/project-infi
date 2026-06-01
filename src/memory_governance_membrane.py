"""Unified memory governance membrane — board + Nova stores + session metadata."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.intent_store import (
    flush_nova_intent_store,
    rehydrate_nova_intent,
    resolve_intent_store_root,
)
from src.cog_runtime.narrative_store import (
    flush_nova_narrative_store,
    rehydrate_nova_narrative,
    resolve_narrative_store_root,
)
from src.cogos_runtime_bridge import seed_session_nova_intent, seed_session_nova_narrative


def resolve_operator_identity_id(session) -> str:
    metadata = getattr(session, "metadata", None) or {}
    if not isinstance(metadata, dict):
        return "default"
    from src.cog_runtime.narrative_store import resolve_narrative_id

    return resolve_narrative_id(metadata, nova_face=metadata.get("nova_face"))


def seed_session_memory_membrane(
    session,
    *,
    jarvis_operator=None,
    companion_turn: bool = False,
) -> dict[str, Any]:
    """Boot-seed durable Nova stores and attach board snapshot to session metadata."""
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return {"seeded": False, "reason": "missing_metadata"}

    identity_id = resolve_operator_identity_id(session)
    narrative_root = resolve_narrative_store_root(metadata.get("nova_narrative_store_root"))
    intent_root = resolve_intent_store_root(metadata.get("nova_intent_store_root"))

    membrane: dict[str, Any] = {
        "membrane_version": "1.0",
        "identity_id": identity_id,
        "companion_turn": companion_turn,
        "narrative_rehydrated": False,
        "intent_rehydrated": False,
        "board_attached": False,
    }

    if companion_turn or metadata.get("nova_narrative_persist") or metadata.get("nova_intent_persist"):
        seeded = seed_session_nova_narrative(
            metadata,
            identity_id,
            store_root=narrative_root,
        )
        metadata.update(seeded)
        membrane["narrative_rehydrated"] = bool(metadata.get("nova_narrative"))
        seeded_intent = seed_session_nova_intent(metadata, identity_id, store_root=intent_root)
        metadata.update(seeded_intent)
        membrane["intent_rehydrated"] = bool(metadata.get("nova_intent"))

    if jarvis_operator is not None:
        try:
            snapshot = jarvis_operator.memory_enforcer.get_memory_board_snapshot(
                runtime_context="operator_runtime",
            )
            if isinstance(snapshot, dict):
                metadata["memory_board_snapshot"] = snapshot
                from src.cog_runtime.memory import normalize_cortex_memory_cues

                metadata["cortex_memory_cues"] = normalize_cortex_memory_cues(
                    snapshot,
                    metadata=metadata,
                )
                membrane["board_attached"] = True
        except Exception:
            membrane["board_error"] = "snapshot_unavailable"

    metadata["memory_governance_membrane"] = membrane
    return membrane


def attach_turn_memory_membrane(session, *, jarvis_operator=None) -> dict[str, Any]:
    """Rehydrate durable stores and refresh board cues at turn boundary."""
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return {"attached": False}

    identity_id = resolve_operator_identity_id(session)
    narrative_root = resolve_narrative_store_root(metadata.get("nova_narrative_store_root"))
    intent_root = resolve_intent_store_root(metadata.get("nova_intent_store_root"))

    rehydrate_nova_narrative(session, store_root=narrative_root, nova_face=metadata.get("nova_face"))
    rehydrate_nova_intent(session, store_root=intent_root, nova_face=metadata.get("nova_face"))

    membrane = seed_session_memory_membrane(
        session,
        jarvis_operator=jarvis_operator,
        companion_turn=bool(metadata.get("nova_face") or metadata.get("persona_mode")),
    )
    membrane["turn_boundary"] = "pre_cortex"
    membrane["identity_id"] = identity_id
    metadata["memory_governance_membrane"] = membrane
    return membrane


def flush_turn_memory_membrane(
    session,
    *,
    narrative: dict[str, Any] | None = None,
    intent: dict[str, Any] | None = None,
    jarvis_operator=None,
) -> dict[str, Any]:
    """Flush durable Nova stores through the unified membrane after a turn."""
    metadata = getattr(session, "metadata", None)
    if not isinstance(metadata, dict):
        return {"flushed": False}

    narrative_root = resolve_narrative_store_root(metadata.get("nova_narrative_store_root"))
    intent_root = resolve_intent_store_root(metadata.get("nova_intent_store_root"))
    narrative_payload = narrative if isinstance(narrative, dict) else metadata.get("nova_narrative")
    intent_payload = intent if isinstance(intent, dict) else metadata.get("nova_intent")

    result: dict[str, Any] = {"flushed": False, "paths": {}}
    if isinstance(narrative_payload, dict):
        path = flush_nova_narrative_store(
            session,
            narrative_payload,
            store_root=narrative_root,
            nova_face=metadata.get("nova_face"),
        )
        if path:
            result["paths"]["narrative"] = str(path)
            result["flushed"] = True
            _record_membrane_board_event(
                jarvis_operator,
                event_type="nova_narrative_flush",
                details={"path": str(path), "identity_id": resolve_operator_identity_id(session)},
            )
    if isinstance(intent_payload, dict):
        path = flush_nova_intent_store(
            session,
            intent_payload,
            store_root=intent_root,
            nova_face=metadata.get("nova_face"),
        )
        if path:
            result["paths"]["intent"] = str(path)
            result["flushed"] = True
            _record_membrane_board_event(
                jarvis_operator,
                event_type="nova_intent_flush",
                details={"path": str(path), "identity_id": resolve_operator_identity_id(session)},
            )

    metadata["memory_governance_membrane_flush"] = result
    return result


def _record_membrane_board_event(
    jarvis_operator,
    *,
    event_type: str,
    details: dict[str, Any],
) -> None:
    if jarvis_operator is None:
        return
    try:
        jarvis_operator.memory_enforcer.record_board_event(
            action=event_type,
            slot_id="slot_05",
            source="memory_governance_membrane",
            detail=str(details.get("path") or event_type),
            meta=details,
            runtime_context="operator_runtime",
        )
    except Exception:
        return
