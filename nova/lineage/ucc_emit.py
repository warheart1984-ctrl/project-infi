from __future__ import annotations

from datetime import datetime, timezone

from nova.lineage.bus import publish_lineage_event
from nova.lineage.ucc_schema import UCCContext, UCCLineageEvent


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def emit_ucc_event(
    *,
    kind: str,
    actor_id: str,
    intent_id: str | None,
    cognitive_style: str,
    overload_score: float,
    pacing_ok: bool,
    capability: str | None = None,
    protection_flags: dict[str, bool] | None = None,
    interpreter_used: bool = False,
    pacing_mode: str | None = None,
    structure_mode: str | None = None,
) -> UCCLineageEvent:
    ctx = UCCContext(
        cognitive_style=cognitive_style,  # type: ignore[arg-type]
        pacing_mode=pacing_mode,  # type: ignore[arg-type]
        structure_mode=structure_mode,  # type: ignore[arg-type]
        overload_score=overload_score,
        protection_flags=protection_flags,
        interpreter_used=interpreter_used,
    )

    event = UCCLineageEvent(
        id=f"ucc:{kind}:{intent_id or 'none'}",
        kind=kind,
        actor_id=actor_id,
        intent_id=intent_id,
        ucc=ctx,
        timestamp=_now_iso(),
    )

    extra: dict = {"pacing_ok": pacing_ok}
    if capability:
        extra["capability"] = capability

    publish_lineage_event(event, extra=extra)
    return event
