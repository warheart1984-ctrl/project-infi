"""Tests for Speaking Runtime Jarvis integration."""

import unittest
from types import SimpleNamespace

from src.speaking_runtime.integration import (
    apply_speaking_runtime_finalization,
    build_speaking_runtime_prompt_block,
    resolve_speaking_runtime_enabled,
    summarize_speaking_runtime_state,
)


def _session(**metadata):
    return SimpleNamespace(metadata=dict(metadata))


class TestSpeakingRuntimeIntegration(unittest.TestCase):
    def test_request_flag_enables_runtime(self):
        session = _session()
        enabled = resolve_speaking_runtime_enabled(
            session,
            {"speaking_runtime": True},
            "Explain the loop",
            companion_turn=False,
            direct_challenge=False,
            local_fallback=False,
        )
        self.assertTrue(enabled)
        self.assertTrue(session.metadata["speaking_runtime_enabled"])
        self.assertTrue(build_speaking_runtime_prompt_block(session))

    def test_trigger_phrase_enables_runtime(self):
        session = _session()
        enabled = resolve_speaking_runtime_enabled(
            session,
            {},
            "Please use speaking runtime for this answer",
            companion_turn=False,
            direct_challenge=False,
            local_fallback=False,
        )
        self.assertTrue(enabled)

    def test_companion_turn_disables_runtime(self):
        session = _session(speaking_runtime_enabled=True)
        enabled = resolve_speaking_runtime_enabled(
            session,
            {"speaking_runtime": True},
            "hello",
            companion_turn=True,
            direct_challenge=False,
            local_fallback=False,
        )
        self.assertFalse(enabled)
        self.assertFalse(session.metadata["speaking_runtime_enabled"])

    def test_finalization_wraps_noncompliant_reply(self):
        session = _session(speaking_runtime_enabled=True)
        response_trace = {}
        wrapped = apply_speaking_runtime_finalization(
            session,
            "What is a speaking runtime?",
            "A governed loop that speaks its process.",
            response_trace=response_trace,
        )
        self.assertIn("**Listen**", wrapped)
        self.assertIn("**Check**", wrapped)
        self.assertIn("speaking_runtime", response_trace)

    def test_finalization_passes_through_valid_reply(self):
        session = _session(speaking_runtime_enabled=True)
        valid = (
            "**Listen** — I'm first making sure I understand.\n\n"
            "**Frame** — I'm treating this as a question.\n\n"
            "**Plan** — I'm going to give you a direct answer.\n\n"
            "**Speak** — Here is the answer.\n\n"
            "**Check** — I've given you an answer; if you want more depth, say so."
        )
        result = apply_speaking_runtime_finalization(
            session,
            "What is it?",
            valid,
            response_trace={},
        )
        self.assertEqual(result, valid)

    def test_summarize_state(self):
        session = _session(
            speaking_runtime_enabled=True,
            speaking_runtime_trace={"frame_kind": "question", "goal": "Answer: test", "utterances": [{}]},
        )
        summary = summarize_speaking_runtime_state(session)
        self.assertTrue(summary["enabled"])
        self.assertEqual(summary["frame_kind"], "question")


if __name__ == "__main__":
    unittest.main()
