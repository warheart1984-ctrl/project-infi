"""Recalibration governance engine — Five-Team adversarial review behind evaluateProposal."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.continuity.css2.amendment import check_proposal_amendment, check_recalibration_amendment
from src.continuity.css2.models import (
    Calibration,
    InvariantRef,
    RecalibrationDecision,
    RecalibrationEvent,
    RecalibrationLedger,
    RecalibrationProposalContext,
    new_recalibration_event_id,
)
from src.continuity.css2.spec import CSS2_REFERENCE
from src.continuity.ra.models import default_invariants
from simulation.five_team_protocol import build_round_protocol


class AdversarialReviewResult(BaseModel):
    passed: bool
    max_attack_score: int = 0
    drift_index: int = 0
    red_findings: list[str] = Field(default_factory=list)
    black_findings: list[str] = Field(default_factory=list)
    blue_defense: str = ""
    white_notes: list[str] = Field(default_factory=list)
    gold_continuity_effect: str = "ambiguous"

    def to_team_reviews(self) -> list["TeamAdversarialReview"]:
        """Map aggregate review to per-team records for v0.2 ThresholdDelta legitimacy."""
        from src.continuity.css2.recalibration_governance import TeamAdversarialReview

        red_pass = not self.red_findings and self.max_attack_score < 7
        black_pass = not self.black_findings
        return [
            TeamAdversarialReview(
                team="red",
                passed=red_pass,
                notes="; ".join(self.red_findings) or "No red findings.",
            ),
            TeamAdversarialReview(
                team="black",
                passed=black_pass,
                notes="; ".join(self.black_findings) or "Edge cases within tolerance.",
            ),
            TeamAdversarialReview(
                team="blue",
                passed=self.passed,
                notes=self.blue_defense,
            ),
            TeamAdversarialReview(
                team="white",
                passed=True,
                notes="; ".join(self.white_notes) or "Coherence check recorded.",
            ),
            TeamAdversarialReview(
                team="gold",
                passed=self.gold_continuity_effect != "degraded",
                notes=f"Continuity effect: {self.gold_continuity_effect}",
            ),
        ]


class RecalibrationGovernanceEngine:
    """
    CSS-2 recalibration gate for RA-COS-1.

    evaluate_proposal runs Red/Black/Blue/White/Gold orchestration and
    returns a governed RecalibrationEvent for the continuity ledger.
    """

    def __init__(self, ledger: RecalibrationLedger | None = None) -> None:
        self.ledger = ledger or RecalibrationLedger()

    def evaluate_proposal(self, ctx: RecalibrationProposalContext) -> RecalibrationEvent:
        preflight = check_proposal_amendment(ctx)
        if not ctx.triggers:
            return self._reject(
                ctx,
                legitimacy_basis="No recalibration trigger — Amendment X trigger requirement.",
                audit_note="Rejected at preflight: missing triggers.",
            )

        if not any(trigger.is_legitimate for trigger in ctx.triggers):
            return self._reject(
                ctx,
                legitimacy_basis="No legitimate trigger type — persistent mismatch, failure, error, or mandate required.",
                audit_note="Rejected at preflight: illegitimate triggers.",
            )

        adversarial = self._run_adversarial_review(ctx)
        violates = self._violates_non_derogable(ctx)

        if violates:
            return self._build_event(
                ctx,
                decision="rejected",
                legitimacy_basis="violates non-derogable invariant (Amendment X invariance constraint)",
                adversarial=adversarial,
                continuity_effect="degraded",
            )

        if adversarial.max_attack_score >= 7:
            return self._build_event(
                ctx,
                decision="escalated",
                legitimacy_basis=f"High adversarial attack score ({adversarial.max_attack_score}) — White Team review required.",
                adversarial=adversarial,
                continuity_effect="ambiguous",
            )

        if not adversarial.passed:
            return self._build_event(
                ctx,
                decision="deferred",
                legitimacy_basis="Adversarial review incomplete — Blue defense insufficient.",
                adversarial=adversarial,
                continuity_effect="ambiguous",
            )

        if preflight.violations:
            return self._build_event(
                ctx,
                decision="deferred",
                legitimacy_basis=f"Amendment preflight issues: {'; '.join(preflight.violations[:2])}",
                adversarial=adversarial,
                continuity_effect="ambiguous",
            )

        event = self._build_event(
            ctx,
            decision="approved",
            legitimacy_basis="Process followed; evidence documented; invariants checked; continuity impact assessed.",
            adversarial=adversarial,
            continuity_effect=self._map_continuity_effect(adversarial),
        )
        self._apply_approved_changes(ctx, event)
        return event

    def _run_adversarial_review(self, ctx: RecalibrationProposalContext) -> AdversarialReviewResult:
        """Red/Black/Blue/White/Gold war-room for recalibration proposal."""
        chaos_results: list[dict[str, object]] = []
        red_findings: list[str] = []
        black_findings: list[str] = []

        for change in ctx.proposed_changes:
            if "identity" in change.rationale.lower() or "K1" in change.metric_id:
                red_findings.append(f"Proposed change {change.id} may affect identity coherence.")
                chaos_results.append(
                    {
                        "scenario": f"recal-{change.id}",
                        "vas_validated": False,
                        "chaos_test_passed": True,
                    }
                )
            if isinstance(change.before, (int, float)) and isinstance(change.after, (int, float)):
                if change.before and abs(change.after - change.before) > abs(change.before) * 0.5:
                    black_findings.append(
                        f"Large threshold swing on {change.metric_id} — edge-case risk."
                    )

        if not chaos_results:
            chaos_results.append(
                {"scenario": "routine_recal_probe", "vas_validated": True, "chaos_test_passed": True}
            )

        adm_proxy = min(1.0, len(ctx.proposed_changes) * 0.15)
        protocol = build_round_protocol(
            round_id=len(self.ledger.events) + 1,
            adm_drift_score=adm_proxy,
            adm_high_drift=adm_proxy >= 0.6,
            k4_satisfied=not any("K4" in change.metric_id for change in ctx.proposed_changes),
            crk1_compliant=True,
            psd_aggregate=adm_proxy * 0.5,
            chaos_results=chaos_results,
            invariant_target="Recalibration thresholds",
        )

        red_attacks = [attack for attack in protocol.attacks if attack.team == "red"]
        for attack in red_attacks:
            red_findings.append(attack.description)

        passed = protocol.max_attack_score < 7 and not red_findings
        blue_defense = (
            f"Defended {len(ctx.proposed_changes)} threshold change(s); "
            f"drift index {protocol.drift_index}; attack score {protocol.max_attack_score}."
        )

        return AdversarialReviewResult(
            passed=passed or protocol.max_attack_score <= 4,
            max_attack_score=protocol.max_attack_score,
            drift_index=protocol.drift_index,
            red_findings=red_findings,
            black_findings=black_findings,
            blue_defense=blue_defense,
            white_notes=[f"Continuity signal: {protocol.continuity_signal}"],
            gold_continuity_effect="improved" if protocol.continuity_signal == "healthy" else "ambiguous",
        )

    def _violates_non_derogable(self, ctx: RecalibrationProposalContext) -> bool:
        for inv in ctx.invariants:
            if not inv.non_derogable:
                continue
            for change in ctx.proposed_changes:
                if inv.id.lower() in change.rationale.lower():
                    return True
        return False

    def _reject(
        self,
        ctx: RecalibrationProposalContext,
        *,
        legitimacy_basis: str,
        audit_note: str,
    ) -> RecalibrationEvent:
        event = self._build_event(
            ctx,
            decision="rejected",
            legitimacy_basis=legitimacy_basis,
            adversarial=AdversarialReviewResult(passed=False),
            continuity_effect="degraded",
            audit_notes=[audit_note],
        )
        self.ledger.append(event)
        return event

    def _build_event(
        self,
        ctx: RecalibrationProposalContext,
        *,
        decision: RecalibrationDecision,
        legitimacy_basis: str,
        adversarial: AdversarialReviewResult,
        continuity_effect: str,
        audit_notes: list[str] | None = None,
    ) -> RecalibrationEvent:
        audit_trail = [
            f"{CSS2_REFERENCE} governance evaluation",
            adversarial.blue_defense,
            *adversarial.white_notes,
            *(audit_notes or []),
        ]
        event = RecalibrationEvent(
            event_id=new_recalibration_event_id(),
            timestamp=datetime.now(UTC).replace(microsecond=0),
            scope=ctx.scope,
            trigger_type=ctx.trigger_type,
            failure_mode_before=ctx.candidate_failure_mode,
            proposed_changes=ctx.proposed_changes,
            invariants_checked=ctx.invariants,
            constraints_checked=[inv.id for inv in ctx.invariants],
            decision=decision,
            legitimacy_basis=legitimacy_basis,
            continuity_effect=continuity_effect,  # type: ignore[arg-type]
            decided_by="RecalibrationGovernanceEngine",
            triggers=ctx.triggers,
            adversarial_review_passed=adversarial.passed,
            audit_trail=audit_trail,
        )
        compliance = check_recalibration_amendment(event)
        if not compliance.compliant and decision == "approved":
            event.decision = "deferred"
            event.legitimacy_basis = f"Amendment X compliance failed: {'; '.join(compliance.violations[:2])}"
        self.ledger.append(event)
        return event

    def _apply_approved_changes(
        self,
        ctx: RecalibrationProposalContext,
        event: RecalibrationEvent,
    ) -> None:
        if event.decision != "approved":
            return
        cal_id = f"cal-{ctx.scope}"
        existing = self.ledger.get_calibration(cal_id)
        thresholds = dict(existing.thresholds) if existing else {}

        for change in ctx.proposed_changes:
            band = thresholds.get(change.metric_id)
            if band is None:
                from src.continuity.css2.models import ThresholdBand

                after_val = float(change.after) if isinstance(change.after, (int, float)) else 1.0
                thresholds[change.metric_id] = ThresholdBand(
                    metric_id=change.metric_id,
                    normal_max=after_val * 0.5,
                    concerning_max=after_val * 0.8,
                    intervention_max=after_val,
                )
            else:
                if isinstance(change.after, (int, float)):
                    band.intervention_max = float(change.after)

        self.ledger.calibrations[cal_id] = Calibration(
            calibration_id=cal_id,
            scope=ctx.scope,
            thresholds=thresholds,
            version=(existing.version + 1) if existing else 1,
            governed=True,
        )

    @staticmethod
    def _map_continuity_effect(adversarial: AdversarialReviewResult) -> str:
        if adversarial.gold_continuity_effect == "improved":
            return "improved"
        if adversarial.max_attack_score >= 5:
            return "degraded"
        return "ambiguous"


def default_recalibration_invariants() -> list[InvariantRef]:
    """Map K1–K4 to CSS-2 InvariantRef for governance checks."""
    refs: list[InvariantRef] = []
    for inv_id, inv in default_invariants().items():
        refs.append(
            InvariantRef(
                id=inv_id,
                description=inv.description,
                non_derogable=inv_id in {"K1", "K3"},
            )
        )
    return refs


class SimpleRecalibrationGovernance(RecalibrationGovernanceEngine):
    """Alias matching the spec's SimpleRecalibrationGovernance stub."""

    async def evaluate_proposal_async(self, ctx: RecalibrationProposalContext) -> RecalibrationEvent:
        return self.evaluate_proposal(ctx)
