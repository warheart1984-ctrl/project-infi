"""AAES-OS v1.0 reference implementation tests."""

from __future__ import annotations

import unittest

from src.aaes_os import (
    AaesOsValidationError,
    AuthEnvelope,
    EventType,
    GovernedSpan,
    Role,
    RuntimeContext,
    SpanState,
    TraceBusValidator,
    TraceEvent,
    governed_action,
    reconstruct_span,
)


def _runtime_context() -> RuntimeContext:
    return RuntimeContext(
        runtime_version="aais-standalone-1.0",
        invariant_version="aaes_os_invariants.v1",
        prompt_hash="prompt_" + "a" * 32,
        decision_policy_hash="policy_" + "b" * 32,
        toolchain_hash="toolchain_" + "c" * 32,
        memory_snapshot_hash="memory_" + "d" * 32,
    )


def _auth(role: Role, actor: str) -> AuthEnvelope:
    return AuthEnvelope(role=role, actor_id=actor, signature_hash=f"sig_{actor}")


class AaesOsV1Tests(unittest.TestCase):
    def test_happy_path_governed_action(self):
        bus = TraceBusValidator()
        ctx = _runtime_context()

        span, outcome, result_event = governed_action(
            bus,
            runtime_context=ctx,
            intent_auth=_auth(Role.USER, "operator-1"),
            intent_payload={"action": "deploy", "target": "staging"},
            decision_auth=_auth(Role.GOVERNOR, "governor-1"),
            decision_payload={"decision": "allow"},
            execution_auth=_auth(Role.EXECUTOR, "executor-1"),
            execution_payload={"tool": "make", "args": ["test"]},
            execute_fn=lambda: {"status": "ok"},
        )

        self.assertEqual(outcome, {"status": "ok"})
        self.assertEqual(span.state, SpanState.CLOSED)
        self.assertEqual(result_event.event_type, EventType.RESULT)
        self.assertEqual(len(bus.events_for_span(span.span_id)), 4)

        rebuilt = reconstruct_span(bus, span.span_id)
        self.assertEqual(rebuilt.state, SpanState.CLOSED)
        self.assertEqual(len(rebuilt.events), 4)

    def test_rejects_bad_transition(self):
        bus = TraceBusValidator()
        ctx = _runtime_context()
        span = GovernedSpan(runtime_context=ctx)
        bus.register_span(span)

        intent = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.INTENT,
            auth=_auth(Role.USER, "operator-1"),
            runtime_context=ctx,
            payload={"action": "x"},
        )
        bus.validate_and_append(intent, span)

        execution = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.EXECUTION,
            auth=_auth(Role.EXECUTOR, "executor-1"),
            runtime_context=ctx,
            payload={"tool": "x"},
            parent_event_id=intent.event_id,
        )
        with self.assertRaises(AaesOsValidationError) as ctx_err:
            bus.validate_and_append(execution, span)
        self.assertEqual(ctx_err.exception.code, "AAES_SPAN_STATE_INVALID")

    def test_rejects_missing_auth(self):
        bus = TraceBusValidator()
        ctx = _runtime_context()
        span = GovernedSpan(runtime_context=ctx)
        bus.register_span(span)

        bad_auth = AuthEnvelope(role=Role.USER, actor_id="", signature_hash="sig")
        event = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.INTENT,
            auth=bad_auth,
            runtime_context=ctx,
            payload={},
        )
        with self.assertRaises(AaesOsValidationError) as ctx_err:
            bus.validate_and_append(event, span)
        self.assertEqual(ctx_err.exception.code, "AAES_AUTH_MISSING")

    def test_rejects_causal_violation(self):
        bus = TraceBusValidator()
        ctx = _runtime_context()
        span = GovernedSpan(runtime_context=ctx)
        bus.register_span(span)

        intent = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.INTENT,
            auth=_auth(Role.RUNTIME, "runtime-1"),
            runtime_context=ctx,
            payload={"action": "sync"},
        )
        bus.validate_and_append(intent, span)

        decision = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.DECISION,
            auth=_auth(Role.GOVERNOR, "governor-1"),
            runtime_context=ctx,
            payload={"decision": "allow"},
            parent_event_id=intent.event_id,
        )
        bus.validate_and_append(decision, span)

        bad_result = TraceEvent(
            span_id=span.span_id,
            event_type=EventType.RESULT,
            auth=_auth(Role.EXECUTOR, "executor-1"),
            runtime_context=ctx,
            payload={"rollback_possible": False},
            parent_event_id=decision.event_id,
        )
        with self.assertRaises(AaesOsValidationError) as ctx_err:
            bus.validate_and_append(bad_result, span)
        self.assertIn(
            ctx_err.exception.code,
            {"AAES_SPAN_STATE_INVALID", "AAES_CAUSAL_VIOLATION"},
        )


if __name__ == "__main__":
    unittest.main()
