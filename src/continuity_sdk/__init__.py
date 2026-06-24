# src/continuity_sdk/__init__.py
"""
Continuity SDK v0 — minimal steward interface for CRK-1 / CE-1 / CLG-1.

See README.md in this package for install, quick start, and guarantees.
"""

from .demos import (
    run_falling_object_scenario,
    run_mission_005_calibration_lineage_stress,
)
from .lawful_llm_adapter import FallingObjectModel, LawfulLLMAdapter

from .steward_certification import (
    CERTIFICATION_TITLE,
    PASSING_SCORE,
    STEWARD_CERTIFICATION_QUESTIONS,
    StewardCertificationResult,
    grade_steward_certification,
)
from .steward_console import render_steward_console

__all__ = [
    "LawfulLLMAdapter",
    "FallingObjectModel",
    "run_falling_object_scenario",
    "run_mission_005_calibration_lineage_stress",
    "render_steward_console",
    "CERTIFICATION_TITLE",
    "PASSING_SCORE",
    "STEWARD_CERTIFICATION_QUESTIONS",
    "StewardCertificationResult",
    "grade_steward_certification",
]
