"""Tests for Scorpion stage 1/2 governed OS anomaly extractor."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scorpion.events import load_events_from_path
from scorpion.invariants.evaluators import evaluate_all
from scorpion.ledger import append_claim_record, build_claim_record
from scorpion.reconstructor import build_reconstruction_plan
from scorpion.governance import build_snapshot_index_record
from scorpion.scorpion import (
    ScorpionRequest,
    judge_request,
    main,
    run_chaos_checks,
    scan_request,
    observe_request,
)
from scorpion.sentinel.audit_log import AuditExportSentinel
from scorpion.sentinel.fixture import FixtureSentinel
from scorpion.sentinel.registry import get_sentinel


FIXTURES = Path(__file__).resolve().parents[1] / "scorpion" / "fixtures" / "traces"
ALL_DRIFT_FIXTURES = [
    "syscall_misuse.ndjson",
    "scheduler_jitter.ndjson",
    "memory_leak.ndjson",
    "fd_leak.ndjson",
    "ipc_misorder.ndjson",
    "privilege_drift.ndjson",
    "entropy_collapse.ndjson",
    "race_precursor.ndjson",
]


class TestScorpionEvaluators(unittest.TestCase):
    def test_syscall_misuse_detects_drift(self):
        events = load_events_from_path(str(FIXTURES / "syscall_misuse.ndjson"))
        drifts = evaluate_all(events)
        ids = {d["invariant_id"] for d in drifts}
        self.assertIn("syscall_sequence", ids)

    def test_fd_leak_detects_drift(self):
        events = load_events_from_path(str(FIXTURES / "fd_leak.ndjson"))
        drifts = evaluate_all(events)
        self.assertTrue(any(d["invariant_id"] == "fd_flow" for d in drifts))

    def test_clean_baseline_no_drift(self):
        events = load_events_from_path(str(FIXTURES / "clean_baseline.ndjson"))
        drifts = evaluate_all(events)
        self.assertEqual(drifts, [])

    def test_all_drift_fixtures_detect_anomaly(self):
        for name in ALL_DRIFT_FIXTURES:
            with self.subTest(fixture=name):
                events = load_events_from_path(str(FIXTURES / name))
                drifts = evaluate_all(events)
                self.assertGreater(len(drifts), 0, msg=name)

    def test_scan_is_deterministic(self):
        request = ScorpionRequest(
            case_id="sc-det-001",
            trace_path=str(FIXTURES / "memory_leak.ndjson"),
        )
        one = scan_request(request, sentinel_name="fixture")
        two = scan_request(request, sentinel_name="fixture")
        self.assertEqual(one["scan_hash"], two["scan_hash"])
        self.assertEqual(one["drift_count"], two["drift_count"])

    def test_reconstruction_plan_has_steps_for_drift(self):
        drifts = [{"invariant_id": "fd_flow", "drift_summary": "leak"}]
        plan = build_reconstruction_plan(case_id="sc-plan", drifts=drifts)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].invariant_id, "fd_flow")
        self.assertEqual(plan.safety_state, "dry_run_only")


class TestScorpionGating(unittest.TestCase):
    def test_judge_approve_requires_allow_flag(self):
        request = ScorpionRequest(case_id="sc-judge-001", trace_path="")
        with self.assertRaisesRegex(ValueError, "allow-approve"):
            judge_request(
                request,
                decision="approve",
                reason="ok",
                reviewer="ops",
                invariant_id="fd_flow",
                drift_summary="leak",
                evidence_hash="abc",
                allow_approve=False,
            )

    def test_chaos_check_proven(self):
        payload = run_chaos_checks()
        self.assertEqual(payload["claim_label"], "proven")
        self.assertEqual(payload["scenarios_passed"], payload["scenarios_run"])


class TestScorpionCli(unittest.TestCase):
    def test_cli_observe_mode(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(
                [
                    "--mode",
                    "observe",
                    "--case-id",
                    "sc-cli-001",
                    "--trace-path",
                    str(FIXTURES / "clean_baseline.ndjson"),
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["mode"], "observe")
        self.assertEqual(payload["claim_label"], "proven")

    def test_cli_scan_mode(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(
                [
                    "--mode",
                    "scan",
                    "--case-id",
                    "sc-cli-002",
                    "--trace-path",
                    str(FIXTURES / "privilege_drift.ndjson"),
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertGreater(payload["drift_count"], 0)

    def test_cli_chaos_check(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(["--mode", "chaos-check", "--case-id", "sc-cli-003"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stream.getvalue())["claim_label"], "proven")

    def test_sentinel_fixture_ingest(self):
        sentinel = FixtureSentinel()
        events = sentinel.ingest(str(FIXTURES / "entropy_collapse.ndjson"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].domain, "entropy_signature")

    def test_sentinel_audit_text_parse(self):
        events = AuditExportSentinel().ingest(str(FIXTURES / "audit_syscall_misuse.audit"))
        self.assertGreater(len(events), 0)
        drifts = evaluate_all(events)
        self.assertTrue(any(d["invariant_id"] == "syscall_sequence" for d in drifts))

    def test_sentinel_registry(self):
        self.assertEqual(get_sentinel("fixture").adapter_id, FixtureSentinel.adapter_id)

    def test_cli_status_mode(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = main(["--mode", "status", "--case-id", "sc-cli-status"])
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertIn("stage_1_observation", payload["stages"])

    def test_snapshot_index_record_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "scorpion_report.json"
            snapshot = root / "scorpion_snapshot.json"
            ledger = root / "ledger.jsonl"
            report.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot.write_text(
                json.dumps(
                    {
                        "snapshot_id": "scsnap-test",
                        "claim_label": "proven",
                        "linkage": {"report_hash": "", "ledger_hash": ""},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            record = build_snapshot_index_record(
                snapshot_path=snapshot,
                report_path=report,
                ledger_path=ledger,
                case_id="sc-idx",
            )
            self.assertEqual(record["index_version"], "scorpion.snapshot_index.v1")
            self.assertIn("claim_transition", record)


class TestScorpionLedger(unittest.TestCase):
    def test_ledger_append(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "ledger.jsonl"
            record = build_claim_record(
                case_id="sc-led-001",
                mode="judge",
                invariant_id="fd_flow",
                decision="reject",
                claim_label="rejected",
                reviewer="bot",
                reason="drift",
                drift_summary="unclosed fd",
                evidence_hash="deadbeef",
            )
            append_claim_record(record, ledger)
            lines = ledger.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["ledger_version"], "scorpion.ledger.v1")


if __name__ == "__main__":
    unittest.main()
