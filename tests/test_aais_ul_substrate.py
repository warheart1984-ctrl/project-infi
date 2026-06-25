"""Tests for the AAIS UL runtime substrate layer."""

import unittest

from src.aais_ul import (
    adapt_ingress,
    build_default_registry,
    build_ul_snapshot,
)
from src.aais_ul.runtime import (
    SUBSTRATE_CONTRACT_VERSION,
    SUBSTRATE_ID,
    AAISULSubstrate,
    aais_ul_substrate,
    substrate_status,
    wrap_bridge_result,
    wrap_capability_result,
    wrap_pipeline,
)


class TestAAISULAdapters(unittest.TestCase):
    """Verify extended UL adapters cover runtime surfaces."""

    def test_cognitive_bridge_adapter(self):
        snapshot = build_ul_snapshot(
            bridge_results=[
                {
                    "bridge_id": "aais.cognitive_bridge",
                    "version": "0.1",
                    "decision": "ALLOW",
                    "status": "ready",
                    "execution_allowed": True,
                    "risk": "low",
                    "summary": "cleared",
                }
            ]
        )
        self.assertGreaterEqual(snapshot["count"], 1)
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_governed_pipeline_adapter(self):
        snapshot = build_ul_snapshot(
            pipeline={
                "protocol_id": "aais.governed_direct_pipeline",
                "pipeline_id": "gdp_test",
                "active_lane": "direct_cognitive",
                "traffic_class": "core_cognition",
                "response_mode": "fast",
                "summary": "direct lane",
            }
        )
        self.assertIn("mission_context", snapshot["sections"])

    def test_capability_result_adapter(self):
        snapshot = build_ul_snapshot(
            capability_results=[
                {
                    "ok": True,
                    "module": "image",
                    "action": "analyze",
                    "trace_id": "cap_test",
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_proposal_state_adapter(self):
        snapshot = build_ul_snapshot(
            proposals=[
                {
                    "module_id": "aais.governed_llm_module",
                    "proposal_only": True,
                    "status": "READY",
                    "reason": "cleared",
                }
            ]
        )
        self.assertIn("proposal_state", snapshot["sections"])

    def test_generic_ingress_fallback(self):
        payload = adapt_ingress({"unknown_key": "value"})
        self.assertEqual(payload["section"], "protocol_trace")
        self.assertEqual(payload["kind"], "ingress")


class TestAAISULSubstrate(unittest.TestCase):
    """Verify the unified UL substrate envelope and wrapping helpers."""

    def test_status_payload(self):
        status = substrate_status()
        self.assertEqual(status["substrate_id"], SUBSTRATE_ID)
        self.assertEqual(status["contract_version"], SUBSTRATE_CONTRACT_VERSION)
        self.assertGreaterEqual(status["adapter_count"], 10)

    def test_wrap_bridge_result(self):
        wrapped = wrap_bridge_result(
            {
                "bridge_id": "aais.cognitive_bridge",
                "decision": "ALLOW",
                "status": "ready",
                "execution_allowed": True,
                "risk": "low",
                "summary": "test",
                "normalized_input": {"source": "llm", "type": "generation_request"},
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("ul_trace", wrapped)
        self.assertGreaterEqual(wrapped["ul_trace"]["count"], 1)

    def test_wrap_pipeline(self):
        wrapped = wrap_pipeline(
            {
                "protocol_id": "aais.governed_direct_pipeline",
                "pipeline_id": "gdp_wrap_test",
                "active_lane": "direct_cognitive",
                "traffic_class": "core_cognition",
                "response_mode": "fast",
                "summary": "wrapped",
                "forward_packets": [
                    {
                        "packet_id": "pkt_1",
                        "source": "llm",
                        "target": "jar",
                        "lane": "direct_cognitive",
                        "intent": "respond",
                        "priority": "normal",
                    }
                ],
                "service_packets": [],
                "return_packets": [],
                "bridge_hops": [],
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("mission_context", wrapped["ul_trace"]["sections"])

    def test_wrap_capability_result(self):
        wrapped = wrap_capability_result(
            {
                "ok": True,
                "module": "document",
                "action": "extract",
                "trace_id": "cap_wrap",
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("tool_results", wrapped["ul_trace"]["sections"])

    def test_execute_governed_command_allowed(self):
        substrate = AAISULSubstrate(registry=build_default_registry())
        result = substrate.execute_governed_command("cat jumps x2")
        self.assertTrue(result["allowed"])
        self.assertIn("ul_substrate", result)

    def test_execute_governed_command_blocked(self):
        substrate = AAISULSubstrate(registry=build_default_registry())
        result = substrate.execute_governed_command("cat delete_repo x1")
        self.assertFalse(result["allowed"])
        self.assertIn("ul_substrate", result)

    def test_singleton_instance(self):
        self.assertIsInstance(aais_ul_substrate, AAISULSubstrate)


class TestAAISULSubstratePhase2(unittest.TestCase):
    """Verify Phase 2 runtime surfaces speak UL."""

    def test_immune_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "system_mode": "normal",
                    "event_count": 2,
                    "incident_count": 0,
                    "reason": "baseline",
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_mission_board_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "mission_count": 3,
                    "cisiv_stage_sequence": ["concept", "identity"],
                    "counts": {"active": 1, "done": 2},
                    "summary": "focused",
                }
            ]
        )
        self.assertIn("mission_context", snapshot["sections"])

    def test_module_governance_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "id": "aais.module_governance",
                    "version": "1.1",
                    "module_counts": {"admitted": 2, "quarantined": 0},
                    "cisiv_stage_sequence": ["concept"],
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_memory_board_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "board": {"board_id": "jarvis_memory_board", "board_label": "Memory Board"},
                    "slots": [{"slot_id": "slot_01"}],
                    "active_slots": 1,
                    "installed_slots": 1,
                }
            ]
        )
        self.assertIn("knowledge_context", snapshot["sections"])

    def test_operator_action_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "action": {"id": "run_tests", "label": "Run Tests"},
                    "status": "completed",
                    "exit_code": 0,
                    "summary": "ok",
                    "ran_at": "2026-05-28T00:00:00+00:00",
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_ugr_runtime_response_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "runtime_id": "aais.ugr.unified_runtime",
                    "runtime_version": "0.1",
                    "trace_id": "ugr-test",
                    "status": "ok",
                    "summary": "accepted",
                    "lane_results": [{}],
                }
            ]
        )
        self.assertIn("runtime_context", snapshot["sections"])

    def test_wrap_operator_action(self):
        from src.aais_ul.runtime import wrap_operator_action

        wrapped = wrap_operator_action(
            {
                "response": "done",
                "tool_result": {
                    "type": "action_result",
                    "action": {"id": "run_tests", "label": "Run Tests"},
                    "status": "completed",
                    "exit_code": 0,
                    "summary": "ok",
                    "ran_at": "2026-05-28T00:00:00+00:00",
                },
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("ul_trace", wrapped["tool_result"])

    def test_wrap_ugr_response(self):
        from src.aais_ul.runtime import wrap_ugr_response

        wrapped = wrap_ugr_response(
            {
                "runtime_id": "aais.ugr.unified_runtime",
                "runtime_version": "0.1",
                "trace_id": "ugr-wrap",
                "status": "ok",
                "summary": "ok",
                "lane_results": [],
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("runtime_context", wrapped["ul_trace"]["sections"])


class TestAAISULSubstratePhase3(unittest.TestCase):
    """Verify Phase 3 capability, operator, and console surfaces speak UL."""

    def test_capability_bridge_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "bridge_id": "aais.capability_service_bridge",
                    "version": "0.1",
                    "service_lane": "service_tools",
                    "event_count": 1,
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_operator_console_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "console_id": "aais.operator.ugr_cloud_console",
                    "console_version": "1.1",
                    "status": "ok",
                    "claim_status": "asserted",
                }
            ]
        )
        self.assertIn("runtime_context", snapshot["sections"])

    def test_workspace_context_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "query": "auth middleware",
                    "prompt_block": "Workspace context auto-attached",
                    "results": [{"relative_path": "src/api.py"}],
                    "summary": "Attached 1 workspace matches.",
                }
            ]
        )
        self.assertIn("workspace_context", snapshot["sections"])

    def test_story_forge_capability_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "status": "completed",
                    "artifact_type": "FinalMovieArtifact",
                    "capability": {"name": "story_forge_audio", "version": "v1"},
                    "movie_path": "/tmp/movie.mp4",
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_wrap_service_bridge_result(self):
        from src.aais_ul.runtime import wrap_service_bridge_result

        wrapped = wrap_service_bridge_result(
            {
                "response": "ok",
                "tool_result": {
                    "type": "spatial_reason",
                    "capability": {"module": "spatial", "action": "query", "ok": True},
                },
                "execution_preview": {
                    "path": "capability_service_bridge",
                    "capability": "spatial",
                    "action": "query",
                    "tool": "spatial_reason",
                    "flow": ["capability_service_bridge"],
                },
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("ul_trace", wrapped["tool_result"])


class TestAAISULSubstratePhase4(unittest.TestCase):
    """Verify Phase 4 forge, evolve, patch, and cloud forge surfaces speak UL."""

    def test_patch_plan_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "plan_id": "patch_test",
                    "status": "proposal_only",
                    "goal": "Fix auth seam",
                    "target_files": ["src/api.py"],
                    "hunk_count": 1,
                    "preview_only": True,
                }
            ]
        )
        self.assertIn("proposal_state", snapshot["sections"])

    def test_forge_ul_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "count": 1,
                    "sections": ["runtime_context"],
                    "payloads": [
                        {
                            "source": "forge_runtime",
                            "kind": "context",
                            "section": "runtime_context",
                            "data": {"environment": "forge"},
                        }
                    ],
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_cloud_forge_bundle_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "contract_version": "cloud_forge.v1",
                    "rail_decision": {"rail": "NORMAL", "risk": "LOW"},
                    "cognition_plan": {"domain_template": "code", "steps": ["analyze"]},
                }
            ]
        )
        self.assertIn("mission_context", snapshot["sections"])

    def test_cloud_forge_readout_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "rail": "NORMAL",
                    "risk": "LOW",
                    "summary": "Cloud Forge rail: NORMAL",
                    "runtime_effect": "readout_only",
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_contractor_response_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "task_id": "forge-test",
                    "kind": "generate_diff",
                    "ok": True,
                    "result": {"status": "completed"},
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_evolve_response_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "job_id": "evolve-test",
                    "task": "Improve prompt",
                    "ok": True,
                    "result": {"status": "completed"},
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_wrap_contractor_payload(self):
        from src.aais_ul.runtime import wrap_contractor_payload

        wrapped = wrap_contractor_payload(
            {
                "task_id": "forge-wrap",
                "kind": "generate_diff",
                "ok": True,
                "result": {"status": "completed"},
                "ul_snapshot": {
                    "count": 1,
                    "sections": ["runtime_context"],
                    "payloads": [
                        {
                            "source": "forge_runtime",
                            "kind": "context",
                            "section": "runtime_context",
                            "data": {"environment": "forge"},
                        }
                    ],
                },
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertGreaterEqual(wrapped["ul_trace"]["count"], 1)

    def test_wrap_cloud_forge_bundle(self):
        from src.aais_ul.runtime import wrap_cloud_forge_bundle

        wrapped = wrap_cloud_forge_bundle(
            {
                "contract_version": "cloud_forge.v1",
                "rail_decision": {"rail": "NORMAL", "risk": "LOW"},
                "cognition_plan": {"domain_template": "code", "steps": ["analyze"]},
                "cloud_forge_readout": {
                    "rail": "NORMAL",
                    "risk": "LOW",
                    "summary": "readout",
                    "runtime_effect": "readout_only",
                },
            }
        )
        self.assertIn("ul_substrate", wrapped)
        self.assertIn("ul_trace", wrapped["cloud_forge_readout"])

    def test_attach_ul_substrate_idempotent(self):
        from src.aais_ul.runtime import attach_ul_substrate, wrap_runtime_snapshot

        wrapped = wrap_runtime_snapshot({"task_id": "forge-1", "kind": "analyze", "ok": True})
        again = attach_ul_substrate(wrapped)
        self.assertIs(again, wrapped)


class TestAAISULSubstratePhase5(unittest.TestCase):
    """Verify Phase 5 creative core, mystic, and patch review surfaces speak UL."""

    def test_v9_core_result_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "status": "completed",
                    "location": "Gate",
                    "provider": "openrouter",
                    "pipeline": ["DraftAngel"],
                    "output": "Scene text",
                    "characters": [],
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_v10_core_result_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "status": "completed",
                    "version": "v10",
                    "location": "Gate",
                    "provider": "openrouter",
                    "pipeline": ["SceneAngel"],
                    "quality_report": {"quality_score": 80, "readiness": "strong_draft"},
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_mystic_reading_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "input_text": "I feel stuck",
                    "state": "burdened",
                    "dominant_archetype": "shadow",
                    "trial": "Guilt vs understanding",
                    "next_action": "Write one honest sentence.",
                }
            ]
        )
        self.assertIn("knowledge_context", snapshot["sections"])

    def test_patch_review_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "id": "patch_1",
                    "goal": "Fix seam",
                    "status": "proposed",
                    "patch_plan": {"plan_id": "patch_1", "target_files": ["src/api.py"]},
                    "current_decision": {"state": "proposed"},
                }
            ]
        )
        self.assertIn("proposal_state", snapshot["sections"])

    def test_creative_runtime_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "core": "v10",
                    "runtime_version": "v10",
                    "status": "ready",
                    "run_count": 2,
                    "failure_count": 0,
                    "event_count": 2,
                }
            ]
        )
        self.assertIn("runtime_context", snapshot["sections"])


class TestAAISULSubstratePhase6(unittest.TestCase):
    """Verify Phase 6 operator-visible long tail surfaces speak UL."""

    def test_spatial_reason_result_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "from": "A",
                    "to": "B",
                    "path": ["A", "B"],
                    "distance": 2,
                    "visible": True,
                }
            ]
        )
        self.assertIn("tool_results", snapshot["sections"])

    def test_corrigibility_state_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "status": "steady",
                    "total_corrections": 0,
                    "recent": [],
                    "pending": None,
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_corrigibility_tool_result_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "type": "corrigibility",
                    "status": "queued",
                    "direction": "self_correct",
                    "severity": "medium",
                    "rating": 2,
                    "action": {"id": "corrigibility_self_correct"},
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_operator_health_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "module_id": "AAIS-OHS-01",
                    "operator_state": "stable",
                    "recommended_mode": "normal",
                    "cognitive_load_score": 0.1,
                    "confidence": 0.4,
                    "advisory_only": True,
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_run_ledger_record_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "id": "run_test",
                    "session_id": "sess_1",
                    "status": "open",
                    "kind": "operator",
                    "cisiv_stage": "implementation",
                    "steps": [],
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_operator_readout_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "status": "empty",
                    "trace_count": 0,
                    "traces_path": "/tmp/traces.jsonl",
                    "runtime_effect": "readout_only",
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_operator_health_sentinel_wrap(self):
        from src.operator_health_sentinel import observe_operator_health

        snapshot = observe_operator_health({})
        self.assertIn("ul_substrate", snapshot)
        self.assertGreaterEqual(snapshot["ul_trace"]["count"], 1)

    def test_run_ledger_wrap(self):
        import tempfile

        from src.run_ledger import RunLedger

        ledger = RunLedger(tempfile.mkdtemp())
        run = ledger.create_run("sess_ul", "UL test run", "operator")
        self.assertIn("ul_substrate", run)
        self.assertGreaterEqual(run["ul_trace"]["count"], 1)

    def test_trace_viewer_wrap(self):
        from src.ugr.operator_console.trace_viewer import load_deliberation_traces

        payload = load_deliberation_traces()
        self.assertIn("ul_substrate", payload)
        self.assertGreaterEqual(payload["ul_trace"]["count"], 1)

    def test_corrigibility_default_state_wrap(self):
        from src.corrigibility import default_corrigibility_state

        state = default_corrigibility_state()
        self.assertIn("ul_substrate", state)
        self.assertGreaterEqual(state["ul_trace"]["count"], 1)


class TestAAISULSubstratePhase7(unittest.TestCase):
    """Verify Phase 7 internal and protocol long-tail surfaces speak UL."""

    def test_memory_smith_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "review_count": 2,
                    "durable_count": 1,
                    "expired_count": 0,
                    "project_summary": {"summary": "green"},
                }
            ]
        )
        self.assertIn("knowledge_context", snapshot["sections"])

    def test_knowledge_authority_snapshot_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "authority_order": [{"label": "memory"}],
                    "preferences": {"preset": "strict_local"},
                    "current_contract": "Prefer workspace truth.",
                    "summary": {"mode": "local-only"},
                    "memory": [],
                    "documents": [],
                }
            ]
        )
        self.assertIn("knowledge_context", snapshot["sections"])

    def test_invariant_validation_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "module_id": "aais.invariant_engine.bridge_guard",
                    "status": "pass",
                    "allows": True,
                    "failed_invariants": [],
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_reasoning_exchange_result_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "protocol_id": "aais.reasoning_exchange",
                    "protocol_version": "0.1",
                    "status": "ACCEPT",
                    "reason": None,
                    "confidence_adjustment": 0.0,
                }
            ]
        )
        self.assertIn("protocol_trace", snapshot["sections"])

    def test_governed_event_chain_adapter(self):
        snapshot = build_ul_snapshot(
            ingress=[
                {
                    "module_id": "aais.governed_event_chain",
                    "version": "0.1",
                    "status": "proceed",
                    "decision": "ALLOW",
                    "runtime_context": "live_runtime",
                    "advisory_only": True,
                }
            ]
        )
        self.assertIn("guardrail_state", snapshot["sections"])

    def test_memory_smith_wrap(self):
        from src.memory_smith import MemorySmith

        smith = MemorySmith()
        snapshot = smith.snapshot()
        self.assertIn("ul_substrate", snapshot)

    def test_knowledge_authority_wrap(self):
        from src.knowledge_authority import normalize_authority_preferences
        from src.aais_ul.runtime import attach_ul_substrate

        snapshot = attach_ul_substrate(
            {
                "authority_order": [{"label": "memory"}],
                "preferences": normalize_authority_preferences(None),
                "current_contract": "Prefer workspace truth.",
                "summary": {"mode": "local-only"},
                "memory": [],
                "documents": [],
            }
        )
        self.assertIn("ul_substrate", snapshot)

    def test_governed_event_chain_wrap(self):
        from src.governed_event_chain import governed_event

        result = governed_event({"runtime_context": "live_runtime"})
        self.assertIn("ul_substrate", result)


if __name__ == "__main__":
    unittest.main()
