"""ADM-1 — Accumulation Drift Model (pathological accumulation detection)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css.spec import (
    ADM1_FORMULA,
    ADM_EPSILON_CAPTURE,
    ADM_ALPHA_INFLATION,
    ADM_BETA_FRAGMENTATION,
    ADM_DELTA_OVERLOAD,
    ADM_GAMMA_OSSIFICATION,
    ADM_HIGH_THRESHOLD,
    ADM1_REFERENCE,
    ACCUMULATION_DRIFT_MODES,
)
from src.cos1.accumulation.chain_detector import (
    ClassifiedAccumulationEvent,
    detect_compounding_chains,
)
from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEventLog


class AccumulationDriftSignals(BaseModel):
    inflation: float = 0.0
    fragmentation: float = 0.0
    ossification: float = 0.0
    overload: float = 0.0
    capture: float = 0.0


class ADM1Assessment(BaseModel):
    reference: str = ADM1_REFERENCE
    formula: str = ADM1_FORMULA
    signals: AccumulationDriftSignals = Field(default_factory=AccumulationDriftSignals)
    accumulation_drift_score: float = 0.0
    high_drift: bool = False
    continuity_collapse_risk: bool = False
    active_modes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _signal_inflation(events: list) -> float:
    """A1 added faster than integrated — concepts outpace integration."""
    if not events:
        return 0.0
    a1 = sum(1 for event in events if event.accumulation.signature == "A1")
    integrated = sum(1 for event in events if event.accumulation.returns_stronger)
    raw = (a1 / len(events)) - (integrated / len(events))
    return _clamp(raw + 0.2 if a1 > integrated else raw)


def _signal_fragmentation(events: list) -> float:
    """Pile of insights without shared grammar."""
    if len(events) < 2:
        return 0.0
    tag_sets = [set(event.insight.structural_alignment) for event in events]
    if not any(tag_sets):
        return 0.8
    shared = set.intersection(*tag_sets) if tag_sets else set()
    union = set.union(*tag_sets) if tag_sets else set()
    if not union:
        return 0.7
    coherence = len(shared) / len(union)
    return _clamp(1.0 - coherence)


def _signal_ossification(events: list) -> float:
    """Prior structure weight prevents innovation."""
    if not events:
        return 0.0
    a2 = sum(1 for event in events if event.accumulation.signature == "A2")
    generative = sum(
        1 for event in events if event.accumulation.signature in ("A3", "A4")
    )
    if a2 == 0:
        return 0.0
    return _clamp((a2 / len(events)) - (generative / len(events)))


def _signal_overload(events: list, *, max_chain_threshold: float = 4.0) -> float:
    """Future stewards cannot reconstruct the lineage."""
    classified = [
        ClassifiedAccumulationEvent(
            event_id=event.event_id,
            actor_id=event.actor.id,
            accumulation_signature=event.accumulation.signature,
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
        )
        for event in events
    ]
    chains = detect_compounding_chains(classified)
    if not chains:
        return 0.0 if len(events) <= 3 else 0.3
    max_len = max(chain.length for chain in chains)
    return _clamp(max_len / max_chain_threshold)


def _signal_capture(events: list) -> float:
    """Generation rewarded over integration — one actor dominates."""
    if not events:
        return 0.0
    counts: dict[str, int] = {}
    for event in events:
        counts[event.actor.id] = counts.get(event.actor.id, 0) + 1
    max_share = max(counts.values()) / len(events)
    return _clamp(max_share - (1.0 / len(counts)) if len(counts) > 1 else max_share)


def assess_adm1(
    ce_log: ContinuityEngineEventLog,
    *,
    drift_threshold: float = ADM_HIGH_THRESHOLD,
) -> ADM1Assessment:
    """
    AD = αI + βF + γO + δL + εC

    High AD = continuity collapse through over-growth.
    """
    events = ce_log.accumulation_events()
    signals = AccumulationDriftSignals(
        inflation=_signal_inflation(events),
        fragmentation=_signal_fragmentation(events),
        ossification=_signal_ossification(events),
        overload=_signal_overload(events),
        capture=_signal_capture(events),
    )

    ad = (
        ADM_ALPHA_INFLATION * signals.inflation
        + ADM_BETA_FRAGMENTATION * signals.fragmentation
        + ADM_GAMMA_OSSIFICATION * signals.ossification
        + ADM_DELTA_OVERLOAD * signals.overload
        + ADM_EPSILON_CAPTURE * signals.capture
    )
    ad = round(_clamp(ad), 4)
    high = ad >= drift_threshold

    mode_threshold = 0.35
    active: list[str] = []
    notes: list[str] = []
    for mode, value in (
        ("inflation", signals.inflation),
        ("fragmentation", signals.fragmentation),
        ("ossification", signals.ossification),
        ("overload", signals.overload),
        ("capture", signals.capture),
    ):
        if value >= mode_threshold:
            active.append(mode)
            notes.append(f"{mode}: {value:.2f}")

    return ADM1Assessment(
        signals=signals,
        accumulation_drift_score=ad,
        high_drift=high,
        continuity_collapse_risk=high,
        active_modes=active,
        notes=notes,
    )


def format_accumulation_drift_modes() -> str:
    lines = [f"=== {ADM1_REFERENCE} ===", ""]
    for mode, description in ACCUMULATION_DRIFT_MODES:
        lines.append(f"  {mode}: {description}")
    return "\n".join(lines)
