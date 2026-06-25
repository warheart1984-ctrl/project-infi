"""Constitutional heartbeat — epoch runtimes plus scheduled reconstructability fitness."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from constitutional.runtime.amendment_triggers import (
    apply_dashboard_to_amendment_triggers,
    maybe_trigger_reconstructability_amendment,
)
from constitutional.runtime.constitutional_debt import apply_fitness_to_debt
from constitutional.runtime.constitutional_state_scheduler import ConstitutionalStateScheduler
from constitutional.runtime.dashboard_governance import (
    apply_and_persist_dashboard_governance,
    apply_dashboard_to_mission_preconditions as persist_dashboard_for_missions,
)
from constitutional.runtime.fitness_governance import apply_fitness_to_governance_gate
from constitutional.runtime.fitness_risk import apply_fitness_to_risk
from constitutional.runtime.global_constitutional_state import ConstitutionalStateAggregator
from constitutional.runtime.personal_constitutional_state import PersonalConstitutionalStateRuntime
from constitutional.runtime.reconstructability_dashboard_runtime import (
    ReconstructabilityDashboardRuntime,
    ReconstructabilityDashboardState,
)
from constitutional.hiddenness.hiddenness_pressure import (
    apply_hiddenness_pressure,
    apply_hiddenness_to_fitness,
    apply_hiddenness_to_mission_fidelity,
)
from constitutional.hiddenness.hiddenness_runtime_v2 import HiddennessRuntimeV2, HiddennessStateV2
from constitutional.runtime.mission_fidelity_runtime import MissionFidelityRuntime, MissionFidelityState
from constitutional.runtime.reconstructability_fitness_runtime import (
    ReconstructabilityFitnessRuntime,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

from constitutional.runtime.survivability_enforcement import (
    FITNESS_ASSESSMENT_INTERVAL,
    cold_start_test_due,
    load_cold_start_schedule,
    record_cold_start_run,
)
from operator_kernel.csr import CSR
from operator_kernel.succession import apply_dashboard_to_succession_protocol

LAST_FITNESS_RUN_AT: datetime | None = None
FITNESS_INTERVAL = FITNESS_ASSESSMENT_INTERVAL


def run_system_runtimes(
    now: datetime,
    csr: ConstitutionalStateRuntime,
    *,
    scheduler: ConstitutionalStateScheduler | None = None,
) -> None:
    sched = scheduler or ConstitutionalStateScheduler()
    sched.maybe_snapshot(csr, trigger="interval", force=sched.should_snapshot_by_time())


def run_constitutional_runtimes(now: datetime, csr: ConstitutionalStateRuntime) -> None:
    ConstitutionalStateAggregator(csr).update_snapshot(snapshot_at=now)


def run_personal_runtimes(now: datetime, csr: ConstitutionalStateRuntime) -> None:
    PersonalConstitutionalStateRuntime(csr).update_snapshot(snapshot_at=now)


def run_hiddenness_audit(
    now: datetime,
    csr: ConstitutionalStateRuntime,
    *,
    trigger_amendments: bool = False,
) -> HiddennessStateV2:
    return HiddennessRuntimeV2(csr).run_scan(
        snapshot_at=now,
        trigger_amendments=trigger_amendments,
    )


def run_mission_fidelity_test(
    now: datetime,
    csr: ConstitutionalStateRuntime,
) -> MissionFidelityState:
    return MissionFidelityRuntime(csr).run_test(snapshot_at=now)


def run_constitutional_competence_cycle(
    now: datetime,
    csr: ConstitutionalStateRuntime,
) -> dict:
    """Significance + ECK-1 + JPSS-I identity dashboard competence stack."""
    from constitutional.eck1.continuity_suite import ECK1ContinuitySuite
    from constitutional.jpss.invariant_drift_dashboard import InvariantDriftDashboardRuntime
    from constitutional.significance.competence_stack import constitutional_competence_stack_heartbeat

    stack = constitutional_competence_stack_heartbeat(csr, snapshot_at=now)
    eck1 = ECK1ContinuitySuite(csr).run(now)
    stack["eck1_continuity"] = eck1
    stack["invariant_drift_dashboard"] = InvariantDriftDashboardRuntime(csr).update_snapshot(snapshot_at=now)
    return stack


def run_constitutional_pressure_cycle(
    now: datetime,
    csr: ConstitutionalStateRuntime,
    *,
    include_competence_stack: bool = True,
) -> tuple[HiddennessStateV2, ReconstructabilityFitnessState, MissionFidelityState, ReconstructabilityDashboardState]:
    """Hiddenness-first constitutional heartbeat — meta-runtime drives R, P, and dashboard."""
    hiddenness = run_hiddenness_audit(now, csr, trigger_amendments=False)

    rf = ReconstructabilityFitnessRuntime(csr)
    fitness = rf.run_audit(snapshot_at=now)
    fitness = apply_hiddenness_to_fitness(csr, fitness, hiddenness)

    mission = run_mission_fidelity_test(now, csr)
    mission = apply_hiddenness_to_mission_fidelity(csr, mission, hiddenness)

    apply_fitness_to_debt(csr, fitness)
    apply_fitness_to_risk(csr, fitness, snapshot_at=now)
    apply_fitness_to_governance_gate(csr, fitness)
    maybe_trigger_reconstructability_amendment(csr, fitness, opened_at=now)

    dashboard = run_dashboard_update(now, csr)
    apply_hiddenness_pressure(csr, hiddenness, fitness, mission, dashboard, opened_at=now)
    record_cold_start_run(csr, dashboard, run_at=now, reason="fitness_assessment")

    if include_competence_stack:
        run_constitutional_competence_cycle(now, csr)

    return hiddenness, fitness, mission, dashboard


def run_dashboard_update(
    now: datetime,
    csr: ConstitutionalStateRuntime,
) -> ReconstructabilityDashboardState:
    fitness: ReconstructabilityFitnessState | None = None
    try:
        from constitutional.runtime.fitness_risk import get_reconstructability_fitness_state

        fitness = get_reconstructability_fitness_state(csr)
    except KeyError:
        fitness = None

    dashboard = ReconstructabilityDashboardRuntime(csr).update_snapshot(now)
    apply_and_persist_dashboard_governance(csr, dashboard)
    persist_dashboard_for_missions(csr, dashboard)
    apply_dashboard_to_succession_protocol(csr, dashboard, fitness=fitness)

    from operator_kernel.succession import load_succession_mandatory_tracker

    tracker = load_succession_mandatory_tracker(csr)
    apply_dashboard_to_amendment_triggers(
        csr,
        dashboard,
        fitness=fitness,
        opened_at=now,
        mandatory_founder_cycles=tracker.consecutive_high_founder_cycles,
    )
    return dashboard


def run_fitness_audit(
    now: datetime,
    csr: ConstitutionalStateRuntime,
) -> ReconstructabilityFitnessState:
    _, fitness, _, _ = run_constitutional_pressure_cycle(now, csr)
    return fitness


def constitutional_heartbeat(
    now: datetime | None = None,
    *,
    csr: ConstitutionalStateRuntime | None = None,
    scheduler: ConstitutionalStateScheduler | None = None,
    force_fitness: bool = False,
) -> ReconstructabilityFitnessState | None:
    """Advance constitutional runtimes and run fitness audit on schedule (v0: every 6h)."""
    global LAST_FITNESS_RUN_AT

    clock = now or datetime.now(UTC).replace(microsecond=0)
    runtime = csr or CSR

    run_system_runtimes(clock, runtime, scheduler=scheduler)
    run_constitutional_runtimes(clock, runtime)
    run_personal_runtimes(clock, runtime)

    cold_start_force = False
    try:
        from constitutional.runtime.reconstructability_dashboard_runtime import (
            load_reconstructability_dashboard,
        )

        dashboard_preview = load_reconstructability_dashboard(runtime)
        schedule = load_cold_start_schedule(runtime)
        cold_start_force, _ = cold_start_test_due(schedule, dashboard_preview, now=clock)
    except KeyError:
        cold_start_force = False

    due = (
        force_fitness
        or cold_start_force
        or LAST_FITNESS_RUN_AT is None
        or clock - LAST_FITNESS_RUN_AT >= FITNESS_INTERVAL
    )
    if not due:
        return None

    rf_state = run_fitness_audit(clock, runtime)
    LAST_FITNESS_RUN_AT = clock
    return rf_state


def reset_fitness_schedule() -> None:
    """Test helper — clear last fitness run timestamp."""
    global LAST_FITNESS_RUN_AT
    LAST_FITNESS_RUN_AT = None
