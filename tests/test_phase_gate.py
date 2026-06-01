"""Tests for the Jarvis phase gate admission controller."""

import unittest

from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    IllegalPhaseTransitionError,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    assert_routable,
    can_demote_component,
    can_promote_component,
    demote_component,
    get_component,
    is_executable,
    is_routable,
    list_components,
    list_phase_events,
    promote_component,
    register_component,
    reset_registry,
)


class TestPhaseGate(unittest.TestCase):
    """Ensure phase admission stays explicit, auditable, and fail-closed."""

    def setUp(self):
        reset_registry()

    def _component(
        self,
        component_id: str,
        *,
        phase: Phase = Phase.CONCEPT,
        allowed_contexts: list[str] | None = None,
    ) -> GovernedComponent:
        return GovernedComponent(
            component_id=component_id,
            name="StoryForge Presentation",
            component_type="workflow",
            phase=phase,
            allowed_contexts=list(allowed_contexts or []),
            notes="Governed component for tests.",
        )

    def test_register_component_stores_valid_component(self):
        register_component(self._component("storyforge.llm_presentation"))

        component = get_component("storyforge.llm_presentation")
        components = list_components()

        self.assertEqual(component.phase, Phase.CONCEPT)
        self.assertEqual(component.allowed_contexts, [])
        self.assertEqual(component.history[0].from_phase, None)
        self.assertEqual(component.history[0].to_phase, Phase.CONCEPT.value)
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].component_id, "storyforge.llm_presentation")

    def test_register_component_rejects_duplicate_id(self):
        register_component(self._component("runtime.bridge"))

        with self.assertRaises(PhaseGateError):
            register_component(self._component("runtime.bridge"))

    def test_get_component_raises_for_unknown_id(self):
        with self.assertRaises(ComponentNotRegisteredError):
            get_component("missing.component")

    def test_concept_phase_is_blocked_everywhere(self):
        register_component(self._component("latent.module", phase=Phase.CONCEPT))

        self.assertFalse(is_executable("latent.module", "live_runtime"))
        self.assertFalse(is_executable("latent.module", "sandbox"))

        with self.assertRaises(PhaseViolationError):
            assert_executable("latent.module", "live_runtime")

    def test_prototype_phase_is_executable_only_in_sandbox_and_test(self):
        register_component(self._component("proto.module", phase=Phase.PROTOTYPE))

        self.assertTrue(is_executable("proto.module", "sandbox"))
        self.assertTrue(is_executable("proto.module", "test_harness"))
        self.assertFalse(is_executable("proto.module", "live_runtime"))
        self.assertFalse(is_executable("proto.module", "operator_runtime"))

    def test_validated_phase_is_allowed_only_in_guarded_contexts(self):
        register_component(self._component("validated.module", phase=Phase.VALIDATED))

        self.assertTrue(is_executable("validated.module", "operator_runtime"))
        self.assertTrue(is_executable("validated.module", "test_harness"))
        self.assertFalse(is_executable("validated.module", "live_runtime"))
        self.assertFalse(is_executable("validated.module", "sandbox"))

    def test_active_phase_is_allowed_in_live_runtime(self):
        register_component(self._component("active.module", phase=Phase.ACTIVE))

        self.assertTrue(is_executable("active.module", "live_runtime"))
        self.assertTrue(is_executable("active.module", "operator_runtime"))

    def test_active_phase_can_use_explicit_dreamspace_runtime_context(self):
        register_component(
            self._component(
                "dreamspace.reader",
                phase=Phase.ACTIVE,
                allowed_contexts=["dreamspace_runtime"],
            )
        )

        self.assertTrue(is_executable("dreamspace.reader", "dreamspace_runtime"))
        self.assertFalse(is_executable("dreamspace.reader", "operator_runtime"))

    def test_routing_blocks_prototype_and_allows_validated_and_active_in_supported_contexts(self):
        register_component(self._component("proto.route", phase=Phase.PROTOTYPE))
        register_component(self._component("validated.route", phase=Phase.VALIDATED))
        register_component(self._component("active.route", phase=Phase.ACTIVE))

        self.assertFalse(is_routable("proto.route", "sandbox"))
        self.assertTrue(is_routable("validated.route", "operator_runtime"))
        self.assertFalse(is_routable("validated.route", "live_runtime"))
        self.assertTrue(is_routable("active.route", "live_runtime"))

    def test_legal_promotion_succeeds_and_records_history(self):
        register_component(self._component("promotion.target"))

        self.assertTrue(can_promote_component("promotion.target", Phase.PROTOTYPE))
        promote_component(
            "promotion.target",
            Phase.PROTOTYPE,
            reason="Initial sandbox build is ready.",
            evidence="pytest tests/test_phase_gate.py -q",
            actor="operator",
        )

        component = get_component("promotion.target")
        transition = component.history[-1]

        self.assertEqual(component.phase, Phase.PROTOTYPE)
        self.assertEqual(component.allowed_contexts, ["sandbox", "test_harness"])
        self.assertEqual(transition.from_phase, Phase.CONCEPT.value)
        self.assertEqual(transition.to_phase, Phase.PROTOTYPE.value)
        self.assertEqual(transition.reason, "Initial sandbox build is ready.")
        self.assertEqual(transition.evidence, "pytest tests/test_phase_gate.py -q")
        self.assertEqual(transition.actor, "operator")

    def test_illegal_promotion_skip_fails(self):
        register_component(self._component("illegal.skip"))

        self.assertFalse(can_promote_component("illegal.skip", Phase.VALIDATED))
        with self.assertRaises(IllegalPhaseTransitionError):
            promote_component("illegal.skip", Phase.VALIDATED, reason="Skipping ahead is not allowed.")

    def test_legal_demotion_succeeds_and_records_history(self):
        register_component(self._component("rollback.target", phase=Phase.ACTIVE))

        self.assertTrue(can_demote_component("rollback.target", Phase.VALIDATED))
        demote_component(
            "rollback.target",
            Phase.VALIDATED,
            reason="Seam instability detected in live runtime.",
            evidence="runtime seam detector",
            actor="phase_guard",
        )

        component = get_component("rollback.target")
        transition = component.history[-1]

        self.assertEqual(component.phase, Phase.VALIDATED)
        self.assertEqual(component.allowed_contexts, ["operator_runtime", "test_harness"])
        self.assertEqual(transition.from_phase, Phase.ACTIVE.value)
        self.assertEqual(transition.to_phase, Phase.VALIDATED.value)
        self.assertEqual(transition.reason, "Seam instability detected in live runtime.")

    def test_invalid_demotion_fails(self):
        register_component(self._component("invalid.rollback", phase=Phase.PROTOTYPE))

        self.assertFalse(can_demote_component("invalid.rollback", Phase.ACTIVE))
        with self.assertRaises(IllegalPhaseTransitionError):
            demote_component("invalid.rollback", Phase.ACTIVE, reason="Cannot demote upward.")

    def test_blocked_execution_fails_closed_and_logs_event(self):
        register_component(self._component("blocked.exec", phase=Phase.VALIDATED))

        with self.assertRaises(PhaseViolationError):
            assert_executable("blocked.exec", "live_runtime")

        events = list_phase_events()
        self.assertEqual(events[-1]["event"], "phase_block")
        self.assertEqual(events[-1]["component_id"], "blocked.exec")
        self.assertEqual(events[-1]["check"], "execution")

    def test_blocked_routing_fails_closed_and_logs_event(self):
        register_component(self._component("blocked.route", phase=Phase.PROTOTYPE))

        with self.assertRaises(PhaseViolationError):
            assert_routable("blocked.route", "sandbox")

        events = list_phase_events()
        self.assertEqual(events[-1]["event"], "phase_block")
        self.assertEqual(events[-1]["component_id"], "blocked.route")
        self.assertEqual(events[-1]["check"], "routing")


if __name__ == "__main__":
    unittest.main()
