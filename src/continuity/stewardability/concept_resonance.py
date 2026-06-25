"""Concept Resonance — ambiguous diagnostic at the propagation/convergence fork."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.continuity.stewardability.lineage_event_log import LineageEventLog

CONCEPT_RESONANCE_DEFINITION = (
    "A lineage-compatible insight arising after limited concept exposure — "
    "ambiguous evidence that increases probability on both propagation "
    "(lineage vitality) and convergence (reality-tracking) axes."
)

CONCEPT_RESONANCE_AMBIGUITY_NOTE = (
    "Concept resonance is the input; propagation or convergence is the classification."
)

PROPAGATION_MODE_TRANSMISSION = "transmission"
PROPAGATION_MODE_PROPAGATION = "propagation"

DevelopmentalStage = Literal[
    "concept_resonance",
    "reconstruction",
    "application",
    "critique",
    "extension",
    "lineage_propagation",
    "steward_emergence",
    "stewardability",
]

DEVELOPMENTAL_PROGRESSION: tuple[tuple[DevelopmentalStage, str], ...] = (
    (
        "concept_resonance",
        "Ambiguous fork — propagation and convergence both plausible until disambiguated.",
    ),
    ("reconstruction", "Person rebuilds the framework from artifacts."),
    ("application", "Person uses the framework to analyze new systems."),
    ("critique", "Person identifies weaknesses or blind spots."),
    ("extension", "Person generates new concepts within the framework."),
    ("lineage_propagation", "Concept leaves founders, enters another mind, returns improved."),
    ("steward_emergence", "Person can govern the framework's evolution."),
    ("stewardability", "Lineage produces stewards without founders."),
)

STAGES_NOT_RESONANCE: frozenset[str] = frozenset(
    {
        "memorization",
        "reconstruction",
        "application",
        "critique",
        "extension",
        "stewardship",
    }
)

CRT3_MIN_CONTRIBUTORS = 3
CRT3_MIN_CONTEXTS = 2
CRT3_MIN_INSIGHTS_PER_CONTRIBUTOR = 1


class ConceptExposure(BaseModel):
    """Isolated idea encountered — not the full framework."""

    concept_id: str
    description: str
    jpss_adjacent: bool = True


class ConceptResonanceInsight(BaseModel):
    """Independent insight generated from a single concept encounter."""

    text: str
    extends_trigger: bool = False
    adds_explanatory_power: bool = False
    lineage_compatible: bool = False
    uses_jpss_vocabulary: bool = False


class ConceptResonanceEvent(BaseModel):
    """Recorded concept-resonance observation (e.g. Sue's contribution)."""

    id: str
    contributor_id: str
    recorded_at: datetime
    context_domain: str
    exposure: ConceptExposure
    insight: ConceptResonanceInsight
    trained_on_jpss: bool = False
    coached: bool = False
    framework_exposed: bool = False
    imitation_flag: bool = False
    notes: str | None = None


class ConceptResonanceRegister(BaseModel):
    """Ledger of concept-resonance events — spore stage of a living tradition."""

    events: list[ConceptResonanceEvent] = Field(default_factory=list)

    def append(self, event: ConceptResonanceEvent) -> None:
        self.events.append(event)

    def valid_resonance_events(self) -> list[ConceptResonanceEvent]:
        return [event for event in self.events if validate_concept_resonance_event(event).valid]


class ResonanceValidation(BaseModel):
    valid: bool
    blockers: list[str] = Field(default_factory=list)


class CRT3Assessment(BaseModel):
    """Concept Resonance Threshold — volume of ambiguous resonance events (not confirmed propagation)."""

    threshold_met: bool
    contributor_count: int
    context_count: int
    valid_event_count: int
    required_contributors: int = CRT3_MIN_CONTRIBUTORS
    required_contexts: int = CRT3_MIN_CONTEXTS
    propagation_mode: Literal["transmission", "propagation"] = PROPAGATION_MODE_TRANSMISSION
    contributors_remaining: int = 0
    contexts_remaining: int = 0
    blockers: list[str] = Field(default_factory=list)


def new_resonance_event_id() -> str:
    return f"resonance-{uuid4().hex[:12]}"


def validate_concept_resonance_event(event: ConceptResonanceEvent) -> ResonanceValidation:
    """Check whether an event qualifies as genuine concept resonance (not imitation/training)."""
    blockers: list[str] = []

    if event.trained_on_jpss:
        blockers.append("Contributor was trained on JPSS — not concept resonance.")
    if event.coached:
        blockers.append("Contributor was coached — not independent generation.")
    if event.framework_exposed:
        blockers.append("Full framework exposure invalidates isolated-concept criterion.")
    if event.imitation_flag:
        blockers.append("Insight flagged as imitation (paraphrase/echo/regurgitation).")
    if event.insight.uses_jpss_vocabulary:
        blockers.append("Insight uses JPSS vocabulary — suggests framework transfer, not concept transfer.")
    if not event.insight.lineage_compatible:
        blockers.append("Insight is not lineage-compatible.")
    if not event.insight.extends_trigger:
        blockers.append("Insight does not extend the triggering concept.")
    if not event.insight.adds_explanatory_power:
        blockers.append("Insight does not add explanatory power.")
    if not event.insight.text.strip():
        blockers.append("Insight text is empty.")

    return ResonanceValidation(valid=not blockers, blockers=blockers)


def infer_structural_alignment(text: str) -> list[str]:
    """Infer JPSS structural primitives from insight text (caller narrows to StructuralPrimitive)."""
    lowered = text.lower()
    tags: list[str] = []
    for keyword in (
        "drift",
        "boundary",
        "calibration",
        "invariant",
        "threshold",
        "stewardship",
    ):
        if keyword in lowered:
            tags.append(keyword)
    if "drift" in lowered and "calibration" in lowered:
        tags.append("threshold_shift")
    return tags


def infer_novelty_level(event: ConceptResonanceEvent) -> str:
    if event.imitation_flag:
        return "ECHO"
    if event.insight.adds_explanatory_power and event.insight.extends_trigger:
        return "INDEPENDENT_EXPLANATION"
    if event.insight.extends_trigger:
        return "VARIATION"
    return "NEW_CONCEPT"


def concept_resonance_to_lineage_event(event: ConceptResonanceEvent) -> "LineageEvent":
    """Map concept resonance to lineage log v0.1 with origin.type AMBIGUOUS."""
    from src.continuity.stewardability.lineage_event_log import (
        LineageActor,
        LineageEvent,
        LineageInsight,
        LineageOrigin,
        LineagePropagation,
        NoveltyLevel,
        OriginEvidence,
        RealityTracking,
        new_lineage_event_id,
    )

    exposed = event.trained_on_jpss or event.framework_exposed
    alignment = infer_structural_alignment(event.insight.text)
    novelty: NoveltyLevel = infer_novelty_level(event)  # type: ignore[assignment]

    return LineageEvent(
        event_id=new_lineage_event_id(),
        timestamp=event.recorded_at,
        actor=LineageActor(
            id=event.contributor_id,
            domain=event.context_domain,
            exposed_to_jpss=exposed,
        ),
        insight=LineageInsight(
            text=event.insight.text,
            lineage_compatible=event.insight.lineage_compatible,
            novelty_level=novelty,
            structural_alignment=alignment,
        ),
        origin=LineageOrigin(
            type="AMBIGUOUS",
            possible=["PROPAGATION", "CONVERGENCE"],
            evidence=OriginEvidence(
                no_exposure_confirmed=not exposed,
                independent_derivation_plausible=(
                    event.insight.adds_explanatory_power and not event.imitation_flag
                ),
                exposure_confirmed=event.exposure.jpss_adjacent and not exposed,
                causal_influence_plausible=event.exposure.jpss_adjacent and not exposed,
                imitation_detected=event.imitation_flag,
            ),
        ),
        propagation=LineagePropagation(
            trigger_concept=event.exposure.concept_id if event.exposure.jpss_adjacent else None,
            bidirectional=False,
        ),
        reality_tracking=RealityTracking(
            matches_real_system=event.insight.lineage_compatible,
        ),
        concept_resonance_id=event.id,
    )


def record_concept_resonance(
    register: ConceptResonanceRegister,
    *,
    contributor_id: str,
    context_domain: str,
    exposure: ConceptExposure,
    insight: ConceptResonanceInsight,
    trained_on_jpss: bool = False,
    coached: bool = False,
    framework_exposed: bool = False,
    imitation_flag: bool = False,
    notes: str | None = None,
    recorded_at: datetime | None = None,
    lineage_log: "LineageEventLog | None" = None,
) -> ConceptResonanceEvent:
    event = ConceptResonanceEvent(
        id=new_resonance_event_id(),
        contributor_id=contributor_id,
        recorded_at=recorded_at or datetime.now(UTC).replace(microsecond=0),
        context_domain=context_domain,
        exposure=exposure,
        insight=insight,
        trained_on_jpss=trained_on_jpss,
        coached=coached,
        framework_exposed=framework_exposed,
        imitation_flag=imitation_flag,
        notes=notes,
    )
    register.append(event)
    if lineage_log is not None:
        lineage_log.append(concept_resonance_to_lineage_event(event))
    return event


def assess_crt3(register: ConceptResonanceRegister) -> CRT3Assessment:
    """
    CRT-3: ambiguous resonance volume threshold — 3+ independent contributors
    across 2+ contexts each generate lineage-compatible insights from isolated concepts.

    Confirmed propagation is measured on the transmission axis via disambiguated lineage events.
    """
    valid_events = register.valid_resonance_events()
    contributors = {event.contributor_id for event in valid_events}
    contexts = {event.context_domain for event in valid_events}

    contributor_count = len(contributors)
    context_count = len(contexts)
    blockers: list[str] = []

    insights_by_contributor: dict[str, int] = {}
    for event in valid_events:
        insights_by_contributor[event.contributor_id] = (
            insights_by_contributor.get(event.contributor_id, 0) + 1
        )
    for contributor_id, count in insights_by_contributor.items():
        if count < CRT3_MIN_INSIGHTS_PER_CONTRIBUTOR:
            blockers.append(
                f"{contributor_id} has fewer than {CRT3_MIN_INSIGHTS_PER_CONTRIBUTOR} valid insight(s)."
            )

    if contributor_count < CRT3_MIN_CONTRIBUTORS:
        blockers.append(
            f"Need {CRT3_MIN_CONTRIBUTORS - contributor_count} more independent contributor(s)."
        )
    if context_count < CRT3_MIN_CONTEXTS:
        blockers.append(f"Need {CRT3_MIN_CONTEXTS - context_count} more distinct context(s).")

    threshold_met = (
        contributor_count >= CRT3_MIN_CONTRIBUTORS
        and context_count >= CRT3_MIN_CONTEXTS
        and not blockers
    )

    return CRT3Assessment(
        threshold_met=threshold_met,
        contributor_count=contributor_count,
        context_count=context_count,
        valid_event_count=len(valid_events),
        propagation_mode=(
            PROPAGATION_MODE_PROPAGATION if threshold_met else PROPAGATION_MODE_TRANSMISSION
        ),
        contributors_remaining=max(0, CRT3_MIN_CONTRIBUTORS - contributor_count),
        contexts_remaining=max(0, CRT3_MIN_CONTEXTS - context_count),
        blockers=blockers if not threshold_met else [],
    )


def sue_reference_event() -> ConceptResonanceEvent:
    """First documented concept-resonance data point (Sue)."""
    return ConceptResonanceEvent(
        id="resonance-sue-001",
        contributor_id="sue",
        recorded_at=datetime.now(UTC).replace(microsecond=0),
        context_domain="personal_psychology",
        exposure=ConceptExposure(
            concept_id="judgment_preservation_adjacent",
            description="Encountered one JPSS-adjacent idea about how decisions carry forward.",
            jpss_adjacent=True,
        ),
        insight=ConceptResonanceInsight(
            text="People can retain knowledge while their calibration drifts.",
            extends_trigger=True,
            adds_explanatory_power=True,
            lineage_compatible=True,
            uses_jpss_vocabulary=False,
        ),
        trained_on_jpss=False,
        coached=False,
        framework_exposed=False,
        imitation_flag=False,
        notes=(
            "Ambiguous fork — propagation (extended your idea) and convergence "
            "(independent continuity failure mode) both plausible; convergence is stronger."
        ),
    )
