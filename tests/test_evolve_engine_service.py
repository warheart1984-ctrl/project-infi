"""Tests for the isolated EvolveEngine boundary."""

from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from evolve_engine.main import app
from evolve_engine.service import EvolveEngineService
from src.evolve_client import EvolveClient


RUNTIME_ROOT = Path.cwd() / ".runtime" / "pytest-temp"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def _make_runtime_dir(prefix: str) -> Path:
    target = RUNTIME_ROOT / f"{prefix}-{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    return target


class _FakeEvaluator:
    def __init__(self):
        self.calls = []

    def evaluate_candidate(self, *, job_id, generation_index, individual_index, request, candidate):
        self.calls.append((job_id, generation_index, individual_index, candidate))
        score = 1.0 if "winner" in candidate.lower() else 0.1
        ok = "broken" not in candidate.lower()
        if not ok:
            return {
                "ok": False,
                "task_id": f"{job_id}-g{generation_index}-i{individual_index}",
                "mode": request.evaluation.forge_eval_mode,
                "error": {"code": "sandbox_error", "message": "candidate crashed"},
            }
        return {
            "ok": True,
            "task_id": f"{job_id}-g{generation_index}-i{individual_index}",
            "mode": request.evaluation.forge_eval_mode,
            "result": {
                "score": score,
                "details": {"candidate_length": len(candidate)},
            },
        }


class _SelectiveEvaluator:
    def __init__(self):
        self.calls = []

    def evaluate_candidate(self, *, job_id, generation_index, individual_index, request, candidate):
        self.calls.append((job_id, generation_index, individual_index, candidate))
        lowered = candidate.lower()
        if "bad-parent-marker" in lowered:
            return {
                "ok": False,
                "task_id": f"{job_id}-g{generation_index}-i{individual_index}",
                "mode": request.evaluation.forge_eval_mode,
                "error": {"code": "candidate_rejected", "message": "invalid parent lineage"},
            }
        score = 1.0 if "winner" in lowered or "good-parent" in lowered else 0.3
        return {
            "ok": True,
            "task_id": f"{job_id}-g{generation_index}-i{individual_index}",
            "mode": request.evaluation.forge_eval_mode,
            "result": {
                "score": score,
                "details": {"candidate_length": len(candidate)},
            },
        }


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


class TestEvolveEngineService(unittest.TestCase):
    """Verify the isolated evolve service behavior."""

    def test_evolve_records_history_and_mutation_halls(self):
        tmp_dir = _make_runtime_dir("evolve-engine")
        try:
            service = EvolveEngineService(
                storage_root=tmp_dir,
                evaluator=_FakeEvaluator(),
            )
            result, status_code = service.evolve(
                {
                    "job_id": "evolve-job-1",
                    "jarvis_run_id": "jarvis-run-1",
                    "task": "Evolve this candidate",
                    "config": {
                        "seed_candidates": ["winner candidate", "broken candidate"],
                    },
                    "evaluation": {
                        "mode": "forge_eval",
                        "forge_eval_mode": "llm_rubric",
                        "candidate_field": "program",
                        "payload": {"config": {"criteria": ["winner"]}},
                        "success_threshold": 0.9,
                        "failure_threshold": 0.2,
                    },
                    "constraints": {
                        "population_size": 2,
                        "max_generations": 2,
                        "max_evaluations": 4,
                    },
                }
            )

            self.assertEqual(status_code, 200)
            self.assertTrue(result.ok)
            self.assertGreaterEqual(result.result.best_score, 1.0)
            self.assertGreaterEqual(result.result.hall_of_fame_count, 1)
            self.assertGreaterEqual(result.result.hall_of_shame_count, 1)
            self.assertEqual(result.law_enforcement["contract_version"], "aais.evolve.ul.v1")
            self.assertEqual(result.law_enforcement["origin_integrity"]["admission_status"], "evaluation_only")
            self.assertTrue(result.law_enforcement["adaptation_constraints"]["requires_forge_approval"])
            self.assertGreaterEqual(result.ul_snapshot["count"], 1)

            trace = service.get_job_trace("evolve-job-1")
            self.assertIsNotNone(trace)
            self.assertEqual(trace["job"]["jarvis_run_id"], "jarvis-run-1")
            self.assertGreaterEqual(len(trace["history"]), 1)
            self.assertGreaterEqual(len(trace["decisions"]), 2)
            self.assertEqual(trace["violations"], [])
            self.assertGreaterEqual(len(trace["hall_of_fame"]), 1)
            self.assertGreaterEqual(len(trace["hall_of_shame"]), 1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_service_route_returns_success_payload(self):
        tmp_dir = _make_runtime_dir("evolve-route")
        try:
            service = EvolveEngineService(
                storage_root=tmp_dir,
                evaluator=_FakeEvaluator(),
            )

            import evolve_engine.main as evolve_main

            original_service = evolve_main.evolve_engine_service
            evolve_main.evolve_engine_service = service
            try:
                with app.test_client() as client:
                    response = client.post(
                        "/evolve",
                        json={
                            "job_id": "evolve-job-2",
                            "task": "Evolve this candidate",
                            "config": {"seed_candidates": ["winner candidate"]},
                            "evaluation": {
                                "mode": "forge_eval",
                                "forge_eval_mode": "llm_rubric",
                                "payload": {"config": {"criteria": ["winner"]}},
                                "candidate_field": "program",
                            },
                        },
                    )
            finally:
                evolve_main.evolve_engine_service = original_service

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()["ok"])
            self.assertEqual(response.get_json()["job_id"], "evolve-job-2")
            self.assertIn("law_enforcement", response.get_json())
            self.assertIn("ul_snapshot", response.get_json())
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_invalid_strategy_is_rejected_as_law_violation(self):
        tmp_dir = _make_runtime_dir("evolve-law-block")
        try:
            service = EvolveEngineService(
                storage_root=tmp_dir,
                evaluator=_FakeEvaluator(),
            )

            result, status_code = service.evolve(
                {
                    "job_id": "evolve-job-law-block",
                    "task": "Try an invalid execution mode",
                    "config": {
                        "strategy": "remote_autonomy",
                        "seed_candidates": ["winner candidate"],
                    },
                    "evaluation": {
                        "mode": "forge_eval",
                        "forge_eval_mode": "llm_rubric",
                        "candidate_field": "program",
                        "payload": {"config": {"criteria": ["winner"]}},
                    },
                }
            )

            self.assertEqual(status_code, 400)
            self.assertFalse(result.ok)
            self.assertEqual(result.error.code, "law_violation")
            self.assertTrue(result.law_enforcement["violation_state"]["violation_recorded"])
            self.assertEqual(
                result.law_enforcement["violation_state"]["blocking_law_id"],
                "law_2_execution_governance",
            )

            trace = service.get_job_trace("evolve-job-law-block")
            self.assertIsNotNone(trace)
            self.assertEqual(trace["job"]["status"], "law_blocked")
            self.assertEqual(len(trace["violations"]), 1)
            self.assertEqual(trace["violations"][0]["law_id"], "law_2_execution_governance")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_adaptation_only_uses_validated_parent_pool(self):
        tmp_dir = _make_runtime_dir("evolve-adaptation")
        try:
            service = EvolveEngineService(
                storage_root=tmp_dir,
                evaluator=_SelectiveEvaluator(),
            )

            result, status_code = service.evolve(
                {
                    "job_id": "evolve-job-validated-parents",
                    "task": "good-parent winner goal",
                    "config": {
                        "seed_candidates": ["good-parent winner", "bad-parent-marker"],
                    },
                    "evaluation": {
                        "mode": "forge_eval",
                        "forge_eval_mode": "llm_rubric",
                        "candidate_field": "program",
                        "payload": {"config": {"criteria": ["winner"]}},
                    },
                    "constraints": {
                        "population_size": 4,
                        "max_generations": 2,
                        "max_evaluations": 8,
                    },
                }
            )

            self.assertEqual(status_code, 200)
            self.assertTrue(result.ok)
            self.assertGreaterEqual(result.result.validated_outcomes, 1)

            evaluations = service.get_job_evaluations("evolve-job-validated-parents")["evaluations"]
            generation_one = [item for item in evaluations if item["generation_index"] == 1]
            self.assertGreaterEqual(len(generation_one), 1)
            self.assertTrue(
                all("bad-parent-marker" not in item["candidate"].lower() for item in generation_one)
            )

            trace = service.get_job_trace("evolve-job-validated-parents")
            adaptation_decisions = [
                item for item in trace["decisions"] if item["phase"] == "adaptation_parent_pool"
            ]
            self.assertGreaterEqual(len(adaptation_decisions), 1)
            self.assertEqual(
                adaptation_decisions[0]["payload"]["selection_rule"],
                "validated_outcomes_only",
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class TestEvolveClient(unittest.TestCase):
    """Verify the AAIS-side evolve client."""

    def test_client_posts_request_and_normalizes_response(self):
        session = _FakeSession(
            post_response=_FakeResponse(
                200,
                {
                    "ok": True,
                    "job_id": "evolve-job-3",
                    "task": "Improve it",
                    "result": {
                        "best_score": 0.95,
                        "best_genome": {"candidate": "winner", "candidate_field": "program"},
                        "best_program": "winner",
                        "generations_run": 2,
                        "evaluations": 4,
                        "validated_outcomes": 4,
                        "history": [],
                        "hall_of_fame_count": 2,
                        "hall_of_shame_count": 1,
                    },
                    "law_enforcement": {"contract_version": "aais.evolve.ul.v1"},
                    "ul_snapshot": {"count": 2, "sections": ["runtime_context"]},
                },
            )
        )
        client = EvolveClient(base_url="http://evolve.local", session=session, timeout_seconds=12)

        result = client.evolve(
            task="Improve it",
            job_id="evolve-job-3",
            config={"seed_candidates": ["winner"]},
            evaluation={
                "mode": "forge_eval",
                "forge_eval_mode": "llm_rubric",
                "payload": {"config": {"criteria": ["winner"]}},
                "candidate_field": "program",
            },
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["job_id"], "evolve-job-3")
        self.assertEqual(session.posts[0][0], "http://evolve.local/evolve")
        self.assertEqual(result["law_enforcement"]["contract_version"], "aais.evolve.ul.v1")
        self.assertEqual(result["result"]["validated_outcomes"], 4)
