"""Tests for OTEM execution → workflow approvals bridge."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.auth as auth
import app.db as db
import app.main as main
from src.jarvis_operator import JarvisOperator
from src.otem_execution_approval_bridge import (
    OTEM_EXECUTION_SHELL_WORKFLOW_ID,
    OTEM_EXECUTION_STEP_TYPE,
    ensure_otem_execution_shell_workflow,
    maybe_enqueue_otem_execution_approval,
    resolve_otem_execution_approval,
)
from src.otem_execution_substrate import get_otem_execution_substrate


class OtemExecutionApprovalBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_token = auth.APP_BEARER_TOKEN
        db.DB_PATH = Path(self.tempdir.name) / "otem-approval-bridge.db"
        auth.APP_BEARER_TOKEN = ""
        db.init_db()

    def tearDown(self):
        auth.APP_BEARER_TOKEN = self.original_token
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def _handoff_otem_result(self) -> dict:
        return {
            "status": "active",
            "restated_task": "Handle this operator task: design a daily brief workflow.",
            "task": "Use OTEM to design a daily brief workflow that emails the operator every morning.",
            "plan": [{"index": 1, "title": "Clarify", "status": "pending"}],
            "workflow_handoff": {
                "workflow_template_id": "daily-ai-brief",
                "template_name": "Daily AI Brief",
                "rationale": "Matches daily brief workflow shape.",
                "proposal_only": True,
            },
        }

    def test_ensure_shell_workflow_is_idempotent(self):
        first = ensure_otem_execution_shell_workflow()
        second = ensure_otem_execution_shell_workflow()
        self.assertEqual(first["id"], OTEM_EXECUTION_SHELL_WORKFLOW_ID)
        self.assertEqual(second["id"], OTEM_EXECUTION_SHELL_WORKFLOW_ID)

    def test_enqueue_and_dedupe_pending_approval(self):
        queue_meta = maybe_enqueue_otem_execution_approval("session-otem-1", self._handoff_otem_result())
        self.assertIsNotNone(queue_meta)
        self.assertEqual(queue_meta["status"], "pending")
        self.assertFalse(queue_meta.get("deduped"))

        queue_meta_2 = maybe_enqueue_otem_execution_approval("session-otem-1", self._handoff_otem_result())
        self.assertTrue(queue_meta_2.get("deduped"))
        self.assertEqual(queue_meta_2["approval_id"], queue_meta["approval_id"])

        pending = db.list_pending_workflow_approvals()
        otem_pending = [item for item in pending if item.get("step_type") == OTEM_EXECUTION_STEP_TYPE]
        self.assertEqual(len(otem_pending), 1)

    def test_resolve_approve_rejects_stale_substrate_after_restart(self):
        queue_meta = maybe_enqueue_otem_execution_approval("session-otem-stale", self._handoff_otem_result())
        approval = db.get_workflow_approval(queue_meta["approval_id"])
        substrate = get_otem_execution_substrate()
        substrate._workflows.pop(queue_meta["otem_execution_workflow_id"], None)

        with self.assertRaises(KeyError) as ctx:
            resolve_otem_execution_approval(approval, "approve")
        self.assertIn("stale after restart", str(ctx.exception))

    def test_resolve_approve_runs_substrate_through_ledger(self):
        queue_meta = maybe_enqueue_otem_execution_approval("session-otem-2", self._handoff_otem_result())
        approval = db.get_workflow_approval(queue_meta["approval_id"])
        self.assertIsNotNone(approval)

        result = resolve_otem_execution_approval(approval, "approve")
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["substrate"]["stage"], "ledger_record")

        run_record = db.get_workflow_run(queue_meta["workflow_run_id"])
        self.assertEqual(run_record["status"], "completed")

    def test_workflow_api_approve_otem_without_celery(self):
        queue_meta = maybe_enqueue_otem_execution_approval("session-otem-3", self._handoff_otem_result())
        prior_boot = os.environ.get("AAIS_GENOME_BOOT")
        os.environ["AAIS_GENOME_BOOT"] = "warn"
        try:
            with TestClient(main.app) as client, patch.object(main.run_workflow_job, "delay") as delay_mock:
                response = client.post(
                    f"/workflows/approvals/{queue_meta['approval_id']}",
                    json={"action": "approve"},
                )
                self.assertEqual(response.status_code, 200)
                delay_mock.assert_not_called()
        finally:
            if prior_boot is None:
                os.environ.pop("AAIS_GENOME_BOOT", None)
            else:
                os.environ["AAIS_GENOME_BOOT"] = prior_boot

        run_record = db.get_workflow_run(queue_meta["workflow_run_id"])
        self.assertEqual(run_record["status"], "completed")
        substrate = get_otem_execution_substrate()
        applied = substrate.get_workflow(queue_meta["otem_execution_workflow_id"])
        self.assertEqual(applied["stage"], "ledger_record")


class OtemOperatorEnqueueTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.tempdir.name) / "otem-operator-enqueue.db"
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_build_otem_turn_result_attaches_execution_approval_queue(self):
        operator = JarvisOperator()
        result = operator.build_otem_turn_result(
            "Use OTEM to design a daily brief workflow that emails the operator every morning.",
            session_id="session-handoff-enqueue",
        )
        self.assertIsNotNone(result.get("workflow_handoff"))
        queue_meta = result.get("execution_approval_queue")
        self.assertIsNotNone(queue_meta)
        self.assertEqual(queue_meta["status"], "pending")

        repeat = operator.build_otem_turn_result(
            "Use OTEM to design a daily brief workflow that emails the operator every morning.",
            session_id="session-handoff-enqueue",
            prior_state=result,
        )
        self.assertTrue(repeat.get("execution_approval_queue", {}).get("deduped"))
