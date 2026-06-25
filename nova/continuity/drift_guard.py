from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DriftReport:
    epoch_a: str
    epoch_b: str
    divergence: float
    drift_detected: bool
    changed_sections: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_a": self.epoch_a,
            "epoch_b": self.epoch_b,
            "divergence": round(self.divergence, 6),
            "drift_detected": self.drift_detected,
            "changed_sections": list(self.changed_sections),
        }


_epoch_states: dict[str, dict[str, Any]] = {}


class DriftGuard:
    """Monotone drift detection across epoch cockpit summaries."""

    def record_epoch_state(self, epoch_id: str, summary: dict[str, Any]) -> None:
        _epoch_states[epoch_id] = dict(summary)

    def detect_drift(self, epoch_a: str, epoch_b: str) -> DriftReport:
        state_a = _epoch_states.get(epoch_a, {})
        state_b = _epoch_states.get(epoch_b, {})
        changed: list[str] = []
        divergence = 0.0
        sections = set(state_a.keys()) | set(state_b.keys())
        for section in sorted(sections):
            if state_a.get(section) != state_b.get(section):
                changed.append(section)
                divergence += 1.0
        if sections:
            divergence /= len(sections)
        return DriftReport(
            epoch_a=epoch_a,
            epoch_b=epoch_b,
            divergence=divergence,
            drift_detected=bool(changed),
            changed_sections=changed,
        )


def clear_epoch_states() -> None:
    _epoch_states.clear()
