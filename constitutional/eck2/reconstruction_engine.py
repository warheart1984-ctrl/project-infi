"""ECK-2 Reconstruction Engine — ECK-R backward pipeline."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.eck1.models import EnvironmentState, PriorState, SignificanceState
from constitutional.eck1.registers import load_calibration_register, load_environment_register
from constitutional.eck2.models import (
    CalibrationReconstructionState,
    ContinuityUpdateState,
    ECK2ReconstructionResult,
    JudgmentReconstructionState,
    PerceptionReconstructionState,
    SalienceReconstructionState,
)
from constitutional.jpss.registers import (
    load_decision_register,
    load_outcome_register,
    load_perception_register,
    load_reflection_register,
)
from constitutional.priors.ledger import load_prior_ledger
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.ledger import load_salience_ledger


class ECK2ReconstructionEngine:
    """Reverse engine: Environment → … → Significance Reconstruction → Continuity Update."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def reconstruct(self, decision_id: str) -> ECK2ReconstructionResult:
        now = datetime.now(UTC).replace(microsecond=0)
        missing: list[str] = []
        remediation: list[str] = []

        env_register = load_environment_register(self.csr)
        env_entry = next(
            (entry for entry in reversed(env_register.entries) if entry.decision_id == decision_id),
            None,
        )
        environment: EnvironmentState | None = None
        if env_entry:
            environment = EnvironmentState(
                constraints_active=env_entry.constraints_active,
                incentives_present=env_entry.incentives_present,
                uncertainties_dominant=env_entry.uncertainties_dominant,
                environmental_factors=env_entry.environmental_factors,
                failure_modes_feared=env_entry.failure_modes_feared,
                decision_id=decision_id,
                steward_id=env_entry.steward_id,
                captured_at=env_entry.timestamp,
            )
        else:
            missing.append("environment")
            remediation.append("Preserve environment snapshot in environment register.")

        perception_register = load_perception_register(self.csr)
        perception_entry = perception_register.latest_for_decision(decision_id)
        perception: PerceptionReconstructionState | None = None
        perception_signals: list[str] = []
        if perception_entry:
            perception_signals = perception_entry.available_signals
            perception = PerceptionReconstructionState(
                available_signals=perception_entry.available_signals,
                missing_signals=perception_entry.missing_signals,
                intake_channels=perception_entry.intake_channels,
                decision_id=decision_id,
                steward_id=perception_entry.steward_id,
                captured_at=perception_entry.timestamp,
                reconstructable=True,
            )
        else:
            missing.append("perception")
            remediation.append("Write perception register entry at formation time.")

        salience_ledger = load_salience_ledger(self.csr)
        salience_entry = next(
            (entry for entry in reversed(salience_ledger.entries) if entry.decision_id == decision_id),
            None,
        )
        salience: SalienceReconstructionState | None = None
        if salience_entry:
            salience = SalienceReconstructionState(
                primary_signals=salience_entry.primary_signals,
                secondary_signals=salience_entry.secondary_signals,
                ignored_signals=salience_entry.ignored_signals,
                decision_id=decision_id,
                steward_id=salience_entry.steward_id,
                captured_at=salience_entry.timestamp,
                reconstructable=True,
            )
        else:
            missing.append("salience")
            remediation.append("Record salience ledger entry during JPSS-F.")

        calibration_register = load_calibration_register(self.csr)
        calibration_entry = calibration_register.latest_for_decision(decision_id)
        calibration: CalibrationReconstructionState | None = None
        if calibration_entry:
            calibration = CalibrationReconstructionState(
                evidence_threshold=calibration_entry.evidence_threshold,
                risk_tolerance=calibration_entry.risk_tolerance,
                required_invariants=calibration_entry.required_invariants,
                decision_id=decision_id,
                steward_id=calibration_entry.steward_id,
                captured_at=calibration_entry.timestamp,
                reconstructable=True,
            )
        else:
            missing.append("calibration")
            remediation.append("Persist calibration thresholds in calibration register.")

        prior_ledger = load_prior_ledger(self.csr)
        prior_entry = next(
            (entry for entry in reversed(prior_ledger.entries) if entry.decision_id == decision_id),
            None,
        )
        priors: PriorState | None = None
        if prior_entry:
            priors = PriorState(
                expected_signals=prior_entry.expected_signals,
                expected_risks=prior_entry.expected_risks,
                assumed_stabilities=prior_entry.assumed_stabilities,
                assumed_volatilities=prior_entry.assumed_volatilities,
                ignored_possibilities=prior_entry.ignored_possibilities,
                decision_id=decision_id,
                steward_id=prior_entry.steward_id,
                captured_at=prior_entry.timestamp,
            )
        else:
            missing.append("priors")
            remediation.append("Mirror perception into prior ledger at formation.")

        decision_register = load_decision_register(self.csr)
        decision_entry = decision_register.latest_for_decision(decision_id)
        judgment: JudgmentReconstructionState | None = None
        if decision_entry:
            judgment = JudgmentReconstructionState(
                decision_id=decision_id,
                outcome=decision_entry.outcome,
                rationale=decision_entry.rationale,
                applied_invariants=decision_entry.applied_invariants,
                steward_id=decision_entry.steward_id,
                captured_at=decision_entry.timestamp,
                reconstructable=True,
            )
        else:
            missing.append("judgment")
            remediation.append("Record decision in decision register.")

        outcome_register = load_outcome_register(self.csr)
        reflection_register = load_reflection_register(self.csr)
        if not outcome_register.latest_for_decision(decision_id):
            missing.append("outcome")
            remediation.append("Link outcome register to decision.")
        if not reflection_register.latest_for_decision(decision_id):
            missing.append("reflection")
            remediation.append("Complete reflection register after outcome.")

        significance: SignificanceState | None = None
        if judgment:
            significance = SignificanceState(
                artifact_id=decision_id,
                tier=2,
                rationale=judgment.rationale,
                lineage=[decision_id],
                decision_id=decision_id,
                steward_id=judgment.steward_id,
                captured_at=now,
            )

        reconstructable = len(missing) == 0
        continuity = ContinuityUpdateState(
            decision_id=decision_id,
            symmetry_index=1.0 if reconstructable else max(0.0, 1.0 - (len(missing) / 8)),
            reconstructable=reconstructable,
            remediation_hints=remediation,
            captured_at=now,
        )

        return ECK2ReconstructionResult(
            decision_id=decision_id,
            environment=environment,
            perception=perception,
            salience=salience,
            calibration=calibration,
            priors=priors,
            judgment=judgment,
            significance=significance,
            continuity=continuity,
            perception_available_signals=perception_signals,
            reconstructable=reconstructable,
            missing_layers=missing,
            captured_at=now,
        )
