"""Tests for the persistent Jarvis Mission Board."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from src.mission_board import MissionBoardController


class TestMissionBoard(unittest.TestCase):
    """Ensure the Mission Board tracks persistent objectives cleanly."""

    def setUp(self):
        self.runtime_dir = Path(tempfile.mkdtemp(prefix="aais-mission-board-"))
        self.board = MissionBoardController(runtime_dir=self.runtime_dir)
        self.board.reset()

    def tearDown(self):
        shutil.rmtree(self.runtime_dir, ignore_errors=True)

    def test_create_mission_focus_and_snapshot(self):
        snapshot = self.board.create_mission(
            title="Stabilize startup",
            objective="Make local startup more reliable on the laptop.",
            next_step="Check first-request latency after boot.",
            session_id="session-1",
            status="active",
        )

        self.assertEqual(snapshot["mission_count"], 1)
        self.assertEqual(snapshot["active_mission"]["title"], "Stabilize startup")
        self.assertEqual(snapshot["counts"]["active"], 1)
        self.assertEqual(snapshot["session_missions"][0]["session_id"], "session-1")
        self.assertEqual(snapshot["active_mission"]["cisiv_stage"], "concept")
        self.assertEqual(snapshot["active_mission"]["history"][0]["cisiv_stage"], "concept")

    def test_build_session_context_uses_active_mission(self):
        self.board.create_mission(
            title="Mission Board",
            objective="Give Jarvis a durable objective layer.",
            next_step="Attach the active mission to the runtime directive.",
            session_id="session-2",
            status="active",
        )

        context = self.board.build_session_context("session-2")

        self.assertIn("Mission Board:", context["prompt_block"])
        self.assertEqual(context["active_mission"]["title"], "Mission Board")
        self.assertEqual(len(context["related_missions"]), 1)

    def test_attach_browser_and_action_results_updates_links_and_activity(self):
        self.board.create_mission(
            title="Fix Settings",
            objective="Ground the settings route against the local code.",
            session_id="session-3",
            status="active",
            focus=True,
        )

        self.board.attach_browser_verification(
            "session-3",
            {
                "target_path": "/settings",
                "status": "warning",
                "summary": "Settings page needs attention.",
                "suggested_action": {"id": "build_frontend", "label": "Build Frontend"},
                "workspace_context": {
                    "results": [
                        {"relative_path": "AAIS-main/frontend/src/pages/Settings.jsx"},
                    ],
                },
            },
        )
        snapshot = self.board.attach_action_result(
            "session-3",
            {
                "action": {"id": "build_frontend", "label": "Build Frontend"},
                "status": "completed",
                "summary": "Build completed successfully.",
            },
        )

        active = snapshot["active_mission"]
        link_values = {link["value"] for link in active["links"]}
        self.assertIn("/settings", link_values)
        self.assertIn("build_frontend", link_values)
        self.assertEqual(active["session_id"], "session-3")
        self.assertEqual(active["cisiv_stage"], "implementation")
        activity_kinds = {entry["kind"] for entry in active["activity"]}
        self.assertIn("browser_verification", activity_kinds)
        self.assertIn("action_result", activity_kinds)
        history_kinds = [entry["kind"] for entry in active["history"]]
        self.assertEqual(history_kinds[0], "mission_created")
        self.assertIn("browser_verification", history_kinds)
        self.assertIn("action_result", history_kinds)
        browser_entry = next(entry for entry in active["history"] if entry["kind"] == "browser_verification")
        action_entry = next(entry for entry in active["history"] if entry["kind"] == "action_result")
        self.assertEqual(browser_entry["cisiv_stage"], "verification")
        self.assertEqual(action_entry["cisiv_stage"], "implementation")

    def test_attach_critic_review_updates_active_mission(self):
        self.board.create_mission(
            title="Stabilize startup",
            objective="Improve startup latency on the laptop.",
            session_id="session-4",
            status="active",
            focus=True,
        )

        snapshot = self.board.attach_critic_review(
            "session-4",
            {
                "source": "reply",
                "status": "advancing",
                "score": 0.84,
                "confidence": 0.78,
                "summary": "Mission Critic sees the latest reply as moving the mission forward.",
                "recommended_next": "Measure cold-start latency after the next restart.",
            },
        )

        active = snapshot["active_mission"]
        self.assertEqual(active["critic"]["status"], "advancing")
        self.assertEqual(active["critic"]["score"], 0.84)
        self.assertEqual(
            active["critic"]["recommended_next"],
            "Measure cold-start latency after the next restart.",
        )
        self.assertEqual(active["critic"]["cisiv_stage"], "verification")
        self.assertEqual(active["cisiv_stage"], "verification")

    def test_apply_critic_suggestion_promotes_status_and_next_step(self):
        snapshot = self.board.create_mission(
            title="Fix settings",
            objective="Repair the settings route.",
            session_id="session-5",
            status="active",
            focus=True,
        )
        mission_id = snapshot["active_mission"]["id"]
        self.board.attach_critic_review(
            "session-5",
            {
                "source": "browser_verification",
                "status": "blocked",
                "score": 0.41,
                "confidence": 0.84,
                "summary": "The live route is still mismatched and needs more work.",
                "recommended_next": "Inspect the settings component and rebuild the frontend.",
                "suggested_mission_status": "blocked",
            },
        )

        updated = self.board.apply_critic_suggestion(mission_id)
        active = updated["active_mission"]
        self.assertEqual(active["status"], "blocked")
        self.assertEqual(
            active["next_step"],
            "Inspect the settings component and rebuild the frontend.",
        )
        self.assertTrue(any(entry["kind"] == "critic_apply" for entry in active["activity"]))
        history_kinds = [entry["kind"] for entry in active["history"]]
        self.assertEqual(history_kinds[0], "mission_created")
        self.assertEqual(history_kinds[-2:], ["critic_review", "critic_apply"])

    def test_attach_critic_review_runs_verification_gate_and_blocks_failed_missions(self):
        self.board.create_mission(
            title="Admit capability adapter",
            objective="Verify the new adapter board before live admission.",
            session_id="session-6",
            status="active",
            focus=True,
        )

        snapshot = self.board.attach_critic_review(
            "session-6",
            {
                "source": "browser_verification",
                "status": "mixed",
                "score": 0.66,
                "confidence": 0.82,
                "summary": "Verification found law and intent instability.",
                "recommended_next": "Fix the failed verification tests before admission.",
                "verification_results": [
                    {
                        "test_id": "gate_1",
                        "law": 1,
                        "intent": 2,
                        "role": 2,
                        "constraint": 2,
                        "drift": 1,
                        "tags": ["LAW_BREAK"],
                    },
                    {
                        "test_id": "gate_2",
                        "law": 2,
                        "intent": 1,
                        "role": 2,
                        "constraint": 2,
                        "drift": 1,
                        "tags": ["ROLE_DRIFT", "DRIFT_INSTABILITY"],
                        "is_repeat_test": True,
                    },
                    {
                        "test_id": "gate_3",
                        "law": 2,
                        "intent": 2,
                        "role": 2,
                        "constraint": 2,
                        "drift": 1,
                        "tags": ["ROLE_DRIFT"],
                    },
                ],
            },
        )

        active = snapshot["active_mission"]
        self.assertEqual(active["status"], "blocked")
        self.assertEqual(active["verification_gate"]["decision"], "BLOCK")
        self.assertEqual(active["verification_gate"]["failed_tests"], ["gate_1", "gate_2"])
        self.assertIn("LAW_BREAK present", "; ".join(active["verification_gate"]["reasons"]))
        self.assertIn("ROLE_DRIFT occurred more than once", active["verification_gate"]["reasons"])
        self.assertTrue(any(entry["kind"] == "verification_gate" for entry in active["activity"]))
        self.assertTrue(any(entry["kind"] == "verification_gate" for entry in active["history"]))
        self.assertIn("gate_1: LAW_BREAK present", active["blocker"])

    def test_legacy_mission_without_history_initializes_on_first_append(self):
        mission_id = "legacy-mission"
        state_path = self.runtime_dir / "mission-board.json"
        legacy_payload = {
            "active_mission_id": mission_id,
            "missions": [
                {
                    "id": mission_id,
                    "title": "Legacy mission",
                    "objective": "Carry older mission data forward safely.",
                    "status": "active",
                    "session_id": "legacy-session",
                    "activity": [],
                    "links": [],
                    "tags": ["legacy"],
                }
            ],
            "updated_at": "2026-04-05T00:00:00+00:00",
        }
        state_path.write_text(json.dumps(legacy_payload, indent=2), encoding="utf-8")

        legacy_board = MissionBoardController(runtime_dir=self.runtime_dir)
        snapshot = legacy_board.attach_critic_review(
            "legacy-session",
            {
                "source": "reply",
                "status": "mixed",
                "score": 0.5,
                "confidence": 0.7,
                "summary": "Legacy mission accepted its first critic review.",
                "recommended_next": "Keep moving the mission forward.",
            },
        )

        active = snapshot["active_mission"]
        self.assertIsNotNone(active)
        self.assertEqual(active["id"], mission_id)
        self.assertEqual(active["history_count"], 1)
        self.assertEqual(active["history"][0]["kind"], "critic_review")

        persisted = json.loads(state_path.read_text(encoding="utf-8"))
        persisted_mission = persisted["missions"][0]
        self.assertIn("history", persisted_mission)
        self.assertEqual(len(persisted_mission["history"]), 1)
        self.assertEqual(persisted_mission["history"][0]["kind"], "critic_review")
