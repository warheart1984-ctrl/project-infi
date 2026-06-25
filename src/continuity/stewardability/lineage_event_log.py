"""JPSS Lineage Event Log — minimal atomic unit (v0.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

LINEAGE_EVENT_LOG_VERSION = "jpss_lineage_event_log.v0.1"

NoveltyLevel = Literal["ECHO", "VARIATION", "INDEPENDENT_EXPLANATION", "NEW_CONCEPT"]
OriginType = Literal["PROPAGATION", "CONVERGENCE", "NOISE", "DRIFT", "AMBIGUOUS"]
PredictiveValue = Literal["UNKNOWN", "WEAK", "MODERATE", "STRONG"]
StructuralPrimitive = Literal[
    "drift",
    "boundary",
    "calibration",
    "invariant",
    "threshold",
    "stewardship",
    "threshold_shift",
]

TRANSMISSION_AXIS = "transmission"
REALITY_AXIS = "reality"


class LineageActor(BaseModel):
    id: str
    domain: str
    exposed_to_jpss: bool


class LineageInsight(BaseModel):
    text: str
    lineage_compatible: bool
    novelty_level: NoveltyLevel
    structural_alignment: list[StructuralPrimitive] = Field(default_factory=list)


class OriginEvidence(BaseModel):
    no_exposure_confirmed: bool | None = None
    independent_derivation_plausible: bool | None = None
    exposure_confirmed: bool | None = None
    causal_influence_plausible: bool | None = None
    imitation_detected: bool | None = None
    identity_breaking_divergence: bool | None = None
    notes: str | None = None


class LineageOrigin(BaseModel):
    type: OriginType
    possible: list[OriginType] = Field(default_factory=list)
    evidence: OriginEvidence = Field(default_factory=OriginEvidence)


class LineagePropagation(BaseModel):
    trigger_concept: str | None = None
    bidirectional: bool = False


class RealityTracking(BaseModel):
    matches_real_system: bool | None = None
    predictive_value: PredictiveValue = "UNKNOWN"
    cross_domain_similarity: list[str] = Field(default_factory=list)


class LineageEvent(BaseModel):
    """Atomic lineage observation — input to disambiguation, DOV-T1, and growth curves."""

    event_id: str
    timestamp: datetime
    actor: LineageActor
    insight: LineageInsight
    origin: LineageOrigin
    propagation: LineagePropagation = Field(default_factory=LineagePropagation)
    reality_tracking: RealityTracking = Field(default_factory=RealityTracking)
    concept_resonance_id: str | None = None


class LineageEventLog(BaseModel):
    version: str = LINEAGE_EVENT_LOG_VERSION
    events: list[LineageEvent] = Field(default_factory=list)

    def append(self, event: LineageEvent) -> None:
        self.events.append(event)

    def disambiguated_events(self) -> list[LineageEvent]:
        return [event for event in self.events if event.origin.type != "AMBIGUOUS"]

    def propagation_events(self) -> list[LineageEvent]:
        return [event for event in self.events if event.origin.type == "PROPAGATION"]

    def convergence_events(self) -> list[LineageEvent]:
        return [event for event in self.events if event.origin.type == "CONVERGENCE"]

    def ambiguous_events(self) -> list[LineageEvent]:
        return [event for event in self.events if event.origin.type == "AMBIGUOUS"]


def new_lineage_event_id(prefix: str = "evt") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


def record_lineage_event(
    log: LineageEventLog,
    *,
    actor: LineageActor,
    insight: LineageInsight,
    origin: LineageOrigin,
    event_id: str | None = None,
    timestamp: datetime | None = None,
    concept_resonance_id: str | None = None,
) -> LineageEvent:
    event = LineageEvent(
        event_id=event_id or new_lineage_event_id(),
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0),
        actor=actor,
        insight=insight,
        origin=origin,
        concept_resonance_id=concept_resonance_id,
    )
    log.append(event)
    return event


def sue_reference_lineage_event() -> LineageEvent:
    """Sue — ambiguous concept resonance; convergence interpretation is stronger."""
    return LineageEvent(
        event_id="evt-sue-001",
        timestamp=datetime.now(UTC).replace(microsecond=0),
        actor=LineageActor(
            id="sue",
            domain="psychology",
            exposed_to_jpss=False,
        ),
        insight=LineageInsight(
            text="People can retain knowledge while their calibration drifts.",
            lineage_compatible=True,
            novelty_level="INDEPENDENT_EXPLANATION",
            structural_alignment=["calibration", "drift", "threshold_shift"],
        ),
        origin=LineageOrigin(
            type="AMBIGUOUS",
            possible=["PROPAGATION", "CONVERGENCE"],
            evidence=OriginEvidence(
                no_exposure_confirmed=True,
                independent_derivation_plausible=True,
                exposure_confirmed=False,
            ),
        ),
        propagation=LineagePropagation(trigger_concept=None, bidirectional=False),
        reality_tracking=RealityTracking(
            matches_real_system=True,
            predictive_value="UNKNOWN",
        ),
        concept_resonance_id="resonance-sue-001",
    )
