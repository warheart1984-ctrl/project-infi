"""Operator continuity rubric — N>=3 paired A/B fixture sessions (INV-2)."""

from __future__ import annotations

import unittest

from src.cog_runtime.narrative_continuity_operator_rubric import (
    PASS_THRESHOLD,
    run_operator_rubric_study,
    run_paired_rubric_session,
)


class TestNarrativeContinuityOperatorRubric(unittest.TestCase):
    def test_paired_session_treatment_beats_control(self):
        result = run_paired_rubric_session(
            session_id="unit-pair-001",
            prior_narrative={
                "active_story": "Helping forge Wolf Cog OS",
                "current_chapter": "Nova Cortex Development",
                "working_on": "Cross-machine proof",
                "last_growth": "Composed turns integrated into Jarvis",
                "open_threads": ["Cross-machine proof", "Unified memory path"],
                "continuity_answers": {
                    "doing": "Cross-machine proof",
                    "done": "Composed turns integrated into Jarvis",
                    "toward": "Helping forge Wolf Cog OS",
                },
            },
            treatment_next={
                "active_story": "Helping forge Wolf Cog OS",
                "current_chapter": "Operator rubric",
                "working_on": "Cross-machine proof",
                "last_growth": "Session reset harness landed",
                "open_threads": ["Cross-machine proof", "Operator rubric"],
                "continuity_answers": {
                    "doing": "Cross-machine proof",
                    "done": "Session reset harness landed",
                    "toward": "Helping forge Wolf Cog OS | Operator rubric",
                },
            },
            control_next={
                "working_on": "Cross-machine proof",
                "open_threads": [],
            },
        )
        self.assertTrue(result["passed"])
        self.assertGreater(result["treatment"]["average"], result["control"]["average"])
        self.assertGreaterEqual(result["treatment"]["average"], PASS_THRESHOLD)

    def test_operator_rubric_study_runs_three_paired_sessions(self):
        study = run_operator_rubric_study()
        self.assertEqual(study["minimum_pairs"], 3)
        self.assertEqual(len(study["sessions"]), 3)
        self.assertEqual(study["passed_pairs"], 3)
        self.assertTrue(study["passed"])
        self.assertEqual(study["claim_label"], "proven")
        for session in study["sessions"]:
            self.assertTrue(session["treatment"]["pass"])
            self.assertGreater(session["delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
