"""Bridge drift failures into the ECK-1 failure register."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.eck1.registers import FailureEntry, FailureRegister, load_failure_register, save_failure_register
from constitutional.priors.drift_detector import PriorDriftFailure, PriorDriftState
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.continuity_runtime import SalienceFailure, SalienceContinuityState
from constitutional.salience.perceptual_drift import PerceptualDriftFailure, PerceptualDriftState


def _failure_class_for_prior(failure: PriorDriftFailure) -> str:
    return failure.value


def _failure_class_for_perceptual(failure: PerceptualDriftFailure) -> str:
    return failure.value


def _failure_class_for_salience(failure: SalienceFailure) -> str:
    return failure.value


def record_epistemic_failures(
    csr: ConstitutionalStateRuntime,
    *,
    prior_drift_state: PriorDriftState | None = None,
    perceptual_drift_state: PerceptualDriftState | None = None,
    salience_continuity_state: SalienceContinuityState | None = None,
    steward_id: str = "steward",
) -> FailureRegister:
    """Append unresolved drift/continuity failures to the failure register."""
    register = load_failure_register(csr)
    now = datetime.now(UTC).replace(microsecond=0)
    existing = {(entry.failure_class, entry.layer) for entry in register.entries if not entry.resolved}

    if prior_drift_state:
        for failure in prior_drift_state.failed_surfaces:
            key = (_failure_class_for_prior(failure), "prior")
            if key not in existing:
                register.append(
                    FailureEntry(
                        timestamp=now,
                        failure_class=_failure_class_for_prior(failure),
                        layer="prior",
                        description="; ".join(prior_drift_state.drift_cases or prior_drift_state.blindspots or []),
                        steward_id=steward_id,
                    )
                )
                existing.add(key)

    if perceptual_drift_state:
        for failure in perceptual_drift_state.failed_surfaces:
            key = (_failure_class_for_perceptual(failure), "salience")
            if key not in existing:
                register.append(
                    FailureEntry(
                        timestamp=now,
                        failure_class=_failure_class_for_perceptual(failure),
                        layer="salience",
                        description="; ".join(
                            perceptual_drift_state.drift_cases
                            or perceptual_drift_state.blindspots
                            or []
                        ),
                        steward_id=steward_id,
                    )
                )
                existing.add(key)

    if salience_continuity_state:
        for failure in salience_continuity_state.failed_surfaces:
            key = (_failure_class_for_salience(failure), "salience")
            if key not in existing:
                register.append(
                    FailureEntry(
                        timestamp=now,
                        failure_class=_failure_class_for_salience(failure),
                        layer="salience",
                        description="; ".join(salience_continuity_state.missing_salience_entries or []),
                        steward_id=steward_id,
                    )
                )
                existing.add(key)

    save_failure_register(csr, register)
    return register


def historical_failure_classes_for_layer(register: FailureRegister, layer: str) -> set[str]:
    return {entry.failure_class for entry in register.entries if entry.layer == layer}


def feared_failures_from_register(register: FailureRegister) -> list[str]:
    """Failure classes that historically shaped steward priors."""
    return sorted({entry.failure_class for entry in register.entries})
