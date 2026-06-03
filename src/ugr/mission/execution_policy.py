"""URG execution modes, kill switch, and provider call policy."""

from __future__ import annotations

import os
from typing import Any


EXECUTION_MODE_DRY_RUN = "DRY_RUN"
EXECUTION_MODE_SHADOW = "SHADOW_EXECUTION"
EXECUTION_MODE_LIVE = "LIVE_EXECUTION"

EXECUTION_MODES = (
    EXECUTION_MODE_DRY_RUN,
    EXECUTION_MODE_SHADOW,
    EXECUTION_MODE_LIVE,
)

EXECUTION_STATE_PLANNED = "execution_planned"
EXECUTION_STATE_DISPATCHED = "execution_dispatched"
EXECUTION_STATE_COMMITTED = "execution_committed"
EXECUTION_STATE_SIMULATED = "execution_simulated"
EXECUTION_STATE_ABORTED = "aborted_by_operator"

URG_EXECUTION_MODE_ENV = "URG_EXECUTION_MODE"
URG_MISSION_KILL_SWITCH_ENV = "URG_MISSION_KILL_SWITCH"


def mission_kill_switch_active() -> bool:
    raw = os.getenv(URG_MISSION_KILL_SWITCH_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def resolve_execution_mode(request: dict[str, Any] | None = None) -> str:
    """Resolve mode: mission field overrides env (default DRY_RUN)."""
    req = dict(request or {})
    explicit = str(req.get("execution_mode") or os.getenv(URG_EXECUTION_MODE_ENV, "")).strip().upper()
    if explicit in EXECUTION_MODES:
        return explicit
    if llm_execute_legacy_enabled():
        return EXECUTION_MODE_LIVE
    return EXECUTION_MODE_DRY_RUN


def llm_execute_legacy_enabled() -> bool:
    """Backward compat: UGR_LLM_EXECUTE=1 implies LIVE_EXECUTION."""
    raw = os.getenv("UGR_LLM_EXECUTE", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def provider_calls_allowed(mode: str) -> bool:
    return str(mode or "").upper() in {EXECUTION_MODE_SHADOW, EXECUTION_MODE_LIVE}


def execution_results_downstream(mode: str) -> bool:
    return str(mode or "").upper() == EXECUTION_MODE_LIVE


def is_shadow_execution(mode: str) -> bool:
    return str(mode or "").upper() == EXECUTION_MODE_SHADOW


def operator_abort_requested(request: dict[str, Any] | None) -> bool:
    req = dict(request or {})
    return bool(req.get("operator_abort") or req.get("abort_by_operator"))


def reject_new_mission(*, request: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Kill switch rejects new missions unless operator_abort on in-flight only."""
    if not mission_kill_switch_active():
        return False, ""
    if operator_abort_requested(request):
        return False, ""
    return True, "urg_mission_kill_switch_active"


def should_force_provider_execute(mode: str) -> bool:
    return provider_calls_allowed(mode)
