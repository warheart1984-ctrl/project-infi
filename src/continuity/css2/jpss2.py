"""JPSS-2 — Judgment pipeline with governed recalibration layers 8–11."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css2.governance import RecalibrationGovernanceEngine, default_recalibration_invariants
from src.continuity.css2.models import (
    RecalibrationEvent,
    RecalibrationProposalContext,
    RecalibrationTrigger,
    ThresholdChange,
)
from src.continuity.css2.spec import JPSS2_FULL_PIPELINE, JPSS2_RECALIBRATION_STAGES


class JPSS2StageResult(BaseModel):
    stage: str
    stage_index: int
    summary: str
    artifacts: dict[str, object] = Field(default_factory=dict)


class JPSS2PipelineResult(BaseModel):
    stages: list[JPSS2StageResult] = Field(default_factory=list)
    recalibration_event: RecalibrationEvent | None = None
    calibration_updated: bool = False


class JPSS2Pipeline:
    """
    JPSS-2 extends JPSS-1 with governed recalibration (stages 8–11).

    Judgment = stages 1–7; Calibration = stage 4 + final governed update;
    Recalibration = stages 8–11.
    """

    def __init__(self, governance: RecalibrationGovernanceEngine | None = None) -> None:
        self.governance = governance or RecalibrationGovernanceEngine()

    def run_recalibration_path(
        self,
        *,
        triggers: list[RecalibrationTrigger],
        proposed_changes: list[ThresholdChange],
        evidence: list[dict[str, object]] | None = None,
        failure_mode_before: str | None = None,
        scope: str = "subsystem",
    ) -> JPSS2PipelineResult:
        stages: list[JPSS2StageResult] = []

        stages.append(
            JPSS2StageResult(
                stage="recalibration_trigger_detection",
                stage_index=8,
                summary=f"Detected {len(triggers)} trigger(s).",
                artifacts={"triggers": [trigger.model_dump() for trigger in triggers]},
            )
        )

        stages.append(
            JPSS2StageResult(
                stage="recalibration_proposal",
                stage_index=9,
                summary=f"Proposed {len(proposed_changes)} threshold change(s).",
                artifacts={"changes": [change.model_dump() for change in proposed_changes]},
            )
        )

        ctx = RecalibrationProposalContext(
            evidence=evidence or [],
            proposed_changes=proposed_changes,
            candidate_failure_mode=failure_mode_before,  # type: ignore[arg-type]
            invariants=default_recalibration_invariants(),
            triggers=triggers,
            scope=scope,  # type: ignore[arg-type]
            trigger_type=triggers[0].trigger_type if triggers else "evidence",
        )

        event = self.governance.evaluate_proposal(ctx)
        stages.append(
            JPSS2StageResult(
                stage="recalibration_governance",
                stage_index=10,
                summary=f"Governance decision: {event.decision}.",
                artifacts={
                    "decision": event.decision,
                    "legitimacy_basis": event.legitimacy_basis,
                    "adversarial_review_passed": event.adversarial_review_passed,
                },
            )
        )

        if event.decision == "approved":
            stages.append(
                JPSS2StageResult(
                    stage="recalibration_event",
                    stage_index=11,
                    summary=f"Event {event.event_id} recorded.",
                    artifacts={"event_id": event.event_id},
                )
            )
            stages.append(
                JPSS2StageResult(
                    stage="calibration_update_governed",
                    stage_index=12,
                    summary="Calibration updated via governed recalibration (not implicit drift).",
                )
            )

        return JPSS2PipelineResult(
            stages=stages,
            recalibration_event=event,
            calibration_updated=event.decision == "approved",
        )

    @staticmethod
    def pipeline_stages() -> tuple[str, ...]:
        return JPSS2_FULL_PIPELINE

    @staticmethod
    def recalibration_stages() -> tuple[str, ...]:
        return JPSS2_RECALIBRATION_STAGES
