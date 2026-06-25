from __future__ import annotations

import pytest

from nova.law_kernel.models import new_intent
from nova.lineage.bus import clear_lineage_bus
from nova.substrate.ucc_send_email import (
    clear_sent_emails,
    make_ucc_send_email_registry,
    send_email_contract,
)


def make_intent():
    return new_intent(
        kind="ACT",
        payload={
            "capability": "send_email",
            "tool_args": {
                "to": "boss@example.com",
                "body": "Hi, I can't take this on right now.",
            },
        },
        origin="user:123",
    )


def test_send_email_blocks_on_overload():
    clear_lineage_bus()
    reg = make_ucc_send_email_registry()
    intent = make_intent()

    with pytest.raises(RuntimeError, match="Overload too high"):
        reg.execute(
            intent,
            overload_score=0.95,
            pacing_ok=True,
            cognitive_style="audhd",
        )


def test_send_email_blocks_without_pacing_consent():
    clear_lineage_bus()
    reg = make_ucc_send_email_registry()
    intent = make_intent()

    with pytest.raises(RuntimeError, match="Pacing consent not granted"):
        reg.execute(
            intent,
            overload_score=0.2,
            pacing_ok=False,
            cognitive_style="linear",
        )


def test_send_email_succeeds_when_safe():
    clear_lineage_bus()
    clear_sent_emails()
    reg = make_ucc_send_email_registry()
    intent = make_intent()

    result = reg.execute(
        intent,
        overload_score=0.3,
        pacing_ok=True,
        cognitive_style="audhd",
    )

    assert result["status"] == "sent"

    from nova.lineage.bus import list_lineage_events

    events = list_lineage_events()
    assert len(events) == 1
    extra = events[0]["extra"]
    assert events[0]["kind"] == "UCC_CAPABILITY_EXEC"
    assert extra["capability"] == "send_email"
    assert extra["pacing_ok"] is True
    assert events[0]["ucc"]["overload_score"] == 0.3


def test_send_email_contract_registered():
    reg = make_ucc_send_email_registry()
    assert send_email_contract.name == "send_email"
