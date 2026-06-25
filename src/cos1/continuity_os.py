"""ContinuityOS (COS-1) — orchestrates memory, runtime, immune system, and succession."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.capacity_test import StewardshipCapacityTestResult
from src.continuity.stewardability.concept_resonance import CRT3Assessment
from src.continuity.stewardability.lineage_axes import DualAxesAssessment
from src.cos1.accumulation.chain_detector import MAT3Assessment
from src.cos1.accumulation.forecast_model import StewardabilityForecast
from src.cos1.continuity_engine.engine import CE1Assessment
from src.continuity.ra.ra_cos1 import RACOS1CycleResult
from src.continuity.stewardability.drift_detector import DriftSignal
from src.continuity.stewardability.emergence_protocol import EmergenceCandidate
from src.continuity.stewardability.operating_conditions import StewardabilityConditions
from src.continuity.stewardability.regenerative_model import ContinuityState
from src.continuity.stewardability.register import StewardDemonstration
from src.cos1.immune_system import ContinuityImmuneSystem
from src.cos1.memory import ContinuityMemory
from src.cos1.runtime import ContinuityRuntime
from src.cos1.succession import ContinuitySuccession

_step_result_model_ready = False


def _ensure_continuity_step_result_model() -> None:
    global _step_result_model_ready
    if _step_result_model_ready:
        return
    from src.continuity.css.orchestrator import CSS1Assessment

    ContinuityStepResult.model_rebuild(
        _types_namespace={"CSS1Assessment": CSS1Assessment},
    )
    _step_result_model_ready = True


class ContinuityStepResult(BaseModel):
    continuity_state: ContinuityState
    continuity_succeeded: bool
    drift_signals: list[DriftSignal] = Field(default_factory=list)
    emergence_recognized: bool | None = None
    concept_resonance: CRT3Assessment | None = None
    lineage_axes: DualAxesAssessment | None = None
    accumulation_mat3: MAT3Assessment | None = None
    stewardability_forecast: StewardabilityForecast | None = None
    ce1: CE1Assessment | None = None
    css1: "CSS1Assessment | None" = None
    ra_cos1: RACOS1CycleResult | None = None


class ContinuityOS:
    """COS-1 prototype: OS whose purpose is to preserve the stewardship runtime."""

    def __init__(
        self,
        memory: ContinuityMemory | None = None,
        csr: object | None = None,
    ) -> None:
        self.memory = memory or ContinuityMemory(csr=csr)
        if csr is not None and self.memory.csr is None:
            self.memory.sync_from_constitutional(csr)
        self.runtime = ContinuityRuntime(self.memory)
        self.immune = ContinuityImmuneSystem(self.memory)
        self.succession = ContinuitySuccession(self.memory)

    def step(
        self,
        conditions: StewardabilityConditions,
        candidate: EmergenceCandidate | None = None,
        demo: StewardDemonstration | None = None,
        *,
        capacity_test: StewardshipCapacityTestResult | None = None,
        require_capacity_test: bool = False,
    ) -> ContinuityStepResult:
        emergence_recognized: bool | None = None

        if candidate is not None and demo is not None:
            result = self.runtime.run_emergence(
                candidate,
                demo,
                capacity_test=capacity_test,
                require_capacity_test=require_capacity_test,
            )
            emergence_recognized = result.recognized_as_steward

        self.succession.update(conditions)
        drift_signals = self.immune.check_stewardability_drift()
        crt3 = self.memory.assess_concept_resonance_threshold()
        lineage_axes = self.memory.assess_lineage_axes()
        mat3 = self.memory.assess_accumulation_mat3()
        forecast = self.memory.forecast_stewardability()
        ce1 = self.memory.assess_ce1()
        css1 = self.memory.assess_css1(drift_signals=drift_signals)
        ra_cos1 = self.memory.run_ra_cos_cycle()

        _ensure_continuity_step_result_model()
        return ContinuityStepResult(
            continuity_state=self.succession.get_state(),
            continuity_succeeded=self.succession.continuity_succeeded(),
            drift_signals=drift_signals,
            emergence_recognized=emergence_recognized,
            concept_resonance=crt3,
            lineage_axes=lineage_axes,
            accumulation_mat3=mat3,
            stewardability_forecast=forecast,
            ce1=ce1,
            css1=css1,
            ra_cos1=ra_cos1,
        )
