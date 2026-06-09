"""Tests for security_protocol_core immune enforcement."""

from __future__ import annotations

from src.security_protocol_core import (
    Action,
    CallerContext,
    ResourceMeta,
    ResourceType,
    SecurityProtocolCore,
)


def test_blacklisted_module_is_denied():
    core = SecurityProtocolCore()
    decision = core.check_action(
        CallerContext(id="operator", role="operator"),
        ResourceMeta(id="bad_module", type=ResourceType.TOOL, category="module", sensitivity=3),
        Action.USE_TOOL,
        immune_snapshot={
            "system_mode": "normal",
            "blacklisted_modules": [
                {"module_id": "bad_module", "blacklisted_at": "now"},
            ],
            "quarantined_resources": [],
            "disabled_tools": [],
            "caller_overrides": {},
        },
    )
    assert decision.decision.value == "deny"
    assert "blacklisted" in decision.reason.lower()
