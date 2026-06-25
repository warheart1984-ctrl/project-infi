"""Telemetry adapter: inner-loop spine health → CRK-T2 signal vector s(t)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Protocol


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class BoundaryTelemetrySource(Protocol):
    def semantic_overlap_score(self) -> float: ...

    def replay_depth_score(self) -> float: ...

    def contract_violation_rate(self) -> float: ...

    def fitness_drift_score(self) -> float: ...

    def contract_overlap_score(self) -> float: ...


def _health_below_threshold(spine: dict[str, Any], key: str) -> set[str]:
    section = spine.get(key) or {}
    items = section.get("below_threshold") or []
    return {str(item) for item in items}


def measure_semantic_overlap(spine: dict[str, Any]) -> float:
    keys = (
        "comprehension_health",
        "meaning_health",
        "evidence_fitness_health",
        "structural_health",
        "generative_health",
        "proof_health",
    )
    sets = [_health_below_threshold(spine, key) for key in keys if spine.get(key)]
    sets = [item for item in sets if item]
    if len(sets) < 2:
        return 0.0
    overlap_pairs = 0
    union_pairs = 0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            overlap_pairs += len(sets[i] & sets[j])
            union_pairs += len(sets[i] | sets[j])
    if union_pairs == 0:
        return 0.0
    return _clamp(overlap_pairs / union_pairs)


def measure_replay_complexity(spine: dict[str, Any]) -> float:
    warning_count = 0
    for key in (
        "comprehension_health",
        "meaning_health",
        "evidence_fitness_health",
        "structural_health",
        "generative_health",
        "proof_health",
        "outcome_health",
    ):
        section = spine.get(key) or {}
        warning_count += len(section.get("warnings") or [])
    return _clamp(warning_count / 24.0)


def count_contract_failures(spine: dict[str, Any]) -> float:
    blocks = spine.get("block_reasons") or []
    return _clamp(len(blocks) / 7.0)


def measure_fitness_drift(spine: dict[str, Any]) -> float:
    outcome_drift = float(spine.get("outcome_drift") or 0.0)
    layers = [
        float((spine.get("comprehension_health") or {}).get("avg_chi") or 0.0),
        float((spine.get("meaning_health") or {}).get("avg_mu") or 0.0),
        float((spine.get("evidence_fitness_health") or {}).get("avg_omega") or 0.0),
        float((spine.get("structural_health") or {}).get("avg_sigma") or 0.0),
        float((spine.get("generative_health") or {}).get("avg_lambda") or 0.0),
        float((spine.get("proof_health") or {}).get("avg_phi") or 0.0),
    ]
    mean = sum(layers) / len(layers) if layers else 0.0
    spread = math.sqrt(sum((value - mean) ** 2 for value in layers) / len(layers)) if layers else 0.0
    return _clamp(outcome_drift + spread)


def detect_contract_overlap() -> float:
    from src.continuity.crk1_compliance import scan_contract_classes

    found = scan_contract_classes()
    redundant = max(0, len(found) - 4)
    return _clamp(redundant / 4.0)


@dataclass(slots=True)
class SpineBoundaryTelemetry:
    """Wraps spine health dict with CRK-T2 telemetry method names."""

    spine: dict[str, Any]

    def semantic_overlap_score(self) -> float:
        return measure_semantic_overlap(self.spine)

    def replay_depth_score(self) -> float:
        return measure_replay_complexity(self.spine)

    def contract_violation_rate(self) -> float:
        return count_contract_failures(self.spine)

    def fitness_drift_score(self) -> float:
        return measure_fitness_drift(self.spine)

    def contract_overlap_score(self) -> float:
        return detect_contract_overlap()

    def as_vector(self) -> tuple[float, float, float, float, float]:
        return (
            self.semantic_overlap_score(),
            self.replay_depth_score(),
            self.contract_violation_rate(),
            self.fitness_drift_score(),
            self.contract_overlap_score(),
        )


def telemetry_from_spine(spine: dict[str, Any]) -> SpineBoundaryTelemetry:
    return SpineBoundaryTelemetry(spine=spine)
