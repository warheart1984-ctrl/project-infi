"""L3 immune runtime — quarantine, anomaly hooks, law evolution corridor."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

LAW_EVOLUTION_CORRIDOR_ID = os.environ.get(
    "RLS_LAW_EVOLUTION_CORRIDOR_ID", "law-evolution-v1"
).strip()

_QUARANTINED: set[str] = set()


def is_law_evolution_corridor(corridor_id: str) -> bool:
    return corridor_id == LAW_EVOLUTION_CORRIDOR_ID


def quarantine_corridor(corridor_id: str, *, reason: str = "anomaly") -> None:
    _QUARANTINED.add(corridor_id)


def is_quarantined(corridor_id: str) -> bool:
    return corridor_id in _QUARANTINED


def clear_quarantine(corridor_id: str) -> None:
    _QUARANTINED.discard(corridor_id)


@dataclass
class ImmuneMonitor:
    """Fault threshold → quarantine."""

    fault_threshold: int = 3
    faults: dict[str, int] = field(default_factory=dict)

    def record_fault(self, corridor_id: str, *, detail: str = "") -> bool:
        self.faults[corridor_id] = self.faults.get(corridor_id, 0) + 1
        if self.faults[corridor_id] >= self.fault_threshold:
            quarantine_corridor(corridor_id, reason=detail or "fault_threshold")
            return True
        return False
