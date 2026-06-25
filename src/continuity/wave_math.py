"""WMMS-1 substrate-to-wave measurement standard.

This module derives operational wave parameters from observable continuity
substrate fields. It is intentionally deterministic: every wave value is backed
by event, trace, or substrate data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from src.continuity.ccs import CCSStore, ContinuityTrace, Event
from src.continuity.substrate import ContinuitySubstrate


WMMS_STANDARD = "WMMS-1"

ARCHITECTURAL_SCOPE_SCORES = {
    "local": 0.25,
    "subsystem": 0.65,
    "global": 1.0,
}

REQUIRED_OBSERVABLES = (
    "identity_count",
    "system_count",
    "lineage_depth",
    "governance_impact",
    "architectural_scope_score",
    "pattern_count",
    "time_window",
    "declared_intent_vector",
    "observed_behavior_vector",
    "lineage_direction_vector",
    "replay_divergence",
    "cross_kernel_disagreement",
    "cross_layer_mismatch",
    "lineage_pointer_mismatch",
    "invariant_violation_rate",
    "pattern_persistence",
    "natural_frequency",
    "governance_reinforcement_cycles",
)


@dataclass(frozen=True, slots=True)
class WaveSignature:
    amplitude: float
    frequency: float
    phase: float
    coherence: float
    resonance: float
    standard: str = WMMS_STANDARD
    sources: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "standard": self.standard,
            "A": self.amplitude,
            "f": self.frequency,
            "phi": self.phase,
            "C": self.coherence,
            "R": self.resonance,
            "sources": dict(self.sources),
        }


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _normalize_count(value: float, scale: float) -> float:
    if scale <= 0:
        return 0.0
    return _clamp(value / scale)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return _clamp(dot / (left_norm * right_norm))


def _as_vector(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)):
        return []
    vector: list[float] = []
    for item in value:
        try:
            vector.append(float(item))
        except (TypeError, ValueError):
            return []
    return vector


def _max_context_float(events: list[Event], key: str, default: float = 0.0) -> float:
    values: list[float] = []
    for event in events:
        try:
            values.append(float(event.context.get(key, default)))
        except (TypeError, ValueError):
            continue
    return max(values, default=default)


def _first_context_vector(events: list[Event], key: str) -> list[float]:
    for event in events:
        vector = _as_vector(event.context.get(key))
        if vector:
            return vector
    return []


def _scope_score(value: Any) -> float:
    if isinstance(value, (int, float)):
        return _clamp(float(value))
    return ARCHITECTURAL_SCOPE_SCORES.get(str(value or "").strip().lower(), 0.0)


def _derive_time_window(trace: ContinuityTrace | None, event_count: int) -> float:
    if trace is not None:
        metadata_window = trace.reproducibility_metadata.get("window_seconds")
        try:
            window = float(metadata_window)
            if window > 0:
                return window / 60.0
        except (TypeError, ValueError):
            pass
    return max(float(event_count), 1.0)


def _trace_error(trace: ContinuityTrace | None, key: str) -> float:
    if trace is None:
        return 0.0
    try:
        return _clamp(float(trace.continuity_summary.get(key, 0.0)))
    except (TypeError, ValueError):
        return 0.0


def substrate_observables(
    store: CCSStore,
    substrate: ContinuitySubstrate,
    *,
    trace_id: str | None = None,
    pattern_key: str | None = None,
) -> dict[str, Any]:
    """Extract CSSENS-1 observables from CCS substrate fields."""

    event_ids = list(substrate.ccs_layer.get("events") or [])
    events = [store.events[event_id] for event_id in event_ids if event_id in store.events]
    trace_ids = list(substrate.trace_layer.get("traces") or [])
    active_trace_id = trace_id or (trace_ids[0] if trace_ids else None)
    trace = store.traces.get(active_trace_id or "") if active_trace_id else None

    identities: set[str] = set()
    systems: set[str] = set()
    pattern_count = 0
    selected_pattern = pattern_key or ""
    scope_scores: list[float] = []
    for event in events:
        identities.update(str(item) for item in event.actors if str(item).startswith("identity:"))
        identities.update(str(item) for item in event.targets if str(item).startswith("identity:"))
        identities.update(str(item) for item in event.context.get("affected_identities", []) or [])
        systems.update(str(item) for item in event.targets if str(item).startswith("system:"))
        systems.update(str(item) for item in event.context.get("affected_systems", []) or [])
        event_pattern = str(event.context.get("pattern_key") or event.kind)
        if not selected_pattern:
            selected_pattern = event_pattern
        if event_pattern == selected_pattern:
            pattern_count += 1
        scope_scores.append(_scope_score(event.context.get("architectural_scope")))

    lineage_depth = _max_context_float(events, "lineage_depth")
    governance_impact = _max_context_float(events, "governance_severity")
    time_window = _derive_time_window(trace, len(events))
    return {
        "identity_count": len(identities),
        "system_count": len(systems),
        "lineage_depth": lineage_depth,
        "governance_impact": governance_impact,
        "architectural_scope_score": max(scope_scores, default=0.0),
        "pattern_count": pattern_count,
        "time_window": time_window,
        "declared_intent_vector": _first_context_vector(events, "declared_intent_vector"),
        "observed_behavior_vector": _first_context_vector(events, "observed_behavior_vector"),
        "lineage_direction_vector": _first_context_vector(events, "lineage_direction_vector"),
        "replay_divergence": _trace_error(trace, "replay_divergence"),
        "cross_kernel_disagreement": _trace_error(trace, "cross_kernel_disagreement"),
        "cross_layer_mismatch": _trace_error(trace, "cross_layer_mismatch"),
        "lineage_pointer_mismatch": _trace_error(trace, "lineage_pointer_mismatch"),
        "invariant_violation_rate": _trace_error(trace, "invariant_violation_rate"),
        "pattern_persistence": _max_context_float(events, "pattern_persistence"),
        "natural_frequency": _max_context_float(events, "natural_frequency"),
        "governance_reinforcement_cycles": _max_context_float(events, "governance_reinforcement_cycles"),
        "sources": {
            "substrate_id": substrate.substrate_id,
            "trace_id": active_trace_id,
            "event_ids": [event.id for event in events],
            "pattern_key": selected_pattern,
        },
    }


def measure_wave_signature(observables: dict[str, Any]) -> WaveSignature:
    """Compute WMMS-1 A, f, phi, C, and R from normalized observables."""

    missing = [key for key in REQUIRED_OBSERVABLES if key not in observables]
    if missing:
        raise ValueError(f"missing required observables: {', '.join(missing)}")

    identity_signal = _normalize_count(float(observables["identity_count"]), 5.0)
    system_signal = _normalize_count(float(observables["system_count"]), 5.0)
    lineage_signal = _normalize_count(float(observables["lineage_depth"]), 5.0)
    governance_signal = _clamp(float(observables["governance_impact"]))
    scope_signal = _clamp(float(observables["architectural_scope_score"]))
    amplitude = _clamp(
        (
            identity_signal
            + system_signal
            + lineage_signal
            + governance_signal
            + scope_signal
        )
        / 5.0
    )

    time_window = max(float(observables["time_window"]), 1.0)
    frequency = _clamp(float(observables["pattern_count"]) / time_window)

    intent = _as_vector(observables["declared_intent_vector"])
    behavior = _as_vector(observables["observed_behavior_vector"])
    lineage = _as_vector(observables["lineage_direction_vector"])
    phase = _clamp((_cosine_similarity(intent, behavior) + _cosine_similarity(behavior, lineage)) / 2.0)

    errors = [
        _clamp(float(observables["replay_divergence"])),
        _clamp(float(observables["cross_kernel_disagreement"])),
        _clamp(float(observables["cross_layer_mismatch"])),
        _clamp(float(observables["lineage_pointer_mismatch"])),
        _clamp(float(observables["invariant_violation_rate"])),
    ]
    coherence = _clamp(1.0 - (sum(errors) / len(errors)))

    persistence = _clamp(float(observables["pattern_persistence"]))
    natural_frequency = _clamp(float(observables["natural_frequency"]))
    reinforcement = _normalize_count(float(observables["governance_reinforcement_cycles"]), 5.0)
    frequency_lock = _clamp(1.0 - abs(frequency - natural_frequency))
    resonance = _clamp(max(persistence * frequency_lock, amplitude * reinforcement))

    return WaveSignature(
        amplitude=round(amplitude, 10),
        frequency=round(frequency, 10),
        phase=round(phase, 10),
        coherence=round(coherence, 10),
        resonance=round(resonance, 10),
        sources=dict(observables.get("sources") or {}),
    )


def derive_wave_signature_from_substrate(
    store: CCSStore,
    substrate: ContinuitySubstrate,
    *,
    trace_id: str | None = None,
    pattern_key: str | None = None,
) -> WaveSignature:
    """Run CSSENS-1 extraction and WMMS-1 measurement for one substrate."""

    return measure_wave_signature(
        substrate_observables(
            store,
            substrate,
            trace_id=trace_id,
            pattern_key=pattern_key,
        )
    )
