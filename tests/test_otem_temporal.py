"""Unit tests for OTEM Temporal activities (no live Temporal server)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.db as db
from src.otem.execution import get_otem_execution_substrate, reset_otem_execution_substrate
from src.otem_temporal.activities import _substrate_apply, _substrate_approve


class OtemTemporalActivityTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.tempdir.name) / "otem-temporal-activities.db"
        db.init_db()
        reset_otem_execution_substrate()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()
        reset_otem_execution_substrate()

    def test_approve_and_apply_activity_helpers(self):
        substrate = get_otem_execution_substrate()
        record = substrate.create_proposal(
            {"summary": "Temporal activity test", "objective": "Verify approve/apply wrappers"},
            runtime_context="operator_runtime",
        )
        workflow_id = str(record["workflow_id"])

        approved = _substrate_approve(workflow_id)
        self.assertEqual(approved.get("stage"), "execution_preview")

        applied = _substrate_apply(workflow_id)
        self.assertEqual(applied.get("stage"), "ledger_record")


class OtemTemporalBridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.tempdir.name) / "otem-temporal-bridge.db"
        db.init_db()
        reset_otem_execution_substrate()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()
        reset_otem_execution_substrate()

    def _handoff_otem_result(self) -> dict:
        return {
            "status": "active",
            "restated_task": "Temporal bridge test",
            "task": "Run OTEM with Temporal orchestration",
            "plan": [{"index": 1, "title": "Step", "status": "pending"}],
            "workflow_handoff": {
                "workflow_template_id": "temporal-test",
                "template_name": "Temporal Test",
                "rationale": "Exercise temporal bridge wiring",
                "proposal_only": True,
            },
        }

    @patch("src.otem_execution_approval_bridge._maybe_start_temporal_workflow", return_value=True)
    @patch("src.otem_execution_approval_bridge._resolve_via_temporal")
    def test_resolve_approve_uses_temporal_when_flagged(self, mock_resolve, _mock_start):
        from src.otem_execution_approval_bridge import (
            maybe_enqueue_otem_execution_approval,
            resolve_otem_execution_approval,
        )

        mock_resolve.return_value = {
            "status": "approved",
            "substrate_approved": {"stage": "operator_approval"},
            "substrate": {"stage": "ledger_record", "apply_result": {"message": "ok"}},
        }

        queue_meta = maybe_enqueue_otem_execution_approval("session-temporal", self._handoff_otem_result())
        approval = db.get_workflow_approval(queue_meta["approval_id"])
        payload = dict(approval.get("payload") or {})
        payload["temporal_orchestrated"] = True
        with db.get_conn() as conn:
            conn.execute(
                "UPDATE workflow_approvals SET payload_json = ? WHERE id = ?",
                (json.dumps(payload), approval["id"]),
            )
        approval = db.get_workflow_approval(queue_meta["approval_id"])

        result = resolve_otem_execution_approval(approval, "approve")
        self.assertEqual(result["status"], "approved")
        mock_resolve.assert_called_once_with(queue_meta["otem_execution_workflow_id"], "approve")


if __name__ == "__main__":
    unittest.main()
