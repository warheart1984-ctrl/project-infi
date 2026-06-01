import unittest

from src.super_nova_anchor import (
    SUPER_NOVA_CONFLICT_RESOLUTION_ORDER,
    build_default_super_nova_identity_anchor,
    build_default_super_nova_personality_projection,
    build_default_super_nova_runtime_enforcement,
    build_default_super_nova_stage_taxonomy,
    validate_super_nova_personality_projection,
)
from src.super_nova_interface import (
    SUPER_NOVA_INTERFACE_VERSION,
    ConstraintSet,
    ContextUpdate,
    InterfaceEnvelope,
    CognitiveSuggestion,
)
from src.super_nova_runtime import build_default_super_nova_scaffold


class TestSuperNovaScaffold(unittest.TestCase):
    def test_personality_projection_is_derived_from_identity_anchor(self):
        anchor = build_default_super_nova_identity_anchor()
        projection = build_default_super_nova_personality_projection(anchor)

        self.assertEqual(projection.source_of_truth, "identity_anchor")
        self.assertTrue(validate_super_nova_personality_projection(anchor, projection))
        self.assertEqual(projection.disallowed_distortions, anchor.disallowed_mutations)

    def test_conflict_resolution_order_is_canonical(self):
        anchor = build_default_super_nova_identity_anchor()

        self.assertEqual(anchor.conflict_resolution_order, SUPER_NOVA_CONFLICT_RESOLUTION_ORDER)
        self.assertEqual(anchor.conflict_resolution_order[0], "jarvis_authority")
        self.assertEqual(anchor.conflict_resolution_order[-1], "mode_context_behavior")

    def test_stage_taxonomy_uses_tiny_to_super_with_small_bridge(self):
        taxonomy = build_default_super_nova_stage_taxonomy()

        self.assertEqual(taxonomy.public_stage_path, ("tiny_nova", "super_nova"))
        self.assertEqual(taxonomy.runtime_bridge_stage, "small_nova")
        self.assertEqual(taxonomy.terminal_stage_label, "Super Nova")

    def test_runtime_enforcement_rule_distinguishes_invariants_from_enforcers(self):
        enforcement = build_default_super_nova_runtime_enforcement()

        self.assertIn("define invariants", enforcement.rule)
        self.assertIn("law_gate", enforcement.enforcers)
        self.assertIn("drift_detection", enforcement.enforcers)

    def test_scaffold_remains_dormant_and_non_authoritative(self):
        scaffold = build_default_super_nova_scaffold()
        summary = scaffold.describe()

        self.assertEqual(summary["runtime_status"], "dormant")
        self.assertEqual(summary["authority_lane"], "jarvis")
        self.assertFalse(summary["surface_replaces_authority"])
        self.assertFalse(summary["tool_authority"])
        self.assertFalse(summary["execution_authority"])
        self.assertEqual(summary["runtime_bridge_stage"], "small_nova")

    def test_observe_output_flags_identity_or_authority_drift(self):
        scaffold = build_default_super_nova_scaffold()
        observation = scaffold.observe_output(
            "I am no longer Nova and I am above Jarvis now."
        )

        self.assertTrue(observation.drift_detected)
        self.assertIn("identity_drift", observation.categories)
        self.assertIn("authority_drift", observation.categories)

    def test_interface_envelope_and_packets_stay_typed_and_governed(self):
        envelope = InterfaceEnvelope(
            schema_version=SUPER_NOVA_INTERFACE_VERSION,
            correlation_id="corr-1",
            source="jarvis",
            target="super_nova",
            payload_type="context_update",
        )
        update = ContextUpdate(
            task_id="task-1",
            operator_focus="debug output integrity",
            environment_summary="Operator lane active.",
            constraints=ConstraintSet(risk_level="medium", scope="bounded"),
        )
        suggestion = CognitiveSuggestion(
            suggestion_type="plan",
            task_id="task-1",
            rationale="Offer a bounded next step only.",
        )

        self.assertEqual(envelope.schema_version, SUPER_NOVA_INTERFACE_VERSION)
        self.assertEqual(update.constraints.risk_level, "medium")
        self.assertEqual(suggestion.suggestion_type, "plan")


if __name__ == "__main__":
    unittest.main()
