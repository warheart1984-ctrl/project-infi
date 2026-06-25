"""RA-COS-1 event loop — triggers → governance → registry → ledger."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from src.continuity.css2.crk_invariants import check_crk_threshold_delta
from src.continuity.css2.governance import (
    RecalibrationGovernanceEngine,
    default_recalibration_invariants,
)
from src.continuity.css2.models import (
    RecalibrationDecision,
    RecalibrationEvent,
    RecalibrationProposalContext,
    RecalibrationTrigger as CssRecalibrationTrigger,
    ThresholdChange,
    new_recalibration_event_id,
)
from src.continuity.css2.recalibration_governance import apply_approved_delta
from src.continuity.css2.threshold import (
    RecalibrationRule,
    SystemState,
    Threshold,
    ThresholdDelta,
)
from src.continuity.ra.recalibration_triggers import (
    RecalibrationTrigger as RaRecalibrationTrigger,
    RecalibrationTriggerReason,
    detect_recalibration_triggers,
)

if TYPE_CHECKING:
    from src.continuity.css2.threshold_store import RacosThresholdStore


class RACosLoopResult(BaseModel):
    triggers: list[RaRecalibrationTrigger] = Field(default_factory=list)
    events: list[RecalibrationEvent] = Field(default_factory=list)
    thresholds: list[Threshold] = Field(default_factory=list)


def process_ra_cos_event(
    event: dict[str, Any],
    drift_signals: dict[str, Any] | None,
    validation: dict[str, Any] | None,
    state: SystemState,
    *,
    governance: RecalibrationGovernanceEngine | None = None,
    rule: RecalibrationRule | None = None,
    store: RacosThresholdStore | None = None,
) -> RACosLoopResult:
    """
    End-to-end RA-COS-1 recalibration path:

    detect_recalibration_triggers → build proposal → Five-Team governance
    → apply_approved_delta on Threshold registry → append RecalibrationLedger.
    """
    engine = governance or RecalibrationGovernanceEngine()
    active_rule = rule or state.recalibration_rule
    ra_triggers = detect_recalibration_triggers(event, drift_signals, validation, state)

    thresholds = list(state.thresholds)
    if store is not None and not thresholds:
        thresholds = store.load_thresholds()

    events: list[RecalibrationEvent] = []

    threshold_by_id = {th.id: th for th in thresholds}

    for ra_trig in ra_triggers:
        th = threshold_by_id.get(ra_trig.threshold_id)
        if th is None:
            continue

        proposed_value = propose_new_threshold_value(th, ra_trig)
        if proposed_value == th.value:
            continue

        after_th = th.model_copy(update={"value": proposed_value})
        delta = ThresholdDelta(
            threshold_id=th.id,
            before=th,
            after=after_th,
            rationale=f"Auto-proposal from trigger: {ra_trig.reason}",
            proposed_by="RA-COS-1",
        )

        crk_violations = check_crk_threshold_delta(delta)
        if crk_violations:
            rec_event = _crk_rejected_event(
                delta=delta,
                violations=crk_violations,
                ra_trigger=ra_trig,
                ledger=engine.ledger,
            )
            events.append(rec_event)
            if store is not None:
                store.record_recalibration_event(rec_event, threshold_id=th.id)
            continue

        ctx = build_recalibration_proposal(
            ra_trigger=ra_trig,
            threshold=th,
            delta=delta,
            evidence=ra_trig.evidence,
        )

        rec_event = engine.evaluate_proposal(ctx)
        events.append(rec_event)
        if store is not None:
            store.record_recalibration_event(rec_event, threshold_id=th.id)

        if rec_event.decision == "approved":
            thresholds = apply_approved_delta(
                delta,
                thresholds,
                updated_by=rec_event.decided_by,
            )
            threshold_by_id[th.id] = next(t for t in thresholds if t.id == th.id)
            if store is not None:
                store.apply_threshold_update(
                    delta,
                    event_id=rec_event.event_id,
                    actor_id=rec_event.decided_by,
                )

    return RACosLoopResult(
        triggers=ra_triggers,
        events=events,
        thresholds=thresholds,
    )


def propose_new_threshold_value(
    th: Threshold,
    trig: RaRecalibrationTrigger,
) -> Any:
    """Mirror continuity-engine proposeNewValue heuristics."""
    if not isinstance(th.value, (int, float)):
        return th.value
    value = float(th.value)
    if trig.reason == "late_intervention":
        return max(1, value - 1) if value > 1 else value
    if trig.reason == "over_intervention":
        return value + 1
    if trig.reason == "systematic_misclassification" and th.comparator in (">", ">="):
        return max(1, value - 1) if value > 1 else value
    return th.value


def build_recalibration_proposal(
    *,
    ra_trigger: RaRecalibrationTrigger,
    threshold: Threshold,
    delta: ThresholdDelta,
    evidence: list[Any],
) -> RecalibrationProposalContext:
    """Map RA trigger + ThresholdDelta to CSS-2 RecalibrationProposalContext."""
    css_trigger = ra_trigger_to_css_trigger(ra_trigger, threshold)
    change = ThresholdChange(
        id=f"chg-{threshold.id}",
        metric_id=threshold.metric,
        before=threshold.value,
        after=delta.after.value,
        rationale=delta.rationale,
    )
    return RecalibrationProposalContext(
        proposed_changes=[change],
        triggers=[css_trigger],
        invariants=default_recalibration_invariants(),
        scope=_scope_for_domain(threshold.domain),
        trigger_type=css_trigger.trigger_type,
        evidence=[{"ra_reason": ra_trigger.reason, "payload": evidence}],
        state_snapshot={"threshold_id": threshold.id, "domain": threshold.domain},
    )


def ra_trigger_to_css_trigger(
    ra_trigger: RaRecalibrationTrigger,
    threshold: Threshold,
) -> CssRecalibrationTrigger:
    trigger_type, persistent, repeated, calibration_err, mandate = _reason_flags(
        ra_trigger.reason
    )
    return CssRecalibrationTrigger(
        trigger_id=f"ra-{ra_trigger.threshold_id}-{ra_trigger.reason}",
        trigger_type=trigger_type,
        description=(
            f"RA-COS trigger {ra_trigger.reason} on {threshold.metric} "
            f"({threshold.domain})"
        ),
        evidence_refs=[str(ra_trigger.threshold_id)],
        persistent_mismatch=persistent,
        repeated_failure=repeated,
        calibration_error=calibration_err,
        constitutional_mandate=mandate,
    )


def _reason_flags(
    reason: RecalibrationTriggerReason,
) -> tuple[str, bool, bool, bool, bool]:
    match reason:
        case "drift_signal":
            return "drift", False, False, False, False
        case "failure_pattern" | "late_intervention":
            return "failure", False, True, False, False
        case "systematic_misclassification":
            return "evidence", True, False, True, False
        case "over_intervention":
            return "evidence", False, False, True, False
        case _:
            return "other", False, False, False, False


def _scope_for_domain(domain: str) -> str:
    if domain.startswith("CE-1") or domain.startswith("Org"):
        return "subsystem"
    if "Safety" in domain or "Trust" in domain:
        return "system"
    return "local"


def _crk_rejected_event(
    *,
    delta: ThresholdDelta,
    violations: list[str],
    ra_trigger: RaRecalibrationTrigger,
    ledger: Any,
) -> RecalibrationEvent:
    """Record CRK-blocked delta without applying registry change."""
    from datetime import UTC, datetime

    inv_desc = ", ".join(violations)
    event = RecalibrationEvent(
        event_id=new_recalibration_event_id(),
        timestamp=datetime.now(UTC).replace(microsecond=0),
        scope=_scope_for_domain(delta.before.domain),  # type: ignore[arg-type]
        trigger_type="evidence",
        proposed_changes=[
            ThresholdChange(
                id=f"chg-{delta.threshold_id}",
                metric_id=delta.before.metric,
                before=delta.before.value,
                after=delta.after.value,
                rationale=delta.rationale,
            )
        ],
        invariants_checked=default_recalibration_invariants(),
        decision="rejected",
        legitimacy_basis=(
            f"Proposed threshold violates non-derogable invariant(s): {inv_desc}."
        ),
        continuity_effect="degraded",
        decided_by="CRK-1",
        triggers=[ra_trigger_to_css_trigger(ra_trigger, delta.before)],
        adversarial_review_passed=False,
        audit_trail=[f"CRK preflight rejection: {inv_desc}"],
    )
    ledger.append(event)
    return event
