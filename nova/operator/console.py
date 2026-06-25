from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from nova.continuity.fitness import (
    ContinuityFitnessComponents,
    compute_pit_fitness,
    continuity_fitness_index,
)
from nova.law_kernel.law_ledger import LawLedger


@dataclass
class OperatorConsole:
    ledger: LawLedger

    def snapshot_status(self, omega_score: float, lineage_stability: float) -> dict[str, Any]:
        pit_fitness = compute_pit_fitness(self.ledger)
        cfi = continuity_fitness_index(
            ContinuityFitnessComponents(
                omega_score=omega_score,
                pit_fitness=pit_fitness,
                lineage_stability=lineage_stability,
            )
        )
        return {
            "omega_score": omega_score,
            "pit_fitness": pit_fitness,
            "lineage_stability": lineage_stability,
            "continuity_fitness_index": cfi,
        }

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.snapshot_status(**kwargs), indent=2)
