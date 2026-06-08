"""Tests for immune system heal and resilience cycle."""

from __future__ import annotations

import tempfile
import unittest

from src.immune_system import CLEAN_STREAK_HEAL_THRESHOLD, ImmuneSystemController


class TestImmuneSystemHealCycle(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="immune-system-")
        self.immune = ImmuneSystemController(runtime_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_clean_streak_increments_on_record_clean_turn(self):
        result = self.immune.record_clean_turn()
        self.assertEqual(result["clean_streak"], 1)
        self.assertFalse(result["heal"]["healed"])

    def test_packet_threat_resets_clean_streak(self):
        self.immune.record_clean_turn()
        self.immune.observe_packet_threats(
            {
                "response": "REJECT",
                "threats": [{"code": "memory_context_leak", "message": "leak"}],
                "reasons": ["memory leak"],
                "mutations": {"quarantined_nodes": []},
            }
        )
        snapshot = self.immune.snapshot(limit_events=5, limit_incidents=5)
        self.assertEqual(snapshot["clean_streak"], 0)
        self.assertIsNotNone(snapshot["last_threat_at"])

    def test_auto_heal_steps_down_after_clean_streak(self):
        with self.immune._lock:
            self.immune._state.system_mode = "restricted"
            self.immune._state.clean_streak = CLEAN_STREAK_HEAL_THRESHOLD
            self.immune._persist_locked()
        result = self.immune.attempt_heal(reason="test_heal")
        self.assertTrue(result["healed"])
        self.assertEqual(result["state"]["system_mode"], "normal")
        self.assertIsNotNone(result["state"]["last_heal_at"])

    def test_close_incident_increments_hardening(self):
        with self.immune._lock:
            opened = self.immune._open_incident_locked(
                trigger="test",
                mode="restricted",
                event={"caller_id": "tester", "resource_id": "resource"},
            )
            self.immune._persist_locked()
        incident_id = opened["incident_id"]
        result = self.immune.close_incident(incident_id, reason="test_close")
        self.assertTrue(result["closed"])
        self.assertGreaterEqual(result["hardening"]["defense_generation"], 1)

    def test_blacklist_blocks_auto_heal(self):
        with self.immune._lock:
            self.immune._state.clean_streak = CLEAN_STREAK_HEAL_THRESHOLD
            self.immune._state.system_mode = "restricted"
            self.immune._state.blacklisted_modules["bad_mod"] = {
                "module_id": "bad_mod",
                "blacklisted_at": "now",
            }
            self.immune._persist_locked()
        eligibility = self.immune.evaluate_heal_eligibility()
        self.assertFalse(eligibility["eligible"])
        self.assertEqual(eligibility["reason"], "blacklisted_modules_present")


if __name__ == "__main__":
    unittest.main()
