"""Constitutional competence stack v1 — integrated significance + environment + judgment."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from constitutional.runtime.mission_fidelity_runtime import MissionFidelityRuntime
from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessRuntime
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.artifact_index import get_artifact_index
from constitutional.significance.context_aware_significance_evolution import (
    ContextAwareSignificanceEvolutionTest,
)
from constitutional.significance.decision_environment_runtime import DecisionEnvironmentRuntime
from constitutional.significance.significance_judgment_runtime import (
    SignificanceJudgmentRuntime,
    StewardSignificanceAnswer,
    check_succession_readiness,
    get_reference_lattice,
    get_reference_rationales,
)
from constitutional.significance.significance_pressure import apply_significance_pressure
from constitutional.significance.significance_review_runtime import SignificanceReviewRuntime
from constitutional.significance.significance_runtime import SignificanceRuntime
from constitutional.significance.significance_stability_runtime import SignificanceStabilityRuntime
from constitutional.significance.significance_tier_register import sync_tier_register_from_index
from constitutional.significance.stewardship_context_ledger import StewardshipContextLedger


def check_succession_readiness_with_competence(
    csr: ConstitutionalStateRuntime,
    fitness,
    mission,
    significance,
    sig_cont,
    sig_evo,
    env_state,
    sj_result,
) -> tuple[bool, str]:
    if not sj_result.passed:
        return False, f"Succession blocked: steward failed Significance Judgment (score={sj_result.score})."

    from constitutional.core.articles import (
        SUCCESSION_MIN_DECISION_ENVIRONMENT,
        SUCCESSION_MIN_FITNESS,
        SUCCESSION_MIN_PURPOSE_CONTINUITY_INDEX,
        SUCCESSION_MIN_SIGNIFICANCE_CONTINUITY,
        SUCCESSION_MIN_SIGNIFICANCE_HEALTH,
    )

    if fitness.fitness_score < SUCCESSION_MIN_FITNESS:
        return False, "Succession blocked: reconstructability fitness below threshold."

    if mission.purpose_continuity_index < SUCCESSION_MIN_PURPOSE_CONTINUITY_INDEX:
        return False, "Succession blocked: purpose continuity below threshold."

    if significance.significance_health_index < SUCCESSION_MIN_SIGNIFICANCE_HEALTH:
        return False, "Succession blocked: significance health below threshold."

    if sig_cont.continuity_index < SUCCESSION_MIN_SIGNIFICANCE_CONTINUITY:
        return False, "Succession blocked: Significance Continuity below threshold."

    if sig_evo.passed is False:
        return False, "Succession blocked: context-aware significance evolution failing."

    if env_state.environment_health_index < SUCCESSION_MIN_DECISION_ENVIRONMENT:
        return False, "Succession blocked: Decision Environment Continuity below threshold."

    ready, message = check_succession_readiness(csr)
    if not ready:
        return False, message

    return True, "Succession readiness satisfied with full constitutional competence stack."


def constitutional_competence_stack_heartbeat(
    csr: ConstitutionalStateRuntime,
    *,
    steward_knowledge_index: dict[str, str] | None = None,
    context_ledger: StewardshipContextLedger | None = None,
    current_env_snapshot: dict[str, Any] | None = None,
    steward_significance_answers: dict[str, StewardSignificanceAnswer] | None = None,
    snapshot_at: datetime | None = None,
) -> dict[str, Any]:
    """Run the full constitutional competence stack (fitness through significance judgment)."""
    now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    artifact_index = get_artifact_index(csr)
    ledger = context_ledger
    if ledger is None:
        from constitutional.significance.stewardship_context_ledger import load_stewardship_context_ledger

        ledger = load_stewardship_context_ledger(csr)
    env_snapshot = current_env_snapshot or {}

    fitness = ReconstructabilityFitnessRuntime(csr).run_audit(snapshot_at=now)
    mission = MissionFidelityRuntime(csr).run_test(snapshot_at=now)

    significance = SignificanceRuntime(csr, artifact_index=artifact_index).run_scan(snapshot_at=now)
    stability = SignificanceStabilityRuntime(csr, artifact_index=artifact_index).run(snapshot_at=now)
    sig_cont = SignificanceReviewRuntime(
        csr,
        artifact_index=artifact_index,
        steward_knowledge_index=steward_knowledge_index,
    ).run_review(snapshot_at=now)

    sig_evo = ContextAwareSignificanceEvolutionTest(
        csr=csr,
        artifact_index=artifact_index,
        context_ledger=ledger,
        current_env_snapshot=env_snapshot,
    ).run()

    env_state = DecisionEnvironmentRuntime(
        csr=csr,
        context_ledger=ledger,
        current_env_snapshot=env_snapshot,
    ).run(snapshot_at=now)

    apply_significance_pressure(csr, significance, stability, opened_at=now)
    sync_tier_register_from_index(csr, artifact_index)

    sj_runtime = SignificanceJudgmentRuntime(
        reference_lattice=get_reference_lattice(),
        reference_rationales=get_reference_rationales(),
    )
    answers = steward_significance_answers or {}
    if not answers:
        from constitutional.significance.significance_judgment_runtime import load_significance_judgment_state

        state = load_significance_judgment_state(csr)
        answers = state.steward_answers if state else {}
    sj_result = sj_runtime.evaluate(answers)

    succession_ok, succession_reason = check_succession_readiness_with_competence(
        csr,
        fitness,
        mission,
        significance,
        sig_cont,
        sig_evo,
        env_state,
        sj_result,
    )

    return {
        "fitness": fitness,
        "mission": mission,
        "significance": significance,
        "significance_stability": stability,
        "significance_continuity": sig_cont,
        "significance_evolution": sig_evo,
        "decision_environment": env_state,
        "significance_judgment": sj_result,
        "succession_ok": succession_ok,
        "succession_reason": succession_reason,
    }
