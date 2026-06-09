"""Tests for OTEM Level 20 constitutional recovery ceiling."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.immune_hardening import enroll_post_ceiling_hardening, project_hardening_recommendations
from src.otem_ceiling import (
    CEILING_DECISIONS,
    OtemCeilingController,
    OtemCeilingError,
    default_rules_snapshot,
    operator_invoke_requested,
)


class TestOtemCeilingController(unittest.TestCase):
    def setUp(self):
        self._temp_root = Path(tempfile.mkdtemp(prefix="otem-ceiling-"))
        self._runtime_dir = self._temp_root / "runtime"
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._invoke_env = os.environ.get("AAIS_OTEM_CEILING_INVOKE")
        os.environ["AAIS_OTEM_CEILING_INVOKE"] = "1"
        self.controller = OtemCeilingController(runtime_dir=self._runtime_dir)

    def tearDown(self):
        if self._invoke_env is None:
            os.environ.pop("AAIS_OTEM_CEILING_INVOKE", None)
        else:
            os.environ["AAIS_OTEM_CEILING_INVOKE"] = self._invoke_env
        shutil.rmtree(self._temp_root, ignore_errors=True)

    def test_default_rules_snapshot_governed_idle(self):
        rules = default_rules_snapshot()
        self.assertEqual(rules.get("authority_band"), "governed")
        self.assertFalse(rules.get("ceiling_active"))
        self.assertEqual(rules.get("pipeline_state"), "idle")

    def test_operator_invoke_enters_containment(self):
        event = self.controller.evaluate_trigger(
            trigger_type="operator_invoke",
            summary="test invoke",
            scope_id="test-scope",
        )
        self.assertIsNotNone(event)
        status = self.controller.status_for_console()
        self.assertTrue(status.get("containment_mode"))
        self.assertEqual(status.get("authority_band"), "containment")
        self.assertEqual(status.get("pipeline_state"), "diagnostic")
        self.assertIn("operator_invoke", status.get("activation_triggers") or [])

    def test_preview_rejects_unknown_decision(self):
        self.controller.evaluate_trigger(trigger_type="operator_invoke", summary="preview gate")
        with self.assertRaises(OtemCeilingError):
            self.controller.preview_decision("not_a_real_decision")

    def test_preview_and_apply_quarantine_archive(self):
        self.controller.evaluate_trigger(trigger_type="operator_invoke", summary="apply path")
        preview = self.controller.preview_decision(
            "quarantine_archive",
            scope_id="test-scope",
        )
        self.assertEqual(preview.get("decision"), "quarantine_archive")
        self.assertTrue(preview.get("preview_fingerprint"))

        applied = self.controller.apply_decision(
            "quarantine_archive",
            scope_id="test-scope",
            operator_id="operator-test",
        )
        self.assertEqual(applied.get("status"), "applied")
        status = self.controller.status_for_console()
        self.assertFalse(status.get("containment_mode"))
        self.assertEqual(status.get("pipeline_state"), "idle")

    def test_accept_containment_keeps_containment(self):
        self.controller.evaluate_trigger(trigger_type="operator_invoke", summary="accept path")
        self.controller.preview_decision("accept_containment", scope_id="hold-scope")
        applied = self.controller.apply_decision("accept_containment", scope_id="hold-scope")
        self.assertEqual(applied.get("status"), "applied")
        status = self.controller.status_for_console()
        self.assertTrue(status.get("containment_mode"))

    def test_constitutional_amendment_reaches_sovereign(self):
        self.controller.preview_decision("constitutional_amendment", scope_id="amend-scope")
        applied = self.controller.apply_decision(
            "constitutional_amendment",
            scope_id="amend-scope",
            operator_id="operator-amend",
        )
        self.assertEqual(applied.get("status"), "applied")
        status = self.controller.status_for_console()
        self.assertTrue(status.get("ceiling_active"))
        self.assertEqual(status.get("authority_band"), "sovereign")
        self.assertEqual(status.get("numeric_level"), 20)

    def test_all_five_decisions_declared(self):
        self.assertEqual(
            CEILING_DECISIONS,
            frozenset(
                {
                    "rollback_to_checkpoint",
                    "quarantine_archive",
                    "safe_mode_reanchor",
                    "accept_containment",
                    "constitutional_amendment",
                }
            ),
        )


class TestOtemCeilingHelpers(unittest.TestCase):
    def test_operator_invoke_requested_env(self):
        original = os.environ.get("AAIS_OTEM_CEILING_INVOKE")
        os.environ["AAIS_OTEM_CEILING_INVOKE"] = "1"
        try:
            self.assertTrue(operator_invoke_requested())
        finally:
            if original is None:
                os.environ.pop("AAIS_OTEM_CEILING_INVOKE", None)
            else:
                os.environ["AAIS_OTEM_CEILING_INVOKE"] = original

    def test_project_hardening_recommendations(self):
        payload = project_hardening_recommendations({"reason": "unit-test"})
        self.assertIn("recommendations", payload)
        self.assertIsInstance(payload.get("recommendations"), list)

    def test_enroll_post_ceiling_hardening(self):
        payload = enroll_post_ceiling_hardening("quarantine_archive", scope_id="test")
        self.assertEqual(payload.get("decision"), "quarantine_archive")
        self.assertIn("generation", payload)


if __name__ == "__main__":
    unittest.main()
