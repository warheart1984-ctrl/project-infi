import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.auth as auth
import app.db as db
import app.workflow_runtime as workflow_runtime
from app.workflow_recovery import sweep_workflow_runs
from app.workflow_runtime import execute_queued_workflow_run
from app.workflow_validation import WorkflowValidationError, build_workflow_config_from_graph
from src.project_infi_law import PROJECT_INFI_CONTRACT_VERSION


try:
    import celery  # type: ignore  # pragma: no cover
except ModuleNotFoundError:  # pragma: no cover
    fake_celery_module = types.ModuleType("celery")

    class FakeTask:
        def __init__(self, fn):
            self.fn = fn
            self.delay = lambda *args, **kwargs: None

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

    class FakeCelery:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self.conf = types.SimpleNamespace(task_track_started=False, result_expires=None)

        def task(self, name=None):
            def decorator(fn):
                task = FakeTask(fn)
                task.name = name or fn.__name__
                return task

            return decorator

    fake_celery_module.Celery = FakeCelery
    sys.modules["celery"] = fake_celery_module

import app.main as main


def assert_project_infi_payload(testcase: unittest.TestCase, payload: dict) -> None:
    testcase.assertIn("law_enforcement", payload)
    testcase.assertIn("ul_snapshot", payload)
    testcase.assertIn("law_event_log", payload)
    testcase.assertEqual(payload["law_enforcement"]["contract_version"], PROJECT_INFI_CONTRACT_VERSION)
    testcase.assertEqual(payload["law_enforcement"]["source_of_truth"], "project_infi_law")
    testcase.assertEqual(payload["law_enforcement"]["execution_governance"]["authoritative_controller"], "project_infi_law")


def make_nodes(include_invalid_action=False):
    action_subtype = "unsupported.action" if include_invalid_action else "task.create"
    return [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {
                "label": "Incoming Trigger",
                "kind": "trigger",
                "subtype": "manual",
                "config": {},
            },
        },
        {
            "id": "step-1",
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": "Create Task",
                "kind": "action",
                "subtype": action_subtype,
                "config": {"title": "One"},
            },
        },
        {
            "id": "step-2",
            "type": "actionNode",
            "position": {"x": 700, "y": 140},
            "data": {
                "label": "Create Follow Up",
                "kind": "action",
                "subtype": "task.create",
                "config": {"title": "Two"},
            },
        },
    ]


def make_edges():
    return [
        {"id": "e1", "source": "trigger-1", "target": "step-1", "sourceHandle": None},
        {"id": "e2", "source": "step-1", "target": "step-2", "sourceHandle": None},
    ]


def make_webhook_nodes(secret="hook-secret", delay_ms="0"):
    return [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {
                "label": "Incoming Webhook",
                "kind": "trigger",
                "subtype": "webhook.received",
                "config": {"source": "partner-system", "secret": secret},
            },
        },
        {
            "id": "step-1",
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": "Summarize Event",
                "kind": "action",
                "subtype": "ai.analyze",
                "config": {"goal": "Summarize the event", "mode": "fake"},
            },
        },
        {
            "id": "step-2",
            "type": "actionNode",
            "position": {"x": 700, "y": 140},
            "data": {
                "label": "Prepare Slack Alert",
                "kind": "action",
                "subtype": "slack.send",
                "config": {
                    "channel": "#alerts",
                    "deliveryMode": "fake",
                    "simulateDelayMs": delay_ms,
                },
            },
        },
    ]


def make_failing_recovery_nodes():
    return [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {
                "label": "Incoming Trigger",
                "kind": "trigger",
                "subtype": "manual",
                "config": {},
            },
        },
        {
            "id": "step-1",
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": "Create Task",
                "kind": "action",
                "subtype": "task.create",
                "config": {"title": "One"},
            },
        },
        {
            "id": "step-2",
            "type": "actionNode",
            "position": {"x": 700, "y": 140},
            "data": {
                "label": "Broken API",
                "kind": "action",
                "subtype": "api.call",
                "config": {},
            },
        },
    ]


class WorkflowHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_token = auth.APP_BEARER_TOKEN
        db.DB_PATH = Path(self.tempdir.name) / "workflow-tests.db"
        auth.APP_BEARER_TOKEN = ""
        db.init_db()

    def tearDown(self):
        auth.APP_BEARER_TOKEN = self.original_token
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_graph_validation_rejects_common_bad_shapes(self):
        base_nodes = make_nodes()
        base_edges = make_edges()

        cases = [
            (
                "missing trigger",
                base_nodes[1:],
                base_edges[1:],
                "exactly one trigger",
            ),
            (
                "duplicate ids",
                [
                    base_nodes[0],
                    {**base_nodes[1], "id": "step-dup"},
                    {**base_nodes[2], "id": "step-dup"},
                ],
                base_edges,
                "ids must be unique",
            ),
            (
                "dangling edge",
                base_nodes,
                [
                    {"id": "e1", "source": "trigger-1", "target": "missing-step", "sourceHandle": None},
                ],
                "must point to nodes that exist",
            ),
            (
                "cycle",
                base_nodes,
                [
                    {"id": "e1", "source": "trigger-1", "target": "step-1", "sourceHandle": None},
                    {"id": "e2", "source": "step-1", "target": "step-2", "sourceHandle": None},
                    {"id": "e3", "source": "step-2", "target": "step-1", "sourceHandle": None},
                ],
                "cycle",
            ),
            (
                "unreachable node",
                base_nodes,
                [
                    {"id": "e1", "source": "trigger-1", "target": "step-1", "sourceHandle": None},
                ],
                "Connect all steps",
            ),
            (
                "invalid step type",
                make_nodes(include_invalid_action=True),
                base_edges,
                "Unsupported action type",
            ),
        ]

        for label, nodes, edges, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(WorkflowValidationError, message):
                    build_workflow_config_from_graph("Bad Workflow", nodes, edges)

    def test_run_route_marks_run_failed_when_enqueue_breaks(self):
        config = build_workflow_config_from_graph("Queue Failure Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Queue Failure Workflow", make_nodes(), make_edges(), config)

        with TestClient(main.app) as client, patch.object(
            main.run_workflow_job,
            "delay",
            side_effect=RuntimeError("broker offline"),
        ):
            response = client.post(
                "/workflows/run",
                json={"id": workflow["id"], "trigger_data": {"text": "manual run"}},
            )

        self.assertEqual(response.status_code, 503)
        runs = db.list_workflow_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "failed")
        self.assertEqual(runs[0]["output"]["message"], "Workflow queue failed")

    def test_step_failure_preserves_partial_progress(self):
        config = {
            "schemaVersion": 1,
            "name": "Partial Progress Workflow",
            "trigger": {"id": "trigger-1", "type": "manual", "label": "Manual", "config": {}},
            "steps": [
                {"id": "step-1", "order": 1, "type": "task.create", "label": "Create Task", "config": {"title": "One"}},
                {"id": "step-2", "order": 2, "type": "api.call", "label": "Broken API", "config": {}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger-1", "target": "step-1", "sourceHandle": None},
                {"id": "e2", "source": "step-1", "target": "step-2", "sourceHandle": None},
            ],
        }
        workflow = db.create_workflow("Partial Progress Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "queued", {"message": "queued"})
        approval = db.create_workflow_approval(
            workflow_run_id=run["id"],
            workflow_id=workflow["id"],
            step_id="step-2",
            step_label="Broken API",
            step_type="api.call",
            reason="Pre-approved for failure test",
            payload={"step": {"id": "step-2"}},
        )
        db.update_workflow_approval(approval["id"], "approved")

        with self.assertRaisesRegex(RuntimeError, "missing config.url"):
            execute_queued_workflow_run(run["id"], workflow["id"], {"text": "hello"})

        saved_run = db.get_workflow_run(run["id"])
        self.assertEqual(saved_run["status"], "failed")
        self.assertEqual(len(saved_run["output"]["steps"]), 1)
        self.assertEqual(saved_run["output"]["steps"][0]["label"], "Create Task")
        self.assertEqual(saved_run["output"]["plannedSteps"][1]["status"], "failed")

    def test_duplicate_worker_pickup_does_not_duplicate_steps(self):
        config = build_workflow_config_from_graph("Duplicate Pickup Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Duplicate Pickup Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "queued", {"message": "queued"})

        execute_queued_workflow_run(run["id"], workflow["id"], {"text": "hello"})
        first_result = db.get_workflow_run(run["id"])
        execute_queued_workflow_run(run["id"], workflow["id"], {"text": "hello"})
        second_result = db.get_workflow_run(run["id"])

        self.assertEqual(first_result["status"], "completed")
        self.assertEqual(second_result["status"], "completed")
        self.assertEqual(len(second_result["output"]["steps"]), 2)

    def test_completed_run_preserves_full_ledger_history(self):
        config = build_workflow_config_from_graph("Ledger Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Ledger Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "queued", {"message": "queued"})

        execute_queued_workflow_run(run["id"], workflow["id"], {"text": "hello"})

        saved_run = db.get_workflow_run(run["id"])
        ledger_types = [entry["type"] for entry in saved_run["output"]["ledger"]]

        self.assertEqual(saved_run["status"], "completed")
        self.assertEqual(
            ledger_types,
            [
                "running",
                "step_started",
                "step_completed",
                "step_started",
                "step_completed",
                "completed",
            ],
        )

    def test_approval_requires_paused_run_and_cannot_be_applied_twice(self):
        config = build_workflow_config_from_graph("Approval Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Approval Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "queued", {"message": "queued"})
        approval = db.create_workflow_approval(
            workflow_run_id=run["id"],
            workflow_id=workflow["id"],
            step_id="step-1",
            step_label="Create Task",
            step_type="task.create",
            reason="Test approval",
            payload={"step": {"id": "step-1"}},
        )

        with TestClient(main.app) as client:
            not_paused = client.post(f"/workflows/approvals/{approval['id']}", json={"action": "approve"})
            self.assertEqual(not_paused.status_code, 409)

        update = db.update_workflow_run(
            run["id"],
            status="awaiting_approval",
            output={
                "nextStepIndex": 0,
                "plannedSteps": [
                    {"stepId": "step-1", "label": "Create Task", "status": "awaiting_approval"},
                    {"stepId": "step-2", "label": "Create Follow Up", "status": "pending"},
                ],
            },
        )
        self.assertEqual(update["status"], "awaiting_approval")

        with TestClient(main.app) as client, patch.object(main.run_workflow_job, "delay", return_value=None):
            approved = client.post(f"/workflows/approvals/{approval['id']}", json={"action": "approve"})
            self.assertEqual(approved.status_code, 200)

            repeated = client.post(f"/workflows/approvals/{approval['id']}", json={"action": "approve"})
            self.assertEqual(repeated.status_code, 409)

    def test_stale_run_recovers_from_last_incomplete_step(self):
        config = build_workflow_config_from_graph("Recovery Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Recovery Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "running", {"message": "running"})
        started_at = db.now_iso()

        seeded_output = {
            "workflowName": config["name"],
            "trigger": config["trigger"],
            "totalSteps": 2,
            "currentStep": 2,
            "currentStepLabel": "Create Follow Up",
            "nextStepIndex": 1,
            "plannedSteps": [
                {
                    "stepId": "step-1",
                    "label": "Create Task",
                    "type": "task.create",
                    "order": 1,
                    "status": "completed",
                    "output": "Created task draft: One",
                    "error": None,
                    "attempt": 1,
                    "startedAt": started_at,
                    "completedAt": started_at,
                    "resultRef": "step-1:attempt:1",
                },
                {
                    "stepId": "step-2",
                    "label": "Create Follow Up",
                    "type": "task.create",
                    "order": 2,
                    "status": "running",
                    "output": None,
                    "error": None,
                    "attempt": 1,
                    "startedAt": started_at,
                    "completedAt": None,
                    "resultRef": None,
                },
            ],
            "steps": [
                {
                    "stepId": "step-1",
                    "label": "Create Task",
                    "type": "task.create",
                    "ok": True,
                    "output": "Created task draft: One",
                    "data": {"title": "One", "payload": {"text": "hello"}},
                    "attempt": 1,
                    "resultRef": "step-1:attempt:1",
                }
            ],
            "completedSteps": [
                {
                    "stepId": "step-1",
                    "label": "Create Task",
                    "type": "task.create",
                    "ok": True,
                    "output": "Created task draft: One",
                    "data": {"title": "One", "payload": {"text": "hello"}},
                    "attempt": 1,
                    "resultRef": "step-1:attempt:1",
                }
            ],
            "currentData": {"title": "One", "payload": {"text": "hello"}},
            "startedAt": started_at,
        }
        db.update_workflow_run(
            run["id"],
            status="running",
            output=seeded_output,
            lease_owner="dead-worker",
            lease_expires_at="2000-01-01T00:00:00Z",
            last_heartbeat_at="2000-01-01T00:00:00Z",
            recovery_state="active",
        )

        executed_steps = []
        original_run_step = workflow_runtime.run_workflow_step

        def tracked_run_step(step, input_data):
            executed_steps.append(step["id"])
            return original_run_step(step, input_data)

        with patch.object(workflow_runtime, "run_workflow_step", side_effect=tracked_run_step):
            sweep_workflow_runs(
                lambda workflow_run_id, workflow_id: execute_queued_workflow_run(
                    workflow_run_id,
                    workflow_id,
                    None,
                    True,
                )
            )

        saved_run = db.get_workflow_run(run["id"])
        self.assertEqual(saved_run["status"], "completed")
        self.assertEqual(executed_steps, ["step-2"])
        self.assertEqual(len(saved_run["output"]["steps"]), 2)
        self.assertEqual(saved_run["output"]["plannedSteps"][0]["attempt"], 1)
        self.assertEqual(saved_run["output"]["plannedSteps"][1]["attempt"], 2)

    def test_duplicate_recovery_sweep_does_not_rerun_completed_steps(self):
        config = build_workflow_config_from_graph("Recovery Dedup Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Recovery Dedup Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(
            workflow["id"],
            "running",
            {
                "workflowName": config["name"],
                "trigger": config["trigger"],
                "totalSteps": 2,
                "currentStep": 1,
                "currentStepLabel": "Create Task",
                "nextStepIndex": 0,
                "plannedSteps": [
                    {
                        "stepId": "step-1",
                        "label": "Create Task",
                        "type": "task.create",
                        "order": 1,
                        "status": "running",
                        "output": None,
                        "error": None,
                        "attempt": 1,
                        "startedAt": db.now_iso(),
                        "completedAt": None,
                        "resultRef": None,
                    },
                    {
                        "stepId": "step-2",
                        "label": "Create Follow Up",
                        "type": "task.create",
                        "order": 2,
                        "status": "pending",
                        "output": None,
                        "error": None,
                        "attempt": 0,
                        "startedAt": None,
                        "completedAt": None,
                        "resultRef": None,
                    },
                ],
                "steps": [],
                "completedSteps": [],
                "currentData": {"text": "hello"},
                "startedAt": db.now_iso(),
            },
        )
        db.update_workflow_run(
            run["id"],
            status="running",
            lease_owner="dead-worker",
            lease_expires_at="2000-01-01T00:00:00Z",
            last_heartbeat_at="2000-01-01T00:00:00Z",
            recovery_state="active",
        )

        executed_steps = []
        original_run_step = workflow_runtime.run_workflow_step

        def tracked_run_step(step, input_data):
            executed_steps.append(step["id"])
            return original_run_step(step, input_data)

        with patch.object(workflow_runtime, "run_workflow_step", side_effect=tracked_run_step):
            sweep_workflow_runs(
                lambda workflow_run_id, workflow_id: execute_queued_workflow_run(workflow_run_id, workflow_id, None, True)
            )
            sweep_workflow_runs(
                lambda workflow_run_id, workflow_id: execute_queued_workflow_run(workflow_run_id, workflow_id, None, True)
            )

        self.assertEqual(executed_steps, ["step-1", "step-2"])
        saved_run = db.get_workflow_run(run["id"])
        self.assertEqual(saved_run["status"], "completed")
        self.assertEqual(len(saved_run["output"]["steps"]), 2)

    def test_sweeper_marks_expired_running_but_not_approval_waits(self):
        config = build_workflow_config_from_graph("Sweep Guard Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Sweep Guard Workflow", make_nodes(), make_edges(), config)
        running_run = db.create_workflow_run(workflow["id"], "running", {"message": "running"})
        awaiting_run = db.create_workflow_run(workflow["id"], "awaiting_approval", {"message": "paused"})

        db.update_workflow_run(
            running_run["id"],
            status="running",
            lease_owner="dead-worker",
            lease_expires_at="2000-01-01T00:00:00Z",
            last_heartbeat_at="2000-01-01T00:00:00Z",
            recovery_state="active",
        )
        db.update_workflow_run(
            awaiting_run["id"],
            status="awaiting_approval",
            lease_owner=None,
            lease_expires_at="2000-01-01T00:00:00Z",
            last_heartbeat_at="2000-01-01T00:00:00Z",
            recovery_state=None,
        )

        sweep_workflow_runs(lambda workflow_run_id, workflow_id: None)

        refreshed_running = db.get_workflow_run(running_run["id"])
        refreshed_awaiting = db.get_workflow_run(awaiting_run["id"])
        self.assertEqual(refreshed_running["status"], "recovering")
        self.assertEqual(refreshed_awaiting["status"], "awaiting_approval")

    def test_invalid_lease_owner_cannot_override_run_state(self):
        config = build_workflow_config_from_graph("Lease Guard Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Lease Guard Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(workflow["id"], "running", {"message": "running"})
        db.update_workflow_run(
            run["id"],
            status="running",
            lease_owner="owner-a",
            lease_expires_at=db.now_iso(),
            last_heartbeat_at=db.now_iso(),
            recovery_state="active",
        )

        update_result = db.update_workflow_run(
            run["id"],
            status="failed",
            output={"error": "bad update"},
            expected_lease_owner="owner-b",
            clear_lease=True,
        )
        refreshed = db.get_workflow_run(run["id"])

        self.assertIsNone(update_result)
        self.assertEqual(refreshed["status"], "running")
        self.assertEqual(refreshed["lease_owner"], "owner-a")

    def test_stale_run_recovery_failure_preserves_completed_steps(self):
        config = build_workflow_config_from_graph(
            "Recovery Failure Workflow",
            make_failing_recovery_nodes(),
            make_edges(),
        )
        workflow = db.create_workflow("Recovery Failure Workflow", make_failing_recovery_nodes(), make_edges(), config)
        run = db.create_workflow_run(
            workflow["id"],
            "running",
            {
                "workflowName": config["name"],
                "trigger": config["trigger"],
                "totalSteps": 2,
                "currentStep": 2,
                "currentStepLabel": "Broken API",
                "nextStepIndex": 1,
                "plannedSteps": [
                    {
                        "stepId": "step-1",
                        "label": "Create Task",
                        "type": "task.create",
                        "order": 1,
                        "status": "completed",
                        "output": "Created task draft: One",
                        "error": None,
                        "attempt": 1,
                        "startedAt": db.now_iso(),
                        "completedAt": db.now_iso(),
                        "resultRef": "step-1:attempt:1",
                    },
                    {
                        "stepId": "step-2",
                        "label": "Broken API",
                        "type": "api.call",
                        "order": 2,
                        "status": "running",
                        "output": None,
                        "error": None,
                        "attempt": 1,
                        "startedAt": db.now_iso(),
                        "completedAt": None,
                        "resultRef": None,
                    },
                ],
                "steps": [
                    {
                        "stepId": "step-1",
                        "label": "Create Task",
                        "type": "task.create",
                        "ok": True,
                        "output": "Created task draft: One",
                        "data": {"title": "One", "payload": {"text": "hello"}},
                        "attempt": 1,
                        "resultRef": "step-1:attempt:1",
                    }
                ],
                "completedSteps": [
                    {
                        "stepId": "step-1",
                        "label": "Create Task",
                        "type": "task.create",
                        "ok": True,
                        "output": "Created task draft: One",
                        "data": {"title": "One", "payload": {"text": "hello"}},
                        "attempt": 1,
                        "resultRef": "step-1:attempt:1",
                    }
                ],
                "currentData": {"title": "One", "payload": {"text": "hello"}},
                "startedAt": db.now_iso(),
            },
        )
        db.update_workflow_run(
            run["id"],
            status="running",
            lease_owner="dead-worker",
            lease_expires_at="2000-01-01T00:00:00Z",
            last_heartbeat_at="2000-01-01T00:00:00Z",
            recovery_state="active",
        )
        approval = db.create_workflow_approval(
            workflow_run_id=run["id"],
            workflow_id=workflow["id"],
            step_id="step-2",
            step_label="Broken API",
            step_type="api.call",
            reason="Pre-approved recovery failure path",
            payload={"step": {"id": "step-2"}},
        )
        db.update_workflow_approval(approval["id"], "approved")

        stale = db.mark_workflow_run_stale(run["id"], "worker heartbeat expired", "2100-01-01T00:00:00Z")
        self.assertEqual(stale["status"], "stale")
        recovering = db.begin_workflow_run_recovery(run["id"], "worker heartbeat expired", max_recovery_attempts=3)
        self.assertEqual(recovering["status"], "recovering")

        with self.assertRaisesRegex(RuntimeError, "missing config.url"):
            execute_queued_workflow_run(run["id"], workflow["id"], None, True)

        saved_run = db.get_workflow_run(run["id"])
        self.assertEqual(saved_run["status"], "failed")
        self.assertEqual(saved_run["output"]["steps"][0]["stepId"], "step-1")
        self.assertEqual(saved_run["output"]["plannedSteps"][0]["status"], "completed")
        self.assertEqual(saved_run["output"]["plannedSteps"][1]["status"], "failed")


class WorkflowApiContractTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_token = auth.APP_BEARER_TOKEN
        db.DB_PATH = Path(self.tempdir.name) / "workflow-api-tests.db"
        auth.APP_BEARER_TOKEN = ""
        db.init_db()

    def tearDown(self):
        auth.APP_BEARER_TOKEN = self.original_token
        db.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_workflow_crud_routes_return_stable_shapes(self):
        payload = {
            "name": "Contract Workflow",
            "nodes": make_nodes(),
            "edges": make_edges(),
            "config": build_workflow_config_from_graph("Contract Workflow", make_nodes(), make_edges()),
        }

        with TestClient(main.app) as client:
            created = client.post("/workflows", json=payload)
            self.assertEqual(created.status_code, 200)
            created_body = created.json()
            self.assertEqual(set(created_body.keys()), {"workflow", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, created_body)
            self.assertTrue(
                {
                    "id",
                    "name",
                    "active",
                    "nodes",
                    "edges",
                    "config",
                    "cisiv_stage",
                    "created_at",
                    "updated_at",
                }.issubset(created_body["workflow"].keys())
            )
            self.assertEqual(created_body["workflow"]["cisiv_stage"], "structure")

            workflow_id = created_body["workflow"]["id"]

            listed = client.get("/workflows")
            self.assertEqual(listed.status_code, 200)
            listed_body = listed.json()
            self.assertEqual(set(listed_body.keys()), {"workflows", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, listed_body)
            self.assertIsInstance(listed_body["workflows"], list)
            self.assertEqual(listed_body["workflows"][0]["id"], workflow_id)

            fetched = client.get(f"/workflows?workflow_id={workflow_id}")
            self.assertEqual(fetched.status_code, 200)
            fetched_body = fetched.json()
            self.assertEqual(set(fetched_body.keys()), {"workflow", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, fetched_body)
            self.assertEqual(fetched_body["workflow"]["id"], workflow_id)

            updated = client.put(
                "/workflows",
                json={
                    **payload,
                    "id": workflow_id,
                    "name": "Contract Workflow Updated",
                },
            )
            self.assertEqual(updated.status_code, 200)
            updated_body = updated.json()
            self.assertEqual(set(updated_body.keys()), {"workflow", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, updated_body)
            self.assertEqual(updated_body["workflow"]["name"], "Contract Workflow Updated")
            self.assertEqual(updated_body["workflow"]["cisiv_stage"], "structure")

            templates = client.get("/workflows/templates")
            self.assertEqual(templates.status_code, 200)
            templates_body = templates.json()
            self.assertEqual(set(templates_body.keys()), {"templates", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, templates_body)
            self.assertIsInstance(templates_body["templates"], list)
            self.assertTrue(any(template["id"] == "webhook-summary-slack-safe" for template in templates_body["templates"]))

    def test_run_and_run_detail_routes_return_stable_shapes(self):
        config = build_workflow_config_from_graph("Run Contract Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Run Contract Workflow", make_nodes(), make_edges(), config)

        with TestClient(main.app) as client, patch.object(main.run_workflow_job, "delay", return_value=None):
            queued = client.post(
                "/workflows/run",
                json={"id": workflow["id"], "trigger_data": {"text": "manual run", "source": "builder"}},
            )
            self.assertEqual(queued.status_code, 200)
            queued_body = queued.json()
            self.assertEqual(
                set(queued_body.keys()),
                {
                    "ok",
                    "queued",
                    "workflow_run_id",
                    "workflow_id",
                    "status",
                    "source",
                    "cisiv_stage",
                    "law_enforcement",
                    "ul_snapshot",
                    "law_event_log",
                },
            )
            assert_project_infi_payload(self, queued_body)
            self.assertEqual(queued_body["status"], "queued")
            self.assertEqual(queued_body["workflow_id"], workflow["id"])
            self.assertEqual(queued_body["source"], "builder")
            self.assertEqual(queued_body["cisiv_stage"], "implementation")

            runs = client.get("/workflows/runs")
            self.assertEqual(runs.status_code, 200)
            runs_body = runs.json()
            self.assertEqual(set(runs_body.keys()), {"runs", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, runs_body)
            self.assertIsInstance(runs_body["runs"], list)
            self.assertEqual(runs_body["runs"][0]["id"], queued_body["workflow_run_id"])

            detail = client.get(f"/workflows/runs/{queued_body['workflow_run_id']}")
            self.assertEqual(detail.status_code, 200)
            detail_body = detail.json()
            self.assertEqual(set(detail_body.keys()), {"run", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, detail_body)
            self.assertTrue(
                {
                    "id",
                    "workflow_id",
                    "status",
                    "output",
                    "created_at",
                    "updated_at",
                    "workflow",
                    "cisiv_stage",
                    "lease_owner",
                    "lease_expires_at",
                    "last_heartbeat_at",
                    "recovery_state",
                    "recovery_attempts",
                    "stale_reason",
                }.issubset(detail_body["run"].keys())
            )
            self.assertEqual(detail_body["run"]["cisiv_stage"], "implementation")
            self.assertEqual(detail_body["run"]["output"]["cisiv_stage"], "implementation")
            assert_project_infi_payload(self, detail_body["run"]["output"])

    def test_generate_and_simulate_routes_carry_cisiv_defaults(self):
        with TestClient(main.app) as client:
            generated = client.post(
                "/workflows/generate",
                json={"prompt": "Summarize email and send a Slack alert"},
            )
            self.assertEqual(generated.status_code, 200)
            generated_body = generated.json()
            assert_project_infi_payload(self, generated_body)
            self.assertEqual(generated_body["workflow"]["cisiv_stage"], "concept")

            simulated = client.post(
                "/workflows/simulate",
                json={
                    "workflow": build_workflow_config_from_graph(
                        "Sim Contract Workflow",
                        make_nodes(),
                        make_edges(),
                    ),
                },
            )
            self.assertEqual(simulated.status_code, 200)
            simulated_body = simulated.json()
            assert_project_infi_payload(self, simulated_body)
            self.assertEqual(simulated_body["cisiv_stage"], "verification")
            self.assertTrue(all(step["cisiv_stage"] == "verification" for step in simulated_body["steps"]))

    def test_workflow_generate_route_requires_external_adoption_to_be_filtered(self):
        with TestClient(main.app) as client:
            blocked = client.post(
                "/workflows/generate",
                json={
                    "prompt": "Generate a workflow from this outside proposal.",
                    "external_suggestion": {
                        "source": "outside_note",
                        "summary": "Adopt this directly.",
                    },
                    "external_suggestion_usage": "adoption",
                },
            )
            self.assertEqual(blocked.status_code, 400)
            self.assertIn("external_suggestion_law_filter", blocked.json()["detail"])
            self.assertIn("admitted_external_form", blocked.json()["detail"])

            admitted = client.post(
                "/workflows/generate",
                json={
                    "prompt": "Generate a workflow from this filtered outside proposal.",
                    "external_suggestion": {
                        "source": "outside_note",
                        "summary": "Adopt this after filtering.",
                    },
                    "external_suggestion_usage": "adoption",
                    "law_filter_applied": True,
                    "admitted_external_form": "Use only the trigger sequencing pattern and keep the existing workflow boundaries.",
                },
            )
            self.assertEqual(admitted.status_code, 200)
            admitted_body = admitted.json()
            assert_project_infi_payload(self, admitted_body)
            self.assertEqual(
                admitted_body["law_enforcement"]["external_suggestion_admission"]["status"],
                "admitted",
            )

    def test_approval_and_onboarding_routes_return_stable_shapes(self):
        config = build_workflow_config_from_graph("Approval Contract Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Approval Contract Workflow", make_nodes(), make_edges(), config)
        run = db.create_workflow_run(
            workflow["id"],
            "awaiting_approval",
            {
                "nextStepIndex": 0,
                "plannedSteps": [
                    {"stepId": "step-1", "label": "Create Task", "status": "awaiting_approval"},
                    {"stepId": "step-2", "label": "Create Follow Up", "status": "pending"},
                ],
            },
        )
        approval = db.create_workflow_approval(
            workflow_run_id=run["id"],
            workflow_id=workflow["id"],
            step_id="step-1",
            step_label="Create Task",
            step_type="task.create",
            reason="Review this step",
            payload={"step": {"id": "step-1"}},
        )

        with TestClient(main.app) as client, patch.object(main.run_workflow_job, "delay", return_value=None):
            approvals = client.get("/workflows/approvals")
            self.assertEqual(approvals.status_code, 200)
            approvals_body = approvals.json()
            self.assertEqual(set(approvals_body.keys()), {"approvals", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, approvals_body)
            self.assertIsInstance(approvals_body["approvals"], list)
            self.assertEqual(approvals_body["approvals"][0]["id"], approval["id"])
            self.assertEqual(approvals_body["approvals"][0]["cisiv_stage"], "implementation")

            approved = client.post(f"/workflows/approvals/{approval['id']}", json={"action": "approve"})
            self.assertEqual(approved.status_code, 200)
            approved_body = approved.json()
            self.assertEqual(set(approved_body.keys()), {"ok", "status", "law_enforcement", "ul_snapshot", "law_event_log"})
            assert_project_infi_payload(self, approved_body)
            self.assertEqual(approved_body["status"], "approved")

            onboarding_before = client.get("/onboarding")
            self.assertEqual(onboarding_before.status_code, 200)
            self.assertEqual(
                set(onboarding_before.json().keys()),
                {
                    "onboarding_done",
                    "goal",
                    "tools",
                    "created_at",
                    "updated_at",
                    "cisiv_stage",
                    "law_enforcement",
                    "ul_snapshot",
                    "law_event_log",
                },
            )
            assert_project_infi_payload(self, onboarding_before.json())
            self.assertEqual(onboarding_before.json()["cisiv_stage"], "identity")

            onboarding_after = client.post(
                "/onboarding/complete",
                json={"goal": "Summarize emails", "tools": ["email", "slack"]},
            )
            self.assertEqual(onboarding_after.status_code, 200)
            onboarding_after_body = onboarding_after.json()
            self.assertEqual(
                set(onboarding_after_body.keys()),
                {
                    "ok",
                    "onboarding_done",
                    "goal",
                    "tools",
                    "created_at",
                    "updated_at",
                    "cisiv_stage",
                    "law_enforcement",
                    "ul_snapshot",
                    "law_event_log",
                },
            )
            assert_project_infi_payload(self, onboarding_after_body)
            self.assertTrue(onboarding_after_body["onboarding_done"])
            self.assertEqual(onboarding_after_body["cisiv_stage"], "identity")

    def test_webhook_route_supports_fake_mode_and_stable_shape(self):
        config = build_workflow_config_from_graph(
            "Webhook Contract Workflow",
            make_webhook_nodes(),
            make_edges(),
        )
        workflow = db.create_workflow("Webhook Contract Workflow", make_webhook_nodes(), make_edges(), config)

        with TestClient(main.app) as client, patch.object(main.run_workflow_job, "delay", return_value=None):
            unauthorized = client.post(
                f"/integrations/webhooks/{workflow['id']}",
                json={"text": "payload"},
            )
            self.assertEqual(unauthorized.status_code, 401)

            queued = client.post(
                f"/integrations/webhooks/{workflow['id']}",
                json={"text": "payload", "importance": "high"},
                headers={"x-workflow-secret": "hook-secret", "x-webhook-source": "contract-test"},
            )
            self.assertEqual(queued.status_code, 202)
            queued_body = queued.json()
            self.assertEqual(
                set(queued_body.keys()),
                {
                    "ok",
                    "queued",
                    "workflow_run_id",
                    "workflow_id",
                    "status",
                    "source",
                    "cisiv_stage",
                    "law_enforcement",
                    "ul_snapshot",
                    "law_event_log",
                },
            )
            assert_project_infi_payload(self, queued_body)
            self.assertEqual(queued_body["status"], "queued")
            self.assertEqual(queued_body["source"], "webhook")
            self.assertEqual(queued_body["cisiv_stage"], "implementation")

            saved_run = db.get_workflow_run(queued_body["workflow_run_id"])
            self.assertEqual(saved_run["output"]["triggerData"]["source"], "contract-test")
            assert_project_infi_payload(self, saved_run["output"])

    def test_webhook_route_rejects_non_webhook_workflows(self):
        config = build_workflow_config_from_graph("Manual Workflow", make_nodes(), make_edges())
        workflow = db.create_workflow("Manual Workflow", make_nodes(), make_edges(), config)

        with TestClient(main.app) as client:
            response = client.post(
                f"/integrations/webhooks/{workflow['id']}",
                json={"text": "payload"},
            )
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["detail"], "Workflow is not configured for webhook triggers")

    def test_health_details_reports_legacy_api_mount(self):
        with TestClient(main.app) as client:
            response = client.get("/health/details")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        assert_project_infi_payload(self, payload)
        self.assertEqual(payload["legacy_api_mount_path"], "/legacy_api")
        self.assertTrue(payload["legacy_api_mounted"])

    def test_legacy_api_mount_exposes_existing_chat_routes(self):
        with TestClient(main.app) as client:
            response = client.get("/legacy_api/api/chat/sessions")

        self.assertEqual(response.status_code, 200)
        self.assertIn("sessions", response.json())

    def test_legacy_api_mount_bootstraps_ai_runtime(self):
        previous_app = main.legacy_api_bridge._app
        previous_loaded = main.legacy_api_bridge.loaded
        previous_error = main.legacy_api_bridge.load_error
        main.legacy_api_bridge._app = None
        main.legacy_api_bridge.loaded = False
        main.legacy_api_bridge.load_error = None

        try:
            with patch("src.api.bootstrap_ai_runtime") as mock_bootstrap:
                with TestClient(main.app) as client:
                    response = client.get("/legacy_api/api/chat/sessions")
        finally:
            main.legacy_api_bridge._app = previous_app
            main.legacy_api_bridge.loaded = previous_loaded
            main.legacy_api_bridge.load_error = previous_error

        self.assertEqual(response.status_code, 200)
        mock_bootstrap.assert_called_once_with(reason="legacy_bridge_load")


if __name__ == "__main__":
    unittest.main()
