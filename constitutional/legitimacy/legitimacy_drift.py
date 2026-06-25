"""Legitimacy Drift Model v1.0 — Protocol §4 (seven drift classes)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from constitutional.legitimacy.jpss_c_exam import load_jpss_c_exam_result
from constitutional.legitimacy.legitimacy_criterion import load_legitimacy_criterion_result
from constitutional.legitimacy.legitimacy_register import load_legitimacy_register
from constitutional.legitimacy.spec import (
    MAX_PLURALITY_BEFORE_UNDER_CONCENTRATION,
    MIN_LEGITIMACY_INDEX,
    MIN_PLURALITY_FOR_INVARIANT_ALTERATION,
)
from constitutional.jpss.stewardship_balancing_test import load_stewardship_balancing_result
from constitutional.runtime.runtime import ConstitutionalStateRuntime

LEGITIMACY_DRIFT_STATE_ID = "legitimacy_drift__latest"
_DRIFT_SURFACE_COUNT = 7


class LegitimacyDriftFailure(str, Enum):
    OVER_CONCENTRATION = "L-D1 OverConcentrationDrift"
    UNDER_CONCENTRATION = "L-D2 UnderConcentrationDrift"
    COMPETENCE_DRIFT = "L-D3 CompetenceDrift"
    CULTURAL_CAPTURE = "L-D4 CulturalCaptureDrift"
    FOUNDER_CAPTURE = "L-D5 FounderCaptureDrift"
    STEWARD_CAPTURE = "L-D6 StewardCaptureDrift"
    BOUNDARY_DRIFT = "L-D7 BoundaryDrift"


class LegitimacyDriftState(BaseModel):
    snapshot_at: datetime
    version: int = 1
    drift_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[LegitimacyDriftFailure] = Field(default_factory=list)
    over_concentration_signals: list[str] = Field(default_factory=list)
    under_concentration_signals: list[str] = Field(default_factory=list)
    competence_signals: list[str] = Field(default_factory=list)
    capture_signals: list[str] = Field(default_factory=list)
    boundary_signals: list[str] = Field(default_factory=list)

    # Legacy field aliases for panels
    @property
    def salience_gaps(self) -> list[str]:
        return self.competence_signals

    @property
    def calibration_notes(self) -> list[str]:
        return self.competence_signals


class LegitimacyDriftDetector:
    """Detect drift in who qualifies as a legitimate steward (Protocol §4)."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def run(self) -> LegitimacyDriftState:
        now = datetime.now(UTC).replace(microsecond=0)
        register = load_legitimacy_register(self.csr)
        failures: list[LegitimacyDriftFailure] = []
        over_signals: list[str] = []
        under_signals: list[str] = []
        competence: list[str] = []
        capture: list[str] = []
        boundary: list[str] = []

        active = register.active_stewards()
        active_count = len(active)

        if active_count < register.minimum_plurality:
            failures.append(LegitimacyDriftFailure.OVER_CONCENTRATION)
            over_signals.append(
                f"Only {active_count} certified stewards (min plurality: {register.minimum_plurality})."
            )

        if active_count > MAX_PLURALITY_BEFORE_UNDER_CONCENTRATION:
            failures.append(LegitimacyDriftFailure.UNDER_CONCENTRATION)
            under_signals.append(
                f"{active_count} certified stewards exceeds max {MAX_PLURALITY_BEFORE_UNDER_CONCENTRATION}."
            )

        if active:
            avg_index = sum(entry.legitimacy_index for entry in active) / active_count
            if avg_index < MIN_LEGITIMACY_INDEX:
                failures.append(LegitimacyDriftFailure.COMPETENCE_DRIFT)
                competence.append(
                    f"Average legitimacy index {avg_index:.2f} < {MIN_LEGITIMACY_INDEX:.2f}."
                )

            for entry in active:
                criterion = load_legitimacy_criterion_result(self.csr, entry.steward_id)
                if criterion is None or not criterion.passed:
                    failures.append(LegitimacyDriftFailure.COMPETENCE_DRIFT)
                    competence.append(f"{entry.steward_id} failed reconstruction criterion.")
                    break

            founder_only = all(
                entry.certified_by == ["founder"] or entry.certified_by == ["steward-founder"]
                for entry in active
            )
            if founder_only:
                failures.append(LegitimacyDriftFailure.FOUNDER_CAPTURE)
                capture.append("All stewards certified solely by founder cohort.")

            certifier_sets = [tuple(entry.certified_by) for entry in active]
            if len(active) >= 2 and len(set(certifier_sets)) == 1 and certifier_sets[0]:
                single_gatekeeper = len(certifier_sets[0]) == 1
                if single_gatekeeper:
                    failures.append(LegitimacyDriftFailure.STEWARD_CAPTURE)
                    capture.append(f"Single steward gatekeeps all certifications: {certifier_sets[0][0]}.")

            without_receipts = [entry.steward_id for entry in active if not entry.receipt_refs]
            if without_receipts:
                failures.append(LegitimacyDriftFailure.CULTURAL_CAPTURE)
                capture.append(f"Certified without receipt refs (implicit trust): {without_receipts}")

            jpss_c = load_jpss_c_exam_result(self.csr)
            balancing = load_stewardship_balancing_result(self.csr)
            if jpss_c is None or not jpss_c.passed or balancing is None or not balancing.passed:
                failures.append(LegitimacyDriftFailure.BOUNDARY_DRIFT)
                boundary.append("JPSS-C or JPSS-I balancing competence not demonstrated system-wide.")

        revoked = [entry for entry in register.entries if not entry.active]
        if revoked and not active:
            failures.append(LegitimacyDriftFailure.COMPETENCE_DRIFT)
            competence.append("No active certified stewards — bar may be ossified.")

        unique_failures = list(dict.fromkeys(failures))
        drift_index = 1.0 - (len(unique_failures) / _DRIFT_SURFACE_COUNT)

        return LegitimacyDriftState(
            snapshot_at=now,
            drift_index=drift_index,
            failed_surfaces=unique_failures,
            over_concentration_signals=over_signals,
            under_concentration_signals=under_signals,
            competence_signals=competence,
            capture_signals=capture,
            boundary_signals=boundary,
        )


def detect_legitimacy_drift(csr: ConstitutionalStateRuntime) -> LegitimacyDriftState:
    state = LegitimacyDriftDetector(csr).run()
    csr.put_domain_doc(LEGITIMACY_DRIFT_STATE_ID, "legitimacy_drift_state", state)
    return state


def load_legitimacy_drift_state(csr: ConstitutionalStateRuntime) -> LegitimacyDriftState | None:
    try:
        doc = csr.get_domain_doc(LEGITIMACY_DRIFT_STATE_ID, LegitimacyDriftState)
        assert isinstance(doc, LegitimacyDriftState)
        return doc
    except KeyError:
        return None
