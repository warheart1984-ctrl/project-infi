"""Constitutional Drift Detector — boundary between adaptive and invariant."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.jpss.constitutional_ledgers import (
    load_elevation_review_ledger,
    load_retirement_review_ledger,
)
from constitutional.jpss.constitutional_register import load_constitutional_register
from constitutional.jpss.invariant_drift import detect_invariant_drift, load_invariant_drift_state
from constitutional.jpss.invariant_register import load_invariant_register
from constitutional.legitimacy.jpss_c_spec import (
    JPSS_C_DRIFT_INDEX_COMPONENTS,
    JPSS_C_DRIFT_MODES,
    JPSS_C_DRIFT_SIGNALS,
    JPSS_C_DRIFT_TYPES,
    JPSS_C_MIN_DRIFT_INDEX,
    ConstitutionalDriftMode,
    ConstitutionalDriftType,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

CONSTITUTIONAL_DRIFT_STATE_ID = "jpss_c_constitutional_drift__latest"

MAX_INVARIANTS_BEFORE_OVER_SACRALIZATION = 12
MIN_INVARIANTS_BEFORE_UNDER_SACRALIZATION = 2


class DriftSignalFinding(BaseModel):
    signal: str
    active: bool = False
    detail: str = ""


class ConstitutionalDriftFinding(BaseModel):
    drift_type: ConstitutionalDriftType
    active: bool = False
    severity: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = ""


class ConstitutionalDriftReport(BaseModel):
    drift_index: float = Field(default=1.0, ge=0.0, le=1.0)
    component_scores: dict[str, float] = Field(default_factory=dict)
    drift_modes: list[ConstitutionalDriftMode] = Field(default_factory=list)
    drift_types: list[ConstitutionalDriftFinding] = Field(default_factory=list)
    signals: list[DriftSignalFinding] = Field(default_factory=list)
    drift_detected: bool = False
    captured_at: datetime | None = None


def _count_invariants(register) -> int:
    latest = register.latest()
    if latest is None:
        return 0
    return (
        len(latest.purpose_clauses)
        + len(latest.core_values)
        + len(latest.commitments)
        + len(latest.identity_markers)
        + len(latest.sacred_constraints)
    )


def _boundary_stability(constitutional_entries: int, elevation_count: int, retirement_count: int) -> float:
    if constitutional_entries == 0 and elevation_count == 0:
        return 0.65
    recorded = min(1.0, constitutional_entries / 3)
    if elevation_count + retirement_count == 0:
        turnover_factor = 0.9
    else:
        turnover = retirement_count / (elevation_count + retirement_count)
        turnover_factor = 1.0 - abs(turnover - 0.3)
    return round(0.5 * recorded + 0.5 * turnover_factor, 4)


def detect_constitutional_drift(csr: ConstitutionalStateRuntime) -> ConstitutionalDriftReport:
    """Detect when the adaptive/invariant boundary is failing."""
    now = datetime.now(UTC).replace(microsecond=0)

    invariant_register = load_invariant_register(csr)
    constitutional_register = load_constitutional_register(csr)
    elevation_ledger = load_elevation_review_ledger(csr)
    retirement_ledger = load_retirement_review_ledger(csr)
    invariant_drift = load_invariant_drift_state(csr) or detect_invariant_drift(csr)

    invariant_count = _count_invariants(invariant_register)
    elevation_count = len(elevation_ledger.entries)
    retirement_count = len(retirement_ledger.entries)
    latest = invariant_register.latest()

    boundary_stability = _boundary_stability(
        len(constitutional_register.entries),
        elevation_count,
        retirement_count,
    )
    turnover_rate = retirement_count / max(1, elevation_count + 1)
    identity_coherence = 0.2 if invariant_drift.drift_detected else 1.0
    purpose_alignment = 0.3 if invariant_drift.failed_surfaces else 1.0
    sacred_integrity = 1.0
    if latest and latest.sacred_constraints:
        sacred_integrity = 0.0 if invariant_drift.sacred_violations else 1.0

    component_scores = {
        "boundary_stability": boundary_stability,
        "invariant_turnover_rate": round(min(1.0, turnover_rate * 2), 4),
        "identity_coherence": identity_coherence,
        "purpose_alignment": purpose_alignment,
        "sacred_constraint_integrity": sacred_integrity,
    }
    drift_index = round(sum(component_scores.values()) / len(JPSS_C_DRIFT_INDEX_COMPONENTS), 4)

    signals: list[DriftSignalFinding] = []
    too_many = invariant_count > MAX_INVARIANTS_BEFORE_OVER_SACRALIZATION
    too_few = invariant_count < MIN_INVARIANTS_BEFORE_UNDER_SACRALIZATION and latest is not None
    signals.append(
        DriftSignalFinding(
            signal="too_many_invariants",
            active=too_many,
            detail=f"{invariant_count} total invariant surfaces (max {MAX_INVARIANTS_BEFORE_OVER_SACRALIZATION}).",
        )
    )
    signals.append(
        DriftSignalFinding(
            signal="too_few_invariants",
            active=too_few,
            detail=f"{invariant_count} total invariant surfaces (min {MIN_INVARIANTS_BEFORE_UNDER_SACRALIZATION}).",
        )
    )
    contradict_purpose = invariant_drift.drift_detected and bool(invariant_drift.erosion_cases)
    signals.append(
        DriftSignalFinding(
            signal="invariants_contradicting_purpose",
            active=contradict_purpose,
            detail="Purpose erosion detected in invariant drift.",
        )
    )
    blocking_survival = too_many and turnover_rate < 0.1
    signals.append(
        DriftSignalFinding(
            signal="invariants_blocking_survival",
            active=blocking_survival,
            detail="High invariant count with no retirement turnover.",
        )
    )

    drift_modes: list[ConstitutionalDriftMode] = []
    if too_many:
        drift_modes.append("over_sacralization")
    if too_few:
        drift_modes.append("under_sacralization")
    if boundary_stability < 0.4:
        drift_modes.append("boundary_drift")
    if drift_index < 0.5:
        drift_modes.append("constitutional_drift")

    drift_types: list[ConstitutionalDriftFinding] = []
    for drift_type in JPSS_C_DRIFT_TYPES:
        active = False
        severity = 0.0
        description = ""
        if drift_type == "over_sacralization":
            active = too_many
            severity = min(1.0, invariant_count / MAX_INVARIANTS_BEFORE_OVER_SACRALIZATION - 1) if too_many else 0.0
            description = "Invariant inflation → ossification risk."
        elif drift_type == "under_sacralization":
            active = too_few
            severity = 0.8 if too_few else 0.0
            description = "Insufficient invariant anchoring → identity collapse risk."
        elif drift_type == "boundary_drift":
            active = boundary_stability < JPSS_C_MIN_DRIFT_INDEX
            severity = 1.0 - boundary_stability
            description = "Adaptive/invariant misclassification detected."
        elif drift_type == "identity_distortion":
            active = invariant_drift.drift_detected and bool(invariant_drift.identity_shifts)
            severity = invariant_drift.drift_index if active else 0.0
            description = "Identity markers shifting without constitutional review."
        elif drift_type == "purpose_erosion":
            active = contradict_purpose
            severity = invariant_drift.drift_index if active else 0.0
            description = "Purpose clauses eroding."
        elif drift_type == "commitment_inflation":
            active = latest is not None and len(latest.commitments) > 6
            severity = min(1.0, len(latest.commitments) / 10) if latest and active else 0.0
            description = "Commitment surface expanding without retirement."

        drift_types.append(
            ConstitutionalDriftFinding(
                drift_type=drift_type,
                active=active,
                severity=round(severity, 4),
                description=description,
            )
        )

    for signal_name in JPSS_C_DRIFT_SIGNALS:
        if any(s.signal == signal_name for s in signals):
            continue
        signals.append(DriftSignalFinding(signal=signal_name, active=False, detail="No signal detected."))

    severe_active = any(f.active and f.severity >= 0.5 for f in drift_types)
    report = ConstitutionalDriftReport(
        drift_index=drift_index,
        component_scores=component_scores,
        drift_modes=drift_modes,
        drift_types=drift_types,
        signals=signals,
        drift_detected=severe_active or drift_index < 0.5,
        captured_at=now,
    )
    csr.put_domain_doc(CONSTITUTIONAL_DRIFT_STATE_ID, "jpss_c_constitutional_drift", report)
    return report


def load_constitutional_drift_report(csr: ConstitutionalStateRuntime) -> ConstitutionalDriftReport | None:
    try:
        doc = csr.get_domain_doc(CONSTITUTIONAL_DRIFT_STATE_ID, ConstitutionalDriftReport)
        assert isinstance(doc, ConstitutionalDriftReport)
        return doc
    except KeyError:
        return None
