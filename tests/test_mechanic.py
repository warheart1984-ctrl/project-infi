"""Tests for AI Mechanic MVP."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mechanic.diagnosis.engine import diagnose_genome
from mechanic.genome.extractor import extract_process_genome
from mechanic.genome.schema import validate_genome
from mechanic.invariants.evaluators import evaluate_all
from mechanic.mechanic import MechanicError, MechanicRequest, main, rebuild_request, run_chaos_checks, scan_request
from mechanic.rebuild.planner import build_rebuild_bundle
from mechanic.runtime.enforcer import EnforcementViolation, enforce_turn_request, load_runtime_profile

FIXTURE_REPO = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "sample-customer-repo"
FIXTURE_V2 = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "sample-customer-repo-v2"
SAMPLE_TRACE = Path(__file__).resolve().parents[1] / "mechanic" / "fixtures" / "traces" / "sample_trace.ndjson"


class TestMechanicGenome(unittest.TestCase):
    def test_extract_fixture_genome(self):
        genome = extract_process_genome(case_id="mc-fixture", repo_path=FIXTURE_REPO)
        validate_genome(genome)
        self.assertGreater(len(genome.get("nodes") or []), 0)
        types = {str(n.get("type")) for n in genome.get("nodes") or []}
        self.assertIn("model_call", types)

    def test_fixture_triggers_multiple_codes(self):
        genome = extract_process_genome(case_id="mc-drift", repo_path=FIXTURE_REPO)
        drifts = evaluate_all(genome)
        codes = {str(d.get("code")) for d in drifts}
        self.assertIn("GOV-12", codes)
        self.assertIn("HUM-03", codes)
        self.assertTrue(codes & {"CST-07", "RNT-11", "GOV-15"})


class TestMechanicDiagnosis(unittest.TestCase):
    def test_diagnose_report_schema(self):
        genome = extract_process_genome(case_id="mc-diag", repo_path=FIXTURE_REPO)
        report = diagnose_genome(genome)
        self.assertEqual(report.get("schema_version"), "mechanic_scan.v1")
        self.assertGreater(int(report.get("drift_count") or 0), 0)
        self.assertIn("scan_hash", report)


class TestMechanicRebuild(unittest.TestCase):
    def test_rebuild_bundle_dry_run(self):
        genome = extract_process_genome(case_id="mc-rebuild", repo_path=FIXTURE_REPO)
        drifts = evaluate_all(genome)
        bundle = build_rebuild_bundle(case_id="mc-rebuild", genome=genome, drifts=drifts)
        self.assertEqual(bundle.get("safety_state"), "dry_run_only")
        self.assertIn("target_workflow", bundle)
        self.assertIn("patch_plan", bundle)
        self.assertIn("runtime_profile", bundle)
        self.assertIn("reconstruction_plan", bundle)
        self.assertEqual(
            bundle["runtime_profile"].get("profile_version"),
            "mechanic.runtime_profile.v1",
        )

    def test_rebuild_does_not_mutate_fixture_repo(self):
        before = (FIXTURE_REPO / "agent_bot.py").read_text(encoding="utf-8")
        genome = extract_process_genome(case_id="mc-no-mutate", repo_path=FIXTURE_REPO)
        report = diagnose_genome(genome)
        rebuild_request(
            MechanicRequest(case_id="mc-no-mutate"),
            genome=genome,
            scan=report,
        )
        after = (FIXTURE_REPO / "agent_bot.py").read_text(encoding="utf-8")
        self.assertEqual(before, after)


class TestMechanicRuntimeEnforcer(unittest.TestCase):
    def test_enforcer_admits_valid_turn(self):
        profile = {
            "profile_version": "mechanic.runtime_profile.v1",
            "case_id": "test",
            "enforcement": {
                "allowed_action_set": ["read", "propose"],
                "blocked_modes": ["apply"],
                "require_audit_fields": ["trace_id", "case_id"],
                "cost_ceiling": {"max_model_calls_per_turn": 2},
            },
        }
        result = enforce_turn_request(
            profile,
            action="propose",
            model_calls_this_turn=1,
            audit_fields={"trace_id": "t1", "case_id": "test"},
        )
        self.assertTrue(result.get("admitted"))

    def test_enforcer_blocks_cost_ceiling(self):
        profile = {
            "profile_version": "mechanic.runtime_profile.v1",
            "case_id": "test",
            "enforcement": {
                "allowed_action_set": ["propose"],
                "blocked_modes": [],
                "require_audit_fields": [],
                "cost_ceiling": {"max_model_calls_per_turn": 1},
            },
        }
        with self.assertRaises(EnforcementViolation) as ctx:
            enforce_turn_request(profile, action="propose", model_calls_this_turn=5)
        self.assertEqual(ctx.exception.code, "CST-07")

    def test_enforcer_blocks_apply_mode(self):
        profile = {
            "profile_version": "mechanic.runtime_profile.v1",
            "case_id": "test",
            "enforcement": {
                "allowed_action_set": ["propose"],
                "blocked_modes": ["apply"],
                "require_audit_fields": [],
            },
        }
        with self.assertRaises(EnforcementViolation):
            enforce_turn_request(profile, action="apply")


class TestMechanicCLI(unittest.TestCase):
    def test_chaos_check_proven(self):
        payload = run_chaos_checks()
        self.assertEqual(payload.get("claim_label"), "proven")

    def test_apply_mode_blocked(self):
        code = main(["--mode", "apply", "--case-id", "mc-block"])
        self.assertEqual(code, 1)

    def test_scan_fixture_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(
                [
                    "--mode",
                    "scan",
                    "--case-id",
                    "mc-cli-scan",
                    "--repo-path",
                    str(FIXTURE_REPO),
                    "--runtime-dir",
                    tmp,
                    "--write-json",
                ]
            )
            self.assertEqual(code, 0)
            genome_path = Path(tmp) / "mc-cli-scan" / "process_genome.v1.json"
            self.assertTrue(genome_path.exists())
            genome = json.loads(genome_path.read_text(encoding="utf-8"))
            validate_genome(genome)

    def test_full_pipeline_write_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ("scan", "diagnose", "rebuild", "verify"):
                code = main(
                    [
                        "--mode",
                        mode,
                        "--case-id",
                        "mc-pipeline",
                        "--repo-path",
                        str(FIXTURE_REPO),
                        "--runtime-dir",
                        tmp,
                        "--ledger-path",
                        str(Path(tmp) / "ledger.jsonl"),
                        "--drift-index",
                        str(Path(tmp) / "drift.jsonl"),
                        "--write-json",
                    ]
                )
                self.assertEqual(code, 0, msg=mode)
            case_dir = Path(tmp) / "mc-pipeline"
            for name in (
                "process_genome.v1.json",
                "mechanic_scan.v1.json",
                "target_workflow.v1.json",
                "patch_plan.v1.json",
                "MECHANIC_RUNTIME_PROFILE.json",
                "reconstruction_plan.v1.json",
            ):
                self.assertTrue((case_dir / name).exists(), msg=name)
            profile = load_runtime_profile(case_dir / "MECHANIC_RUNTIME_PROFILE.json")
            enforce_turn_request(
                profile,
                action="propose",
                model_calls_this_turn=1,
                audit_fields={"trace_id": "x", "case_id": "mc-pipeline"},
            )


class TestMechanicScanRequest(unittest.TestCase):
    def test_scan_requires_repo_path(self):
        with self.assertRaises(MechanicError):
            scan_request(MechanicRequest(case_id="x", repo_path=""))


class TestMechanicV2AndTrace(unittest.TestCase):
    def test_v2_fixture_distinct_profile(self):
        genome = extract_process_genome(case_id="mc-v2", repo_path=FIXTURE_V2)
        drifts = evaluate_all(genome)
        codes = {str(d.get("code")) for d in drifts}
        self.assertIn("GOV-20", codes)
        self.assertIn("RNT-04", codes)

    def test_trace_ndjson_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(
                [
                    "--mode",
                    "scan",
                    "--case-id",
                    "mc-trace-cli",
                    "--repo-path",
                    str(FIXTURE_REPO),
                    "--trace-path",
                    str(SAMPLE_TRACE),
                    "--runtime-dir",
                    tmp,
                    "--write-json",
                ]
            )
            self.assertEqual(code, 0)
            genome = json.loads((Path(tmp) / "mc-trace-cli" / "process_genome.v1.json").read_text(encoding="utf-8"))
            self.assertTrue(any(str(n.get("id", "")).startswith("trace_") for n in genome.get("nodes") or []))

    def test_report_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ("scan", "diagnose", "rebuild", "report"):
                args = [
                    "--mode",
                    mode,
                    "--case-id",
                    "mc-report-cli",
                    "--repo-path",
                    str(FIXTURE_REPO),
                    "--runtime-dir",
                    tmp,
                ]
                if mode in {"scan", "diagnose", "rebuild", "report"}:
                    args.append("--write-json")
                code = main(args)
                self.assertEqual(code, 0, msg=mode)
            report_path = Path(tmp) / "mc-report-cli" / "report.md"
            self.assertTrue(report_path.is_file())
            self.assertIn("Drift codes", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
