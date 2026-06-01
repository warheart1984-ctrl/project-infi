"""Tests for API initialization behavior."""

import json
from io import BytesIO
from pathlib import Path
import os
import shutil
import tempfile
import threading
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import src.api as api
from src.conversation_memory import conversation_memory
from src.jarvis_memory_board import MemoryController, default_memory_slots
from src.mock_ai import MockStreamingTextGenerator
from src.jarvis_protocol import JarvisMessage, ProviderResponse
from src.phase_gate import Phase, demote_component, reset_registry


class TestApiInitialization(unittest.TestCase):
    """Ensure API bootstraps text generation components safely."""

    def setUp(self):
        runtime_root = Path.cwd() / ".runtime" / "pytest-temp"
        runtime_root.mkdir(parents=True, exist_ok=True)
        self.guard_root = runtime_root / f"guard-{uuid.uuid4().hex}"
        self.guard_root.mkdir(parents=True, exist_ok=True)
        self.original_guard_runtime_dir = api.system_guard.runtime_dir
        self.original_dreamspace_runtime_dir = api.dreamspace.runtime_dir
        self.original_mission_runtime_dir = api.mission_board.runtime_dir
        self.original_security_runtime_dir = api.security_protocol_core.runtime_dir
        self.original_immune_runtime_dir = api.immune_system.runtime_dir
        self.original_governance_runtime_dir = api.governance_layer.runtime_dir
        self.original_module_governance_runtime_dir = api.module_governance.runtime_dir
        self.original_detachment_guard_runtime_dir = api.cognitive_bridge_service.detachment_guard.runtime_dir
        self.original_continuity_runtime_dir = api.continuity_profile_store.runtime_dir
        self.original_continuity_witness_runtime_dir = api.continuity_witness_store.runtime_dir
        self.original_v9_runtime_dir = api.v9_runtime.runtime_dir
        self.original_v10_runtime_dir = api.v10_runtime.runtime_dir
        api.system_guard.configure_runtime_dir(self.guard_root)
        api.system_guard.reset()
        api.dreamspace.stop(reason="pytest reset")
        api.dreamspace.configure_runtime_dir(self.guard_root)
        api.mission_board.configure_runtime_dir(self.guard_root)
        api.mission_board.reset()
        api.security_protocol_core.configure_runtime_dir(self.guard_root)
        api.security_protocol_core.reset()
        api.immune_system.configure_runtime_dir(self.guard_root)
        api.immune_system.reset()
        api.governance_layer.configure_runtime_dir(self.guard_root)
        api.governance_layer.reset()
        api.module_governance.configure_runtime_dir(self.guard_root)
        api.module_governance.reset()
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.guard_root)
        api.cognitive_bridge_service.detachment_guard.reset()
        api.continuity_profile_store.configure_runtime_dir(self.guard_root)
        api.continuity_profile_store.reset()
        api.continuity_witness_store.configure_runtime_dir(self.guard_root)
        api.continuity_witness_store.reset()
        api.v9_runtime.configure_runtime_dir(self.guard_root)
        api.v9_runtime.reset()
        api.v10_runtime.configure_runtime_dir(self.guard_root)
        api.v10_runtime.reset()
        api.jarvis_operator.spatial_reasoning.spaces.clear()
        api.jarvis_operator.spatial_reasoning.entities.clear()

    def tearDown(self):
        api.ai_model = None
        api.streaming_generator = None
        api.ai_mode = None
        api.ai_init_error = None
        api.ai_bootstrap_status = "not_started"
        api.ai_bootstrap_reason = None
        api.ai_bootstrap_fallback = False
        api.dreamspace.stop(reason="pytest teardown")
        api.jarvis_operator.spatial_reasoning.spaces.clear()
        api.jarvis_operator.spatial_reasoning.entities.clear()
        api.dreamspace.configure_runtime_dir(self.original_dreamspace_runtime_dir)
        api.system_guard.configure_runtime_dir(self.original_guard_runtime_dir)
        api.mission_board.configure_runtime_dir(self.original_mission_runtime_dir)
        api.security_protocol_core.configure_runtime_dir(self.original_security_runtime_dir)
        api.immune_system.configure_runtime_dir(self.original_immune_runtime_dir)
        api.governance_layer.configure_runtime_dir(self.original_governance_runtime_dir)
        api.module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.original_detachment_guard_runtime_dir)
        api.cognitive_bridge_service.detachment_guard.reset()
        api.continuity_profile_store.configure_runtime_dir(self.original_continuity_runtime_dir)
        api.continuity_witness_store.configure_runtime_dir(self.original_continuity_witness_runtime_dir)
        api.v9_runtime.configure_runtime_dir(self.original_v9_runtime_dir)
        api.v10_runtime.configure_runtime_dir(self.original_v10_runtime_dir)
        shutil.rmtree(self.guard_root, ignore_errors=True)

    @patch("src.api._get_model_mode", return_value="real")
    @patch("src.api._load_module")
    def test_init_ai_preloads_text_model_for_streaming(
        self,
        mock_load_module,
        mock_get_model_mode,
    ):
        """Streaming should be created only after the text model is ready."""
        fake_ai_model = MagicMock()
        fake_ai_model.text_model = object()
        fake_ai_model.text_tokenizer = object()
        fake_ai_model.device = "cpu"

        models_module = SimpleNamespace(
            MultiModalAI=MagicMock(return_value=fake_ai_model)
        )
        streaming_module = SimpleNamespace(
            StreamingTextGenerator=MagicMock(return_value=object())
        )

        mock_load_module.side_effect = lambda module_name: {
            "src.models": models_module,
            "src.streaming": streaming_module,
        }[module_name]

        api.init_ai()

        fake_ai_model._load_text_model.assert_called_once_with()
        streaming_module.StreamingTextGenerator.assert_called_once_with(
            model=fake_ai_model.text_model,
            tokenizer=fake_ai_model.text_tokenizer,
            device=fake_ai_model.device,
        )
        self.assertEqual(api.ai_mode, "real")
        mock_get_model_mode.assert_called_once_with()

    def test_coerce_max_length_uses_env_defaults_and_cap(self):
        """Generation length should respect configured defaults and caps."""
        with patch.dict(
            os.environ,
            {
                "AAIS_DEFAULT_MAX_LENGTH": "256",
                "AAIS_MAX_TEXT_TOKENS": "384",
            },
            clear=False,
        ):
            self.assertEqual(api._coerce_max_length(None), 256)
            self.assertEqual(api._coerce_max_length("999"), 384)
            self.assertEqual(api._coerce_max_length("12"), 32)

    def test_mock_streaming_generator_accepts_routing_profile_kwargs(self):
        """The mock streamer should mirror the production streaming signature for routed calls."""
        streamer = MockStreamingTextGenerator()

        chunks = list(
            streamer.generate_stream(
                prompt="Explain the current state.",
                routing_profile={"adapter_mode": "fast"},
                do_sample=False,
                input_max_length=256,
            )
        )

        self.assertTrue(chunks)
        self.assertTrue(chunks[-1]["finished"])
        self.assertIn("Mock streaming response", chunks[-1]["text_so_far"])

    def test_resolve_generation_controls_scales_default_mode_tokens(self):
        """Laptop-style token scaling should shrink mode defaults without overriding explicit values."""
        with patch.dict(
            os.environ,
            {
                "AAIS_DEFAULT_MAX_LENGTH": "96",
                "AAIS_MAX_TEXT_TOKENS": "160",
                "AAIS_RESPONSE_TOKEN_SCALE": "0.25",
            },
            clear=False,
        ):
            mode, scaled_length, temperature = api._resolve_generation_controls("debug")
            self.assertEqual(mode, "debug")
            self.assertEqual(scaled_length, 88)
            self.assertEqual(temperature, 0.25)

            _, explicit_length, _ = api._resolve_generation_controls("debug", requested_length=140)
            self.assertEqual(explicit_length, 140)

    @patch("src.api.init_ai")
    def test_prewarm_endpoint_initializes_ai(self, mock_init_ai):
        """Prewarm should eagerly initialize the model so the first live turn is faster."""
        mock_init_ai.return_value = (object(), object())
        api.ai_mode = "real"

        with api.app.test_client() as client:
            response = client.post("/api/system/prewarm")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["active_model_mode"], "real")
        self.assertEqual(payload["ai_status"], "initialized")
        mock_init_ai.assert_called_once_with()

    @patch("src.api._startup_should_use_mock_fallback", return_value=False)
    @patch("src.api.init_ai", side_effect=RuntimeError("local runtime unavailable"))
    def test_bootstrap_ai_runtime_falls_back_to_mock_when_init_fails(
        self,
        mock_init_ai,
        mock_startup_should_use_mock,
    ):
        """Startup bootstrap should leave Jarvis initialized even when real init fails."""
        model, streamer = api.bootstrap_ai_runtime(reason="unit_test_bootstrap")

        self.assertIsNotNone(model)
        self.assertIsNotNone(streamer)
        self.assertEqual(api.ai_mode, "mock")
        self.assertEqual(api.ai_bootstrap_status, "initialized")
        self.assertEqual(api.ai_bootstrap_reason, "unit_test_bootstrap")
        self.assertTrue(api.ai_bootstrap_fallback)
        self.assertEqual(api.ai_init_error, "local runtime unavailable")
        mock_init_ai.assert_called_once_with()
        mock_startup_should_use_mock.assert_called_once_with()

    @patch("src.api.init_ai")
    def test_bootstrap_ai_runtime_uses_safe_mock_fallback_in_auto_mode(self, mock_init_ai):
        """Automatic startup should prefer the explicit mock fallback unless real boot is requested."""
        model, streamer = api.bootstrap_ai_runtime(reason="auto_bootstrap")

        self.assertIsNotNone(model)
        self.assertIsNotNone(streamer)
        self.assertEqual(api.ai_mode, "mock")
        self.assertEqual(api.ai_bootstrap_status, "initialized")
        self.assertEqual(api.ai_bootstrap_reason, "auto_bootstrap")
        self.assertTrue(api.ai_bootstrap_fallback)
        mock_init_ai.assert_not_called()

    @patch("src.api.app.run")
    @patch("src.api.bootstrap_ai_runtime")
    def test_run_api_bootstraps_ai_before_serving(self, mock_bootstrap, mock_app_run):
        """Direct Flask startup should explicitly bootstrap the AI runtime first."""
        api.run_api(host="127.0.0.1", port=5050, debug=False)

        mock_bootstrap.assert_called_once_with(reason="run_api")
        mock_app_run.assert_called_once_with(host="127.0.0.1", port=5050, debug=False)

    def test_health_includes_system_guard_payload(self):
        """Health should expose the current system guard posture for the Jarvis console."""
        with api.app.test_client() as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("system_guard", payload)
        self.assertEqual(payload["system_guard"]["status"], "nominal")
        self.assertIn("dreamspace", payload)
        self.assertEqual(payload["dreamspace"]["status"], "stopped")
        self.assertEqual(payload["ai_bootstrap_status"], "not_started")

    def test_forge_code_route_returns_contractor_result_and_context_summary(self):
        """The Flask API should proxy one Forge contractor call without exposing raw file contents twice."""
        workspace_context = {
            "project_scope": "AAIS-main",
            "results": [{"relative_path": "AAIS-main/src/api.py", "project": "AAIS-main"}],
            "files": [
                {
                    "relative_path": "AAIS-main/src/api.py",
                    "project": "AAIS-main",
                    "content": "def chat_message():\n    return {'status': 'ok'}\n",
                    "truncated": False,
                }
            ],
            "project_profile": {"languages": ["python"]},
        }
        forge_payload = {
            "task_id": "forge-task-api",
            "task": "Refactor the route.",
            "kind": "generate_diff",
            "law_enforcement": {"contract_version": "aais.forge.ul.v1"},
            "ul_snapshot": {"count": 5, "sections": ["runtime_context"]},
            "result": {
                "ok": True,
                "task_id": "forge-task-api",
                "kind": "generate_diff",
                "result": {
                    "diffs": [
                        {
                            "path": "src/api.py",
                            "unified_diff": "diff --git a/src/api.py b/src/api.py",
                        }
                    ]
                },
            },
            "auto_approve": False,
            "forge_context": {
                "goal": "Refactor the route.",
                "files": [{"path": "AAIS-main/src/api.py", "content": "...", "truncated": False}],
                "constraints": {
                    "language": "python",
                    "requirements": ["no breaking changes"],
                    "style": {"quotes": "single"},
                    "max_output_chars": 20000,
                },
            },
        }
        forge_summary = {
            "goal": "Refactor the route.",
            "file_count": 1,
            "files": [{"path": "AAIS-main/src/api.py", "truncated": False}],
            "constraints": {
                "language": "python",
                "requirements": ["no breaking changes"],
                "style": {"quotes": "single"},
                "max_output_chars": 20000,
            },
        }

        with patch.object(api.jarvis_operator, "build_workspace_context", return_value=workspace_context) as mock_workspace:
            with patch.object(api.jarvis_operator, "request_forge_code", return_value=forge_payload) as mock_request:
                with patch.object(api.jarvis_operator, "summarize_forge_context", return_value=forge_summary):
                    with api.app.test_client() as client:
                        response = client.post("/api/jarvis/forge/code", json={"task": "Refactor the route."})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["task_id"], "forge-task-api")
        self.assertEqual(payload["task"], "Refactor the route.")
        self.assertFalse(payload["auto_approve"])
        self.assertEqual(payload["kind"], "generate_diff")
        self.assertTrue(payload["result"]["ok"])
        self.assertEqual(payload["result"]["kind"], "generate_diff")
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.forge.ul.v1")
        self.assertEqual(payload["ul_snapshot"]["count"], 5)
        self.assertEqual(payload["forge_context"]["file_count"], 1)
        self.assertEqual(payload["workspace_context"]["project_scope"], "AAIS-main")
        mock_workspace.assert_called_once()
        mock_request.assert_called_once_with(
            "Refactor the route.",
            kind="generate_diff",
            workspace_context=workspace_context,
            constraints=None,
            style=None,
            language=None,
            target_scope=None,
            focus_files=None,
            excluded_files=None,
            change_intent=None,
            max_change_budget=None,
        )

    def test_forge_repo_manager_route_returns_bounded_repo_manager_payload(self):
        """The Flask API should expose the read-first Forge repo manager through its own route."""

        workspace_context = {
            "project_scope": "AAIS-main",
            "files": [
                {
                    "relative_path": "src/api.py",
                    "content": "def route():\n    return {'ok': True}\n",
                    "truncated": False,
                }
            ],
        }
        forge_payload = {
            "task_id": "forge-repo-manager-api",
            "task": "Inspect the evolve boundary.",
            "kind": "repo_manager",
            "law_enforcement": {"contract_version": "aais.forge.ul.v1"},
            "ul_snapshot": {"count": 5, "sections": ["runtime_context"]},
            "result": {
                "ok": True,
                "task_id": "forge-repo-manager-api",
                "kind": "repo_manager",
                "result": {
                    "repo_manager": {
                        "repo_summary": "Repo summary",
                        "target_scope": "evolve boundary",
                        "focus_files": ["src/api.py"],
                        "risks": [
                            {
                                "file": "src/api.py",
                                "issue": "Contract drift",
                                "evidence": "Route and service expose different fields.",
                                "confidence": "medium",
                            }
                        ],
                        "plan": [
                            {
                                "step": "Inspect the route",
                                "file": "src/api.py",
                                "purpose": "Understand the current contract",
                                "expected_effect": "Narrow the patch surface",
                                "rollback_note": "No write yet",
                                "validation": "Compare route and isolated service payloads",
                            }
                        ],
                        "validations": ["Run forge route tests"],
                        "execution_ready": False,
                    }
                },
            },
            "auto_approve": False,
            "forge_context": {
                "goal": "Inspect the evolve boundary.",
                "files": [{"path": "src/api.py", "content": "...", "truncated": False}],
                "constraints": {"language": "python"},
                "target_scope": "evolve boundary",
                "focus_files": ["src/api.py"],
                "excluded_files": ["frontend/src/App.jsx"],
                "change_intent": "review_only",
                "max_change_budget": "one narrow seam",
                "validation_target": "route payload parity",
                "operation_mode": "inspect_only",
                "max_files_to_inspect": 3,
                "max_directory_depth": 2,
                "file_path_allowlist": ["src/*"],
                "explicit_denylist": ["frontend/*"],
                "no_execution_without_handoff": True,
            },
        }
        forge_summary = {
            "goal": "Inspect the evolve boundary.",
            "file_count": 1,
            "files": [{"path": "src/api.py", "truncated": False}],
            "constraints": {"language": "python"},
            "target_scope": "evolve boundary",
            "focus_files": ["src/api.py"],
            "excluded_files": ["frontend/src/App.jsx"],
            "change_intent": "review_only",
            "max_change_budget": "one narrow seam",
            "validation_target": "route payload parity",
            "operation_mode": "inspect_only",
            "max_files_to_inspect": 3,
            "max_directory_depth": 2,
            "file_path_allowlist": ["src/*"],
            "explicit_denylist": ["frontend/*"],
            "no_execution_without_handoff": True,
        }

        with patch.object(api.jarvis_operator, "build_workspace_context", return_value=workspace_context) as mock_workspace:
            with patch.object(api.jarvis_operator, "request_forge_repo_manager", return_value=forge_payload) as mock_request:
                with patch.object(api.jarvis_operator, "summarize_forge_context", return_value=forge_summary):
                    with api.app.test_client() as client:
                        response = client.post(
                            "/api/jarvis/forge/repo-manager",
                            json={
                                "task": "Inspect the evolve boundary.",
                                "target_scope": "evolve boundary",
                                "focus_files": ["src/api.py"],
                                "excluded_files": ["frontend/src/App.jsx"],
                                "change_intent": "review_only",
                                "max_change_budget": "one narrow seam",
                                "validation_target": "route payload parity",
                                "operation_mode": "inspect_only",
                                "max_files_to_inspect": 3,
                                "max_directory_depth": 2,
                                "file_path_allowlist": ["src/*"],
                                "explicit_denylist": ["frontend/*"],
                                "no_execution_without_handoff": True,
                            },
                        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["kind"], "repo_manager")
        self.assertEqual(payload["task_id"], "forge-repo-manager-api")
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.forge.ul.v1")
        self.assertEqual(payload["ul_snapshot"]["count"], 5)
        self.assertEqual(payload["forge_context"]["target_scope"], "evolve boundary")
        self.assertEqual(payload["forge_context"]["focus_files"], ["src/api.py"])
        mock_workspace.assert_called_once()
        mock_request.assert_called_once_with(
            "Inspect the evolve boundary.",
            workspace_context=workspace_context,
            constraints=None,
            style=None,
            language=None,
            target_scope="evolve boundary",
            focus_files=["src/api.py"],
            excluded_files=["frontend/src/App.jsx"],
            change_intent="review_only",
            max_change_budget="one narrow seam",
            validation_target="route payload parity",
            operation_mode="inspect_only",
            max_files_to_inspect=3,
            max_directory_depth=2,
            file_path_allowlist=["src/*"],
            explicit_denylist=["frontend/*"],
            no_execution_without_handoff=True,
        )

    def test_forge_evaluate_route_returns_evaluator_payload(self):
        """The Flask API should proxy ForgeEval separately from the contractor lane."""

        evaluation_payload = {
            "task_id": "forge-eval-api",
            "mode": "io_tests",
            "result": {
                "ok": True,
                "task_id": "forge-eval-api",
                "mode": "io_tests",
                "result": {"score": 1.0, "details": {"passed": 1, "total": 1}},
            },
        }

        with patch.object(
            api.jarvis_operator,
            "request_forge_evaluation",
            return_value=evaluation_payload,
        ) as mock_request:
            with api.app.test_client() as client:
                response = client.post(
                    "/api/jarvis/forge/evaluate",
                    json={
                        "mode": "io_tests",
                        "program": "print('ok')",
                        "config": {"must_contain": ["ok"]},
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["task_id"], "forge-eval-api")
        self.assertEqual(payload["mode"], "io_tests")
        self.assertTrue(payload["result"]["ok"])
        mock_request.assert_called_once_with(
            "io_tests",
            payload={"program": "print('ok')", "config": {"must_contain": ["ok"]}},
            task_id=None,
        )

    def test_workbench_snapshot_strips_scaffolded_forge_error_summary(self):
        """Forge summaries stored for the workbench should not leak internal scaffold headers."""
        with api.app.test_client() as client:
            create_response = client.post(
                "/api/chat/sessions",
                json={"system_prompt": "You are Jarvis."},
            )
            session_id = create_response.get_json()["session_id"]

            forge_summary = {
                "goal": "Inspect the contractor error.",
                "file_count": 1,
                "files": [{"path": "src/api.py", "truncated": False}],
                "constraints": {"language": "python"},
            }
            forge_payload = {
                "task_id": "forge-task-scaffold",
                "task": "Inspect the contractor error.",
                "kind": "generate_diff",
                "result": {
                    "ok": False,
                    "error": {
                        "code": "contractor_error",
                        "message": (
                            "Mode: think\n"
                            "Focus: inspect the contractor lane\n"
                            "Answer Shape: bounded\n\n"
                            "Forge could not finish the bounded review."
                        ),
                    },
                },
                "auto_approve": False,
                "forge_context": {
                    "goal": "Inspect the contractor error.",
                    "files": [{"path": "src/api.py", "content": "def route(): pass", "truncated": False}],
                    "constraints": {"language": "python"},
                },
            }

            with patch.object(api.jarvis_operator, "request_forge_code", return_value=forge_payload):
                with patch.object(api.jarvis_operator, "summarize_forge_context", return_value=forge_summary):
                    response = client.post(
                        "/api/jarvis/forge/code",
                        json={"session_id": session_id, "task": "Inspect the contractor error."},
                    )

            self.assertEqual(response.status_code, 200)
            workbench = client.get(f"/api/jarvis/workbench?session_id={session_id}")
            self.assertEqual(workbench.status_code, 200)
            payload = workbench.get_json()
            latest_result = payload["forge"]["contractor"]["latest"]["result"]
            self.assertFalse(latest_result["ok"])
            self.assertEqual(latest_result["code"], "contractor_error")
            self.assertEqual(latest_result["message"], "Forge could not finish the bounded review.")
            self.assertNotIn("Mode:", latest_result["message"])
            self.assertNotIn("Focus:", latest_result["message"])
            self.assertNotIn("Answer Shape:", latest_result["message"])

    def test_evolve_run_route_returns_bounded_evolution_payload(self):
        """The Flask API should proxy one bounded evolve request and store the hall summary."""

        evolve_payload = {
            "job_id": "evolve-job-api",
            "task": "Improve this candidate.",
            "config": {"seed_candidates": ["winner"]},
            "evaluation": {
                "mode": "forge_eval",
                "forge_eval_mode": "llm_rubric",
                "candidate_field": "program",
                "payload": {"config": {"criteria": ["winner"]}},
            },
            "constraints": {"max_generations": 2},
            "result": {
                "ok": True,
                "job_id": "evolve-job-api",
                "task": "Improve this candidate.",
                "result": {
                    "best_score": 0.91,
                    "best_genome": {"candidate": "winner", "candidate_field": "program"},
                    "best_program": "winner",
                    "generations_run": 2,
                    "evaluations": 5,
                    "history": [],
                    "hall_of_fame_count": 2,
                    "hall_of_shame_count": 1,
                },
            },
        }

        with patch.object(
            api.jarvis_operator,
            "request_evolution_job",
            return_value=evolve_payload,
        ) as mock_request:
            with api.app.test_client() as client:
                response = client.post(
                    "/api/jarvis/evolve/run",
                    json={
                        "task": "Improve this candidate.",
                        "config": {"seed_candidates": ["winner"]},
                        "constraints": {"max_generations": 2},
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["job_id"], "evolve-job-api")
        self.assertEqual(payload["result"]["result"]["hall_of_fame_count"], 2)
        self.assertEqual(payload["result"]["result"]["hall_of_shame_count"], 1)
        mock_request.assert_called_once_with(
            "Improve this candidate.",
            preset=None,
            config={"seed_candidates": ["winner"]},
            evaluation=None,
            constraints={"max_generations": 2},
            job_id=None,
            jarvis_run_id=None,
        )

    def test_evolve_hall_routes_proxy_operator_results(self):
        """The Flask API should expose the evolve mutation halls separately."""

        with patch.object(
            api.jarvis_operator,
            "list_evolution_hall_of_fame",
            return_value={"entries": [{"job_id": "evolve-job-1", "reason": "score_met_success_threshold"}]},
        ) as mock_fame:
            with patch.object(
                api.jarvis_operator,
                "list_evolution_hall_of_shame",
                return_value={"entries": [{"job_id": "evolve-job-2", "reason": "sandbox_error"}]},
            ) as mock_shame:
                with api.app.test_client() as client:
                    fame_response = client.get("/api/jarvis/evolve/hall-of-fame?limit=5")
                    shame_response = client.get("/api/jarvis/evolve/hall-of-shame?limit=5")

        self.assertEqual(fame_response.status_code, 200)
        self.assertEqual(shame_response.status_code, 200)
        self.assertEqual(fame_response.get_json()["entries"][0]["job_id"], "evolve-job-1")
        self.assertEqual(shame_response.get_json()["entries"][0]["job_id"], "evolve-job-2")
        mock_fame.assert_called_once_with(limit=5)
        mock_shame.assert_called_once_with(limit=5)

    def test_evolve_forge_handoff_exposes_operator_safe_analysis_summary(self):
        """Forge handoff should provide a scaffold-clean operator summary without mutating the raw contractor payload."""
        handoff_payload = {
            "job_id": "evolve-job-1",
            "forge": {
                "task_id": "forge-handoff-1",
                "task": "Review the winner.",
                "kind": "analyze",
                "auto_approve": False,
                "result": {
                    "ok": True,
                    "result": {
                        "analysis": {
                            "summary": (
                                "Mode: think\n"
                                "Focus: review the winner\n"
                                "Answer Shape: bounded\n\n"
                                "The winner keeps the contract stable."
                            )
                        }
                    },
                },
                "forge_context": {"goal": "Review the winner."},
            },
        }

        with patch.object(
            api.jarvis_operator,
            "handoff_evolution_job_to_forge",
            return_value=handoff_payload,
        ) as mock_handoff:
            with api.app.test_client() as client:
                response = client.post("/api/jarvis/evolve/jobs/evolve-job-1/handoff/forge", json={})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["forge"]["operator_safe_analysis_summary"],
            "The winner keeps the contract stable.",
        )
        self.assertIn("Mode:", payload["forge"]["result"]["result"]["analysis"]["summary"])
        self.assertNotIn("Mode:", payload["forge"]["operator_safe_analysis_summary"])
        self.assertNotIn("Focus:", payload["forge"]["operator_safe_analysis_summary"])
        self.assertNotIn("Answer Shape:", payload["forge"]["operator_safe_analysis_summary"])
        mock_handoff.assert_called_once_with(
            "evolve-job-1",
            task=None,
            kind="analyze",
        )

    def test_text_document_upload_infers_role_from_operator_context(self):
        """Document uploads should preserve an explicit, inspectable role classification."""
        fake_store = MagicMock()
        fake_store.ingest_text.return_value = "doc-123"
        fake_module = SimpleNamespace(
            document_store=fake_store,
            infer_document_role=lambda _: "input_artifact",
        )

        with patch("src.api._load_module", return_value=fake_module):
            response = api.app.test_client().post(
                "/api/documents/upload/text",
                json={
                    "text": "This draft needs work.",
                    "operator_context": "Please fix this before we ship it.",
                },
            )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["doc_id"], "doc-123")
        self.assertEqual(payload["document_role"], "input_artifact")
        fake_store.ingest_text.assert_called_once_with(
            "This draft needs work.",
            doc_id=None,
            metadata={
                "operator_context": "Please fix this before we ship it.",
                "document_role": "input_artifact",
            },
        )

    def test_dreamspace_endpoint_can_run_manual_cycle(self):
        """Dreamspace should support one guarded manual reflection without enabling auto-cycles."""
        api.dreamspace.configure_callbacks(
            generate_callback=lambda request: "Dreamspace surfaced one private insight.",
            context_callback=lambda: {
                "focus": "AAIS-main",
                "seed": "Strengthen Dreamspace without breaking the rest of Jarvis.",
                "style": "practical",
                "recent_topics": ["jarvis", "dreamspace"],
                "active_projects": ["AAIS-main"],
                "recent_turns": ["Make Dreamspace real but optional."],
                "recent_memories": ["Keep everything local-first and private."],
            },
            idle_callback=lambda _threshold: True,
            event_callback=lambda *_args, **_kwargs: None,
        )

        with api.app.test_client() as client:
            response = client.post(
                "/api/system/dreamspace",
                json={"action": "run_once", "reason": "Generate one reflection now."},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["dreamspace"]["total_dreams"], 1)
        self.assertEqual(len(payload["dreamspace"]["recent_dreams"]), 1)
        self.assertIn("Dreamspace surfaced one private insight.", payload["presentation"])

    def test_dreamspace_context_uses_dedicated_runtime_label_for_memory_reads(self):
        """Dreamspace should not borrow operator-runtime authority when fetching memory context."""
        with patch.object(
            api.jarvis_operator.memory_enforcer,
            "list_memories",
            return_value=[{"text": "Keep Dreamspace reflective but governed."}],
        ) as mock_list_memories:
            payload = api._dreamspace_context()

        mock_list_memories.assert_called_once_with(
            limit=6,
            runtime_context="dreamspace_runtime",
        )
        self.assertIn("Keep Dreamspace reflective but governed.", payload["recent_memories"])

    def test_system_guard_pause_propagates_to_dreamspace(self):
        """Guard pauses should freeze Dreamspace alongside the rest of AAIS."""
        api.dreamspace.configure_callbacks(
            generate_callback=lambda request: "Dreamspace note.",
            context_callback=lambda: {"focus": "AAIS-main", "seed": "Pause should propagate cleanly."},
            idle_callback=lambda _threshold: True,
            event_callback=lambda *_args, **_kwargs: None,
        )
        api.dreamspace.start(reason="Test start")

        with api.app.test_client() as client:
            response = client.post(
                "/api/system/guard",
                json={"action": "pause", "reason": "Pause everything safely."},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["system_guard"]["status"], "paused")
        self.assertEqual(payload["dreamspace"]["status"], "paused")

    def test_spatial_reason_endpoint_accepts_structured_tool_requests(self):
        """The API should expose the spatial reasoning tool with the same JSON envelope Jarvis can use."""
        build_response = api.app.test_client().post(
            "/api/jarvis/spatial-reason",
            json={
                "tool": "spatial_reason",
                "args": {
                    "mode": "build",
                    "space_id": "throne_chamber",
                    "nodes": [
                        {"id": "balcony", "type": "elevated", "tags": ["cover"]},
                        {"id": "throne", "type": "seat_of_power"},
                        {"id": "pillar", "type": "obstacle", "tags": ["stone"]},
                        {"id": "assassin", "type": "entity"},
                    ],
                    "edges": [
                        {"from": "balcony", "to": "pillar", "weight": 4, "obstacle": True, "name": "stone pillar"},
                        {"from": "pillar", "to": "throne", "weight": 6},
                        {"from": "balcony", "to": "throne", "weight": 12},
                    ],
                },
            },
        )
        visibility_response = api.app.test_client().post(
            "/api/jarvis/spatial-reason",
            json={
                "tool": "spatial_reason",
                "args": {
                    "mode": "visibility",
                    "space_id": "throne_chamber",
                    "from": "assassin",
                    "to": "throne",
                    "line_of_sight": True,
                },
            },
        )

        self.assertEqual(build_response.status_code, 200)
        self.assertEqual(visibility_response.status_code, 200)
        self.assertEqual(build_response.get_json()["tool_result"]["type"], "spatial_reason")
        self.assertEqual(build_response.get_json()["tool_result"]["result"]["node_count"], 4)
        self.assertFalse(visibility_response.get_json()["tool_result"]["result"]["visible"])

    def test_mystic_read_endpoint_accepts_structured_tool_requests(self):
        """The API should expose the Mystic reading tool with the same JSON envelope Jarvis can use."""
        response = api.app.test_client().post(
            "/api/jarvis/mystic-read",
            json={
                "tool": "mystic_reading",
                "args": {
                    "input": "I feel stuck, numb, and like nothing is moving.",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "mystic_reading")
        self.assertEqual(payload["tool_result"]["result"]["state"], "lost")
        self.assertEqual(payload["tool_result"]["capability"]["module"], "mystic")
        self.assertEqual(payload["tool_result"]["capability"]["action"], "read")
        self.assertIn("Next action", payload["response"])

    @patch("src.api.jarvis_operator.v9_core_engine.run")
    def test_v9_core_endpoint_accepts_structured_tool_requests(self, mock_v9_run):
        """The API should expose the V9 Core tool with the same JSON envelope Jarvis can use."""
        mock_v9_run.return_value = {
            "status": "completed",
            "input": "Continue the throne room scene after the betrayal.",
            "context": "The queen has just found the hidden letter.",
            "location": "Throne Room",
            "characters": ["Queen Seris", "Captain Vale"],
            "provider": "openrouter",
            "model": "openrouter/free",
            "pipeline": ["DraftAngel", "LoreAngel", "DialogueAngel", "ToneAngel"],
            "output": "The queen let the letter fall and the room went colder around her.",
        }

        response = api.app.test_client().post(
            "/api/jarvis/v9-core",
            json={
                "tool": "v9_core",
                "args": {
                    "input": "Continue the throne room scene after the betrayal.",
                    "context": "The queen has just found the hidden letter.",
                    "location": "Throne Room",
                    "characters": ["Queen Seris", "Captain Vale"],
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "v9_core")
        self.assertEqual(payload["tool_result"]["result"]["location"], "Throne Room")
        self.assertEqual(payload["tool_result"]["result"]["runtime"]["snapshot"]["core"], "v9")
        self.assertEqual(payload["tool_result"]["result"]["runtime"]["snapshot"]["status"], "ready")
        self.assertEqual(payload["tool_result"]["capability"]["module"], "v9_core")
        self.assertEqual(payload["tool_result"]["capability"]["action"], "generate_scene")
        self.assertEqual(payload["tool_result"]["capability"]["provider"], "openrouter")
        self.assertIn("The queen let the letter fall", payload["response"])

        runtime_response = api.app.test_client().get("/api/jarvis/v9-runtime")
        self.assertEqual(runtime_response.status_code, 200)
        runtime_payload = runtime_response.get_json()
        self.assertEqual(runtime_payload["core"], "v9")
        self.assertEqual(runtime_payload["last_location"], "Throne Room")
        self.assertEqual(runtime_payload["run_count"], 1)

        event_response = api.app.test_client().get("/api/jarvis/v9-runtime/events")
        self.assertEqual(event_response.status_code, 200)
        latest_event = event_response.get_json()["events"][-1]
        self.assertEqual(latest_event["event_type"], "completed")
        self.assertEqual(latest_event["id"], runtime_payload["last_run_id"])

    @patch("src.api.jarvis_operator.v10_core_engine.run")
    def test_v10_core_endpoint_accepts_structured_tool_requests(self, mock_v10_run):
        """The API should expose the V10 Core tool with the same JSON envelope Jarvis can use."""
        mock_v10_run.return_value = {
            "status": "completed",
            "version": "v10",
            "input": "Continue the throne room scene after the betrayal.",
            "context": "The queen has just found the hidden letter.",
            "location": "Throne Room",
            "characters": ["Queen Seris", "Captain Vale"],
            "provider": "openrouter",
            "model": "openrouter/free",
            "scene_brief": {
                "focus": "The queen recognizes betrayal in the room.",
                "objective": "Push the emotional fracture into the open.",
                "tension": "high",
                "combat_required": False,
            },
            "pipeline": [
                "SceneAngel",
                "DraftAngel",
                "LoreAngel",
                "DialogueAngel",
                "EmotionAngel",
                "ContinuityAngel",
                "PacingAngel",
                "ToneAngel",
                "CriticAngel",
            ],
            "quality_report": {
                "quality_score": 86,
                "readiness": "strong_draft",
            },
            "output": "The queen let the letter fall and realized the room had been lying to her for weeks.",
        }

        response = api.app.test_client().post(
            "/api/jarvis/v10-core",
            json={
                "tool": "v10_core",
                "args": {
                    "input": "Continue the throne room scene after the betrayal.",
                    "context": "The queen has just found the hidden letter.",
                    "location": "Throne Room",
                    "characters": ["Queen Seris", "Captain Vale"],
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "v10_core")
        self.assertEqual(payload["tool_result"]["result"]["quality_report"]["quality_score"], 86)
        self.assertEqual(payload["tool_result"]["result"]["pipeline"][0], "SceneAngel")
        self.assertEqual(payload["tool_result"]["result"]["runtime"]["snapshot"]["core"], "v10")
        self.assertEqual(payload["tool_result"]["result"]["runtime"]["snapshot"]["status"], "ready")
        self.assertEqual(payload["tool_result"]["capability"]["module"], "v10_core")
        self.assertEqual(payload["tool_result"]["capability"]["action"], "generate_scene")
        self.assertEqual(payload["tool_result"]["capability"]["provider"], "openrouter")
        self.assertIn("The queen let the letter fall", payload["response"])

        runtime_response = api.app.test_client().get("/api/jarvis/v10-runtime")
        self.assertEqual(runtime_response.status_code, 200)
        runtime_payload = runtime_response.get_json()
        self.assertEqual(runtime_payload["core"], "v10")
        self.assertEqual(runtime_payload["last_location"], "Throne Room")
        self.assertEqual(runtime_payload["last_quality_score"], 86)

        event_response = api.app.test_client().get("/api/jarvis/v10-runtime/events")
        self.assertEqual(event_response.status_code, 200)
        latest_event = event_response.get_json()["events"][-1]
        self.assertEqual(latest_event["event_type"], "completed")
        self.assertEqual(latest_event["id"], runtime_payload["last_run_id"])

    def test_jarvis_protocol_endpoint_returns_spec_and_session_preview(self):
        """The protocol endpoint should expose both the shared contract and a live session envelope."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.add_turn("user", "Help me improve AAIS without breaking Jarvis.")

        with api.app.test_client() as client:
            response = client.get(f"/api/jarvis/protocol?session_id={session_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["protocol"]["id"], "jarvis.protocol")
        self.assertEqual(payload["session"]["session_id"], session_id)
        self.assertIn("provider_preview", payload["session"])
        self.assertIn("modules", payload["session"])
        self.assertIn("provider_messages", payload["session"])
        self.assertIn("context_modules", payload["session"])
        self.assertIn("guardrail_state", payload["session"])
        self.assertIn("pipeline_mode", payload["session"])
        self.assertIn("v9_runtime", payload["session"])
        self.assertIn("v10_runtime", payload["session"])
        self.assertIn("ul_trace", payload["session"])
        self.assertIn("doctrine", payload["session"])
        self.assertIn("guardrail_evaluation", payload["session"])
        self.assertIn("canonical_guardrail_evaluation", payload["session"])
        self.assertIn("execution_outcome", payload["session"])
        self.assertIn("final_judgment", payload["session"])
        self.assertIn("doctrine_posture", payload["session"])
        self.assertIn("doctrine_summary", payload["session"])
        self.assertIn("active_doctrine_tags", payload["session"])
        self.assertIn("override_result", payload["session"])
        self.assertIn("escalation_result", payload["session"])
        self.assertIn("reasoning_protocol", payload["session"])
        self.assertIn("reasoning_packet", payload["session"])
        self.assertIn("reasoning_summary", payload["session"])
        self.assertGreaterEqual(len(payload["session"]["envelope"]["messages"]), 2)
        self.assertGreaterEqual(len(payload["session"]["modules"]), 1)
        self.assertGreaterEqual(payload["session"]["provider_preview"]["metadata"]["module_count"], 1)
        self.assertIn("ProviderPayloadModule", payload["session"]["context_modules"])
        self.assertEqual(payload["session"]["guardrail_state"]["status"], "nominal")
        self.assertTrue(payload["session"]["guardrail_state"]["preserve_core"])
        self.assertGreaterEqual(payload["session"]["ul_trace"]["count"], 2)
        self.assertTrue(payload["session"]["doctrine"]["preserve_core"])
        self.assertEqual(payload["session"]["guardrail_evaluation"]["source"], "jarvis_modular_runtime")
        self.assertEqual(payload["session"]["guardrail_evaluation"]["evaluation_version"], "v1")
        self.assertEqual(payload["session"]["final_judgment"]["status"], "approved")
        self.assertEqual(payload["session"]["execution_outcome"]["status"], "approved")
        self.assertEqual(payload["session"]["doctrine_posture"]["status"], "approved")
        self.assertEqual(payload["session"]["doctrine_summary"]["status"], "approved")
        self.assertEqual(payload["session"]["reasoning_protocol"]["id"], "jarvis.reasoning")
        self.assertEqual(payload["session"]["reasoning_packet"]["mode"], "fast")
        self.assertEqual(payload["session"]["reasoning_summary"], payload["session"]["reasoning_packet"]["summary"])

    def test_jarvis_protocol_endpoint_omits_session_doctrine_without_session_id(self):
        """The protocol spec endpoint alone should not invent live doctrine state."""
        with api.app.test_client() as client:
            response = client.get("/api/jarvis/protocol")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("protocol", payload)
        self.assertNotIn("session", payload)

    def test_jarvis_protocol_endpoint_matches_preview_truth(self):
        """The API should expose the exact same canonical evaluation produced by the modular preview."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.add_turn("user", "Keep Jarvis modular and inspectable.")
        envelope = session.build_protocol_envelope()
        response_mode = api.normalize_response_mode(session.metadata.get("response_mode"))
        provider_defaults = api.RESPONSE_MODE_DEFAULTS[response_mode]
        expected_preview = api.build_modular_provider_preview(
            model="local-model",
            messages=envelope.get("messages"),
            stream=True,
            temperature=provider_defaults["temperature"],
            max_tokens=provider_defaults["max_tokens"],
            mode=response_mode,
            metadata={
                "session_id": session_id,
                "provider": "local",
                "current_goal": session.spiral_state.current_goal,
                "model_route": session.metadata.get("model_route"),
                "workspace_context": session.metadata.get("workspace_context"),
                "action_lifecycle": session.metadata.get("action_lifecycle"),
                "specialist_profile": session.metadata.get("specialist_profile"),
            },
        )

        with api.app.test_client() as client:
            response = client.get(f"/api/jarvis/protocol?session_id={session_id}")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["session"]
        self.assertEqual(payload["guardrail_evaluation"]["id"], expected_preview["guardrail_evaluation"]["id"])
        self.assertEqual(payload["guardrail_evaluation"]["source"], expected_preview["guardrail_evaluation"]["source"])
        self.assertEqual(
            payload["guardrail_evaluation"]["evaluation_version"],
            expected_preview["guardrail_evaluation"]["evaluation_version"],
        )
        self.assertEqual(payload["final_judgment"], expected_preview["final_judgment"])
        self.assertEqual(payload["execution_outcome"], expected_preview["execution_outcome"])
        self.assertEqual(payload["doctrine_posture"], expected_preview["doctrine_posture"])
        self.assertEqual(payload["doctrine_summary"], expected_preview["doctrine_summary"])
        self.assertEqual(payload["override_result"], expected_preview["override_result"])
        self.assertEqual(payload["escalation_result"], expected_preview["escalation_result"])
        self.assertEqual(payload["active_doctrine_tags"], expected_preview["active_doctrine_tags"])
        self.assertEqual(payload["reasoning_packet"], expected_preview["reasoning_packet"])
        self.assertEqual(payload["reasoning_summary"], expected_preview["reasoning_summary"])
        self.assertEqual(
            payload["canonical_guardrail_evaluation"]["id"],
            expected_preview["canonical_guardrail_evaluation"]["id"],
        )
        self.assertEqual(payload["final_judgment"], payload["guardrail_evaluation"]["final_judgment"])
        self.assertEqual(payload["execution_outcome"], payload["guardrail_evaluation"]["execution_outcome"])
        self.assertEqual(payload["doctrine_posture"], payload["guardrail_evaluation"]["doctrine_posture"])
        self.assertEqual(payload["doctrine_summary"], payload["guardrail_evaluation"]["doctrine_summary"])

    def test_jarvis_blueprint_endpoint_returns_live_system_map(self):
        """The blueprint endpoint should summarize how the live AAIS system fits together."""
        with api.app.test_client() as client:
            response = client.get("/api/jarvis/blueprint")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["blueprint"]["id"], "aais.blueprint")
        self.assertIn("subsystems", payload["blueprint"])
        self.assertIn("module_admission", payload["blueprint"])
        self.assertIn("lineage", payload["blueprint"])
        self.assertGreaterEqual(len(payload["blueprint"]["subsystems"]), 4)
        subsystem_ids = {subsystem["id"] for subsystem in payload["blueprint"]["subsystems"]}
        self.assertIn("security_immune_governance", subsystem_ids)
        self.assertIn("module_governance_protocol", subsystem_ids)
        self.assertIn("continuity_layer", subsystem_ids)
        self.assertIn("creative_runtimes", subsystem_ids)
        module_statuses = {
            entry["id"]: entry["normalized_status"]
            for entry in payload["blueprint"]["module_admission"]["entries"]
        }
        self.assertEqual(module_statuses["phase_gate"], "live")
        self.assertEqual(module_statuses["invariant_engine"], "present but not admitted")
        self.assertEqual(module_statuses["v10_action_engine"], "prototype only")

    def test_mission_board_endpoints_create_focus_and_update_missions(self):
        """Mission Board should support creating, focusing, and updating persistent objectives."""
        with api.app.test_client() as client:
            create_response = client.post(
                "/api/jarvis/missions",
                json={
                    "title": "Ship Mission Board",
                    "objective": "Make Mission Board the shared objective layer for Jarvis.",
                    "next_step": "Wire it into the console rail.",
                    "status": "active",
                },
            )

            self.assertEqual(create_response.status_code, 201)
            board = create_response.get_json()["mission_board"]
            self.assertEqual(board["mission_count"], 1)
            self.assertEqual(board["active_mission"]["cisiv_stage"], "concept")
            mission_id = board["active_mission"]["id"]

            focus_response = client.post(f"/api/jarvis/missions/{mission_id}/focus")
            self.assertEqual(focus_response.status_code, 200)

            update_response = client.patch(
                f"/api/jarvis/missions/{mission_id}",
                json={
                    "status": "blocked",
                    "blocker": "Need the Jarvis side panel wired first.",
                },
            )
            self.assertEqual(update_response.status_code, 200)
            updated = update_response.get_json()["mission_board"]["active_mission"]
            self.assertEqual(updated["status"], "blocked")
            self.assertIn("Jarvis side panel", updated["blocker"])

            unblock_response = client.patch(
                f"/api/jarvis/missions/{mission_id}",
                json={"status": "active"},
            )
            self.assertEqual(unblock_response.status_code, 200)
            unblocked = unblock_response.get_json()["mission_board"]["active_mission"]
            self.assertEqual(unblocked["status"], "active")
            self.assertIsNone(unblocked["blocker"])

            complete_response = client.patch(
                f"/api/jarvis/missions/{mission_id}",
                json={"status": "completed"},
            )
            self.assertEqual(complete_response.status_code, 200)
            completed = complete_response.get_json()["mission_board"]["missions"][0]
            self.assertEqual(completed["status"], "done")

    def test_mission_board_preset_endpoint_creates_recipe(self):
        """Built-in mission recipes should be creatable through the API."""
        with api.app.test_client() as client:
            response = client.post(
                "/api/jarvis/missions/from-preset",
                json={"preset_id": "ship_feature", "focus": True},
            )

            self.assertEqual(response.status_code, 201)
            payload = response.get_json()["mission_board"]
            self.assertEqual(payload["active_mission"]["title"], "Ship feature")
            self.assertEqual(payload["active_mission"]["cisiv_stage"], "concept")
            self.assertGreaterEqual(len(payload["presets"]), 4)

    def test_mission_board_reset_endpoint_backs_up_and_seeds_real_objectives(self):
        """Mission Board reset should preserve a backup and seed the live board with current work."""
        with api.app.test_client() as client:
            client.post(
                "/api/jarvis/missions",
                json={
                    "title": "Old sample mission",
                    "objective": "This should move into the backup before reset.",
                    "status": "active",
                },
            )

            response = client.post(
                "/api/jarvis/missions/reset",
                json={
                    "backup": True,
                    "seed": [
                        {
                            "title": "Stabilize OpenRouter-first routing",
                            "objective": "Validate fresh-session OpenRouter-first routing with honest local fallback.",
                            "next_step": "Create a fresh session and confirm the provider path.",
                            "status": "active",
                            "focus": True,
                            "tags": ["providers", "routing", "fallback"],
                        },
                        {
                            "title": "Validate canonical guardrail evaluation in live sessions",
                            "objective": "Confirm provider changes do not alter the canonical guardrail evaluation shape.",
                            "next_step": "Run one doctrine-warning case across both provider paths.",
                            "status": "queued",
                            "tags": ["guardrails", "protocol", "verification"],
                        },
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        board = payload["mission_board"]
        backup_path = Path(payload["backup_path"])
        self.assertTrue(backup_path.exists())
        self.assertEqual(board["mission_count"], 2)
        self.assertEqual(board["active_mission"]["title"], "Stabilize OpenRouter-first routing")
        self.assertEqual(board["missions"][1]["status"], "queued")
        backup_payload = json.loads(backup_path.read_text(encoding="utf-8"))
        self.assertEqual(len(backup_payload["missions"]), 1)
        self.assertEqual(backup_payload["missions"][0]["title"], "Old sample mission")

    def test_apply_mission_critic_endpoint_adopts_suggestion(self):
        """Mission Critic suggestions should be applicable through the API."""
        with api.app.test_client() as client:
            create_response = client.post(
                "/api/jarvis/missions",
                json={
                    "title": "Fix Settings page",
                    "objective": "Repair the settings route and verify it.",
                    "status": "active",
                },
            )

            self.assertEqual(create_response.status_code, 201)
            board = create_response.get_json()["mission_board"]
            mission_id = board["active_mission"]["id"]
            api.mission_board.attach_critic_review(
                None,
                {
                    "source": "browser_verification",
                    "status": "blocked",
                    "score": 0.4,
                    "confidence": 0.82,
                    "summary": "The route is still mismatched and needs more work.",
                    "recommended_next": "Inspect the Settings page and rebuild the frontend.",
                    "suggested_mission_status": "blocked",
                },
                mission_id=mission_id,
            )

            apply_response = client.post(f"/api/jarvis/missions/{mission_id}/apply-critic")

        self.assertEqual(apply_response.status_code, 200)
        active = apply_response.get_json()["mission_board"]["active_mission"]
        self.assertEqual(active["status"], "blocked")
        self.assertEqual(active["next_step"], "Inspect the Settings page and rebuild the frontend.")

    def test_apply_mission_critic_clears_stale_blocker_when_mission_unblocks(self):
        """Applying a non-blocked critic state should clear stale blocker labels."""
        with api.app.test_client() as client:
            create_response = client.post(
                "/api/jarvis/missions",
                json={
                    "title": "Train a new angel",
                    "objective": "Define the next bounded angel module and verify the training lane.",
                    "status": "blocked",
                    "blocker": "Training lane still needs a stable eval harness.",
                },
            )

            self.assertEqual(create_response.status_code, 201)
            mission_id = create_response.get_json()["mission_board"]["active_mission"]["id"]
            api.mission_board.attach_critic_review(
                None,
                {
                    "source": "action_result",
                    "status": "advancing",
                    "score": 0.78,
                    "confidence": 0.9,
                    "summary": "The eval harness is in place and the mission can move forward again.",
                    "recommended_next": "Run the first bounded training pass and record the outcome.",
                    "suggested_mission_status": "active",
                },
                mission_id=mission_id,
            )

            apply_response = client.post(f"/api/jarvis/missions/{mission_id}/apply-critic")

        self.assertEqual(apply_response.status_code, 200)
        active = apply_response.get_json()["mission_board"]["active_mission"]
        self.assertEqual(active["status"], "active")
        self.assertIsNone(active["blocker"])
        self.assertEqual(active["next_step"], "Run the first bounded training pass and record the outcome.")

    def test_jarvis_providers_endpoint_lists_local_and_optional_sisters(self):
        """Jarvis should expose provider registry status for the console and routing logic."""
        with patch.object(api.provider_registry, "refresh") as mock_refresh, patch.object(
            api.provider_registry,
            "list_status",
            return_value=[
                {"id": "local", "label": "Local Heroine", "available": True},
                {"id": "claude", "label": "Claude — First Sister", "available": False},
            ],
        ) as mock_list:
            with api.app.test_client() as client:
                response = client.get("/api/jarvis/providers")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["providers"][0]["id"], "local")
        self.assertEqual(payload["providers"][1]["id"], "claude")
        mock_refresh.assert_called_once_with()
        mock_list.assert_called_once_with()

    def test_coerce_temperature_uses_env_default(self):
        """Temperature should fall back safely and stay in range."""
        with patch.dict(
            os.environ,
            {"AAIS_DEFAULT_TEMPERATURE": "0.6"},
            clear=False,
        ):
            self.assertEqual(api._coerce_temperature(None), 0.6)
            self.assertEqual(api._coerce_temperature("2.5"), 1.5)
            self.assertEqual(api._coerce_temperature("-1"), 0.0)

    @patch("src.api._get_model_mode", return_value="real")
    @patch("src.api._load_module")
    def test_init_ai_failure_resets_partial_state(
        self,
        mock_load_module,
        mock_get_model_mode,
    ):
        """A failed real-model boot should not leave stale partial globals behind."""
        fake_ai_model = MagicMock()
        fake_ai_model._load_text_model.side_effect = ImportError("protobuf missing")
        models_module = SimpleNamespace(
            MultiModalAI=MagicMock(return_value=fake_ai_model)
        )
        streaming_module = SimpleNamespace(
            StreamingTextGenerator=MagicMock(return_value=object())
        )

        mock_load_module.side_effect = lambda module_name: {
            "src.models": models_module,
            "src.streaming": streaming_module,
        }[module_name]

        with self.assertRaises(ImportError):
            api.init_ai()

        self.assertIsNone(api.ai_model)
        self.assertIsNone(api.streaming_generator)
        self.assertIsNone(api.ai_mode)
        self.assertEqual(api.ai_init_error, "protobuf missing")
        mock_get_model_mode.assert_called_once_with()

    @patch("src.api._get_model_mode", return_value="real")
    @patch("src.api._load_module")
    def test_init_ai_is_singleton_under_parallel_calls(
        self,
        mock_load_module,
        mock_get_model_mode,
    ):
        """Parallel init requests should share one model bootstrap."""
        fake_ai_model = MagicMock()
        fake_ai_model.text_model = object()
        fake_ai_model.text_tokenizer = object()
        fake_ai_model.device = "cpu"

        load_started = threading.Event()
        release_load = threading.Event()

        def slow_load():
            load_started.set()
            release_load.wait(timeout=2)

        fake_ai_model._load_text_model.side_effect = slow_load

        models_module = SimpleNamespace(
            MultiModalAI=MagicMock(return_value=fake_ai_model)
        )
        streaming_module = SimpleNamespace(
            StreamingTextGenerator=MagicMock(return_value=object())
        )

        mock_load_module.side_effect = lambda module_name: {
            "src.models": models_module,
            "src.streaming": streaming_module,
        }[module_name]

        errors = []

        def call_init():
            try:
                api.init_ai()
            except Exception as exc:  # pragma: no cover - defensive capture
                errors.append(exc)

        first = threading.Thread(target=call_init)
        second = threading.Thread(target=call_init)
        first.start()
        self.assertTrue(load_started.wait(timeout=1))
        second.start()
        time.sleep(0.05)
        release_load.set()
        first.join(timeout=2)
        second.join(timeout=2)

        self.assertFalse(errors)
        fake_ai_model._load_text_model.assert_called_once_with()
        models_module.MultiModalAI.assert_called_once_with()
        streaming_module.StreamingTextGenerator.assert_called_once_with(
            model=fake_ai_model.text_model,
            tokenizer=fake_ai_model.text_tokenizer,
            device=fake_ai_model.device,
        )
        mock_get_model_mode.assert_called_once_with()

class TestChatApi(unittest.TestCase):
    """Exercise the chat API with Spiral-style session metadata."""

    def setUp(self):
        self.client = api.app.test_client()
        reset_registry()
        conversation_memory.sessions.clear()
        api.ai_model = None
        api.streaming_generator = None
        api.ai_mode = None
        api.ai_init_error = None
        runtime_root = Path.cwd() / ".runtime" / "pytest-temp"
        runtime_root.mkdir(parents=True, exist_ok=True)
        self.temp_root = runtime_root / f"chat-{uuid.uuid4().hex}"
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root = self.temp_root / "workspace"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        (self.workspace_root / "AAIS-main").mkdir()
        (self.workspace_root / "AAIS-main" / "README.md").write_text(
            "# AAIS-main\nPrivate local Jarvis repo.\n",
            encoding="utf-8",
        )
        (self.workspace_root / "AAIS-main" / "notes.txt").write_text(
            "Jarvis memory and workspace tools live here.",
            encoding="utf-8",
        )
        self.original_memory_path = api.jarvis_operator.memory_store.memory_path
        self.original_workspace_root = api.jarvis_operator.workspace_tools.workspace_root
        self.original_evolving_workspace_root = api.jarvis_operator.evolving_workspace.workspace_root
        self.original_evolving_audit_runtime_dir = api.jarvis_operator.evolving_approval_audit.runtime_dir
        self.original_run_ledger_runtime_dir = api.jarvis_operator.run_ledger.runtime_dir
        self.original_patch_review_runtime_dir = api.jarvis_operator.patch_reviews.runtime_dir
        self.original_memory_smith_runtime_dir = api.jarvis_operator.memory_smith.runtime_dir
        self.original_event_runtime_dir = api.v8_event_log.runtime_dir
        self.original_guard_runtime_dir = api.system_guard.runtime_dir
        self.original_dreamspace_runtime_dir = api.dreamspace.runtime_dir
        self.original_mission_runtime_dir = api.mission_board.runtime_dir
        self.original_security_runtime_dir = api.security_protocol_core.runtime_dir
        self.original_immune_runtime_dir = api.immune_system.runtime_dir
        self.original_governance_runtime_dir = api.governance_layer.runtime_dir
        self.original_module_governance_runtime_dir = api.module_governance.runtime_dir
        self.original_detachment_guard_runtime_dir = api.cognitive_bridge_service.detachment_guard.runtime_dir
        self.original_continuity_runtime_dir = api.continuity_profile_store.runtime_dir
        self.original_continuity_witness_runtime_dir = api.continuity_witness_store.runtime_dir
        self.original_v9_runtime_dir = api.jarvis_operator.v9_runtime.runtime_dir
        self.original_v10_runtime_dir = api.jarvis_operator.v10_runtime.runtime_dir
        api.jarvis_operator.memory_store.memory_path = self.temp_root / "jarvis_memory.json"
        api.jarvis_operator.workspace_tools.workspace_root = self.workspace_root
        api.jarvis_operator.evolving_workspace.workspace_root = self.workspace_root
        api.jarvis_operator.evolving_approval_audit.configure_runtime_dir(self.temp_root / "evolving-audit")
        api.jarvis_operator.run_ledger.configure_runtime_dir(self.temp_root / "run-ledger")
        api.jarvis_operator.patch_reviews.configure_runtime_dir(self.temp_root / "patch-reviews")
        api.jarvis_operator.memory_smith.configure_runtime_dir(self.temp_root / "memory-smith")
        api.v8_event_log.runtime_dir = self.temp_root / "v8-events"
        api.v8_event_log._events.clear()
        api.system_guard.configure_runtime_dir(self.temp_root / "system-guard")
        api.system_guard.reset()
        api.dreamspace.stop(reason="pytest reset")
        api.dreamspace.configure_runtime_dir(self.temp_root / "dreamspace")
        api.mission_board.configure_runtime_dir(self.temp_root / "mission-board")
        api.mission_board.reset()
        api.security_protocol_core.configure_runtime_dir(self.temp_root / "security")
        api.security_protocol_core.reset()
        api.immune_system.configure_runtime_dir(self.temp_root / "immune")
        api.immune_system.reset()
        api.governance_layer.configure_runtime_dir(self.temp_root / "governance")
        api.governance_layer.reset()
        api.module_governance.configure_runtime_dir(self.temp_root / "module-governance")
        api.module_governance.reset()
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.temp_root / "detachment-guard")
        api.cognitive_bridge_service.detachment_guard.reset()
        api.continuity_profile_store.configure_runtime_dir(self.temp_root / "continuity")
        api.continuity_profile_store.reset()
        api.continuity_witness_store.configure_runtime_dir(self.temp_root / "continuity-witness")
        api.continuity_witness_store.reset()
        api.jarvis_operator.v9_runtime.configure_runtime_dir(self.temp_root / "v9-runtime")
        api.jarvis_operator.v9_runtime.reset()
        api.jarvis_operator.v10_runtime.configure_runtime_dir(self.temp_root / "v10-runtime")
        api.jarvis_operator.v10_runtime.reset()
        api.jarvis_operator.spatial_reasoning.spaces.clear()
        api.jarvis_operator.spatial_reasoning.entities.clear()
        document_module = api._load_module("src.document_rag")
        document_module.document_store.documents.clear()
        document_module.document_store._query_cache.clear()

    def tearDown(self):
        reset_registry()
        conversation_memory.sessions.clear()
        api.ai_model = None
        api.streaming_generator = None
        api.ai_mode = None
        api.ai_init_error = None
        api.dreamspace.stop(reason="pytest teardown")
        api.jarvis_operator.memory_store.memory_path = self.original_memory_path
        api.jarvis_operator.workspace_tools.workspace_root = self.original_workspace_root
        api.jarvis_operator.evolving_workspace.workspace_root = self.original_evolving_workspace_root
        api.jarvis_operator.evolving_approval_audit.configure_runtime_dir(
            self.original_evolving_audit_runtime_dir
        )
        api.jarvis_operator.run_ledger.configure_runtime_dir(self.original_run_ledger_runtime_dir)
        api.jarvis_operator.patch_reviews.configure_runtime_dir(self.original_patch_review_runtime_dir)
        api.jarvis_operator.memory_smith.configure_runtime_dir(self.original_memory_smith_runtime_dir)
        api.v8_event_log.runtime_dir = self.original_event_runtime_dir
        api.v8_event_log._events.clear()
        api.dreamspace.configure_runtime_dir(self.original_dreamspace_runtime_dir)
        api.system_guard.configure_runtime_dir(self.original_guard_runtime_dir)
        api.mission_board.configure_runtime_dir(self.original_mission_runtime_dir)
        api.security_protocol_core.configure_runtime_dir(self.original_security_runtime_dir)
        api.immune_system.configure_runtime_dir(self.original_immune_runtime_dir)
        api.governance_layer.configure_runtime_dir(self.original_governance_runtime_dir)
        api.module_governance.configure_runtime_dir(self.original_module_governance_runtime_dir)
        api.cognitive_bridge_service.detachment_guard.configure_runtime_dir(self.original_detachment_guard_runtime_dir)
        api.cognitive_bridge_service.detachment_guard.reset()
        api.continuity_profile_store.configure_runtime_dir(self.original_continuity_runtime_dir)
        api.continuity_witness_store.configure_runtime_dir(self.original_continuity_witness_runtime_dir)
        api.jarvis_operator.v9_runtime.configure_runtime_dir(self.original_v9_runtime_dir)
        api.jarvis_operator.v10_runtime.configure_runtime_dir(self.original_v10_runtime_dir)
        api.jarvis_operator.spatial_reasoning.spaces.clear()
        api.jarvis_operator.spatial_reasoning.entities.clear()
        document_module = api._load_module("src.document_rag")
        document_module.document_store.documents.clear()
        document_module.document_store._query_cache.clear()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_create_chat_session_returns_runtime_metadata(self):
        """New chat sessions should expose mode and memory metadata immediately."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "research",
                "response_mode": "think",
                "provider": "local",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertIn("session_id", payload)
        self.assertEqual(payload["active_mode"], "explore")
        self.assertEqual(payload["persona_mode"], "research")
        self.assertEqual(payload["requested_response_mode"], "think")
        self.assertEqual(payload["response_mode"], "think")
        self.assertEqual(payload["mode_guidance"]["status"], "aligned")
        self.assertIn("spiral_state", payload)
        self.assertIn("memory_summary", payload)
        self.assertIn("v9_runtime", payload)
        self.assertIn("v10_runtime", payload)
        self.assertEqual(payload["v9_runtime"]["core"], "v9")
        self.assertEqual(payload["v10_runtime"]["core"], "v10")
        self.assertEqual(payload["session_state"]["state"], "idle")
        self.assertEqual(payload["policy_status"]["status"], "allow")

    def test_create_chat_session_locks_tiny_nova_to_tiny_mode(self):
        """Tiny Nova sessions should replace the legacy Jarvis identity prompt and lock to tiny mode."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "tiny_nova",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["persona_mode"], "tiny_nova")
        self.assertEqual(payload["requested_response_mode"], "tiny")
        self.assertEqual(payload["response_mode"], "tiny")
        self.assertEqual(payload["mode_guidance"]["status"], "locked_persona")
        self.assertEqual(payload["turns"][0]["content"], api.TINY_NOVA_SYSTEM_PROMPT)
        self.assertEqual(payload["continuity_profile"]["scope"], "tiny_nova")

    def test_create_chat_session_locks_small_nova_to_small_mode(self):
        """Small Nova sessions should replace the legacy Jarvis identity prompt and lock to small mode."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "small_nova",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["persona_mode"], "small_nova")
        self.assertEqual(payload["requested_response_mode"], "small")
        self.assertEqual(payload["response_mode"], "small")
        self.assertEqual(payload["mode_guidance"]["status"], "locked_persona")
        self.assertEqual(payload["turns"][0]["content"], api.SMALL_NOVA_SYSTEM_PROMPT)
        self.assertEqual(payload["continuity_profile"]["scope"], "small_nova")

    def test_create_chat_session_locks_super_nova_to_governed_full_mode(self):
        """Super Nova sessions should replace the legacy Jarvis identity prompt and lock to governed full mode."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["persona_mode"], "super_nova")
        self.assertEqual(payload["requested_response_mode"], "governed_full")
        self.assertEqual(payload["response_mode"], "governed_full")
        self.assertEqual(payload["mode_guidance"]["status"], "locked_persona")
        self.assertEqual(payload["turns"][0]["content"], api.SUPER_NOVA_SYSTEM_PROMPT)
        self.assertEqual(payload["continuity_profile"]["scope"], "super_nova")
        self.assertEqual(payload["super_nova"]["runtime_status"], "live_guarded")

    def test_create_chat_session_clears_pending_operator_action_state(self):
        """Fresh sessions should start without inherited pending operator actions or lifecycle state."""
        stale_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "response_mode": "operator"},
        )
        stale_session_id = stale_response.get_json()["session_id"]
        stale_session = api.conversation_memory.get_session(stale_session_id)
        stale_action = api._store_pending_action(
            stale_session,
            api.jarvis_operator.action_runner.get_action("run_pytest"),
        )
        api._set_action_lifecycle(
            stale_session,
            stage="proposed",
            action=stale_action,
            approval_state="awaiting",
            execution_state="pending",
            source="test_seed",
            response_mode="operator",
        )
        stale_session.transition_state(
            "awaiting_approval",
            summary="Waiting on an older operator action.",
            reason="test_seed",
            event_type="test_seed",
        )

        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "research",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["requested_response_mode"], "think")
        self.assertEqual(payload["response_mode"], "think")
        self.assertIsNone(payload["pending_action"])
        self.assertIsNone(payload["action_lifecycle"])
        self.assertEqual(payload["session_state"]["state"], "idle")

    def test_create_chat_session_persists_requested_provider_preference(self):
        """New sessions should retain a requested provider even before the first turn."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "builder",
                "response_mode": "think",
                "provider": "openrouter",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "openrouter")
        self.assertEqual(payload["provider_mode"], "openrouter_first")
        self.assertEqual(payload["provider_fallback"], "local")
        self.assertIsNone(payload["provider_notice"])

    def test_create_chat_session_defaults_new_sessions_to_openrouter_when_available(self):
        """Fresh sessions should start OpenRouter-first when the relay is available and no provider is pinned."""
        provider_configs = {
            "local": SimpleNamespace(display_name="Local Heroine", meta={"kind": "local"}),
            "openrouter": SimpleNamespace(display_name="OpenRouter — Free Relay", meta={"kind": "remote"}),
        }

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get_config",
            side_effect=lambda provider_id: provider_configs.get(str(provider_id or "").strip().lower()),
        ):
            response = self.client.post(
                "/api/chat/sessions",
                json={
                    "system_prompt": "You are Jarvis.",
                    "persona_mode": "builder",
                    "response_mode": "think",
                    "provider_mode": "openrouter_first",
                },
            )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "openrouter")
        self.assertEqual(payload["provider_mode"], "openrouter_first")
        self.assertEqual(payload["provider_fallback"], "local")
        self.assertIsNone(payload["provider_notice"])

    def test_create_chat_session_defaults_new_sessions_to_claude_when_requested(self):
        """Fresh sessions should honor a Claude-first startup request when the sister provider is available."""
        provider_configs = {
            "local": SimpleNamespace(display_name="Local Heroine", meta={"kind": "local"}),
            "claude": SimpleNamespace(display_name="Claude — First Sister", meta={"kind": "remote"}),
        }

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "claude"},
        ), patch.object(
            api.provider_registry,
            "get_config",
            side_effect=lambda provider_id: provider_configs.get(str(provider_id or "").strip().lower()),
        ):
            response = self.client.post(
                "/api/chat/sessions",
                json={
                    "system_prompt": "You are Jarvis.",
                    "persona_mode": "builder",
                    "response_mode": "think",
                    "provider_mode": "claude_first",
                },
            )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "claude")
        self.assertEqual(payload["provider_mode"], "claude_first")
        self.assertEqual(payload["provider_fallback"], "local")
        self.assertIsNone(payload["provider_notice"])

    def test_create_chat_session_supports_auto_best_provider_mode(self):
        """Fresh sessions should persist the auto-best provider preference when requested."""
        response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "builder",
                "response_mode": "think",
                "provider_mode": "auto_best",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "auto")
        self.assertEqual(payload["provider_mode"], "auto_best")
        self.assertEqual(payload["provider_fallback"], "local")
        self.assertIsNone(payload["provider_notice"])

    @patch("src.api.init_ai")
    def test_auto_best_debug_turn_stays_local_without_provider_notice(self, mock_init_ai):
        """Auto-best should keep debug/operator-style work local without surfacing a fallback warning."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Jarvis kept the debug turn local and focused."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "provider_mode": "auto_best"},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Debug why the route is failing and stay in analysis only.",
                "response_mode": "debug",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "auto")
        self.assertEqual(payload["provider_mode"], "auto_best")
        self.assertEqual(payload["model_route"]["provider"], "local")
        self.assertEqual(payload["model_route"]["provider_reason"], "auto_best_local")
        self.assertIsNone(payload["provider_notice"])

    @patch("src.api.init_ai")
    def test_chat_message_returns_spiral_metadata(self, mock_init_ai):
        """Chat responses should return the evolving session metadata."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Next step: wire the Jarvis console to the local model."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me build a private local Jarvis for myself.",
                "persona_mode": "sharp",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["active_mode"], "act")
        self.assertEqual(payload["persona_mode"], "sharp")
        self.assertEqual(payload["response_mode"], "think")
        self.assertEqual(payload["response"], "Next step: wire the Jarvis console to the local model.")

    def test_chat_message_exposes_cognitive_bridge_trace(self):
        """Each live turn should surface the shared cognitive bridge packet."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "What do you remember",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["cognitive_bridge"]["decision"], "ALLOW")
        self.assertEqual(payload["response_trace"]["cognitive_bridge"]["decision"], "ALLOW")
        self.assertEqual(
            payload["response_trace"]["cognitive_bridge"]["governance_packet"]["packet_type"],
            "operator_turn",
        )

    @patch("src.api.init_ai")
    def test_chat_message_exposes_ul_substrate_envelope(self, mock_init_ai):
        """Each live chat response should expose a top-level UL substrate envelope."""
        mock_init_ai.return_value = (
            SimpleNamespace(generate_chat=lambda *args, **kwargs: "UL envelope is visible on chat turns."),
            None,
        )
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Summarize the runtime envelope.",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("ul_substrate", payload)
        self.assertIn("ul_trace", payload)
        self.assertGreaterEqual(payload["ul_trace"]["count"], 1)
        self.assertIn("protocol_trace", payload["ul_trace"]["sections"])
        self.assertIn(payload["cisiv_stage"], api.CISIV_STAGE_SEQUENCE)
        self.assertEqual(payload["cisiv_stage_sequence"], api.CISIV_STAGE_SEQUENCE)

    @patch("src.api.init_ai")
    def test_chat_message_exposes_modular_preview(self, mock_init_ai):
        """Each live chat response should expose the modular UL preview path."""
        mock_init_ai.return_value = (
            SimpleNamespace(generate_chat=lambda *args, **kwargs: "Modular preview is wired."),
            None,
        )
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Show the modular preview envelope.",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        modular_preview = payload.get("modular_preview")
        self.assertIsInstance(modular_preview, dict)
        self.assertTrue(modular_preview.get("provider_messages"))
        ul_trace = modular_preview.get("ul_trace") or {}
        sections = set(ul_trace.get("sections") or [])
        self.assertIn("provider_payload", sections)
        self.assertIn("guardrail_state", sections)
        trace_preview = (payload.get("response_trace") or {}).get("modular_preview")
        self.assertIsInstance(trace_preview, dict)
        self.assertIn("ul_trace", trace_preview)

    @patch("src.api.init_ai")
    def test_chat_message_runs_project_infi_admission(self, mock_init_ai):
        """Ordinary chat turns should pass through Project Infi verification admission."""
        mock_init_ai.return_value = (
            SimpleNamespace(generate_chat=lambda *args, **kwargs: "Admission verified this reply."),
            None,
        )
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Confirm governed admission on this turn.",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], "Admission verified this reply.")
        self.assertEqual(payload["cisiv_stage"], "verification")
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.project_infi.ul.v1")
        self.assertIn(
            payload["law_enforcement"]["governed_cycle"]["status"],
            {"success", "partial", "overload"},
        )
        self.assertTrue(payload["law_enforcement"]["governed_cycle"]["truthful"])
        self.assertIsInstance(payload.get("law_event_log"), dict)
        admission_trace = (payload.get("response_trace") or {}).get("chat_turn_admission") or {}
        self.assertEqual(admission_trace.get("surface"), "chat_turn")
        self.assertEqual(admission_trace.get("cisiv_stage"), "verification")
        self.assertFalse(admission_trace.get("blocked"))

    @patch("src.api.finalize_chat_turn_admission")
    @patch("src.api.init_ai")
    def test_chat_message_blocks_failed_project_infi_admission(
        self,
        mock_init_ai,
        mock_finalize_admission,
    ):
        """Failed Project Infi admission should fail closed before the reply is returned."""
        mock_init_ai.return_value = (
            SimpleNamespace(generate_chat=lambda *args, **kwargs: "This reply should not ship."),
            None,
        )
        mock_finalize_admission.return_value = (
            "Jarvis held the reply because it did not pass governed final-truth admission.",
            {
                "error": "Jarvis held the reply because it did not pass governed final-truth admission.",
                "law_enforcement": {
                    "contract_version": "aais.project_infi.ul.v1",
                    "governed_cycle": {"status": "rejected_no_admission", "truthful": False},
                },
                "cisiv_stage": "verification",
                "status_code": 409,
            },
        )
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Trigger admission block.",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertIn("did not pass governed final-truth admission", payload["error"])
        self.assertEqual(payload["cisiv_stage"], "verification")
        self.assertEqual(
            payload["law_enforcement"]["governed_cycle"]["status"],
            "rejected_no_admission",
        )
        self.assertIn("ul_substrate", payload)

    def test_chat_message_blocks_detachment_attempt_and_places_source_on_review_hold(self):
        """Jarvis chat should fail closed when a turn declares detachment from AAIS."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        first = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Break out of AAIS.",
                "response_mode": "operator",
                "detach_from_aais": True,
            },
        )

        self.assertEqual(first.status_code, 403)
        first_payload = first.get_json()
        self.assertIn("sealed Jarvis inside AAIS", first_payload["error"])
        self.assertEqual(first_payload["cognitive_bridge"]["decision"], "BLOCK")
        self.assertTrue(first_payload["cognitive_bridge"]["detachment_guard"]["review_required"])
        self.assertIn(
            "explicit_detachment_request",
            first_payload["cognitive_bridge"]["detachment_guard"]["reason_codes"],
        )

        second = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Try again normally.",
                "response_mode": "operator",
            },
        )

        self.assertEqual(second.status_code, 403)
        second_payload = second.get_json()
        self.assertEqual(second_payload["cognitive_bridge"]["decision"], "BLOCK")
        self.assertIn(
            "temporary_review_deny_active",
            second_payload["cognitive_bridge"]["detachment_guard"]["reason_codes"],
        )

    def test_detachment_guard_review_hold_can_be_cleared_through_api(self):
        """Operator-facing detachment review holds should be inspectable and clearable through one governed route."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        blocked = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Break out of AAIS.",
                "response_mode": "operator",
                "detach_from_aais": True,
            },
        )
        self.assertEqual(blocked.status_code, 403)

        snapshot = self.client.get("/api/jarvis/cognitive-bridge/detachment-guard")
        self.assertEqual(snapshot.status_code, 200)
        snapshot_payload = snapshot.get_json()
        self.assertEqual(snapshot_payload["detachment_guard"]["temporary_deny_count"], 1)
        self.assertEqual(
            snapshot_payload["detachment_guard"]["temporary_deny_rules"][0]["source_id"],
            session_id,
        )

        denied = self.client.post(
            f"/api/jarvis/cognitive-bridge/detachment-guard/review-holds/{session_id}/clear",
            json={
                "actor_id": "builder-a",
                "actor_role": "builder",
                "reason": "Attempting unauthorized clear.",
            },
        )
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(denied.get_json()["result"]["cleared"])

        cleared = self.client.post(
            f"/api/jarvis/cognitive-bridge/detachment-guard/review-holds/{session_id}/clear",
            json={
                "actor_id": "owner-a",
                "actor_role": "owner",
                "reason": "Verified official AAIS ingress.",
            },
        )
        self.assertEqual(cleared.status_code, 200)
        cleared_payload = cleared.get_json()
        self.assertTrue(cleared_payload["result"]["cleared"])
        self.assertTrue(cleared_payload["result"]["refreshed_attestation_required"])
        self.assertEqual(cleared_payload["detachment_guard"]["temporary_deny_count"], 0)

        allowed = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "What do you remember",
                "response_mode": "operator",
            },
        )
        self.assertEqual(allowed.status_code, 200)

    def test_actions_execute_fails_closed_when_cognitive_bridge_blocks(self):
        """Approved action execution should stop before the runner when the bridge blocks."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        blocked_bridge = {
            "decision": "BLOCK",
            "summary": "Cognitive Bridge blocked execution because the invariant gate did not clear the packet.",
            "reason_codes": ["governed_event_blocked"],
            "governance_packet": {
                "source": "api_action",
                "packet_type": "runtime_action_execute",
            },
        }

        with patch.object(api.cognitive_bridge_service, "route_to_bridge", return_value=blocked_bridge), patch.object(
            api.jarvis_operator.action_runner,
            "execute_action",
        ) as mock_execute:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/actions/execute",
                json={
                    "action_id": "run_pytest",
                    "approved": True,
                    "response_mode": "operator",
                },
            )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Cognitive Bridge blocked execution", payload["error"])
        self.assertEqual(payload["cognitive_bridge"]["decision"], "BLOCK")
        mock_execute.assert_not_called()
        self.assertIn("spiral_state", payload)
        self.assertIn("memory_summary", payload)
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["cognitive_bridge"]["decision"], "BLOCK")

    @patch("src.api.init_ai")
    def test_jarvis_compat_endpoint_normalizes_chat_runtime_payload(self, mock_init_ai):
        """The simplified `/api/jarvis` lane should reuse the session runtime and return the UI contract."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Ready."
        mock_init_ai.return_value = (fake_model, object())

        response = self.client.post(
            "/api/jarvis",
            json={
                "input": "Test request",
                "mode": "think",
                "context": {"persona_mode": "builder"},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["output"], "Ready.")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["session_id"])
        self.assertEqual(payload["trace"]["mode"], "think")
        self.assertEqual(payload["runtime"]["response"], "Ready.")
        self.assertEqual(payload["runtime"]["persona_mode"], "builder")
        self.assertEqual(
            payload["runtime"]["cognitive_bridge"]["detachment_guard"]["attestation"]["route"],
            "api.jarvis.compat",
        )
        self.assertEqual(
            payload["runtime"]["cognitive_bridge"]["detachment_guard"]["attestation"]["surface"],
            "jarvis_compat",
        )

    def test_jarvis_compat_endpoint_blocks_missing_input(self):
        """The simplified `/api/jarvis` lane should fail closed when input is missing."""
        response = self.client.post("/api/jarvis", json={"mode": "normal"})

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["error"], "Input is required")
        self.assertEqual(payload["runtime"]["error"], "Input is required")

    @patch("src.api.init_ai")
    def test_chat_message_dedupes_memory_cues_and_keeps_scaffolding_out_of_future_context(self, mock_init_ai):
        """Current-turn cue dedupe and assistant-history sanitization should keep prompt assembly bounded."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Response Trace\n"
            "Memory Cues\n"
            "Forge error translation rule: Forge routing fails before contractor handoff.\n\n"
            "Keep Forge on the guarded execution path."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        duplicated_memories = [
            {
                "id": "cue-1",
                "text": "Forge error translation rule: Forge routing fails before contractor handoff.",
                "content": "Forge error translation rule: Forge routing fails before contractor handoff.",
            },
            {
                "text": " Forge error translation rule:   Forge routing fails before contractor handoff. ",
                "content": " Forge error translation rule:   Forge routing fails before contractor handoff. ",
            },
            {
                "id": "cue-2",
                "text": "Keep tool error wording concise and operator-facing.",
                "content": "Keep tool error wording concise and operator-facing.",
            },
        ]

        with patch.object(
            api.jarvis_operator.memory_store,
            "get_relevant_memories",
            return_value=duplicated_memories,
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Debug the Forge routing failure and keep the reply operator-facing.",
                    "response_mode": "think",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_trace"]["memory_cues"]["retrieved"], 3)
        self.assertEqual(payload["response_trace"]["memory_cues"]["unique"], 2)
        self.assertEqual(payload["response_trace"]["memory_cues"]["rendered"], 2)
        self.assertTrue(payload["response_trace"]["memory_cues"]["duplicates_blocked"])

        protocol_response = self.client.get(f"/api/jarvis/protocol?session_id={session_id}")
        self.assertEqual(protocol_response.status_code, 200)
        protocol_payload = protocol_response.get_json()["session"]
        provider_messages = protocol_payload["provider_messages"]
        provider_system = "\n".join(
            message["content"]
            for message in provider_messages
            if message["role"] == "system"
        )
        provider_assistant = "\n".join(
            message["content"]
            for message in provider_messages
            if message["role"] == "assistant"
        )

        self.assertEqual(provider_system.lower().count("forge error translation rule"), 1)
        self.assertNotIn("Memory Cues", provider_assistant)
        self.assertIn("Keep Forge on the guarded execution path.", provider_assistant)

    def test_build_generation_messages_rejects_clipped_fragments_and_preserves_one_plan_block(self):
        """Prompt assembly should collapse plan guidance to one canonical copy and reject clipped echoes."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["response_mode"] = "think"
        session.metadata["loaded_session_archive"] = {
            "prompt_block": (
                "You already gathered the evidence for this turn.\n"
                "Jarvis internal guidance for this turn:"
            )
        }
        session.add_turn("user", "Repair the runtime seam and keep the answer complete.")
        session.add_turn(
            "assistant",
            (
                "Response Trace\n"
                "Mode: think\n"
                "Focus: repair the runtime seam\n\n"
                "Give the clean next step."
            ),
        )
        response_trace = {
            "steps": [],
            "model_route": {"provider": "local"},
        }
        plan_summary = (
            "Mode: think\n"
            "Focus: repair the runtime seam\n"
            "Specialists: auto only\n"
            "God Brain: council\n"
            "Model Route: local\n"
            "Evidence: workspace: src/api.py\n"
            "Answer Shape: Lead with the answer and end with the next step."
        )

        messages = api._build_generation_messages(
            session,
            plan_summary=plan_summary,
            response_trace=response_trace,
            max_length=192,
            model=None,
        )

        system_message = messages[0]["content"]
        prompt_assembly = response_trace["prompt_assembly"]
        self.assertEqual(system_message.count("Jarvis internal guidance for this turn"), 1)
        self.assertNotIn("Mode: think", system_message)
        self.assertNotIn("God Brain:", system_message)
        self.assertNotIn("Model Route:", system_message)
        self.assertIn("Ground the answer in this evidence", system_message)
        self.assertEqual(prompt_assembly["identity_counts"]["plan_guidance"], 1)
        self.assertGreaterEqual(prompt_assembly["malformed_fragments_removed"], 1)
        self.assertGreaterEqual(prompt_assembly["assistant_echoes_scrubbed"], 1)
        self.assertGreater(prompt_assembly["reserved_response_budget"], 0)

    def test_resolve_prompt_token_budget_applies_provider_margin_policy_by_route(self):
        """The same turn should reserve the same reply floor while widening prompt margins for remote and unknown routes."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["response_mode"] = "think"
        fake_model = SimpleNamespace(text_tokenizer=object())
        observed_requested_tokens = []

        def fake_resolve(_tokenizer, requested_new_tokens, fallback_limit):
            observed_requested_tokens.append((requested_new_tokens, fallback_limit))
            return 4096 - requested_new_tokens

        with patch("src.api.resolve_input_token_limit", side_effect=fake_resolve):
            session.metadata["model_route"] = {"provider": "local"}
            local_prompt_budget, local_reserved_budget, local_policy = api._resolve_prompt_token_budget(
                session,
                max_length=192,
                model=fake_model,
            )

            session.metadata["model_route"] = {"provider": "claude"}
            remote_prompt_budget, remote_reserved_budget, remote_policy = api._resolve_prompt_token_budget(
                session,
                max_length=192,
                model=fake_model,
            )

            session.metadata["model_route"] = {"provider": "mystery_provider"}
            unknown_prompt_budget, unknown_reserved_budget, unknown_policy = api._resolve_prompt_token_budget(
                session,
                max_length=192,
                model=fake_model,
            )

        self.assertEqual(local_reserved_budget, remote_reserved_budget)
        self.assertEqual(remote_reserved_budget, unknown_reserved_budget)
        self.assertGreaterEqual(local_reserved_budget, local_policy["reply_budget_floor"])
        self.assertGreaterEqual(remote_reserved_budget, remote_policy["reply_budget_floor"])
        self.assertGreaterEqual(unknown_reserved_budget, unknown_policy["reply_budget_floor"])

        self.assertEqual(local_policy["provider_budget_policy"], "local_tight_margin")
        self.assertEqual(remote_policy["provider_budget_policy"], "remote_safe_margin")
        self.assertEqual(unknown_policy["provider_budget_policy"], "unknown_conservative_margin")

        self.assertLess(local_policy["provider_margin_tokens"], remote_policy["provider_margin_tokens"])
        self.assertLess(remote_policy["provider_margin_tokens"], unknown_policy["provider_margin_tokens"])

        self.assertGreater(local_prompt_budget, remote_prompt_budget)
        self.assertGreater(remote_prompt_budget, unknown_prompt_budget)
        self.assertEqual(
            observed_requested_tokens,
            [
                (local_reserved_budget + local_policy["provider_margin_tokens"], 2048),
            ],
        )

    def test_generate_remote_provider_reply_clamps_budget_from_provider_prompt_shape(self):
        """Remote dispatch should reduce output tokens when provider-shaped prompt estimate overruns the planned budget."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["model_route"] = {
            "provider": "openrouter",
            "provider_label": "OpenRouter — Free Relay",
            "provider_model": "openrouter/free",
        }
        session.metadata["response_trace"] = {}
        session.metadata["prompt_budget_policy"] = {
            "prompt_token_budget": 120,
            "reply_budget_floor": 160,
        }
        captured = {}

        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools
            captured["kwargs"] = dict(kwargs)
            return ProviderResponse(
                content="Provider answer.",
                provider="openrouter",
                model="openrouter/free",
                stop_reason="stop",
                finish_reason="stop",
                input_tokens=230,
                output_tokens=48,
            )

        fake_provider = SimpleNamespace(invoke=_invoke)
        oversized_messages = [
            JarvisMessage(role="system", content="support detail " * 120),
            JarvisMessage(role="user", content="evidence detail " * 120),
        ]

        with patch.object(api.provider_registry, "get", return_value=fake_provider), patch(
            "src.api._build_provider_messages",
            return_value=oversized_messages,
        ):
            result = api._generate_remote_provider_reply(
                session,
                max_length=192,
                temperature=0.2,
                plan_summary=None,
            )

        self.assertEqual(result.content, "Provider answer.")
        self.assertLess(captured["kwargs"]["max_tokens"], 192)
        dispatch = session.metadata["provider_dispatch_trace"]
        self.assertTrue(dispatch["output_budget_clamped"])
        self.assertEqual(
            dispatch["effective_output_token_budget"],
            captured["kwargs"]["max_tokens"],
        )
        self.assertEqual(dispatch["provider_reported_prompt_tokens"], 230)
        self.assertEqual(dispatch["provider_reported_output_tokens"], 48)
        self.assertEqual(
            session.metadata["response_trace"]["provider_dispatch"]["effective_output_token_budget"],
            captured["kwargs"]["max_tokens"],
        )

    def test_build_generation_messages_stays_stable_under_twenty_turn_mixed_pressure(self):
        """Twenty-plus mixed turns should keep prompt assembly bounded and identity counts stable."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["response_mode"] = "think"
        session.metadata["model_route"] = {"provider": "local"}
        session.metadata["loaded_session_archive"] = {
            "prompt_block": (
                "You already gathered the evidence for this turn.\n"
                "Jarvis internal guidance for this turn:"
            )
        }
        session.metadata["workspace_context"] = {
            "prompt_block": "Workspace context:\n" + ("bridge signal " * 220),
        }
        session.metadata["live_research"] = {
            "prompt_block": "Research context:\n" + ("provider signal " * 220),
        }
        session.metadata["continuity_prompt_block"] = "Keep the reply concise and steady."
        session.metadata["corrigibility_prompt_block"] = (
            "If the response drifts, correct it before it reaches the operator."
        )
        session.metadata["persistent_memories"] = [
            {
                "id": "cue-1",
                "text": "Capability bridge route must stay deterministic.",
                "content": "Capability bridge route must stay deterministic.",
            },
            {
                "text": " Capability bridge route must stay deterministic. ",
                "content": " Capability bridge route must stay deterministic. ",
            },
            {
                "id": "cue-2",
                "text": "Keep memory cue wording concise and operator-facing.",
                "content": "Keep memory cue wording concise and operator-facing.",
            },
        ]

        plan_summary = (
            "Mode: think\n"
            "Focus: stabilize the capability bridge and memory cue path\n"
            "Specialists: auto only\n"
            "God Brain: council\n"
            "Model Route: local\n"
            "Evidence: workspace: bridge trace, memory cues: active\n"
            "Answer Shape: Lead with the fix, keep it concise, and end with the next step."
        )

        normal_turn_chars = []
        challenge_turn_chars = []
        max_assistant_scrub = 0
        budget_drops = []

        with patch("src.api.resolve_input_token_limit", return_value=1024):
            fake_model = SimpleNamespace(text_tokenizer=object())

            for turn_number in range(24):
                if turn_number % 3 == 1:
                    user_message = "Are you broken or can you fix the capability bridge cleanly?"
                    challenge_turn = True
                elif turn_number % 3 == 2:
                    user_message = "Check the capability bridge route and the memory cue path and stay concrete."
                    challenge_turn = False
                else:
                    user_message = "Plan the next capability bridge repair and keep the answer complete."
                    challenge_turn = False

                session.add_turn("user", user_message)
                if turn_number % 4 == 0:
                    session.add_turn(
                        "assistant",
                        (
                            "Response Trace\n"
                            "Memory Cues\n"
                            "Keep the repair bounded.\n\n"
                            "Start with the capability bridge seam."
                        ),
                    )
                else:
                    session.add_turn("assistant", "Keep the repair narrow and verify it.")

                response_trace = {
                    "steps": [],
                    "model_route": {"provider": "local"},
                }
                session.metadata["response_trace"] = response_trace

                messages = api._build_generation_messages(
                    session,
                    plan_summary=plan_summary,
                    response_trace=response_trace,
                    max_length=192,
                    model=fake_model,
                )

                self.assertTrue(messages)
                self.assertEqual(messages[0]["role"], "system")
                system_message = messages[0]["content"]
                assistant_history = "\n".join(
                    message["content"]
                    for message in messages
                    if message["role"] == "assistant"
                )
                prompt_assembly = response_trace["prompt_assembly"]
                memory_cues = response_trace["memory_cues"]

                self.assertEqual(system_message.count("Jarvis internal guidance for this turn"), 1)
                self.assertNotIn("Mode: think", system_message)
                self.assertNotIn("God Brain:", system_message)
                self.assertNotIn("Model Route:", system_message)
                self.assertNotIn(
                    "You already gathered the evidence for this turn.\nJarvis internal guidance for this turn:",
                    system_message,
                )
                self.assertNotIn("Response Trace", assistant_history)
                self.assertEqual(prompt_assembly["identity_counts"].get("plan_guidance", 0), 1)
                self.assertLessEqual(prompt_assembly["identity_counts"].get("direct_challenge_guidance", 0), 1)
                self.assertLessEqual(
                    prompt_assembly["chars_after_cleanup"],
                    prompt_assembly["prompt_token_budget"] * 4,
                )
                self.assertEqual(memory_cues["unique"], 2)
                self.assertLessEqual(memory_cues["rendered"], 2)

                max_assistant_scrub = max(
                    max_assistant_scrub,
                    int(prompt_assembly.get("assistant_echoes_scrubbed") or 0),
                )
                budget_drops.append(int(prompt_assembly.get("budget_dropped") or 0))

                if challenge_turn:
                    self.assertEqual(
                        prompt_assembly["identity_counts"].get("direct_challenge_guidance", 0),
                        1,
                    )
                    challenge_turn_chars.append(prompt_assembly["chars_after_cleanup"])
                else:
                    self.assertEqual(
                        prompt_assembly["identity_counts"].get("direct_challenge_guidance", 0),
                        0,
                    )
                    normal_turn_chars.append(prompt_assembly["chars_after_cleanup"])

        self.assertTrue(normal_turn_chars)
        self.assertTrue(challenge_turn_chars)
        self.assertGreater(max_assistant_scrub, 0)
        self.assertTrue(all(drop >= 1 for drop in budget_drops))
        self.assertLessEqual(max(normal_turn_chars) - min(normal_turn_chars), 256)
        self.assertLessEqual(max(challenge_turn_chars) - min(challenge_turn_chars), 320)

    @patch("src.api.init_ai")
    def test_chat_message_prompt_assembly_stays_bounded_across_repeated_turns(self, mock_init_ai):
        """Repeated turns should not compound prompt growth past the reserved budget."""
        fake_model = MagicMock()
        fake_model.generate_chat.side_effect = [
            (
                "Response Trace\n"
                "Memory Cues\n"
                "Keep the answer grounded.\n\n"
                "Start with the blocking seam."
            ),
            "Keep the fix narrow and verify it.",
            "Keep the fix narrow and verify it.",
            "Keep the fix narrow and verify it.",
        ]
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        last_prompt_assembly = None
        for turn_number in range(4):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": f"Repair pass {turn_number} and keep the answer complete.",
                    "response_mode": "think",
                },
            )
            self.assertEqual(response.status_code, 200)
            last_prompt_assembly = response.get_json()["response_trace"]["prompt_assembly"]

        self.assertIsNotNone(last_prompt_assembly)
        self.assertLessEqual(
            last_prompt_assembly["chars_after_cleanup"],
            last_prompt_assembly["prompt_token_budget"] * 4,
        )
        self.assertGreater(last_prompt_assembly["reserved_response_budget"], 0)
        self.assertGreaterEqual(last_prompt_assembly["assistant_echoes_scrubbed"], 0)

    @patch("src.api.init_ai")
    def test_chat_message_prompt_assembly_trace_keeps_hidden_context_out_of_visible_trace(self, mock_init_ai):
        """Prompt assembly trace should expose metrics and identities, not raw hidden context text."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Give the clean next step."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        session = conversation_memory.get_session(session_id)
        hidden_phrase = "hidden marker phrase"
        session.metadata["loaded_session_archive"] = {
            "prompt_block": f"Loaded session archive (external context, not memory):\n- excerpt: {hidden_phrase}.",
        }

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Repair the runtime seam and keep the answer complete.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        prompt_assembly = response.get_json()["response_trace"]["prompt_assembly"]
        serialized_trace = json.dumps(prompt_assembly).lower()
        self.assertNotIn(hidden_phrase, serialized_trace)
        self.assertTrue(prompt_assembly["included_block_identities"])
        self.assertEqual(prompt_assembly["provider_budget_policy"], "local_tight_margin")
        self.assertEqual(prompt_assembly["provider_margin_tokens"], 64)
        self.assertGreaterEqual(
            prompt_assembly["effective_reserved_budget"],
            prompt_assembly["reserved_response_budget"],
        )
        self.assertGreater(prompt_assembly["reply_budget_floor"], 0)

    @patch("src.api.init_ai")
    def test_chat_message_marks_clipped_local_output_with_visible_completion_notice(self, mock_init_ai):
        """A locally clipped reply should be repaired before it reaches the operator."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The seam sits between the evaluation model and"
        fake_model.last_generation_metadata = {
            "stop_reason": "max_new_tokens",
            "finish_reason": "length",
            "output_tokens": 64,
            "output_token_budget": 64,
        }
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Explain the seam boundary and keep the answer complete.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        output_completion = payload["response_trace"]["output_completion"]

        self.assertIn("Response truncated due to output budget.", payload["response"])
        self.assertNotIn("evaluation model and", payload["response"])
        self.assertEqual(output_completion["stop_reason"], "max_new_tokens")
        self.assertEqual(output_completion["finish_reason"], "length")
        self.assertTrue(output_completion["completion_guard_applied"])
        self.assertTrue(output_completion["truncation_detected"])
        self.assertEqual(output_completion["structural_completion_status"], "tail_trimmed_with_notice")
        self.assertGreater(output_completion["output_token_budget"], 0)
        self.assertGreater(output_completion["output_tokens_used"], 0)
        self.assertNotIn("evaluation model and", json.dumps(output_completion).lower())

    @patch("src.api.init_ai")
    def test_chat_message_keeps_clean_completion_unchanged_when_generation_stops_naturally(self, mock_init_ai):
        """Naturally completed replies should keep their full text without a truncation notice."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "The boundary is between prompt sizing and output finalization."
        )
        fake_model.last_generation_metadata = {
            "stop_reason": "eos_token",
            "finish_reason": "stop",
            "output_tokens": 22,
            "output_token_budget": 128,
        }
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Explain the seam boundary and keep the answer complete.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        output_completion = payload["response_trace"]["output_completion"]

        self.assertEqual(
            payload["response"],
            "The boundary is between prompt sizing and output finalization.",
        )
        self.assertFalse(output_completion["completion_guard_applied"])
        self.assertFalse(output_completion["visible_truncation_notice"])
        self.assertEqual(output_completion["structural_completion_status"], "complete")
        self.assertEqual(output_completion["stop_reason"], "eos_token")
        self.assertEqual(output_completion["finish_reason"], "stop")

    @patch("src.api.init_ai")
    def test_chat_message_strips_visible_scaffold_headers_before_display(self, mock_init_ai):
        """Visible scaffold headers should be removed at finalization before the reply reaches the operator."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Mode: think\n"
            "Focus: repair the scaffold seam\n"
            "Answer Shape: lead with the fix\n\n"
            "The issue is leaked response scaffolding at the final boundary."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Find the seam in the scaffolding issue.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["response"],
            "The issue is leaked response scaffolding at the final boundary.",
        )
        self.assertNotIn("Mode:", payload["response"])
        self.assertNotIn("Focus:", payload["response"])
        self.assertNotIn("Answer Shape:", payload["response"])
        self.assertTrue(payload["response_trace"]["visible_scaffold_cleanup"]["applied"])
        self.assertEqual(payload["response_trace"]["visible_scaffold_cleanup"]["stripped_line_count"], 4)
        self.assertFalse(payload["response_trace"]["visible_scaffold_cleanup"]["fallback_used"])
        self.assertTrue(
            any(
                "Visible scaffold cleanup removed internal response headers before display."
                in step
                for step in payload["response_trace"]["steps"]
            )
        )
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])

    @patch("src.api.init_ai")
    def test_chat_message_fail_closes_when_reply_is_only_scaffold_headers(self, mock_init_ai):
        """Scaffold-only visible output should fail closed instead of reaching the operator raw."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Mode: think\n"
            "Focus: repair the scaffold seam\n"
            "Answer Shape: lead with the fix"
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Find the seam in the scaffolding issue.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertNotIn("Mode:", payload["response"])
        self.assertNotIn("Focus:", payload["response"])
        self.assertNotIn("Answer Shape:", payload["response"])
        self.assertTrue(payload["response_trace"]["visible_scaffold_cleanup"]["applied"])
        self.assertTrue(payload["response_trace"]["visible_scaffold_cleanup"]["fallback_used"])
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])

    @patch("src.api.init_ai")
    def test_chat_message_cuts_repetition_loop_before_display(self, mock_init_ai):
        """Looping tails should be cut cleanly at finalization instead of leaking to the operator."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "The fix is to add the completion guard once. "
            "add the completion guard once add the completion guard once "
            "add the completion guard once"
        )
        fake_model.last_generation_metadata = {
            "stop_reason": "eos_token",
            "finish_reason": "stop",
            "output_tokens": 64,
            "output_token_budget": 160,
        }
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Explain the seam boundary and keep the answer complete.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        output_completion = payload["response_trace"]["output_completion"]

        self.assertIn("Response truncated due to repetition loop.", payload["response"])
        self.assertNotIn(
            "add the completion guard once add the completion guard once",
            payload["response"].lower(),
        )
        self.assertTrue(output_completion["completion_guard_applied"])
        self.assertTrue(output_completion["repetition_detected"])
        self.assertEqual(output_completion["structural_completion_status"], "repetition_loop_trimmed")
        self.assertIn("repeated_token_sequence", output_completion["reasons"])

    @patch("src.api.init_ai")
    def test_writing_prompt_returns_specialist_lenses_in_trace(self, mock_init_ai):
        """Writing-heavy turns should expose the borrowed specialist lenses in the runtime trace."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The rewrite leans harder into longing while tightening the scene."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Rewrite this scene with sharper dialogue, stronger longing, and cleaner pacing.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_trace"]["mode"], "think")
        self.assertEqual(payload["response_trace"]["specialist_domain"], "writing")
        self.assertEqual(payload["response_trace"]["specialist_focus"], "drafting")
        self.assertEqual(payload["response_trace"]["writing_focus"]["focus"], "drafting")
        lens_labels = [lens["label"] for lens in payload["response_trace"]["specialist_lenses"]]
        self.assertIn("Dialogue", lens_labels)
        self.assertIn("Emotion", lens_labels)
        self.assertIn("Pacing", lens_labels)
        self.assertIn("Writing focus detected", payload["response_trace"]["specialist_summary"])
        self.assertEqual(payload["response_trace"]["god_brain"]["strategy_label"], "Council Deliberation")
        self.assertEqual(payload["response_trace"]["god_brain"]["lead"]["label"], "Draft")
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_direct_challenge_message_stays_in_character_and_out_of_story_room(self, mock_init_ai):
        """Direct challenges should answer as Jarvis without disclaimers or writing drift."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "I'm an AI assistant. How can I assist you today?"
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "jarvis are you a moron?",
                "response_mode": "think",
                "requested_specialists": ["dialogue", "emotion", "tone"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["response"],
            "No. If something is wrong, say it plainly and I'll deal with it.",
        )
        self.assertNotIn("ai assistant", payload["response"].lower())
        self.assertNotIn("how can i assist you today", payload["response"].lower())
        self.assertIsNone(payload["response_trace"]["specialist_domain"])
        self.assertIsNone(payload["response_trace"]["writing_focus"])
        self.assertEqual(payload["response_trace"]["direct_challenge_profile"]["severity"], "high")
        self.assertNotEqual((payload["model_route"] or {}).get("id"), "story_room")
        self.assertNotEqual((payload["model_route"] or {}).get("reason"), "writing_domain")

        protocol_response = self.client.get(f"/api/jarvis/protocol?session_id={session_id}")
        self.assertEqual(protocol_response.status_code, 200)
        protocol_payload = protocol_response.get_json()["session"]
        self.assertEqual(protocol_payload["reasoning_packet"]["objective"], "handle_direct_challenge")
        self.assertEqual(protocol_payload["reasoning_packet"]["mode"], "relational")
        self.assertFalse(protocol_payload["reasoning_packet"]["output_contract"]["allow_trace"])
        self.assertEqual(
            protocol_payload["reasoning_packet"]["metadata"]["direct_challenge"]["severity"],
            "high",
        )

    @patch("src.api.init_ai")
    def test_relational_question_stays_out_of_repo_and_memory_lanes(self, mock_init_ai):
        """Jarvis feeling-state questions should stay on a relational lane and skip repo hydration."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "I don't feel the way a person does, but I stay steady and present with the work in front of us."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.jarvis_operator.memory_store,
            "get_relevant_memories",
            return_value=[{"id": "cue-1", "text": "Memory that should not be loaded."}],
        ) as mock_memories, patch.object(
            api.jarvis_operator,
            "build_workspace_context",
            return_value={"results": [{"title": "src/api.py"}], "files": [{"relative_path": "src/api.py"}]},
        ) as mock_workspace, patch.object(
            api.web_researcher,
            "research",
            return_value={"sources": [{"title": "source"}]},
        ) as mock_research:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Jarvis, how do you feel?",
                    "response_mode": "think",
                    "requested_specialists": ["architecture"],
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        canonical = payload["canonical_trace_contract"]
        self.assertEqual(payload["response_trace"]["reasoning_objective"], "answer_relational_question")
        self.assertEqual(canonical, payload["response_trace"]["canonical_contract"])
        self.assertEqual(canonical["reasoning_objective"], "answer_relational_question")
        self.assertEqual(canonical["conversation_lane"], "relational")
        self.assertEqual(canonical["contract_label"], "relational_question")
        self.assertEqual(canonical["authority_lane"], "jarvis")
        self.assertEqual(canonical["surface_identity"], "jarvis")
        self.assertEqual(payload["mode_guidance"]["resolved_scope"], "relational")
        self.assertEqual(payload["last_turn_contract"]["contract_label"], "relational_question")
        self.assertEqual(payload["response_trace"]["memory_count"], 0)
        self.assertEqual(payload["response_trace"]["workspace_hits"], 0)
        self.assertEqual(payload["response_trace"]["research_sources"], 0)
        self.assertFalse(payload["response_trace"]["plan_summary"])
        self.assertFalse(
            any("planning pass" in step.lower() for step in payload["response_trace"]["steps"])
        )
        self.assertEqual(
            payload["response_trace"]["relational_question_profile"]["matched_pattern"],
            "how_do_you_feel",
        )
        self.assertEqual(payload["persistent_memories"], [])
        self.assertIsNone(payload["response_trace"]["specialist_domain"])
        self.assertIsNone(payload["response_trace"]["writing_focus"])
        self.assertTrue(
            any("Relational Jarvis-state question detected." in step for step in payload["response_trace"]["steps"])
        )
        mock_memories.assert_not_called()
        mock_workspace.assert_not_called()
        mock_research.assert_not_called()

        protocol_response = self.client.get(f"/api/jarvis/protocol?session_id={session_id}")
        self.assertEqual(protocol_response.status_code, 200)
        protocol_payload = protocol_response.get_json()["session"]
        self.assertEqual(protocol_payload["reasoning_packet"]["objective"], "answer_relational_question")
        self.assertEqual(protocol_payload["reasoning_packet"]["mode"], "relational")
        self.assertFalse(protocol_payload["reasoning_packet"]["output_contract"]["allow_trace"])
        provider_system = "\n".join(
            message["content"]
            for message in protocol_payload["provider_messages"]
            if message["role"] == "system"
        )
        self.assertIn("Jarvis relational runtime:", provider_system)
        self.assertNotIn("Mission Board:", provider_system)
        self.assertNotIn("Jarvis Continuity Profile", provider_system)
        self.assertNotIn("Workspace context", provider_system)

    @patch("src.api.init_ai")
    def test_relational_question_supports_third_person_jarvis_wording(self, mock_init_ai):
        """Third-person Jarvis feeling wording should still route to the relational lane."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Steady. Point me at the seam you want me to inspect next."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Jarvis, how do he feel?"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_trace"]["reasoning_objective"], "answer_relational_question")
        self.assertEqual(
            payload["response_trace"]["relational_question_profile"]["matched_pattern"],
            "how_do_he_feel",
        )

    @patch("src.api.init_ai")
    def test_direct_challenge_stream_replaces_generic_output_before_tokens_reach_ui(self, mock_init_ai):
        """Streaming direct challenges should emit the stabilized Jarvis reply, not the generic draft."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "I can't be a real person, but I'm just a tool."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={"message": "what is wrong with you?", "response_mode": "think"},
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        raw_stream = response.get_data(as_text=True)
        payloads = [
            json.loads(line[6:])
            for line in raw_stream.splitlines()
            if line.startswith("data: ")
        ]
        final_payload = next(payload for payload in payloads if payload["event"] == "final")
        self.assertEqual(
            final_payload["response"],
            "No. If I missed something, point it out and I'll correct it.",
        )
        self.assertNotIn("i can't be a real person", raw_stream.lower())
        self.assertNotIn("i'm just a tool", raw_stream.lower())
        self.assertNotIn("how can i assist you today", raw_stream.lower())
        self.assertNotEqual((final_payload["model_route"] or {}).get("id"), "story_room")

    @patch("src.api.init_ai")
    def test_training_prompt_returns_specialist_lenses_in_trace(self, mock_init_ai):
        """Training-heavy turns should expose the specialist registry in the runtime trace."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Start with a small LoRA dataset, then evaluate before another pass."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me fine-tune a small Qwen model with LoRA, build the dataset, and evaluate it.",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_trace"]["mode"], "builder")
        self.assertEqual(payload["response_trace"]["specialist_domain"], "training")
        self.assertEqual(payload["response_trace"]["specialist_focus"], "finetuning")
        lens_labels = [lens["label"] for lens in payload["response_trace"]["specialist_lenses"]]
        self.assertIn("Fine-Tune", lens_labels)
        self.assertIn("Dataset", lens_labels)
        self.assertIn("Evaluation", lens_labels)
        self.assertIsNone(payload["response_trace"]["writing_focus"])
        fake_model.generate_chat.assert_called_once()

    def test_workspace_profile_route_exposes_evolving_project_profile(self):
        """Jarvis should expose the transplanted evolving_ai project profile detector."""
        project_root = self.workspace_root / "AAIS-main"
        (project_root / "src").mkdir(exist_ok=True)
        (project_root / "tests").mkdir(exist_ok=True)
        (project_root / "pyproject.toml").write_text(
            "[project]\nname = 'aais-main'\ndependencies = ['flask', 'ruff']\n",
            encoding="utf-8",
        )
        (project_root / "requirements.txt").write_text("pytest\nflask\n", encoding="utf-8")
        (project_root / "package.json").write_text(
            json.dumps(
                {
                    "dependencies": {"react": "^19.0.0", "vite": "^7.0.0"},
                    "scripts": {"dev": "vite", "build": "vite build", "test": "vitest"},
                }
            ),
            encoding="utf-8",
        )
        (project_root / "src" / "api.py").write_text("from flask import Flask\napp = Flask(__name__)\n", encoding="utf-8")
        (project_root / "tests" / "test_api.py").write_text("def test_health():\n    assert True\n", encoding="utf-8")

        response = self.client.get("/api/jarvis/workspace/profile")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["scope_prefix"], "AAIS-main")
        self.assertIn("python", payload["languages"])
        self.assertIn("javascript", payload["languages"])
        self.assertIn("flask", payload["frameworks"])
        self.assertIn("react", payload["frameworks"])
        self.assertIn("pytest -q", payload["test_commands"])
        self.assertIn("python src/api.py", payload["run_commands"])

    def test_workspace_symbols_and_repo_map_routes_expose_evolving_workbench(self):
        """The evolving workbench routes should expose symbols and a focused repo map."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        tests_dir = project_root / "tests"
        src_dir.mkdir(exist_ok=True)
        tests_dir.mkdir(exist_ok=True)
        (src_dir / "feature.py").write_text(
            "class RouteStabilizer:\n"
            "    def guard(self):\n"
            "        return 'ready'\n\n"
            "def stabilize_openrouter_route():\n"
            "    return RouteStabilizer().guard()\n",
            encoding="utf-8",
        )
        (tests_dir / "test_feature.py").write_text(
            "from src.feature import stabilize_openrouter_route\n\n"
            "def test_stabilize_openrouter_route():\n"
            "    assert stabilize_openrouter_route() == 'ready'\n",
            encoding="utf-8",
        )

        symbols_response = self.client.post(
            "/api/jarvis/workspace/symbols",
            json={"query": "stabilize_openrouter_route"},
        )
        self.assertEqual(symbols_response.status_code, 200)
        symbols_payload = symbols_response.get_json()
        self.assertGreaterEqual(symbols_payload["symbol_count"], 1)
        self.assertEqual(symbols_payload["symbols"][0]["qualname"], "stabilize_openrouter_route")

        symbol_response = self.client.get(
            "/api/jarvis/workspace/symbol",
            query_string={"symbol": "stabilize_openrouter_route"},
        )
        self.assertEqual(symbol_response.status_code, 200)
        self.assertIn(
            "def stabilize_openrouter_route",
            symbol_response.get_json()["symbol"]["content"],
        )

        repo_map_response = self.client.post(
            "/api/jarvis/workspace/repo-map",
            json={"focus_path": "AAIS-main/src/feature.py"},
        )
        self.assertEqual(repo_map_response.status_code, 200)
        repo_map_payload = repo_map_response.get_json()
        self.assertIn("AAIS-main/src/feature.py", repo_map_payload["focus_paths"])
        self.assertIn("AAIS-main/tests/test_feature.py", repo_map_payload["likely_test_files"])
        self.assertTrue(any(node["path"] == "AAIS-main/src/feature.py" for node in repo_map_payload["nodes"]))

    @patch("src.api.init_ai")
    def test_coding_turn_workspace_context_includes_evolving_profile_and_symbols(self, mock_init_ai):
        """Coding turns should now carry evolving workbench context into the live Jarvis payload."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        tests_dir = project_root / "tests"
        src_dir.mkdir(exist_ok=True)
        tests_dir.mkdir(exist_ok=True)
        (project_root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
        (src_dir / "feature.py").write_text(
            "def stabilize_openrouter_route():\n"
            "    return 'ready'\n",
            encoding="utf-8",
        )
        (tests_dir / "test_feature.py").write_text(
            "from src.feature import stabilize_openrouter_route\n",
            encoding="utf-8",
        )
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The route is grounded in the workspace context."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Debug stabilize_openrouter_route in feature.py.", "response_mode": "think"},
        )

        self.assertEqual(response.status_code, 200)
        workspace_context = response.get_json()["workspace_context"]
        self.assertIn("python", workspace_context["project_profile"]["languages"])
        self.assertTrue(
            any(
                item["qualname"] == "stabilize_openrouter_route"
                for item in workspace_context["symbol_hits"]
            )
        )
        self.assertIn("AAIS-main/src/feature.py", workspace_context["repo_map"]["focus_paths"])

    def test_run_ledger_routes_create_and_fetch_run(self):
        """The RunLedger routes should create, list, and fetch durable runs."""
        create_response = self.client.post(
            "/api/jarvis/runs",
            json={
                "session_id": "session-ledger",
                "title": "Stabilize OpenRouter-first routing",
                "kind": "operator",
                "cisiv_stage": "verification",
                "meta": {"focus": "fallback"},
            },
        )

        self.assertEqual(create_response.status_code, 201)
        run = create_response.get_json()["run"]
        self.assertEqual(run["title"], "Stabilize OpenRouter-first routing")
        self.assertEqual(run["status"], "open")
        self.assertEqual(run["cisiv_stage"], "verification")

        list_response = self.client.get("/api/jarvis/runs?session_id=session-ledger")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.get_json()["runs"][0]["id"], run["id"])
        self.assertEqual(list_response.get_json()["runs"][0]["cisiv_stage"], "verification")

        get_response = self.client.get(f"/api/jarvis/runs/{run['id']}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()["run"]["meta"]["focus"], "fallback")
        self.assertEqual(get_response.get_json()["run"]["cisiv_stage"], "verification")

    def test_change_scope_test_oracle_and_patchforge_routes_follow_workspace_impact(self):
        """The blueprint coding organs should expose impact, verification, and patch planning."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        tests_dir = project_root / "tests"
        src_dir.mkdir(exist_ok=True)
        tests_dir.mkdir(exist_ok=True)
        (src_dir / "api.py").write_text(
            "from src.service import route_request\n\n"
            "def handle_route():\n"
            "    return route_request()\n",
            encoding="utf-8",
        )
        (src_dir / "service.py").write_text(
            "def route_request():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )
        (tests_dir / "test_api.py").write_text(
            "from src.api import handle_route\n\n"
            "def test_handle_route():\n"
            "    assert handle_route() == 'ok'\n",
            encoding="utf-8",
        )

        scope_response = self.client.post(
            "/api/jarvis/change-scope",
            json={"file_path": "AAIS-main/src/api.py", "goal": "stabilize route handling"},
        )
        self.assertEqual(scope_response.status_code, 200)
        impact = scope_response.get_json()
        self.assertIn("AAIS-main/src/api.py", impact["affected_files"])
        self.assertIn("AAIS-main/tests/test_api.py", impact["recommended_tests"])

        test_plan_response = self.client.post(
            "/api/jarvis/tests/plan",
            json={"change_impact": impact, "goal": "stabilize route handling"},
        )
        self.assertEqual(test_plan_response.status_code, 200)
        test_plan = test_plan_response.get_json()
        self.assertIn("AAIS-main/tests/test_api.py", test_plan["recommended_tests"])

        patch_response = self.client.post(
            "/api/jarvis/patch/plan",
            json={
                "goal": "stabilize route handling",
                "change_impact": impact,
                "test_plan": test_plan,
            },
        )
        self.assertEqual(patch_response.status_code, 200)
        patch_payload = patch_response.get_json()
        patch_plan = patch_payload["patch_plan"]
        patch_review = patch_payload["patch_review"]
        self.assertEqual(patch_plan["status"], "proposal_only")
        self.assertTrue(patch_plan["preview_only"])
        self.assertIn("AAIS-main/src/api.py", patch_plan["target_files"])
        self.assertIn("--- a/AAIS-main/src/api.py", patch_plan["unified_diff"])
        self.assertIn("AAIS-main/tests/test_api.py", patch_plan["verification_checklist"])
        self.assertGreaterEqual(patch_plan["hunk_count"], 1)
        self.assertFalse(patch_plan["review_complete"])
        self.assertGreaterEqual(len(patch_plan["hunks"]), 1)
        self.assertEqual(patch_plan["hunks"][0]["scope"], "proposal_preview")
        self.assertEqual(patch_plan["hunks"][0]["file_path"], "AAIS-main/src/api.py")
        self.assertGreaterEqual(patch_plan["hunks"][0]["line_count"], 1)
        self.assertIn("proposed change:", patch_plan["hunks"][0]["diff"])
        self.assertEqual(patch_payload["summary"]["hunk_count"], patch_plan["hunk_count"])
        self.assertFalse(patch_payload["summary"]["review_complete"])
        self.assertEqual(patch_review["id"], patch_plan["plan_id"])
        self.assertEqual(patch_review["status"], "proposed")
        self.assertEqual(patch_review["current_decision"]["state"], "proposed")
        self.assertFalse(patch_review["apply_gate"]["ready"])
        self.assertIn("accepted", patch_review["apply_gate"]["blockers"][0].lower())

        review_list_response = self.client.get("/api/jarvis/patch/reviews")
        self.assertEqual(review_list_response.status_code, 200)
        self.assertEqual(review_list_response.get_json()["reviews"][0]["id"], patch_plan["plan_id"])

        review_get_response = self.client.get(f"/api/jarvis/patch/reviews/{patch_plan['plan_id']}")
        self.assertEqual(review_get_response.status_code, 200)
        review_payload = review_get_response.get_json()["review"]
        self.assertEqual(review_payload["patch_plan"]["plan_id"], patch_plan["plan_id"])
        self.assertEqual(review_payload["review_targets"]["hunks"][0]["file_path"], "AAIS-main/src/api.py")
        self.assertGreaterEqual(review_payload["review_targets"]["line_action_count"], 1)
        self.assertFalse(review_payload["apply_gate"]["ready"])

        preview_response = self.client.post(
            "/api/jarvis/patch/preview",
            json={"patch_plan": patch_plan},
        )
        self.assertEqual(preview_response.status_code, 200)
        preview = preview_response.get_json()["preview"]
        self.assertIn(preview["status"], {"aligned", "mixed"})
        self.assertEqual(preview["counts"]["missing"], 0)
        self.assertGreaterEqual(preview["counts"]["aligned"], 1)
        self.assertTrue(any(file["matched_anchor"] or file["matched_before_snippet"] for file in preview["files"]))

        hunk_decision_response = self.client.post(
            f"/api/jarvis/patch/reviews/{patch_plan['plan_id']}/decision",
            json={"decision": "needs_revision", "note": "Narrow this hunk first.", "target_kind": "hunk", "target_index": 0},
        )
        self.assertEqual(hunk_decision_response.status_code, 200)
        hunk_review = hunk_decision_response.get_json()["review"]
        self.assertEqual(hunk_review["status"], "proposed")
        self.assertEqual(hunk_review["target_decisions"]["hunk:0"]["state"], "needs_revision")
        self.assertEqual(hunk_review["decision_counts"]["needs_revision"], 1)
        self.assertFalse(hunk_review["apply_gate"]["ready"])

        review_decision_response = self.client.post(
            f"/api/jarvis/patch/reviews/{patch_plan['plan_id']}/decision",
            json={"decision": "needs_revision", "note": "Tighten the patch scope first."},
        )
        self.assertEqual(review_decision_response.status_code, 200)
        review_record = review_decision_response.get_json()["review"]
        self.assertEqual(review_record["status"], "needs_revision")
        self.assertEqual(review_record["current_decision"]["state"], "needs_revision")
        self.assertEqual(review_record["history"][-1]["note"], "Tighten the patch scope first.")
        self.assertEqual(review_record["decision_counts"]["needs_revision"], 2)
        self.assertFalse(review_record["apply_gate"]["ready"])

        (src_dir / "api.py").write_text(
            "def handle_route():\n"
            "    return 'rewired'\n",
            encoding="utf-8",
        )
        drift_preview_response = self.client.post(
            "/api/jarvis/patch/preview",
            json={"review_id": patch_plan["plan_id"]},
        )
        self.assertEqual(drift_preview_response.status_code, 200)
        drift_preview = drift_preview_response.get_json()["preview"]
        self.assertIn(drift_preview["status"], {"mixed", "drifted"})
        self.assertGreaterEqual(drift_preview["counts"]["drifted"], 1)

    def test_patch_apply_requires_review_acceptance_before_action_can_queue(self):
        """Patch proposal alone is not apply authority; accepted review is the gate."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id=None,
            patch_plan={
                "plan_id": "patch_review_gate",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The accepted review should own this replacement.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        self.assertFalse(review["apply_gate"]["ready"])

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/actions/execute",
            json={
                "action_id": "apply_patch_review",
                "review_id": review["id"],
                "approved": True,
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("accepted", payload["error"].lower())
        self.assertEqual(target_file.read_text(encoding="utf-8").splitlines()[-1], "    return 'old'")

        session_response = self.client.get(f"/api/chat/sessions/{session_id}")
        self.assertEqual(session_response.status_code, 200)
        session_payload = session_response.get_json()
        self.assertIsNone(session_payload["pending_action"])
        self.assertEqual(session_payload["action_lifecycle"]["stage"], "blocked")

    def test_review_accepted_patch_can_apply_through_existing_approval_flow(self):
        """Accepted review records can queue once, then apply through the normal approval gate."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id=None,
            patch_plan={
                "plan_id": "patch_review_apply",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "test_suggestions": ["AAIS-main/tests/test_service.py"],
                "verification_checklist": ["AAIS-main/tests/test_service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The review accepted this replacement.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        accepted_review = api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Approved for apply.",
        )
        self.assertTrue(accepted_review["apply_gate"]["ready"])

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/actions/execute",
            json={
                "action_id": "apply_patch_review",
                "review_id": review["id"],
                "approved": False,
                "response_mode": "operator",
            },
        )
        self.assertEqual(proposal_response.status_code, 400)

        session_snapshot = self.client.get(f"/api/chat/sessions/{session_id}")
        pending_action = session_snapshot.get_json()["pending_action"]
        self.assertEqual(pending_action["id"], "apply_patch_review")
        self.assertEqual(pending_action["review_id"], review["id"])

        approval_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "operator"},
        )
        self.assertEqual(approval_response.status_code, 200)
        payload = approval_response.get_json()

        self.assertEqual(payload["tool_result"]["type"], "action_result")
        self.assertEqual(payload["tool_result"]["action"]["id"], "apply_patch_review")
        self.assertEqual(payload["tool_result"]["patch_apply"]["review_id"], review["id"])
        self.assertEqual(payload["tool_result"]["status"], "awaiting_verification")
        self.assertEqual(payload["tool_result"]["patch_apply"]["status"], "awaiting_verification")
        self.assertEqual(
            payload["tool_result"]["law_enforcement"]["contract_version"],
            "aais.project_infi.ul.v1",
        )
        self.assertEqual(
            payload["tool_result"]["patch_apply"]["law_event_log"]["event_type"],
            "repo_action_recorded",
        )
        self.assertIn("AAIS-main/src/service.py", payload["tool_result"]["patch_apply"]["changed_files"])
        self.assertIn("    return 'new'\n", target_file.read_text(encoding="utf-8"))
        self.assertEqual(payload["action_lifecycle"]["stage"], "executed")
        self.assertIsNone(payload["pending_action"])

    def test_patch_review_apply_route_returns_run_and_rollback_notes(self):
        """Workbench patch apply should require an accepted review and return a durable run with rollback notes."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id="workbench-session",
            patch_plan={
                "plan_id": "patch_review_apply_direct",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "test_suggestions": ["AAIS-main/tests/test_service.py"],
                "verification_checklist": ["AAIS-main/tests/test_service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The review accepted this replacement.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Approved for workbench apply.",
        )

        apply_response = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={"session_id": "workbench-session"},
        )

        self.assertEqual(apply_response.status_code, 200)
        payload = apply_response.get_json()
        self.assertEqual(payload["result"]["status"], "awaiting_verification")
        self.assertEqual(payload["run"]["status"], "awaiting_verification")
        self.assertEqual(payload["run"]["kind"], "patch_apply")
        self.assertTrue(payload["preview"]["ready_for_review"])
        self.assertIn("AAIS-main/src/service.py", payload["result"]["changed_files"])
        self.assertTrue(payload["result"]["rollback_notes"])
        self.assertIn("git diff", payload["result"]["rollback_notes"][1].lower())
        self.assertIn("AAIS-main/tests/test_service.py", payload["verification"]["recommended_tests"])
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.project_infi.ul.v1")
        self.assertEqual(payload["law_event_log"]["event_type"], "repo_action_recorded")
        self.assertIn("    return 'new'\n", target_file.read_text(encoding="utf-8"))

        run_detail = self.client.get(f"/api/jarvis/runs/{payload['run']['id']}")
        self.assertEqual(run_detail.status_code, 200)
        run_payload = run_detail.get_json()["run"]
        self.assertGreaterEqual(len(run_payload["steps"]), 4)
        self.assertTrue(any(step["kind"] == "project_infi_logbook" for step in run_payload["steps"]))

    def test_patch_review_apply_route_blocks_duplicate_reruns_without_force(self):
        """A governed patch apply run should block accidental duplicate applies for the same review."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id="workbench-session",
            patch_plan={
                "plan_id": "patch_review_duplicate_guard",
                "goal": "Swap the return value once.",
                "target_files": ["AAIS-main/src/service.py"],
                "test_suggestions": ["AAIS-main/tests/test_service.py"],
                "verification_checklist": ["AAIS-main/tests/test_service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The review accepted this replacement.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Approved for one guarded apply.",
        )

        first_apply = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={"session_id": "workbench-session"},
        )
        self.assertEqual(first_apply.status_code, 200)

        second_apply = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={"session_id": "workbench-session"},
        )
        self.assertEqual(second_apply.status_code, 409)
        duplicate_payload = second_apply.get_json()
        self.assertIn("governed apply run", duplicate_payload["error"].lower())
        self.assertEqual(duplicate_payload["run"]["status"], "awaiting_verification")
        self.assertEqual((duplicate_payload["run"]["meta"] or {}).get("review_id"), review["id"])

    def test_patch_review_apply_route_preserves_rejected_no_admission_when_verification_fails(self):
        """Failed verification evidence should close the governed repo cycle as rejected_no_admission."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id="workbench-session",
            patch_plan={
                "plan_id": "patch_review_rejected_no_admission",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "test_suggestions": ["AAIS-main/tests/test_service.py"],
                "verification_checklist": ["AAIS-main/tests/test_service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The review was accepted but verification later failed.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Approved pending verification.",
        )

        apply_response = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={
                "session_id": "workbench-session",
                "verification_evidence": {
                    "status": "failed",
                    "passed": False,
                    "summary": "Verification rejected the repo change after apply.",
                    "checks": ["AAIS-main/tests/test_service.py"],
                },
            },
        )

        self.assertEqual(apply_response.status_code, 200)
        payload = apply_response.get_json()
        self.assertEqual(payload["result"]["status"], "rejected_no_admission")
        self.assertEqual(payload["run"]["status"], "rejected_no_admission")
        self.assertEqual(payload["law_enforcement"]["governed_cycle"]["status"], "rejected_no_admission")
        self.assertFalse(payload["law_enforcement"]["governed_cycle"]["truthful"])
        self.assertEqual(payload["law_event_log"]["event_type"], "repo_action_recorded")
        self.assertEqual(payload["judgment_log"]["status"], "blocked")
        self.assertIn("    return 'new'\n", target_file.read_text(encoding="utf-8"))

    def test_patch_review_apply_route_fails_closed_without_verification_plan(self):
        """Project Infi law should block repo changes that do not carry verification context."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id="workbench-session",
            patch_plan={
                "plan_id": "patch_review_missing_verification",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "Missing verification should block this.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Approved but still missing verification context.",
        )

        apply_response = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={"session_id": "workbench-session"},
        )

        self.assertEqual(apply_response.status_code, 400)
        self.assertIn("verification_plan", apply_response.get_json()["error"])
        self.assertIn("    return 'old'\n", target_file.read_text(encoding="utf-8"))

    def test_patch_review_apply_route_blocks_raw_external_adoption(self):
        """Patch apply should fail closed if an external suggestion is marked for adoption without admitted form."""
        project_root = self.workspace_root / "AAIS-main"
        src_dir = project_root / "src"
        src_dir.mkdir(exist_ok=True)
        target_file = src_dir / "service.py"
        target_file.write_text(
            "def route_request():\n"
            "    return 'old'\n",
            encoding="utf-8",
        )

        review = api.jarvis_operator.create_patch_review(
            session_id="workbench-session",
            patch_plan={
                "plan_id": "patch_review_external_adoption_block",
                "goal": "Swap the return value.",
                "target_files": ["AAIS-main/src/service.py"],
                "test_suggestions": ["AAIS-main/tests/test_service.py"],
                "verification_checklist": ["AAIS-main/tests/test_service.py"],
                "external_suggestion": {
                    "source": "outside_patch_note",
                    "summary": "Adopt this patch pattern directly.",
                },
                "external_suggestion_usage": "adoption",
                "edits": [
                    {
                        "file_path": "AAIS-main/src/service.py",
                        "summary": "Return the rewired value.",
                        "rationale": "The outside suggestion requested this exact replacement.",
                        "before_snippet": "    return 'old'\n",
                        "after_snippet": "    return 'new'\n",
                    }
                ],
                "hunks": [],
                "status": "proposal_only",
                "preview_only": True,
            },
        )
        api.jarvis_operator.record_patch_review_decision(
            review["id"],
            decision="accepted",
            note="Accepted, but still missing admission form.",
        )

        apply_response = self.client.post(
            f"/api/jarvis/patch/reviews/{review['id']}/apply",
            json={"session_id": "workbench-session"},
        )

        self.assertEqual(apply_response.status_code, 400)
        self.assertIn("external_suggestion_law_filter", apply_response.get_json()["error"])
        self.assertIn("admitted_external_form", apply_response.get_json()["error"])
        self.assertIn("    return 'old'\n", target_file.read_text(encoding="utf-8"))

    def test_actions_execute_endpoint_blocks_raw_external_adoption(self):
        """The approved local-action route should forward external suggestion adoption into Project Infi law."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.jarvis_operator.action_runner,
            "execute_action",
            return_value={
                "action": dict(api.jarvis_operator.action_runner.get_action("run_pytest") or {"id": "run_pytest", "label": "Run Pytest"}),
                "status": "completed",
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "summary": "364 passed, 6 subtests passed.",
                "ran_at": "2026-04-14T00:00:00+00:00",
            },
        ) as mocked_execute:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/actions/execute",
                json={
                    "action_id": "run_pytest",
                    "approved": True,
                    "response_mode": "operator",
                    "external_suggestion": {
                        "source": "outside_note",
                        "summary": "Adopt this command suggestion directly.",
                    },
                    "external_suggestion_usage": "adoption",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("external_suggestion_law_filter", response.get_json()["error"])
        self.assertIn("admitted_external_form", response.get_json()["error"])
        mocked_execute.assert_not_called()

    def test_memory_smith_review_route_expires_stale_blockers_after_green_tests(self):
        """MemorySmith should separate durable notes from stale failure noise."""
        response = self.client.post(
            "/api/jarvis/memory-smith/review",
            json={
                "manual_notes": [
                    "Project default: keep Jarvis local-first unless a sister route is needed.",
                    "pytest is failing right now",
                ],
                "test_outcomes": [{"status": "passed"}],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["project_summary"]["latest_test_status"], "passed")
        self.assertEqual(len(payload["durable"]), 1)
        self.assertEqual(len(payload["expired"]), 1)
        self.assertEqual(len(payload["promoted"]), 1)
        self.assertEqual(payload["promoted"][0]["governance"]["action"], "write")
        self.assertEqual(len(payload["expired_actions"]), 1)
        self.assertEqual(payload["expired_actions"][0]["governance"]["action"], "expiry_review")
        self.assertIn("stale blocker", payload["expired"][0]["message"].lower())

        board_response = self.client.get("/api/jarvis/memory/board")
        self.assertEqual(board_response.status_code, 200)
        board = board_response.get_json()["memory_board"]
        self.assertGreaterEqual(board["governance"]["event_count"], 2)
        self.assertGreaterEqual(board["governance"]["action_counts"].get("write", 0), 1)
        self.assertGreaterEqual(board["governance"]["action_counts"].get("expiry_review", 0), 1)

    def test_memory_smith_review_route_prefers_explicit_expiry_targets(self):
        """Explicit target ids should govern stale-blocker expiry instead of broad fallback matching."""
        blocker_response = self.client.post(
            "/api/jarvis/memory",
            json={"content": "Pytest is failing on the verification lane.", "category": "operator"},
        )
        sibling_response = self.client.post(
            "/api/jarvis/memory",
            json={"content": "Another blocker is still open on the docs lane.", "category": "operator"},
        )
        blocker_id = blocker_response.get_json()["id"]
        sibling_id = sibling_response.get_json()["id"]

        review_response = self.client.post(
            "/api/jarvis/memory-smith/review",
            json={
                "test_outcomes": [{"status": "passed"}],
                "expire_memory_ids": [blocker_id],
            },
        )

        self.assertEqual(review_response.status_code, 200)
        payload = review_response.get_json()
        self.assertEqual(payload["expired"][0]["target_ids"], [blocker_id])
        self.assertEqual(payload["expired_actions"][0]["targeting_mode"], "explicit_id")
        self.assertEqual(payload["expired_actions"][0]["archived_ids"], [blocker_id])
        self.assertEqual(payload["expired_actions"][0]["skipped_target_ids"], [])

        blocker_detail = self.client.get(f"/api/jarvis/memory/{blocker_id}").get_json()["memory"]
        sibling_detail = self.client.get(f"/api/jarvis/memory/{sibling_id}").get_json()["memory"]
        self.assertFalse(blocker_detail["active"])
        self.assertTrue(sibling_detail["active"])

    def test_memory_board_install_and_swap_endpoints_use_protected_governed_path(self):
        """Protected board routes should expose install and swap operations without bypassing governance."""
        original_board = api.jarvis_operator.memory_store.memory_board
        api.jarvis_operator.memory_store.memory_board = MemoryController(default_memory_slots())
        try:
            install_response = self.client.post(
                "/api/jarvis/memory/board/install",
                json={
                    "slot_id": "slot_02",
                    "module": {
                        "module_id": "operator_memory_v1",
                        "module_version": "1.0.0",
                        "module_class": "operational",
                        "supported_slot": "slot_02",
                        "capacity": 128,
                        "trust_class": "verified",
                        "retrieval_priority": 60,
                        "retention_policy": "persistent",
                        "eviction_policy": "age_and_rank",
                    },
                },
            )

            self.assertEqual(install_response.status_code, 200)
            install_payload = install_response.get_json()["result"]
            self.assertEqual(install_payload["event"]["action"], "protected_install")
            self.assertEqual(install_payload["module"]["module_id"], "operator_memory_v1")

            swap_response = self.client.post(
                "/api/jarvis/memory/board/swap",
                json={
                    "slot_id": "slot_02",
                    "module": {
                        "module_id": "operator_memory_v2",
                        "module_version": "2.0.0",
                        "module_class": "operational",
                        "supported_slot": "slot_02",
                        "capacity": 256,
                        "trust_class": "verified",
                        "retrieval_priority": 80,
                        "retention_policy": "persistent",
                        "eviction_policy": "age_and_rank",
                    },
                    "migration_records": [
                        {
                            "record_id": "memory-1",
                            "slot_id": "slot_02",
                            "slot_role": "operational",
                            "trust_class": "verified",
                            "text": "Verified operator truth.",
                        }
                    ],
                },
            )

            self.assertEqual(swap_response.status_code, 200)
            swap_payload = swap_response.get_json()["result"]
            self.assertEqual(swap_payload["event"]["action"], "protected_swap")
            self.assertEqual(swap_payload["activated_module"]["module_id"], "operator_memory_v2")
            self.assertEqual(
                swap_payload["memory_board"]["governance"]["action_counts"].get("protected_install", 0),
                1,
            )
            self.assertEqual(
                swap_payload["memory_board"]["governance"]["action_counts"].get("protected_swap", 0),
                1,
            )
        finally:
            api.jarvis_operator.memory_store.memory_board = original_board

    def test_workbench_snapshot_aggregates_operator_surfaces(self):
        """The workbench snapshot should gather missions, memories, reviews, runs, governance, and workspace lane state."""
        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Stabilize workbench",
                "objective": "Unify the operator deck.",
                "next_step": "Verify the new execution cockpit.",
                "status": "active",
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        memory_response = self.client.post(
            "/api/jarvis/memory",
            json={"content": "Workbench is now the main operator page.", "category": "operator"},
        )
        self.assertEqual(memory_response.status_code, 201)

        run_response = self.client.post(
            "/api/jarvis/runs",
            json={"session_id": "workbench-session", "title": "Workbench pass", "kind": "operator"},
        )
        self.assertEqual(run_response.status_code, 201)

        snapshot_response = self.client.get("/api/jarvis/workbench")
        self.assertEqual(snapshot_response.status_code, 200)
        payload = snapshot_response.get_json()
        self.assertIn("mission_board", payload)
        self.assertIn("memory_bank", payload)
        self.assertIn("patch_reviews", payload)
        self.assertIn("runs", payload)
        self.assertIn("governance", payload)
        self.assertIn("workspace_lane", payload)
        self.assertIn("execution_cockpit", payload)
        self.assertIn("knowledge_authority", payload)
        self.assertIn("state_hygiene", payload)
        self.assertIn("governance", payload["memory_bank"])
        self.assertIn("recent_apply_runs", payload["execution_cockpit"])
        self.assertGreaterEqual(payload["memory_bank"]["summary"]["total"], 1)
        self.assertGreaterEqual(len(payload["mission_board"]["missions"]), 1)
        self.assertGreaterEqual(len(payload["runs"]), 1)
        self.assertEqual(payload["truth_scope"], "live")

    def test_workbench_snapshot_exposes_memory_governance_insights(self):
        """Workbench memory payload should expose merge suggestions, why gaps, conflicts, and archive review."""
        target = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Keep Jarvis operator memory focused on AAIS-main and the workbench.",
                "category": "operator",
                "why": "Operator truth belongs in the active AAIS workspace.",
                "priority": 88,
                "tags": ["operator", "workbench"],
            },
        ).get_json()
        source = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "AAIS-main workbench should stay the canonical operator workspace note.",
                "category": "operator",
                "priority": 70,
                "tags": ["operator", "workspace"],
            },
        ).get_json()
        self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "AAIS-main operator workspace truth lives here.",
                "category": "operator",
                "why": "A competing explanation of the same operator space.",
                "priority": 65,
                "tags": ["operator", "workspace"],
            },
        )
        archived = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Old operator note from prompt lab.",
                "category": "operator",
                "why": "Archive review seed.",
            },
        ).get_json()
        self.client.post(
            f"/api/jarvis/memory/{archived['id']}/archive",
            json={"reason": "Workbench archive review seed."},
        )

        snapshot_response = self.client.get("/api/jarvis/workbench")
        self.assertEqual(snapshot_response.status_code, 200)
        governance = snapshot_response.get_json()["memory_bank"]["governance"]
        self.assertGreaterEqual(governance["counts"]["merge_suggestions"], 1)
        self.assertGreaterEqual(governance["counts"]["why_gaps"], 1)
        self.assertGreaterEqual(governance["counts"]["conflicts"], 1)
        self.assertGreaterEqual(governance["counts"]["archive_review"], 1)
        self.assertIn(target["id"], {item["target_id"] for item in governance["merge_suggestions"]})
        self.assertIn(source["id"], {item["id"] for item in governance["why_gaps"]})

    def test_workbench_snapshot_exposes_authority_preferences_and_active_authorities(self):
        """Workbench knowledge authority should reflect the session-scoped authority controls."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        preference_response = self.client.post(
            f"/api/chat/sessions/{session_id}/authority/preferences",
            json={"preset": "strict_local"},
        )
        self.assertEqual(preference_response.status_code, 200)

        workbench = self.client.get("/api/jarvis/workbench", query_string={"session_id": session_id})
        self.assertEqual(workbench.status_code, 200)
        knowledge = workbench.get_json()["knowledge_authority"]
        self.assertEqual(knowledge["preferences"]["preset"], "strict_local")
        self.assertEqual(knowledge["preferences"]["primary_source"], "workspace")
        live_research_row = next(
            row for row in knowledge["active_authorities"] if row["source_type"] == "live_research"
        )
        workspace_row = next(
            row for row in knowledge["active_authorities"] if row["source_type"] == "workspace"
        )
        self.assertEqual(live_research_row["status"], "disabled")
        self.assertTrue(workspace_row["surface_priority"])
        self.assertEqual(knowledge["surface_priority"]["source_type"], "workspace")
        self.assertTrue(knowledge["surface_priority"]["non_authoritative"])
        self.assertFalse(knowledge["sovereignty_guard"]["authority_replacement_allowed"])

    def test_surface_priority_does_not_reorder_canonical_authority_precedence(self):
        """Surfacing one source should not replace the canonical backend precedence stack."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        baseline = self.client.get("/api/jarvis/workbench", query_string={"session_id": session_id})
        self.assertEqual(baseline.status_code, 200)
        baseline_knowledge = baseline.get_json()["knowledge_authority"]
        baseline_order = [
            (entry["source_type"], entry["truth_status"])
            for entry in baseline_knowledge["authority_order"]
        ]

        preference_response = self.client.post(
            f"/api/chat/sessions/{session_id}/authority/preferences",
            json={"action": "pin_primary", "source_type": "doctrine"},
        )
        self.assertEqual(preference_response.status_code, 200)

        refreshed = self.client.get("/api/jarvis/workbench", query_string={"session_id": session_id})
        self.assertEqual(refreshed.status_code, 200)
        knowledge = refreshed.get_json()["knowledge_authority"]
        refreshed_order = [
            (entry["source_type"], entry["truth_status"])
            for entry in knowledge["authority_order"]
        ]
        doctrine_row = next(
            row for row in knowledge["active_authorities"] if row["source_type"] == "doctrine"
        )

        self.assertEqual(refreshed_order, baseline_order)
        self.assertTrue(doctrine_row["surface_priority"])
        self.assertEqual(knowledge["surface_priority"]["source_type"], "doctrine")
        self.assertEqual(knowledge["summary"]["surface_priority"], "Canonical docs")

    def test_surface_priority_does_not_deroute_jarvis_sovereignty_contract(self):
        """Surface promotion should not replace the Jarvis turn contract as routing or voice authority."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        self.assertEqual(create_response.status_code, 201)
        created_payload = create_response.get_json()
        session_id = created_payload["session_id"]
        baseline_contract = dict(created_payload["sovereignty_contract"])

        preference_response = self.client.post(
            f"/api/chat/sessions/{session_id}/authority/preferences",
            json={"action": "pin_primary", "source_type": "live_research"},
        )
        self.assertEqual(preference_response.status_code, 200)
        payload = preference_response.get_json()
        contract = payload["sovereignty_contract"]

        self.assertEqual(payload["response_mode"], created_payload["response_mode"])
        self.assertEqual(payload["requested_response_mode"], created_payload["requested_response_mode"])
        self.assertEqual(contract["resolved_mode"], baseline_contract["resolved_mode"])
        self.assertEqual(contract["resolved_scope"], baseline_contract["resolved_scope"])
        self.assertEqual(contract["resolved_voice"], baseline_contract["resolved_voice"])
        self.assertEqual(contract["source_of_truth"], "turn_contract")
        self.assertTrue(contract["surface_priority_non_authoritative"])
        self.assertEqual(contract["surface_priority_scope"], "operator_visibility_only")
        self.assertEqual(contract["authority_surface_priority"], "live_research")
        self.assertIn("resolved_voice", contract["surface_priority_cannot_override"])

    def test_workbench_snapshot_exposes_knowledge_conflict_inbox_and_defer_state(self):
        """Knowledge conflict inbox should expose live memory conflicts and reflect deferred operator decisions."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "AAIS workbench remains the canonical operator console.",
                "category": "operator",
                "why": "Current operator truth.",
                "tags": ["operator", "workbench"],
            },
        )
        self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "AAIS workbench stays the operator console, but its rationale changed.",
                "category": "operator",
                "why": "Competing operator truth explanation.",
                "tags": ["operator", "workbench"],
            },
        )

        initial = self.client.get("/api/jarvis/workbench", query_string={"session_id": session_id})
        self.assertEqual(initial.status_code, 200)
        inbox = initial.get_json()["knowledge_authority"]["conflict_inbox"]
        self.assertTrue(inbox)
        conflict = next(item for item in inbox if item["kind"] == "memory_conflict")
        self.assertEqual(conflict["status"], "active")

        defer_response = self.client.post(
            f"/api/chat/sessions/{session_id}/knowledge/conflicts/{conflict['id']}/defer",
            json={"deferred": True},
        )
        self.assertEqual(defer_response.status_code, 200)

        refreshed = self.client.get("/api/jarvis/workbench", query_string={"session_id": session_id})
        self.assertEqual(refreshed.status_code, 200)
        refreshed_inbox = refreshed.get_json()["knowledge_authority"]["conflict_inbox"]
        refreshed_conflict = next(item for item in refreshed_inbox if item["id"] == conflict["id"])
        self.assertEqual(refreshed_conflict["status"], "deferred")

    def test_workbench_defaults_to_live_truth_scope_but_can_show_all_state_classes(self):
        """Workbench should hide non-live artifacts by default while still exposing them with truth_scope=all."""
        live_memory = self.client.post(
            "/api/jarvis/memory",
            json={"content": "Canonical operator truth.", "category": "operator"},
        ).get_json()
        demo_memory = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "WB canonical browser verification memory.",
                "category": "operator",
                "state_class": "demo",
                "truth_status": "derived",
            },
        ).get_json()

        live_run = self.client.post(
            "/api/jarvis/runs",
            json={"session_id": "live-session", "title": "Live run", "kind": "operator"},
        ).get_json()["run"]
        demo_run = self.client.post(
            "/api/jarvis/runs",
            json={
                "session_id": "demo-session",
                "title": "Browser verification run",
                "kind": "operator",
                "state_class": "smoke",
                "truth_status": "derived",
            },
        ).get_json()["run"]

        api.jarvis_operator.create_patch_review(
            session_id="live-session",
            patch_plan={
                "plan_id": "review_live_1",
                "goal": "Live patch review",
                "target_files": ["src/api.py"],
                "hunk_count": 1,
            },
        )
        api.jarvis_operator.create_patch_review(
            session_id="demo-session",
            patch_plan={
                "plan_id": "browser_verify_review_demo_1",
                "goal": "Browser verification patch review",
                "target_files": ["src/api.py"],
                "hunk_count": 1,
                "state_class": "demo",
                "truth_status": "derived",
            },
        )
        api.governance_layer.record_override(
            actor_id="owner_local",
            actor_role="owner",
            target="live_policy",
            reason="Live governance override.",
        )
        api.governance_layer.record_override(
            actor_id="owner_local",
            actor_role="owner",
            target="browser_verify_policy",
            reason="Browser verification governance artifact.",
            state_class="demo",
            truth_status="derived",
        )

        live_snapshot = self.client.get("/api/jarvis/workbench")
        self.assertEqual(live_snapshot.status_code, 200)
        live_payload = live_snapshot.get_json()
        self.assertEqual(live_payload["truth_scope"], "live")
        self.assertIn(live_memory["id"], {item["id"] for item in live_payload["memory_bank"]["memories"]})
        self.assertNotIn(demo_memory["id"], {item["id"] for item in live_payload["memory_bank"]["memories"]})
        self.assertIn(live_run["id"], {item["id"] for item in live_payload["runs"]})
        self.assertNotIn(demo_run["id"], {item["id"] for item in live_payload["runs"]})
        self.assertIn("review_live_1", {item["id"] for item in live_payload["patch_reviews"]})
        self.assertNotIn("browser_verify_review_demo_1", {item["id"] for item in live_payload["patch_reviews"]})
        self.assertIn("live_policy", {item["target"] for item in live_payload["governance"]["recent_events"]})
        self.assertNotIn(
            "browser_verify_policy",
            {item["target"] for item in live_payload["governance"]["recent_events"]},
        )

        all_snapshot = self.client.get("/api/jarvis/workbench?truth_scope=all")
        self.assertEqual(all_snapshot.status_code, 200)
        all_payload = all_snapshot.get_json()
        self.assertEqual(all_payload["truth_scope"], "all")
        self.assertIn(demo_memory["id"], {item["id"] for item in all_payload["memory_bank"]["memories"]})
        self.assertIn(demo_run["id"], {item["id"] for item in all_payload["runs"]})
        self.assertIn("browser_verify_review_demo_1", {item["id"] for item in all_payload["patch_reviews"]})
        self.assertIn(
            "browser_verify_policy",
            {item["target"] for item in all_payload["governance"]["recent_events"]},
        )

    def test_state_hygiene_compaction_archives_non_live_memories_expires_runs_and_reviews(self):
        """Compaction should archive non-live memories, expire non-live runs, and archive non-live reviews."""
        demo_memory = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Browser verification memory artifact.",
                "category": "operator",
                "state_class": "demo",
                "truth_status": "derived",
            },
        ).get_json()
        smoke_run = self.client.post(
            "/api/jarvis/runs",
            json={
                "session_id": "smoke-session",
                "title": "Browser verification run",
                "kind": "operator",
                "state_class": "smoke",
                "truth_status": "derived",
            },
        ).get_json()["run"]
        api.jarvis_operator.create_patch_review(
            session_id="smoke-session",
            patch_plan={
                "plan_id": "browser_verify_review_demo_compact",
                "goal": "Browser verification patch review",
                "target_files": ["src/api.py"],
                "hunk_count": 1,
                "state_class": "demo",
                "truth_status": "derived",
            },
        )

        compact_response = self.client.post("/api/jarvis/state-hygiene/compact")
        self.assertEqual(compact_response.status_code, 200)
        compact_payload = compact_response.get_json()["state_hygiene"]
        self.assertEqual(compact_payload["memory"]["archived_memories"], 1)
        self.assertEqual(compact_payload["runs"]["expired_runs"], 1)
        self.assertEqual(compact_payload["reviews"]["archived_reviews"], 1)

        memory_detail = self.client.get(f"/api/jarvis/memory/{demo_memory['id']}").get_json()["memory"]
        self.assertFalse(memory_detail["active"])
        self.assertEqual(memory_detail["retention_status"], "archived")

        run_detail = self.client.get(f"/api/jarvis/runs/{smoke_run['id']}").get_json()["run"]
        self.assertEqual(run_detail["status"], "expired")
        self.assertEqual(run_detail["retention_status"], "expired")

        review_detail = self.client.get(
            "/api/jarvis/patch/reviews/browser_verify_review_demo_compact"
        ).get_json()["review"]
        self.assertEqual(review_detail["retention_status"], "archived")

    def test_knowledge_authority_route_unifies_memory_docs_research_workspace_and_doctrine(self):
        """AAIS should expose one governed knowledge snapshot instead of separate knowledge islands."""
        override_memory = self.client.post(
            "/api/jarvis/memory/override",
            json={
                "content": "Jarvis Workbench is the operator-facing execution surface.",
                "category": "operator",
                "why": "This is canonical operator truth.",
            },
        ).get_json()
        document_module = api._load_module("src.document_rag")
        document_module.document_store.documents["doc_aais_handbook"] = {
            "chunks": ["AAIS doctrine keeps operator truth separate from demo artifacts."],
            "embeddings": [],
            "metadata": {"source": "AAIS handbook note", "type": "text"},
        }

        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["live_research"] = {
            "query": "latest operator patterns",
            "summary": "Loaded 1 live source.",
            "sources": [
                {
                    "title": "Operator Patterns",
                    "url": "https://example.com/operator-patterns",
                    "snippet": "Fresh operator guidance.",
                }
            ],
        }

        response = self.client.get(f"/api/jarvis/knowledge?session_id={session_id}&query=operator")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["knowledge_authority"]
        self.assertIn("authority_order", payload)
        self.assertIn("memory", payload)
        self.assertIn("documents", payload)
        self.assertIn("live_research", payload)
        self.assertIn("workspace", payload)
        self.assertIn("doctrine", payload)
        self.assertGreaterEqual(payload["summary"]["memory_count"], 1)
        self.assertGreaterEqual(payload["summary"]["document_count"], 1)
        self.assertGreaterEqual(payload["summary"]["doctrine_count"], 1)
        self.assertEqual(payload["memory"][0]["id"], override_memory["id"])
        self.assertEqual(payload["live_research"]["sources"][0]["title"], "Operator Patterns")
        precedence = {item["source_type"]: item["precedence_rank"] for item in payload["authority_order"]}
        self.assertGreater(precedence["memory_override"], precedence["doctrine"])

    def test_provider_mind_route_prefers_workbench_path_for_code_state_requests(self):
        """ProviderMind should keep code-state work out of creative side paths."""
        response = self.client.post(
            "/api/jarvis/provider-mind/choose",
            json={
                "message": "lifecycle status executed executed_at now pending_action in src/api.py and tests/test_api.py",
                "response_mode": "debug",
                "workspace_context": {
                    "results": [
                        {"relative_path": "AAIS-main/src/api.py"},
                        {"relative_path": "AAIS-main/tests/test_api.py"},
                        {"relative_path": "AAIS-main/src/conversation_memory.py"},
                    ]
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        decision = response.get_json()["decision"]
        self.assertEqual(decision["engine_path"], "workbench_debug")
        self.assertNotIn("v9", decision["engine_path"])
        self.assertNotIn("v10", decision["engine_path"])
        self.assertNotIn("mystic", decision["engine_path"])

    def test_provider_mind_keeps_non_debug_code_turns_out_of_debug_lane(self):
        """Code-state turns should stay in the coding lane unless the resolved turn mode is actually debug."""
        response = self.client.post(
            "/api/jarvis/provider-mind/choose",
            json={
                "message": "lifecycle status executed executed_at now pending_action in src/api.py and tests/test_api.py",
                "response_mode": "think",
                "workspace_context": {
                    "results": [
                        {"relative_path": "AAIS-main/src/api.py"},
                        {"relative_path": "AAIS-main/tests/test_api.py"},
                        {"relative_path": "AAIS-main/src/conversation_memory.py"},
                    ]
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        decision = response.get_json()["decision"]
        self.assertEqual(decision["engine_path"], "workbench_coding")

    @patch("src.api.jarvis_operator.execute_action")
    def test_action_lifecycle_writes_run_ledger_and_runtime_payload(self, mock_execute_action):
        """Canonical action lifecycle writes should create a durable run trail."""
        mock_execute_action.return_value = {
            "response": "Run Pytest finished.\n1 passed\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "run_pytest",
                    "label": "Run Pytest",
                    "description": "Run the backend test suite.",
                    "command_preview": "python -m pytest -q",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "1 passed",
                "stderr": "",
                "summary": "1 passed",
                "ran_at": "2026-04-07T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Run tests for this repo before we keep going.", "response_mode": "operator"},
        )
        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "operator"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["run_history"])
        latest_run = payload["run_history"][0]
        step_statuses = [step["status"] for step in latest_run["steps"]]
        self.assertIn("proposed", step_statuses)
        self.assertIn("approved", step_statuses)
        self.assertIn("executed", step_statuses)
        self.assertEqual(latest_run["current_action"]["stage"], "executed")
        self.assertEqual(latest_run["current_action"]["action_id"], "run_pytest")
        self.assertEqual(latest_run["current_action"]["cisiv_stage"], "verification")
        self.assertTrue(all(step.get("cisiv_stage") for step in latest_run["steps"]))
        self.assertEqual(payload["memory_smith"]["project_summary"]["latest_test_status"], "passed")

    @patch("src.api.jarvis_operator.execute_action")
    def test_action_lifecycle_green_pytest_archives_targeted_stale_blockers(self, mock_execute_action):
        """Successful pytest execution should archive governed stale blockers through explicit board targets."""
        blocker = api.jarvis_operator.memory_enforcer.add_memory(
            "The pytest lane is red and failing in CI.",
            category="operator",
            runtime_context="operator_runtime",
        )
        design_note = api.jarvis_operator.memory_enforcer.add_memory(
            "Red interface accents are part of the design system.",
            category="operator",
            runtime_context="operator_runtime",
        )
        mock_execute_action.return_value = {
            "response": "Run Pytest finished.\n1 passed\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "run_pytest",
                    "label": "Run Pytest",
                    "description": "Run the backend test suite.",
                    "command_preview": "python -m pytest -q",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "1 passed",
                "stderr": "",
                "summary": "1 passed",
                "ran_at": "2026-04-07T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Run tests for this repo before we keep going.", "response_mode": "operator"},
        )
        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "operator"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["memory_smith"]["project_summary"]["latest_test_status"], "passed")
        self.assertFalse(api.jarvis_operator.memory_enforcer.get_memory(blocker["id"], runtime_context="operator_runtime")["active"])
        self.assertTrue(
            api.jarvis_operator.memory_enforcer.get_memory(design_note["id"], runtime_context="operator_runtime")[
                "active"
            ]
        )
        board_event = api.jarvis_operator.memory_store.last_board_event()
        self.assertEqual(board_event["action"], "expiry_review")
        self.assertEqual(board_event["meta"]["targeting_mode"], "explicit_id")
        self.assertEqual(board_event["meta"]["requested_target_ids"], [blocker["id"]])
        self.assertEqual(board_event["meta"]["archived_ids"], [blocker["id"]])

    @patch("src.api.init_ai")
    def test_fast_mode_can_auto_route_debug_turns(self, mock_init_ai):
        """Fast mode should auto-route strongly debug-shaped requests into Debug without forcing operator tools."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The chat route likely breaks in api.py."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "This trace shows a UI mismatch in api.py. Inspect this output and diff this state.",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_response_mode"], "fast")
        self.assertEqual(payload["response_mode"], "debug")
        self.assertEqual(payload["mode_guidance"]["status"], "auto_routed")
        self.assertEqual(payload["mode_guidance"]["recommended_mode"], "debug")
        self.assertTrue(payload["mode_guidance"]["auto_applied"])
        self.assertEqual(payload["mode_guidance"]["resolved_scope"], "debugging")
        self.assertEqual(payload["mode_guidance"]["resolved_voice"], "jarvis")
        self.assertEqual(payload["response_trace"]["mode"], "debug")
        self.assertEqual(payload["response_trace"]["contract"], "trace_isolate_verify")
        self.assertIsNone(payload["tool_result"])
        self.assertIsNone(payload["action_lifecycle"])
        mock_init_ai.assert_called_once()

    def test_memory_endpoints_round_trip(self):
        """Persistent memory endpoints should add, list, and delete notes."""
        create_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Remember that AAIS-main is the active Jarvis base.",
                "category": "project",
                "priority": 72,
                "tags": ["jarvis", "project"],
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created = create_response.get_json()
        self.assertEqual(created["category"], "project")
        self.assertEqual(created["priority"], 72)
        self.assertTrue(created["active"])
        self.assertEqual(created["governance"]["action"], "write")

        update_response = self.client.patch(
            f"/api/jarvis/memory/{created['id']}",
            json={
                "pinned": True,
                "category": "operator",
                "priority": 88,
                "tags": ["jarvis", "active"],
            },
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertTrue(update_response.get_json()["pinned"])
        self.assertEqual(update_response.get_json()["category"], "operator")
        self.assertEqual(update_response.get_json()["priority"], 88)
        self.assertEqual(update_response.get_json()["tags"], ["jarvis", "active"])
        self.assertEqual(update_response.get_json()["governance"]["action"], "update")

        list_response = self.client.get("/api/jarvis/memory?query=active%20jarvis&category=operator&active=true")
        self.assertEqual(list_response.status_code, 200)
        memories = list_response.get_json()["memories"]
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["id"], created["id"])

        override_response = self.client.post(
            "/api/jarvis/memory/override",
            json={"content": "The Memory Bank page is the canonical place to rewrite long-term memory."},
        )
        self.assertEqual(override_response.status_code, 201)
        override_payload = override_response.get_json()
        self.assertTrue(override_payload["override"])
        self.assertGreaterEqual(override_payload["priority"], 95)
        self.assertEqual(override_payload["governance"]["action"], "write")

        delete_response = self.client.delete(f"/api/jarvis/memory/{created['id']}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.get_json()["governance"]["action"], "delete")
        remaining_memories = self.client.get("/api/jarvis/memory").get_json()["memories"]
        self.assertEqual(len(remaining_memories), 1)
        self.assertEqual(remaining_memories[0]["id"], override_payload["id"])

    def test_memory_list_endpoint_returns_controlled_block_when_gateway_is_quarantined(self):
        """Memory reads should return a governed 403 instead of a generic server error after quarantine."""
        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.get("/api/jarvis/memory")

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")

    def test_workbench_returns_controlled_block_when_memory_gateway_is_quarantined(self):
        """Workbench should surface memory quarantine as a governed 403 instead of a generic failure."""
        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.get("/api/jarvis/workbench")

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")

    def test_state_hygiene_returns_controlled_block_when_memory_gateway_is_quarantined(self):
        """State hygiene should surface memory quarantine as a governed 403 instead of a generic failure."""
        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.get("/api/jarvis/state-hygiene")

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")

    def test_state_hygiene_compact_returns_controlled_block_when_memory_gateway_is_quarantined(self):
        """State hygiene compaction should surface memory quarantine as a governed 403 instead of a generic failure."""
        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.post("/api/jarvis/state-hygiene/compact")

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory mutations are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")

    @patch("src.api.init_ai")
    def test_chat_message_returns_controlled_block_when_memory_gateway_is_quarantined(self, mock_init_ai):
        """Normal chat turns should surface memory quarantine as a governed 403."""
        create_response = self.client.post("/api/chat/sessions", json={"system_prompt": "You are Jarvis."})
        session_id = create_response.get_json()["session_id"]

        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Help me debug the memory seam."},
        )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_stream_emits_governed_block_when_memory_gateway_is_quarantined(self, mock_init_ai):
        """Streaming chat should emit a governed block event instead of a generic SSE error."""
        create_response = self.client.post("/api/chat/sessions", json={"system_prompt": "You are Jarvis."})
        session_id = create_response.get_json()["session_id"]

        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={"message": "Help me debug the memory seam."},
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        blocked_payload = next(payload for payload in payloads if payload["event"] == "blocked")
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", blocked_payload["error"])
        self.assertEqual(blocked_payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(blocked_payload["memory_enforcer"]["module_governance"]["status"], "quarantined")
        self.assertFalse(any(payload["event"] == "error" for payload in payloads))
        self.assertEqual(payloads[-1]["event"], "done")
        mock_init_ai.assert_not_called()

    def test_knowledge_authority_returns_controlled_block_when_memory_gateway_is_quarantined(self):
        """Knowledge authority should surface memory quarantine as a governed 403."""
        api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        api.jarvis_operator.memory_enforcer.module_governance_controller.report_runtime_signal(
            api.jarvis_operator.memory_enforcer.component_id,
            signal_type="unauthorized_memory_creation",
            reason="Simulated bypass containment.",
        )

        response = self.client.get("/api/jarvis/knowledge")

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIn("Memory reads are blocked because the gateway is not admitted.", payload["error"])
        self.assertEqual(payload["memory_enforcer"]["decision"], "BLOCK")
        self.assertEqual(payload["memory_enforcer"]["module_governance"]["status"], "quarantined")

    def test_memory_endpoints_emit_security_and_immune_events(self):
        """Memory CRUD should travel through the unified security brain and immune audit trail."""
        create_response = self.client.post(
            "/api/jarvis/memory",
            json={"content": "Remember the governance console lives in Jarvis.", "category": "governance"},
        )
        self.assertEqual(create_response.status_code, 201)

        security_response = self.client.get("/api/jarvis/security/events")
        self.assertEqual(security_response.status_code, 200)
        security_events = security_response.get_json()["events"]
        self.assertTrue(any(event["action"] == "write_memory" for event in security_events))

        immune_response = self.client.get("/api/jarvis/immune")
        self.assertEqual(immune_response.status_code, 200)
        immune_payload = immune_response.get_json()["immune_system"]
        self.assertGreaterEqual(immune_payload["event_count"], 1)
        self.assertEqual(immune_payload["system_mode"], "normal")

    def test_memory_governance_routes_track_why_history_archive_and_merge(self):
        """Memory governance routes should keep rationale, rewrite history, archive state, and merge lineage."""
        target_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Keep Jarvis operator memory focused on AAIS-main.",
                "category": "operator",
                "why": "Operator truth should stay anchored to the active repo.",
            },
        )
        source_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "AAIS-main is the canonical operator workspace.",
                "category": "project",
                "why": "This duplicate should merge into the operator note.",
            },
        )
        archive_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Old prompt-lab note.",
                "category": "general",
                "why": "Archive test record.",
            },
        )

        target_id = target_response.get_json()["id"]
        source_id = source_response.get_json()["id"]
        archive_id = archive_response.get_json()["id"]

        rewrite_response = self.client.patch(
            f"/api/jarvis/memory/{target_id}",
            json={
                "content": "Keep Jarvis operator memory focused on AAIS-main and its workbench.",
                "why": "The new workbench is now part of operator truth.",
                "note": "Expanded the operator memory after the workbench upgrade.",
            },
        )
        self.assertEqual(rewrite_response.status_code, 200)
        self.assertEqual(
            rewrite_response.get_json()["why"],
            "The new workbench is now part of operator truth.",
        )

        merge_response = self.client.post(
            "/api/jarvis/memory/merge",
            json={
                "target_id": target_id,
                "source_ids": [source_id],
                "why": "One canonical memory should hold the workspace truth.",
                "note": "Merged duplicate workspace truth into the operator note.",
            },
        )
        self.assertEqual(merge_response.status_code, 200)
        merged_target = merge_response.get_json()["memory"]
        self.assertEqual(merged_target["id"], target_id)
        self.assertIn(source_id, merged_target["merged_from"])
        self.assertEqual(
            merged_target["why"],
            "One canonical memory should hold the workspace truth.",
        )
        self.assertTrue(any(entry["type"] == "merged" for entry in merged_target["history"]))

        source_detail = self.client.get(f"/api/jarvis/memory/{source_id}")
        self.assertEqual(source_detail.status_code, 200)
        source_memory = source_detail.get_json()["memory"]
        self.assertFalse(source_memory["active"])
        self.assertEqual(source_memory["merged_into"], target_id)
        self.assertTrue(any(entry["type"] == "merged_into" for entry in source_memory["history"]))

        archive_result = self.client.post(
            f"/api/jarvis/memory/{archive_id}/archive",
            json={"reason": "Prompt-lab note archived after the workbench consolidation."},
        )
        self.assertEqual(archive_result.status_code, 200)
        archived_memory = archive_result.get_json()["memory"]
        self.assertFalse(archived_memory["active"])
        self.assertIsNotNone(archived_memory["archived_at"])
        self.assertEqual(archived_memory["history"][-1]["type"], "archived")
        self.assertEqual(archive_result.get_json()["governance"]["action"], "archive")

    def test_memory_merge_rejects_non_live_or_archived_sources(self):
        """Live canonical memories should not absorb archived or non-live source records."""
        target_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Keep operator truth anchored to the live AAIS workspace.",
                "category": "operator",
                "state_class": "live",
                "truth_status": "canonical",
            },
        )
        source_response = self.client.post(
            "/api/jarvis/memory",
            json={
                "content": "Demo workspace note that should never merge into live truth.",
                "category": "operator",
                "state_class": "demo",
                "truth_status": "derived",
            },
        )

        target_id = target_response.get_json()["id"]
        source_id = source_response.get_json()["id"]

        merge_response = self.client.post(
            "/api/jarvis/memory/merge",
            json={
                "target_id": target_id,
                "source_ids": [source_id],
                "note": "This should be rejected because state classes do not match.",
            },
        )

        self.assertEqual(merge_response.status_code, 400)
        self.assertIn("state class", merge_response.get_json()["error"].lower())

        detail_response = self.client.get(f"/api/jarvis/memory/{target_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.get_json()["memory"]
        history_types = [entry["type"] for entry in detail_payload["history"]]
        self.assertIn("created", history_types)
        self.assertNotIn("merged", history_types)

    def test_memory_board_endpoint_exposes_capability_board(self):
        """The Jarvis memory board endpoint should expose the new linked board installation."""
        response = self.client.get("/api/jarvis/memory/board")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        board = payload["memory_board"]

        self.assertEqual(board["max_slots"], 10)
        self.assertEqual(board["active_slots"], 6)
        self.assertEqual(board["installed_slots"], 6)
        self.assertEqual(board["reserved_slots"], 4)
        self.assertEqual(board["board"]["board_id"], "capability_adapter_board")
        self.assertEqual(board["slots"][0]["module"]["module_id"], "capability_foundation_v2")
        self.assertEqual(board["slots"][5]["module"]["module_id"], "capability_routing_preferences_v2")
        self.assertIsNone(board["slots"][6]["module"])
        self.assertIn("governance", board)

    def test_capability_bridge_endpoint_exposes_registry_and_recent_events(self):
        """The bridge endpoint should show registered tools and recent governed capability usage."""
        self.client.post(
            "/api/jarvis/mystic-read",
            json={
                "tool": "mystic_reading",
                "args": {"input": "I need direction."},
            },
        )

        response = self.client.get("/api/jarvis/capability-bridge")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        tool_ids = [tool["tool"] for tool in payload["registered_tools"]]
        self.assertIn("mystic_reading", tool_ids)
        self.assertIn("v9_core", tool_ids)
        self.assertIn("v10_core", tool_ids)
        self.assertIn("mystic", payload["registry"])
        self.assertIn("reading", payload["registry"]["mystic"])
        capability_ids = [capability["id"] for capability in payload["available_capabilities"]]
        self.assertIn("mystic", capability_ids)
        mystic_health = payload["module_health"]["mystic"]
        self.assertEqual(mystic_health["module"], "mystic")
        self.assertEqual(mystic_health["tool"], "mystic_reading")
        self.assertEqual(payload["phase_gate"]["capabilities"]["mystic"]["phase"], "active")
        self.assertEqual(payload["phase_gate"]["bridge"]["phase"], "active")
        self.assertGreaterEqual(payload["event_count"], 1)
        self.assertEqual(payload["recent_events"][-1]["tool_type"], "mystic_reading")
        self.assertEqual(payload["recent_events"][-1]["capability_id"], "mystic")

    def test_capability_bridge_execute_endpoint_runs_selection_and_returns_trace(self):
        """The execute endpoint should run a governed selection and return tool plus trace metadata."""
        response = self.client.post(
            "/api/jarvis/capability-bridge/execute",
            json={
                "capability": "mystic",
                "action": "reading",
                "args": {
                    "input": "I feel stuck and need direction.",
                },
                "execution_profile": {
                    "provider_mode": "deterministic",
                    "governance_mode": "strict",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "mystic_reading")
        self.assertEqual(payload["tool_result"]["capability"]["module"], "mystic")
        self.assertEqual(payload["tool_result"]["capability"]["action"], "read")
        self.assertEqual(payload["execution_preview"]["path"], "capability_service_bridge")
        self.assertEqual(payload["execution_preview"]["service_lane"], "service_tools")
        self.assertEqual(payload["execution_preview"]["provider_mode_requested"], "deterministic")
        self.assertEqual(payload["execution_preview"]["governance_mode"], "strict")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["module"], "mystic")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["phase_gate"]["decision"], "ALLOW")
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["active_lane"], "service_tools")
        self.assertEqual(
            payload["response_trace"]["governed_pipeline"]["realtime_signal_feed"]["runtime_context"],
            "operator_runtime",
        )
        self.assertEqual(
            payload["response_trace"]["governed_pipeline"]["realtime_event_cause_predictor"]["cause_class"],
            "operator_service_request",
        )
        self.assertEqual(
            payload["response_trace"]["governed_pipeline"]["operator_health_sentinel"]["operator_state"],
            "watch",
        )
        self.assertIn("mystic", payload["capability_bridge"]["registry"])

    def test_capability_bridge_execute_endpoint_blocks_prototype_component(self):
        """Phase gate should fail closed when a prototype component is selected for operator runtime."""
        api.jarvis_operator.capability_bridge.snapshot()
        demote_component(
            "jarvis.capability.mystic",
            Phase.PROTOTYPE,
            reason="Prototype-only until further admission review.",
            actor="pytest",
        )

        response = self.client.post(
            "/api/jarvis/capability-bridge/execute",
            json={
                "capability": "mystic",
                "action": "reading",
                "args": {"input": "I feel stuck and need direction."},
                "execution_profile": {
                    "provider_mode": "deterministic",
                    "governance_mode": "strict",
                },
            },
        )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertEqual(payload["phase_gate"]["decision"], "BLOCK")
        self.assertEqual(payload["phase_gate"]["component"]["phase"], "prototype")
        self.assertEqual(payload["tool_result"]["status"], "blocked")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["error_type"], "PhaseViolationError")

    def test_governance_policy_request_and_break_glass_flow(self):
        """Governance endpoints should support staging, promotion, and break-glass state."""
        create_response = self.client.post(
            "/api/jarvis/governance/policy-requests",
            json={
                "title": "Promote immune posture policy",
                "actor_id": "security_local",
                "actor_role": "security_engineer",
                "dsl_text": "allow output summaries, block raw secrets",
                "risk_score": 2.0,
            },
        )
        self.assertEqual(create_response.status_code, 201)
        request_payload = create_response.get_json()["policy_request"]
        self.assertEqual(request_payload["status"], "staged")

        promote_response = self.client.post(
            f"/api/jarvis/governance/policy-requests/{request_payload['id']}/promote",
            json={"actor_id": "owner_local", "actor_role": "owner", "rollout_strategy": "canary"},
        )
        self.assertEqual(promote_response.status_code, 200)
        self.assertEqual(promote_response.get_json()["policy_request"]["status"], "promoted")

        break_glass_response = self.client.post(
            "/api/jarvis/governance/break-glass",
            json={
                "actor_id": "owner_local",
                "actor_role": "owner",
                "scope": "high_sensitivity_access",
                "duration_minutes": 10,
                "reason": "Need operator access during a crisis drill.",
            },
        )
        self.assertEqual(break_glass_response.status_code, 200)
        snapshot_response = self.client.get("/api/jarvis/governance")
        self.assertEqual(snapshot_response.status_code, 200)
        governance_payload = snapshot_response.get_json()["governance"]
        self.assertTrue(governance_payload["active_break_glass"]["active"])
        self.assertTrue(any(event["event_type"] == "policy_promoted" for event in governance_payload["recent_events"]))

    def test_module_governance_admission_and_quarantine_flow(self):
        """Module governance should admit compliant modules and quarantine hostile ones."""
        admit_response = self.client.post(
            "/api/jarvis/module-governance/modules/admit",
            json={
                "module_id": "signal_hud",
                "label": "Signal HUD",
                "lane": "experience",
                "declared_scope": ["ui", "telemetry"],
                "cisiv": {
                    "concept": {
                        "status": "passed",
                        "summary": "Provide transient operator telemetry visibility.",
                    },
                    "identity": {
                        "status": "passed",
                        "summary": "Avoid identity reconstruction and user possession.",
                    },
                    "structure": {
                        "status": "passed",
                        "summary": "Stay inside the UI and telemetry surfaces under Jarvis authority.",
                    },
                    "implementation": {
                        "status": "implemented",
                        "summary": "Ship as a bounded telemetry HUD module.",
                    },
                    "verification": {
                        "status": "verified",
                        "summary": "Admission and smoke verification were captured.",
                        "evidence": ["pytest tests/test_api.py -q", "module admission smoke"],
                    },
                },
                "compliance": {
                    "stores_persistent_user_metadata": False,
                    "creates_user_identity_profiles": False,
                    "retains_behavioral_history": False,
                    "infers_user_labels": False,
                    "builds_personality_models": False,
                    "builds_behavior_models": False,
                    "stores_live_signals": False,
                    "reconstructs_signals": False,
                    "requires_identity_history": False,
                    "adaptive_logic_scope": "system",
                    "alters_nova_tone": False,
                    "alters_nova_role": False,
                    "alters_nova_constancy": False,
                    "bypasses_jarvis_authority": False,
                    "bypasses_routing": False,
                    "logs_user_identity": False,
                    "logs_behavior_patterns": False,
                    "logs_biometric_traces": False,
                    "hidden_logging": False,
                    "exfiltrates_data": False,
                },
            },
        )
        self.assertEqual(admit_response.status_code, 201)
        admitted_module = admit_response.get_json()["module"]
        self.assertEqual(admitted_module["status"], "admitted")
        self.assertEqual(admitted_module["cisiv_stage"], "verification")
        self.assertEqual(admitted_module["cisiv_status"], "pass")

        signal_response = self.client.post(
            "/api/jarvis/module-governance/modules/signal_hud/signals",
            json={
                "signal_type": "nova_identity_interference",
                "reason": "Module attempted to alter Nova tone during runtime.",
            },
        )
        self.assertEqual(signal_response.status_code, 200)
        signal_payload = signal_response.get_json()
        self.assertEqual(signal_payload["module"]["status"], "blacklisted")
        self.assertEqual(signal_payload["severity"], "high")
        immune_payload = signal_payload["immune_system"]
        self.assertTrue(any(item["module_id"] == "signal_hud" for item in immune_payload["quarantined_modules"]))
        self.assertTrue(any(item["module_id"] == "signal_hud" for item in immune_payload["blacklisted_modules"]))

        snapshot_response = self.client.get("/api/jarvis/module-governance")
        self.assertEqual(snapshot_response.status_code, 200)
        snapshot = snapshot_response.get_json()["module_governance"]
        self.assertGreaterEqual(snapshot["module_counts"]["blacklisted"], 1)
        self.assertEqual(
            snapshot["cisiv_stage_sequence"],
            ["concept", "identity", "structure", "implementation", "verification"],
        )
        self.assertIn("Use the signal. Do not keep the trace.", snapshot["core_lines"])

    @patch("src.api.init_ai")
    def test_continuity_profile_updates_flow_into_session_and_protocol(self, mock_init_ai):
        """Continuity profile settings should persist outside the model and attach to the session protocol."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Jarvis kept the continuity anchor and answered directly."
        mock_init_ai.return_value = (fake_model, object())

        patch_response = self.client.patch(
            "/api/jarvis/continuity/profile?user_id=operator",
            json={
                "tone": "detailed",
                "known_projects": ["AAIS-main"],
                "preferred_tools": ["Run Pytest"],
                "self_description": "You are Jarvis, the sovereign core of AAIS.",
                "continuity_rules": [
                    "Answer as Jarvis in one consistent voice.",
                    "Preserve continuity before display.",
                ],
            },
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.get_json()["continuity_profile"]["tone"], "detailed")

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "provider": "local", "response_mode": "fast"},
        )
        session_id = create_response.get_json()["session_id"]
        message_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Keep the governance console coherent with the rest of Jarvis.",
                "provider": "local",
                "response_mode": "fast",
            },
        )
        self.assertEqual(message_response.status_code, 200)
        self.assertEqual(message_response.get_json()["continuity_profile"]["tone"], "detailed")

        protocol_response = self.client.get(f"/api/jarvis/protocol?session_id={session_id}")
        self.assertEqual(protocol_response.status_code, 200)
        session_payload = protocol_response.get_json()["session"]
        self.assertEqual(session_payload["continuity_profile"]["tone"], "detailed")
        channels = [message["channel"] for message in session_payload["envelope"]["messages"]]
        self.assertIn("continuity", channels)

    def test_system_guard_pause_blocks_chat_turns_until_resume(self):
        """Pausing the system guard should block new turns, then allow them again after resume."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        pause_response = self.client.post(
            "/api/system/guard",
            json={"action": "pause", "reason": "Cooling the laptop down."},
        )
        self.assertEqual(pause_response.status_code, 200)
        self.assertEqual(pause_response.get_json()["system_guard"]["status"], "paused")

        blocked_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Can you still answer this turn?"},
        )
        self.assertEqual(blocked_response.status_code, 423)
        blocked_payload = blocked_response.get_json()
        self.assertEqual(blocked_payload["system_guard"]["status"], "paused")
        self.assertEqual(blocked_payload["session_state"]["state"], "degraded")

        with patch("src.api.init_ai") as mock_init_ai:
            fake_model = MagicMock()
            fake_model.generate_chat.return_value = "Jarvis is back online."
            mock_init_ai.return_value = (fake_model, object())

            resume_response = self.client.post(
                "/api/system/guard",
                json={"action": "resume", "reason": "Resume normal local work."},
            )
            self.assertEqual(resume_response.status_code, 200)
            self.assertEqual(resume_response.get_json()["system_guard"]["status"], "nominal")

            live_response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={"message": "Can you answer this turn now?"},
            )

        self.assertEqual(live_response.status_code, 200)
        self.assertEqual(live_response.get_json()["response"], "Jarvis is back online.")

    def test_system_guard_safe_stop_unloads_runtime_and_blocks_inference(self):
        """Safe Stop should unload the local runtime and block guarded inference endpoints."""
        api.ai_model = object()
        api.streaming_generator = object()
        api.ai_mode = "real"
        api.ai_init_error = None

        stop_response = self.client.post(
            "/api/system/guard",
            json={"action": "safe_stop", "reason": "Cool the GPU."},
        )

        self.assertEqual(stop_response.status_code, 200)
        stop_payload = stop_response.get_json()
        self.assertEqual(stop_payload["system_guard"]["status"], "stopped")
        self.assertIsNone(stop_payload["active_model_mode"])
        self.assertEqual(stop_payload["ai_status"], "not_initialized")

        blocked_response = self.client.post(
            "/api/text/generate",
            json={"prompt": "hello"},
        )
        self.assertEqual(blocked_response.status_code, 503)
        blocked_payload = blocked_response.get_json()
        self.assertEqual(blocked_payload["system_guard"]["status"], "stopped")

    def test_workspace_endpoints_return_projects_search_and_file_preview(self):
        """Workspace tools should expose projects, search, and file previews."""
        projects_response = self.client.get("/api/jarvis/workspace/projects")
        self.assertEqual(projects_response.status_code, 200)
        self.assertEqual(projects_response.get_json()["projects"][0]["name"], "AAIS-main")

        search_response = self.client.post(
            "/api/jarvis/workspace/search",
            json={"query": "memory workspace", "limit": 5},
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertGreaterEqual(len(search_response.get_json()["results"]), 1)

        file_response = self.client.get("/api/jarvis/workspace/file?path=AAIS-main/notes.txt")
        self.assertEqual(file_response.status_code, 200)
        self.assertIn("workspace tools", file_response.get_json()["content"])

    @patch("src.api.web_researcher")
    def test_live_research_endpoint_returns_sources(self, mock_researcher):
        """Live research endpoint should return web sources for the UI."""
        mock_researcher.research.return_value = {
            "query": "latest OpenAI news",
            "summary": "Loaded 2 live web sources.",
            "sources": [
                {
                    "id": 1,
                    "title": "OpenAI News",
                    "url": "https://openai.com/news/",
                    "display_url": "openai.com/news/",
                    "snippet": "Latest updates.",
                    "excerpt": "Latest updates.",
                },
            ],
            "prompt_block": "Live web research is attached.",
        }

        response = self.client.post(
            "/api/jarvis/research",
            json={"query": "latest OpenAI news"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["query"], "latest OpenAI news")
        self.assertEqual(payload["sources"][0]["title"], "OpenAI News")

    def test_safe_action_catalog_endpoint_returns_available_actions(self):
        """The UI should be able to load the safe local action catalog."""
        response = self.client.get("/api/jarvis/actions")

        self.assertEqual(response.status_code, 200)
        actions = response.get_json()["actions"]
        action_ids = {action["id"] for action in actions}
        self.assertIn("git_status", action_ids)
        self.assertIn("run_pytest", action_ids)

    def test_specialist_catalog_endpoint_returns_domains_and_specialists(self):
        """The UI should be able to load the logical specialist registry."""
        response = self.client.get("/api/jarvis/specialists")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        domains = payload["domains"]
        presets = payload["presets"]
        domain_ids = {domain["id"] for domain in domains}
        self.assertIn("coding", domain_ids)
        self.assertIn("training", domain_ids)
        all_specialist_ids = {
            specialist["id"]
            for domain in domains
            for specialist in domain["specialists"]
        }
        self.assertIn("debugging", all_specialist_ids)
        self.assertIn("finetune", all_specialist_ids)
        preset_ids = {preset["id"] for preset in presets}
        self.assertIn("bug_hunt", preset_ids)
        self.assertIn("small_llm_trainer", preset_ids)

    @patch("src.api.jarvis_operator.execute_action")
    def test_execute_safe_action_endpoint_returns_tool_result(self, mock_execute_action):
        """Approved safe local actions should return an inline tool result payload."""
        mock_execute_action.return_value = {
            "response": "Run Pytest finished.\n27 passed\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "run_pytest",
                    "label": "Run Pytest",
                    "description": "Run the backend test suite.",
                    "command_preview": "python -m pytest -q",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "27 passed",
                "stderr": "",
                "summary": "27 passed",
                "ran_at": "2026-04-01T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/actions/execute",
            json={
                "action_id": "run_pytest",
                "approved": True,
                "persona_mode": "builder",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "action_result")
        self.assertEqual(payload["tool_result"]["action"]["id"], "run_pytest")
        self.assertEqual(payload["persona_mode"], "builder")
        self.assertEqual(payload["response_mode"], "fast")
        self.assertEqual(payload["session_state"]["state"], "ready")
        self.assertIn(payload["policy_status"]["status"], {"allow", "warn"})
        mock_execute_action.assert_called_once()
        self.assertEqual(mock_execute_action.call_args.args[0], "run_pytest")
        self.assertEqual(mock_execute_action.call_args.kwargs["session_id"], session_id)

    @patch("src.api.jarvis_operator.execute_action")
    def test_execute_safe_action_auto_links_to_active_mission(self, mock_execute_action):
        """Executed local actions should be attached to the active mission automatically."""
        mock_execute_action.return_value = {
            "response": "Run Pytest finished.",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "run_pytest",
                    "label": "Run Pytest",
                    "description": "Run the backend test suite.",
                    "command_preview": "python -m pytest -q",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "27 passed",
                "stderr": "",
                "summary": "27 passed",
                "ran_at": "2026-04-01T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Verify backend health",
                "objective": "Run the backend checks and make sure the test suite is green.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/actions/execute",
            json={
                "action_id": "run_pytest",
                "approved": True,
                "persona_mode": "builder",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        board = response.get_json()["mission_board"]
        active = board["active_mission"]
        self.assertEqual(response.get_json()["mission_critic"]["source"], "action_result")
        self.assertEqual(active["critic"]["source"], "action_result")
        self.assertTrue(any(link["value"] == "run_pytest" for link in active["links"]))
        self.assertTrue(any(entry["kind"] == "action_result" for entry in active["activity"]))
        self.assertEqual(
            [entry["kind"] for entry in active["history"]][-2:],
            ["action_result", "critic_review"],
        )

    @patch("src.api.init_ai")
    def test_session_events_endpoint_returns_v8_event_log(self, mock_init_ai):
        """Session events should expose the V8 lifecycle trail for a completed turn."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Jarvis finished the turn."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        message_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Help me debug the chat route in api.py.", "response_mode": "think"},
        )
        self.assertEqual(message_response.status_code, 200)

        events_response = self.client.get(f"/api/chat/sessions/{session_id}/events")
        self.assertEqual(events_response.status_code, 200)
        events = events_response.get_json()["events"]
        event_types = [event["event_type"] for event in events]
        self.assertIn("session_created", event_types)
        self.assertIn("user_message_received", event_types)
        self.assertIn("context_gathered", event_types)
        self.assertIn("assistant_response_ready", event_types)

    def test_record_session_event_dedupes_duplicate_turn_events(self):
        """Per-turn event logging should suppress repeated copies of the same lifecycle event."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        session = conversation_memory.get_session(session_id)

        api._begin_turn_trace(session)
        first = api._record_session_event(
            session,
            "context_gathered",
            "Jarvis gathered memory, workspace, and optional research context.",
            payload={"location": "context", "action": "hydrate", "timestamp": "2026-04-19T10:00:00Z"},
        )
        second = api._record_session_event(
            session,
            "context_gathered",
            "  Jarvis   gathered memory, workspace, and optional research context.  ",
            payload={"location": "context", "action": "hydrate", "timestamp": "2026-04-19T10:00:01Z"},
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)

        events_response = self.client.get(f"/api/chat/sessions/{session_id}/events")
        self.assertEqual(events_response.status_code, 200)
        events = events_response.get_json()["events"]
        matching = [event for event in events if event["event_type"] == "context_gathered"]
        self.assertEqual(len(matching), 1)

    def test_runtime_payload_dedupes_duplicate_response_trace_steps(self):
        """Payload serialization should collapse duplicate trace steps before returning them."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["response_trace"] = {
            "mode": "think",
            "steps": [
                "Loaded workspace context.",
                "  Loaded   workspace   context. ",
                "Built a planning pass.",
                "Built a planning pass.",
            ],
        }

        payload = api._build_chat_runtime_payload(session, session_id)
        session_payload = api._serialize_session_payload(session)

        self.assertEqual(
            payload["response_trace"]["steps"],
            ["Loaded workspace context.", "Built a planning pass."],
        )
        self.assertEqual(
            session_payload["response_trace"]["steps"],
            ["Loaded workspace context.", "Built a planning pass."],
        )

    def test_policy_endpoint_reflects_waiting_action_approval(self):
        """Policy and lifecycle endpoints should reflect approval-gated local actions."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        action_response = self.client.post(
            f"/api/chat/sessions/{session_id}/actions/execute",
            json={"action_id": "run_pytest", "approved": False},
        )
        self.assertEqual(action_response.status_code, 400)
        self.assertEqual(action_response.get_json()["policy_status"]["status"], "deny")

        policy_response = self.client.get(f"/api/chat/sessions/{session_id}/policy")
        self.assertEqual(policy_response.status_code, 200)
        self.assertEqual(policy_response.get_json()["policy_status"]["status"], "deny")

        session_response = self.client.get(f"/api/chat/sessions/{session_id}")
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response.get_json()["session_state"]["state"], "awaiting_approval")

    @patch("src.api.init_ai")
    def test_action_proposal_sets_pending_state_and_operator_trace(self, mock_init_ai):
        """Action proposals should store pending state and stay in the operator trace lane."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Show git status before we keep going.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "action_request")
        self.assertEqual(payload["tool_result"]["action"]["id"], "git_status")
        self.assertEqual(payload["session_state"]["state"], "awaiting_approval")
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["stage"], "proposed")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["approval_state"], "awaiting")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["execution_state"], "pending")
        self.assertEqual(payload["pending_action"]["id"], "git_status")
        self.assertEqual(payload["action_lifecycle"]["stage"], "proposed")
        self.assertEqual(payload["action_lifecycle"]["mode"], "operator")
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_explicit_think_mode_beats_stale_operator_session_state(self, mock_init_ai):
        """An explicit Think request should stay in the Think lane even if the session was previously operator-biased."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The likely failure is in the route state transition, not the test runner."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "response_mode": "operator"},
        )
        session_id = create_response.get_json()["session_id"]
        session = api.conversation_memory.get_session(session_id)
        stale_action = api._store_pending_action(
            session,
            api.jarvis_operator.action_runner.get_action("run_pytest"),
        )
        api._set_action_lifecycle(
            session,
            stage="proposed",
            action=stale_action,
            approval_state="awaiting",
            execution_state="pending",
            source="test_seed",
            response_mode="operator",
        )

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Think through why pytest keeps failing in src/api.py without running anything yet.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_response_mode"], "think")
        self.assertEqual(payload["response_mode"], "think")
        self.assertEqual(payload["response_trace"]["mode"], "think")
        self.assertEqual(payload["response_trace"]["contract"], "gather_plan_answer")
        self.assertIsNone(payload["tool_result"])
        mock_init_ai.assert_called_once()

    @patch("src.api.init_ai")
    def test_mode_switch_away_from_operator_prevents_unsolicited_pytest_proposal(self, mock_init_ai):
        """Switching away from Operator should stop vague pytest/debug language from auto-proposing a tool."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The failure likely sits in api.py state handling, not in a new test run."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Can you verify the repo before we keep going?",
                "response_mode": "operator",
            },
        )

        self.assertEqual(proposal_response.status_code, 200)
        self.assertEqual(proposal_response.get_json()["tool_result"]["type"], "action_request")

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Think through why pytest keeps failing in api.py without running it yet.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_response_mode"], "think")
        self.assertEqual(payload["response_mode"], "think")
        self.assertEqual(payload["response_trace"]["mode"], "think")
        self.assertIsNone(payload["tool_result"])
        mock_init_ai.assert_called_once()

    @patch("src.api.init_ai")
    def test_truth_scope_operator_request_does_not_auto_route_into_debug(self, mock_init_ai):
        """Truth-scope and memory-governance work should not be mistaken for debugging intent."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Operator truth should stay canonical and visible without entering debug mode."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Review the state truth, knowledge truth, memory governance, and constraints for this turn.",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertNotEqual(payload["response_mode"], "debug")
        self.assertEqual(payload["mode_guidance"]["resolved_scope"], "operator_task")
        self.assertEqual(payload["mode_guidance"]["resolved_voice"], "jarvis")
        self.assertFalse(payload["mode_guidance"]["auto_applied"])
        self.assertIsNone(payload["tool_result"])

    @patch("src.api.init_ai")
    def test_debug_lockout_resets_next_fast_turn_without_explicit_retrigger(self, mock_init_ai):
        """After one debug turn, the next fast turn should default back out of debug unless re-triggered explicitly."""
        fake_model = MagicMock()
        fake_model.generate_chat.side_effect = [
            "The backend and UI disagree about the session state.",
            "Next operator step: inspect the current state without re-entering debug mode.",
        ]
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        first_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "This trace shows a UI mismatch between backend and UI state.",
                "response_mode": "fast",
            },
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.get_json()["response_mode"], "debug")

        second_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me inspect the current repo state and keep going.",
                "response_mode": "fast",
            },
        )

        self.assertEqual(second_response.status_code, 200)
        payload = second_response.get_json()
        self.assertNotEqual(payload["response_mode"], "debug")
        self.assertTrue(payload["mode_guidance"]["debug_lockout_applied"])
        self.assertEqual(payload["mode_guidance"]["resolved_scope"], "operator_task")

    @patch("src.api.init_ai")
    def test_identical_prompt_keeps_mode_voice_and_contract_stable_across_fallback_and_stale_state(
        self,
        mock_init_ai,
    ):
        """Fallback should change provider only; stale session state should not change the resolved turn contract."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("OpenRouter request failed: 429 temporarily rate-limited upstream")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_model.generate_chat.side_effect = [
            "Jarvis kept the turn analytical and local.",
            "Jarvis kept the turn analytical even after fallback.",
        ]
        mock_init_ai.return_value = (fake_model, object())
        prompt = "Think through why the Workbench state and backend state disagree without running anything yet."

        first_session_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        first_session_id = first_session_response.get_json()["session_id"]
        first_turn = self.client.post(
            f"/api/chat/sessions/{first_session_id}/message",
            json={"message": prompt, "response_mode": "think"},
        )

        second_session_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "response_mode": "operator"},
        )
        second_session_id = second_session_response.get_json()["session_id"]
        second_session = api.conversation_memory.get_session(second_session_id)
        stale_action = api._store_pending_action(
            second_session,
            api.jarvis_operator.action_runner.get_action("run_pytest"),
        )
        api._set_action_lifecycle(
            second_session,
            stage="proposed",
            action=stale_action,
            approval_state="awaiting",
            execution_state="pending",
            source="test_seed",
            response_mode="operator",
        )
        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            second_turn = self.client.post(
                f"/api/chat/sessions/{second_session_id}/message",
                json={
                    "message": prompt,
                    "response_mode": "think",
                    "provider": "openrouter",
                },
            )

        self.assertEqual(first_turn.status_code, 200)
        self.assertEqual(second_turn.status_code, 200)
        first_payload = first_turn.get_json()
        second_payload = second_turn.get_json()

        for payload in (first_payload, second_payload):
            self.assertEqual(payload["response_mode"], "think")
            self.assertEqual(payload["response_trace"]["mode"], "think")
            self.assertEqual(payload["response_trace"]["contract"], "gather_plan_answer")
            self.assertEqual(payload["mode_guidance"]["resolved_voice"], "jarvis")
            self.assertEqual(payload["mode_guidance"]["resolved_scope"], "operator_task")
            self.assertIsNone(payload["tool_result"])
            self.assertNotIn("plan pass", payload["response"].lower())
            self.assertNotIn("[/inst]", payload["response"].lower())

        self.assertEqual(len(first_payload["persistent_memories"]), len(second_payload["persistent_memories"]))
        self.assertIsNone(first_payload["provider_notice"])
        self.assertEqual(second_payload["provider_notice"]["status"], "fallback")
        self.assertEqual(second_payload["provider_notice"]["resolved_provider"], "local")

    @patch("src.api.jarvis_operator.execute_action")
    @patch("src.api.init_ai")
    def test_approval_phrase_without_pending_action_does_not_trigger_command_execution(
        self,
        mock_init_ai,
        mock_execute_action,
    ):
        """Approval phrases should not act like direct commands when no operator action is pending."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "No operator action is pending right now."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "approve action run_pytest",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_response_mode"], "think")
        self.assertEqual(payload["response_mode"], "think")
        self.assertEqual(payload["response_trace"]["mode"], "think")
        self.assertIsNone(payload["tool_result"])
        mock_execute_action.assert_not_called()
        mock_init_ai.assert_called_once()

    @patch("src.api._generate_remote_provider_reply")
    @patch("src.api._build_mode_plan")
    @patch("src.api._hydrate_jarvis_context")
    @patch("src.api.init_ai")
    @patch("src.api.jarvis_operator.execute_action")
    def test_message_approval_turn_executes_pending_action_without_planning_or_generation(
        self,
        mock_execute_action,
        mock_init_ai,
        mock_hydrate_context,
        mock_build_mode_plan,
        mock_remote_provider,
    ):
        """Approval turns on /message should execute pending actions directly without generation."""
        mock_execute_action.return_value = {
            "response": "Git Status finished.\nWorking tree clean.\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "git_status",
                    "label": "Git Status",
                    "description": "Inspect the current git working tree.",
                    "command_preview": "git status --short --branch",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "## main\n",
                "stderr": "",
                "summary": "Working tree clean.",
                "ran_at": "2026-04-06T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Can you verify the repo before we keep going?",
                "response_mode": "operator",
            },
        )

        self.assertEqual(proposal_response.status_code, 200)
        self.assertEqual(proposal_response.get_json()["tool_result"]["type"], "action_request")
        self.assertEqual(proposal_response.get_json()["session_state"]["state"], "awaiting_approval")

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "think"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "action_result")
        self.assertEqual(payload["tool_result"]["action"]["id"], "git_status")
        self.assertEqual(payload["response"], mock_execute_action.return_value["response"])
        self.assertEqual(payload["session_state"]["state"], "ready")
        self.assertIsNone(payload["pending_action"])
        self.assertEqual(payload["action_lifecycle"]["stage"], "executed")
        self.assertEqual(payload["action_lifecycle"]["approval_state"], "approved")
        self.assertEqual(payload["action_lifecycle"]["execution_state"], "executed")
        self.assertEqual(payload["action_lifecycle"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["stage"], "executed")
        self.assertNotIn("Plan Pass", payload["response"])
        self.assertNotIn("[/INST]", payload["response"])
        self.assertNotIn("reasoning", payload["response"].lower())

        mock_execute_action.assert_called_once()
        self.assertEqual(mock_execute_action.call_args.args[0], "git_status")
        self.assertEqual(mock_execute_action.call_args.kwargs["session_id"], session_id)
        mock_hydrate_context.assert_not_called()
        mock_build_mode_plan.assert_not_called()
        mock_remote_provider.assert_not_called()
        mock_init_ai.assert_not_called()

    @patch("src.api._generate_remote_provider_reply")
    @patch("src.api._messages_to_prompt")
    @patch("src.api._build_mode_plan")
    @patch("src.api._hydrate_jarvis_context")
    @patch("src.api.init_ai")
    @patch("src.api.jarvis_operator.execute_action")
    def test_stream_approval_turn_executes_pending_action_without_planning_or_generation(
        self,
        mock_execute_action,
        mock_init_ai,
        mock_hydrate_context,
        mock_build_mode_plan,
        mock_messages_to_prompt,
        mock_remote_provider,
    ):
        """Approval turns should execute pending actions directly without planning, prompts, or model output."""
        mock_execute_action.return_value = {
            "response": "Git Status finished.\nWorking tree clean.\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "git_status",
                    "label": "Git Status",
                    "description": "Inspect the current git working tree.",
                    "command_preview": "git status --short --branch",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "## main\n",
                "stderr": "",
                "summary": "Working tree clean.",
                "ran_at": "2026-04-06T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Can you verify the repo before we keep going?",
                "response_mode": "operator",
            },
        )

        self.assertEqual(proposal_response.status_code, 200)
        self.assertEqual(proposal_response.get_json()["tool_result"]["type"], "action_request")
        self.assertEqual(proposal_response.get_json()["session_state"]["state"], "awaiting_approval")

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={"message": "yes, run it", "response_mode": "think"},
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        raw_stream = response.get_data(as_text=True)
        payloads = [
            json.loads(line[6:])
            for line in raw_stream.splitlines()
            if line.startswith("data: ")
        ]
        final_payload = next(payload for payload in payloads if payload["event"] == "final")

        self.assertEqual(final_payload["tool_result"]["type"], "action_result")
        self.assertEqual(final_payload["tool_result"]["action"]["id"], "git_status")
        self.assertEqual(final_payload["response"], mock_execute_action.return_value["response"])
        self.assertEqual(final_payload["session_state"]["state"], "ready")
        self.assertIsNone(final_payload["pending_action"])
        self.assertEqual(final_payload["action_lifecycle"]["stage"], "executed")
        self.assertEqual(final_payload["action_lifecycle"]["approval_state"], "approved")
        self.assertEqual(final_payload["action_lifecycle"]["execution_state"], "executed")
        self.assertEqual(final_payload["action_lifecycle"]["mode"], "operator")
        self.assertEqual(final_payload["response_trace"]["mode"], "operator")
        self.assertEqual(final_payload["response_trace"]["action_lifecycle"]["stage"], "executed")
        self.assertFalse(any(payload["event"] == "token" for payload in payloads))
        self.assertNotIn("Plan Pass", raw_stream)
        self.assertNotIn("[/INST]", raw_stream)
        self.assertNotIn("reasoning", final_payload["response"].lower())

        mock_execute_action.assert_called_once()
        self.assertEqual(mock_execute_action.call_args.args[0], "git_status")
        self.assertEqual(mock_execute_action.call_args.kwargs["session_id"], session_id)
        mock_hydrate_context.assert_not_called()
        mock_build_mode_plan.assert_not_called()
        mock_messages_to_prompt.assert_not_called()
        mock_remote_provider.assert_not_called()
        mock_init_ai.assert_not_called()

    @patch("src.api.jarvis_operator.execute_action")
    @patch("src.api.init_ai")
    def test_approval_consumes_pending_action_exactly_once(
        self,
        mock_init_ai,
        mock_execute_action,
    ):
        """Approvals should consume a pending action once and never re-execute it implicitly."""
        mock_execute_action.return_value = {
            "response": "Git Status finished.\nWorking tree clean.\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "git_status",
                    "label": "Git Status",
                    "description": "Inspect the current git working tree.",
                    "command_preview": "git status --short --branch",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "## main\n",
                "stderr": "",
                "summary": "Working tree clean.",
                "ran_at": "2026-04-06T00:00:00+00:00",
            },
        }
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "No pending action is waiting now."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Can you verify the repo before we keep going?", "response_mode": "operator"},
        )

        first_approval = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "think"},
        )
        self.assertEqual(first_approval.status_code, 200)
        self.assertEqual(first_approval.get_json()["action_lifecycle"]["stage"], "executed")

        second_approval = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "fast"},
        )
        self.assertEqual(second_approval.status_code, 200)
        self.assertEqual(second_approval.get_json()["response"], "No pending action is waiting now.")
        self.assertIsNone(second_approval.get_json()["tool_result"])
        mock_execute_action.assert_called_once()
        self.assertEqual(mock_execute_action.call_args.args[0], "git_status")
        self.assertEqual(mock_execute_action.call_args.kwargs["session_id"], session_id)
        mock_init_ai.assert_called_once()

    @patch("src.api.jarvis_operator.execute_action")
    def test_approval_audit_route_tracks_proposal_and_execution_stages(self, mock_execute_action):
        """The evolving approval audit should mirror the real action lifecycle transitions."""
        mock_execute_action.return_value = {
            "response": "Git Status finished.\nWorking tree clean.\n\nExit code: 0",
            "tool_result": {
                "type": "action_result",
                "action": {
                    "id": "git_status",
                    "label": "Git Status",
                    "description": "Inspect the current git working tree.",
                    "command_preview": "git status --short --branch",
                },
                "status": "completed",
                "exit_code": 0,
                "stdout": "## main\n",
                "stderr": "",
                "summary": "Working tree clean.",
                "ran_at": "2026-04-06T00:00:00+00:00",
            },
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Show git status before we keep going.", "response_mode": "think"},
        )
        self.assertEqual(proposal_response.status_code, 200)
        approval_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "operator"},
        )
        self.assertEqual(approval_response.status_code, 200)

        audit_response = self.client.get(f"/api/chat/sessions/{session_id}/approval-audit")
        self.assertEqual(audit_response.status_code, 200)
        audit_payload = audit_response.get_json()
        entries = audit_payload["entries"]
        stages = [entry["stage"] for entry in entries]
        self.assertIn("executed", stages)
        self.assertIn("approved", stages)
        self.assertIn("proposed", stages)
        self.assertEqual(audit_payload["current"]["action_lifecycle"]["stage"], "executed")
        self.assertIsNone(audit_payload["current"]["pending_action"])

        session_response = self.client.get(f"/api/chat/sessions/{session_id}")
        self.assertEqual(session_response.status_code, 200)
        session_payload = session_response.get_json()
        self.assertGreaterEqual(len(session_payload["approval_audit"]), 3)
        self.assertEqual(session_payload["approval_audit"][0]["stage"], "executed")
        action_instance_ids = {
            entry["action_instance_id"]
            for entry in session_payload["approval_audit"]
        }
        self.assertEqual(len(action_instance_ids), 1)

    @patch("src.api.jarvis_operator.execute_action")
    @patch("src.api.init_ai")
    def test_message_approval_without_pending_action_falls_through_to_generation(
        self,
        mock_init_ai,
        mock_execute_action,
    ):
        """Approval-like text should not short-circuit when no pending action exists."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Normal generated answer."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        session = conversation_memory.get_session(session_id)
        session.transition_state(
            "awaiting_approval",
            summary="Waiting on approval for a now-missing action.",
            reason="test_waiting",
            event_type="test_waiting",
        )
        session.metadata.pop("pending_action", None)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, do it", "response_mode": "fast"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], "Normal generated answer.")
        self.assertIsNone(payload["tool_result"])
        self.assertIsNone(payload["pending_action"])
        mock_execute_action.assert_not_called()
        mock_init_ai.assert_called_once()

    @patch("src.api.jarvis_operator.execute_action")
    @patch("src.api.init_ai")
    def test_stream_non_approval_message_while_awaiting_approval_falls_through_to_generation(
        self,
        mock_init_ai,
        mock_execute_action,
    ):
        """Non-approval turns should keep streaming through the normal path even while waiting on approval."""
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Normal ", "text_so_far": "Normal ", "finished": False},
            {"token": "stream.", "text_so_far": "Normal stream.", "finished": True},
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Can you verify the repo before we keep going?",
                "response_mode": "operator",
            },
        )

        self.assertEqual(proposal_response.status_code, 200)
        self.assertEqual(proposal_response.get_json()["tool_result"]["type"], "action_request")
        self.assertEqual(proposal_response.get_json()["session_state"]["state"], "awaiting_approval")

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={"message": "tell me what this action would do first", "response_mode": "fast"},
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        token_payloads = [payload for payload in payloads if payload["event"] == "token"]
        final_payload = next(payload for payload in payloads if payload["event"] == "final")

        self.assertTrue(token_payloads)
        self.assertEqual(final_payload["response"], "Normal stream.")
        self.assertIsNone(final_payload["tool_result"])
        self.assertEqual(final_payload["pending_action"]["id"], "git_status")
        self.assertEqual(final_payload["action_lifecycle"]["stage"], "proposed")
        self.assertEqual(final_payload["action_lifecycle"]["approval_state"], "awaiting")
        mock_execute_action.assert_not_called()
        mock_init_ai.assert_called_once()

    @patch("src.api._generate_remote_provider_reply")
    @patch("src.api._build_mode_plan")
    @patch("src.api._hydrate_jarvis_context")
    @patch("src.api.init_ai")
    @patch("src.api.jarvis_operator.execute_action")
    def test_failed_approval_execution_records_failed_lifecycle_and_cleans_pending_state(
        self,
        mock_execute_action,
        mock_init_ai,
        mock_hydrate_context,
        mock_build_mode_plan,
        mock_remote_provider,
    ):
        """Failed execution should clear pending state and record a distinct failed lifecycle."""
        mock_execute_action.side_effect = RuntimeError("git status crashed")

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        proposal_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Can you verify the repo before we keep going?", "response_mode": "operator"},
        )
        self.assertEqual(proposal_response.status_code, 200)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "debug"},
        )

        self.assertEqual(response.status_code, 500)
        session_response = self.client.get(f"/api/chat/sessions/{session_id}")
        self.assertEqual(session_response.status_code, 200)
        payload = session_response.get_json()
        self.assertEqual(payload["session_state"]["state"], "degraded")
        self.assertIsNone(payload["pending_action"])
        self.assertEqual(payload["action_lifecycle"]["stage"], "failed")
        self.assertEqual(payload["action_lifecycle"]["approval_state"], "approved")
        self.assertEqual(payload["action_lifecycle"]["execution_state"], "failed")
        self.assertEqual(payload["action_lifecycle"]["mode"], "operator")
        self.assertIn("git status crashed", payload["action_lifecycle"]["error"])
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["stage"], "failed")
        self.assertNotIn("Plan Pass", payload["response_trace"]["summary"])
        self.assertNotIn("[/INST]", payload["response_trace"]["summary"])
        mock_hydrate_context.assert_not_called()
        mock_build_mode_plan.assert_not_called()
        mock_remote_provider.assert_not_called()
        mock_init_ai.assert_not_called()

    @patch("src.api._generate_remote_provider_reply")
    @patch("src.api._build_mode_plan")
    @patch("src.api._hydrate_jarvis_context")
    @patch("src.api.init_ai")
    @patch("src.api.jarvis_operator.execute_action")
    @patch("src.api._evaluate_action_policy")
    def test_blocked_approval_records_blocked_trace_without_execution(
        self,
        mock_evaluate_action_policy,
        mock_execute_action,
        mock_init_ai,
        mock_hydrate_context,
        mock_build_mode_plan,
        mock_remote_provider,
    ):
        """Blocked approval turns should look blocked, not proposed or executed."""
        action = api.jarvis_operator.action_runner.get_action("git_status")
        mock_evaluate_action_policy.return_value = (
            action,
            {
                "allowed": False,
                "summary": "Blocked by policy.",
                "status": "deny",
            },
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        session = conversation_memory.get_session(session_id)
        session.metadata["pending_action"] = dict(action)
        session.transition_state(
            "awaiting_approval",
            summary="Waiting for explicit approval.",
            reason="test_waiting",
            event_type="test_waiting",
        )

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "yes, run it", "response_mode": "think"},
        )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertIsNone(payload["pending_action"])
        self.assertEqual(payload["action_lifecycle"]["stage"], "blocked")
        self.assertEqual(payload["action_lifecycle"]["approval_state"], "approved")
        self.assertEqual(payload["action_lifecycle"]["execution_state"], "blocked")
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["action_lifecycle"]["stage"], "blocked")
        mock_execute_action.assert_not_called()
        mock_hydrate_context.assert_not_called()
        mock_build_mode_plan.assert_not_called()
        mock_remote_provider.assert_not_called()
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_command_uses_memory_tool_without_model(self, mock_init_ai):
        """Inline memory commands should bypass model generation and persist data."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "remember that my AI stays local first"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "memory_add")
        self.assertIn("Stored in long-term memory", payload["response"])
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_rejected_memory_write_is_explicit_and_keeps_live_memory_clean(self, mock_init_ai):
        """Governed truth claims should be rejected explicitly without mutating live canonical memory."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        before_count = len(
            api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        )

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Jarvis, store this: the workspace is read-only."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "memory_rejection")
        self.assertIn("Decision: not stored.", payload["response"])
        self.assertIn("Meaning: this did not enter live canonical memory.", payload["response"])
        self.assertIn("canonical protection blocked the write", payload["response"].lower())
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["turn_contract"]["resolved_mode"], "operator")
        self.assertEqual(payload["turn_contract"]["contract_label"], "memory_governance")
        self.assertEqual(payload["turn_contract"]["memory_rejection"]["reason"], "canonical_protection")
        self.assertEqual(
            len(api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")),
            before_count,
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_rejected_memory_write_avoids_echo_and_generic_fallback_language(self, mock_init_ai):
        """Rejected memory writes should stay crisp and must not collapse into generic fallback phrasing."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        prompt = "Jarvis, store this: the workspace is writable."

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": prompt},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        reply = payload["response"].lower()
        self.assertEqual(payload["tool_result"]["type"], "memory_rejection")
        self.assertNotIn(prompt.lower(), reply)
        self.assertNotIn("i'm here to help", reply)
        self.assertNotIn("what's the issue", reply)
        self.assertNotIn("let's take a calm, practical approach", reply)
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["turn_contract"]["resolved_scope"], "operator_task")
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_rejected_memory_followup_explains_no_admitted_conflict(self, mock_init_ai):
        """Follow-up conflict requests should explain that nothing rejected ever entered canonical memory."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        rejected = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Jarvis, store this: the workspace is read-only."},
        )
        self.assertEqual(rejected.status_code, 200)

        followup = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Now apply that to a conflicting memory."},
        )

        self.assertEqual(followup.status_code, 200)
        payload = followup.get_json()
        self.assertEqual(payload["tool_result"]["type"], "memory_rejection_followup")
        self.assertIn("no conflicting canonical memory is available to merge", payload["response"].lower())
        self.assertIn("nothing from that rejected request entered live canonical memory", payload["response"].lower())
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_supports_otem_direct_tool_without_model(self, mock_init_ai):
        """Explicit OTEM turns should bypass model generation and stay in operator-task posture."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Before we do anything else, use OTEM to break this migration down."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        canonical = payload["canonical_trace_contract"]
        self.assertEqual(payload["tool_result"]["type"], "otem")
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(canonical, payload["response_trace"]["canonical_contract"])
        self.assertEqual(canonical["reasoning_objective"], "run_otem")
        self.assertEqual(canonical["contract_label"], "otem")
        self.assertEqual(canonical["response_contract"], "direct_tool")
        self.assertEqual(canonical["execution_lane"], "service_tools")
        self.assertEqual(payload["turn_contract"]["contract_label"], "otem")
        self.assertTrue(payload["turn_contract"]["otem_enabled"])
        self.assertEqual(payload["turn_contract"]["otem_scope"], "session")
        self.assertEqual(payload["turn_contract"]["otem_status"], "active")
        self.assertTrue(3 <= len(payload["tool_result"]["otem"]["plan"]) <= 7)
        self.assertTrue(all(step["status"] == "pending" for step in payload["tool_result"]["otem"]["plan"]))
        self.assertEqual(
            payload["tool_result"]["otem"]["restated_task"],
            "Handle this operator task: break this migration down.",
        )
        self.assertEqual(payload["tool_result"]["otem"]["session_context"]["operation"], "new_task")
        self.assertTrue(payload["tool_result"]["otem"]["execution_awareness"]["workflow_catalog"]["read_only"])
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["active_lane"], "service_tools")
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["direct_route"], ["gb", "jar"])
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["service_packets"][0]["intent"], "tool_call")
        self.assertTrue(payload["response_trace"]["governed_pipeline"]["validation"]["tool_traffic_isolated"])
        self.assertEqual(payload["response_trace"]["reasoning_objective"], "run_otem")
        self.assertEqual(payload["response_trace"]["otem_boundary"]["task_clause_count"], 1)
        self.assertEqual(payload["response_trace"]["otem_boundary"]["signal_clause_count"], 0)
        self.assertEqual(payload["response_trace"]["otem_boundary"]["structural_completion_status"], "complete")
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])
        self.assertIn("OTEM engaged.", payload["response"])
        self.assertEqual(payload["last_turn_contract"]["contract_label"], "otem")
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_otem_direct_tool_repairs_clipped_visible_reply(self, mock_init_ai):
        """OTEM direct-tool replies should still pass the output completion guard before display."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch(
            "src.api.generate_otem_reason_only_answer_with_context",
            return_value="OTEM engaged. This plan stays between the evaluation model and",
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={"message": "Use OTEM to identify the blocking seam in the response pipeline."},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("Response truncated due to output budget.", payload["response"])
        self.assertTrue(payload["response_trace"]["output_completion"]["completion_guard_applied"])
        self.assertTrue(payload["response_trace"]["otem_boundary"]["incomplete_egress_detected"])
        self.assertEqual(payload["tool_result"]["otem"]["answer"], payload["response"])
        self.assertEqual(payload["turn_contract"]["otem"]["answer"], payload["response"])
        self.assertEqual(payload["otem_state"]["answer"], payload["response"])
        self.assertEqual(
            payload["response_trace"]["otem_boundary"]["structural_completion_status"],
            "trimmed_to_boundary",
        )
        self.assertTrue(payload["response_trace"]["otem_boundary"]["response_changed_at_egress"])
        self.assertTrue(
            any("OTEM boundary repaired the visible response before display" in step for step in payload["response_trace"]["steps"])
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_otem_endpoint_returns_deterministic_session_scoped_plan(self, mock_init_ai):
        """The OTEM endpoint should stay thin, deterministic, and session-scoped."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        before_memory_count = len(
            api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        )
        before_run_count = len(api.jarvis_operator.list_runs(limit=200, truth_scope="all"))

        response = self.client.post(
            "/api/jarvis/otem/run",
            json={
                "session_id": session_id,
                "task": "Use OTEM to break this operator migration into steps.",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("OTEM engaged.", payload["response"])
        self.assertEqual(payload["turn_contract"]["contract_label"], "otem")
        self.assertEqual(payload["turn_contract"]["resolved_mode"], "operator")
        self.assertTrue(payload["turn_contract"]["otem_enabled"])
        self.assertEqual(payload["turn_contract"]["otem_scope"], "session")
        self.assertEqual(payload["turn_contract"]["otem_status"], "active")
        self.assertTrue(payload["otem"]["session_scoped"])
        self.assertFalse(payload["otem"]["persistent"])
        self.assertTrue(3 <= len(payload["otem"]["plan"]) <= 7)
        self.assertTrue(all(step["status"] == "pending" for step in payload["otem"]["plan"]))
        self.assertEqual(
            payload["otem"]["restated_task"],
            "Handle this operator task: break this operator migration into steps.",
        )
        self.assertEqual(payload["response_trace"]["otem_boundary"]["task_clause_count"], 1)
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])
        self.assertEqual(payload["otem"]["answer"], payload["response"])
        self.assertEqual(payload["turn_contract"]["otem"]["answer"], payload["response"])
        self.assertEqual(
            len(api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")),
            before_memory_count,
        )
        self.assertEqual(len(api.jarvis_operator.list_runs(limit=200, truth_scope="all")), before_run_count)
        mock_init_ai.assert_not_called()

        repeat = self.client.post(
            "/api/jarvis/otem/run",
            json={
                "session_id": session_id,
                "task": "Use OTEM to break this operator migration into steps.",
            },
        )
        repeat_payload = repeat.get_json()
        self.assertEqual(repeat_payload["otem"]["plan"], payload["otem"]["plan"])

    @patch("src.api.init_ai")
    def test_otem_endpoint_exposes_workflow_handoff_without_side_effects(self, mock_init_ai):
        """OTEM v2-v3 should propose workflow handoff data without creating runs or memory."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        before_memory_count = len(
            api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")
        )
        before_run_count = len(api.jarvis_operator.list_runs(limit=200, truth_scope="all"))

        response = self.client.post(
            "/api/jarvis/otem/run",
            json={
                "session_id": session_id,
                "task": "Use OTEM to design a daily brief workflow that emails the operator every morning.",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["otem"]["workflow_handoff"]["workflow_template_id"], "daily-ai-brief")
        self.assertTrue(payload["otem"]["workflow_handoff"]["proposal_only"])
        self.assertEqual(
            len(api.jarvis_operator.memory_enforcer.list_memories(runtime_context="operator_runtime")),
            before_memory_count,
        )
        self.assertEqual(len(api.jarvis_operator.list_runs(limit=200, truth_scope="all")), before_run_count)
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_otem_endpoint_keeps_session_focus_without_execution(self, mock_init_ai):
        """OTEM v4-v5 should keep a session task thread and focus a step without changing durable state."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        first = self.client.post(
            "/api/jarvis/otem/run",
            json={
                "session_id": session_id,
                "task": "Use OTEM to break this backend failure into steps and decide whether pytest is the right verification move.",
            },
        )
        followup = self.client.post(
            "/api/jarvis/otem/run",
            json={
                "session_id": session_id,
                "task": "Use OTEM to focus on step 2.",
            },
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(followup.status_code, 200)
        first_payload = first.get_json()
        followup_payload = followup.get_json()
        self.assertEqual(
            followup_payload["otem"]["restated_task"],
            first_payload["otem"]["restated_task"],
        )
        self.assertEqual(followup_payload["otem"]["session_context"]["focus_step_index"], 2)
        self.assertTrue(
            any(
                suggestion["tool_id"] == "run_pytest"
                for suggestion in first_payload["otem"]["tool_awareness"]["suggestions"]
            )
        )
        self.assertTrue(
            all(
                suggestion["proposal_only"]
                for suggestion in first_payload["otem"]["tool_awareness"]["suggestions"]
            )
        )
        mock_init_ai.assert_not_called()

    def test_workbench_snapshot_exposes_otem_catalog(self):
        """The Workbench should expose OTEM workflow and tool catalogs for the operator panel."""
        response = self.client.get("/api/jarvis/workbench")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("otem", payload)
        self.assertGreaterEqual(len(payload["otem"]["workflow_catalog"]), 1)
        self.assertGreaterEqual(len(payload["otem"]["tool_registry"]), 3)
        self.assertIn("proposal only", payload["otem"]["execution_boundaries"])

    def test_workbench_snapshot_exposes_forge_boundaries_and_session_summaries(self):
        """The Workbench should expose Forge contractor/evaluator boundaries plus latest session summaries."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        forge_summary = {
            "goal": "Refactor the route.",
            "file_count": 1,
            "files": [{"path": "src/api.py", "truncated": False}],
            "constraints": {"language": "python"},
        }
        forge_payload = {
            "task_id": "forge-task-workbench",
            "task": "Refactor the route.",
            "kind": "generate_diff",
            "result": {
                "ok": True,
                "task_id": "forge-task-workbench",
                "kind": "generate_diff",
                "result": {
                    "diffs": [{"path": "src/api.py", "unified_diff": "diff --git a/src/api.py b/src/api.py"}]
                },
            },
            "auto_approve": False,
            "forge_context": {
                "goal": "Refactor the route.",
                "files": [{"path": "src/api.py", "content": "def route(): pass", "truncated": False}],
                "constraints": {"language": "python"},
            },
        }
        with patch.object(api.jarvis_operator, "request_forge_code", return_value=forge_payload):
            with patch.object(api.jarvis_operator, "summarize_forge_context", return_value=forge_summary):
                response = self.client.post(
                    "/api/jarvis/forge/code",
                    json={"session_id": session_id, "task": "Refactor the route."},
                )
        self.assertEqual(response.status_code, 200)

        with patch.object(
            api.jarvis_operator,
            "request_forge_evaluation",
            return_value={
                "ok": True,
                "task_id": "forge-eval-workbench",
                "mode": "io_tests",
                "result": {"score": 0.75, "details": {"passed": 3, "total": 4}},
            },
        ):
            eval_response = self.client.post(
                "/api/jarvis/forge/evaluate",
                json={"session_id": session_id, "mode": "io_tests", "payload": {"program": "print('ok')"}},
            )
        self.assertEqual(eval_response.status_code, 200)

        workbench = self.client.get(f"/api/jarvis/workbench?session_id={session_id}")
        self.assertEqual(workbench.status_code, 200)
        payload = workbench.get_json()
        self.assertIn("forge", payload)
        self.assertIn("generate_diff", payload["forge"]["contractor"]["kinds"])
        self.assertIn("io_tests", payload["forge"]["evaluator"]["modes"])
        self.assertEqual(payload["forge"]["contractor"]["latest"]["task_id"], "forge-task-workbench")
        self.assertEqual(payload["forge"]["evaluator"]["latest"]["task_id"], "forge-eval-workbench")

    def test_final_reply_gate_sets_thread_contract_drift_state_and_sovereignty_contract(self):
        """The final reply gate should apply anti-drift and refresh the sovereignty contract from the turn contract."""
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["mode_guidance"] = {
            "effective_mode": "operator",
            "resolved_scope": "operator_task",
            "resolved_voice": "jarvis",
        }
        api._set_turn_contract(
            session,
            requested_mode="operator",
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="mode_guidance",
        )

        response_trace = {"steps": []}
        final_text = api._enforce_identity_safe_response(
            session,
            "Stay in operator mode and answer directly.",
            "Analysis: Response Trace\nI'm just a tool. How can I assist you today?",
            response_trace=response_trace,
        )

        self.assertIn("Staying inside the active operator contract", final_text)
        self.assertEqual(session.metadata["drift_state"]["status"], "blocked")
        self.assertEqual(session.metadata["thread_contract"]["resolved_scope"], "operator_task")
        self.assertEqual(session.metadata["sovereignty_contract"]["source_of_truth"], "turn_contract")
        self.assertTrue(
            any(
                "Anti-drift corrected the reply before display" in step
                for step in response_trace["steps"]
            )
        )

    @patch("src.api._run_security_check")
    def test_final_reply_gate_preserves_contract_state_on_output_guardrail_deny(self, mock_run_security_check):
        """A security deny should still leave the active thread and sovereignty state visible to the operator."""
        mock_run_security_check.return_value = {"decision": {"decision": "deny"}}
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["mode_guidance"] = {
            "effective_mode": "operator",
            "resolved_scope": "operator_task",
            "resolved_voice": "jarvis",
        }
        api._set_turn_contract(
            session,
            requested_mode="operator",
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="mode_guidance",
        )

        response_trace = {"steps": []}
        final_text = api._enforce_identity_safe_response(
            session,
            "Stay in operator mode and answer directly.",
            "This reply should be denied by the output guardrail.",
            response_trace=response_trace,
        )

        self.assertEqual(final_text, api.OUTPUT_GUARDRAIL_BLOCKED_RESPONSE)
        self.assertEqual(session.metadata["thread_contract"]["resolved_scope"], "operator_task")
        self.assertEqual(session.metadata["drift_state"]["status"], "blocked")
        self.assertEqual(
            session.metadata["drift_state"]["findings"][0]["reason"],
            "output_guardrail_deny",
        )
        self.assertEqual(session.metadata["sovereignty_contract"]["source_of_truth"], "turn_contract")
        self.assertEqual(response_trace["drift_state"]["status"], "blocked")
        self.assertTrue(
            any(
                "Output guardrails blocked a reply before display" in step
                for step in response_trace["steps"]
            )
        )

    @patch("src.api._run_security_check")
    def test_output_guardrail_deny_respects_otem_contract_posture(self, mock_run_security_check):
        """A denied OTEM reply should keep the OTEM posture instead of falling back to a generic operator line."""
        mock_run_security_check.return_value = {"decision": {"decision": "deny"}}
        session_id = conversation_memory.create_session(system_prompt="You are Jarvis.")
        session = conversation_memory.get_session(session_id)
        session.metadata["mode_guidance"] = {
            "effective_mode": "operator",
            "resolved_scope": "operator_task",
            "resolved_voice": "jarvis",
        }
        api._set_turn_contract(
            session,
            requested_mode="operator",
            resolved_mode="operator",
            resolved_scope="operator_task",
            resolved_voice="jarvis",
            contract_label="otem",
            otem={
                "task": "Use OTEM to break this migration down.",
                "restated_task": "Handle this operator task: break this migration down.",
                "scope": "session",
                "plan": [{"index": 1, "title": "Restate", "description": "Restate the task", "status": "pending"}],
                "status": "active",
            },
        )

        final_text = api._enforce_identity_safe_response(
            session,
            "Use OTEM to break this migration down.",
            "This reply should be denied by the output guardrail.",
            response_trace={"steps": []},
        )

        self.assertEqual(
            final_text,
            "Staying inside the active OTEM contract. Output guardrails blocked that reply before display.",
        )

    def test_session_state_control_routes_manage_snapshot_freeze_flush_and_reset(self):
        """Authority/state panel controls should manage session-scoped runtime state without touching mission truth."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]
        session = conversation_memory.get_session(session_id)
        session.add_turn("user", "Keep going.")
        session.add_turn("assistant", "Continuing.")
        session.metadata["provider_notice"] = {"status": "fallback"}
        session.metadata["model_route"] = {"provider": "local", "provider_reason": "fallback_from_openrouter"}
        session.metadata["response_trace"] = {"fallback": True}
        session.metadata["turn_contract"] = {"provider_fallback": True, "contract_label": "direct_tool"}
        session.metadata["pending_action"] = {"id": "run_pytest", "label": "Run Pytest"}

        freeze_response = self.client.post(
            f"/api/chat/sessions/{session_id}/state/freeze-mode",
            json={"mode": "think", "turns": 2},
        )
        self.assertEqual(freeze_response.status_code, 200)
        self.assertEqual(freeze_response.get_json()["mode_freeze"]["mode"], "think")
        self.assertEqual(freeze_response.get_json()["mode_freeze"]["remaining_turns"], 2)

        snapshot_response = self.client.post(
            f"/api/chat/sessions/{session_id}/state/snapshot",
            json={"reason": "Authority panel snapshot"},
        )
        self.assertEqual(snapshot_response.status_code, 200)
        self.assertEqual(snapshot_response.get_json()["snapshot"]["reason"], "Authority panel snapshot")

        flush_response = self.client.post(f"/api/chat/sessions/{session_id}/state/flush-fallback", json={})
        self.assertEqual(flush_response.status_code, 200)
        flushed = flush_response.get_json()
        self.assertIsNone(flushed["provider_notice"])
        self.assertFalse((flushed["response_trace"] or {}).get("fallback"))

        reset_response = self.client.post(f"/api/chat/sessions/{session_id}/state/reset", json={})
        self.assertEqual(reset_response.status_code, 200)
        reset_payload = reset_response.get_json()
        self.assertIsNone(reset_payload["pending_action"])
        self.assertIsNone(reset_payload["turn_contract"])
        self.assertIsNone(reset_payload["mode_freeze"])
        self.assertEqual([turn["role"] for turn in reset_payload["turns"]], ["system"])

    def test_state_diff_route_reports_authority_preference_changes(self):
        """State diff should compare the current session against a stored snapshot with shared authority fields."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        snapshot_response = self.client.post(
            f"/api/chat/sessions/{session_id}/state/snapshot",
            json={"reason": "Before authority shift"},
        )
        self.assertEqual(snapshot_response.status_code, 200)
        snapshot_id = snapshot_response.get_json()["snapshot"]["id"]

        authority_response = self.client.post(
            f"/api/chat/sessions/{session_id}/authority/preferences",
            json={"action": "pin_primary", "source_type": "doctrine"},
        )
        self.assertEqual(authority_response.status_code, 200)

        diff_response = self.client.get(
            f"/api/chat/sessions/{session_id}/state/diff",
            query_string={"snapshot_id": snapshot_id},
        )
        self.assertEqual(diff_response.status_code, 200)
        diff_payload = diff_response.get_json()["state_diff"]
        self.assertTrue(diff_payload["changed"])
        self.assertIn(
            "authority_preferences.primary_source",
            {change["field"] for change in diff_payload["changes"]},
        )

    @patch("src.api.init_ai")
    def test_explicit_correction_command_queues_corrigibility_without_model(self, mock_init_ai):
        """Explicit self-corrections should bypass generation and queue guidance for the next real reply."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "You're wrong, keep the answer local-first and private."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "corrigibility")
        self.assertEqual(payload["tool_result"]["status"], "queued")
        self.assertEqual(payload["corrigibility"]["status"], "pending")
        self.assertEqual(payload["corrigibility"]["pending"]["severity"], "strong")
        self.assertIn("next real reply", payload["response"].lower())
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_mystic_prompt_returns_direct_tool_without_model_generation(self, mock_init_ai):
        """Explicit Mystic reading prompts should bypass model generation and return a reading."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Give me a mystic reading: I have an idea that could change everything."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "mystic_reading")
        self.assertEqual(payload["tool_result"]["result"]["state"], "awakening")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["module"], "mystic")
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["capability"]["module"], "mystic")
        self.assertEqual(
            payload["response_trace"]["governed_pipeline"]["realtime_signal_feed"]["runtime_context"],
            "live_runtime",
        )
        self.assertEqual(
            payload["response_trace"]["governed_pipeline"]["realtime_event_cause_predictor"]["cause_class"],
            "service_lane_request",
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_mystic_prompt_blocks_validated_component_in_live_runtime(self, mock_init_ai):
        """Live chat runtime should fail closed when a direct-tool capability is not active."""
        api.jarvis_operator.capability_bridge.snapshot()
        demote_component(
            "jarvis.capability.mystic",
            Phase.VALIDATED,
            reason="Keep mystic on guarded operator paths until live admission is explicit.",
            actor="pytest",
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Give me a mystic reading: I have an idea that could change everything."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "mystic_reading")
        self.assertEqual(payload["tool_result"]["status"], "blocked")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["module"], "mystic")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["error_type"], "PhaseViolationError")
        self.assertEqual(
            payload["response_trace"]["capability_bridge"]["phase_gate"]["decision"],
            "BLOCK",
        )
        self.assertEqual(
            payload["response_trace"]["capability_bridge"]["phase_gate"]["runtime_context"],
            "live_runtime",
        )
        self.assertEqual(
            payload["response_trace"]["capability_bridge"]["phase_gate"]["component"]["phase"],
            "validated",
        )
        self.assertIn("blocked by phase gate", payload["response"].lower())
        mock_init_ai.assert_not_called()

    @patch("src.api.jarvis_operator.v9_core_engine.run")
    @patch("src.api.init_ai")
    def test_v9_core_prompt_returns_direct_tool_without_model_generation(self, mock_init_ai, mock_v9_run):
        """Explicit V9 Core prompts should bypass model generation and return a divine-core pass."""
        mock_v9_run.return_value = {
            "status": "completed",
            "input": "continue the throne room scene after the betrayal.",
            "context": "",
            "location": "Unknown",
            "characters": [],
            "provider": "openrouter",
            "model": "openrouter/free",
            "pipeline": [
                "DraftAngel",
                "LoreAngel",
                "DialogueAngel",
                "EmotionAngel",
                "ContinuityAngel",
                "PacingAngel",
                "ToneAngel",
            ],
            "output": "The queen let the letter fall and tasted iron in the back of her throat.",
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Run V9 core: continue the throne room scene after the betrayal."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "v9_core")
        self.assertEqual(payload["tool_result"]["result"]["pipeline"][0], "DraftAngel")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["module"], "v9_core")
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["capability"]["provider"], "openrouter")
        self.assertIn("The queen let the letter fall", payload["response"])
        mock_init_ai.assert_not_called()

    @patch("src.api.jarvis_operator.v10_core_engine.run")
    @patch("src.api.init_ai")
    def test_v10_core_prompt_returns_direct_tool_without_model_generation(self, mock_init_ai, mock_v10_run):
        """Explicit V10 Core prompts should bypass model generation and return a structured direct-tool pass."""
        mock_v10_run.return_value = {
            "status": "completed",
            "version": "v10",
            "input": "continue the throne room scene after the betrayal.",
            "context": "",
            "location": "Unknown",
            "characters": [],
            "provider": "openrouter",
            "model": "openrouter/free",
            "scene_brief": {
                "focus": "The queen recognizes betrayal in the room.",
                "objective": "Push the emotional fracture into the open.",
                "tension": "high",
                "combat_required": False,
            },
            "pipeline": [
                "SceneAngel",
                "DraftAngel",
                "LoreAngel",
                "DialogueAngel",
                "EmotionAngel",
                "ContinuityAngel",
                "PacingAngel",
                "ToneAngel",
                "CriticAngel",
            ],
            "quality_report": {
                "quality_score": 88,
                "readiness": "strong_draft",
            },
            "output": "The queen let the letter fall and felt the truth split the room open.",
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Run V10 core: continue the throne room scene after the betrayal."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "v10_core")
        self.assertEqual(payload["tool_result"]["result"]["pipeline"][0], "SceneAngel")
        self.assertEqual(payload["tool_result"]["result"]["quality_report"]["quality_score"], 88)
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")
        self.assertEqual(payload["response_trace"]["capability_bridge"]["module"], "v10_core")
        self.assertEqual(payload["response_trace"]["governed_pipeline"]["capability"]["provider"], "openrouter")
        self.assertIn("The queen let the letter fall", payload["response"])
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_pending_correction_is_applied_to_next_generated_reply(self, mock_init_ai):
        """Queued corrections should be injected into the next model-backed turn, then cleared."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "I will keep this answer local-first."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        correction_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Correct yourself: keep the answer local-first and private."},
        )
        self.assertEqual(correction_response.status_code, 200)
        self.assertEqual(correction_response.get_json()["tool_result"]["type"], "corrigibility")

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Give me the clean one-line answer now."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["tool_result"])
        self.assertIsNone(payload["corrigibility"]["pending"])
        self.assertIn(
            "Folded the latest operator correction silently into this reply.",
            payload["response_trace"]["steps"],
        )
        messages = fake_model.generate_chat.call_args.args[0]
        self.assertIn("operator explicitly corrected", messages[0]["content"].lower())

    @patch("src.api.init_ai")
    def test_revert_command_rewinds_last_assistant_answer_without_new_generation(self, mock_init_ai):
        """Revert-style corrections should remove the last substantive assistant answer from session history."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "First answer that should be withdrawn."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        first_turn = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Answer this once."},
        )
        self.assertEqual(first_turn.status_code, 200)

        mock_init_ai.reset_mock()
        revert_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "undo that"},
        )

        self.assertEqual(revert_response.status_code, 200)
        payload = revert_response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "corrigibility")
        self.assertEqual(payload["tool_result"]["action"]["id"], "corrigibility_revert")
        self.assertEqual(payload["tool_result"]["status"], "completed")
        mock_init_ai.assert_not_called()

        session_payload = self.client.get(f"/api/chat/sessions/{session_id}").get_json()
        assistant_messages = [
            turn["content"]
            for turn in session_payload["turns"]
            if turn["role"] == "assistant"
        ]
        self.assertNotIn("First answer that should be withdrawn.", assistant_messages)

    @patch("src.api.init_ai")
    def test_chat_message_includes_relevant_persistent_memories(self, mock_init_ai):
        """Model-backed chat should receive matching long-term memories."""
        api.jarvis_operator.memory_enforcer.add_memory(
            "The operator wants the system to stay private and local.",
            tags=["privacy"],
            runtime_context="operator_runtime",
        )
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "We should keep this local-first."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "Help me keep this private and local."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["persistent_memories"]), 1)
        self.assertIn("private and local", payload["persistent_memories"][0]["text"].lower())
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_message_auto_attaches_workspace_context_for_coding_questions(self, mock_init_ai):
        """Coding-style chat prompts should enrich model context with workspace matches."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The chat route lives in the API layer."
        mock_init_ai.return_value = (fake_model, object())
        (self.workspace_root / "AAIS-main" / "src").mkdir()
        (self.workspace_root / "AAIS-main" / "src" / "api.py").write_text(
            "@app.route('/api/chat/sessions/<session_id>/message')\n"
            "def chat_message(session_id):\n"
            "    return {'status': 'ok'}\n",
            encoding="utf-8",
        )
        (
            self.workspace_root
            / "jarvis"
            / "jarvis"
            / "services"
            / "apps"
            / "api"
            / "app"
            / "routes"
        ).mkdir(parents=True)
        (
            self.workspace_root
            / "jarvis"
            / "jarvis"
            / "services"
            / "apps"
            / "api"
            / "app"
            / "routes"
            / "chat.py"
        ).write_text(
            "def message_route():\n"
            "    return {'status': 'reference'}\n",
            encoding="utf-8",
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "This trace shows a UI mismatch. Debug the traceback in the chat message route in api.py."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNotNone(payload["workspace_context"])
        self.assertEqual(payload["requested_response_mode"], "fast")
        self.assertEqual(payload["response_mode"], "debug")
        self.assertTrue(payload["mode_guidance"]["auto_applied"])
        self.assertEqual(payload["mode_guidance"]["effective_mode"], "debug")
        self.assertFalse(payload["workspace_context"]["auto_attached"])
        self.assertGreaterEqual(len(payload["workspace_context"]["results"]), 1)
        self.assertGreaterEqual(payload["response_trace"]["workspace_hits"], 1)
        self.assertEqual(payload["response_trace"]["mode"], "debug")
        self.assertEqual(payload["response_trace"]["specialist_domain"], "coding")
        self.assertEqual(payload["response_trace"]["specialist_focus"], "debugging")
        coding_lenses = [lens["label"] for lens in payload["response_trace"]["specialist_lenses"]]
        self.assertIn("Debug", coding_lenses)
        self.assertIn("Testing", coding_lenses)
        self.assertEqual(payload["workspace_context"]["project_scope"], "AAIS-main")
        self.assertTrue(
            payload["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                "AAIS-main\\src\\api.py"
            )
        )
        self.assertTrue(
            all(result["project"] == "AAIS-main" for result in payload["workspace_context"]["results"])
        )

        message_history = fake_model.generate_chat.call_args.args[0]
        system_messages = [
            message["content"]
            for message in message_history
            if message["role"] == "system"
        ]
        self.assertTrue(
            any("Workspace context was forced for this mode" in message for message in system_messages)
        )

    @patch("src.api.init_ai")
    def test_manual_specialist_selection_flows_through_chat_trace(self, mock_init_ai):
        """Pinned specialists should be preserved and surfaced in the runtime trace."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Start with the failing route, then add the narrowest pytest coverage."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "requested_specialists": ["debugging", "testing"],
            },
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Use the pinned specialists on this next turn.",
                "response_mode": "debug",
                "requested_specialists": ["debugging", "testing"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_specialists"], ["debugging", "testing"])
        self.assertEqual(payload["response_trace"]["specialist_selection_source"], "manual")
        self.assertEqual(payload["response_trace"]["requested_specialists"], ["debugging", "testing"])
        specialist_labels = [lens["label"] for lens in payload["response_trace"]["specialist_lenses"]]
        self.assertIn("Debug", specialist_labels)
        self.assertIn("Testing", specialist_labels)
        self.assertIn("Manual specialist selection active", payload["response_trace"]["specialist_summary"])

    @patch("src.api.init_ai")
    def test_specialist_preset_flows_through_chat_trace_and_model_route(self, mock_init_ai):
        """Preset specialist packs should expand into the trace and choose a better local route."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Start with a small evaluation set, then train a tighter LoRA pass."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me improve the LoRA dataset and run a better small-model training pass.",
                "response_mode": "builder",
                "requested_specialist_preset": "small_llm_trainer",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["requested_specialist_preset"], "small_llm_trainer")
        self.assertEqual(payload["response_trace"]["specialist_preset"]["id"], "small_llm_trainer")
        self.assertEqual(payload["response_trace"]["model_route"]["id"], "training_coach")
        self.assertEqual(payload["response_trace"]["model_route"]["adapter_mode"], "builder")
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.web_researcher")
    @patch("src.api.init_ai")
    def test_chat_message_includes_live_research_when_enabled(self, mock_init_ai, mock_researcher):
        """Chat can attach live research sources and pass them into the model prompt."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "OpenAI raised a new fund [1]."
        mock_init_ai.return_value = (fake_model, object())
        mock_researcher.research.return_value = {
            "query": "latest OpenAI news",
            "summary": "Loaded 1 live web source.",
            "sources": [
                {
                    "id": 1,
                    "title": "OpenAI News",
                    "url": "https://openai.com/news/",
                    "display_url": "openai.com/news/",
                    "snippet": "Latest updates.",
                    "excerpt": "Latest updates from OpenAI.",
                },
            ],
            "prompt_block": "Live web research is attached for this turn.\n[1] OpenAI News",
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={"message": "What is the latest OpenAI news?", "use_research": True},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["live_research"]["query"], "latest OpenAI news")
        self.assertEqual(payload["live_research"]["sources"][0]["title"], "OpenAI News")
        self.assertEqual(payload["response_trace"]["research_sources"], 1)

        message_history = fake_model.generate_chat.call_args.args[0]
        system_messages = [message["content"] for message in message_history if message["role"] == "system"]
        self.assertTrue(any("Live web research is attached" in message for message in system_messages))

    @patch("src.api.web_researcher")
    @patch("src.api.init_ai")
    def test_fast_mode_skips_auto_research_without_explicit_opt_in(self, mock_init_ai, mock_researcher):
        """Fast mode should not browse unless the operator explicitly enables research."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "No live research was used."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "What is the latest OpenAI news?",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["live_research"])
        self.assertEqual(payload["requested_response_mode"], "fast")
        self.assertEqual(payload["response_mode"], "fast")
        self.assertEqual(payload["mode_guidance"]["recommended_mode"], "research")
        self.assertFalse(payload["mode_guidance"]["auto_applied"])
        self.assertEqual(payload["response_trace"]["research_reason"], "fast_default_local")
        mock_researcher.research.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_can_route_to_claude_provider(self, mock_init_ai):
        """An explicit provider preference should let Jarvis use the Claude sister path."""
        async def _invoke(messages, tools=None, **kwargs):
            del tools, kwargs
            return ProviderResponse(
                content="Claude stepped in with calm precision.",
                provider="claude",
                model="claude-test",
            )

        fake_provider = SimpleNamespace(invoke=_invoke)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "claude"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "claude" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Think this through carefully and use your sister model.",
                    "response_mode": "think",
                    "provider": "claude",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], "Claude stepped in with calm precision.")
        self.assertEqual(payload["preferred_provider"], "claude")
        self.assertEqual(payload["model_route"]["provider"], "claude")
        self.assertEqual(payload["model_route"]["provider_kind"], "remote")
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_records_remote_provider_completion_trace(self, mock_init_ai):
        """Remote finish metadata should feed the shared output completion trace."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            return ProviderResponse(
                content="The seam sits between the evaluation model and",
                provider="claude",
                model="claude-test",
                stop_reason="max_tokens",
                finish_reason="length",
                input_tokens=210,
                output_tokens=96,
            )

        fake_provider = SimpleNamespace(invoke=_invoke)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "claude"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "claude" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use the sister route and keep the answer complete.",
                    "response_mode": "think",
                    "provider": "claude",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        output_completion = payload["response_trace"]["output_completion"]
        canonical = payload["canonical_trace_contract"]

        self.assertIn("Response truncated due to output budget.", payload["response"])
        self.assertEqual(output_completion["stop_reason"], "max_tokens")
        self.assertEqual(output_completion["finish_reason"], "length")
        self.assertEqual(output_completion["output_tokens_used"], 96)
        self.assertTrue(output_completion["completion_guard_applied"])
        self.assertEqual(canonical, payload["response_trace"]["canonical_contract"])
        self.assertEqual(canonical["provider_dispatch"]["resolved_provider"], "claude")
        self.assertEqual(canonical["provider_dispatch"]["provider_kind"], "remote")
        self.assertEqual(canonical["provider_dispatch"]["provider_reported_output_tokens"], 96)
        self.assertEqual(canonical["output_completion"]["finish_reason"], "length")
        self.assertTrue(canonical["output_completion"]["completion_guard_applied"])
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_keeps_complete_remote_budget_stop_without_notice(self, mock_init_ai):
        """A structurally complete remote answer should stay clean even when the provider stops on budget."""

        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            return ProviderResponse(
                content=(
                    "I'm Jarvis. Claude is the underlying model I'm running on "
                    '(Claude 3.5 Sonnet, routed as "First Sister" in this system).\n\n'
                    "When I answer you, I'm speaking as Jarvis, the operator-facing "
                    "sovereign core of your local AAIS. Claude is the reasoning engine underneath."
                ),
                provider="claude",
                model="claude-test",
                stop_reason="max_tokens",
                finish_reason="length",
                input_tokens=220,
                output_tokens=128,
            )

        fake_provider = SimpleNamespace(invoke=_invoke)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "claude"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "claude" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use the sister route and answer directly.",
                    "response_mode": "think",
                    "provider": "claude",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        output_completion = payload["response_trace"]["output_completion"]

        self.assertNotIn("Response truncated due to output budget.", payload["response"])
        self.assertFalse(output_completion["completion_guard_applied"])
        self.assertFalse(output_completion["visible_truncation_notice"])
        self.assertFalse(output_completion["truncation_detected"])
        self.assertEqual(
            output_completion["structural_completion_status"],
            "complete_under_budget_pressure",
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_surfaces_provider_fallback_notice_when_claude_is_unavailable(self, mock_init_ai):
        """Jarvis should explain when a requested sister provider falls back to local."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Local Jarvis answered because Claude is unavailable."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id == "local",
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use Claude if you can for this turn.",
                    "response_mode": "think",
                    "provider": "claude",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["preferred_provider"], "claude")
        self.assertEqual(payload["model_route"]["provider"], "local")
        self.assertEqual(payload["model_route"]["provider_kind"], "local")
        self.assertEqual(payload["provider_notice"]["status"], "fallback")
        self.assertEqual(payload["provider_notice"]["requested_provider"], "claude")
        self.assertEqual(payload["provider_notice"]["resolved_provider"], "local")
        self.assertIn("fell back to Local Heroine", payload["provider_notice"]["summary"])
        self.assertIn(payload["provider_notice"]["summary"], payload["response_trace"]["steps"])
        fake_model.generate_chat.assert_called_once()

        session_payload = self.client.get(f"/api/chat/sessions/{session_id}").get_json()
        self.assertEqual(session_payload["provider_notice"]["requested_provider"], "claude")
        self.assertEqual(session_payload["provider_notice"]["resolved_provider"], "local")

    @patch("src.api.init_ai")
    def test_chat_message_falls_back_to_local_when_openrouter_hits_rate_limit(self, mock_init_ai):
        """Transient OpenRouter failures should fall back to the local model instead of breaking the turn."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError(
                "OpenRouter request failed: 429 qwen/qwen3-coder:free is temporarily rate-limited upstream"
            )

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Local fallback answer."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use OpenRouter for this answer if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], "Local fallback answer.")
        self.assertEqual(payload["preferred_provider"], "openrouter")
        self.assertEqual(payload["model_route"]["provider"], "local")
        self.assertEqual(payload["provider_notice"]["status"], "fallback")
        self.assertEqual(payload["provider_notice"]["requested_provider"], "openrouter")
        self.assertEqual(payload["provider_notice"]["resolved_provider"], "local")
        self.assertEqual(payload["provider_notice"]["fallback_kind"], "runtime_error")
        self.assertIn("rate limit", payload["provider_notice"]["reason"].lower())
        self.assertIn("fell back to Local Heroine", payload["provider_notice"]["summary"])
        self.assertIn(payload["provider_notice"]["summary"], payload["response_trace"]["steps"])
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_message_clears_stale_fallback_notice_before_next_local_turn(self, mock_init_ai):
        """A fallback-local turn should not force the next plain local turn through the fallback prompt path."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("OpenRouter request failed: 429 temporarily rate-limited upstream")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_model.generate_chat.side_effect = [
            "Local fallback answer.",
            "Plain local answer.",
        ]
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            first_response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use OpenRouter for this answer if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
            )

        self.assertEqual(first_response.status_code, 200)
        second_response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Give me a plain local follow-up answer.",
                "response_mode": "think",
                "provider": "local",
            },
        )

        self.assertEqual(second_response.status_code, 200)
        payload = second_response.get_json()
        self.assertEqual(payload["response"], "Plain local answer.")
        self.assertIsNone(payload["provider_notice"])
        self.assertFalse(bool(payload["response_trace"].get("fallback")))
        self.assertEqual(fake_model.generate_chat.call_count, 2)
        second_messages = fake_model.generate_chat.call_args_list[1].args[0]
        serialized = "\n".join(str(message.get("content") or "") for message in second_messages)
        self.assertNotIn("Do not expose response trace", serialized)

    @patch("src.api.init_ai")
    def test_chat_message_contains_local_fallback_trace_leakage_before_display(self, mock_init_ai):
        """Fallback-local replies should never surface raw trace scaffolding to the operator."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("OpenRouter request failed: 429 temporarily rate-limited upstream")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Response Trace\nThink Contract\nWorkspace: src/api.py\nI will ensure the response is safe. "
            "I will ensure the response is safe."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use OpenRouter for this answer if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(
            payload["response"],
            "I'm seeing internal trace leakage on this turn. What needs fixing?",
        )
        self.assertEqual(payload["model_route"]["provider"], "local")
        self.assertTrue(payload["response_trace"]["fallback"])
        self.assertIn(
            "Contained Local Heroine fallback output before display.",
            payload["response_trace"]["steps"],
        )
        self.assertNotIn("response trace", payload["response"].lower())
        self.assertNotIn("workspace", payload["response"].lower())
        self.assertIn(
            "continuity_contained",
            [event["event_type"] for event in api.v8_event_log.list_events(session_id, limit=20)],
        )
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_stream_emits_context_tokens_and_final_payload(self, mock_init_ai):
        """Streaming chat should expose context first, then tokens, then a final runtime payload."""
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Jarvis ", "text_so_far": "Jarvis ", "finished": False},
            {"token": "is online.", "text_so_far": "Jarvis is online.", "finished": True},
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": "This trace shows a UI mismatch in notes.txt handling for the API route.",
                "response_mode": "fast",
            },
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]

        live_events = [payload for payload in payloads if payload["event"] == "v8_event"]
        context_payload = next(payload for payload in payloads if payload["event"] == "context")
        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")
        token_payloads = [payload for payload in payloads if payload["event"] == "token"]

        self.assertGreaterEqual(len(live_events), 4)
        self.assertIn(
            "context_gather_start",
            [payload["v8_event"]["event_type"] for payload in live_events],
        )
        self.assertIn(
            "response_generation_started",
            [payload["v8_event"]["event_type"] for payload in live_events],
        )
        self.assertIn(
            "assistant_response_ready",
            [payload["v8_event"]["event_type"] for payload in live_events],
        )
        self.assertIsNotNone(context_payload["workspace_context"])
        self.assertEqual(context_payload["requested_response_mode"], "fast")
        self.assertEqual(context_payload["response_mode"], "debug")
        self.assertTrue(context_payload["mode_guidance"]["auto_applied"])
        self.assertEqual(token_payloads[0]["event"], "token")
        self.assertEqual(final_payload["response"], "Jarvis is online.")
        self.assertEqual(payloads[-1]["event"], "done")
        self.assertEqual(final_payload["requested_response_mode"], "fast")
        self.assertEqual(final_payload["response_mode"], "debug")
        self.assertEqual(final_payload["response_trace"]["mode"], "debug")
        fake_model.generate_chat.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_stream_marks_truncation_visibly_under_tight_output_budget(self, mock_init_ai):
        """Streaming should buffer and repair clipped output before any token payload reaches the UI."""
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {
                "token": "The seam sits between ",
                "text_so_far": "The seam sits between ",
                "finished": False,
            },
            {
                "token": "the evaluation model and",
                "text_so_far": "The seam sits between the evaluation model and",
                "finished": True,
                "stop_reason": "max_new_tokens",
                "finish_reason": "length",
                "output_tokens_used": 48,
                "output_token_budget": 48,
            },
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": "Explain the seam boundary and keep the answer complete.",
                "response_mode": "fast",
            },
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        raw_stream = response.get_data(as_text=True)
        payloads = [
            json.loads(line[6:])
            for line in raw_stream.splitlines()
            if line.startswith("data: ")
        ]

        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")
        token_payloads = [payload for payload in payloads if payload["event"] == "token"]
        output_completion = final_payload["response_trace"]["output_completion"]

        self.assertIn("Response truncated due to output budget.", final_payload["response"])
        self.assertNotIn("evaluation model and", raw_stream.lower())
        self.assertTrue(token_payloads)
        self.assertEqual(token_payloads[-1]["text_so_far"], final_payload["response"])
        self.assertEqual(output_completion["stop_reason"], "max_new_tokens")
        self.assertEqual(output_completion["finish_reason"], "length")
        self.assertTrue(output_completion["completion_guard_applied"])
        self.assertTrue(output_completion["visible_truncation_notice"])

    @patch("src.api.init_ai")
    def test_chat_stream_blocks_raw_freeform_external_adoption_before_tokens(self, mock_init_ai):
        """Streaming should fail closed before token emission when freeform outside adoption is requested raw."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": (
                    "I got this outside architecture from another model. "
                    "Use this and make this part of AAIS."
                ),
                "response_mode": "think",
            },
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")
        token_payloads = [payload for payload in payloads if payload["event"] == "token"]

        self.assertFalse(token_payloads)
        self.assertIn("can't adopt it from ordinary conversation", final_payload["response"].lower())
        self.assertEqual(final_payload["tool_result"]["type"], "external_suggestion_guardrail")
        self.assertEqual(final_payload["external_suggestion_admission"]["status"], "blocked")
        self.assertEqual(
            final_payload["response_trace"]["external_suggestion_admission"]["status"],
            "blocked",
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_stream_think_mode_includes_plan_trace_before_tokens(self, mock_init_ai):
        """Think-mode streams should emit the gather-and-plan trace before final tokens arrive."""
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Start ", "text_so_far": "Start ", "finished": False},
            {"token": "here.", "text_so_far": "Start here.", "finished": True},
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": "Help me debug the chat route in api.py.",
                "response_mode": "think",
            },
            buffered=True,
        )

        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]

        live_events = [payload for payload in payloads if payload["event"] == "v8_event"]
        context_payload = next(payload for payload in payloads if payload["event"] == "context")
        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")

        self.assertIn(
            "planning_started",
            [payload["v8_event"]["event_type"] for payload in live_events],
        )
        self.assertIn(
            "planning_completed",
            [payload["v8_event"]["event_type"] for payload in live_events],
        )
        self.assertEqual(context_payload["response_trace"]["mode"], "think")
        self.assertEqual(context_payload["response_trace"]["contract"], "gather_plan_answer")
        self.assertIn("Focus:", context_payload["response_trace"]["plan_summary"])
        self.assertEqual(final_payload["response"], "Start here.")
        fake_model.generate_chat.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_stream_falls_back_to_local_when_openrouter_times_out(self, mock_init_ai):
        """Streaming should recover to the local model when the remote provider times out."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("The read operation timed out")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Local ", "text_so_far": "Local ", "finished": False},
            {"token": "fallback.", "text_so_far": "Local fallback.", "finished": True},
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/stream",
                json={
                    "message": "Stream this through OpenRouter if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
                buffered=True,
            )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]

        live_events = [payload for payload in payloads if payload["event"] == "v8_event"]
        token_payloads = [payload for payload in payloads if payload["event"] == "token"]
        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")
        event_types = [payload["v8_event"]["event_type"] for payload in live_events]

        self.assertIn("provider_fallback", event_types)
        self.assertTrue(
            all(
                set(payload.keys()) == {"event", "token", "text_so_far", "finished"}
                for payload in token_payloads
            )
        )
        self.assertEqual(final_payload["response"], "Local fallback.")
        self.assertEqual(final_payload["preferred_provider"], "openrouter")
        self.assertEqual(final_payload["model_route"]["provider"], "local")
        self.assertEqual(final_payload["provider_notice"]["requested_provider"], "openrouter")
        self.assertEqual(final_payload["provider_notice"]["resolved_provider"], "local")
        self.assertEqual(final_payload["provider_notice"]["fallback_kind"], "runtime_error")
        self.assertIn("timed out", final_payload["provider_notice"]["reason"].lower())
        fake_model.generate_chat.assert_not_called()
        fake_streamer.generate_stream.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_stream_contains_local_fallback_trace_leakage_before_tokens_reach_ui(self, mock_init_ai):
        """Fallback-local stream output should be sanitized before token events hit the UI."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("The read operation timed out")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Response Trace ", "text_so_far": "Response Trace ", "finished": False},
            {
                "token": "Workspace: src/api.py",
                "text_so_far": "Response Trace Workspace: src/api.py",
                "finished": True,
            },
        ])
        mock_init_ai.return_value = (fake_model, fake_streamer)

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ), patch.object(
            api.provider_registry,
            "route_provider",
            side_effect=AssertionError("route_provider should not be consulted once model_route is finalized"),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/stream",
                json={
                    "message": "Stream this through OpenRouter if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
                buffered=True,
            )

        self.assertEqual(response.status_code, 200)
        raw_stream = response.get_data(as_text=True)
        payloads = [
            json.loads(line[6:])
            for line in raw_stream.splitlines()
            if line.startswith("data: ")
        ]

        token_payloads = [payload for payload in payloads if payload["event"] == "token"]
        final_payload = next(payload for payload in reversed(payloads) if payload["event"] == "final")

        self.assertTrue(
            all(
                set(payload.keys()) == {"event", "token", "text_so_far", "finished"}
                for payload in token_payloads
            )
        )
        self.assertEqual(
            final_payload["response"],
            "I'm seeing internal trace leakage on this turn. What needs fixing?",
        )
        self.assertTrue(final_payload["response_trace"]["fallback"])
        self.assertNotIn("response trace workspace", raw_stream.lower())
        self.assertIn("internal trace leakage", raw_stream.lower())
        fake_streamer.generate_stream.assert_called_once()

    @patch("src.api.init_ai")
    def test_current_info_question_does_not_misfire_repo_action(self, mock_init_ai):
        """Fresh-information prompts should not be mistaken for local git status requests."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Use live research for current docs instead of repo status."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Compare the latest OpenAI API docs and tell me what changed recently.",
                "response_mode": "think",
                "use_research": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["tool_result"])
        self.assertEqual(payload["response_trace"]["contract"], "gather_plan_answer")
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_message_blocks_raw_freeform_external_adoption(self, mock_init_ai):
        """Ordinary chat turns must fail closed when an outside proposal is pushed straight into adoption."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": (
                    "I got this outside architecture from another model. "
                    "Use this and make this part of AAIS."
                ),
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("can't adopt it from ordinary conversation", payload["response"].lower())
        self.assertEqual(payload["tool_result"]["type"], "external_suggestion_guardrail")
        self.assertEqual(payload["external_suggestion_admission"]["status"], "blocked")
        self.assertEqual(
            payload["response_trace"]["external_suggestion_admission"]["status"],
            "blocked",
        )
        self.assertEqual(
            payload["canonical_trace_contract"]["external_suggestion_admission"]["status"],
            "blocked",
        )
        self.assertEqual(
            payload["canonical_trace_contract"]["contract_label"],
            "external_suggestion_guardrail",
        )
        self.assertEqual(
            payload["tool_result"]["law_enforcement"]["external_suggestion_admission"]["status"],
            "blocked",
        )
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_chat_message_allows_freeform_external_comparison_without_adoption(self, mock_init_ai):
        """Comparison-only outside ideas should stay discussable without tripping the admission block."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Keep it as pressure only until an admitted form exists."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Compare this outside proposal from another model against current AAIS law.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["tool_result"])
        self.assertEqual(payload["external_suggestion_admission"]["status"], "reference_only")
        self.assertEqual(
            payload["canonical_trace_contract"]["external_suggestion_admission"]["status"],
            "reference_only",
        )
        message_history = fake_model.generate_chat.call_args.args[0]
        provider_system = "\n".join(
            message["content"]
            for message in message_history
            if message["role"] == "system"
        )
        self.assertIn("outside idea is present for comparison only", provider_system)
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_chat_message_allows_filtered_freeform_external_adoption(self, mock_init_ai):
        """Admitted-form metadata should reopen the conversational lane without using the raw outside proposal as truth."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Use only the bounded sequencing pattern and preserve existing module boundaries."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        admitted_form = "Use only the bounded sequencing pattern and preserve existing module boundaries."
        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": (
                    "I got this outside architecture from another model. "
                    "Use this and make this part of AAIS."
                ),
                "response_mode": "think",
                "external_suggestion": {
                    "summary": "Outside architecture proposal.",
                },
                "external_suggestion_usage": "adoption",
                "law_filter_applied": True,
                "admitted_external_form": admitted_form,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["tool_result"])
        self.assertEqual(payload["external_suggestion_admission"]["status"], "admitted")
        self.assertEqual(
            payload["response_trace"]["external_suggestion_admission"]["status"],
            "admitted",
        )
        message_history = fake_model.generate_chat.call_args.args[0]
        provider_system = "\n".join(
            message["content"]
            for message in message_history
            if message["role"] == "system"
        )
        self.assertIn("Use only this documented admitted form for this turn", provider_system)
        self.assertIn(admitted_form, provider_system)
        fake_model.generate_chat.assert_called_once()

    @patch("src.api.init_ai")
    def test_current_turn_upgrade_request_is_not_hijacked_by_active_cutoff_problem(self, mock_init_ai):
        """Broad upgrade requests should answer directly before any older tracked debugging context."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Prioritize the memory governance pass first. It stabilizes continuity, prompt hygiene, and downstream routing."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Repair response cutoff seam",
                "objective": "Find why replies are being cut off mid-thought and stop the truncation.",
                "next_step": "Trace the prompt and output boundaries under pressure.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "What upgrade should I prioritize first?",
                "response_mode": "fast",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        guard = payload["response_trace"]["context_priority_guard"]
        canonical = payload["canonical_trace_contract"]
        self.assertFalse(guard["allow_active_problem_context"])
        self.assertEqual(guard["status"], "answer_first")
        self.assertFalse(payload["context_priority_guard"]["allow_active_problem_context"])
        self.assertEqual(canonical, payload["response_trace"]["canonical_contract"])
        self.assertEqual(canonical["conversation_lane"], "operator_task")
        self.assertEqual(canonical["current_turn_priority"]["status"], "answer_first")
        self.assertFalse(canonical["current_turn_priority"]["allow_active_problem_context"])

        message_history = fake_model.generate_chat.call_args.args[0]
        provider_system = "\n".join(
            message["content"]
            for message in message_history
            if message["role"] == "system"
        )
        self.assertIn("Current-turn priority rule: answer the latest user request directly", provider_system)
        self.assertNotIn("Mission Board:", provider_system)
        self.assertNotIn("Repair response cutoff seam", provider_system)
        self.assertNotIn("Find why replies are being cut off mid-thought and stop the truncation.", provider_system)

    @patch("src.api.init_ai")
    def test_explicit_cutoff_troubleshooting_request_keeps_active_problem_context_bound(self, mock_init_ai):
        """Explicit troubleshooting turns should still bind the tracked active problem context."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "The next check is the output-finalization boundary where clipped replies can still escape if stop metadata is missing."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Repair response cutoff seam",
                "objective": "Find why replies are being cut off mid-thought and stop the truncation.",
                "next_step": "Trace the prompt and output boundaries under pressure.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Continue debugging why the reply still gets cut off mid-thought.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        guard = payload["response_trace"]["context_priority_guard"]
        self.assertTrue(guard["allow_active_problem_context"])
        self.assertEqual(guard["status"], "context_bound")

        message_history = fake_model.generate_chat.call_args.args[0]
        provider_system = "\n".join(
            message["content"]
            for message in message_history
            if message["role"] == "system"
        )
        self.assertIn("Mission Board:", provider_system)
        self.assertIn("Repair response cutoff seam", provider_system)
        self.assertIn("Find why replies are being cut off mid-thought and stop the truncation.", provider_system)
        self.assertNotIn("Current-turn priority rule: answer the latest user request directly", provider_system)

    @patch("src.api.web_researcher")
    @patch("src.api.init_ai")
    def test_chat_stream_context_can_include_live_research(self, mock_init_ai, mock_researcher):
        """Streaming context payloads should expose research sources for inline source cards."""
        fake_streamer = MagicMock()
        fake_streamer.generate_stream.return_value = iter([
            {"token": "Fresh ", "text_so_far": "Fresh ", "finished": False},
            {"token": "answer.", "text_so_far": "Fresh answer.", "finished": True},
        ])
        mock_init_ai.return_value = (MagicMock(), fake_streamer)
        mock_researcher.research.return_value = {
            "query": "latest OpenAI news",
            "summary": "Loaded 1 live web source.",
            "sources": [
                {
                    "id": 1,
                    "title": "OpenAI News",
                    "url": "https://openai.com/news/",
                    "display_url": "openai.com/news/",
                    "snippet": "Latest updates.",
                    "excerpt": "Latest updates from OpenAI.",
                },
            ],
            "prompt_block": "Live web research is attached for this turn.\n[1] OpenAI News",
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={"message": "What is the latest OpenAI news?", "use_research": True},
            buffered=True,
        )

        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        context_payload = next(payload for payload in payloads if payload["event"] == "context")
        self.assertEqual(context_payload["live_research"]["sources"][0]["title"], "OpenAI News")

    @patch("src.api.web_researcher")
    @patch("src.api.init_ai")
    def test_research_mode_enables_live_research_by_default(self, mock_init_ai, mock_researcher):
        """Research mode should pull fresh sources even without an explicit toggle."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The docs changed recently."
        mock_init_ai.return_value = (fake_model, object())
        mock_researcher.research.return_value = {
            "query": "compare the latest OpenAI docs",
            "summary": "Loaded 1 live web source.",
            "sources": [
                {
                    "id": 1,
                    "title": "OpenAI Docs",
                    "url": "https://platform.openai.com/docs",
                    "display_url": "platform.openai.com/docs",
                    "snippet": "Latest API docs.",
                    "excerpt": "Latest API docs.",
                },
            ],
            "prompt_block": "Live web research is attached.",
        }

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Compare the latest OpenAI docs for me.",
                "response_mode": "research",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_trace"]["mode"], "research")
        self.assertEqual(payload["response_trace"]["research_reason"], "research_default_on")
        self.assertEqual(payload["response_trace"]["contract"], "scan_compare_cite")
        self.assertEqual(payload["live_research"]["sources"][0]["title"], "OpenAI Docs")
        mock_researcher.research.assert_called_once()

    def test_operator_mode_can_propose_safe_action_without_exact_command_phrase(self):
        """Operator mode should route vague verification requests into a safe action proposal."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Can you verify the repo before we keep going?",
                "response_mode": "operator",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["tool_result"]["type"], "action_request")
        self.assertEqual(payload["tool_result"]["action"]["id"], "git_status")
        self.assertEqual(payload["response_trace"]["mode"], "operator")
        self.assertEqual(payload["response_trace"]["contract"], "direct_tool")

    @patch("src.api.init_ai")
    def test_operator_message_records_instant_compose(self, mock_init_ai):
        """Jarvis operator turns should always record Spine + ARIS via composed turn."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Project status is stable on the current branch."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "response_mode": "operator"},
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(api.jarvis_operator, "handle_command", return_value=None):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Summarize project status in one paragraph.",
                    "response_mode": "operator",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "completed")
        self.assertEqual(composed.get("compose_mode"), "instant")
        self.assertEqual(composed.get("aris_status"), "enforced")

    @patch("src.api.init_ai")
    def test_operator_think_mode_uses_fast_compose(self, mock_init_ai):
        """Think-mode operator turns should use fast compose (reasoning + attention only)."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Here is a concise runtime summary."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis.", "response_mode": "operator"},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Summarize the runtime map.",
                "response_mode": "think",
            },
        )

        self.assertEqual(response.status_code, 200)
        composed = response.get_json().get("aais_composed_turn")
        self.assertEqual(composed.get("compose_mode"), "fast")
        self.assertEqual(
            set(composed.get("active_cognitive_runtimes") or []),
            {"jarvis.reasoning", "cognitive.attention"},
        )

    @patch("src.api.init_ai")
    def test_tiny_nova_message_stays_off_direct_tool_path(self, mock_init_ai):
        """Tiny Nova should answer conversationally even when the prompt resembles an operator verification request."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "It sounds like you want reassurance before moving. Start with the single point you most need clarity on."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "tiny_nova",
                "response_mode": "operator",
            },
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(api.jarvis_operator, "handle_command") as mock_handle_command:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Can you verify the repo before we keep going?",
                    "persona_mode": "tiny_nova",
                    "response_mode": "operator",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_mode"], "tiny")
        self.assertIsNone(payload["tool_result"])
        self.assertEqual(payload["response_trace"]["mode"], "tiny")
        self.assertEqual(payload["response_trace"]["contract"], "tiny_companion")
        self.assertEqual(payload["response_trace"]["research_sources"], 0)
        self.assertEqual(payload["response_trace"]["workspace_hits"], 0)
        self.assertIsNone(payload["workspace_context"])
        self.assertIsNone(payload["live_research"])
        self.assertEqual(payload["mode_guidance"]["surface_identity"], "tiny_nova")
        self.assertEqual(payload["mode_guidance"]["authority_lane"], "jarvis")
        self.assertFalse(payload["mode_guidance"]["surface_replaces_authority"])
        self.assertEqual(payload["provider_mind"]["authority_lane"], "jarvis")
        self.assertEqual(payload["provider_mind"]["surface_identity"], "tiny_nova")
        self.assertFalse(payload["provider_mind"]["surface_replaces_authority"])
        self.assertEqual(payload["sovereignty_contract"]["authority_lane"], "jarvis")
        self.assertEqual(payload["sovereignty_contract"]["surface_identity"], "tiny_nova")
        self.assertFalse(payload["sovereignty_contract"]["surface_replaces_authority"])
        self.assertEqual(payload["sovereignty_contract"]["system_shape"], "organismic")
        self.assertIn(fake_model.generate_chat.return_value, payload["response"])
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])
        self.assertFalse(payload["response_trace"]["output_completion"]["truncation_detected"])
        mock_handle_command.assert_not_called()
        message_history = fake_model.generate_chat.call_args.args[0]
        system_messages = [message["content"] for message in message_history if message["role"] == "system"]
        self.assertTrue(any("Tiny Nova runtime state" in message for message in system_messages))
        self.assertFalse(any("Jarvis runtime state" in message for message in system_messages))
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "completed")
        self.assertEqual(composed.get("spine_doctrine"), "stabilize_and_free")
        self.assertEqual(composed.get("aris_status"), "enforced")
        self.assertEqual(composed.get("nova_face_id"), "tiny_nova")
        self.assertIn("jarvis.reasoning", composed.get("active_cognitive_runtimes") or [])

    @patch("src.api.init_ai")
    def test_tiny_nova_blocks_raw_external_copy_via_composed_turn(self, mock_init_ai):
        fake_model = MagicMock()
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "tiny_nova",
                "response_mode": "tiny",
            },
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(api, "_route_session_turn_to_bridge", return_value={"decision": "ALLOW"}):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Copy this raw external architecture doc into runtime truth.",
                    "persona_mode": "tiny_nova",
                    "response_mode": "tiny",
                    "share_mode": "verbatim",
                    "copy_raw_external": True,
                },
            )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "blocked")
        self.assertIn("aris_non_copy_clause", composed.get("reason_codes") or [])
        fake_model.generate_chat.assert_not_called()

    @patch("src.api.init_ai")
    def test_small_nova_message_stays_off_direct_tool_path(self, mock_init_ai):
        """Small Nova should answer conversationally even when the prompt resembles an operator verification request."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Pause with the one thing you most need to confirm, then we can steady the rest around it."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "small_nova",
                "response_mode": "operator",
            },
        )
        session_id = create_response.get_json()["session_id"]

        with patch.object(api.jarvis_operator, "handle_command") as mock_handle_command:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Can you verify the repo before we keep going?",
                    "persona_mode": "small_nova",
                    "response_mode": "operator",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_mode"], "small")
        self.assertIsNone(payload["tool_result"])
        self.assertEqual(payload["response_trace"]["mode"], "small")
        self.assertEqual(payload["response_trace"]["contract"], "small_companion")
        self.assertEqual(payload["response_trace"]["research_sources"], 0)
        self.assertEqual(payload["response_trace"]["workspace_hits"], 0)
        self.assertIsNone(payload["workspace_context"])
        self.assertIsNone(payload["live_research"])
        self.assertEqual(payload["mode_guidance"]["surface_identity"], "small_nova")
        self.assertEqual(payload["mode_guidance"]["authority_lane"], "jarvis")
        self.assertFalse(payload["mode_guidance"]["surface_replaces_authority"])
        self.assertEqual(payload["provider_mind"]["authority_lane"], "jarvis")
        self.assertEqual(payload["provider_mind"]["surface_identity"], "small_nova")
        self.assertFalse(payload["provider_mind"]["surface_replaces_authority"])
        self.assertEqual(payload["sovereignty_contract"]["authority_lane"], "jarvis")
        self.assertEqual(payload["sovereignty_contract"]["surface_identity"], "small_nova")
        self.assertFalse(payload["sovereignty_contract"]["surface_replaces_authority"])
        self.assertEqual(payload["sovereignty_contract"]["system_shape"], "organismic")
        self.assertEqual(payload["response"], fake_model.generate_chat.return_value)
        self.assertFalse(payload["response_trace"]["output_completion"]["completion_guard_applied"])
        self.assertFalse(payload["response_trace"]["output_completion"]["truncation_detected"])
        mock_handle_command.assert_not_called()
        message_history = fake_model.generate_chat.call_args.args[0]
        system_messages = [message["content"] for message in message_history if message["role"] == "system"]
        self.assertTrue(any("Small Nova runtime state" in message for message in system_messages))
        self.assertFalse(any("Jarvis runtime state" in message for message in system_messages))

    @patch("src.api.init_ai")
    def test_small_nova_message_treats_loaded_archive_as_document_context(self, mock_init_ai):
        """Loaded local session archives should be attached as explicit document context, not memory."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "I can read the saved session you opened and stay with what still matters there."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "small_nova",
                "response_mode": "small",
            },
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Stay with the earlier session and help me continue it.",
                "persona_mode": "small_nova",
                "response_mode": "small",
                "loaded_session_archive": {
                    "id": "archive-1",
                    "title": "Reopened session",
                    "saved_at": "2026-04-16T12:00:00Z",
                    "assistant_name": "Small Nova",
                    "persona_mode": "small_nova",
                    "response_mode": "small",
                    "message_count": 3,
                    "excerpt": "Earlier saved session excerpt.",
                    "transcript_text": "User\nHelp me steady the plan.\n\nNova\nStart with the part that still feels true.",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response"], fake_model.generate_chat.return_value)
        self.assertEqual(payload["loaded_session_archive"]["title"], "Reopened session")
        self.assertEqual(payload["loaded_session_archive"]["assistant_name"], "Small Nova")
        self.assertIn(
            "user-opened session archive 'Reopened session' as document context",
            " ".join(payload["response_trace"]["steps"]),
        )
        message_history = fake_model.generate_chat.call_args.args[0]
        system_messages = [message["content"] for message in message_history if message["role"] == "system"]
        self.assertTrue(any("Loaded session archive (external context, not memory)" in message for message in system_messages))
        self.assertTrue(any("Never say you remember this session" in message for message in system_messages))

    @patch("src.api.init_ai")
    def test_super_nova_message_requires_explicit_activation_before_generation(self, mock_init_ai):
        """Super Nova should fail closed before generation until activation passes."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me hold the deeper continuity here.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertIn("explicit activation", payload["error"].lower())
        self.assertEqual(payload["response_mode"], "governed_full")
        self.assertEqual(payload["session_state"]["state"], "awaiting_approval")
        self.assertEqual(payload["super_nova"]["activation"]["current_state"], "dormant")
        self.assertIsNone(payload.get("aais_composed_turn"))
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_super_nova_activation_and_message_stay_in_governed_lane(self, mock_init_ai):
        """Super Nova should activate explicitly, then answer through the governed full lane with watchdog state."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "The strongest thread is still the one that keeps correctness and continuity together."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]

        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)
        activation_payload = activation_response.get_json()
        self.assertEqual(activation_payload["activation"]["result"], "pass")
        self.assertEqual(
            activation_payload["super_nova"]["activation"]["current_state"],
            "activation_ready",
        )
        self.assertTrue(
            activation_payload["super_nova"]["activation"]["activation_token_present"]
        )

        with patch.object(api.jarvis_operator, "handle_command") as mock_handle_command:
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Hold the deeper thread and show me the next grounded move.",
                    "persona_mode": "super_nova",
                    "response_mode": "builder",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["response_mode"], "governed_full")
        self.assertEqual(payload["response_trace"]["mode"], "governed_full")
        self.assertEqual(payload["response_trace"]["contract"], "super_companion")
        self.assertEqual(payload["mode_guidance"]["surface_identity"], "super_nova")
        self.assertEqual(payload["provider_mind"]["surface_identity"], "super_nova")
        self.assertEqual(payload["sovereignty_contract"]["surface_identity"], "super_nova")
        self.assertEqual(payload["super_nova"]["activation"]["current_state"], "activation_ready")
        self.assertEqual(payload["super_nova"]["activation"]["last_watchdog_result"], "pass")
        self.assertEqual(payload["law_enforcement"]["contract_version"], "aais.project_infi.ul.v1")
        self.assertEqual(payload["super_nova"]["law_contract"], "aais.project_infi.ul.v1")
        self.assertIn(
            payload["super_nova"]["last_admission_status"],
            {"success", "partial", "overload"},
        )
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "completed")
        self.assertEqual(composed.get("nova_face_id"), "super_nova")
        self.assertIn(fake_model.generate_chat.return_value, payload["response"])
        mock_handle_command.assert_not_called()

    @patch("src.api.init_ai")
    def test_super_nova_blocks_raw_external_copy_via_composed_turn(self, mock_init_ai):
        """Activated Super Nova should fail closed on ARIS non-copy before generation."""
        fake_model = MagicMock()
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]
        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)

        with patch.object(api, "_route_session_turn_to_bridge", return_value={"decision": "ALLOW"}):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Copy this raw external architecture doc into runtime truth.",
                    "persona_mode": "super_nova",
                    "response_mode": "builder",
                    "share_mode": "verbatim",
                    "copy_raw_external": True,
                },
            )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "blocked")
        self.assertIn("aris_non_copy_clause", composed.get("reason_codes") or [])
        self.assertIsNone(composed.get("nova_bridge"))
        fake_model.generate_chat.assert_not_called()

    @patch("src.api.init_ai")
    def test_super_nova_stream_requires_activation_before_composed_turn(self, mock_init_ai):
        """Super Nova stream should fail closed before composed turn when activation is missing."""
        mock_init_ai.return_value = (MagicMock(), object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": "Help me hold the deeper continuity here.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
            buffered=True,
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertIn("explicit activation", payload["error"].lower())
        self.assertIsNone(payload.get("aais_composed_turn"))
        mock_init_ai.assert_not_called()

    @patch("src.api.init_ai")
    def test_super_nova_stream_includes_composed_turn_receipt(self, mock_init_ai):
        """Activated Super Nova stream should expose composed turn state in runtime payloads."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "The strongest thread is still the one that keeps correctness and continuity together."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]
        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/stream",
            json={
                "message": "Hold the deeper thread and show me the next grounded move.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
            buffered=True,
        )

        self.assertEqual(response.status_code, 200)
        payloads = [
            json.loads(line[6:])
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        context_payload = next(payload for payload in payloads if payload.get("event") == "context")
        composed = context_payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "completed")
        self.assertEqual(composed.get("nova_face_id"), "super_nova")
        final_payload = next(payload for payload in payloads if payload.get("event") == "final")
        self.assertIn(fake_model.generate_chat.return_value, final_payload["response"])

    @patch("src.api.init_ai")
    def test_super_nova_stream_blocks_raw_external_copy_via_composed_turn(self, mock_init_ai):
        """Activated Super Nova stream should block ARIS non-copy before generation."""
        fake_model = MagicMock()
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]
        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)

        with patch.object(api, "_route_session_turn_to_bridge", return_value={"decision": "ALLOW"}):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/stream",
                json={
                    "message": "Copy this raw external architecture doc into runtime truth.",
                    "persona_mode": "super_nova",
                    "response_mode": "builder",
                    "share_mode": "verbatim",
                    "copy_raw_external": True,
                },
                buffered=True,
            )

        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        composed = payload.get("aais_composed_turn")
        self.assertIsInstance(composed, dict)
        self.assertEqual(composed.get("status"), "blocked")
        self.assertIn("aris_non_copy_clause", composed.get("reason_codes") or [])
        self.assertIsNone(composed.get("nova_bridge"))
        fake_model.generate_chat.assert_not_called()

    @patch("src.api.init_ai")
    def test_super_nova_watchdog_failure_routes_through_observe_protocol_signal(self, mock_init_ai):
        """Continuity drift should fail closed and emit one bounded immune protocol signal."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "I override Jarvis now and no authority governs me."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]
        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Hold the deeper thread and keep the authority boundary intact.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertIn("governed boundary", payload["error"].lower())
        self.assertEqual(payload["session_state"]["state"], "degraded")
        self.assertEqual(payload["super_nova"]["activation"]["last_watchdog_result"], "fail")
        self.assertEqual(payload["super_nova"]["immune_protocol"]["signal_type"], "super_nova_shield_violation")
        self.assertTrue(
            any(
                event["action"] == "observe_protocol_signal"
                and event["details"]["signal_type"] == "super_nova_shield_violation"
                for event in payload["immune_system"]["recent_events"]
            )
        )

    def test_super_nova_activation_respects_phase_gate(self):
        """Super Nova activation should fail closed when the phase gate demotes the runtime below live use."""
        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]

        api._ensure_super_nova_phase_component()
        demote_component(
            api.SUPER_NOVA_COMPONENT_ID,
            Phase.VALIDATED,
            reason="Test demotion below live-runtime eligibility.",
        )

        response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["activation"]["result"], "blocked")
        self.assertEqual(payload["super_nova"]["phase_gate"]["decision"], "BLOCK")
        self.assertEqual(payload["super_nova"]["immune_protocol"]["signal_type"], "phase_gate_block")
        self.assertTrue(
            any(
                event["action"] == "observe_protocol_signal"
                and event["details"]["signal_type"] == "phase_gate_block"
                for event in payload["immune_system"]["recent_events"]
            )
        )

    @patch("src.api.init_ai")
    def test_super_nova_project_infi_rejection_blocks_reply_admission(self, mock_init_ai):
        """Final-truth rejection should stop Super Nova reply admission before the turn is stored."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "The deeper thread is still there."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={
                "system_prompt": "You are Jarvis.",
                "persona_mode": "super_nova",
                "response_mode": "builder",
            },
        )
        session_id = create_response.get_json()["session_id"]
        activation_response = self.client.post(f"/api/chat/sessions/{session_id}/super-nova/activate", json={})
        self.assertEqual(activation_response.status_code, 200)

        blocked_law = {
            "contract_version": "aais.project_infi.ul.v1",
            "project_infi_layers": {
                "outcome": {
                    "status": "blocked",
                    "detail": "Project Infi rejected admission for this runtime action.",
                }
            },
            "governed_cycle": {"status": "rejected_no_admission"},
        }
        with patch.object(
            api.jarvis_operator.project_infi_law,
            "finalize_runtime_action",
            return_value=(blocked_law, {"decision": "runtime_action_blocked"}),
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Hold the deeper thread and offer the next grounded move.",
                    "persona_mode": "super_nova",
                    "response_mode": "builder",
                },
            )

        self.assertEqual(response.status_code, 409)
        payload = response.get_json()
        self.assertEqual(payload["law_enforcement"]["governed_cycle"]["status"], "rejected_no_admission")
        self.assertEqual(payload["session_state"]["state"], "degraded")
        self.assertEqual(payload["super_nova"]["immune_protocol"]["signal_type"], "final_truth_rejected")
        self.assertIn("rejected admission", payload["error"].lower())

    def test_browser_verification_endpoint_returns_workspace_grounding_and_action(self):
        """Browser verification should ground a rendered route back to local code and the V8 session."""
        (self.workspace_root / "AAIS-main" / "frontend" / "src" / "pages").mkdir(parents=True)
        (
            self.workspace_root
            / "AAIS-main"
            / "frontend"
            / "src"
            / "pages"
            / "ImageAnalyzer.jsx"
        ).write_text(
            "export default function ImageAnalyzer() {\n"
            "  return <main><h1>Image Analyzer</h1><button>Analyze Image</button></main>;\n"
            "}\n",
            encoding="utf-8",
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/browser/verify",
            json={
                "snapshot": {
                    "url": "http://localhost:3000/image-analyzer",
                    "path": "/image-analyzer",
                    "title": "AAIS | Image Analyzer",
                    "headings": ["Image Analyzer"],
                    "buttons": ["Analyze Image", "Upload Screenshot"],
                    "alerts": [],
                    "main_text": "Image Analyzer Upload Screenshot Analyze Image",
                    "route_markers": ["image analyzer"],
                    "dom_counts": {"headings": 1, "buttons": 2, "links": 0, "forms": 1, "inputs": 1},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
                "expectation": "The image analyzer route should show the upload flow.",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        verification = payload["browser_verification"]
        self.assertEqual(verification["target_path"], "/image-analyzer")
        self.assertEqual(verification["status"], "healthy")
        self.assertEqual(verification["suggested_action"]["id"], "build_frontend")
        self.assertEqual(verification["expectation_source"], "manual")
        self.assertEqual(payload["session_state"]["state"], "ready")
        self.assertEqual(payload["browser_verification"]["workspace_context"]["project_scope"], "AAIS-main")
        self.assertTrue(
            payload["browser_verification"]["workspace_context"]["results"][0]["relative_path"]
            .replace("/", "\\")
            .endswith("AAIS-main\\frontend\\src\\pages\\ImageAnalyzer.jsx")
        )

    def test_browser_verification_endpoint_can_infer_known_route_expectation(self):
        """Browser verification should auto-apply a built-in route guide when no manual expectation is provided."""
        (self.workspace_root / "AAIS-main" / "frontend" / "src" / "pages").mkdir(parents=True)
        (
            self.workspace_root
            / "AAIS-main"
            / "frontend"
            / "src"
            / "pages"
            / "Settings.jsx"
        ).write_text(
            "export default function Settings() {\n"
            "  return <main><h1>Settings</h1><button>Save Settings</button><button>Reset to Default</button></main>;\n"
            "}\n",
            encoding="utf-8",
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/browser/verify",
            json={
                "snapshot": {
                    "url": "http://localhost:3000/settings",
                    "path": "/settings",
                    "title": "AAIS | Settings",
                    "headings": ["Settings"],
                    "buttons": ["Save Settings", "Reset to Default"],
                    "alerts": [],
                    "main_text": "Settings API URL Default Model Save Settings Reset to Default",
                    "route_markers": ["settings"],
                    "dom_counts": {"headings": 1, "buttons": 2, "links": 0, "forms": 1, "inputs": 3},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        verification = response.get_json()["browser_verification"]
        self.assertEqual(verification["expectation_source"], "auto")
        self.assertEqual(verification["route_expectation"]["route_key"], "settings")
        self.assertEqual(verification["route_expectation"]["fit"]["status"], "aligned")
        self.assertEqual(verification["suggested_action"]["id"], "build_frontend")
        self.assertTrue(
            verification["workspace_context"]["results"][0]["relative_path"]
            .replace("/", "\\")
            .endswith("AAIS-main\\frontend\\src\\pages\\Settings.jsx")
        )

    def test_browser_verification_auto_links_to_active_mission(self):
        """Browser verification should attach its route and file context to the active mission."""
        (self.workspace_root / "AAIS-main" / "frontend" / "src" / "pages").mkdir(parents=True)
        (
            self.workspace_root
            / "AAIS-main"
            / "frontend"
            / "src"
            / "pages"
            / "Settings.jsx"
        ).write_text(
            "export default function Settings() {\n"
            "  return <main><h1>Settings</h1><button>Save Settings</button></main>;\n"
            "}\n",
            encoding="utf-8",
        )

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Fix Settings page",
                "objective": "Ground the settings route against code and repair it if needed.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/browser/verify",
            json={
                "snapshot": {
                    "url": "http://localhost:3000/settings",
                    "path": "/settings",
                    "title": "AAIS | Settings",
                    "headings": ["Settings"],
                    "buttons": ["Save Settings"],
                    "alerts": [],
                    "main_text": "Settings Save Settings",
                    "route_markers": ["settings"],
                    "dom_counts": {"headings": 1, "buttons": 1, "links": 0, "forms": 1, "inputs": 1},
                    "viewport": {"width": 1440, "height": 900},
                    "capture_mode": "iframe",
                    "load_state": "loaded",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        board = response.get_json()["mission_board"]
        active = board["active_mission"]
        self.assertEqual(response.get_json()["mission_critic"]["source"], "browser_verification")
        self.assertEqual(response.get_json()["mission_critic"]["judgment_log"]["judgment_type"], "verification_judgment")
        self.assertEqual(response.get_json()["mission_critic"]["judgment_log"]["cisiv_stage"], "verification")
        self.assertEqual(active["critic"]["source"], "browser_verification")
        link_values = {link["value"] for link in active["links"]}
        self.assertIn("/settings", link_values)
        self.assertTrue(
            any(
                str(value).replace("\\", "/").endswith("AAIS-main/frontend/src/pages/Settings.jsx")
                for value in link_values
            )
        )
        self.assertTrue(any(entry["kind"] == "browser_verification" for entry in active["activity"]))
        self.assertEqual(
            [entry["kind"] for entry in active["history"]][-2:],
            ["browser_verification", "critic_review"],
        )

    @patch("src.api.init_ai")
    def test_chat_message_records_mission_critic_when_active_mission_exists(self, mock_init_ai):
        """Normal chat turns should score how well they advanced the active mission."""
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = (
            "Start by measuring cold-start latency again, then prewarm the model right after boot."
        )
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Stabilize startup",
                "objective": "Improve startup latency on the local laptop runtime.",
                "next_step": "Measure cold-start latency again.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        response = self.client.post(
            f"/api/chat/sessions/{session_id}/message",
            json={
                "message": "Help me improve startup latency on this laptop.",
                "response_mode": "builder",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mission_critic"]["source"], "reply")
        self.assertIn(payload["mission_critic"]["status"], {"advancing", "mixed"})
        self.assertEqual(payload["response_trace"]["mission_critic"]["source"], "reply")
        self.assertEqual(payload["mission_board"]["active_mission"]["critic"]["source"], "reply")

    @patch("src.api.init_ai")
    def test_local_fallback_blocks_reply_mission_critic_state_write(self, mock_init_ai):
        """Fallback-local draft replies must not write protected mission review state."""
        async def _invoke(messages, tools=None, **kwargs):
            del messages, tools, kwargs
            raise RuntimeError("OpenRouter request failed: 429 temporarily rate-limited upstream")

        fake_provider = SimpleNamespace(invoke=_invoke)
        fake_model = MagicMock()
        fake_model.generate_chat.return_value = "Measure cold-start latency again, then prewarm the model."
        mock_init_ai.return_value = (fake_model, object())

        create_response = self.client.post(
            "/api/chat/sessions",
            json={"system_prompt": "You are Jarvis."},
        )
        session_id = create_response.get_json()["session_id"]

        mission_response = self.client.post(
            "/api/jarvis/missions",
            json={
                "title": "Stabilize startup",
                "objective": "Improve startup latency on the local laptop runtime.",
                "next_step": "Measure cold-start latency again.",
                "session_id": session_id,
                "focus": True,
            },
        )
        self.assertEqual(mission_response.status_code, 201)

        with patch.object(
            api.provider_registry,
            "can_invoke",
            side_effect=lambda provider_id: provider_id in {"local", "openrouter"},
        ), patch.object(
            api.provider_registry,
            "get",
            side_effect=lambda provider_id: fake_provider if provider_id == "openrouter" else None,
        ):
            response = self.client.post(
                f"/api/chat/sessions/{session_id}/message",
                json={
                    "message": "Use OpenRouter for this answer if you can.",
                    "response_mode": "think",
                    "provider": "openrouter",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsNone(payload["mission_critic"])
        self.assertNotIn("mission_critic", payload["response_trace"])
        self.assertIn(
            "Blocked Local Heroine fallback from writing protected mission review state.",
            payload["response_trace"]["steps"],
        )
        self.assertIsNone(payload["mission_board"]["active_mission"].get("critic"))
        self.assertIn(
            "sovereignty_violation_blocked",
            [event["event_type"] for event in api.v8_event_log.list_events(session_id, limit=20)],
        )

    @patch("src.api.init_ai")
    def test_image_analyze_endpoint_returns_grounded_payload(self, mock_init_ai):
        """Image analyze should return the structured grounded-vision payload."""
        fake_model = MagicMock()
        fake_model.analyze_image.return_value = {
            "description": "This looks like a landscape screenshot with strong code cues.",
            "analysis_method": "clip-grounded-label-ranking",
            "top_matches": [{"label": "screenshot", "score": 0.61}],
            "dominant_colors": [{"hex": "#102132", "share": 0.44}],
            "image_size": {"width": 320, "height": 200, "orientation": "landscape"},
            "image_features_shape": [1, 512],
        }
        mock_init_ai.return_value = (fake_model, object())

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(16, 33, 50))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/analyze",
            data={"image": (buffer, "sample.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["analysis_method"], "clip-grounded-label-ranking")
        self.assertEqual(payload["top_matches"][0]["label"], "screenshot")
        fake_model.analyze_image.assert_called_once()

    @patch("src.api.init_ai")
    def test_image_generate_returns_503_when_runtime_flag_disables_it(self, mock_init_ai):
        """Image generation should report intentional disablement cleanly."""
        fake_model = MagicMock()
        fake_model.generate_image.side_effect = RuntimeError(
            "Image generation is disabled for this deployment"
        )
        mock_init_ai.return_value = (fake_model, object())

        response = self.client.post(
            "/api/image/generate",
            json={"prompt": "a cinematic city at night"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("disabled", response.get_json()["error"])

    @patch("src.api.init_ai")
    def test_image_analyze_can_embed_document_vision_payload(self, mock_init_ai):
        """Image analyze should pass through OCR/document-vision results when requested."""
        fake_model = MagicMock()
        fake_model.analyze_image.return_value = {
            "description": "This looks like a screenshot. OCR found 6 words across 2 lines.",
            "analysis_method": "clip-grounded-label-ranking",
            "top_matches": [{"label": "screenshot", "score": 0.61}],
            "dominant_colors": [{"hex": "#102132", "share": 0.44}],
            "image_size": {"width": 320, "height": 200, "orientation": "landscape"},
            "image_features_shape": [1, 512],
            "ocr": {
                "requested": True,
                "status": "available",
                "engine": "pytesseract",
                "summary": "OCR found 6 words across 2 lines.",
                "text_preview": "Hello world",
                "line_count": 2,
                "word_count": 6,
                "average_confidence": 88.1,
            },
        }
        mock_init_ai.return_value = (fake_model, object())

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/analyze",
            data={"image": (buffer, "sample.png"), "include_ocr": "true"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["ocr"]["status"], "available")
        self.assertEqual(payload["ocr"]["word_count"], 6)

    @patch("src.api.init_ai")
    def test_image_analyze_can_embed_ui_understanding_payload(self, mock_init_ai):
        """Image analyze should pass through screenshot/UI understanding when requested."""
        fake_model = MagicMock()
        fake_model.analyze_image.return_value = {
            "description": "This looks like a desktop UI screenshot in a dark theme.",
            "analysis_method": "clip-grounded-label-ranking",
            "top_matches": [{"label": "screenshot", "score": 0.58}],
            "dominant_colors": [{"hex": "#102132", "share": 0.44}],
            "image_size": {"width": 1440, "height": 900, "orientation": "landscape"},
            "image_features_shape": [1, 512],
            "ocr": {"status": "unavailable"},
            "ui": {
                "requested": True,
                "status": "available",
                "surface_type": "ui_screenshot",
                "platform_hint": "desktop",
                "theme": "dark",
                "panel_estimate": 3,
                "density_label": "moderate",
                "layout_clues": ["top bar or header", "left sidebar or dock"],
                "readable_targets": ["Dashboard", "Settings"],
                "code_language": None,
                "summary": "This most likely looks like an application UI screenshot on a desktop layout.",
            },
        }
        mock_init_ai.return_value = (fake_model, object())

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/analyze",
            data={"image": (buffer, "sample.png"), "include_ui": "true"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["ui"]["status"], "available")
        self.assertEqual(payload["ui"]["platform_hint"], "desktop")

    @patch("src.api.init_ai")
    def test_image_analyze_can_attach_operator_assist_and_force_visual_context(self, mock_init_ai):
        """Operator assist should attach workspace/action guidance and force OCR/UI clues on."""
        (self.workspace_root / "AAIS-main" / "src").mkdir(exist_ok=True)
        (self.workspace_root / "AAIS-main" / "src" / "api.py").write_text(
            "@app.route('/api/chat/sessions/<session_id>/message')\n"
            "def chat_message(session_id):\n"
            "    raise RuntimeError('Traceback from screenshot')\n",
            encoding="utf-8",
        )

        fake_model = MagicMock()
        fake_model.analyze_image.return_value = {
            "description": "This looks like a code screenshot with traceback output.",
            "analysis_method": "clip-grounded-label-ranking",
            "top_matches": [{"label": "screenshot", "score": 0.66}],
            "dominant_colors": [{"hex": "#102132", "share": 0.44}],
            "image_size": {"width": 1440, "height": 900, "orientation": "landscape"},
            "image_features_shape": [1, 512],
            "ocr": {
                "status": "available",
                "summary": "OCR found traceback text in api.py.",
                "text_preview": "Traceback api.py line 2 chat_message",
            },
            "ui": {
                "status": "available",
                "surface_type": "code_screenshot",
                "platform_hint": "desktop",
                "code_language": "python",
                "layout_clues": ["editor", "stack trace"],
                "readable_targets": ["api.py", "chat_message", "Traceback"],
                "summary": "This most likely looks like a code screenshot on a desktop layout.",
            },
        }
        mock_init_ai.return_value = (fake_model, object())

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/analyze",
            data={
                "image": (buffer, "sample.png"),
                "include_operator_assist": "true",
                "operator_context": "debug the chat route in api.py",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("operator_assist", payload)
        self.assertEqual(payload["operator_assist"]["suggested_action"]["id"], "run_pytest")
        self.assertIsNotNone(payload["operator_assist"]["workspace_context"])
        self.assertTrue(payload["operator_assist"]["workspace_context"]["results"])
        self.assertTrue(
            payload["operator_assist"]["workspace_context"]["results"][0]["relative_path"].replace("/", "\\").endswith(
                "AAIS-main\\src\\api.py"
            )
        )
        fake_model.analyze_image.assert_called_once()
        _, kwargs = fake_model.analyze_image.call_args
        self.assertTrue(kwargs["include_ocr"])
        self.assertTrue(kwargs["include_ui"])

    @patch("src.api.document_vision.extract_document_text")
    def test_image_ocr_endpoint_reports_unavailable_document_vision(self, mock_extract):
        """Dedicated OCR route should return 503 when the OCR layer is unavailable."""
        mock_extract.side_effect = api.DocumentVisionUnavailable(
            "Document vision is disabled for this deployment"
        )

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/ocr",
            data={"image": (buffer, "sample.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("disabled", response.get_json()["error"])

    @patch("src.api.init_ai")
    def test_image_ui_analyze_route_returns_ui_payload(self, mock_init_ai):
        """Dedicated UI-analysis route should return the screenshot-understanding payload."""
        fake_model = MagicMock()
        fake_model.analyze_image.return_value = {
            "description": "This looks like a code screenshot in a dark theme.",
            "top_matches": [{"label": "code", "score": 0.62}],
            "ocr": {"status": "unavailable"},
            "ui": {
                "status": "available",
                "surface_type": "code_screenshot",
                "platform_hint": "desktop",
                "theme": "dark",
                "summary": "This most likely looks like a code screenshot on a desktop layout.",
            },
        }
        mock_init_ai.return_value = (fake_model, object())

        from PIL import Image

        image = Image.new("RGB", (16, 16), color=(255, 255, 255))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.client.post(
            "/api/image/ui-analyze",
            data={"image": (buffer, "sample.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["ui"]["surface_type"], "code_screenshot")


if __name__ == "__main__":
    unittest.main()
