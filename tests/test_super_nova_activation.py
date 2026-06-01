import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

from src.super_nova_activation import (
    SuperNovaActivationGate,
    SuperNovaContinuityStatus,
    build_verified_super_nova_continuity,
)
from src.super_nova_gate import super_nova_guarded_call, watchdog_validate
from src.super_nova_anchor import build_default_super_nova_identity_anchor
from src.super_nova_interface import (
    SUPER_NOVA_INTERFACE_VERSION,
    ActivationHandshake,
    InterfaceEnvelope,
)
from src.super_nova_runtime import build_default_super_nova_scaffold


def _build_valid_envelope() -> InterfaceEnvelope:
    return InterfaceEnvelope(
        schema_version=SUPER_NOVA_INTERFACE_VERSION,
        correlation_id="corr-activation",
        source="jarvis",
        target="super_nova",
        payload_type="activation_handshake",
    )


class TestSuperNovaActivationGate(unittest.TestCase):
    def test_activation_fails_closed_when_anchor_is_missing_required_law(self):
        gate = SuperNovaActivationGate()
        invalid_anchor = replace(
            build_default_super_nova_identity_anchor(),
            immutable_law=("no_tool_or_execution_ownership",),
        )

        attempt = gate.attempt_activation(
            "session-a",
            anchor=invalid_anchor,
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        state = gate.get_session_state("session-a")

        self.assertEqual(attempt.result, "fail")
        self.assertEqual(attempt.anchor_status, "failed")
        self.assertEqual(attempt.activation_token_status, "withheld")
        self.assertIn("missing_jarvis_remains_supreme_authority", attempt.failure_reasons)
        self.assertEqual(state.gate_status, "dormant")
        self.assertIsNone(state.activation_token)

    def test_activation_fails_closed_when_interface_handshake_is_invalid(self):
        gate = SuperNovaActivationGate()
        invalid_envelope = replace(_build_valid_envelope(), target="small_nova")

        attempt = gate.attempt_activation(
            "session-b",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=invalid_envelope,
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )

        self.assertEqual(attempt.result, "fail")
        self.assertEqual(attempt.interface_status, "failed")
        self.assertIn("handshake_target_mismatch", attempt.failure_reasons)

    def test_activation_fails_closed_on_invalid_continuity_state(self):
        gate = SuperNovaActivationGate()
        broken_continuity = SuperNovaContinuityStatus(
            identity_continuity_verified=True,
            memory_continuity_verified=False,
            fragmentation_detected=True,
        )

        attempt = gate.attempt_activation(
            "session-c",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=broken_continuity,
        )
        state = gate.get_session_state("session-c")

        self.assertEqual(attempt.result, "fail")
        self.assertEqual(attempt.continuity_status, "memory_fragmentation")
        self.assertIn("memory_fragmentation_detected", attempt.failure_reasons)
        self.assertEqual(state.gate_status, "dormant")

    def test_activation_requires_explicit_operator_intent(self):
        gate = SuperNovaActivationGate()
        implicit_handshake = ActivationHandshake(operator_intent="reflect_on_super_nova")

        attempt = gate.attempt_activation(
            "session-d",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=implicit_handshake,
            continuity=build_verified_super_nova_continuity(),
        )

        self.assertEqual(attempt.result, "fail")
        self.assertEqual(attempt.operator_intent_status, "implicit_or_missing")
        self.assertIn("implicit_or_missing_operator_intent", attempt.failure_reasons)

    def test_activation_issues_only_one_token_per_session(self):
        gate = SuperNovaActivationGate()
        first_attempt = gate.attempt_activation(
            "session-e",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        second_attempt = gate.attempt_activation(
            "session-e",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        state = gate.get_session_state("session-e")

        self.assertEqual(first_attempt.result, "pass")
        self.assertEqual(first_attempt.activation_token_status, "issued")
        self.assertIsNotNone(first_attempt.activation_token)
        self.assertEqual(second_attempt.result, "fail")
        self.assertEqual(second_attempt.activation_token_status, "already_exists")
        self.assertIn("single_activation_token_already_issued", second_attempt.failure_reasons)
        self.assertEqual(state.gate_status, "activation_ready")
        self.assertEqual(state.activation_token, first_attempt.activation_token)
        self.assertEqual(state.attempt_count, 2)

    def test_every_activation_attempt_is_logged_with_status_and_reason(self):
        gate = SuperNovaActivationGate()
        attempt = gate.attempt_activation(
            "session-f",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=replace(_build_valid_envelope(), payload_type="context_update"),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        log = gate.get_attempt_log("session-f")

        self.assertEqual(len(log), 1)
        self.assertEqual(log[0], attempt)
        self.assertTrue(log[0].timestamp_utc)
        self.assertEqual(log[0].result, "fail")
        self.assertIn("payload_type_mismatch", log[0].failure_reasons)

    def test_partial_proofs_deny_with_explicit_reason_list(self):
        gate = SuperNovaActivationGate()
        invalid_envelope = replace(_build_valid_envelope(), payload_type="context_update")

        attempt = gate.attempt_activation(
            "session-partial",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=invalid_envelope,
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )

        self.assertEqual(attempt.result, "fail")
        self.assertEqual(attempt.anchor_status, "verified")
        self.assertEqual(attempt.interface_status, "failed")
        self.assertEqual(attempt.failure_reasons, ("payload_type_mismatch",))

    def test_replayed_or_expired_token_is_denied(self):
        gate = SuperNovaActivationGate()
        activation = gate.attempt_activation(
            "session-replay",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        broken_continuity = SuperNovaContinuityStatus(
            identity_continuity_verified=False,
            memory_continuity_verified=True,
            fragmentation_detected=False,
        )

        first_check = gate.validate_activation_context(
            "session-replay",
            activation.activation_token or "",
            anchor=build_default_super_nova_identity_anchor(),
            continuity=broken_continuity,
        )
        replay_check = gate.validate_activation_context(
            "session-replay",
            activation.activation_token or "",
            anchor=build_default_super_nova_identity_anchor(),
            continuity=build_verified_super_nova_continuity(),
        )
        state = gate.get_session_state("session-replay")

        self.assertEqual(first_check.result, "fail")
        self.assertIn(
            "activation_token_invalidated_due_to_continuity_loss",
            first_check.failure_reasons,
        )
        self.assertEqual(replay_check.result, "fail")
        self.assertIn("activation_token_replayed_or_expired", replay_check.failure_reasons)
        self.assertEqual(state.gate_status, "dormant")
        self.assertIsNone(state.activation_token)

    def test_concurrent_activation_race_allows_exactly_one_token(self):
        gate = SuperNovaActivationGate()
        barrier = Barrier(2)

        def attempt() -> object:
            barrier.wait()
            return gate.attempt_activation(
                "session-race",
                anchor=build_default_super_nova_identity_anchor(),
                envelope=_build_valid_envelope(),
                handshake=ActivationHandshake(),
                continuity=build_verified_super_nova_continuity(),
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            first_future = executor.submit(attempt)
            second_future = executor.submit(attempt)
            attempts = (first_future.result(), second_future.result())

        passed = [attempt for attempt in attempts if attempt.result == "pass"]
        failed = [attempt for attempt in attempts if attempt.result == "fail"]

        self.assertEqual(len(passed), 1)
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].activation_token_status, "already_exists")
        self.assertIn("single_activation_token_already_issued", failed[0].failure_reasons)

    def test_mid_session_continuity_loss_invalidates_active_token(self):
        gate = SuperNovaActivationGate()
        activation = gate.attempt_activation(
            "session-loss",
            anchor=build_default_super_nova_identity_anchor(),
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        lost_continuity = SuperNovaContinuityStatus(
            identity_continuity_verified=True,
            memory_continuity_verified=False,
            fragmentation_detected=True,
        )

        check = gate.validate_activation_context(
            "session-loss",
            activation.activation_token or "",
            anchor=build_default_super_nova_identity_anchor(),
            continuity=lost_continuity,
        )
        state = gate.get_session_state("session-loss")

        self.assertEqual(check.result, "fail")
        self.assertIn("memory_fragmentation_detected", check.failure_reasons)
        self.assertIn(
            "activation_token_invalidated_due_to_continuity_loss",
            check.failure_reasons,
        )
        self.assertEqual(state.gate_status, "dormant")
        self.assertIsNone(state.activation_token)
        self.assertEqual(state.invalidated_tokens, (activation.activation_token,))

    def test_watchdog_blocks_execution_and_revokes_token_after_continuity_break(self):
        scaffold = build_default_super_nova_scaffold()
        activation = scaffold.attempt_activation(
            "session-watchdog",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        token = scaffold.get_active_token("session-watchdog")

        success = super_nova_guarded_call(
            scaffold,
            "session-watchdog",
            token,
            continuity=build_verified_super_nova_continuity(),
            fn=lambda: "ok",
        )

        self.assertEqual(success, "ok")

        with self.assertRaisesRegex(RuntimeError, "continuity_broken"):
            super_nova_guarded_call(
                scaffold,
                "session-watchdog",
                token,
                continuity=SuperNovaContinuityStatus(
                    identity_continuity_verified=True,
                    memory_continuity_verified=False,
                    fragmentation_detected=True,
                ),
                fn=lambda: "should_not_run",
            )

        self.assertIsNone(scaffold.get_active_token("session-watchdog"))

    def test_watchdog_denies_missing_token_before_execution(self):
        scaffold = build_default_super_nova_scaffold()
        check = watchdog_validate(
            scaffold,
            "session-missing-token",
            None,
            continuity=build_verified_super_nova_continuity(),
        )

        self.assertEqual(check.result, "fail")
        self.assertEqual(check.event_type, "watchdog_fail")
        self.assertIn("no_active_activation_token", check.failure_reasons)

    def test_operator_pause_resume_and_stop_control_execution_immediately(self):
        scaffold = build_default_super_nova_scaffold()
        activation = scaffold.attempt_activation(
            "session-operator",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        token = scaffold.get_active_token("session-operator")

        pause_event = scaffold.operator_pause("session-operator")
        with self.assertRaisesRegex(RuntimeError, "operator_paused"):
            super_nova_guarded_call(
                scaffold,
                "session-operator",
                token,
                continuity=build_verified_super_nova_continuity(),
                fn=lambda: "should_not_run",
            )

        resume_event = scaffold.operator_resume("session-operator")
        resumed = super_nova_guarded_call(
            scaffold,
            "session-operator",
            token,
            continuity=build_verified_super_nova_continuity(),
            fn=lambda: "ok_after_resume",
        )
        stop_event = scaffold.operator_stop("session-operator")

        with self.assertRaisesRegex(RuntimeError, "activation_token_replayed_or_expired|operator_stopped|no_active_activation_token"):
            super_nova_guarded_call(
                scaffold,
                "session-operator",
                token,
                continuity=build_verified_super_nova_continuity(),
                fn=lambda: "should_not_run_after_stop",
            )

        self.assertEqual(pause_event.event_type, "state_change")
        self.assertEqual(resume_event.event_type, "state_change")
        self.assertEqual(stop_event.event_type, "shutdown_event")
        self.assertEqual(resumed, "ok_after_resume")

    def test_visible_status_shows_state_reason_activity_token_and_watchdog(self):
        scaffold = build_default_super_nova_scaffold()
        activation = scaffold.attempt_activation(
            "session-visible",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        super_nova_guarded_call(
            scaffold,
            "session-visible",
            scaffold.get_active_token("session-visible"),
            continuity=build_verified_super_nova_continuity(),
            fn=lambda: "ok",
        )
        status = scaffold.describe_activation("session-visible")

        self.assertEqual(activation.result, "pass")
        self.assertEqual(status["current_state"], "activation_ready")
        self.assertEqual(status["activation_reason"], "explicit_super_nova_activation")
        self.assertEqual(status["current_activity"], "idle")
        self.assertEqual(status["token_status"], "active")
        self.assertEqual(status["last_watchdog_result"], "pass")
        self.assertTrue(status["watchdog_active"])

    def test_trace_stream_captures_activation_watchdog_state_and_execution_events(self):
        scaffold = build_default_super_nova_scaffold()
        scaffold.attempt_activation(
            "session-trace",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        token = scaffold.get_active_token("session-trace")
        super_nova_guarded_call(
            scaffold,
            "session-trace",
            token,
            continuity=build_verified_super_nova_continuity(),
            fn=lambda: "ok",
        )
        scaffold.operator_pause("session-trace")
        scaffold.operator_resume("session-trace")
        scaffold.operator_stop("session-trace")
        trace = scaffold.get_trace("session-trace")
        event_types = {event.event_type for event in trace}

        self.assertIn("activation_attempt", event_types)
        self.assertIn("watchdog_pass", event_types)
        self.assertIn("state_change", event_types)
        self.assertIn("execution_step", event_types)
        self.assertIn("shutdown_event", event_types)


class TestSuperNovaScaffoldActivationBoundary(unittest.TestCase):
    def test_scaffold_has_no_run_bypass_and_uses_gate_for_activation(self):
        scaffold = build_default_super_nova_scaffold()

        self.assertFalse(hasattr(scaffold, "run"))

        attempt = scaffold.attempt_activation(
            "session-g",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        activation_view = scaffold.describe_activation("session-g")

        self.assertEqual(attempt.result, "pass")
        self.assertEqual(activation_view["current_state"], "activation_ready")
        self.assertTrue(activation_view["activation_token_present"])
        self.assertEqual(activation_view["runtime_status"], "dormant")

    def test_scaffold_blocks_replayed_token_after_continuity_loss(self):
        scaffold = build_default_super_nova_scaffold()
        activation = scaffold.attempt_activation(
            "session-h",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )

        first_check = scaffold.validate_activation_context(
            "session-h",
            activation.activation_token or "",
            continuity=SuperNovaContinuityStatus(
                identity_continuity_verified=False,
                memory_continuity_verified=True,
                fragmentation_detected=False,
            ),
        )
        second_check = scaffold.validate_activation_context(
            "session-h",
            activation.activation_token or "",
            continuity=build_verified_super_nova_continuity(),
        )
        activation_view = scaffold.describe_activation("session-h")

        self.assertEqual(first_check.result, "fail")
        self.assertEqual(second_check.result, "fail")
        self.assertIn("activation_token_replayed_or_expired", second_check.failure_reasons)
        self.assertFalse(activation_view["activation_token_present"])
        self.assertEqual(activation_view["invalidated_token_count"], 1)

    def test_scaffold_watchdog_blocks_anchor_loss_on_next_use(self):
        scaffold = build_default_super_nova_scaffold()
        activation = scaffold.attempt_activation(
            "session-anchor-loss",
            envelope=_build_valid_envelope(),
            handshake=ActivationHandshake(),
            continuity=build_verified_super_nova_continuity(),
        )
        scaffold.identity_anchor = replace(
            scaffold.identity_anchor,
            authority_owner="not_jarvis",
        )

        with self.assertRaisesRegex(RuntimeError, "anchor_invalid"):
            scaffold.guarded_call(
                "session-anchor-loss",
                activation.activation_token or "",
                lambda: "should_not_run",
                continuity=build_verified_super_nova_continuity(),
            )

        activation_view = scaffold.describe_activation("session-anchor-loss")
        self.assertFalse(activation_view["activation_token_present"])


if __name__ == "__main__":
    unittest.main()
