"""ECK-1 canonical transitions — Priors → Salience → … → Continuity."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from constitutional.eck1.models import (
    CalibrationState,
    EnvironmentState,
    JudgmentState,
    PriorState,
    SalienceState,
    SignificanceState,
)
from constitutional.eck1.registers import (
    CalibrationEntry,
    CalibrationRegister,
    EnvironmentEntry,
    EnvironmentRegister,
)
from constitutional.priors.ledger import PriorEntry, StewardshipPriorLedger
from constitutional.salience.ledger import SalienceEntry, SalienceLedger


def perception_transition(
    priors: PriorState,
    environment: EnvironmentState,
    *,
    decision_id: str | None = None,
    steward_id: str = "steward",
    captured_at: datetime | None = None,
) -> SalienceState:
    """Priors × Environment → Salience."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    primary = list(dict.fromkeys(priors.expected_signals + environment.failure_modes_feared))
    secondary = list(dict.fromkeys(priors.expected_risks + environment.uncertainties_dominant))
    ignored = list(priors.ignored_possibilities)
    return SalienceState(
        primary_signals=primary,
        secondary_signals=secondary,
        ignored_signals=ignored,
        risk_salience=priors.expected_risks,
        deprioritized_risks=priors.ignored_possibilities,
        decision_id=decision_id or environment.decision_id,
        steward_id=steward_id,
        captured_at=now,
    )


def calibration_transition(
    salience: SalienceState,
    environment: EnvironmentState,
    *,
    decision_id: str | None = None,
    steward_id: str = "steward",
    captured_at: datetime | None = None,
) -> CalibrationState:
    """Salience × Environment → Calibration."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    pressure = len(salience.primary_signals) + len(environment.constraints_active)
    evidence_threshold = min(0.95, 0.5 + (pressure * 0.02))
    risk_tolerance = max(0.1, 0.6 - (len(salience.risk_salience) * 0.05))
    return CalibrationState(
        evidence_threshold=evidence_threshold,
        risk_tolerance=risk_tolerance,
        required_invariants=[],
        required_purpose_links=[],
        evidence_available=salience.primary_signals,
        evidence_missing=salience.ignored_signals,
        decision_id=decision_id or salience.decision_id,
        steward_id=steward_id,
        captured_at=now,
    )


def judgment_transition(
    calibration: CalibrationState,
    *,
    decision_id: str,
    outcome: str,
    rationale: str,
    applied_invariants: list[str] | None = None,
    applied_purpose_clauses: list[str] | None = None,
    steward_id: str = "steward",
    captured_at: datetime | None = None,
) -> JudgmentState:
    """Calibration → Judgment."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    return JudgmentState(
        decision_id=decision_id,
        outcome=outcome,
        rationale=rationale,
        applied_invariants=applied_invariants or calibration.required_invariants,
        applied_purpose_clauses=applied_purpose_clauses or calibration.required_purpose_links,
        steward_id=steward_id,
        captured_at=now,
    )


def significance_transition(
    judgment: JudgmentState,
    *,
    artifact_id: str,
    tier: int,
    rationale: str,
    lineage: list[str] | None = None,
    captured_at: datetime | None = None,
) -> SignificanceState:
    """Judgment → Significance."""
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    return SignificanceState(
        artifact_id=artifact_id,
        tier=tier,
        rationale=rationale,
        lineage=lineage or [judgment.decision_id],
        decision_id=judgment.decision_id,
        steward_id=judgment.steward_id,
        captured_at=now,
    )


def prior_state_from_inputs(steward_inputs: dict[str, Any], *, captured_at: datetime | None = None) -> PriorState:
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    return PriorState(
        expected_signals=steward_inputs.get("expected_signals", []),
        expected_risks=steward_inputs.get("expected_risks", []),
        assumed_stabilities=steward_inputs.get("assumed_stabilities", []),
        assumed_volatilities=steward_inputs.get("assumed_volatilities", []),
        ignored_possibilities=steward_inputs.get("ignored_possibilities", []),
        decision_id=steward_inputs.get("decision_id"),
        steward_id=steward_inputs.get("steward_id", "steward"),
        captured_at=now,
    )


def environment_state_from_inputs(
    steward_inputs: dict[str, Any],
    *,
    captured_at: datetime | None = None,
) -> EnvironmentState:
    now = captured_at or datetime.now(UTC).replace(microsecond=0)
    return EnvironmentState(
        constraints_active=steward_inputs.get("constraints_active", []),
        incentives_present=steward_inputs.get("incentives_present", []),
        uncertainties_dominant=steward_inputs.get("uncertainties_dominant", []),
        environmental_factors=steward_inputs.get("environmental_factors", []),
        failure_modes_feared=steward_inputs.get("failure_modes_feared", []),
        decision_id=steward_inputs.get("decision_id"),
        steward_id=steward_inputs.get("steward_id", "steward"),
        captured_at=now,
    )


def append_to_ledgers(
    prior_ledger: StewardshipPriorLedger,
    salience_ledger: SalienceLedger,
    calibration_register: CalibrationRegister,
    environment_register: EnvironmentRegister,
    *,
    priors: PriorState,
    salience: SalienceState,
    environment: EnvironmentState,
    calibration: CalibrationState,
) -> None:
    """Persist epistemic states to canonical registers."""
    ts = priors.captured_at or datetime.now(UTC).replace(microsecond=0)
    decision_id = priors.decision_id or "unknown"

    prior_ledger.append(
        PriorEntry(
            timestamp=ts,
            decision_id=decision_id,
            expected_signals=priors.expected_signals,
            expected_risks=priors.expected_risks,
            assumed_stabilities=priors.assumed_stabilities,
            assumed_volatilities=priors.assumed_volatilities,
            ignored_possibilities=priors.ignored_possibilities,
            steward_id=priors.steward_id,
        )
    )
    salience_ledger.append(
        SalienceEntry(
            timestamp=ts,
            decision_id=decision_id,
            primary_signals=salience.primary_signals,
            secondary_signals=salience.secondary_signals,
            ignored_signals=salience.ignored_signals,
            risk_salience=salience.risk_salience,
            deprioritized_risks=salience.deprioritized_risks,
            steward_id=salience.steward_id,
        )
    )
    calibration_register.append(
        CalibrationEntry(
            timestamp=ts,
            decision_id=decision_id,
            evidence_threshold=calibration.evidence_threshold,
            risk_tolerance=calibration.risk_tolerance,
            required_invariants=calibration.required_invariants,
            required_purpose_links=calibration.required_purpose_links,
            evidence_available=calibration.evidence_available,
            evidence_missing=calibration.evidence_missing,
            steward_id=calibration.steward_id,
        )
    )
    environment_register.append(
        EnvironmentEntry(
            timestamp=ts,
            decision_id=decision_id,
            constraints_active=environment.constraints_active,
            incentives_present=environment.incentives_present,
            uncertainties_dominant=environment.uncertainties_dominant,
            environmental_factors=environment.environmental_factors,
            failure_modes_feared=environment.failure_modes_feared,
            steward_id=environment.steward_id,
        )
    )
