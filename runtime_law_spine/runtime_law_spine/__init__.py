"""Runtime Law Spine — law envelope between invariant engine and cognitive OS."""

from runtime_law_spine.runtime_law_spine.boot import run_measured_boot
from runtime_law_spine.runtime_law_spine.conformance import ConformanceLevel, assert_conformance_level
from runtime_law_spine.runtime_law_spine.envelope import CorridorExecutor, DelegateAttestation
from runtime_law_spine.runtime_law_spine.gate import RuntimeLawSpineGate
from runtime_law_spine.runtime_law_spine.immune import (
    LAW_EVOLUTION_CORRIDOR_ID,
    ImmuneMonitor,
    is_law_evolution_corridor,
    quarantine_corridor,
)

__all__ = [
    "ConformanceLevel",
    "CorridorExecutor",
    "DelegateAttestation",
    "ImmuneMonitor",
    "LAW_EVOLUTION_CORRIDOR_ID",
    "RuntimeLawSpineGate",
    "assert_conformance_level",
    "is_law_evolution_corridor",
    "quarantine_corridor",
    "run_measured_boot",
]

RLS_CONTRACT_VERSION = "1.0.0"
