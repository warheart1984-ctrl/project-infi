"""Minimal RA-COS-1 JPSS accumulation simulation — Sue/Bradley MAT-3 pattern."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.cos1.accumulation.ae_json_schema import AccumulationSignature

AccumulationType = AccumulationSignature
EpistemicMode = Literal["OBSERVATION", "INTERPRETATION", "INTEGRATION", "VALIDATION"]
AccumulationOrigin = Literal["PLA", "LA", "SA"]
GovernanceBehavior = Literal["integrate", "compress", "validate", "correct"]

JPSSLayerTarget = Literal["Continuity", "Transferability", "Governance", "Meta"]

# Bradley's proposed judgment-transmission carriers (COS-1 territory)
JUDGMENT_TRANSMISSION_CARRIERS: tuple[str, ...] = (
    "judgment_lineage",
    "stewardship_record",
    "constitutional_precedent_record",
)

JUDGMENT_ARCHITECTURE_LAYERS: tuple[str, ...] = (
    "judgment_categories",
    "judgment_transmission",
    "judgment_evolution",
)

MAT3_MIN_ACCUMULATION_EVENTS = 3
MAT3_MIN_DISTINCT_ACTORS = 2


class JPSSContributionEvent(BaseModel):
    """CSS-1 / RA-COS-1 contribution event — O/I/I₂/V epistemic modes."""

    id: str
    actor: str
    timestamp: datetime
    source_text: str

    from_exposure: bool = False
    accumulation_type: AccumulationType = "NONE"
    targets_layer: JPSSLayerTarget = "Continuity"

    builds_on: list[str] = Field(default_factory=list)

    # Epistemic tagging (parity with cos1-accumulation-sim)
    origin: AccumulationOrigin | None = None
    mode: EpistemicMode | None = None
    phenomenon_anchor: str | None = None
    lineage_compatible: bool = True
    governance_behavior: GovernanceBehavior | None = None
    vas_passed: bool | None = None

    # Optional COS-1 enrichment
    move_summary: str = ""
    judgment_carriers: list[str] = Field(default_factory=list)


class RAAccumulationState(BaseModel):
    """
    Minimal in-memory RA accumulation state for JPSS contribution tracking.

    Named RAAccumulationState to distinguish from governance ``RAState`` in models.py.
    """

    events: list[JPSSContributionEvent] = Field(default_factory=list)
    accumulation_count: int = 0
    multi_person_actors: list[str] = Field(default_factory=list)

    @property
    def actor_set(self) -> set[str]:
        return set(self.multi_person_actors)


def new_contribution_event_id(prefix: str = "jpss-ev") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:8]}"


def ingest_event(state: RAAccumulationState, event: JPSSContributionEvent) -> RAAccumulationState:
    """Append event and update accumulation counters."""
    is_accum = event.accumulation_type != "NONE"
    new_count = state.accumulation_count + (1 if is_accum else 0)
    actors = list(state.multi_person_actors)
    if is_accum and event.actor not in actors:
        actors.append(event.actor)
    return RAAccumulationState(
        events=[*state.events, event],
        accumulation_count=new_count,
        multi_person_actors=actors,
    )


def has_reached_mat3(state: RAAccumulationState) -> bool:
    """
    MAT-3 in the wild: multi-person accumulation with structural deepening.

    Requires ≥3 accumulation events, ≥2 distinct accumulating actors,
    and at least one A2, A3, or A4 event.
    """
    distinct_actors = len(state.actor_set)
    has_a2_or_higher = any(
        event.accumulation_type in {"A2", "A3", "A4"}
        for event in state.events
        if event.accumulation_type != "NONE"
    )
    return (
        state.accumulation_count >= MAT3_MIN_ACCUMULATION_EVENTS
        and distinct_actors >= MAT3_MIN_DISTINCT_ACTORS
        and has_a2_or_higher
    )


def mat3_assessment(state: RAAccumulationState) -> dict[str, object]:
    """Inspectable MAT-3 signal for dashboards and Dar-z replay."""
    distinct = len(state.actor_set)
    has_a2 = any(e.accumulation_type in {"A2", "A3", "A4"} for e in state.events)
    reached = has_reached_mat3(state)
    blockers: list[str] = []
    if state.accumulation_count < MAT3_MIN_ACCUMULATION_EVENTS:
        blockers.append(
            f"Need {MAT3_MIN_ACCUMULATION_EVENTS - state.accumulation_count} more accumulation event(s)."
        )
    if distinct < MAT3_MIN_DISTINCT_ACTORS:
        blockers.append(
            f"Need {MAT3_MIN_DISTINCT_ACTORS - distinct} more distinct accumulating actor(s)."
        )
    if not has_a2:
        blockers.append("Need at least one A2, A3, or A4 (structural or higher) event.")
    return {
        "reached": reached,
        "accumulation_count": state.accumulation_count,
        "distinct_actors": distinct,
        "actors": sorted(state.actor_set),
        "has_a2_or_higher": has_a2,
        "blockers": blockers,
        "verdict": (
            "Multi-person accumulation (MAT-3) — no longer single-mind compounding."
            if reached
            else "Pre-MAT-3 — accumulation not yet multi-person and structural."
        ),
    }


def event_sue_calibration_drift(*, builds_on: list[str] | None = None) -> JPSSContributionEvent:
    """Sue: A1 Accumulation (Explanatory Deepening) — calibration drift without knowledge loss."""
    return JPSSContributionEvent(
        id="E_Sue",
        actor="Sue",
        timestamp=datetime.now(UTC).replace(microsecond=0),
        source_text=(
            "Calibration can drift while knowledge persists — a continuity failure mode "
            "distinct from knowledge loss."
        ),
        from_exposure=True,
        accumulation_type="A1",
        targets_layer="Continuity",
        builds_on=builds_on or [],
        move_summary="Revealed calibration drift without knowledge loss.",
    )


def event_bradley_judgment_transmission(*, builds_on: list[str] | None = None) -> JPSSContributionEvent:
    """Bradley: A2 Accumulation (Structural Deepening) — judgment transmission gap + carriers."""
    return JPSSContributionEvent(
        id="E_Bradley",
        actor="Bradley",
        timestamp=datetime.now(UTC).replace(microsecond=0),
        source_text=(
            "Judgment requires categories, transmission, and evolution — carried by "
            "judgment lineage, stewardship record, and constitutional precedent record."
        ),
        from_exposure=True,
        accumulation_type="A2",
        targets_layer="Transferability",
        builds_on=builds_on or ["E_Sue"],
        move_summary="Challenged structural assumption; proposed judgment transmission layer.",
        judgment_carriers=list(JUDGMENT_TRANSMISSION_CARRIERS),
    )


def event_jon_structural_prior(*, event_id: str = "E_Jon") -> JPSSContributionEvent:
    """Optional seed: Jon's earlier A2 move before Sue/Bradley."""
    return JPSSContributionEvent(
        id=event_id,
        actor="Jon",
        timestamp=datetime.now(UTC).replace(microsecond=0),
        source_text="JPSS dual-pipeline architecture — formation and reconstruction symmetry.",
        from_exposure=False,
        accumulation_type="A2",
        targets_layer="Governance",
        builds_on=[],
        move_summary="Structural deepening of ECK-2 dual pipeline.",
    )


def simulate_sue_bradley_mat3(
    *,
    include_jon_seed: bool = True,
) -> tuple[RAAccumulationState, list[dict[str, object]]]:
    """
    Run minimal RA-COS-1 sim: seed → Sue → Bradley.

    Returns final state and step-by-step MAT-3 assessments (inspectable flip false → true).
    """
    state = RAAccumulationState()
    trace: list[dict[str, object]] = []

    if include_jon_seed:
        state = ingest_event(state, event_jon_structural_prior())
        trace.append({"step": "Jon (A2 seed)", **mat3_assessment(state)})

    state = ingest_event(state, event_sue_calibration_drift(builds_on=["E_Jon"] if include_jon_seed else []))
    trace.append({"step": "Sue (A1 continuity failure mode)", **mat3_assessment(state)})

    state = ingest_event(state, event_bradley_judgment_transmission())
    trace.append({"step": "Bradley (A2 transmission gap)", **mat3_assessment(state)})

    return state, trace


def css1_accumulation_classification(event: JPSSContributionEvent) -> dict[str, str]:
    """Map a contribution event to CSS-1 accumulation axis labels."""
    type_labels = {
        "A1": "A1 Accumulation (Explanatory Deepening)",
        "A2": "A2 Accumulation (Structural Deepening)",
        "A3": "A3 Accumulation (Integrative Synthesis)",
        "A4": "A4 Accumulation (Generational Compounding)",
        "NONE": "No accumulation",
    }
    return {
        "actor": event.actor,
        "type": type_labels.get(event.accumulation_type, event.accumulation_type),
        "axis": event.targets_layer,
        "move": event.move_summary or event.source_text[:120],
        "complementary_pattern": (
            "Sue → continuity failure mode; Bradley → transmission gap + architectural patch"
            if event.actor in {"Sue", "Bradley"}
            else ""
        ),
    }
