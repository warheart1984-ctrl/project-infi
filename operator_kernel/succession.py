"""Succession protocol (C6) — Article S-2 constitutional inevitability, not founder choice."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_S2_REFERENCE,
    ARTICLE_S_REFERENCE,
    FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD,
    MANDATORY_SUCCESSION_CYCLES,
    RED_ZONE_PF_THREAT_COUNT,
    RED_ZONE_RF_THREAT_COUNT,
    SUCCESSION_MAX_FOUNDER_DEPENDENCY,
    SUCCESSION_MIN_FITNESS,
    SUCCESSION_MIN_PURPOSE_CONTINUITY_INDEX,
    SUCCESSION_MIN_STEWARD_INDEPENDENCE,
    SUCCESSION_MIN_SURVIVABILITY,
)
from constitutional.runtime.hiddenness_governance import succession_hiddenness_ready
from constitutional.hiddenness.hiddenness_runtime import HiddennessState, load_hiddenness_state
from constitutional.runtime.mission_fidelity_runtime import (
    MissionFidelityState,
    load_mission_fidelity_state,
)
from constitutional.runtime.purpose_governance import succession_purpose_ready
from constitutional.runtime.reconstructability_dashboard_runtime import (
    ReconstructabilityDashboardState,
)
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.survivability_amendment import (
    cold_start_steward_passes,
    fitness_passes,
)
from constitutional.significance.significance_governance import (
    succession_significance_continuity_ready,
    succession_significance_evolution_ready,
    succession_significance_judgment_ready,
)
from constitutional.salience.governance import (
    succession_perceptual_drift_ready,
    succession_salience_continuity_ready,
    succession_salience_judgment_ready,
)
from constitutional.priors.governance import succession_prior_continuity_ready, succession_prior_judgment_ready
from constitutional.environment.governance import succession_decision_environment_ready
from constitutional.significance.significance_judgment_runtime import check_succession_readiness
from constitutional.eck2.governance import succession_eck2_dual_pipeline_ready

SUCCESSION_STATE_ID = "succession_protocol__latest"
SUCCESSION_MANDATORY_TRACKER_ID = "succession_mandatory_tracker__global"
SUCCESSION_PROOF_STATE_ID = "succession_proof__latest"


class SuccessionProcessRecord(BaseModel):
    state_id: str = SUCCESSION_STATE_ID
    state_type: str = "succession_protocol"
    opened_at: datetime
    reason: str
    snapshot: dict[str, Any] = Field(default_factory=dict)
    status: str = "open"
    article_reference: str = ARTICLE_S2_REFERENCE


class SuccessionMandatoryTracker(BaseModel):
    state_id: str = SUCCESSION_MANDATORY_TRACKER_ID
    state_type: str = "succession_mandatory_tracker"
    consecutive_high_founder_cycles: int = Field(default=0, ge=0)
    last_dashboard_version: int = Field(default=0, ge=0)
    mandatory_triggered: bool = False
    last_evaluated_at: datetime | None = None


class SuccessionProof(BaseModel):
    """C6-SP2 — proof recorded as the Succession Event."""

    state_id: str = SUCCESSION_PROOF_STATE_ID
    state_type: str = "succession_proof"
    recorded_at: datetime
    continuity_proof_reconstruction: bool = False
    interpretation_summary: str = ""
    authority_chain_verified: bool = False
    invariant_interpretation: str = ""
    operational_demonstration: bool = False
    evolution_test_passed: bool = False
    dashboard_snapshot: dict[str, Any] = Field(default_factory=dict)
    complete: bool = False


class SuccessionPreconditions(BaseModel):
    reconstructability_demonstrable: bool = False
    stewardship_reproducible: bool = False
    authority_transferable: bool = False
    knowledge_externalized: bool = False
    continuity_intact: bool = False

    @property
    def all_met(self) -> bool:
        return (
            self.reconstructability_demonstrable
            and self.stewardship_reproducible
            and self.authority_transferable
            and self.knowledge_externalized
            and self.continuity_intact
        )


def succession_ready(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    mf_state: MissionFidelityState | None = None,
    interactive_passed: bool | None = None,
    csr: ConstitutionalStateRuntime | None = None,
    hiddenness: HiddennessState | None = None,
) -> bool:
    """S-2.1 — succession readiness thresholds (constitutional, not founder choice)."""
    purpose_ok, _ = succession_purpose_ready(
        dashboard,
        mf_state=mf_state,
        interactive_passed=interactive_passed,
    )
    if csr is not None:
        if hiddenness is None:
            try:
                hiddenness = load_hiddenness_state(csr)
            except KeyError:
                hiddenness = None
        hiddenness_ok, _ = succession_hiddenness_ready(dashboard, hiddenness=hiddenness)
        significance_ok, _, _, _ = _succession_significance_stack_ready(csr)
        salience_ok, _ = succession_salience_judgment_ready(csr)
        salience_ok = salience_ok and succession_salience_continuity_ready(csr)[0]
        salience_ok = salience_ok and succession_perceptual_drift_ready(csr)[0]
        prior_ok = succession_prior_continuity_ready(csr)[0]
        prior_ok = prior_ok and succession_prior_judgment_ready(csr)[0]
        env_ok = succession_decision_environment_ready(csr)[0]
        eck2_ok, _ = succession_eck2_dual_pipeline_ready(csr)
    else:
        hiddenness_ok = True
        significance_ok = True
        salience_ok = True
        prior_ok = True
        env_ok = True
        eck2_ok = True
    return (
        dashboard.steward_independence_score >= SUCCESSION_MIN_STEWARD_INDEPENDENCE
        and dashboard.system_survivability_score >= SUCCESSION_MIN_SURVIVABILITY
        and dashboard.founder_dependency_index <= SUCCESSION_MAX_FOUNDER_DEPENDENCY
        and dashboard.purpose_continuity_index >= SUCCESSION_MIN_PURPOSE_CONTINUITY_INDEX
        and cold_start_steward_passes(dashboard, fitness, csr=csr)
        and fitness_passes(dashboard, fitness, min_score=SUCCESSION_MIN_FITNESS)
        and purpose_ok
        and hiddenness_ok
        and significance_ok
        and salience_ok
        and prior_ok
        and env_ok
        and eck2_ok
    )


def evaluate_succession_preconditions(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    csr: ConstitutionalStateRuntime | None = None,
    hiddenness: HiddennessState | None = None,
) -> SuccessionPreconditions:
    """S-2.2 — constitutional preconditions before a succession event may proceed."""
    lineage_threats = {RF.EVIDENCE_LOSS, RF.LINEAGE_BREAK}
    authority_threats = {RF.AUTHORITY_OPACITY, RF.ACCOUNTABILITY_EROSION}
    if csr is not None:
        if hiddenness is None:
            try:
                hiddenness = load_hiddenness_state(csr)
            except KeyError:
                hiddenness = None
        hiddenness_ok, _ = succession_hiddenness_ready(dashboard, hiddenness=hiddenness)
    else:
        hiddenness_ok = dashboard.implicit_assumptions_required == 0

    return SuccessionPreconditions(
        reconstructability_demonstrable=fitness_passes(
            dashboard, fitness, min_score=SUCCESSION_MIN_FITNESS
        ),
        stewardship_reproducible=cold_start_steward_passes(dashboard, fitness, csr=csr),
        authority_transferable=not any(t in dashboard.active_threats for t in authority_threats),
        knowledge_externalized=dashboard.implicit_assumptions_required == 0 and hiddenness_ok,
        continuity_intact=not any(t in dashboard.active_threats for t in lineage_threats),
    )


def succession_blocked(
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
    *,
    mf_state: MissionFidelityState | None = None,
    interactive_passed: bool | None = None,
    csr: ConstitutionalStateRuntime | None = None,
    hiddenness: HiddennessState | None = None,
) -> tuple[bool, list[str]]:
    """S-2.5 — failure modes that block succession and require remediation."""
    reasons: list[str] = []

    if not fitness_passes(dashboard, fitness, min_score=SUCCESSION_MIN_FITNESS):
        reasons.append("fitness_fails")

    if not cold_start_steward_passes(dashboard, fitness, csr=csr):
        reasons.append("cold_start_fails")

    if dashboard.founder_dependency_index > SUCCESSION_MAX_FOUNDER_DEPENDENCY:
        reasons.append("founder_dependency_too_high")

    authority_threats = {RF.AUTHORITY_OPACITY, RF.ACCOUNTABILITY_EROSION}
    if any(t in dashboard.active_threats for t in authority_threats):
        reasons.append("authority_chain_incomplete")

    if dashboard.implicit_assumptions_required > 0:
        reasons.append("knowledge_not_externalized")

    if len(dashboard.active_threats) >= RED_ZONE_RF_THREAT_COUNT:
        reasons.append("active_rf_threats_red_zone")

    purpose_ok, purpose_reasons = succession_purpose_ready(
        dashboard,
        mf_state=mf_state,
        interactive_passed=interactive_passed,
    )
    if not purpose_ok:
        reasons.extend(purpose_reasons)

    if csr is not None:
        if hiddenness is None:
            try:
                hiddenness = load_hiddenness_state(csr)
            except KeyError:
                hiddenness = None
        hiddenness_ok, hiddenness_reasons = succession_hiddenness_ready(
            dashboard,
            hiddenness=hiddenness,
        )
        if not hiddenness_ok:
            reasons.extend(hiddenness_reasons)

        _, judgment_reasons, continuity_reasons, evolution_reasons = _succession_significance_stack_ready(
            csr
        )
        reasons.extend(judgment_reasons)
        reasons.extend(continuity_reasons)
        reasons.extend(evolution_reasons)

        _, salience_judgment_reasons = succession_salience_judgment_ready(csr)
        _, salience_continuity_reasons = succession_salience_continuity_ready(csr)
        _, perceptual_drift_reasons = succession_perceptual_drift_ready(csr)
        _, prior_continuity_reasons = succession_prior_continuity_ready(csr)
        _, prior_judgment_reasons = succession_prior_judgment_ready(csr)
        _, env_reasons = succession_decision_environment_ready(csr)
        reasons.extend(salience_judgment_reasons)
        reasons.extend(salience_continuity_reasons)
        reasons.extend(perceptual_drift_reasons)
        reasons.extend(prior_continuity_reasons)
        reasons.extend(prior_judgment_reasons)
        reasons.extend(env_reasons)

    return bool(reasons), reasons


def _succession_significance_stack_ready(
    csr: ConstitutionalStateRuntime,
) -> tuple[bool, list[str], list[str], list[str]]:
    judgment_ok, judgment_reasons = succession_significance_judgment_ready(csr)
    continuity_ok, continuity_reasons = succession_significance_continuity_ready(csr)
    evolution_ok, evolution_reasons = succession_significance_evolution_ready(csr)
    return (
        judgment_ok and continuity_ok and evolution_ok,
        judgment_reasons,
        continuity_reasons,
        evolution_reasons,
    )


def load_succession_mandatory_tracker(
    csr: ConstitutionalStateRuntime,
) -> SuccessionMandatoryTracker:
    try:
        doc = csr.get_domain_doc(SUCCESSION_MANDATORY_TRACKER_ID, SuccessionMandatoryTracker)
        assert isinstance(doc, SuccessionMandatoryTracker)
        return doc
    except KeyError:
        return SuccessionMandatoryTracker()


def save_succession_mandatory_tracker(
    csr: ConstitutionalStateRuntime,
    tracker: SuccessionMandatoryTracker,
) -> None:
    csr.put_domain_doc(SUCCESSION_MANDATORY_TRACKER_ID, "succession_mandatory_tracker", tracker)


def track_mandatory_succession_cycle(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    *,
    evaluated_at: datetime | None = None,
) -> SuccessionMandatoryTracker:
    """S-2.3 — count cycles where founder dependency threatens survivability."""
    now = evaluated_at or dashboard.snapshot_at
    tracker = load_succession_mandatory_tracker(csr)

    if dashboard.version != tracker.last_dashboard_version:
        if dashboard.founder_dependency_index > FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD:
            tracker.consecutive_high_founder_cycles += 1
        else:
            tracker.consecutive_high_founder_cycles = 0
        tracker.last_dashboard_version = dashboard.version
        tracker.last_evaluated_at = now

    if tracker.consecutive_high_founder_cycles >= MANDATORY_SUCCESSION_CYCLES:
        tracker.mandatory_triggered = True

    save_succession_mandatory_tracker(csr, tracker)
    return tracker


def mandatory_succession_required(tracker: SuccessionMandatoryTracker) -> bool:
    return tracker.mandatory_triggered


def prepare_succession_proof(
    dashboard: ReconstructabilityDashboardState,
    *,
    preconditions: SuccessionPreconditions | None = None,
    recorded_at: datetime | None = None,
) -> SuccessionProof:
    """S-2.4 — scaffold Succession Proof (C6-SP2) from current dashboard state."""
    pre = preconditions or evaluate_succession_preconditions(dashboard)
    now = recorded_at or dashboard.snapshot_at
    complete = pre.all_met and succession_ready(dashboard)

    return SuccessionProof(
        recorded_at=now,
        continuity_proof_reconstruction=pre.continuity_intact and pre.reconstructability_demonstrable,
        interpretation_summary=(
            f"Succession proof under {ARTICLE_S2_REFERENCE} at dashboard v{dashboard.version}"
        ),
        authority_chain_verified=pre.authority_transferable,
        invariant_interpretation=ARTICLE_S_REFERENCE,
        operational_demonstration=pre.stewardship_reproducible,
        evolution_test_passed=pre.knowledge_externalized,
        dashboard_snapshot=dashboard.model_dump(mode="json"),
        complete=complete,
    )


def save_succession_proof(csr: ConstitutionalStateRuntime, proof: SuccessionProof) -> SuccessionProof:
    csr.put_domain_doc(SUCCESSION_PROOF_STATE_ID, "succession_proof", proof)
    return proof


def load_succession_proof(csr: ConstitutionalStateRuntime) -> SuccessionProof | None:
    try:
        doc = csr.get_domain_doc(SUCCESSION_PROOF_STATE_ID, SuccessionProof)
        assert isinstance(doc, SuccessionProof)
        return doc
    except KeyError:
        return None


def open_succession_process(
    csr: ConstitutionalStateRuntime,
    *,
    reason: str,
    snapshot: dict[str, Any],
    opened_at: datetime | None = None,
) -> SuccessionProcessRecord:
    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    record = SuccessionProcessRecord(
        opened_at=now,
        reason=reason,
        snapshot=snapshot,
    )
    csr.put_domain_doc(SUCCESSION_STATE_ID, "succession_protocol", record)
    return record


def load_succession_process(csr: ConstitutionalStateRuntime) -> SuccessionProcessRecord | None:
    try:
        doc = csr.get_domain_doc(SUCCESSION_STATE_ID, SuccessionProcessRecord)
        assert isinstance(doc, SuccessionProcessRecord)
        return doc
    except KeyError:
        return None


def maybe_initiate_succession(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
) -> SuccessionProcessRecord | None:
    """S-1.2 — fitness assessment is mandatory before any succession event."""
    if fitness is None:
        from operator_kernel.heartbeat import run_fitness_audit

        now = dashboard.snapshot_at or datetime.now(UTC).replace(microsecond=0)
        fitness = run_fitness_audit(now, csr)
        from constitutional.runtime.reconstructability_dashboard_runtime import (
            load_reconstructability_dashboard,
        )

        try:
            dashboard = load_reconstructability_dashboard(csr)
        except KeyError:
            pass

    mf_state: MissionFidelityState | None = None
    try:
        mf_state = load_mission_fidelity_state(csr)
    except KeyError:
        mf_state = None

    interactive_passed: bool | None = None
    from constitutional.runtime.mission_fidelity_interactive import load_mission_fidelity_interactive

    interactive = load_mission_fidelity_interactive(csr)
    if interactive is not None:
        interactive_passed = interactive.interactive_passed

    hiddenness: HiddennessState | None = None
    try:
        hiddenness = load_hiddenness_state(csr)
    except KeyError:
        hiddenness = None

    blocked, block_reasons = succession_blocked(
        dashboard,
        fitness,
        mf_state=mf_state,
        interactive_passed=interactive_passed,
        csr=csr,
        hiddenness=hiddenness,
    )
    if blocked:
        return None

    if not succession_ready(
        dashboard,
        fitness,
        mf_state=mf_state,
        interactive_passed=interactive_passed,
        csr=csr,
        hiddenness=hiddenness,
    ):
        return None

    preconditions = evaluate_succession_preconditions(
        dashboard,
        fitness,
        csr=csr,
        hiddenness=hiddenness,
    )
    if not preconditions.all_met:
        return None

    sj_ready, _sj_message = check_succession_readiness(csr)
    if not sj_ready:
        return None

    existing = load_succession_process(csr)
    if existing is not None and existing.status == "open":
        return existing

    proof = prepare_succession_proof(dashboard, preconditions=preconditions)
    save_succession_proof(csr, proof)

    return open_succession_process(
        csr,
        reason=(
            f"Succession readiness satisfies {ARTICLE_S2_REFERENCE} "
            f"({ARTICLE_S_REFERENCE})."
        ),
        snapshot=dashboard.model_dump(mode="json"),
        opened_at=dashboard.snapshot_at,
    )


def apply_mandatory_succession_obligations(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    *,
    opened_at: datetime | None = None,
) -> list[str]:
    """S-2.3 — when mandatory trigger fires, record constitutional obligations."""
    tracker = track_mandatory_succession_cycle(csr, dashboard, evaluated_at=opened_at)
    if not mandatory_succession_required(tracker):
        return []

    obligations = [
        "open_succession_readiness_amendment",
        "initiate_knowledge_transfer",
        "schedule_cold_start_steward_test",
        "prepare_succession_proof",
    ]
    prepare_succession_proof(dashboard)
    return obligations


def apply_dashboard_to_succession_protocol(
    csr: ConstitutionalStateRuntime,
    dashboard: ReconstructabilityDashboardState,
    fitness: ReconstructabilityFitnessState | None = None,
) -> SuccessionProcessRecord | None:
    apply_mandatory_succession_obligations(csr, dashboard)
    return maybe_initiate_succession(csr, dashboard, fitness=fitness)
