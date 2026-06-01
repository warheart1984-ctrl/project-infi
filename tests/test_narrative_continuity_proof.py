"""A/B continuity proof tests — narrative vs arc+planning baseline."""

import unittest

from src.cog_runtime.narrative import NOVA_CORE_IDENTITY
from src.cog_runtime.narrative_continuity import (
    compare_continuity_treatment_vs_baseline,
    continuity_answers,
    score_continuity_completeness,
)


class TestNarrativeContinuityProof(unittest.TestCase):
    def test_narrative_answers_three_questions(self):
        narrative = {
            "core_identity": NOVA_CORE_IDENTITY,
            "active_story": "Helping forge Wolf Cog OS",
            "current_chapter": "Nova Cortex Development",
            "becoming": "improving long-term continuity",
            "working_on": "Cross-machine proof",
            "open_threads": ["Unified memory path"],
            "promises": [],
            "last_growth": "Composed turns integrated into Jarvis",
            "continuity_answers": {
                "doing": "Cross-machine proof",
                "done": "Composed turns integrated into Jarvis",
                "toward": "Helping forge Wolf Cog OS",
            },
        }
        score = score_continuity_completeness(narrative)
        self.assertTrue(score["complete"])
        self.assertEqual(score["score"], 1.0)
        answers = continuity_answers(narrative)
        self.assertTrue(answers["doing"])
        self.assertTrue(answers["done"])
        self.assertTrue(answers["toward"])

    def test_baseline_missing_done(self):
        arc = {
            "goal": "Helping forge Wolf Cog OS",
            "root_goal": "Helping forge Wolf Cog OS",
            "open_threads": ["Cross-machine proof"],
            "current_subgoal": "Nova Cortex Development",
        }
        planning = {"next_action": "Keep primary focus on: cross-machine proof"}
        comparison = compare_continuity_treatment_vs_baseline(
            {
                "working_on": "Cross-machine proof",
                "last_growth": "Integrated composed turns",
                "active_story": "Helping forge Wolf Cog OS",
                "becoming": "improving continuity",
                "open_threads": ["Unified memory path"],
            },
            arc=arc,
            planning=planning,
        )
        self.assertFalse(comparison["baseline"]["filled"]["done"])
        self.assertTrue(comparison["treatment"]["filled"]["done"])
        self.assertTrue(comparison["passed"])
        self.assertGreater(comparison["delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
