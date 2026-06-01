"""Tests for the isolated ForgeEval boundary."""

from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from forge_eval.main import app
from forge_eval.service import ForgeEvalService
from src.forge_eval_client import ForgeEvalClient


RUNTIME_ROOT = Path.cwd() / ".runtime" / "pytest-temp"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def _make_runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    return target


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


class TestForgeEvalService(unittest.TestCase):
    """Verify the evaluator service behavior."""

    def test_io_tests_contract_success(self):
        tmp_dir = _make_runtime_dir("forge-eval")
        try:
            service = ForgeEvalService(storage_root=tmp_dir)
            result, status_code = service.evaluate(
                {
                    "task_id": "eval-1",
                    "mode": "io_tests",
                    "payload": {
                        "program": "def add(a, b):\n    return a + b\n",
                        "config": {"must_contain": ["return a + b"]},
                    },
                }
            )

            self.assertEqual(status_code, 200)
            self.assertTrue(result.ok)
            self.assertGreaterEqual(result.result.score, 1.0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_repo_patch_requires_existing_repo(self):
        tmp_dir = _make_runtime_dir("forge-eval")
        try:
            service = ForgeEvalService(storage_root=tmp_dir)
            result, status_code = service.evaluate(
                {
                    "task_id": "eval-2",
                    "mode": "repo_patch",
                    "payload": {
                        "patch": "diff --git a/src/api.py b/src/api.py",
                        "repo": str(Path(tmp_dir) / "missing"),
                    },
                }
            )

            self.assertEqual(status_code, 503)
            self.assertFalse(result.ok)
            self.assertEqual(result.error.code, "sandbox_error")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_service_route_returns_success_payload(self):
        tmp_dir = _make_runtime_dir("forge-eval")
        try:
            service = ForgeEvalService(storage_root=tmp_dir)

            import forge_eval.main as forge_eval_main

            original_service = forge_eval_main.forge_eval_service
            forge_eval_main.forge_eval_service = service
            try:
                with app.test_client() as client:
                    response = client.post(
                        "/evaluate",
                        json={
                            "task_id": "eval-3",
                            "mode": "llm_rubric",
                            "payload": {
                                "program": "clear structure and goal coverage",
                                "config": {"criteria": ["clear structure", "goal coverage"]},
                            },
                        },
                    )
            finally:
                forge_eval_main.forge_eval_service = original_service

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()["ok"])
            self.assertEqual(response.get_json()["mode"], "llm_rubric")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestForgeEvalClient(unittest.TestCase):
    """Verify the AAIS-side evaluator client."""

    def test_client_posts_request_and_normalizes_response(self):
        session = _FakeSession(
            post_response=_FakeResponse(
                200,
                {
                    "ok": True,
                    "task_id": "eval-4",
                    "mode": "io_tests",
                    "result": {"score": 1.0, "details": {"passed": 1, "total": 1}},
                },
            )
        )
        client = ForgeEvalClient(base_url="http://forge-eval.local", session=session, timeout_seconds=12)

        result = client.evaluate(
            mode="io_tests",
            task_id="eval-4",
            payload={"program": "print('ok')", "config": {"must_contain": ["ok"]}},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "io_tests")
        self.assertEqual(session.posts[0][0], "http://forge-eval.local/evaluate")
