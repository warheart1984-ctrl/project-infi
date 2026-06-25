"""ContinuityMemory — stores registers across continuity layers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.ra.ra_cos1 import RACOS1CycleResult, RACOS1Runtime
from src.continuity.ra.models import RAState, empty_ra_state
from src.continuity.stewardability.register import StewardAbilityRegister
from src.continuity.stewardability.concept_resonance import (
    ConceptResonanceRegister,
    CRT3Assessment,
    assess_crt3,
    concept_resonance_to_lineage_event,
)
from src.continuity.stewardability.lineage_axes import DualAxesAssessment, assess_dual_axes
from src.continuity.stewardability.lineage_event_log import LineageEventLog
from src.cos1.accumulation.ae_json_schema import AccumulationEventLog
from src.cos1.accumulation.chain_detector import MAT3Assessment, assess_mat3, ClassifiedAccumulationEvent
from src.cos1.accumulation.forecast_model import StewardabilityForecast, forecast_from_logs
from src.cos1.constitutional_bridge import ContinuityRegisterSnapshot, sync_constitutional_registers
from src.cos1.continuity_engine.engine import CE1Assessment, ContinuityEngine
from src.cos1.continuity_engine.forecast_ce1 import StewardshipEmergenceSignals
from src.cos1.continuity_engine.state_model import ContinuityStateVector


class ContinuityMemoryState(BaseModel):
    stewardability_register: StewardAbilityRegister = Field(default_factory=StewardAbilityRegister)
    concept_resonance_register: ConceptResonanceRegister = Field(
        default_factory=ConceptResonanceRegister
    )
    lineage_event_log: LineageEventLog = Field(default_factory=LineageEventLog)
    accumulation_event_log: AccumulationEventLog = Field(default_factory=AccumulationEventLog)
    constitutional_snapshot: ContinuityRegisterSnapshot | None = None
    prior_ce_state: ContinuityStateVector | None = None
    ra_state: RAState = Field(default_factory=empty_ra_state)


class ContinuityMemory:
    def __init__(
        self,
        state: ContinuityMemoryState | None = None,
        csr: object | None = None,
    ) -> None:
        self.state = state or ContinuityMemoryState()
        self._csr = csr
        if csr is not None:
            self.sync_from_constitutional(csr)

    @property
    def csr(self) -> object | None:
        return self._csr

    def get_stewardability_register(self) -> StewardAbilityRegister:
        return self.state.stewardability_register

    def get_concept_resonance_register(self) -> ConceptResonanceRegister:
        return self.state.concept_resonance_register

    def get_lineage_event_log(self) -> LineageEventLog:
        return self.state.lineage_event_log

    def get_accumulation_event_log(self) -> AccumulationEventLog:
        return self.state.accumulation_event_log

    def assess_accumulation_mat3(self) -> MAT3Assessment:
        classified = [
            ClassifiedAccumulationEvent.from_accumulation_event(event)
            for event in self.state.accumulation_event_log.events
        ]
        return assess_mat3(classified)

    def forecast_stewardability(self) -> StewardabilityForecast:
        return forecast_from_logs(
            self.state.lineage_event_log,
            self.state.accumulation_event_log,
        )

    def assess_ce1(self, *, update_prior: bool = True) -> CE1Assessment:
        """Run Continuity Engine CE-1 unified assessment."""
        self.sync_lineage_log_from_resonance()
        register = self.state.stewardability_register
        signals = StewardshipEmergenceSignals(
            successor_stewards=len(register.emergence_events()) > 0,
            continuity_mode=False,
        )
        engine = ContinuityEngine(prior_state=self.state.prior_ce_state)
        assessment = engine.assess_from_memory(
            self.state.lineage_event_log,
            self.state.accumulation_event_log,
            prior_state=self.state.prior_ce_state,
            stewardship_signals=signals,
        )
        if update_prior:
            self.state.prior_ce_state = assessment.state
        return assessment

    def sync_lineage_log_from_resonance(self) -> int:
        """Backfill lineage log from concept-resonance events missing lineage rows."""
        existing = {
            event.concept_resonance_id
            for event in self.state.lineage_event_log.events
            if event.concept_resonance_id
        }
        added = 0
        for resonance in self.state.concept_resonance_register.events:
            if resonance.id in existing:
                continue
            self.state.lineage_event_log.append(concept_resonance_to_lineage_event(resonance))
            added += 1
        return added

    def assess_concept_resonance_threshold(self) -> CRT3Assessment:
        return assess_crt3(self.state.concept_resonance_register)

    def assess_lineage_axes(self, *, disambiguate: bool = True) -> DualAxesAssessment:
        self.sync_lineage_log_from_resonance()
        return assess_dual_axes(self.state.lineage_event_log, disambiguate=disambiguate)

    def assess_css1(
        self,
        *,
        drift_signals: list | None = None,
        disambiguate: bool = True,
    ) -> "CSS1Assessment":
        """Run full CSS-1 continuity stack assessment."""
        from src.continuity.css.orchestrator import assess_css1

        self.sync_lineage_log_from_resonance()
        return assess_css1(
            self.state.lineage_event_log,
            self.state.accumulation_event_log,
            self.state.stewardability_register,
            prior_state=self.state.prior_ce_state,
            drift_signals=drift_signals,
            disambiguate=disambiguate,
        )

    def get_ra_runtime(self) -> RACOS1Runtime:
        return RACOS1Runtime(self.state.ra_state)

    def run_ra_cos_cycle(self, **kwargs: object) -> RACOS1CycleResult:
        runtime = self.get_ra_runtime()
        result = runtime.run_cycle(**kwargs)  # type: ignore[arg-type]
        self.state.ra_state = result.state
        return result

    def get_constitutional_snapshot(self) -> ContinuityRegisterSnapshot | None:
        return self.state.constitutional_snapshot

    def sync_from_constitutional(self, csr: object | None = None) -> ContinuityRegisterSnapshot:
        """Load Layers 1–7 registers from CSR into memory snapshot."""
        target = csr if csr is not None else self._csr
        if target is None:
            raise ValueError("No ConstitutionalStateRuntime available for sync.")
        self._csr = target
        snapshot = sync_constitutional_registers(target, self.state.stewardability_register)
        self.state.constitutional_snapshot = snapshot
        return snapshot

    def artifacts_intact(self) -> bool:
        snapshot = self.state.constitutional_snapshot
        if snapshot is None:
            return False
        return snapshot.artifacts_populated
