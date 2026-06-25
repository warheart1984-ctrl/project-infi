from __future__ import annotations

from nova.lineage.bus import clear_lineage_bus
from nova.lineage.ucc_emit import emit_ucc_event
from nova.lineage.ucc_schema import UCCLineageEvent
from nova.operator.ucc_console import UCCOperatorConsole


def test_ucc_operator_console_metrics():
    clear_lineage_bus()
    emit_ucc_event(
        kind="UCC_CAPABILITY_EXEC",
        actor_id="user:1",
        intent_id="intent:1",
        cognitive_style="audhd",
        overload_score=0.4,
        pacing_ok=True,
        capability="send_email",
    )
    emit_ucc_event(
        kind="UCC_CAPABILITY_EXEC",
        actor_id="user:2",
        intent_id="intent:2",
        cognitive_style="linear",
        overload_score=0.6,
        pacing_ok=True,
        capability="send_email",
    )

    from nova.lineage.bus import list_structured_events, list_lineage_events

    console = UCCOperatorConsole(list_structured_events(), list_lineage_events())
    metrics = console.to_json()
    assert metrics["audhd_sessions"] == 1
    assert metrics["linear_sessions"] == 1

    stats = console.capability_stats("send_email")
    assert stats["count"] == 2
    assert stats["avg_overload"] == 0.5
