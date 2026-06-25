"""Collapsed stack — CRK-1 → RA-COS-1 → AAIS → LLM."""

from src.stack.aais_runtime import AAISRuntime, LLMAdapter, MockLLMAdapter
from src.stack.crk1_api import CRK1Kernel, ConstitutionalSnapshot
from src.stack.epistemic import (
    EpistemicMetrics,
    EpistemicMode,
    classify_mode,
    compute_epistemic_metrics,
    tag_contribution_event,
)
from src.stack.falsification import (
    FalsificationAssessment,
    FalsificationChannel,
    assess_falsification,
    compute_fm1_observation_delta,
    compute_fm2_convergence_index,
    compute_fm3_interpretation_drift_index,
    compute_fm4_pla_validation_failure_rate,
)
from src.stack.governed_stack import GovernedStack, GovernedStackRequest, GovernedStackResponse
from src.stack.ra_cos1_api import ContinuityHealth, RACOS1Layer
from src.stack.vertical_slice import run_task_planning_slice

__all__ = [
    "AAISRuntime",
    "CRK1Kernel",
    "ConstitutionalSnapshot",
    "ContinuityHealth",
    "EpistemicMetrics",
    "EpistemicMode",
    "FalsificationAssessment",
    "FalsificationChannel",
    "GovernedStack",
    "GovernedStackRequest",
    "GovernedStackResponse",
    "LLMAdapter",
    "MockLLMAdapter",
    "RACOS1Layer",
    "assess_falsification",
    "classify_mode",
    "compute_epistemic_metrics",
    "compute_fm1_observation_delta",
    "compute_fm2_convergence_index",
    "compute_fm3_interpretation_drift_index",
    "compute_fm4_pla_validation_failure_rate",
    "run_task_planning_slice",
    "tag_contribution_event",
]
