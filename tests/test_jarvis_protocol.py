"""Tests for the canonical Jarvis protocol layer."""

import unittest

from src.conversation_memory import ConversationSession
from src.jarvis_modular import (
    AttachmentsModule,
    KnowledgeModule,
    ProviderPayloadModule,
    ToolResultsModule,
    build_modular_provider_preview,
    build_protocol_view,
    build_provider_messages_from_protocol,
    context_modules,
)
from src.jarvis_reasoning_protocol import (
    REASONING_PROTOCOL_ID,
    REASONING_PROTOCOL_VERSION,
    analyze_direct_challenge,
    analyze_otem_request,
    analyze_relational_question,
    build_otem_result,
    build_reasoning_packet,
    detect_otem,
    detect_objective,
    evaluate_otem_viability,
    enforce_direct_challenge_identity,
    looks_like_direct_challenge,
    restate_otem_task,
    weight_factors,
)
from src.jarvis_protocol import (
    JarvisMessage,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    ToolResult,
    build_provider_payload,
    protocol_spec,
)
from src.reasoning_types import ReasoningFactor


class TestJarvisProtocol(unittest.TestCase):
    """Verify the explicit Jarvis language used across AAIS."""

    def test_protocol_spec_exposes_stable_contract(self):
        """The protocol spec should describe the shared Jarvis message language."""
        spec = protocol_spec()

        self.assertEqual(spec["id"], PROTOCOL_ID)
        self.assertEqual(spec["version"], PROTOCOL_VERSION)
        self.assertIn("system", spec["roles"])
        self.assertIn("runtime", spec["channels"])
        self.assertEqual(spec["reasoning_protocol"]["id"], REASONING_PROTOCOL_ID)
        self.assertEqual(spec["reasoning_protocol"]["version"], REASONING_PROTOCOL_VERSION)

    def test_build_provider_payload_collapses_channel_metadata(self):
        """Provider payloads should keep only the role/content form backends expect."""
        payload = build_provider_payload(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "Jarvis runtime state: builder",
                    "channel": "runtime",
                },
                {
                    "role": "user",
                    "content": "Help me ship the smallest working slice.",
                    "channel": "dialogue",
                },
            ],
            stream=True,
            temperature=0.35,
            max_tokens=320,
            mode="builder",
            metadata={"session_id": "session-1"},
        )

        self.assertEqual(payload["model"], "local-model")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertNotIn("channel", payload["messages"][0])
        self.assertEqual(payload["metadata"]["protocol_id"], PROTOCOL_ID)

    def test_session_protocol_envelope_exposes_context_channels(self):
        """Sessions should expose runtime and gathered context through the protocol envelope."""
        session = ConversationSession("session-protocol", system_prompt="You are Jarvis.")
        session.metadata["workspace_context"] = {
            "project_scope": "AAIS-main",
            "prompt_block": "Workspace context auto-attached for api.py.",
        }
        session.metadata["live_research"] = {
            "prompt_block": "Live research attached for this turn.",
        }
        session.add_turn("user", "Help me debug api.py.")

        envelope = session.build_protocol_envelope()
        channels = [message["channel"] for message in envelope["messages"]]

        self.assertEqual(envelope["protocol"]["id"], PROTOCOL_ID)
        self.assertIn("runtime", channels)
        self.assertIn("workspace", channels)
        self.assertIn("research", channels)
        self.assertIn("dialogue", channels)

    def test_jarvis_message_and_tool_result_support_provider_adapters(self):
        """Protocol dataclasses should support remote-provider adapters cleanly."""
        message = JarvisMessage(
            role="assistant",
            content="I found the likely break point.",
            channel="dialogue",
        )
        anthropic_message = message.to_anthropic()
        tool = ToolResult.from_claude(
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "workspace_search",
                "input": {"query": "api.py"},
            }
        )

        self.assertEqual(anthropic_message["role"], "assistant")
        self.assertEqual(tool.id, "toolu_1")
        self.assertEqual(tool.name, "workspace_search")
        self.assertEqual(tool.arguments["query"], "api.py")

    def test_modular_provider_messages_preserve_context_as_named_modules(self):
        """The evolving-style modular bridge should keep context blocks explicit for providers."""
        provider_messages = build_provider_messages_from_protocol(
            [
                {
                    "role": "system",
                    "content": "Use a grounded operator voice.",
                    "channel": "instruction",
                },
                {
                    "role": "system",
                    "content": "Workspace hit: src/api.py",
                    "channel": "workspace",
                },
                {
                    "role": "system",
                    "content": "Research source: release notes",
                    "channel": "research",
                },
                {
                    "role": "user",
                    "content": "Help me merge the modular app shell.",
                    "channel": "dialogue",
                },
            ]
        )

        self.assertEqual(provider_messages[0].role, "system")
        self.assertEqual(provider_messages[0].content, "Use a grounded operator voice.")
        self.assertEqual(provider_messages[1].content, "Workspace context:\nWorkspace hit: src/api.py")
        self.assertEqual(provider_messages[2].content, "Knowledge context:\nResearch source: release notes")
        self.assertEqual(provider_messages[3].role, "user")

    def test_modular_provider_preview_exposes_modules_and_provider_payload(self):
        """Protocol previews should expose the modular context blocks derived from evolving_ai patterns."""
        preview = build_modular_provider_preview(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": "Mission: keep the merge modular.",
                    "channel": "orchestration",
                },
                {
                    "role": "user",
                    "content": "Pull evolving_ai into Jarvis.",
                    "channel": "dialogue",
                },
            ],
            stream=True,
            temperature=0.35,
            max_tokens=320,
            mode="builder",
        )

        self.assertEqual(preview["modules"][0]["channel"], "orchestration")
        self.assertEqual(preview["provider_messages"][0]["role"], "system")
        self.assertTrue(preview["provider_messages"][0]["content"].startswith("Mission context:\n"))
        self.assertEqual(preview["provider_payload"]["metadata"]["module_count"], 1)
        self.assertIn("ProviderPayloadModule", preview["context_modules"])
        self.assertIn("ProtocolContextModule", preview["provider_payload"]["metadata"]["module_names"])
        self.assertEqual(preview["pipeline_mode"], "default")
        self.assertEqual(preview["guardrail_state"]["status"], "nominal")
        self.assertTrue(preview["guardrail_state"]["preserve_core"])
        self.assertTrue(preview["guardrail_state"]["inspectable"])
        self.assertGreaterEqual(preview["ul_trace"]["count"], 2)
        self.assertIn("provider_payload", preview["ul_trace"]["sections"])
        self.assertTrue(preview["doctrine"]["preserve_core"])
        self.assertIn("six_wards", preview["doctrine"])
        self.assertIn("angels_and_wards", preview["doctrine"])
        self.assertIn("guardrail_evaluation", preview)
        self.assertEqual(preview["guardrail_evaluation"]["id"], preview["canonical_guardrail_evaluation"]["id"])
        self.assertEqual(preview["guardrail_evaluation"]["source"], "jarvis_modular_runtime")
        self.assertEqual(preview["guardrail_evaluation"]["evaluation_version"], "v1")
        self.assertEqual(preview["final_judgment"]["status"], "approved")
        self.assertEqual(preview["execution_outcome"]["status"], "approved")
        self.assertEqual(preview["doctrine_posture"]["status"], "approved")
        self.assertEqual(preview["doctrine_summary"]["status"], "approved")
        self.assertEqual(preview["canonical_guardrail_evaluation"]["runtime_effect"], "readout_only")
        self.assertEqual(preview["final_judgment"], preview["guardrail_evaluation"]["final_judgment"])
        self.assertEqual(preview["execution_outcome"], preview["guardrail_evaluation"]["execution_outcome"])
        self.assertEqual(preview["doctrine_summary"], preview["guardrail_evaluation"]["doctrine_summary"])
        self.assertEqual(preview["doctrine_posture"], preview["guardrail_evaluation"]["doctrine_posture"])
        self.assertIn("core:safe", preview["active_doctrine_tags"])
        self.assertEqual(preview["override_result"]["status"], "none")
        self.assertEqual(preview["escalation_result"]["status"], "none")
        self.assertEqual(preview["reasoning_protocol"]["id"], REASONING_PROTOCOL_ID)
        self.assertEqual(preview["reasoning_packet"]["mode"], "builder")
        self.assertEqual(preview["reasoning_packet"]["stage"], "orient")
        self.assertEqual(preview["reasoning_summary"], preview["reasoning_packet"]["summary"])

    def test_context_module_pipeline_includes_evolving_style_modules(self):
        """Jarvis should expose the modular pipeline as real module objects, not only helper functions."""
        names = [module.name for module in context_modules]

        self.assertIn(KnowledgeModule.name, names)
        self.assertIn(ToolResultsModule.name, names)
        self.assertIn(AttachmentsModule.name, names)
        self.assertIn(ProviderPayloadModule.name, names)

    def test_guardrails_block_module_override_outside_approved_zone(self):
        """Protected or unspecified zones should not be allowed to replace the core pipeline."""
        preview = build_modular_provider_preview(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "Mission: keep Jarvis stable.",
                    "channel": "orchestration",
                },
                {
                    "role": "user",
                    "content": "Keep the provider assembly inspectable.",
                    "channel": "dialogue",
                },
            ],
            stream=False,
            temperature=0.2,
            max_tokens=128,
            mode="research",
            modules=[KnowledgeModule(), ProviderPayloadModule()],
            metadata={"adaptive_zone": "provider_assembly_contracts"},
        )

        self.assertEqual(preview["guardrail_state"]["status"], "blocked")
        self.assertTrue(preview["guardrail_state"]["override_blocked"])
        self.assertIn("ProtocolContextModule", preview["context_modules"])
        self.assertNotEqual(preview["context_modules"], ["KnowledgeModule", "ProviderPayloadModule"])
        self.assertFalse(preview["doctrine"]["preserve_core"])
        self.assertFalse(preview["doctrine"]["six_wards"]["passed"])
        self.assertEqual(preview["doctrine_summary"]["status"], "blocked")
        self.assertEqual(preview["final_judgment"]["status"], "blocked")
        self.assertEqual(preview["override_result"]["status"], "blocked")

    def test_detect_objective_returns_otem_for_explicit_trigger(self):
        """OTEM should become the authoritative operator-task objective when explicitly requested."""
        objective = detect_objective("Use OTEM to break this operator task into steps.")

        self.assertEqual(objective, "run_otem")

    def test_detect_otem_supports_mid_message_trigger_but_not_generic_task_language(self):
        """OTEM should require an explicit trigger phrase instead of generic task language."""
        self.assertTrue(detect_otem("Keep the session in operator mode, then use OTEM to break the rollout into steps."))
        self.assertFalse(detect_otem("Break the rollout into steps and keep it deterministic."))
        self.assertFalse(detect_otem("The block feels near OTEM and confidence is high."))

    def test_otem_viability_allows_reasoning_about_storage_without_false_rejection(self):
        """Reasoning about storage should stay allowed when OTEM is not asked to persist state itself."""
        self.assertEqual(
            evaluate_otem_viability("find the best place to store database credentials")["status"],
            "active",
        )
        self.assertEqual(
            evaluate_otem_viability("debug the service runner and identify the blocker")["status"],
            "active",
        )

    def test_otem_viability_still_rejects_direct_side_effect_requests(self):
        """Direct persistence or execution verbs should still be blocked in the OTEM lane."""
        self.assertEqual(
            evaluate_otem_viability("save this session state for later")["status"],
            "rejected",
        )
        self.assertEqual(
            evaluate_otem_viability("run this workflow now")["status"],
            "rejected",
        )

    def test_direct_challenge_boolean_and_profile_stay_aligned(self):
        """Boolean detection and structured direct-challenge analysis should agree on the same turns."""
        prompt = "Jarvis, are you stupid?"

        self.assertTrue(looks_like_direct_challenge(prompt))
        self.assertTrue(analyze_direct_challenge(prompt)["detected"])

    def test_detect_objective_does_not_route_otem_on_signal_only_mention(self):
        """Mentioning OTEM as a location signal should not activate the OTEM lane."""
        objective = detect_objective("I think the block is near OTEM and confidence is high.")

        self.assertNotEqual(objective, "run_otem")

    def test_analyze_otem_request_separates_task_and_signal_clauses(self):
        """OTEM analysis should keep signal language out of the canonical task."""
        prompt = (
            "Use OTEM to identify the blocking seam in the response pipeline near OTEM, "
            "but I mostly feel the block is close and the confidence is high."
        )

        analysis = analyze_otem_request(prompt)

        self.assertTrue(analysis["explicit_trigger"])
        self.assertEqual(analysis["task"], "identify the blocking seam in the response pipeline near OTEM")
        self.assertEqual(
            analysis["signal_clauses"],
            ["I mostly feel the block is close and the confidence is high"],
        )
        self.assertEqual(analysis["operator_signals"]["proximity"], "near OTEM")
        self.assertEqual(analysis["operator_signals"]["confidence"], "high")

    def test_otem_result_restates_and_plans_deterministically(self):
        """OTEM v2 planning should consume a deterministic restatement before building the plan."""
        prompt = "Before anything else, use OTEM to break this migration down, then identify the safest next move."

        result_one = build_otem_result(prompt)
        result_two = build_otem_result(prompt)

        self.assertEqual(
            result_one["restated_task"],
            "Handle this operator task: break this migration down, then identify the safest next move.",
        )
        self.assertEqual(result_one["restated_task"], restate_otem_task(prompt))
        self.assertEqual(result_one["plan"], result_two["plan"])
        self.assertEqual(result_one["status"], "complete")
        self.assertTrue(result_one["session_scoped"])
        self.assertFalse(result_one["persistent"])

    def test_otem_result_drops_signal_clauses_from_restated_task(self):
        """Signal clauses should remain metadata and not enter the OTEM restatement."""
        prompt = (
            "I think the block is near OTEM and confidence is high. "
            "Use OTEM to identify the blocking seam in the response pipeline."
        )

        result = build_otem_result(prompt)

        self.assertEqual(
            result["restated_task"],
            "Handle this operator task: identify the blocking seam in the response pipeline.",
        )
        self.assertEqual(
            result["task_clauses"],
            ["identify the blocking seam in the response pipeline"],
        )
        self.assertEqual(
            result["signal_clauses"],
            ["I think the block is near OTEM and confidence is high"],
        )
        self.assertEqual(result["operator_signals"]["proximity"], "near OTEM")
        self.assertEqual(result["operator_signals"]["confidence"], "high")

    def test_guardrails_allow_override_inside_approved_zone(self):
        """Approved non-core growth zones may execute while doctrine still raises caution."""
        preview = build_protocol_view(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "Sandbox experiment is active.",
                    "channel": "runtime",
                },
                {
                    "role": "user",
                    "content": "Try the lightweight scoring path.",
                    "channel": "dialogue",
                },
            ],
            stream=False,
            temperature=0.3,
            max_tokens=160,
            mode="operator",
            modules=[KnowledgeModule(), ProviderPayloadModule()],
            metadata={"adaptive_zone": "non_core_module_selection"},
        )

        self.assertEqual(preview["guardrail_state"]["status"], "allow")
        self.assertFalse(preview["guardrail_state"]["override_blocked"])
        self.assertEqual(preview["context_modules"], ["KnowledgeModule", "ProviderPayloadModule"])
        self.assertEqual(preview["guardrail_state"]["pipeline_mode"], "operator")
        self.assertEqual(preview["execution_outcome"]["status"], "approved")
        self.assertEqual(preview["final_judgment"]["status"], "approved")
        self.assertEqual(preview["doctrine_posture"]["status"], "caution")
        self.assertEqual(preview["doctrine_summary"]["status"], "caution")
        self.assertEqual(preview["guardrail_evaluation"]["state"], "approved")
        self.assertEqual(preview["guardrail_evaluation"]["runtime_state"], "allow")
        self.assertEqual(preview["override_result"]["status"], "approved")
        self.assertEqual(preview["escalation_result"]["status"], "advisory")
        self.assertEqual(preview["reasoning_packet"]["mode"], "operator")

    def test_doctrine_caution_propagates_without_changing_runtime_contract(self):
        """Advisory doctrine signals should surface as caution readouts without becoming runtime blockers."""
        preview = build_modular_provider_preview(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "Runtime status: nominal.",
                    "channel": "runtime",
                },
                {
                    "role": "user",
                    "content": "Keep the preview readable.",
                    "channel": "dialogue",
                },
            ],
            stream=False,
            temperature=0.2,
            max_tokens=120,
            mode="default",
            metadata={"repetition_score": 0.72},
        )

        self.assertEqual(preview["guardrail_state"]["status"], "nominal")
        self.assertEqual(preview["execution_outcome"]["status"], "approved")
        self.assertEqual(preview["doctrine_summary"]["status"], "caution")
        self.assertEqual(preview["doctrine_posture"]["status"], "caution")
        self.assertEqual(preview["final_judgment"]["status"], "approved")
        self.assertEqual(preview["escalation_result"]["status"], "advisory")
        self.assertEqual(preview["final_judgment"]["runtime_effect"], "readout_only")
        self.assertTrue(preview["final_judgment"]["runtime_allowed"])
        self.assertIn("six_ward:weary", preview["active_doctrine_tags"])

    def test_operator_pipeline_stays_mode_specific(self):
        """Mode pipelines should remain inspectable and deterministic."""
        preview = build_modular_provider_preview(
            model="local-model",
            messages=[
                {
                    "role": "system",
                    "content": "Runtime status: nominal.",
                    "channel": "runtime",
                },
                {
                    "role": "system",
                    "content": "Research source: changelog.",
                    "channel": "research",
                },
                {
                    "role": "user",
                    "content": "Verify the active route.",
                    "channel": "dialogue",
                },
            ],
            stream=False,
            temperature=0.2,
            max_tokens=120,
            mode="operator",
        )

        self.assertEqual(preview["pipeline_mode"], "operator")
        self.assertIn("ProtocolContextModule", preview["context_modules"])
        self.assertNotIn("KnowledgeModule", preview["context_modules"])

    def test_direct_challenge_objective_detection_preempts_general_fallback(self):
        """Direct insults or confrontations should be classified as a direct Jarvis challenge."""
        self.assertEqual(detect_objective("Jarvis are you a moron?"), "handle_direct_challenge")
        self.assertEqual(detect_objective("What is wrong with you?"), "handle_direct_challenge")

    def test_detect_objective_routes_jarvis_feeling_questions_to_relational_lane(self):
        """Jarvis-directed feeling questions should not fall through to the general-answer lane."""
        self.assertEqual(detect_objective("Jarvis, how do you feel?"), "answer_relational_question")
        self.assertEqual(detect_objective("Tell me how you feel."), "answer_relational_question")

    def test_analyze_relational_question_supports_third_person_jarvis_wording(self):
        """Jarvis-addressed third-person feeling phrasing should still classify as relational."""
        profile = analyze_relational_question("Jarvis, how do he feel?")

        self.assertTrue(profile["detected"])
        self.assertEqual(profile["matched_pattern"], "how_do_he_feel")
        self.assertEqual(profile["addressed_target"], "jarvis")

    def test_direct_challenge_packet_forces_relational_mode_and_hides_trace(self):
        """Direct challenge packets should stay relational and clamp trace visibility."""
        packet = build_reasoning_packet(
            goal="answer the user directly",
            mode="think",
            messages=[{"role": "user", "content": "are you stupid?", "channel": "dialogue"}],
            specialist_profile={"domain": "writing", "focus": "dialogue"},
            guardrail_evaluation={"reason": "nominal"},
        )

        self.assertEqual(packet["objective"], "handle_direct_challenge")
        self.assertEqual(packet["mode"], "relational")
        self.assertFalse(packet["output_contract"]["allow_trace"])
        self.assertEqual(packet["metadata"]["direct_challenge"]["severity"], "high")
        constraint_names = {item["name"] for item in packet["constraints"]}
        self.assertIn("must_answer_as_jarvis", constraint_names)
        self.assertIn("forbid_generic_assistant_disclaimer", constraint_names)
        self.assertIn("do_not_refer_to_user_as_jarvis", constraint_names)
        factor_map = {item["name"]: item for item in packet["factors"]}
        self.assertEqual(factor_map["creative_relevance"]["weight"], 0.0)
        self.assertFalse(factor_map["trace_visibility"]["value"])

    def test_weight_factors_returns_a_new_weighted_list(self):
        """Weighting should not mutate the caller's factor instances in place."""
        base_factors = [
            ReasoningFactor(
                name="trace_visibility",
                weight=0.25,
                value=True,
                source="test",
                confidence=0.5,
                trust=0.5,
            )
        ]

        weighted = weight_factors("handle_direct_challenge", base_factors)

        self.assertIsNot(weighted, base_factors)
        self.assertEqual(base_factors[0].weight, 0.25)
        self.assertTrue(base_factors[0].value)
        self.assertEqual(weighted[0].weight, 1.0)
        self.assertFalse(weighted[0].value)

    def test_relational_question_packet_forces_relational_mode_and_hides_trace(self):
        """Jarvis-state questions should stay relational and avoid repo-grounded output."""
        packet = build_reasoning_packet(
            goal="answer the user directly",
            mode="think",
            messages=[{"role": "user", "content": "Jarvis, how do you feel?", "channel": "dialogue"}],
            specialist_profile={"domain": "coding", "focus": "debugging"},
            guardrail_evaluation={"reason": "nominal"},
        )

        self.assertEqual(packet["objective"], "answer_relational_question")
        self.assertEqual(packet["mode"], "relational")
        self.assertFalse(packet["output_contract"]["allow_trace"])
        self.assertFalse(packet["output_contract"]["include_repo_grounding"])
        self.assertEqual(
            packet["metadata"]["relational_question"]["matched_pattern"],
            "how_do_you_feel",
        )
        constraint_names = {item["name"] for item in packet["constraints"]}
        self.assertIn("must_answer_as_jarvis", constraint_names)
        self.assertIn("suspend_repo_and_memory_routing", constraint_names)
        factor_map = {item["name"]: item for item in packet["factors"]}
        self.assertEqual(factor_map["workspace_need"]["weight"], 0.0)
        self.assertFalse(factor_map["trace_visibility"]["value"])

    def test_direct_challenge_identity_guard_replaces_generic_assistant_leak(self):
        """Identity fallback should replace generic assistant disclaimer leakage cleanly."""
        repaired = enforce_direct_challenge_identity("I'm an AI assistant. How can I assist you today?")

        self.assertEqual(repaired, "No. But I can be wrong. Tell me what I missed, and I'll fix it.")
