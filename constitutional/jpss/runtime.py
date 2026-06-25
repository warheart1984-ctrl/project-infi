"""JPSS-1 forward runtime — Judgment Formation Pipeline (JPSS-F)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from constitutional.core.models import StateObject
from constitutional.eck1.registers import (
    load_calibration_register,
    load_environment_register,
    save_calibration_register,
    save_environment_register,
)
from constitutional.eck1.transitions import append_to_ledgers
from constitutional.jpss.models import JPSSCycleResult
from constitutional.jpss.registers import (
    JPSS_CYCLE_STATE_ID,
    DecisionEntry,
    OutcomeEntry,
    PerceptionEntry,
    ReflectionEntry,
    load_decision_register,
    load_outcome_register,
    load_perception_register,
    load_reflection_register,
    save_decision_register,
    save_outcome_register,
    save_perception_register,
    save_reflection_register,
)
from constitutional.jpss.spec import JPSS_CANONICAL_CYCLE
from constitutional.jpss.transitions import (
    calibration_from_salience,
    calibration_update_from_reflection,
    decision_from_calibration,
    environment_from_steward_inputs,
    outcome_from_decision,
    perception_from_environment,
    reflection_from_outcome,
    salience_from_perception,
)
from constitutional.priors.ledger import load_prior_ledger, save_prior_ledger
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.ledger import load_salience_ledger, save_salience_ledger


class JPSSFormationRuntime:
    """Implements JPSS-F: Environment → … → Calibration Update."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def run(
        self,
        steward_inputs: dict[str, Any],
        *,
        snapshot_at: datetime | None = None,
    ) -> JPSSCycleResult:
        now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        decision_id = steward_inputs.get("decision_id", f"jpss-{int(now.timestamp())}")
        steward_inputs = {**steward_inputs, "decision_id": decision_id}

        environment = environment_from_steward_inputs(steward_inputs, captured_at=now)
        perception = perception_from_environment(environment, steward_inputs, captured_at=now)
        salience = salience_from_perception(perception, environment)
        calibration = calibration_from_salience(salience, environment)
        decision = decision_from_calibration(calibration, steward_inputs)
        outcome = outcome_from_decision(decision, steward_inputs, captured_at=now)
        reflection = reflection_from_outcome(outcome, decision, captured_at=now)
        calibration_update = calibration_update_from_reflection(reflection, calibration, captured_at=now)

        self._persist_registers(
            environment=environment,
            perception=perception,
            salience=salience,
            calibration=calibration,
            decision=decision,
            outcome=outcome,
            reflection=reflection,
            calibration_update=calibration_update,
        )

        cycle = JPSSCycleResult(
            decision_id=decision_id,
            environment=environment,
            perception=perception,
            salience=salience,
            calibration=calibration,
            decision=decision,
            outcome=outcome,
            reflection=reflection,
            calibration_update=calibration_update,
            stages_completed=list(JPSS_CANONICAL_CYCLE),
            captured_at=now,
        )
        self.csr.register_or_replace_state(
            StateObject(
                state_id=JPSS_CYCLE_STATE_ID,
                state_type="jpss_cycle",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(JPSS_CYCLE_STATE_ID, "jpss_cycle", cycle)
        return cycle

    def _persist_registers(self, **states) -> None:
        environment = states["environment"]
        perception = states["perception"]
        salience = states["salience"]
        calibration = states["calibration"]
        decision = states["decision"]
        outcome = states["outcome"]
        reflection = states["reflection"]
        calibration_update = states["calibration_update"]
        ts = perception.captured_at or datetime.now(UTC).replace(microsecond=0)

        perception_register = load_perception_register(self.csr)
        perception_register.append(
            PerceptionEntry(
                timestamp=ts,
                decision_id=decision.decision_id,
                available_signals=perception.available_signals,
                missing_signals=perception.missing_signals,
                intake_channels=perception.intake_channels,
                steward_id=perception.steward_id,
            )
        )
        save_perception_register(self.csr, perception_register)

        decision_register = load_decision_register(self.csr)
        decision_register.append(
            DecisionEntry(
                timestamp=ts,
                decision_id=decision.decision_id,
                outcome=decision.outcome,
                rationale=decision.rationale,
                applied_invariants=decision.applied_invariants,
                applied_purpose_clauses=decision.applied_purpose_clauses,
                steward_id=decision.steward_id,
            )
        )
        save_decision_register(self.csr, decision_register)

        outcome_register = load_outcome_register(self.csr)
        outcome_register.append(
            OutcomeEntry(
                timestamp=ts,
                decision_id=outcome.decision_id,
                observed_result=outcome.observed_result,
                expected_result=outcome.expected_result,
                success=outcome.success,
                steward_id=outcome.steward_id,
            )
        )
        save_outcome_register(self.csr, outcome_register)

        reflection_register = load_reflection_register(self.csr)
        reflection_register.append(
            ReflectionEntry(
                timestamp=ts,
                decision_id=reflection.decision_id,
                expectation_delta=reflection.expectation_delta,
                lessons=reflection.lessons,
                steward_id=reflection.steward_id,
            )
        )
        save_reflection_register(self.csr, reflection_register)

        prior_ledger = load_prior_ledger(self.csr)
        salience_ledger = load_salience_ledger(self.csr)
        calibration_register = load_calibration_register(self.csr)
        environment_register = load_environment_register(self.csr)

        from constitutional.jpss.transitions import priors_from_perception

        priors = priors_from_perception(perception)
        append_to_ledgers(
            prior_ledger,
            salience_ledger,
            calibration_register,
            environment_register,
            priors=priors,
            salience=salience,
            environment=environment,
            calibration=calibration,
        )
        save_prior_ledger(self.csr, prior_ledger)
        save_salience_ledger(self.csr, salience_ledger)
        save_calibration_register(self.csr, calibration_register)
        save_environment_register(self.csr, environment_register)

        from constitutional.eck1.registers import CalibrationEntry

        if (
            calibration_update.new_evidence_threshold != calibration.evidence_threshold
            or calibration_update.new_risk_tolerance != calibration.risk_tolerance
        ):
            calibration_register.append(
                CalibrationEntry(
                    timestamp=ts,
                    decision_id=decision.decision_id,
                    evidence_threshold=calibration_update.new_evidence_threshold,
                    risk_tolerance=calibration_update.new_risk_tolerance,
                    required_invariants=calibration.required_invariants,
                    required_purpose_links=calibration.required_purpose_links,
                    evidence_available=calibration.evidence_available,
                    evidence_missing=calibration.evidence_missing,
                    steward_id=calibration.steward_id,
                    notes=calibration_update.adjustment_rationale,
                )
            )
            save_calibration_register(self.csr, calibration_register)


def load_jpss_cycle(csr: ConstitutionalStateRuntime) -> JPSSCycleResult | None:
    try:
        doc = csr.get_domain_doc(JPSS_CYCLE_STATE_ID, JPSSCycleResult)
        assert isinstance(doc, JPSSCycleResult)
        return doc
    except KeyError:
        return None
