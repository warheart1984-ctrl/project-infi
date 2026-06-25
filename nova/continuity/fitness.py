from __future__ import annotations

from dataclasses import dataclass
from typing import List

from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.models import LawRecord


@dataclass
class ContinuityFitnessComponents:
    omega_score: float
    pit_fitness: float
    lineage_stability: float


def compute_pit_fitness(ledger: LawLedger) -> float:
    pits: List[LawRecord] = [law for law in ledger.all() if law.code.startswith("PIT-")]
    if not pits:
        return 0.0
    vals = [max(0.0, min(law.fitness, 1.0)) for law in pits]
    return sum(vals) / len(vals)


def compute_lineage_stability(replay_passes: int, replay_total: int) -> float:
    if replay_total == 0:
        return 0.0
    return replay_passes / replay_total


def continuity_fitness_index(components: ContinuityFitnessComponents) -> float:
    w_omega = 0.5
    w_pit = 0.25
    w_lineage = 0.25
    return (
        w_omega * components.omega_score
        + w_pit * components.pit_fitness
        + w_lineage * components.lineage_stability
    )
