"""Mission launch preconditions — gated on reconstructability dashboard and fitness."""

from __future__ import annotations

from typing import Protocol

from constitutional.core.articles import (
    MISSION_MAX_FOUNDER_DEPENDENCY,
    MISSION_MIN_SURVIVABILITY,
    STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN,
)
from constitutional.runtime.dashboard_governance import apply_dashboard_to_governance_gate
from constitutional.runtime.fitness_risk import get_reconstructability_fitness_state
from constitutional.runtime.reconstructability_dashboard_runtime import (
    ReconstructabilityDashboardState,
    load_reconstructability_dashboard,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

from operator_kernel.csr import CSR

DEFAULT_MIN_FITNESS = 0.5
DEFAULT_MIN_SURVIVABILITY = MISSION_MIN_SURVIVABILITY
DEFAULT_MAX_FOUNDER_DEPENDENCY = MISSION_MAX_FOUNDER_DEPENDENCY
HIGH_IMPACT_MISSION = "high_impact"


class MissionLike(Protocol):
    min_fitness: float


def can_launch_mission_with_dashboard(
    mission: MissionLike | object,
    dashboard: ReconstructabilityDashboardState,
    *,
    min_survivability: float | None = None,
    max_founder_dependency: float | None = None,
) -> bool:
    survivability_floor = min_survivability
    if survivability_floor is None:
        survivability_floor = float(
            getattr(mission, "min_survivability", DEFAULT_MIN_SURVIVABILITY)
        )
    dependency_ceiling = max_founder_dependency
    if dependency_ceiling is None:
        dependency_ceiling = float(
            getattr(mission, "max_founder_dependency", DEFAULT_MAX_FOUNDER_DEPENDENCY)
        )

    if dashboard.system_survivability_score < survivability_floor:
        return False
    if dashboard.founder_dependency_index > dependency_ceiling:
        return False
    if dashboard.steward_independence_score < STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN:
        return False
    return True


def is_high_impact_mission(mission: MissionLike | object) -> bool:
    impact = str(getattr(mission, "impact", "") or getattr(mission, "mission_class", ""))
    return impact == HIGH_IMPACT_MISSION or bool(getattr(mission, "high_impact", False))


def prepare_high_impact_mission(
    mission: MissionLike | object,
    *,
    csr: ConstitutionalStateRuntime | None = None,
    now: datetime | None = None,
) -> bool:
    """S-1.2 — run fitness assessment and Article S gate before high-impact missions."""
    from datetime import UTC, datetime

    from operator_kernel.heartbeat import run_fitness_audit

    runtime = csr or CSR
    clock = now or datetime.now(UTC).replace(microsecond=0)
    run_fitness_audit(clock, runtime)
    dashboard = load_reconstructability_dashboard(runtime)
    if not can_launch_mission_with_dashboard(mission, dashboard):
        return False
    decision = apply_dashboard_to_governance_gate(dashboard)
    return decision.allow


def can_launch_mission(
    mission: MissionLike | object,
    *,
    csr: ConstitutionalStateRuntime | None = None,
    dashboard: ReconstructabilityDashboardState | None = None,
    min_fitness: float | None = None,
) -> bool:
    """Return False when reconstructability is below mission thresholds."""
    if dashboard is not None:
        return can_launch_mission_with_dashboard(mission, dashboard)

    runtime = csr or CSR
    try:
        dashboard_doc = load_reconstructability_dashboard(runtime)
        return can_launch_mission_with_dashboard(mission, dashboard_doc)
    except KeyError:
        pass

    threshold = min_fitness
    if threshold is None:
        threshold = float(getattr(mission, "min_fitness", DEFAULT_MIN_FITNESS))

    try:
        rf_state = get_reconstructability_fitness_state(runtime)
    except KeyError:
        return False

    return rf_state.fitness_score >= threshold


def apply_dashboard_to_mission_preconditions(
    dashboard: ReconstructabilityDashboardState,
) -> ReconstructabilityDashboardState:
    """v0 hook — dashboard is already persisted; return for heartbeat chaining."""
    return dashboard
