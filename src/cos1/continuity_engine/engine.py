"""Continuity Engine CE-1 — unified lineage evolution model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.lineage_event_log import LineageEventLog
from src.cos1.accumulation.ae_json_schema import AccumulationEventLog
from src.cos1.continuity_engine.ce_json_schema import (
    ContinuityEngineEventLog,
    build_ce_log_from_memory_logs,
)
from src.cos1.continuity_engine.forecast_ce1 import (
    CEForecastResult,
    StewardshipEmergenceSignals,
    forecast_ce1,
)
from src.cos1.continuity_engine.kernel import ContinuityKernelAssessment, assess_continuity_kernel
from src.cos1.continuity_engine.spec import CE1_REFERENCE, COMPOUNDING_CURVE_PHASES
from src.cos1.continuity_engine.state_model import (
    CompoundingDominanceAssessment,
    ContinuityStateVector,
    assess_compounding_dominance,
    compute_state_vector,
)
from src.cos1.continuity_engine.thresholds import (
    ContinuityThresholdsAssessment,
    assess_continuity_thresholds,
)


class CE1Assessment(BaseModel):
    reference: str = CE1_REFERENCE
    state: ContinuityStateVector
    thresholds: ContinuityThresholdsAssessment
    kernel: ContinuityKernelAssessment
    forecast: CEForecastResult
    compounding_dominance: CompoundingDominanceAssessment | None = None
    continuity_mode: bool = False
    phase: str = ""
    notes: list[str] = Field(default_factory=list)


class ContinuityEngine:
    """CE-1 — unifies propagation, convergence, accumulation, and stewardship forecast."""

    def __init__(self, prior_state: ContinuityStateVector | None = None) -> None:
        self._prior_state = prior_state

    def build_log(
        self,
        lineage_log: LineageEventLog,
        accumulation_log: AccumulationEventLog,
    ) -> ContinuityEngineEventLog:
        return build_ce_log_from_memory_logs(lineage_log, accumulation_log)

    def assess(
        self,
        ce_log: ContinuityEngineEventLog,
        *,
        prior_state: ContinuityStateVector | None = None,
        stewardship_signals: StewardshipEmergenceSignals | None = None,
    ) -> CE1Assessment:
        state = compute_state_vector(ce_log)
        thresholds = assess_continuity_thresholds(ce_log)
        kernel = assess_continuity_kernel(ce_log.events)

        signals = stewardship_signals or StewardshipEmergenceSignals(
            continuity_mode=thresholds.continuity_mode,
        )
        if not signals.continuity_mode:
            signals.continuity_mode = thresholds.continuity_mode

        forecast = forecast_ce1(state, signals=signals)

        prior = prior_state if prior_state is not None else self._prior_state
        dominance: CompoundingDominanceAssessment | None = None
        if prior is not None:
            dominance = assess_compounding_dominance(prior, state)

        notes = [
            f"Continuity Mode: {thresholds.continuity_mode}",
            f"Phase: {forecast.phase}",
            f"S(t)={forecast.probability:.2f}",
        ]
        if dominance is not None:
            notes.append(dominance.explanation)

        return CE1Assessment(
            state=state,
            thresholds=thresholds,
            kernel=kernel,
            forecast=forecast,
            compounding_dominance=dominance,
            continuity_mode=thresholds.continuity_mode,
            phase=forecast.phase,
            notes=notes,
        )

    def assess_from_memory(
        self,
        lineage_log: LineageEventLog,
        accumulation_log: AccumulationEventLog,
        *,
        prior_state: ContinuityStateVector | None = None,
        stewardship_signals: StewardshipEmergenceSignals | None = None,
    ) -> CE1Assessment:
        ce_log = self.build_log(lineage_log, accumulation_log)
        return self.assess(
            ce_log,
            prior_state=prior_state,
            stewardship_signals=stewardship_signals,
        )


def format_compounding_curve_phases() -> str:
    lines = [f"=== {CE1_REFERENCE} — Compounding Curve ===", ""]
    for phase, description in COMPOUNDING_CURVE_PHASES:
        lines.append(f"  {phase}: {description}")
    lines.append("")
    lines.append("  P → C → A → SE → SA")
    lines.append("")
    return "\n".join(lines)
