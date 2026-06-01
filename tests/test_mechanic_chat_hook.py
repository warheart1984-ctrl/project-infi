"""Tests for AI Mechanic post-MVP hardening."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mechanic.apply.review_gated import create_apply_review, mechanic_patch_plan_to_review_plan
from mechanic.diagnosis.engine import diagnose_genome
from mechanic.genome.extractor import extract_process_genome
from mechanic.integration.chat_hook import enforce_chat_turn_request, mechanic_enforcement_enabled
from mechanic.mechanic import main
from mechanic.report import build_report_payload, generate_report_markdown
from mechanic.runtime.enforcer import load_runtime_profile

FIXTURE_REPO = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "sample-customer-repo"
FIXTURE_V2 = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "sample-customer-repo-v2"
SAMPLE_TRACE = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "traces" / "sample_trace.ndjson"


class TestMechanicV2Fixture(unittest.TestCase):
    def test_v2_triggers_distinct_codes(self):
        genome = extract_process_genome(case_id="mc-v2", repo_path=FIXTURE_V2)
        report = diagnose_genome(genome)
        codes = {str(d.get("code")) for d in report.get("drifts") or []}
        self.assertIn("GOV-20", codes)
        self.assertIn("RNT-04", codes)
        self.assertTrue(codes & {"RNT-15", "HUM-05", "HUM-08", "RNT-20"})


class TestMechanicTraceAdapter(unittest.TestCase):
    def test_trace_path_ingests_nodes(self):
        genome = extract_process_genome(
            case_id="mc-trace",
            repo_path=FIXTURE_REPO,
            trace_path=SAMPLE_TRACE,
        )
        types = {str(n.get("type")) for n in genome.get("nodes") or []}
        self.assertIn("model_call", types)
        self.assertIn("tool_binding", types)
        self.assertGreater(len(genome.get("edges") or []), 0)


class TestMechanicReport(unittest.TestCase):
    def test_report_markdown_on_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_id = "mc-report"
            code = main(
                [
                    "--mode",
                    "rebuild",
                    "--case-id",
                    case_id,
                    "--repo-path",
                    str(FIXTURE_REPO),
                    "--runtime-dir",
                    tmp,
                    "--write-json",
                ]
            )
            self.assertEqual(code, 0)
            payload = build_report_payload(case_id=case_id, case_dir=Path(tmp) / case_id)
            md = payload["report_markdown"]
            self.assertIn("GOV", md)
            self.assertIn("Drift codes", md)


class TestMechanicApplyReview(unittest.TestCase):
    def test_create_review_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_id = "mc-apply-review"
            case_dir = Path(tmp) / case_id
            code = main(
                [
                    "--mode",
                    "rebuild",
                    "--case-id",
                    case_id,
                    "--repo-path",
                    str(FIXTURE_REPO),
                    "--runtime-dir",
                    tmp,
                    "--write-json",
                ]
            )
            self.assertEqual(code, 0)
            result = create_apply_review(case_id=case_id, case_dir=case_dir, runtime_dir=case_dir / "reviews")
            self.assertFalse(result.get("customer_repo_mutated"))
            self.assertTrue(str(result.get("review_id") or ""))
            plan = result["patch_plan"]
            self.assertEqual(plan.get("status"), "proposal_only")

    def test_apply_review_requires_flag(self):
        code = main(["--mode", "apply-review", "--case-id", "x"])
        self.assertEqual(code, 1)

    def test_patch_plan_conversion(self):
        mechanic_plan = {
            "schema_version": "patch_plan.v1",
            "patches": [
                {
                    "code": "GOV-12",
                    "target_path": "agent_bot.py",
                    "suggestion": "add exception handler",
                }
            ],
        }
        review_plan = mechanic_patch_plan_to_review_plan(mechanic_plan, case_id="test")
        self.assertIn("agent_bot.py", review_plan.get("target_files") or [])
        self.assertTrue(review_plan.get("plan_id", "").startswith("mechanic_test_"))


class TestMechanicChatHook(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertFalse(mechanic_enforcement_enabled())
        self.assertIsNone(
            enforce_chat_turn_request(action="propose", audit_fields={"trace_id": "t", "case_id": "c"})
        )

    @mock.patch.dict(os.environ, {"MECHANIC_ENFORCE_PROFILE": "1", "MECHANIC_CASE_ID": "missing-case"})
    def test_blocks_missing_profile(self):
        block = enforce_chat_turn_request(action="propose", audit_fields={"trace_id": "t", "case_id": "missing-case"})
        self.assertIsNotNone(block)
        self.assertEqual(block.get("status_code"), 403)

    @mock.patch.dict(os.environ, {"MECHANIC_ENFORCE_PROFILE": "1", "MECHANIC_CASE_ID": "hook-case"})
    def test_admits_with_valid_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / "hook-case"
            case_dir.mkdir(parents=True)
            profile = {
                "profile_version": "mechanic.runtime_profile.v1",
                "case_id": "hook-case",
                "enforcement": {
                    "allowed_action_set": ["propose"],
                    "blocked_modes": ["apply"],
                    "require_audit_fields": ["trace_id", "case_id"],
                },
            }
            (case_dir / "MECHANIC_RUNTIME_PROFILE.json").write_text(json.dumps(profile), encoding="utf-8")
            runtime_root = Path(tmp)
            block = enforce_chat_turn_request(
                action="propose",
                audit_fields={"trace_id": "t1", "case_id": "hook-case"},
                runtime_root=runtime_root,
            )
            self.assertIsNone(block)
            loaded = load_runtime_profile(case_dir / "MECHANIC_RUNTIME_PROFILE.json")
            self.assertEqual(loaded.get("case_id"), "hook-case")


if __name__ == "__main__":
    unittest.main()
