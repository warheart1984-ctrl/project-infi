"""Focused tests for Project Infi law contract admission behavior."""

import unittest

from src.project_infi_law import ProjectInfiLaw


class TestProjectInfiLaw(unittest.TestCase):
    def setUp(self):
        self.law = ProjectInfiLaw()

    def test_external_reference_can_be_observed_without_adoption(self):
        contract, _ul_snapshot, _plan = self.law.require_contract(
            surface="workflow_shell",
            action_id="external_reference_review",
            actor_id="workflow_shell",
            actor_role="system",
            target="reference_review",
            repo_change=False,
            cisiv_stage="structure",
            details={
                "external_suggestion": {
                    "source": "comparison_note",
                    "summary": "Use this only as comparison pressure.",
                },
                "external_suggestion_usage": "comparison",
            },
        )

        admission = contract["external_suggestion_admission"]
        law_check = next(
            check
            for check in contract["law_checks"]
            if check["law_id"] == "law_7_external_suggestion_admission"
        )

        self.assertEqual(admission["status"], "reference_only")
        self.assertTrue(admission["present"])
        self.assertFalse(admission["adoption_requested"])
        self.assertFalse(admission["law_filter_applied"])
        self.assertTrue(law_check["passed"])
        self.assertEqual(law_check["status"], "observed")

    def test_external_adoption_fails_closed_without_filter_and_admitted_form(self):
        with self.assertRaisesRegex(
            ValueError,
            "external_suggestion_law_filter, admitted_external_form",
        ):
            self.law.require_contract(
                surface="workflow_shell",
                action_id="external_adoption_attempt",
                actor_id="workflow_shell",
                actor_role="system",
                target="adoption_attempt",
                repo_change=False,
                cisiv_stage="structure",
                details={
                    "external_suggestion": {
                        "source": "external_note",
                        "summary": "Adopt this raw proposal.",
                    },
                    "external_suggestion_usage": "adoption",
                },
            )

    def test_external_adoption_requires_documented_admitted_form(self):
        contract, _ul_snapshot, _plan = self.law.require_contract(
            surface="workflow_shell",
            action_id="external_adoption_filtered",
            actor_id="workflow_shell",
            actor_role="system",
            target="adoption_filtered",
            repo_change=False,
            cisiv_stage="structure",
            details={
                "external_suggestion": {
                    "source": "external_note",
                    "summary": "Suggestion offered from outside the project.",
                },
                "external_suggestion_usage": "adoption",
                "law_filter_applied": True,
                "admitted_external_form": "Use the suggestion only as a bounded module-local option with docs and tests.",
            },
        )

        admission = contract["external_suggestion_admission"]
        law_check = next(
            check
            for check in contract["law_checks"]
            if check["law_id"] == "law_7_external_suggestion_admission"
        )

        self.assertEqual(admission["status"], "admitted")
        self.assertTrue(admission["adoption_requested"])
        self.assertTrue(admission["law_filter_applied"])
        self.assertTrue(admission["admitted_form_documented"])
        self.assertEqual(
            admission["admitted_form_summary"],
            "Use the suggestion only as a bounded module-local option with docs and tests.",
        )
        self.assertTrue(law_check["passed"])
        self.assertEqual(law_check["status"], "enforced")

    def test_non_copy_clause_fails_closed_on_raw_copy_request(self):
        with self.assertRaisesRegex(ValueError, "non_copy_clause"):
            self.law.require_contract(
                surface="workflow_shell",
                action_id="raw_copy_attempt",
                actor_id="workflow_shell",
                actor_role="system",
                target="raw_copy_attempt",
                repo_change=False,
                cisiv_stage="structure",
                details={
                    "external_suggestion": {
                        "source": "external_note",
                        "summary": "Copy this directly.",
                    },
                    "external_suggestion_usage": "adoption",
                    "law_filter_applied": True,
                    "admitted_external_form": "Use only the bounded structure, not the raw wording.",
                    "copy_raw_external": True,
                },
            )


if __name__ == "__main__":
    unittest.main()
