"""Tests for workflow chain executor."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.workflow_chain_executor import WorkflowChainExecutor


class WorkflowChainExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.executor = WorkflowChainExecutor(runtime_dir=Path(self.tempdir.name))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_execute_blocked_without_operator_approval(self):
        result = self.executor.execute("research_brief", operator_approved=False)
        self.assertEqual(result["outcome"], "blocked")

    def test_execute_dry_run_with_approval(self):
        with patch("src.workflow_chain_executor.plug_adapter_runtime") as mock_runtime:
            mock_runtime.execute_plug.return_value = {"outcome": "ok", "dry_run": True}
            result = self.executor.execute(
                "research_brief",
                operator_approved=True,
                dry_run=True,
                args={"session_id": "test-session"},
            )
        self.assertIn("run_id", result)
        self.assertEqual(result["workflow_id"], "research_brief")
        self.assertEqual(result["status"], "completed")

    def test_get_run_round_trip(self):
        with patch("src.workflow_chain_executor.plug_adapter_runtime") as mock_runtime:
            mock_runtime.execute_plug.return_value = {"outcome": "ok"}
            run = self.executor.execute("research_brief", operator_approved=True, dry_run=True)
        fetched = self.executor.get_run("research_brief", run["run_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["run_id"], run["run_id"])

    def test_not_found_workflow(self):
        result = self.executor.execute("nonexistent_workflow_xyz", operator_approved=True)
        self.assertEqual(result["outcome"], "not_found")
