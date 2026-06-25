"""Continuity Engine CE-1 — unified model of lineage evolution."""

from src.cos1.continuity_engine.ce_json_schema import (
    CE_JSON_SCHEMA_VERSION,
    ContinuityEngineEvent,
    ContinuityEngineEventLog,
    record_ce_event,
)
from src.cos1.continuity_engine.engine import CE1Assessment, ContinuityEngine, format_compounding_curve_phases
from src.cos1.continuity_engine.forecast_ce1 import CEForecastResult, forecast_ce1
from src.cos1.continuity_engine.kernel import ContinuityKernelAssessment, assess_continuity_kernel
from src.cos1.continuity_engine.spec import (
    CE1_REFERENCE,
    CE1_VERSION,
    COMPOUNDING_CURVE_PHASES,
    CONTINUITY_KERNEL_INVARIANTS,
)
from src.cos1.continuity_engine.state_model import (
    CompoundingDominanceAssessment,
    ContinuityStateVector,
    assess_compounding_dominance,
    compute_state_vector,
)
from src.cos1.continuity_engine.thresholds import (
    ContinuityThresholdsAssessment,
    assess_continuity_thresholds,
    assess_ct2,
    assess_mat3_ce1,
    assess_pt3,
)

__all__ = [
    "CE1Assessment",
    "CE1_REFERENCE",
    "CE1_VERSION",
    "CEForecastResult",
    "CE_JSON_SCHEMA_VERSION",
    "COMPOUNDING_CURVE_PHASES",
    "CONTINUITY_KERNEL_INVARIANTS",
    "CompoundingDominanceAssessment",
    "ContinuityEngine",
    "ContinuityEngineEvent",
    "ContinuityEngineEventLog",
    "ContinuityKernelAssessment",
    "ContinuityStateVector",
    "ContinuityThresholdsAssessment",
    "assess_compounding_dominance",
    "assess_continuity_kernel",
    "assess_continuity_thresholds",
    "assess_ct2",
    "assess_mat3_ce1",
    "assess_pt3",
    "compute_state_vector",
    "forecast_ce1",
    "format_compounding_curve_phases",
    "record_ce_event",
]
