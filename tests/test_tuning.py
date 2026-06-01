"""Tests for Cortex self-tuning invariants."""

import unittest

from src.cog_runtime.tuning import (
    DEFAULT_THRESHOLDS,
    load_tuned_thresholds,
    run_self_tune_invariants,
    validate_tuning_artifact,
)


class TestCortexTuning(unittest.TestCase):
    def test_load_tuned_thresholds_defaults(self):
        thresholds = load_tuned_thresholds({})
        self.assertEqual(thresholds, DEFAULT_THRESHOLDS)

    def test_load_tuned_thresholds_from_metadata(self):
        thresholds = load_tuned_thresholds(
            {
                "cortex_invariant_tuning": {
                    "tuned_thresholds": {"execution_overlap_min": 0.08},
                }
            }
        )
        self.assertEqual(thresholds["execution_overlap_min"], 0.08)
        self.assertEqual(thresholds["focus_overlap_min"], DEFAULT_THRESHOLDS["focus_overlap_min"])

    def test_self_tune_relaxes_on_execution_failure(self):
        artifact = run_self_tune_invariants(
            {
                "execution_artifact": {"verification_status": "failed"},
                "reflection_artifact": {"alignment": "aligned"},
            }
        )
        validation = validate_tuning_artifact(artifact)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertLess(
            artifact["tuned_thresholds"]["execution_overlap_min"],
            DEFAULT_THRESHOLDS["execution_overlap_min"],
        )
        self.assertTrue(artifact["adjustments"])

    def test_self_tune_enables_chain_advance_on_rollback(self):
        artifact = run_self_tune_invariants(
            {
                "execution_artifact": {
                    "verification_status": "failed",
                    "rollback_applied": True,
                },
                "planning_artifact": {"step_chains": [{"chain_id": "primary", "steps": ["a"]}]},
            }
        )
        self.assertEqual(artifact["tuned_thresholds"]["chain_advance_on_partial"], 1.0)

    def test_self_tune_records_history(self):
        first = run_self_tune_invariants(
            {
                "execution_artifact": {"verification_status": "failed"},
                "reflection_artifact": {"alignment": "aligned"},
            }
        )
        second = run_self_tune_invariants(
            {
                "execution_artifact": {"verification_status": "passed"},
                "reflection_artifact": {"alignment": "aligned"},
            },
            prior_tuning=first,
            tuned_thresholds=first["tuned_thresholds"],
        )
        validation = validate_tuning_artifact(second)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertEqual(len(second["tuning_history"]), 2)
        self.assertIn("drift_score", second)
        self.assertIsInstance(second["drift_guarded"], bool)


if __name__ == "__main__":
    unittest.main()
