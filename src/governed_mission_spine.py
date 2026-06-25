"""Backward-compatible alias for the governed constitutional spine."""

from __future__ import annotations

from typing import Any

from src.governed.config import GovernedRuntimeConfig, get_governed_config
from src.governed.make_governed_mission import make_governed_mission


def is_governed_mission_request(payload: dict[str, Any] | None) -> bool:
    data = dict(payload or {})
    raw = data.get("governed", data.get("governed_mission"))
    if isinstance(raw, bool):
        return raw
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def run_governed_mission_spine(
    session: Any,
    user_message: str,
    *,
    request_payload: dict[str, Any] | None = None,
    config: GovernedRuntimeConfig | None = None,
) -> dict[str, Any]:
    """Run the constitutional spine and attach results to session metadata."""
    payload = dict(request_payload or {})
    steward = {
        "operator_id": str(payload.get("operator_id") or "operator"),
        "steward_id": str(payload.get("steward_id") or payload.get("operator_id") or "operator"),
        "session_id": str(getattr(session, "session_id", "") or payload.get("session_id") or ""),
    }
    trace = make_governed_mission(user_message, steward, config=config or get_governed_config())
    metadata = getattr(session, "metadata", None)
    if isinstance(metadata, dict):
        metadata["governed_mission_spine"] = trace
    return trace
