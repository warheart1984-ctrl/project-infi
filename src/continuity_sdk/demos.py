# src/continuity_sdk/demos.py

from .lawful_llm_adapter import FallingObjectModel, LawfulLLMAdapter
from src.crk1.mission_005_calibration_lineage_stress import (
    run_mission_005_calibration_lineage_stress as _run_m005,
)


def run_falling_object_scenario():
    llm = LawfulLLMAdapter(FallingObjectModel(), steward_id="steward_llm")
    exp = llm.predict("Predict fall time for 2m drop.")
    evidence = llm.observe({"value": 0.3, "strength": 1.0})
    correction, crr1 = llm.correct(exp, evidence)
    return correction, crr1


def run_mission_005_calibration_lineage_stress():
    return _run_m005()


__all__ = [
    "run_falling_object_scenario",
    "run_mission_005_calibration_lineage_stress",
]
