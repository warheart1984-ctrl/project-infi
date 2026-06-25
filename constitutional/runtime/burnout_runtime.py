# constitutional_substrate/burnout_runtime.py
"""Burnout runtime — snapshots, recovery plans, and founder load risk."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Literal

from constitutional.runtime.domain_receipt_emitter import build_domain_observation_receipt
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass
from constitutional.runtime.receipts_v2 import ObservationReceiptV2
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.core.models import StateObject
from pydantic import BaseModel

RUNTIME_NAME = "BurnoutRuntime"
LATEST_ID = "burnout__latest"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------- StateObjects ----------


class BurnoutState(BaseModel):
    state_id: str
    state_type: str = "burnout_state"
    snapshot_at: datetime
    sleep_quality: float
    stress_level: float
    cognitive_load: float
    meeting_load: float
    recovery_index: float
    trend: Literal["improving", "stable", "worsening"]


class RecoveryPlanState(BaseModel):
    state_id: str
    state_type: str = "recovery_plan"
    created_at: datetime
    measures: list[str]
    duration_days: int
    adherence: float
    active: bool = True


# ---------- Runtime ----------


class BurnoutRuntime:
    """Detects degradation and governs recovery."""

    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        ReconstructabilityFailureClass.STEWARD_DISCONTINUITY,
    ]

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr
        self._ensure_latest_slot()

    def _ensure_latest_slot(self) -> None:
        try:
            self.csr.get_state(LATEST_ID)
        except KeyError:
            self.csr.register_state(
                StateObject(
                    state_id=LATEST_ID,
                    state_type="burnout_state",
                    current_state="Proposed",
                    invariants=["BR-1", "BR-2", "BR-3"],
                    evidence_requirements=["burnout_snapshot"],
                    authority_model=["founder"],
                    reproducibility_requirements=["exact"],
                    impact_boundaries=["burnout", "personal_health"],
                    accountability_chain=["founder"],
                )
            )

    def snapshot(
        self,
        sleep_quality: float,
        stress_level: float,
        cognitive_load: float,
        meeting_load: float,
        recovery_index: float,
    ) -> BurnoutState:
        now = _utc_now()
        prev: BurnoutState | None = None
        try:
            prev = self.csr.get_state_doc(LATEST_ID)
        except KeyError:
            prev = None

        trend: Literal["improving", "stable", "worsening"] = "stable"
        if prev is not None:
            prev_score = self._score(prev)
            curr_score = self._score_values(
                sleep_quality, stress_level, cognitive_load, meeting_load, recovery_index
            )
            if curr_score < prev_score - 0.1:
                trend = "worsening"
            elif curr_score > prev_score + 0.1:
                trend = "improving"

        state = BurnoutState(
            state_id=LATEST_ID,
            snapshot_at=now,
            sleep_quality=sleep_quality,
            stress_level=stress_level,
            cognitive_load=cognitive_load,
            meeting_load=meeting_load,
            recovery_index=recovery_index,
            trend=trend,
        )
        self.csr.set_burnout_latest(state)
        self._emit_burnout_receipt(state)
        return state

    def create_recovery_plan(self, measures: list[str], duration_days: int) -> RecoveryPlanState:
        now = _utc_now()
        plan = RecoveryPlanState(
            state_id=f"recovery_plan__{int(now.timestamp())}",
            created_at=now,
            measures=measures,
            duration_days=duration_days,
            adherence=0.0,
        )
        self.csr.register_state(
            StateObject(
                state_id=plan.state_id,
                state_type="recovery_plan",
                current_state="Proposed",
                invariants=["BR-2"],
                evidence_requirements=["recovery_plan"],
                authority_model=["founder"],
                reproducibility_requirements=["exact"],
                impact_boundaries=["burnout"],
                accountability_chain=["founder"],
            )
        )
        self.csr.put_domain_doc(plan.state_id, "recovery_plan", plan)
        self._emit_recovery_receipt(plan, kind="PlanCreate")
        return plan

    def assess_risk(self) -> ObservationReceiptV2:
        state = self.csr.get_state_doc(LATEST_ID)
        score = 1.0 - self._score(state)

        level: Literal["ok", "warning", "critical"]
        if score < 0.3:
            level = "ok"
        elif score < 0.6:
            level = "warning"
        else:
            level = "critical"

        payload = {"burnout_risk_score": score, "level": level}
        prior = self.csr.domain_receipts_for(LATEST_ID)
        prev = prior[-1] if prior else None
        receipt = build_domain_observation_receipt(
            runtime=RUNTIME_NAME,
            state_object_id=state.state_id,
            action_type="burnout_risk_assessment",
            kind="Observation",
            invariant_name="FOUNDER_MUST_NOT_OPERATE_IN_SUSTAINED_CRITICAL_BURNOUT_STATE",
            invariant_description="BR-1: sustained critical burnout blocks operation",
            payload=payload,
            impact_scope_in=["personal_health", "burnout"],
            thread_id=LATEST_ID,
            previous_receipt_id=prev.receipt_id if prev else None,
            previous_lineage_hash=prev.continuity.lineage_hash if prev else None,
            observed_status=level,
            threats=list(self.resists),
        )
        self.csr.append_observation_receipt(receipt)
        return receipt

    def _score(self, snapshot: BurnoutState) -> float:
        return self._score_values(
            snapshot.sleep_quality,
            snapshot.stress_level,
            snapshot.cognitive_load,
            snapshot.meeting_load,
            snapshot.recovery_index,
        )

    @staticmethod
    def _score_values(
        sleep_quality: float,
        stress_level: float,
        cognitive_load: float,
        meeting_load: float,
        recovery_index: float,
    ) -> float:
        return max(
            0.0,
            min(
                1.0,
                0.3 * sleep_quality
                + 0.2 * (1 - stress_level)
                + 0.2 * (1 - cognitive_load)
                + 0.1 * (1 - meeting_load)
                + 0.2 * recovery_index,
            ),
        )

    def _emit_burnout_receipt(self, state: BurnoutState) -> None:
        prior = self.csr.domain_receipts_for(state.state_id)
        prev = prior[-1] if prior else None
        receipt = build_domain_observation_receipt(
            runtime=RUNTIME_NAME,
            state_object_id=state.state_id,
            action_type="burnout_snapshot",
            kind="Observation",
            invariant_name="BURNOUT_STATE_MUST_BE_TRACKED_AND_VISIBLE",
            invariant_description="BR-3: cognitive + meeting load must be visible",
            payload=state.model_dump(mode="json"),
            impact_scope_in=["personal_health", "burnout"],
            thread_id=state.state_id,
            previous_receipt_id=prev.receipt_id if prev else None,
            previous_lineage_hash=prev.continuity.lineage_hash if prev else None,
            observed_status=state.trend,
            threats=list(self.resists),
        )
        self.csr.append_observation_receipt(receipt)

    def _emit_recovery_receipt(self, plan: RecoveryPlanState, kind: str) -> None:
        prior = self.csr.domain_receipts_for(plan.state_id)
        prev = prior[-1] if prior else None
        receipt = build_domain_observation_receipt(
            runtime=RUNTIME_NAME,
            state_object_id=plan.state_id,
            action_type=f"recovery_{kind.lower()}",
            kind=kind,
            invariant_name="BURNOUT_WARNINGS_MUST_TRIGGER_RECOVERY_PLANS",
            invariant_description="BR-2: warnings require recovery plan within bounded time",
            payload=plan.model_dump(mode="json"),
            impact_scope_in=["personal_health", "burnout"],
            thread_id=plan.state_id,
            previous_receipt_id=prev.receipt_id if prev else None,
            previous_lineage_hash=prev.continuity.lineage_hash if prev else None,
            observed_status=kind,
            threats=[
                ReconstructabilityFailureClass.REMEDIATION_AMNESIA,
                ReconstructabilityFailureClass.STEWARD_DISCONTINUITY,
            ],
        )
        self.csr.append_observation_receipt(receipt)
