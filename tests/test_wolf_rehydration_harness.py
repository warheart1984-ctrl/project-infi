"""Tests for INV-1 Wolf rehydration harness."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.cog_runtime.wolf_rehydration_harness import (
    run_reboot_round_trip,
    simulate_pre_reboot_persist,
    verify_post_reboot_rehydration,
)


class TestWolfRehydrationHarness(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pre_reboot_persist_writes_stores(self):
        pre = simulate_pre_reboot_persist(store_root=self.store_root, identity_id="operator")
        self.assertTrue(Path(pre["narrative_path"]).is_file())
        self.assertTrue(Path(pre["intent_path"]).is_file())
        self.assertEqual(pre["intent_commitment_count"], 1)

    def test_post_reboot_rehydration_valid(self):
        pre = simulate_pre_reboot_persist(store_root=self.store_root, identity_id="operator")
        post = verify_post_reboot_rehydration(
            store_root=self.store_root,
            identity_id="operator",
            expected_active_story=pre["narrative_active_story"],
        )
        self.assertTrue(post["valid"], post.get("issues"))
        self.assertTrue(post["loaded_records"]["narrative"])
        self.assertTrue(post["loaded_records"]["intent"])

    def test_full_reboot_round_trip(self):
        payload = run_reboot_round_trip(store_root=self.store_root, identity_id="operator")
        self.assertEqual(payload["claim_label"], "asserted")
        self.assertTrue(payload["post_reboot"]["valid"])


if __name__ == "__main__":
    unittest.main()
