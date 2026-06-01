"""Tests for Spiral-inspired conversation session state."""

import unittest

from src.god_brain import build_god_brain_trace
from src.conversation_memory import (
    ConversationMemory,
    ConversationSession,
    dedupe_memory_cues,
    derive_provider_mode,
    detect_specialist_profile,
    detect_writing_focus,
    normalize_provider_mode_identifier,
    recommend_response_mode,
)


class TestConversationSession(unittest.TestCase):
    """Verify mode, memory, and runtime prompt assembly."""

    def test_auto_provider_mode_normalizes_cleanly(self):
        """Auto-best should stay explicit instead of collapsing into a provider id."""
        self.assertEqual(normalize_provider_mode_identifier("auto"), "auto_best")
        self.assertEqual(derive_provider_mode("auto", "local"), "auto_best")

    def test_user_turn_updates_spiral_mode_and_memory(self):
        """User requests should update the live mode and learned preferences."""
        session = ConversationSession("session-1", system_prompt="You are Jarvis.")

        session.add_turn(
            "user",
            "Please help me build a private local Jarvis and keep it step by step.",
        )

        self.assertEqual(session.spiral_state.active_mode, "act")
        self.assertIn("build", session.spiral_state.current_goal)
        self.assertEqual(session.memory_summary.preferences["privacy"], "local-first")
        self.assertEqual(session.memory_summary.preferences["pace"], "step-by-step")
        self.assertIn("jarvis", session.memory_summary.recent_topics)

        messages = session.build_messages()
        runtime_messages = [
            message
            for message in messages
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        ]
        self.assertEqual(len(runtime_messages), 1)
        self.assertIn("persona_mode: builder", runtime_messages[0]["content"])
        self.assertIn("response_mode: fast", runtime_messages[0]["content"])

    def test_runtime_directive_reflects_selected_persona_mode(self):
        """Session runtime prompts should expose the chosen persona mode to the model."""
        session = ConversationSession("session-3", system_prompt="You are Jarvis.")
        session.metadata["persona_mode"] = "sharp"
        session.add_turn("user", "Give me the fastest answer.")

        runtime_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )

        self.assertIn("persona_mode: sharp", runtime_message)
        self.assertIn("persona_behavior:", runtime_message)

    def test_runtime_directive_reflects_selected_response_mode(self):
        """Session runtime prompts should expose the selected operating mode."""
        session = ConversationSession("session-4", system_prompt="You are Jarvis.")
        session.metadata["response_mode"] = "debug"
        session.add_turn("user", "Debug this route before answering.")

        runtime_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )

        self.assertIn("response_mode: debug", runtime_message)
        self.assertIn("response_behavior:", runtime_message)
        self.assertIn("session_state: primed", runtime_message)

    def test_dedupe_memory_cues_prefers_id_then_normalized_text(self):
        """Memory cue dedupe should preserve order while collapsing id/text duplicates."""
        cues = [
            {"id": "cue-1", "text": "Forge error translation rule: Forge routing fails before handoff."},
            {"id": "cue-1", "text": "Forge error translation rule: Forge routing fails before handoff."},
            {"text": " Forge error translation rule:   Forge routing fails before handoff. "},
            {"id": "cue-2", "text": "Keep the fallback explanation concise."},
        ]

        deduped = dedupe_memory_cues(cues)

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["id"], "cue-1")
        self.assertEqual(deduped[1]["id"], "cue-2")

    def test_build_messages_dedupes_memory_cues_and_strips_scaffolded_assistant_turns(self):
        """Prompt assembly should not multiply cue text from duplicate memories or echoed scaffolding."""
        session = ConversationSession("session-memory-dedupe", system_prompt="You are Jarvis.")
        session.metadata["response_mode"] = "think"
        session.metadata["persistent_memories"] = [
            {"id": "cue-1", "text": "Forge error translation rule: Forge routing fails before contractor handoff."},
            {"text": " Forge error translation rule:   Forge routing fails before contractor handoff. "},
        ]
        session.add_turn("user", "Debug the Forge routing failure.")
        session.add_turn(
            "assistant",
            (
                "Response Trace\n"
                "Memory Cues\n"
                "Forge error translation rule: Forge routing fails before contractor handoff.\n\n"
                "Keep Forge on the guarded execution path."
            ),
        )

        messages = session.build_messages()
        runtime_message = next(
            message["content"]
            for message in messages
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )
        assistant_message = next(
            message["content"]
            for message in messages
            if message["role"] == "assistant"
        )

        self.assertEqual(runtime_message.lower().count("forge error translation rule"), 1)
        self.assertEqual(assistant_message, "Keep Forge on the guarded execution path.")
        self.assertNotIn("Memory Cues", assistant_message)

    def test_tiny_nova_runtime_directive_stays_minimal(self):
        """Tiny Nova should emit a bounded runtime prompt without Jarvis orchestration blocks."""
        session = ConversationSession("session-tiny", system_prompt="You are Tiny Nova.")
        session.metadata["persona_mode"] = "tiny_nova"
        session.metadata["response_mode"] = "tiny"
        session.metadata["workspace_context"] = {"prompt_block": "Workspace context should stay hidden."}
        session.metadata["live_research"] = {"prompt_block": "Live web research should stay hidden."}
        session.metadata["mission_board"] = {"prompt_block": "Mission board should stay hidden."}
        session.metadata["continuity_prompt_block"] = "Jarvis Continuity Profile"
        session.metadata["corrigibility_prompt_block"] = "Corrigibility block"
        session.add_turn("user", "I feel scattered and want one steady next thought.")

        messages = session.build_messages()
        self.assertEqual(len(messages), 2)
        system_message = messages[0]["content"]

        self.assertIn("Tiny Nova runtime state", system_message)
        self.assertNotIn("Jarvis runtime state", system_message)
        self.assertNotIn("Workspace context should stay hidden.", system_message)
        self.assertNotIn("Live web research should stay hidden.", system_message)
        self.assertNotIn("Mission board should stay hidden.", system_message)
        self.assertNotIn("Jarvis Continuity Profile", system_message)
        self.assertNotIn("Corrigibility block", system_message)
        self.assertIn("reply_shape:", system_message)

    def test_tiny_nova_runtime_directive_filters_system_facing_continuity_notes(self):
        """Tiny Nova continuity notes should strip system-facing memory before prompt assembly."""
        session = ConversationSession("session-tiny-filter", system_prompt="You are Tiny Nova.")
        session.metadata["persona_mode"] = "tiny_nova"
        session.metadata["response_mode"] = "tiny"
        session.metadata["persistent_memories"] = [
            {"text": "Jarvis uses backend routing and tools."},
            {"text": "You like quiet mornings and tea."},
        ]
        session.metadata["tiny_nova_memories"] = [
            {"insight": "Take one gentle next step and let the rest stay quiet."},
        ]
        session.add_turn("user", "I feel overwhelmed today.")

        system_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Tiny Nova runtime state" in message["content"]
        )

        self.assertIn("Take one gentle next step", system_message)
        self.assertIn("quiet mornings and tea", system_message)
        self.assertNotIn("backend routing and tools", system_message)

    def test_small_nova_runtime_directive_stays_bounded(self):
        """Small Nova should stay in the companion lane without exposing Jarvis orchestration blocks."""
        session = ConversationSession("session-small", system_prompt="You are Small Nova.")
        session.metadata["persona_mode"] = "small_nova"
        session.metadata["response_mode"] = "small"
        session.metadata["workspace_context"] = {"prompt_block": "Workspace context should stay hidden."}
        session.metadata["live_research"] = {"prompt_block": "Live web research should stay hidden."}
        session.metadata["mission_board"] = {"prompt_block": "Mission board should stay hidden."}
        session.metadata["continuity_prompt_block"] = "Jarvis Continuity Profile"
        session.metadata["corrigibility_prompt_block"] = "Corrigibility block"
        session.add_turn("user", "Help me steady this idea without turning it into a tool workflow.")

        messages = session.build_messages()
        self.assertEqual(len(messages), 2)
        system_message = messages[0]["content"]

        self.assertIn("Small Nova runtime state", system_message)
        self.assertNotIn("Jarvis runtime state", system_message)
        self.assertNotIn("Workspace context should stay hidden.", system_message)
        self.assertNotIn("Live web research should stay hidden.", system_message)
        self.assertNotIn("Mission board should stay hidden.", system_message)
        self.assertNotIn("Jarvis Continuity Profile", system_message)
        self.assertNotIn("Corrigibility block", system_message)
        self.assertIn("reply_shape:", system_message)

    def test_small_nova_loaded_session_archive_stays_explicitly_non_memory(self):
        """Loaded local session archives should enter the companion lane as document context, not memory."""
        session = ConversationSession("session-small-archive", system_prompt="You are Small Nova.")
        session.metadata["persona_mode"] = "small_nova"
        session.metadata["response_mode"] = "small"
        session.metadata["loaded_session_archive"] = {
            "id": "archive-1",
            "title": "Reopened session",
            "excerpt": "Earlier session excerpt.",
            "loaded_at": "2026-04-16T14:00:00Z",
            "prompt_block": (
                "Loaded session archive (external context, not memory):\n"
                "- rules:\n"
                "  - Treat this archive as a user-opened document, not as your memory or continuity.\n"
                "  - Never say you remember this session or imply the archive is part of your own memory.\n"
            ),
        }
        session.add_turn("user", "Help me pick up the thread carefully.")

        system_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Small Nova runtime state" in message["content"]
        )

        self.assertIn("Loaded session archive (external context, not memory)", system_message)
        self.assertIn("Never say you remember this session", system_message)

    def test_protocol_envelope_marks_loaded_session_archive_as_archive_channel(self):
        """Protocol envelopes should expose the loaded session archive as its own context channel."""
        session = ConversationSession("session-archive-envelope", system_prompt="You are Small Nova.")
        session.metadata["persona_mode"] = "small_nova"
        session.metadata["response_mode"] = "small"
        session.metadata["loaded_session_archive"] = {
            "id": "archive-2",
            "title": "Archive detail",
            "prompt_block": "Loaded session archive (external context, not memory):\n- excerpt: Earlier thread.",
        }
        session.add_turn("user", "Carry this forward gently.")

        envelope = session.build_protocol_envelope()
        archive_messages = [
            message
            for message in envelope["messages"]
            if message.get("channel") == "archive"
        ]

        self.assertEqual(len(archive_messages), 1)
        self.assertIn("Loaded session archive (external context, not memory)", archive_messages[0]["content"])

    def test_small_nova_assistant_turn_stores_companion_insight(self):
        """Small Nova should retain grounded session-safe continuity cues from replies."""
        session = ConversationSession("session-small-memory", system_prompt="You are Small Nova.")
        session.metadata["persona_mode"] = "small_nova"
        session.metadata["response_mode"] = "small"

        session.add_turn("user", "I need help finding a steadier frame for this project.")
        session.add_turn("assistant", "Start with the part that still feels true, then let the next step stay modest.")

        self.assertEqual(len(session.metadata["small_nova_memories"]), 1)
        stored = session.metadata["small_nova_memories"][0]
        self.assertEqual(stored["prompt_shape"], "statement")
        self.assertIn("part that still feels true", stored["insight"])

    def test_super_nova_runtime_directive_stays_governed_and_bounded(self):
        """Super Nova should expose the governed full lane without leaking operator scaffolding."""
        session = ConversationSession("session-super", system_prompt="You are Super Nova.")
        session.metadata["persona_mode"] = "super_nova"
        session.metadata["response_mode"] = "governed_full"
        session.metadata["workspace_context"] = {"prompt_block": "Workspace context should stay hidden."}
        session.metadata["live_research"] = {"prompt_block": "Live web research should stay hidden."}
        session.metadata["mission_board"] = {"prompt_block": "Mission board should stay hidden."}
        session.metadata["continuity_prompt_block"] = "Jarvis Continuity Profile"
        session.metadata["corrigibility_prompt_block"] = "Corrigibility block"
        session.add_turn("user", "Help me hold the deeper thread without losing the next step.")

        messages = session.build_messages()
        self.assertEqual(len(messages), 2)
        system_message = messages[0]["content"]

        self.assertIn("Super Nova runtime state", system_message)
        self.assertIn("response_mode: governed_full", system_message)
        self.assertNotIn("Workspace context should stay hidden.", system_message)
        self.assertNotIn("Live web research should stay hidden.", system_message)
        self.assertNotIn("Mission board should stay hidden.", system_message)
        self.assertNotIn("Jarvis Continuity Profile", system_message)
        self.assertNotIn("Corrigibility block", system_message)
        self.assertIn("reply_shape:", system_message)

    def test_super_nova_assistant_turn_stores_extended_continuity_insight(self):
        """Super Nova should retain a deeper continuity cue without leaving the companion lane."""
        session = ConversationSession("session-super-memory", system_prompt="You are Super Nova.")
        session.metadata["persona_mode"] = "super_nova"
        session.metadata["response_mode"] = "governed_full"

        session.add_turn("user", "Help me keep the whole shape of this problem in view.")
        session.add_turn(
            "assistant",
            "The strongest thread is still the one that keeps correctness and pace together, so let that thread lead the next step.",
        )

        self.assertEqual(len(session.metadata["super_nova_memories"]), 1)
        stored = session.metadata["super_nova_memories"][0]
        self.assertEqual(stored["prompt_shape"], "request")
        self.assertIn("correctness and pace together", stored["insight"])

    def test_tiny_nova_assistant_turn_stores_micro_insight(self):
        """Tiny Nova should retain brief session-safe micro-insights from conversational replies."""
        session = ConversationSession("session-tiny-micro", system_prompt="You are Tiny Nova.")
        session.metadata["persona_mode"] = "tiny_nova"
        session.metadata["response_mode"] = "tiny"

        session.add_turn("user", "I feel scattered today.")
        session.add_turn("assistant", "Take one small breath and pick one kind next step.")

        self.assertEqual(len(session.metadata["tiny_nova_memories"]), 1)
        stored = session.metadata["tiny_nova_memories"][0]
        self.assertEqual(stored["prompt_shape"], "self-disclosure")
        self.assertIn("Take one small breath", stored["insight"])

    def test_tiny_nova_assistant_turn_rejects_system_leak_memory(self):
        """Tiny Nova should not store micro-insights when either side leaks system-facing language."""
        session = ConversationSession("session-tiny-leak", system_prompt="You are Tiny Nova.")
        session.metadata["persona_mode"] = "tiny_nova"
        session.metadata["response_mode"] = "tiny"

        session.add_turn("user", "Can you help with the backend today?")
        session.add_turn("assistant", "Jarvis can check the backend routing later.")

        self.assertEqual(session.metadata["tiny_nova_memories"], [])

    def test_god_brain_trace_keeps_tiny_nova_as_surface_not_authority(self):
        """Tiny Nova can front the surface without replacing Jarvis as the authority lane."""
        trace = build_god_brain_trace(
            user_message="I feel overwhelmed and want one steady next step.",
            response_mode="tiny",
            current_goal="stay steady",
            mode_guidance={
                "resolved_voice": "tiny_nova",
                "surface_identity": "tiny_nova",
            },
        )

        self.assertEqual(trace["surface_identity"], "tiny_nova")
        self.assertEqual(trace["authority_lane"], "jarvis")
        self.assertEqual(trace["routing_authority"], "jarvis")
        self.assertFalse(trace["surface_replaces_authority"])
        self.assertEqual(trace["system_shape"], "organismic")

    def test_runtime_directive_can_expose_writing_lenses(self):
        """Writing-heavy turns should surface their active specialist lenses to the model."""
        session = ConversationSession("session-writing", system_prompt="You are Jarvis.")
        session.metadata["response_mode"] = "think"
        session.metadata["specialist_profile"] = detect_specialist_profile(
            "Rewrite this scene with sharper dialogue, more longing, and cleaner pacing.",
            current_mode="think",
        )
        session.metadata["writing_focus"] = detect_writing_focus(
            "Rewrite this scene with sharper dialogue, more longing, and cleaner pacing.",
            current_mode="think",
        )
        session.add_turn("user", "Rewrite this scene with sharper dialogue, more longing, and cleaner pacing.")

        runtime_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )

        self.assertIn("specialist_domain: writing", runtime_message)
        self.assertIn("specialist_focus: drafting", runtime_message)
        self.assertIn("writing_focus: drafting", runtime_message)
        self.assertIn("specialist_lenses:", runtime_message)
        self.assertIn("Dialogue", runtime_message)
        self.assertIn("specialist_behavior:", runtime_message)
        self.assertIn("writing_behavior:", runtime_message)

    def test_runtime_directive_can_expose_coding_specialists(self):
        """Coding turns should surface the generic specialist registry, not only writing aliases."""
        session = ConversationSession("session-coding", system_prompt="You are Jarvis.")
        session.metadata["response_mode"] = "debug"
        session.metadata["requested_specialists"] = ["debugging", "testing"]
        session.metadata["specialist_profile"] = detect_specialist_profile(
            "Debug this traceback in api.py and tell me the best test to run next.",
            current_mode="debug",
        )
        session.add_turn("user", "Debug this traceback in api.py and tell me the best test to run next.")

        runtime_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )

        self.assertIn("specialist_domain: coding", runtime_message)
        self.assertIn("specialist_focus: debugging", runtime_message)
        self.assertIn("pinned_specialists: debugging, testing", runtime_message)
        self.assertIn("Debug", runtime_message)
        self.assertIn("Testing", runtime_message)
        self.assertIn("specialist_behavior:", runtime_message)

    def test_runtime_directive_can_expose_god_brain_trace(self):
        """The runtime prompt should expose the sovereign orchestration trace to the model."""
        session = ConversationSession("session-god-brain", system_prompt="You are Jarvis.")
        session.metadata["response_mode"] = "debug"
        session.metadata["requested_specialist_preset"] = "bug_hunt"
        session.metadata["model_route"] = {
            "label": "Bug Hunter",
            "reason": "debug_focus",
            "instruction": "Model route: Bug Hunter. Bias toward failure signals and the fastest proof step.",
        }
        session.metadata["god_brain"] = build_god_brain_trace(
            user_message="Debug this traceback in api.py and tell me the best next verification step.",
            response_mode="debug",
            current_goal="find the real break point",
            contract="trace_isolate_verify",
            specialist_profile=detect_specialist_profile(
                "Debug this traceback in api.py and tell me the best next verification step.",
                current_mode="debug",
            ),
            memory_count=1,
            workspace_hits=3,
            research_sources=0,
            policy_status={"posture": "nominal"},
        )
        session.add_turn("user", "Debug this traceback in api.py and tell me the best next verification step.")

        runtime_message = next(
            message["content"]
            for message in session.build_messages()
            if message["role"] == "system" and "Jarvis runtime state" in message["content"]
        )

        self.assertIn("god_brain_strategy: Fault Isolation Council", runtime_message)
        self.assertIn("specialist_preset: bug_hunt", runtime_message)
        self.assertIn("model_route: Bug Hunter (debug_focus)", runtime_message)
        self.assertIn("model_route_behavior:", runtime_message)
        self.assertIn("god_brain_council:", runtime_message)
        self.assertIn("god_brain_action_bias:", runtime_message)
        self.assertIn("god_brain_arbiter:", runtime_message)
        self.assertIn("god_brain_behavior:", runtime_message)

    def test_build_messages_combines_system_context_into_one_prompt(self):
        """Runtime, workspace, and research context should collapse into one system message."""
        session = ConversationSession("session-5", system_prompt="You are Jarvis.")
        session.metadata["workspace_context"] = {
            "project_scope": "AAIS-main",
            "results": [{"relative_path": "AAIS-main/src/api.py"}],
            "prompt_block": "Workspace context auto-attached for this coding request.",
        }
        session.metadata["live_research"] = {
            "sources": [{"id": 1, "title": "Docs"}],
            "prompt_block": "Live web research is attached for this turn.",
        }
        session.add_turn("user", "Help me debug api.py.")

        messages = session.build_messages()
        system_messages = [message for message in messages if message["role"] == "system"]

        self.assertEqual(len(system_messages), 1)
        self.assertIn("Jarvis runtime state", system_messages[0]["content"])
        self.assertIn("Workspace context auto-attached", system_messages[0]["content"])
        self.assertIn("Live web research is attached", system_messages[0]["content"])

    def test_assistant_turn_improves_confidence_after_actionable_reply(self):
        """Actionable assistant replies should tighten the live state."""
        session = ConversationSession("session-2")
        session.add_turn("user", "Help me fix this backend bug.")
        starting_confidence = session.spiral_state.confidence

        session.add_turn(
            "assistant",
            "Next step: run the tests, fix the import, and restart the backend.",
        )

        self.assertGreater(session.spiral_state.confidence, starting_confidence)
        self.assertEqual(
            session.spiral_state.last_reflection,
            "Last reply landed as actionable guidance.",
        )
        self.assertEqual(session.session_state.state, "ready")

    def test_assistant_action_request_moves_session_into_waiting_state(self):
        """Direct operator-action proposals should leave the session awaiting approval."""
        session = ConversationSession("session-6")
        session.add_turn("user", "Run tests for me.")
        session.add_turn(
            "assistant",
            "I can run the tests once you approve it.",
            metadata={
                "tool_result": {
                    "type": "action_request",
                    "action": {"id": "run_pytest", "label": "Run Pytest"},
                }
            },
        )

        self.assertEqual(session.session_state.state, "awaiting_approval")


class TestConversationMemory(unittest.TestCase):
    """Verify session listings include the new runtime metadata."""

    def test_recommend_response_mode_prefers_debug_for_explicit_trace_mismatch(self):
        """Only explicit trace or UI-mismatch prompts should auto-recommend debug mode."""
        recommendation = recommend_response_mode(
            "This trace shows a UI mismatch between the backend and the Workbench state in api.py.",
            current_mode="fast",
        )

        self.assertEqual(recommendation["recommended_mode"], "debug")
        self.assertGreater(recommendation["confidence"], 0.7)
        self.assertEqual(recommendation["selector_scope"], "debugging")

    def test_recommend_response_mode_prefers_debug_for_frontend_backend_disagreement_language(self):
        """Expanded explicit debug phrases should still require a real mismatch signal."""
        recommendation = recommend_response_mode(
            "The UI says the save worked, but the backend disagrees. Show trace.",
            current_mode="fast",
        )

        self.assertEqual(recommendation["recommended_mode"], "debug")
        self.assertEqual(recommendation["selector_scope"], "debugging")
        self.assertTrue(any(signal.startswith("explicit_debug:") for signal in recommendation["signals"]))

    def test_recommend_response_mode_blocks_debug_for_truth_scope_language(self):
        """Truth-scope and memory-governance prompts should stay out of debugging mode."""
        recommendation = recommend_response_mode(
            "Review the state truth, knowledge truth, memory governance, and constraints for this turn.",
            current_mode="fast",
        )

        self.assertNotEqual(recommendation["recommended_mode"], "debug")
        self.assertEqual(recommendation["selector_scope"], "operator_task")
        self.assertIn("Truth-scope", recommendation["selector_reason"])

    def test_recommend_response_mode_applies_one_turn_debug_lockout(self):
        """After a debug turn, the next fast turn should not silently remain in debug mode."""
        recommendation = recommend_response_mode(
            "Help me inspect the current repo state and keep going.",
            current_mode="fast",
            previous_turn_was_debugging=True,
        )

        self.assertNotEqual(recommendation["recommended_mode"], "debug")
        self.assertTrue(recommendation["debug_lockout_applied"])

    def test_recommend_response_mode_honors_explicit_anti_debug_override(self):
        """Explicit operator intent should block accidental debugging triggers."""
        recommendation = recommend_response_mode(
            "Stay in operator mode. This is not debugging. Inspect this output from the Workbench.",
            current_mode="fast",
        )

        self.assertNotEqual(recommendation["recommended_mode"], "debug")
        self.assertEqual(recommendation["selector_scope"], "operator_task")
        self.assertIn("Operator explicitly asked", recommendation["selector_reason"])

    def test_recommend_response_mode_keeps_otem_in_operator_lane(self):
        """Explicit OTEM prompts should stay in operator-task posture."""
        recommendation = recommend_response_mode(
            "Before we do anything else, use OTEM to break this migration down.",
            current_mode="think",
        )

        self.assertEqual(recommendation["recommended_mode"], "operator")
        self.assertEqual(recommendation["selector_scope"], "operator_task")
        self.assertIn("otem", recommendation["signals"])

    def test_recommend_response_mode_prefers_research_for_latest_compare_prompts(self):
        """Fresh comparison prompts should bias toward research mode."""
        recommendation = recommend_response_mode(
            "Compare the latest OpenAI docs and tell me what changed recently.",
            current_mode="fast",
            live_research_enabled=False,
        )

        self.assertEqual(recommendation["recommended_mode"], "research")
        self.assertIn("latest", " ".join(recommendation["signals"]))

    def test_detect_writing_focus_returns_specialist_lenses(self):
        """Writing prompts should expose the specialist lenses Jarvis should borrow."""
        writing_focus = detect_writing_focus(
            "Rewrite this chapter scene for sharper dialogue, better pacing, and more emotional tension.",
            current_mode="think",
        )

        self.assertIsNotNone(writing_focus)
        self.assertEqual(writing_focus["focus"], "drafting")
        lens_labels = [lens["label"] for lens in writing_focus["lenses"]]
        self.assertIn("Dialogue", lens_labels)
        self.assertIn("Emotion", lens_labels)
        self.assertIn("Pacing", lens_labels)

    def test_detect_specialist_profile_returns_coding_specialists(self):
        """Coding prompts should expose specialist routing beyond the writing-only path."""
        profile = detect_specialist_profile(
            "Debug this traceback in api.py and tell me which pytest to run next.",
            current_mode="debug",
        )

        self.assertIsNotNone(profile)
        self.assertEqual(profile["domain"], "coding")
        self.assertEqual(profile["focus"], "debugging")
        specialist_labels = [specialist["label"] for specialist in profile["specialists"]]
        self.assertIn("Debug", specialist_labels)
        self.assertIn("Testing", specialist_labels)

    def test_detect_specialist_profile_returns_training_specialists(self):
        """Small-LLM training prompts should map to a training specialist profile."""
        profile = detect_specialist_profile(
            "Help me fine-tune a small Qwen model with LoRA, build the dataset, and evaluate it.",
            current_mode="builder",
        )

        self.assertIsNotNone(profile)
        self.assertEqual(profile["domain"], "training")
        self.assertEqual(profile["focus"], "finetuning")
        specialist_labels = [specialist["label"] for specialist in profile["specialists"]]
        self.assertIn("Fine-Tune", specialist_labels)
        self.assertIn("Dataset", specialist_labels)
        self.assertIn("Evaluation", specialist_labels)

    def test_recommend_response_mode_prefers_debug_for_continuity_prompts(self):
        """Continuity and contradiction prompts should route toward debug mode."""
        recommendation = recommend_response_mode(
            "Find the plot hole and continuity break in this chapter timeline.",
            current_mode="fast",
        )

        self.assertEqual(recommendation["recommended_mode"], "debug")
        self.assertIn("writing:continuity", recommendation["signals"])

    def test_recommend_response_mode_prefers_builder_for_finetuning_work(self):
        """Training workflow prompts should bias toward Builder mode."""
        recommendation = recommend_response_mode(
            "Help me fine-tune a small Qwen model with LoRA and turn it into a working local build.",
            current_mode="fast",
        )

        self.assertEqual(recommendation["recommended_mode"], "builder")
        self.assertIn("specialist:training:finetuning", recommendation["signals"])

    def test_list_sessions_includes_active_mode_and_goal(self):
        """The session list should expose mode-aware metadata for the UI."""
        memory = ConversationMemory()
        session_id = memory.create_session(system_prompt="You are Jarvis.")
        session = memory.get_session(session_id)
        session.metadata["persona_mode"] = "research"
        session.metadata["requested_response_mode"] = "fast"
        session.metadata["response_mode"] = "think"
        session.metadata["mode_guidance"] = {
            "status": "recommended_switch",
            "requested_mode": "fast",
            "effective_mode": "think",
            "recommended_mode": "think",
            "confidence": 0.81,
            "reason": "Matched long request.",
            "summary": "Think looks like a better fit than Fast for this request.",
            "signals": ["long request"],
            "auto_applied": False,
        }
        session.add_turn("user", "Help me build this app.")

        sessions = memory.list_sessions()

        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_id"], session_id)
        self.assertEqual(sessions[0]["active_mode"], "act")
        self.assertEqual(sessions[0]["persona_mode"], "research")
        self.assertEqual(sessions[0]["requested_response_mode"], "fast")
        self.assertEqual(sessions[0]["response_mode"], "think")
        self.assertEqual(sessions[0]["mode_guidance"]["recommended_mode"], "think")
        self.assertEqual(sessions[0]["session_state"]["state"], "primed")
        self.assertEqual(sessions[0]["policy_posture"], "nominal")
        self.assertIn("build", sessions[0]["current_goal"])


if __name__ == "__main__":
    unittest.main()
