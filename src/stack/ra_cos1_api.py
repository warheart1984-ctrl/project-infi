"""RA-COS-1 Continuity OS API — observe, log, validate cognitive activity."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.continuity.css2.governance import RecalibrationGovernanceEngine
from src.continuity.css2.models import RecalibrationEvent, RecalibrationLedger, RecalibrationProposalContext
from src.continuity.css2.registry import default_recalibration_rule, seed_css1_thresholds
from src.continuity.css2.threshold import SystemState
from src.continuity.css2.threshold_store import RacosThresholdStore
from src.continuity.ra.jpss_accumulation_sim import (
    JPSSContributionEvent,
    RAAccumulationState,
    ingest_event,
    new_contribution_event_id,
)
from src.continuity.ra.models import ValidationContext
from src.continuity.ra.psdd1 import compute_drift_signals
from src.continuity.ra.ra_cos_loop import RACosLoopResult, process_ra_cos_event
from src.continuity.stewardability.operating_conditions import StewardabilityConditions, good_conditions
from src.cos1.continuity_engine.engine import CE1Assessment
from src.cos1.continuity_os import ContinuityOS
from src.cos1.memory import ContinuityMemory
from src.stack.epistemic import EpistemicMetrics, compute_epistemic_metrics, tag_contribution_event
from src.stack.falsification import FalsificationAssessment, assess_falsification


class ContinuityHealth(BaseModel):
    """Health snapshot: epistemic balance, falsification, CE-1, drift."""

    epistemic: EpistemicMetrics
    falsification: FalsificationAssessment
    ce1: CE1Assessment | None = None
    vas_passed: bool = True
    psdd_classification: str = "STABLE"
    event_count: int = 0
    alerts: list[str] = Field(default_factory=list)


class RACOS1Layer:
    """
    Layer 2 — RA-COS-1 (Continuity OS).

    Observes O/I/I₂/V events, runs PSDD-1 + VAS-1, maintains lineage ledger.
    """

    def __init__(
        self,
        memory: ContinuityMemory | None = None,
        *,
        threshold_store: RacosThresholdStore | None = None,
    ) -> None:
        self._memory = memory or ContinuityMemory()
        self._os = ContinuityOS(memory=self._memory)
        self._jpss_state = RAAccumulationState()
        self._vas_failures: dict[str, bool] = {}
        self._recalibration_ledger = RecalibrationLedger()
        self._recalibration_governance = RecalibrationGovernanceEngine(ledger=self._recalibration_ledger)
        self._threshold_store = threshold_store or RacosThresholdStore()
        if self._threshold_store.is_empty():
            self._threshold_store.seed_from_list(seed_css1_thresholds())
        thresholds = self._threshold_store.load_thresholds()
        self._threshold_state = SystemState(
            thresholds=thresholds,
            recalibration_rule=default_recalibration_rule(),
        )

    @property
    def threshold_store(self) -> RacosThresholdStore:
        return self._threshold_store

    @property
    def threshold_state(self) -> SystemState:
        return self._threshold_state

    def process_recalibration_event(
        self,
        event: dict,
        *,
        drift_signals: dict | None = None,
        validation: dict | None = None,
    ) -> RACosLoopResult:
        """Full RA-COS loop: triggers → Five-Team governance → registry → ledger."""
        result = process_ra_cos_event(
            event,
            drift_signals,
            validation,
            self._threshold_state,
            governance=self._recalibration_governance,
            store=self._threshold_store,
        )
        self._threshold_state = SystemState(
            thresholds=self._threshold_store.load_thresholds(),
            recalibration_rule=self._threshold_state.recalibration_rule,
        )
        return result

    @property
    def recalibration_ledger(self) -> RecalibrationLedger:
        return self._recalibration_ledger

    def evaluate_recalibration(
        self,
        ctx: RecalibrationProposalContext,
    ) -> RecalibrationEvent:
        """CSS-2 recalibration gate — governed threshold changes, not implicit drift."""
        return self._recalibration_governance.evaluate_proposal(ctx)

    @property
    def memory(self) -> ContinuityMemory:
        return self._memory

    @property
    def events(self) -> list[JPSSContributionEvent]:
        return list(self._jpss_state.events)

    def log_event(
        self,
        event: JPSSContributionEvent,
        *,
        tag: bool = True,
    ) -> JPSSContributionEvent:
        """Ingest a JPSS contribution event with optional O/I/I₂/V tagging."""
        tagged = tag_contribution_event(event) if tag else event
        self._jpss_state = ingest_event(self._jpss_state, tagged)
        return tagged

    def log_observation(
        self,
        *,
        actor: str,
        text: str,
        phenomenon_anchor: str | None = None,
        from_exposure: bool = False,
    ) -> JPSSContributionEvent:
        event = JPSSContributionEvent(
            id=new_contribution_event_id("obs"),
            actor=actor,
            timestamp=datetime.now(UTC).replace(microsecond=0),
            source_text=text,
            from_exposure=from_exposure,
            phenomenon_anchor=phenomenon_anchor or text[:120],
            mode="OBSERVATION",
            origin="PLA" if not from_exposure else "LA",
        )
        return self.log_event(event, tag=False)

    def log_interpretation(
        self,
        *,
        actor: str,
        text: str,
        builds_on: list[str] | None = None,
    ) -> JPSSContributionEvent:
        event = JPSSContributionEvent(
            id=new_contribution_event_id("interp"),
            actor=actor,
            timestamp=datetime.now(UTC).replace(microsecond=0),
            source_text=text,
            from_exposure=True,
            builds_on=builds_on or [],
            mode="INTERPRETATION",
            origin="LA",
        )
        return self.log_event(event, tag=False)

    def run_validation(
        self,
        event_id: str,
        ctx: ValidationContext | None = None,
    ) -> VAS1Result:
        """Run VAS-1 on a contribution; record validation event."""
        validation_ctx = ctx or ValidationContext(
            predictive_accuracy_delta=0.1,
            explanatory_compression_delta=0.05,
            cross_domain_convergence=0.6,
            operational_outcome_delta=0.1,
            critique_stability=0.7,
        )
        result = validate_change_vas1(validation_ctx)
        self._vas_failures[event_id] = not result.passed

        source = next((event for event in self._jpss_state.events if event.id == event_id), None)
        if source is not None:
            val_event = JPSSContributionEvent(
                id=new_contribution_event_id("val"),
                actor="ra-cos-1",
                timestamp=datetime.now(UTC).replace(microsecond=0),
                source_text=f"VAS-1 validation for {event_id}: {'PASSED' if result.passed else 'FAILED'}",
                from_exposure=False,
                builds_on=[event_id],
                mode="VALIDATION",
                origin="SA",
                governance_behavior="validate",
                vas_passed=result.passed,
            )
            self.log_event(val_event, tag=False)

        return result

    def run_psdd1(self) -> str:
        """Periodic PSDD-1 drift scan over consequence samples."""
        ra_state = self._memory.state.ra_state
        if not ra_state.consequences:
            return "STABLE"
        drift = compute_drift_signals(ra_state.consequences, baseline=0.5)
        return drift.classification

    def get_continuity_health(
        self,
        *,
        jps_trained_score: float = 0.0,
        control_score: float = 0.0,
    ) -> ContinuityHealth:
        """Aggregate continuity health: epistemic, falsification, CE-1, drift."""
        events = self.events
        epistemic = compute_epistemic_metrics(events)
        falsification = assess_falsification(
            events,
            jps_trained_observation_score=jps_trained_score,
            control_observation_score=control_score,
            vas_failures=self._vas_failures,
        )

        step = self._os.step(good_conditions())
        ce1 = step.ce1

        alerts: list[str] = []
        for channel in falsification.channels_triggered:
            alerts.append(f"Falsification channel triggered: {channel}")
        if epistemic.profile == "doctrine":
            alerts.append("Epistemic profile: doctrine — interpretations without observations.")

        psdd = self.run_psdd1()

        return ContinuityHealth(
            epistemic=epistemic,
            falsification=falsification,
            ce1=ce1,
            vas_passed=all(not failed for failed in self._vas_failures.values()) if self._vas_failures else True,
            psdd_classification=psdd,
            event_count=len(events),
            alerts=alerts,
        )
