"""Tests for the live AAIS blueprint snapshot."""

import unittest

from src.aais_blueprint import build_aais_blueprint


class TestAAISBlueprint(unittest.TestCase):
    """Ensure the blueprint exposes the current system map coherently."""

    def test_build_aais_blueprint_returns_core_sections(self):
        payload = build_aais_blueprint(
            requested_model_mode="laptop",
            active_model_mode="real",
            ai_status="initialized",
        )

        self.assertEqual(payload["id"], "aais.blueprint")
        self.assertEqual(payload["title"], "AAIS Blueprint")
        self.assertGreaterEqual(len(payload["principles"]), 3)
        self.assertTrue(any("organismic" in principle.lower() for principle in payload["principles"]))
        self.assertTrue(any("surface priority does not replace authority" in principle.lower() for principle in payload["principles"]))
        self.assertGreaterEqual(payload["metrics"]["protocol_channel_count"], 1)
        self.assertGreaterEqual(len(payload["providers"]), 1)
        self.assertIn("label", payload["providers"][0])
        self.assertIn("reason", payload["providers"][0])
        self.assertIn("model", payload["providers"][0])
        self.assertIn("activation_hint", payload["providers"][0])
        self.assertIn("module_admission", payload)
        self.assertIn("entries", payload["module_admission"])
        self.assertIn("counts", payload["module_admission"])

        subsystem_ids = {subsystem["id"] for subsystem in payload["subsystems"]}
        self.assertIn("jarvis_shell", subsystem_ids)
        self.assertIn("orchestration_core", subsystem_ids)
        self.assertIn("protocol_provider_fabric", subsystem_ids)
        self.assertIn("universal_language", subsystem_ids)
        self.assertIn("evolve_engine", subsystem_ids)
        self.assertIn("module_governance_protocol", subsystem_ids)

        lineage_ids = {entry["id"] for entry in payload["lineage"]}
        self.assertIn("dashboard_lineage", lineage_ids)
        self.assertIn("guard_lineage", lineage_ids)
        self.assertIn("doctrine_lineage", lineage_ids)

        jarvis_shell = next(
            subsystem for subsystem in payload["subsystems"] if subsystem["id"] == "jarvis_shell"
        )
        self.assertIn("Jarvis keeps routing, state, and safety authority", jarvis_shell["detail"])

        module_statuses = {
            entry["id"]: entry["normalized_status"]
            for entry in payload["module_admission"]["entries"]
        }
        self.assertEqual(module_statuses["phase_gate"], "live")
        self.assertEqual(module_statuses["realtime_event_cause_predictor"], "live")
        self.assertEqual(module_statuses["invariant_engine"], "present but not admitted")
        self.assertEqual(module_statuses["v10_action_engine"], "prototype only")
        self.assertEqual(payload["metrics"]["normalized_module_count"], len(module_statuses))
