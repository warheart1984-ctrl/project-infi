"""CRK-T2 telemetry — spine health → boundary signal source."""

from __future__ import annotations

from typing import Any

from src.kernel.spine_telemetry import SpineBoundaryTelemetry


def build_cockpit_spine() -> dict[str, Any]:
    from src.constitutional_cockpit_routes import _ensure_ledgers
    from src.continuity.evidence_fitness import build_spine_health

    law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
    return build_spine_health(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
        mit_store=meaning_store,
        sit_store=sit_store,
        git_store=git_store,
    )


class Telemetry:
    """Live telemetry adapter for the kernel boundary outer loop."""

    def __init__(self, spine: dict[str, Any] | None = None) -> None:
        self._spine = spine or build_cockpit_spine()
        self._adapter = SpineBoundaryTelemetry(spine=self._spine)

    @classmethod
    def current(cls) -> Telemetry:
        return cls(spine=build_cockpit_spine())

    def refresh(self) -> None:
        self._spine = build_cockpit_spine()
        self._adapter = SpineBoundaryTelemetry(spine=self._spine)

    def semantic_overlap_score(self) -> float:
        return self._adapter.semantic_overlap_score()

    def replay_depth_score(self) -> float:
        return self._adapter.replay_depth_score()

    def contract_violation_rate(self) -> float:
        return self._adapter.contract_violation_rate()

    def fitness_drift_score(self) -> float:
        return self._adapter.fitness_drift_score()

    def contract_overlap_score(self) -> float:
        return self._adapter.contract_overlap_score()
