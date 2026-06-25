"""CognitiveOrchestrator — perception → action pipeline with governed trace."""

# Mythic: Cognitive Runtime
# Engineering: CognitiveOrchestrator
from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.aaes_os.continuity_execution import attach_continuity_execution, evaluate_continuity_execution
from src.aaes_os.errors import AaesOsValidationError
from src.aaes_os.governed_span import GovernedSpan
from src.aaes_os.invariant_engine import InvariantEngine
from src.aaes_os.models import AuthEnvelope, RuntimeContext, TraceEvent
from src.aaes_os.modules.daniel import ModuleRegistry
from src.aaes_os.pipeline_types import (
    AAESAction,
    AAESContext,
    AAESDecision,
    AAESExecuteResult,
    AAESRequest,
    AAESStep,
    AAESStepType,
    PolicyVerdict,
)
from src.aaes_os.policy_engine import PolicyEngine
from src.aaes_os.trace_bus import TraceBusValidator
from src.aaes_os.trace_store import TraceStore
from src.aaes_os.types import EventType, Role
from src.aaes_os.uls import UnifiedLinguisticSurface


def _default_runtime_context() -> RuntimeContext:
    return RuntimeContext(
        runtime_version="aais-standalone-1.0",
        invariant_version="aaes_os_invariants.v1",
        prompt_hash="prompt_" + "a" * 32,
        decision_policy_hash="policy_" + "b" * 32,
        toolchain_hash="toolchain_" + "c" * 32,
        memory_snapshot_hash="memory_" + "d" * 32,
    )


def _auth(role: Role, actor_id: str) -> AuthEnvelope:
    return AuthEnvelope(role=role, actor_id=actor_id, signature_hash=f"sig_{actor_id}")


class CognitiveOrchestrator:
    """Stub cognitive pipeline wired to TraceBusValidator and GovernedSpan."""

    def __init__(
        self,
        *,
        bus: TraceBusValidator | None = None,
        trace_store: TraceStore | None = None,
        policy_engine: PolicyEngine | None = None,
        invariant_engine: InvariantEngine | None = None,
        uls: UnifiedLinguisticSurface | None = None,
        module_registry: ModuleRegistry | None = None,
        runtime_context: RuntimeContext | None = None,
    ) -> None:
        self._bus = bus or TraceBusValidator()
        self._trace_store = trace_store or TraceStore()
        self._policy = policy_engine or PolicyEngine()
        self._invariants = invariant_engine or InvariantEngine()
        self._uls = uls or UnifiedLinguisticSurface()
        self._modules = module_registry or ModuleRegistry()
        self._runtime_context = runtime_context or _default_runtime_context()

        from governance_gate import require_constitutional_boot

        require_constitutional_boot()

    @property
    def bus(self) -> TraceBusValidator:
        return self._bus

    @property
    def trace_store(self) -> TraceStore:
        return self._trace_store

    def execute(self, request: AAESRequest) -> AAESExecuteResult:
        if not isinstance(request, AAESRequest):
            raise TypeError("request must be AAESRequest")

        trace_id = str(request.trace_id or f"trace_{uuid4().hex}")
        span_id = f"span_{uuid4().hex}"
        ctx = AAESContext(trace_id=trace_id, request=request)

        preflight = self._invariants.check(
            request=request,
            runtime_context=self._runtime_context,
        )
        if not preflight.ok:
            result = AAESExecuteResult(
                trace_id=trace_id,
                span_id=span_id,
                status="blocked",
                steps=tuple(),
                decision=None,
                outcome={},
                explanation=preflight.message or "invariant preflight failed",
                blocked=True,
                block_code=preflight.code,
            )
            self._trace_store.save_execute_result(result)
            return result

        continuity_check = evaluate_continuity_execution(dict(request.metadata.get("args") or {}))
        if continuity_check is not None and not continuity_check.ok:
            result = AAESExecuteResult(
                trace_id=trace_id,
                span_id=span_id,
                status="blocked",
                steps=tuple(),
                decision=None,
                outcome={"continuity_execution": continuity_check.to_dict()},
                explanation="CEC-1 continuity execution preflight failed",
                blocked=True,
                block_code="AAES_CONTINUITY_EXECUTION_BLOCKED",
            )
            self._trace_store.save_execute_result(result)
            return result

        ctx.normalized_input = self._uls.normalize_input(request.prompt)
        ctx.steps.append(
            self._record_step(
                AAESStepType.PERCEPTION,
                "normalized operator input",
                {"length": len(ctx.normalized_input)},
            )
        )

        ctx.steps.append(
            self._record_step(
                AAESStepType.DELIBERATION,
                "classified request intent",
                {"intent": request.metadata.get("intent", "execute")},
            )
        )

        decision = self._policy.evaluate(request, ctx)
        if decision.verdict == PolicyVerdict.BLOCK:
            result = AAESExecuteResult(
                trace_id=trace_id,
                span_id=span_id,
                status="blocked",
                steps=tuple(ctx.steps),
                decision=decision,
                outcome={"policy": decision.payload},
                explanation=decision.reason,
                blocked=True,
                block_code="AAES_POLICY_BLOCKED",
            )
            self._trace_store.save_execute_result(result)
            return result

        ctx.steps.append(
            self._record_step(
                AAESStepType.PLANNING,
                f"policy {decision.verdict.value}",
                {"policy_id": decision.policy_id, "reason": decision.reason},
            )
        )

        span = GovernedSpan(span_id=span_id, runtime_context=self._runtime_context)
        self._bus.register_span(span)
        actor = request.actor_id

        try:
            intent_event = self._emit_event(
                span,
                EventType.INTENT,
                _auth(Role.USER, actor),
                attach_continuity_execution(
                    {
                        "normalized_input": ctx.normalized_input,
                        "perception": ctx.steps[0].payload,
                        "deliberation": ctx.steps[1].payload,
                    },
                    continuity_check,
                ),
            )

            decision_event = self._emit_event(
                span,
                EventType.DECISION,
                _auth(Role.GOVERNOR, "policy-engine"),
                attach_continuity_execution(
                    {
                        "verdict": decision.verdict.value,
                        "reason": decision.reason,
                        "policy_id": decision.policy_id,
                    },
                    continuity_check,
                ),
                parent_event_id=intent_event.event_id,
            )

            module_id = str(request.metadata.get("module_id") or "nexus")
            if module_id == "daniel":
                try:
                    self._modules.get("daniel")
                except KeyError:
                    result = AAESExecuteResult(
                        trace_id=trace_id,
                        span_id=span.span_id,
                        status="blocked",
                        steps=tuple(ctx.steps),
                        decision=decision,
                        outcome={"module_id": module_id, "tsr_owner": "nexus"},
                        explanation="Daniel runtime is shut down; TSR is owned by Nexus",
                        blocked=True,
                        block_code="AAES_DANIEL_RUNTIME_SHUTDOWN",
                    )
                    self._trace_store.save_execute_result(result, bus=self._bus)
                    return result

            action = AAESAction(
                module_id=module_id,
                operation=str(request.metadata.get("operation") or "execute"),
                args=dict(request.metadata.get("args") or {}),
            )
            module_outcome = self._modules.execute(action)

            execution_event = self._emit_event(
                span,
                EventType.EXECUTION,
                _auth(Role.EXECUTOR, "nexus"),
                attach_continuity_execution(
                    {"action": action.module_id, "operation": action.operation},
                    continuity_check,
                ),
                parent_event_id=decision_event.event_id,
            )

            ctx.steps.append(
                self._record_step(
                    AAESStepType.ACTION,
                    "module execution completed",
                    module_outcome,
                )
            )

            explanation = self._uls.summarize_trace(
                steps=ctx.steps,
                events=self._bus.events_for_span(span.span_id),
            )
            ctx.steps.append(
                self._record_step(
                    AAESStepType.EXPLAIN,
                    "trace summarized for operator",
                    {"explanation": explanation},
                )
            )

            result_payload = {
                "rollback_possible": True,
                "outcome": module_outcome,
                "explanation": explanation,
            }
            result_payload = attach_continuity_execution(result_payload, continuity_check)
            post_check = self._invariants.check(
                request=request,
                runtime_context=self._runtime_context,
                steps=ctx.steps,
                pending_event=TraceEvent(
                    span_id=span.span_id,
                    event_type=EventType.RESULT,
                    auth=_auth(Role.EXECUTOR, "nexus"),
                    runtime_context=self._runtime_context,
                    payload=result_payload,
                ),
            )
            if not post_check.ok:
                raise AaesOsValidationError(
                    post_check.code or "AAES_INVARIANT_VIOLATION",
                    post_check.message or "post-action invariant failed",
                )

            self._emit_event(
                span,
                EventType.RESULT,
                _auth(Role.EXECUTOR, "nexus"),
                result_payload,
                parent_event_id=execution_event.event_id,
            )
            span.close()
        except AaesOsValidationError as exc:
            result = AAESExecuteResult(
                trace_id=trace_id,
                span_id=span.span_id,
                status="blocked",
                steps=tuple(ctx.steps),
                decision=decision,
                outcome={},
                explanation=str(exc),
                blocked=True,
                block_code=exc.code,
            )
            self._trace_store.save_execute_result(result, bus=self._bus)
            return result

        status = "warn" if decision.verdict == PolicyVerdict.WARN else "ok"
        result = AAESExecuteResult(
            trace_id=trace_id,
            span_id=span.span_id,
            status=status,
            steps=tuple(ctx.steps),
            decision=decision,
            outcome=module_outcome,
            explanation=explanation,
        )
        self._trace_store.save_execute_result(result, bus=self._bus)
        return result

    def _record_step(
        self,
        step_type: AAESStepType,
        summary: str,
        payload: dict[str, Any],
    ) -> AAESStep:
        return AAESStep(step_type=step_type, summary=summary, payload=payload)

    def _emit_event(
        self,
        span: GovernedSpan,
        event_type: EventType,
        auth: AuthEnvelope,
        payload: dict[str, Any],
        *,
        parent_event_id: str | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            span_id=span.span_id,
            event_type=event_type,
            auth=auth,
            runtime_context=self._runtime_context,
            payload=dict(payload),
            parent_event_id=parent_event_id,
        )
        self._bus.validate_and_append(event, span)
        return event
