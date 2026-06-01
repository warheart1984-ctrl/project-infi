"""Tests for shared CISIV stage helpers."""

import unittest

from src.cisiv import (
    CISIV_LOGBOOK_STAGES,
    CISIV_STAGE_SEQUENCE,
    cisiv_stage_label,
    infer_lifecycle_cisiv_stage,
    normalize_cisiv_stage,
)


class TestCisiv(unittest.TestCase):
    def test_normalize_cisiv_stage_aliases(self):
        self.assertEqual(normalize_cisiv_stage("verify"), "verification")
        self.assertEqual(normalize_cisiv_stage("verified"), "verification")
        self.assertEqual(normalize_cisiv_stage("test"), "verification")
        self.assertEqual(normalize_cisiv_stage("build"), "implementation")
        self.assertEqual(normalize_cisiv_stage("implemented"), "implementation")
        self.assertEqual(normalize_cisiv_stage("verification"), "verification")

    def test_normalize_cisiv_stage_fallback(self):
        self.assertEqual(normalize_cisiv_stage("unknown", default="concept"), "concept")
        self.assertEqual(normalize_cisiv_stage(None, default="structure"), "structure")

    def test_cisiv_stage_label(self):
        self.assertEqual(cisiv_stage_label("structure"), "Structure")

    def test_infer_lifecycle_cisiv_stage(self):
        self.assertEqual(
            infer_lifecycle_cisiv_stage({"cisiv_stage": "verify"}),
            "verification",
        )
        self.assertEqual(
            infer_lifecycle_cisiv_stage({"action_id": "run_pytest", "action_label": "Run tests"}),
            "verification",
        )
        self.assertEqual(
            infer_lifecycle_cisiv_stage({"action_id": "apply_patch_review"}),
            "implementation",
        )

    def test_logbook_stages_match_sequence(self):
        self.assertEqual(set(CISIV_LOGBOOK_STAGES), set(CISIV_STAGE_SEQUENCE))


if __name__ == "__main__":
    unittest.main()
