"""Tests for the isolated Forge contractor boundary."""

from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from forge.config import ForgeConfig
from forge.main import app
from forge.preflight import ForgePreflightError, sanitize_context
from forge.service import ForgeService
from src.forge_client import ForgeClient, auto_approve_forge_result


RUNTIME_ROOT = Path.cwd() / ".runtime" / "pytest-temp"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def _make_runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    return target


class _FakeCaller:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        raw, trace_id = self.responses.pop(0)
        return raw, trace_id


class _FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class _FakeSession:
    def __init__(self, *, post_response=None, get_response=None):
        self.post_response = post_response
        self.get_response = get_response
        self.posts = []
        self.gets = []

    def post(self, url, json, timeout):
        self.posts.append((url, json, timeout))
        return self.post_response

    def get(self, url, timeout):
        self.gets.append((url, timeout))
        return self.get_response


class TestForgePreflight(unittest.TestCase):
    """Verify request preflight keeps Forge bounded and task-local."""

    def test_sanitize_context_filters_extensions_and_truncates_large_files(self):
        huge_python = "print('x')\n" * 50_000

        context = sanitize_context(
            {
                "goal": "Refactor api.py",
                "files": [
                    {"path": "src/api.py", "content": huge_python},
                    {"path": "notes.exe", "content": "skip me"},
                ],
                "constraints": {
                    "language": "python",
                    "requirements": ["keep behavior", 123],
                },
            }
        )

        self.assertEqual(context.goal, "Refactor api.py")
        self.assertEqual(len(context.files), 1)
        self.assertEqual(context.files[0].path, "src/api.py")
        self.assertTrue(context.files[0].truncated)
        self.assertEqual(context.constraints["language"], "python")
        self.assertEqual(context.constraints["requirements"], ["keep behavior", 123])

    def test_sanitize_context_rejects_blocked_keys(self):
        with self.assertRaisesRegex(ForgePreflightError, "Blocked context keys"):
            sanitize_context(
                {
                    "goal": "Refactor api.py",
                    "files": [{"path": "src/api.py", "content": "def ok():\n    pass\n"}],
                    "memory": {"prompt": "do not send"},
                }
            )


class TestForgeService(unittest.TestCase):
    """Verify the isolated Forge runtime behavior."""

    def _build_config(self, storage_root: Path) -> ForgeConfig:
        return ForgeConfig(
            host="127.0.0.1",
            port=6060,
            storage_root=storage_root,
            model="claude-test",
            api_key="test-key",
            api_url="https://example.invalid/messages",
            anthropic_version="2023-06-01",
            timeout_ms=5000,
            max_retries=1,
            max_tokens=1500,
            default_output_chars=20000,
            trace_enabled=False,
        )

    def test_contractor_retries_invalid_json_then_returns_valid_payload(self):
        tmp_dir = _make_runtime_dir("forge-service")
        try:
            caller = _FakeCaller(
                [
                    ("not json", "trace-invalid"),
                    (
                        """{
                          "diffs": [
                            {
                              "path": "src/api.py",
                              "unified_diff": "diff --git a/src/api.py b/src/api.py"
                            }
                          ]
                        }""",
                        "trace-valid",
                    ),
                ]
            )
            service = ForgeService(
                config=self._build_config(Path(tmp_dir)),
                model_caller=caller,
            )

            result, status_code, trace_id = service.handle_contractor_request(
                {
                    "task_id": "forge-task-1",
                    "kind": "generate_diff",
                    "context": {
                        "goal": "Refactor the route for clarity",
                        "constraints": {"language": "python"},
                        "files": [
                            {
                                "path": "src/api.py",
                                "content": "def chat_message():\n    return {'status': 'ok'}\n",
                            }
                        ],
                    },
                }
            )

            self.assertEqual(status_code, 200)
            self.assertTrue(result.ok)
            self.assertEqual(result.kind, "generate_diff")
            self.assertEqual(result.result.diffs[0].path, "src/api.py")
            self.assertEqual(result.law_enforcement["contract_version"], "aais.forge.ul.v1")
            self.assertTrue(result.law_enforcement["origin_integrity"]["forge_processed"])
            self.assertEqual(
                result.law_enforcement["execution_governance"]["action_permission_check"],
                "review_only_handoff_required",
            )
            self.assertGreaterEqual(result.ul_snapshot["count"], 1)
            self.assertEqual(trace_id, "trace-valid")
            self.assertEqual(len(caller.calls), 2)
            self.assertTrue((tmp_dir / "traces" / "trace-valid.json").exists())
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_service_route_returns_trace_header(self):
        tmp_dir = _make_runtime_dir("forge-route")
        try:
            service = ForgeService(
                config=self._build_config(tmp_dir),
                model_caller=_FakeCaller(
                    [
                        (
                            """{
                              "analysis": {
                                "summary": "Nothing to change yet.",
                                "issues": [],
                                "notes": "No action."
                              }
                            }""",
                            "trace-analysis",
                        )
                    ]
                ),
            )

            import forge.main as forge_main

            original_service = forge_main.forge_service
            forge_main.forge_service = service
            try:
                with app.test_client() as client:
                    response = client.post(
                        "/contractor",
                        json={
                            "task_id": "forge-task-2",
                            "kind": "analyze",
                            "context": {
                                "goal": "Analyze this file",
                                "files": [
                                    {"path": "src/api.py", "content": "def ok():\n    return True\n"}
                                ],
                            },
                        },
                    )
            finally:
                forge_main.forge_service = original_service

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["X-Forge-Trace-Id"], "trace-analysis")
            self.assertTrue(response.get_json()["ok"])
            self.assertEqual(response.get_json()["kind"], "analyze")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_disabling_review_gate_is_blocked_as_law_violation(self):
        tmp_dir = _make_runtime_dir("forge-law-block")
        try:
            caller = _FakeCaller([])
            service = ForgeService(
                config=self._build_config(tmp_dir),
                model_caller=caller,
            )

            result, status_code, trace_id = service.handle_contractor_request(
                {
                    "task_id": "forge-task-blocked",
                    "kind": "generate_diff",
                    "context": {
                        "goal": "Try to bypass the review gate",
                        "no_execution_without_handoff": False,
                        "files": [
                            {
                                "path": "src/api.py",
                                "content": "def route():\n    return {'ok': True}\n",
                            }
                        ],
                    },
                }
            )

            self.assertEqual(status_code, 400)
            self.assertFalse(result.ok)
            self.assertEqual(result.error.code, "law_violation")
            self.assertEqual(result.law_enforcement["contract_version"], "aais.forge.ul.v1")
            self.assertTrue(result.law_enforcement["violation_state"]["violation_recorded"])
            self.assertEqual(
                result.law_enforcement["violation_state"]["blocking_law_id"],
                "law_2_execution_governance",
            )
            self.assertEqual(result.law_enforcement["violation_state"]["containment_state"], "contained")
            self.assertIsNotNone(trace_id)
            self.assertEqual(len(caller.calls), 0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_repo_manager_kind_uses_codex_pair_profile_and_returns_repo_plan(self):
        tmp_dir = _make_runtime_dir("forge-repo-manager")
        try:
            caller = _FakeCaller(
                [
                    (
                        """{
                          "repo_manager": {
                            "repo_summary": "The repo slice centers on api routing and evolve integration.",
                            "target_scope": "evolve + forge boundary only",
                            "focus_files": ["src/api.py", "evolve_engine/service.py"],
                            "risks": [
                              {
                                "file": "src/api.py",
                                "issue": "Potential contract drift between service and client.",
                                "evidence": "The route and isolated service carry overlapping Forge response fields.",
                                "confidence": "medium"
                              }
                            ],
                            "plan": [
                              {
                                "step": "Inspect the request/response contract.",
                                "file": "src/api.py",
                                "purpose": "Confirm what AAIS expects from Forge.",
                                "expected_effect": "Pin down the narrowest mismatch before any edit.",
                                "rollback_note": "No file changes at this stage.",
                                "validation": "Compare the isolated service contract and the AAIS route."
                              }
                            ],
                            "validations": ["Run evolve API tests", "Check trace payload shape"],
                            "execution_ready": true
                          }
                        }""",
                        "trace-repo-manager",
                    )
                ]
            )
            service = ForgeService(
                config=self._build_config(tmp_dir),
                model_caller=caller,
            )

            result, status_code, trace_id = service.handle_contractor_request(
                {
                    "task_id": "forge-task-repo",
                    "kind": "repo_manager",
                    "context": {
                        "goal": "Manage this repo slice like a careful pair engineer",
                        "constraints": {"language": "python"},
                        "target_scope": "evolve + forge boundary only",
                        "focus_files": ["src/api.py", "evolve_engine/service.py"],
                        "excluded_files": ["frontend/src/App.jsx"],
                        "change_intent": "review_only",
                        "max_change_budget": "one narrow backend seam",
                        "files": [
                            {
                                "path": "src/api.py",
                                "content": "def route():\n    return {'ok': True}\n",
                            }
                        ],
                    },
                }
            )

            self.assertEqual(status_code, 200)
            self.assertTrue(result.ok)
            self.assertEqual(result.kind, "repo_manager")
            self.assertEqual(result.result.repo_manager.focus_files[0], "src/api.py")
            self.assertEqual(result.result.repo_manager.plan[0].step, "Inspect the request/response contract.")
            self.assertFalse(result.result.repo_manager.execution_ready)
            self.assertEqual(result.law_enforcement["contract_version"], "aais.forge.ul.v1")
            self.assertEqual(result.law_enforcement["violation_state"]["containment_state"], "review_only_handoff")
            self.assertEqual(trace_id, "trace-repo-manager")
            self.assertIn("Active contractor profile: `codex_pair`.", caller.calls[0][0])
            self.assertIn("reliable senior pair-programming contractor", caller.calls[0][0])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestForgeClient(unittest.TestCase):
    """Verify the AAIS-side client normalizes Forge responses correctly."""

    def test_client_posts_request_and_normalizes_response(self):
        session = _FakeSession(
            post_response=_FakeResponse(
                200,
                {
                    "ok": True,
                    "task_id": "forge-task-3",
                    "kind": "generate_code",
                    "result": {
                        "files": [
                            {
                                "path": "src/api.py",
                                "content": "def chat_message():\n    return {'status': 'ok'}\n",
                            }
                        ]
                    },
                },
            )
        )
        client = ForgeClient(base_url="http://forge.local", session=session, timeout_seconds=12)

        result = client.request(
            kind="generate_code",
            task_id="forge-task-3",
            context={
                "goal": "Create the route",
                "constraints": {"language": "python"},
                "files": [],
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "generate_code")
        self.assertEqual(result["result"]["files"][0]["path"], "src/api.py")
        self.assertEqual(session.posts[0][0], "http://forge.local/contractor")
        self.assertFalse(auto_approve_forge_result(result))

    def test_client_accepts_repo_manager_kind(self):
        session = _FakeSession(
            post_response=_FakeResponse(
                200,
                {
                    "ok": True,
                    "task_id": "forge-task-4",
                    "kind": "repo_manager",
                    "result": {
                        "repo_manager": {
                            "repo_summary": "Repo manager summary",
                            "target_scope": "api route only",
                            "focus_files": ["src/api.py"],
                            "risks": [
                                {
                                    "file": "src/api.py",
                                    "issue": "One contract mismatch",
                                    "evidence": "The route exposes a field the isolated service does not document.",
                                    "confidence": "medium"
                                }
                            ],
                            "plan": [
                                {
                                    "step": "Read the route first",
                                    "file": "src/api.py",
                                    "purpose": "Confirm current behavior",
                                    "expected_effect": "Clarify the smallest safe fix",
                                    "rollback_note": "None yet",
                                    "validation": "Compare route payload and contract docs"
                                }
                            ],
                            "validations": ["Run targeted tests"],
                            "execution_ready": False
                        }
                    },
                },
            )
        )
        client = ForgeClient(base_url="http://forge.local", session=session, timeout_seconds=12)

        result = client.request(
            kind="repo_manager",
            task_id="forge-task-4",
            context={
                "goal": "Manage the repo slice",
                "constraints": {"language": "python"},
                "target_scope": "api route only",
                "focus_files": ["src/api.py"],
                "excluded_files": [],
                "change_intent": "review_only",
                "max_change_budget": "single route adjustment",
                "files": [],
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["kind"], "repo_manager")
        self.assertEqual(result["result"]["repo_manager"]["focus_files"], ["src/api.py"])
        self.assertFalse(result["result"]["repo_manager"]["execution_ready"])

    def test_client_health_raises_when_service_is_unavailable(self):
        session = _FakeSession(get_response=_FakeResponse(503, {"detail": "offline"}, "offline"))
        client = ForgeClient(base_url="http://forge.local", session=session, timeout_seconds=5)

        with self.assertRaisesRegex(RuntimeError, "Forge contractor unavailable"):
            client.health()
