"""Tests for the bounded anti-drift controller."""

import unittest

from src.anti_drift import build_thread_contract, enforce_anti_drift


class TestAntiDrift(unittest.TestCase):
    """Verify the anti-drift layer stays tied to the active turn contract."""

    def test_build_thread_contract_uses_turn_contract_as_authority(self):
        """The thread contract should inherit the resolved mode, scope, and voice from the active turn."""
        contract = build_thread_contract(
            session_id="session-1",
            user_message="Keep this in operator mode and handle only the current task.",
            turn_contract={
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "mode_guidance",
            },
            mode_guidance={"effective_mode": "debug", "resolved_scope": "debugging", "resolved_voice": "jarvis_debug"},
        )

        self.assertEqual(contract["resolved_mode"], "operator")
        self.assertEqual(contract["resolved_scope"], "operator_task")
        self.assertEqual(contract["resolved_voice"], "jarvis")
        self.assertEqual(contract["authority_order"][0], "active_user_instruction")

    def test_enforce_anti_drift_blocks_trace_and_generic_identity_leakage(self):
        """Trace leakage and generic assistant drift should be blocked before display."""
        contract = build_thread_contract(
            session_id="session-2",
            user_message="Stay in operator mode.",
            turn_contract={
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "mode_guidance",
            },
            mode_guidance={},
        )

        result = enforce_anti_drift(
            "Analysis: Response Trace\nI'm just a tool. How can I assist you today?",
            thread_contract=contract,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertGreaterEqual(result["score"], 4)
        self.assertIn("Staying inside the active operator contract", result["final_text"])

    def test_enforce_anti_drift_clamps_single_signal_generic_identity_drift(self):
        """A single generic assistant drift signal should still be removed before display."""
        contract = build_thread_contract(
            session_id="session-2b",
            user_message="Stay in operator mode.",
            turn_contract={
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "mode_guidance",
            },
            mode_guidance={},
        )

        result = enforce_anti_drift(
            "I'm just a tool. How can I assist you today?",
            thread_contract=contract,
        )

        self.assertEqual(result["status"], "clamped")
        self.assertNotIn("i'm just a tool", result["final_text"].lower())
        self.assertNotIn("how can i assist you today", result["final_text"].lower())
        self.assertIn("Staying inside the active operator contract", result["final_text"])

    def test_enforce_anti_drift_clamps_single_signal_ready_stance_softening(self):
        """A single ready-stance template should be contained before display."""
        contract = build_thread_contract(
            session_id="session-2c",
            user_message="Stay in operator mode.",
            turn_contract={
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "mode_guidance",
            },
            mode_guidance={},
        )

        result = enforce_anti_drift(
            "I'm here to help. What's the issue?",
            thread_contract=contract,
        )

        self.assertEqual(result["status"], "clamped")
        self.assertNotIn("i'm here to help", result["final_text"].lower())
        self.assertNotIn("what's the issue", result["final_text"].lower())
        self.assertIn("Staying inside the active operator contract", result["final_text"])

    def test_enforce_anti_drift_blocks_execution_claims_inside_otem_lane(self):
        """OTEM v5 should block execution claims because it is proposal-only."""
        contract = build_thread_contract(
            session_id="session-3",
            user_message="Use OTEM to break this migration down.",
            turn_contract={
                "resolved_mode": "operator",
                "resolved_scope": "operator_task",
                "resolved_voice": "jarvis",
                "contract_label": "otem",
                "otem_task": "Handle this operator task: break this migration down.",
            },
            mode_guidance={},
        )

        result = enforce_anti_drift(
            "I created the workflow and ran the tool. Here is the final answer.",
            thread_contract=contract,
        )

        self.assertEqual(result["status"], "clamped")
        self.assertTrue(
            any(finding["reason"] == "execution_claim_inside_reason_only_lane" for finding in result["findings"])
        )
        self.assertIn("Staying inside the active OTEM contract", result["final_text"])


if __name__ == "__main__":
    unittest.main()
