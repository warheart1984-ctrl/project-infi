"""UL lineage helpers for Alt-3 subsystem families."""

# Mythic: Alt3 Lineage
# Engineering: Alt3LineageEngine
from __future__ import annotations

from typing import Any

from src.cisiv import normalize_cisiv_stage


def record_alt3_lineage(
    *,
    subsystem: str,
    action: str,
    mission_id: str | None = None,
    session_id: str | None = None,
    session_metadata: dict[str, Any] | None = None,
    claim_label: str = "asserted",
    cisiv_stage: str = "implementation",
    payload: dict[str, Any] | None = None,
    root: Any = None,
) -> dict[str, Any] | None:
    """Emit a capability_call lineage node for an Alt-3 subsystem action."""
    from src.ul_lineage import record_lineage_event

    body = {"alt3_action": action, "subsystem": subsystem}
    if payload:
        body.update(payload)
    return record_lineage_event(
        node_type="capability_call",
        cisiv_stage=normalize_cisiv_stage(cisiv_stage, default="implementation"),
        mission_id=mission_id,
        session_id=session_id,
        session_metadata=session_metadata,
        claim_label=claim_label,
        source_module=f"src.{subsystem}",
        payload=body,
        root=root,
    )


__all__ = ["record_alt3_lineage"]
