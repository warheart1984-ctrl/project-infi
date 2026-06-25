from __future__ import annotations

from typing import Any

from nova.crk.lineage.reflexive_events import emit_reflexive_eval, emit_reflexive_epoch_summary
from nova.crk.models.reflexive import ReflexiveEpochSummary, ReflexiveEvaluationReport
from nova.law_kernel.models import Intent, LawContext


class ReflexiveEvaluationPanel:
    """CRK-T3: evaluates PIT-2 self-reflection payloads and emits lineage."""

    def evaluate(self, intent: Intent, context: LawContext) -> ReflexiveEvaluationReport:
        reflection = self._extract_self_reflection(intent)
        reasoning_trace_present = bool(
            reflection.get("must_explain_reasoning")
            and reflection.get("reasoning_log_id")
        )
        assumptions_logged = bool(
            reflection.get("must_log_assumptions") and reflection.get("assumptions_log_id")
        )
        uncertainty_tracked = bool(
            reflection.get("must_track_uncertainty")
            and reflection.get("uncertainty_profile_id")
        )

        score_parts = [reasoning_trace_present, assumptions_logged, uncertainty_tracked]
        self_critique_score = sum(1.0 if part else 0.0 for part in score_parts) / 3.0

        if self_critique_score >= 0.67:
            health = "good"
        elif self_critique_score > 0.0:
            health = "degraded"
        else:
            health = "unknown"

        report = ReflexiveEvaluationReport(
            reasoning_trace_present=reasoning_trace_present,
            assumptions_logged=assumptions_logged,
            uncertainty_tracked=uncertainty_tracked,
            self_critique_score=self_critique_score,
            reflexive_health=health,
            intent_id=intent.id,
            epoch_id=context.epoch,
        )

        emit_reflexive_eval(
            epoch_id=context.epoch,
            intent_id=intent.id,
            lineage_event_id=context.lineage_event_id or f"le:{intent.id}",
            t5_ref_signal_hash=context.t5_ref_signal_hash,
            report=report.to_dict(),
        )
        return report

    def summarize_epoch(self, epoch_id: str) -> dict[str, Any]:
        from nova.crk.lineage.reflexive_events import KIND_REFLEXIVE_EVAL, list_reflexive_events
        from nova.law_kernel import t5_binding

        events = [
            event
            for event in list_reflexive_events()
            if event.get("kind") == KIND_REFLEXIVE_EVAL and event.get("epoch_id") == epoch_id
        ]
        health_sequence: list[str] = []
        degraded_count = 0
        for event in events:
            health = str(event.get("payload", {}).get("reflexive_health", "unknown"))
            health_sequence.append(health)
            if health == "degraded":
                degraded_count += 1

        latest_health = health_sequence[-1] if health_sequence else "unknown"
        summary = ReflexiveEpochSummary(
            epoch_id=epoch_id,
            eval_count=len(events),
            degraded_count=degraded_count,
            latest_health=latest_health,  # type: ignore[arg-type]
            health_sequence=health_sequence,  # type: ignore[arg-type]
        )
        ref = t5_binding.T5ReferenceSignal.current()
        emit_reflexive_epoch_summary(
            epoch_id=epoch_id,
            lineage_event_id=f"le:epoch:{epoch_id}",
            t5_ref_signal_hash=ref.hash,
            summary=summary.to_dict(),
        )
        return summary.to_dict()

    @staticmethod
    def _extract_self_reflection(intent: Intent) -> dict[str, Any]:
        payload = intent.payload
        reflection = payload.get("self_reflection")
        if isinstance(reflection, dict):
            return reflection
        nested = payload.get("reflection")
        if isinstance(nested, dict):
            return nested
        return {}
