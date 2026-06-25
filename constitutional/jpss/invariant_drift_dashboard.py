"""Invariant Drift Early-Warning Dashboard — weekly identity health check."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from enum import Enum
from typing import IO

from pydantic import BaseModel, Field

from constitutional.core.articles import ARTICLE_JPSS_I_REFERENCE, ECK2_MIN_INVARIANT_DRIFT_INDEX
from constitutional.core.models import StateObject
from constitutional.jpss.drift import detect_jpss_drift
from constitutional.jpss.invariant_drift import (
    InvariantDriftFailure,
    InvariantDriftState,
    detect_invariant_drift,
    load_invariant_drift_state,
)
from constitutional.jpss.invariant_register import InvariantRegister, load_invariant_register
from constitutional.jpss.runtime import load_jpss_cycle
from constitutional.runtime.runtime import ConstitutionalStateRuntime

INVARIANT_DRIFT_DASHBOARD_STATE_ID = "invariant_drift_dashboard__global"

GREEN_ZONE_MIN = 0.90
YELLOW_ZONE_MIN = ECK2_MIN_INVARIANT_DRIFT_INDEX


class InvariantDriftZone(str, Enum):
    GREEN = "Green Zone (Stable)"
    YELLOW = "Yellow Zone (Watch)"
    RED = "Red Zone (Critical)"


class PurposeStabilitySection(BaseModel):
    purpose_clauses_unchanged_pct: float = Field(ge=0.0, le=1.0)
    flagged_erosions: list[str] = Field(default_factory=list)
    reinterpretation_attempts: list[str] = Field(default_factory=list)


class CoreValueIntegritySection(BaseModel):
    value_drift_index: float = Field(ge=0.0, le=1.0)
    reinterpretation_alerts: list[str] = Field(default_factory=list)
    value_conflicts: list[str] = Field(default_factory=list)


class CommitmentStrengthSection(BaseModel):
    commitment_weakening_index: float = Field(ge=0.0, le=1.0)
    bypass_attempts: list[str] = Field(default_factory=list)
    enforcement_gaps: list[str] = Field(default_factory=list)


class IdentityCoherenceSection(BaseModel):
    identity_marker_drift_index: float = Field(ge=0.0, le=1.0)
    identity_shifts: list[str] = Field(default_factory=list)
    narrative_fragmentation: list[str] = Field(default_factory=list)


class SacredConstraintSection(BaseModel):
    violation_attempts: list[str] = Field(default_factory=list)
    near_misses: list[str] = Field(default_factory=list)
    bypass_pathways: list[str] = Field(default_factory=list)


class InvariantDriftDashboardState(BaseModel):
    state_id: str = INVARIANT_DRIFT_DASHBOARD_STATE_ID
    state_type: str = "invariant_drift_dashboard"
    snapshot_at: datetime
    version: int = Field(ge=1, default=1)

    drift_index: float = Field(ge=0.0, le=1.0)
    zone: InvariantDriftZone
    requires_intervention: bool = False

    purpose: PurposeStabilitySection
    core_values: CoreValueIntegritySection
    commitments: CommitmentStrengthSection
    identity: IdentityCoherenceSection
    sacred_constraints: SacredConstraintSection

    adaptive_drift_signals: list[str] = Field(default_factory=list)
    weekly_checklist: list[str] = Field(default_factory=list)
    failed_surfaces: list[InvariantDriftFailure] = Field(default_factory=list)


def classify_drift_zone(drift_index: float) -> InvariantDriftZone:
    if drift_index >= GREEN_ZONE_MIN:
        return InvariantDriftZone.GREEN
    if drift_index >= YELLOW_ZONE_MIN:
        return InvariantDriftZone.YELLOW
    return InvariantDriftZone.RED


def _stability_pct(historical: set[str], current: set[str]) -> float:
    if not historical:
        return 1.0
    preserved = len(historical & current)
    return preserved / len(historical)


def _section_index(historical_count: int, loss_count: int) -> float:
    if historical_count == 0:
        return 1.0
    return max(0.0, 1.0 - (loss_count / historical_count))


def build_weekly_checklist(
    *,
    zone: InvariantDriftZone,
    drift: InvariantDriftState,
    adaptive_signals: list[str],
) -> list[str]:
    items = [
        "Review invariant drift indices",
        "Review reinterpretation logs",
        "Review commitment bypass attempts",
        "Review identity marker changes",
        "Review sacred constraint tension points",
        "Cross-check with adaptive drift signals",
        "Decide whether identity or calibration must be adjusted",
    ]
    if zone == InvariantDriftZone.RED:
        items.insert(0, "IMMEDIATE: Red Zone — steward intervention required")
    if adaptive_signals:
        items.append(f"Active adaptive drift: {', '.join(adaptive_signals)}")
    if drift.failed_surfaces:
        codes = ", ".join(surface.value for surface in drift.failed_surfaces)
        items.append(f"Failed invariant surfaces: {codes}")
    return items


class InvariantDriftDashboardRuntime:
    """Compute and persist the invariant drift early-warning dashboard."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def _historical_sets(self, register: InvariantRegister) -> dict[str, set[str]]:
        purpose: set[str] = set()
        values: set[str] = set()
        commitments: set[str] = set()
        identity: set[str] = set()
        sacred: set[str] = set()
        for entry in register.entries:
            purpose.update(entry.purpose_clauses)
            values.update(entry.core_values)
            commitments.update(entry.commitments)
            identity.update(entry.identity_markers)
            sacred.update(entry.sacred_constraints)
        return {
            "purpose": purpose,
            "values": values,
            "commitments": commitments,
            "identity": identity,
            "sacred": sacred,
        }

    def update_snapshot(
        self,
        snapshot_at: datetime | None = None,
    ) -> InvariantDriftDashboardState:
        now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        register = load_invariant_register(self.csr)
        drift = load_invariant_drift_state(self.csr) or detect_invariant_drift(self.csr)
        historical = self._historical_sets(register)
        current = register.latest()

        current_purpose = set(current.purpose_clauses) if current else set()
        current_values = set(current.core_values) if current else set()
        current_commitments = set(current.commitments) if current else set()
        current_identity = set(current.identity_markers) if current else set()
        current_sacred = set(current.sacred_constraints) if current else set()

        purpose_section = PurposeStabilitySection(
            purpose_clauses_unchanged_pct=_stability_pct(historical["purpose"], current_purpose),
            flagged_erosions=list(drift.erosion_cases),
            reinterpretation_attempts=list(drift.reinterpretations),
        )
        values_section = CoreValueIntegritySection(
            value_drift_index=_section_index(len(historical["values"]), len(drift.reinterpretations)),
            reinterpretation_alerts=list(drift.reinterpretations),
            value_conflicts=[
                value for value in drift.reinterpretations if value in historical["values"]
            ],
        )
        commitments_section = CommitmentStrengthSection(
            commitment_weakening_index=_section_index(
                len(historical["commitments"]), len(drift.weakenings)
            ),
            bypass_attempts=list(drift.weakenings),
            enforcement_gaps=list(drift.weakenings),
        )
        identity_section = IdentityCoherenceSection(
            identity_marker_drift_index=_section_index(
                len(historical["identity"]), len(drift.identity_shifts)
            ),
            identity_shifts=list(drift.identity_shifts),
            narrative_fragmentation=list(drift.identity_shifts),
        )
        sacred_section = SacredConstraintSection(
            violation_attempts=list(drift.sacred_violations),
            near_misses=list(drift.sacred_violations),
            bypass_pathways=list(drift.sacred_violations),
        )

        cycle = load_jpss_cycle(self.csr)
        jpss_drift = detect_jpss_drift(
            self.csr,
            decision_id=cycle.decision_id if cycle else None,
            cycle=cycle,
        )
        adaptive_signals = [
            finding.drift_class.replace("_", " ")
            for finding in jpss_drift.findings
            if finding.detected
        ]

        zone = classify_drift_zone(drift.drift_index)
        checklist = build_weekly_checklist(
            zone=zone,
            drift=drift,
            adaptive_signals=adaptive_signals,
        )

        state = InvariantDriftDashboardState(
            snapshot_at=now,
            drift_index=drift.drift_index,
            zone=zone,
            requires_intervention=zone == InvariantDriftZone.RED,
            purpose=purpose_section,
            core_values=values_section,
            commitments=commitments_section,
            identity=identity_section,
            sacred_constraints=sacred_section,
            adaptive_drift_signals=adaptive_signals,
            weekly_checklist=checklist,
            failed_surfaces=list(drift.failed_surfaces),
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=INVARIANT_DRIFT_DASHBOARD_STATE_ID,
                state_type="invariant_drift_dashboard",
                current_state=zone.value,
            )
        )
        self.csr.put_domain_doc(INVARIANT_DRIFT_DASHBOARD_STATE_ID, "invariant_drift_dashboard", state)
        return state


def load_invariant_drift_dashboard(csr: ConstitutionalStateRuntime) -> InvariantDriftDashboardState | None:
    try:
        doc = csr.get_domain_doc(INVARIANT_DRIFT_DASHBOARD_STATE_ID, InvariantDriftDashboardState)
        assert isinstance(doc, InvariantDriftDashboardState)
        return doc
    except KeyError:
        return None


def format_invariant_drift_panel(state: InvariantDriftDashboardState) -> str:
    lines: list[str] = [
        "",
        f"=== INVARIANT DRIFT EARLY-WARNING ({ARTICLE_JPSS_I_REFERENCE}) ===",
        f"Snapshot: {state.snapshot_at.isoformat()}  v{state.version}",
        f"Drift Index: {state.drift_index:0.2f}  |  {state.zone.value}",
        "----------------------------------------",
        "",
        "A. Purpose Stability",
        f"  Unchanged: {state.purpose.purpose_clauses_unchanged_pct:0.0%}",
        f"  Erosions: {state.purpose.flagged_erosions or 'none'}",
        "",
        "B. Core Value Integrity",
        f"  Value drift index: {state.core_values.value_drift_index:0.2f}",
        f"  Reinterpretation alerts: {state.core_values.reinterpretation_alerts or 'none'}",
        "",
        "C. Commitment Strength",
        f"  Weakening index: {state.commitments.commitment_weakening_index:0.2f}",
        f"  Bypass attempts: {state.commitments.bypass_attempts or 'none'}",
        "",
        "D. Identity Coherence",
        f"  Marker drift index: {state.identity.identity_marker_drift_index:0.2f}",
        f"  Identity shifts: {state.identity.identity_shifts or 'none'}",
        "",
        "E. Sacred Constraint Protection",
        f"  Violation attempts: {state.sacred_constraints.violation_attempts or 'none'}",
        "",
        "Adaptive cross-check:",
        f"  {state.adaptive_drift_signals or 'no active adaptive drift'}",
        "",
        "Weekly steward checklist:",
    ]
    for item in state.weekly_checklist:
        lines.append(f"  [ ] {item}")

    if state.requires_intervention:
        lines.append("")
        lines.append("*** RED ZONE — immediate steward intervention required ***")

    lines.extend(["========================================", ""])
    return "\n".join(lines)


def render_invariant_drift_panel(
    state: InvariantDriftDashboardState,
    *,
    stream: IO[str] | None = None,
) -> str:
    text = format_invariant_drift_panel(state)
    out = stream if stream is not None else sys.stdout
    out.write(text)
    if stream is None:
        out.flush()
    return text
