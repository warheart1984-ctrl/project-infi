"""OTEM capability level — governed ceiling for planning depth and execution ingress."""

from __future__ import annotations

import os

OTEM_MIN_CAPABILITY_LEVEL = 1
OTEM_MAX_CAPABILITY_LEVEL = 20
OTEM_DEFAULT_CAPABILITY_LEVEL = 10

# Level 10–15: proposal-only chat lane + execution via workflow approvals / substrate.
OTEM_EXECUTION_APPROVAL_MIN_LEVEL = 10
OTEM_CONTAINMENT_MIN_LEVEL = 16
OTEM_SOVEREIGN_LEVEL = 20

AUTHORITY_BANDS = ("autonomous", "governed", "containment", "sovereign")


def get_otem_capability_level() -> int:
    """Return configured OTEM capability level (1–20), default 10 when unset."""
    raw = str(os.environ.get("AAIS_OTEM_CAPABILITY_LEVEL", str(OTEM_DEFAULT_CAPABILITY_LEVEL))).strip()
    try:
        level = int(raw)
    except ValueError:
        level = OTEM_DEFAULT_CAPABILITY_LEVEL
    return max(OTEM_MIN_CAPABILITY_LEVEL, min(level, OTEM_MAX_CAPABILITY_LEVEL))


def authority_band(level: int | None = None) -> str:
    """Map numeric OTEM level to authority band."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    if resolved >= OTEM_SOVEREIGN_LEVEL:
        return "sovereign"
    if resolved >= OTEM_CONTAINMENT_MIN_LEVEL:
        return "containment"
    if resolved >= OTEM_EXECUTION_APPROVAL_MIN_LEVEL:
        return "governed"
    return "autonomous"


def is_containment_band(level: int | None = None) -> bool:
    """True when level is in pre-ceiling containment band (16–19)."""
    resolved = get_otem_capability_level() if level is None else int(level)
    return OTEM_CONTAINMENT_MIN_LEVEL <= resolved < OTEM_SOVEREIGN_LEVEL


def is_ceiling_level(level: int | None = None) -> bool:
    """True when level is constitutional recovery ceiling (20)."""
    resolved = get_otem_capability_level() if level is None else int(level)
    return resolved >= OTEM_SOVEREIGN_LEVEL


def get_otem_version_ceiling(level: int | None = None) -> str:
    """Map capability level to the OTEM version ceiling label."""
    resolved = get_otem_capability_level() if level is None else max(
        OTEM_MIN_CAPABILITY_LEVEL,
        min(int(level), OTEM_MAX_CAPABILITY_LEVEL),
    )
    band = authority_band(resolved)
    if band == "sovereign":
        return "v20_sovereign"
    if band == "containment":
        return "v16_containment"
    if band == "governed":
        return "v10_governed"
    if resolved >= 5:
        return "v5_frozen"
    return f"v{resolved}_bounded"


def max_plan_steps(level: int | None = None) -> int:
    """Maximum OTEM plan steps allowed for the active capability level."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    if resolved >= OTEM_SOVEREIGN_LEVEL:
        return 0
    if resolved >= OTEM_CONTAINMENT_MIN_LEVEL:
        return 0
    return max(3, min(resolved, OTEM_EXECUTION_APPROVAL_MIN_LEVEL))


def allows_execution_approval_path(level: int | None = None) -> bool:
    """Whether OTEM may auto-enqueue execution substrate workflow approvals."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    return OTEM_EXECUTION_APPROVAL_MIN_LEVEL <= resolved < OTEM_CONTAINMENT_MIN_LEVEL


def capability_posture(level: int | None = None) -> dict[str, int | str | bool]:
    """Read-only posture snapshot for status APIs and operator UI."""
    resolved = get_otem_capability_level() if level is None else int(level)
    resolved = max(OTEM_MIN_CAPABILITY_LEVEL, min(resolved, OTEM_MAX_CAPABILITY_LEVEL))
    band = authority_band(resolved)
    version = get_otem_version_ceiling(resolved)
    approval_path = allows_execution_approval_path(resolved)
    rls_mode = "lightweight"
    rls_quarantine_count_recent = 0
    wonder_mode = "governed"
    try:
        from src.rls.status import rls_status

        rls_snapshot = rls_status(resolved)
        rls_mode = str(rls_snapshot.get("rls_mode") or rls_mode)
        rls_quarantine_count_recent = int(rls_snapshot.get("quarantine_count_recent") or 0)
    except Exception:
        try:
            from src.rls.substrate import rls_mode_for_level

            rls_mode = rls_mode_for_level(resolved)
        except Exception:
            pass
    try:
        from src.wonder.status import wonder_status

        wonder_snapshot = wonder_status(resolved)
        wonder_mode = str(wonder_snapshot.get("wonder_mode") or wonder_mode)
    except Exception:
        try:
            from src.wonder.gate import wonder_mode_for_level

            wonder_mode = wonder_mode_for_level(resolved)
        except Exception:
            pass
    return {
        "capability_level": resolved,
        "max_capability_level": OTEM_MAX_CAPABILITY_LEVEL,
        "authority_band": band,
        "version_ceiling": version,
        "proposal_only_chat_lane": True,
        "direct_execution_allowed": False,
        "execution_via_workflow_approvals": approval_path,
        "containment_band": is_containment_band(resolved),
        "ceiling_level": is_ceiling_level(resolved),
        "max_plan_steps": max_plan_steps(resolved),
        "rls_mode": rls_mode,
        "rls_quarantine_count_recent": rls_quarantine_count_recent,
        "wonder_mode": wonder_mode,
    }
