"""Consentful inference gate tests (INV-7)."""

from __future__ import annotations

import unittest

from src.cog_runtime.deliberation import run_deliberation_turn
from src.cog_runtime.formal.consentful_inference import evaluate_consentful_inference


class TestConsentfulInference(unittest.TestCase):
    def test_passes_when_no_provisional_upgrade(self):
        evaluation = evaluate_consentful_inference(
            {"chosen_option": "Take the safe verified path", "commit_source": "deterministic"},
            intent_context={
                "intent_commitments": [
                    {"commitment": "Finish cross-machine proof", "claim_posture": "asserted"},
                ]
            },
        )
        self.assertTrue(evaluation["passed"])
        self.assertEqual(evaluation["violations"], [])

    def test_flags_provisional_commitment_in_chosen_option(self):
        evaluation = evaluate_consentful_inference(
            {
                "chosen_option": "Proceed with Finish cross-machine proof immediately",
                "commit_source": "llm",
            },
            intent_context={
                "intent_commitments": [
                    {"commitment": "Finish cross-machine proof", "claim_posture": "asserted"},
                ]
            },
        )
        self.assertFalse(evaluation["passed"])
        self.assertTrue(any("provisional_commitment" in item for item in evaluation["violations"]))

    def test_deliberation_turn_attaches_consentful_inference(self):
        decision, _ = run_deliberation_turn(
            "Should we take the safe verified path or the fast experimental path?",
            context={
                "intent_commitments": [
                    {"commitment": "Take the safe verified path", "claim_posture": "operator"},
                ]
            },
        )
        self.assertIn("consentful_inference", decision)
        self.assertTrue(decision["consentful_inference"]["passed"])


if __name__ == "__main__":
    unittest.main()
