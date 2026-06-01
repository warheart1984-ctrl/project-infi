"""Tests for the Speaking Runtime governed loop."""

import unittest

from src.speaking_runtime import (
    REQUIRED_REPLY_STAGES,
    SPEAKING_STAGES,
    SpeakingRuntimeSession,
    build_check_utterance,
    build_frame_utterance,
    build_listen_utterance,
    build_plan_utterance,
    build_system_prompt,
    compose_reply,
    export_system_prompt_file,
    infer_frame_kind,
    infer_goal,
    run_speaking_turn,
    speaking_runtime_spec,
    validate_reply,
)


class TestSpeakingRuntimeSpec(unittest.TestCase):
    def test_spec_lists_all_stages_and_invariants(self):
        spec = speaking_runtime_spec()
        self.assertEqual(spec["id"], "speaking.runtime")
        self.assertEqual(list(spec["stages"]), list(SPEAKING_STAGES))
        self.assertGreaterEqual(len(spec["invariants"]), 4)
        self.assertIn("system_prompt", spec)


class TestFrameInference(unittest.TestCase):
    def test_implementation_frame(self):
        self.assertEqual(
            infer_frame_kind("I want to build ai that does this"),
            "implementation",
        )

    def test_question_frame(self):
        self.assertEqual(infer_frame_kind("What is a speaking runtime?"), "question")

    def test_decision_frame(self):
        self.assertEqual(
            infer_frame_kind("Should I use a skill or a Python module?"),
            "decision",
        )


class TestSpeakingTurn(unittest.TestCase):
    def test_run_speaking_turn_scaffolds_all_required_stages(self):
        def speak_fn(session: SpeakingRuntimeSession) -> str:
            return f"Here is the answer for a {session.frame_kind} turn."

        reply, session = run_speaking_turn(
            "I want to build ai that does this",
            speak_fn,
            plan_sections=["definition", "contract", "code"],
        )

        validation = validate_reply(reply)
        self.assertTrue(validation["valid"], msg=validation["issues"])
        self.assertEqual(
            validation["stages_found"],
            list(REQUIRED_REPLY_STAGES),
        )
        self.assertIn("implementation", session.frame_kind)
        self.assertEqual(len(session.utterances), 5)

    def test_compose_reply_marks_speak_body_with_traceable_sections(self):
        session = SpeakingRuntimeSession(user_message="Define speaking runtime")
        build_listen_utterance(session)
        build_frame_utterance(session)
        build_plan_utterance(session, sections=["definition", "invariants"])
        build_check_utterance(session, delivered_summary="a runtime spec")

        reply = compose_reply(session, "A speaking runtime speaks its process.")
        self.assertIn("**Listen**", reply)
        self.assertIn("**Speak**", reply)
        self.assertIn("**Check**", reply)
        self.assertIn("speaks its process", reply)


class TestValidation(unittest.TestCase):
    def test_validate_reply_rejects_missing_stages(self):
        result = validate_reply("Just an answer with no stages.")
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing_stages" in issue for issue in result["issues"]))

    def test_build_system_prompt_includes_contract(self):
        prompt = build_system_prompt()
        self.assertIn("Speaking Runtime", prompt)
        self.assertIn("Listen, Frame, Plan, Speak, Check, or Update", prompt)


class TestGoalInference(unittest.TestCase):
    def test_infer_goal_prefixes_by_frame(self):
        goal = infer_goal("design a loop", "design")
        self.assertTrue(goal.startswith("Design or specify:"))


class TestPromptExport(unittest.TestCase):
    def test_export_system_prompt_file(self):
        path = export_system_prompt_file()
        self.assertTrue(path.exists())
        self.assertIn("Speaking Runtime", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
