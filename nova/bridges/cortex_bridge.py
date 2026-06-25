"""cog_runtime spec ↔ nova cortex formal planning/execution."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.execution import EXECUTION_RUNTIME_ID, run_execution_turn
from src.cog_runtime.planning import PLANNING_RUNTIME_ID, run_planning_turn

from nova.cortex.types import CortexPlan, CortexResult


def plan_with_formal_cortex(spec: dict[str, Any]) -> CortexPlan:
    reflection = dict(spec.get("reflection_artifact") or {})
    focus = dict(spec.get("focus_artifact") or {})
    decision = dict(spec.get("decision_object") or {})
    arc = dict(spec.get("cognitive_arc") or {})
    artifact, session = run_planning_turn(
        reflection_artifact=reflection,
        focus_artifact=focus,
        decision_object=decision,
        cognitive_arc=arc,
        frame_kind=str(spec.get("frame_kind") or "general"),
        user_message=str(spec.get("user_message") or ""),
        tuned_thresholds=spec.get("tuned_thresholds"),
        context=spec.get("context"),
    )
    return CortexPlan(
        runtime_id=PLANNING_RUNTIME_ID,
        artifact=artifact,
        session_trace=session.export_ledger(),
    )


def execute_with_formal_cortex(plan: CortexPlan, *, spec: dict[str, Any] | None = None) -> CortexResult:
    body = dict(spec or {})
    artifact, session = run_execution_turn(
        planning_artifact=plan.artifact,
        focus_artifact=body.get("focus_artifact"),
        decision_object=body.get("decision_object"),
        reflection_artifact=body.get("reflection_artifact"),
        cognitive_arc=body.get("cognitive_arc"),
        frame_kind=str(body.get("frame_kind") or "general"),
        user_message=str(body.get("user_message") or ""),
        speak_body=str(body.get("speak_body") or ""),
        tuned_thresholds=body.get("tuned_thresholds"),
    )
    return CortexResult(
        runtime_id=EXECUTION_RUNTIME_ID,
        artifact=artifact,
        session_trace=session.export_ledger(),
    )
