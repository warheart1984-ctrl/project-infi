"""Tests for forge/repo governed-cycle helpers."""

import unittest
from unittest.mock import patch

from src.forge_repo_governance import (
    EVOLVE_CONTRACTOR_SURFACE,
    FORGE_CONTRACTOR_SURFACE,
    REPO_ACTION_SURFACE,
    govern_patch_review_record,
    infer_evolve_cisiv_stage,
    infer_forge_cisiv_stage,
    infer_patch_review_cisiv_stage,
)
from src.cisiv import CISIV_STAGE_SEQUENCE


class TestForgeRepoGovernance(unittest.TestCase):
    def test_infer_forge_cisiv_stage(self):
        self.assertEqual(infer_forge_cisiv_stage("analyze"), "concept")
        self.assertEqual(infer_forge_cisiv_stage("generate_diff"), "structure")
        self.assertEqual(infer_forge_cisiv_stage("repo_manager"), "implementation")

    def test_infer_patch_review_cisiv_stage(self):
        self.assertEqual(infer_patch_review_cisiv_stage(phase="create"), "structure")
        self.assertEqual(infer_patch_review_cisiv_stage(phase="decision"), "verification")
        self.assertEqual(infer_patch_review_cisiv_stage(phase="apply"), "implementation")

    def test_infer_evolve_cisiv_stage(self):
        self.assertEqual(infer_evolve_cisiv_stage(phase="run"), "structure")
        self.assertEqual(infer_evolve_cisiv_stage(phase="verify"), "verification")

    @patch("src.forge_repo_governance.finalize_contractor_runtime_action")
    def test_govern_patch_review_record(self, mock_finalize):
        mock_finalize.return_value = (
            {"contract_version": "aais.project_infi.ul.v1", "governed_cycle": {"status": "success"}},
            {"count": 1, "sections": ["guardrail_state"]},
            {"id": "evt_patch"},
        )
        review = govern_patch_review_record(
            {
                "id": "patch_review_1",
                "session_id": "sess_1",
                "goal": "Update route handler",
                "status": "proposed",
            },
            phase="create",
            action_id="create_patch_review",
        )
        self.assertEqual(review["cisiv_stage"], "structure")
        self.assertEqual(review["cisiv_stage_sequence"], list(CISIV_STAGE_SEQUENCE))
        self.assertIn("ul_substrate", review)
        mock_finalize.assert_called_once()
        call_kwargs = mock_finalize.call_args.kwargs
        self.assertEqual(call_kwargs["surface"], REPO_ACTION_SURFACE)
        self.assertEqual(call_kwargs["action_id"], "create_patch_review")
        self.assertEqual(call_kwargs["cisiv_stage"], "structure")


if __name__ == "__main__":
    unittest.main()
