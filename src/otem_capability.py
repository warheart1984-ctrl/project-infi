"""OTEM capability level — governed ceiling for planning depth and execution ingress."""

from __future__ import annotations

import os

OTEM_MIN_CAPABILITY_LEVEL = 1
OTEM_MAX_CAPABILITY_LEVEL = 10
OTEM_DEFAULT_CAPABILITY_LEVEL = 10

# Level 10: proposal-only chat lane + execution only via workflow approvals / substrate.
OTEM_EXECUTION_APPROVAL_MIN_LEVEL = 10


def get_otem_capability_level() -> int:
    """Return configured OTEM capability level (1–10), default 10 when unset."""
    raw = str(os.environ.get("AAIS_OTEM_CAPABILITY_LEVEL", str(OTEM_DEFAULT_CAPABILITY_LEVEL))).strip()
    try:
        level = int(raw)
    except ValueError:
        level = OTEM_DEFAULT_CAPABILITY_LEVEL
    return max(OTEM_MIN_CAPABILITY_LEVEL, min(level, OTEM_MAX_CAPABILITY_LEVEL))


def get_otem_version_ceiling(level: int | None = None) -> str:
    """Map capability level to the OTEM version ceiling label."""
    resolved = get_otem_capability_level() if level is None else max(
        OTEM_MIN_CAPABILITY_LEVEL,
        min(int(level), OTEM_MAX_CAPABILITY_LEVEL),
    )
    if resolved >= OTEM_EXECUTION_APPROVAL_MIN_LEVEL:
        return "v10_governed"
    if resolved >= 5:
        return "v5_frozen"
    return f"v{resolved}_bounded"


def max_plan_steps(level: int | None = None) -> int:
    """Maximum OTEM plan steps allowed for the active capability level."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    return max(3, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))


def allows_execution_approval_path(level: int | None = None) -> bool:
    """Whether OTEM may auto-enqueue execution substrate workflow approvals."""
    resolved = get_otem_capability_level() if level is None else int(level)
    return resolved >= OTEM_EXECUTION_APPROVAL_MIN_LEVEL


def capability_posture(level: int | None = None) -> dict[str, int | str | bool]:
    """Read-only posture snapshot for status APIs and operator UI."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    version = get_otem_version_ceiling(resolved)
    approval_path = allows_execution_approval_path(resolved)
    return {
        "capability_level": resolved,
        "max_capability_level": OTEM_MAX_CAPABILITY_LEVEL,
        "version_ceiling": version,
        "proposal_only_chat_lane": True,
        "direct_execution_allowed": False,
        "execution_via_workflow_approvals": approval_path,
        "max_plan_steps": max_plan_steps(resolved),
    }
