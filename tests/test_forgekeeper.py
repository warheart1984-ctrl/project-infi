"""Tests for Forgekeeper stage 1/2 safe runtime skeleton."""

from __future__ import annotations

import io
import hashlib
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from forge.forgekeeper import (
    ForgekeeperRequest,
    append_decision_record,
    append_snapshot_index_record,
    build_proof_report,
    build_snapshot_index_record,
    build_snapshot_index,
    build_dry_run_plan,
    build_decision_record,
    build_verification_report,
    build_bundle_export_manifest,
    cross_machine_replay_status,
    derive_attestation_overall,
    evaluate_attestation_hooks,
    judge_request,
    latest_plan_artifact,
    ledger_summary,
    query_drift_window,
    query_governance_reconciliation,
    query_governance_trace,
    query_snapshot_index,
    run_chaos_checks,
    run_reconcile_artifacts,
    snapshot_index_summary,
    main,
)


class TestForgekeeperPlanning(unittest.TestCase):
    """Verify deterministic dry-run planning behavior."""

    def test_build_dry_run_plan_is_deterministic_for_same_request(self):
        request = ForgekeeperRequest(
            plan_id="bf-plan-001",
            goal="map bounded reconstruction",
            scope="src",
            focus_files=["src/b.py", "src/a.py", "src/a.py"],
            constraints={"max_depth": 2, "proof_bundle_ref": "docs/proof/one.md"},
            context_files={"src/a.py": "print('a')", "src/b.py": "print('b')"},
        )

        plan_one = build_dry_run_plan(request)
        plan_two = build_dry_run_plan(request)

        self.assertEqual(plan_one.deterministic_seed, plan_two.deterministic_seed)
        self.assertEqual(plan_one.rollback_token, plan_two.rollback_token)
        self.assertEqual(plan_one.attestation_overall, plan_two.attestation_overall)
        self.assertEqual(
            [node.file_path for node in plan_one.change_nodes],
            [node.file_path for node in plan_two.change_nodes],
        )
        self.assertEqual(
            [node.content_hash for node in plan_one.change_nodes],
            [node.content_hash for node in plan_two.change_nodes],
        )
        self.assertEqual(plan_one.safety_state, "dry_run_only")
        self.assertEqual(plan_one.claim_label, "proven")

    def test_judge_approve_requires_explicit_allow_flag(self):
        request = ForgekeeperRequest(
            plan_id="bf-plan-002",
            goal="judge",
            scope="src",
        )
        with self.assertRaisesRegex(ValueError, "allow-approve"):
            judge_request(
                request,
                decision="approve",
                reason="looks safe",
                reviewer="ops-1",
                allow_approve=False,
            )

    def test_decision_record_has_stable_identifier(self):
        request = ForgekeeperRequest(
            plan_id="bf-plan-003",
            goal="judge",
            scope="src",
        )
        result = judge_request(
            request,
            decision="reject",
            reason="missing attestation",
            reviewer="governance-bot",
        )
        record_one = build_decision_record(result)
        record_two = build_decision_record(result)
        self.assertEqual(record_one.record_id, record_two.record_id)
        self.assertEqual(record_one.attestation_state, "asserted")
        self.assertEqual(record_one.claim_label, "rejected")
        self.assertEqual(record_one.claim_status, "rejected")

    def test_attestation_transition_asserted_when_evidence_missing(self):
        request = ForgekeeperRequest(
            plan_id="bf-plan-004",
            goal="attestation",
            scope="src",
            constraints={},
        )
        hooks = evaluate_attestation_hooks(request)
        self.assertEqual(derive_attestation_overall(hooks), "asserted")
        self.assertEqual(hooks[0].status, "proven")
        self.assertEqual(hooks[1].status, "proven")
        self.assertEqual(hooks[2].status, "asserted")

    def test_attestation_transition_rejected_on_unsafe_scope(self):
        request = ForgekeeperRequest(
            plan_id="bf-plan-005",
            goal="attestation",
            scope="../outside",
            constraints={"proof_bundle_ref": "docs/proof/stage.md"},
        )
        hooks = evaluate_attestation_hooks(request)
        self.assertEqual(derive_attestation_overall(hooks), "rejected")
        self.assertEqual(hooks[1].status, "rejected")


class TestForgekeeperCli(unittest.TestCase):
    """Verify CLI mode gating and non-destructive defaults."""

    def test_cli_plan_mode_writes_json_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "plan.json"
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "plan",
                        "--plan-id",
                        "bf-plan-cli-001",
                        "--goal",
                        "produce dry-run plan",
                        "--scope",
                        "src",
                        "--focus-file",
                        "src/api.py",
                        "--proof-bundle-ref",
                        "docs/proof/bumblebee-forge/STAGE1_PROOF_BUNDLE.md",
                        "--write-plan",
                        str(output_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["mode"], "plan")
            self.assertEqual(payload["claim_label"], "proven")
            self.assertEqual(payload["attestation_overall"], "proven")
            self.assertEqual(payload["safety_state"], "dry_run_only")
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["deterministic_seed"], written["deterministic_seed"])

    def test_cli_blocks_allow_apply_flag(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(
                [
                    "--mode",
                    "observe",
                    "--plan-id",
                    "bf-plan-cli-002",
                    "--allow-apply",
                ]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("apply mode is disabled", stream.getvalue())

    def test_cli_judge_includes_decision_record_payload(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(
                [
                    "--mode",
                    "judge",
                    "--plan-id",
                    "bf-plan-cli-003",
                    "--decision",
                    "reject",
                    "--reason",
                    "insufficient evidence",
                    "--reviewer",
                    "gov-1",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["claim_label"], "rejected")
        self.assertIn("decision_record", payload)
        self.assertEqual(payload["decision_record"]["attestation_state"], "asserted")
        self.assertTrue(payload["ledger_appended"])
        self.assertIn("ledger_path", payload)

    def test_ledger_append_integrity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "decision_ledger.jsonl"
            request = ForgekeeperRequest(plan_id="bf-plan-ledger", goal="judge", scope="src")
            first = build_decision_record(
                judge_request(request, decision="reject", reason="missing evidence", reviewer="gov-1")
            )
            first.evidence_refs = ["docs/proof/one.md"]
            second = build_decision_record(
                judge_request(request, decision="reject", reason="still missing", reviewer="gov-2")
            )
            second.evidence_refs = ["docs/proof/two.md"]

            append_decision_record(first, ledger_path)
            append_decision_record(second, ledger_path)

            lines = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(lines), 2)
            first_payload = json.loads(lines[0])
            second_payload = json.loads(lines[1])
            self.assertEqual(first_payload["reviewer"], "gov-1")
            self.assertEqual(second_payload["reviewer"], "gov-2")
            summary = ledger_summary(ledger_path)
            self.assertEqual(summary["entries"], 2)
            self.assertEqual(summary["last_claim_status"], "rejected")

    def test_build_proof_report_is_deterministic_with_fixed_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            plan_path = temp_root / "stage2_plan.json"
            ledger_path = temp_root / "decision_ledger.jsonl"
            evidence_path = temp_root / "evidence.txt"

            plan_payload = {
                "claim_label": "proven",
                "deterministic_seed": "abc123",
                "rollback_token": "rbk-abc123",
                "attestation_overall": "proven",
            }
            plan_path.write_text(json.dumps(plan_payload, sort_keys=True), encoding="utf-8")
            evidence_path.write_text("proof", encoding="utf-8")

            request = ForgekeeperRequest(plan_id="bf-plan-ledger", goal="judge", scope="src")
            record = build_decision_record(
                judge_request(request, decision="reject", reason="guarded", reviewer="gov-1")
            )
            append_decision_record(record, ledger_path)

            first = build_proof_report(
                plan_artifact_path=plan_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence_path)],
                generated_at_utc="2026-05-27T19:30:00Z",
            )
            second = build_proof_report(
                plan_artifact_path=plan_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence_path)],
                generated_at_utc="2026-05-27T19:30:00Z",
            )
            self.assertEqual(first, second)
            self.assertEqual(first["plan_artifact"]["claim_label"], "proven")
            self.assertEqual(first["evidence_refs"]["claim_label"], "proven")
            artifacts = [item["artifact"] for item in first["hash_manifest"]]
            self.assertEqual(artifacts, sorted(artifacts))

    def test_build_proof_report_missing_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            missing_plan = temp_root / "missing_plan.json"
            missing_ledger = temp_root / "missing_ledger.jsonl"
            report = build_proof_report(
                plan_artifact_path=missing_plan,
                ledger_path=missing_ledger,
                evidence_refs=[str(temp_root / "missing_evidence.txt")],
                generated_at_utc="2026-05-27T19:31:00Z",
            )
            self.assertEqual(report["claim_label"], "rejected")
            self.assertEqual(report["plan_artifact"]["claim_label"], "rejected")
            self.assertEqual(report["ledger"]["claim_label"], "rejected")
            self.assertEqual(report["evidence_refs"]["claim_label"], "rejected")
            self.assertEqual(report["generated_at_utc"], "2026-05-27T19:31:00Z")

    def test_cli_report_mode_writes_report_and_includes_evidence_refs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            proof_dir = temp_root / "proof"
            proof_dir.mkdir(parents=True, exist_ok=True)
            plan_path = proof_dir / "stage2_attested_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "deterministic_seed": "seed-1",
                        "rollback_token": "rbk-seed-1",
                        "attestation_overall": "proven",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            evidence_path = proof_dir / "evidence-a.txt"
            evidence_path.write_text("ok", encoding="utf-8")
            ledger_path = temp_root / "decision_ledger.jsonl"

            request = ForgekeeperRequest(plan_id="bf-plan-cli-report", goal="judge", scope="src")
            record = build_decision_record(
                judge_request(request, decision="reject", reason="guarded", reviewer="gov-report")
            )
            append_decision_record(record, ledger_path)

            report_path = proof_dir / "report.json"
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "report",
                        "--plan-id",
                        "bf-plan-cli-report",
                        "--scope",
                        "src",
                        "--proof-dir",
                        str(proof_dir),
                        "--ledger-path",
                        str(ledger_path),
                        "--report-path",
                        str(report_path),
                        "--fixed-timestamp",
                        "2026-05-27T19:40:00Z",
                        "--evidence-ref",
                        str(evidence_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["report_version"], "forgekeeper.proof_report.v1")
            self.assertEqual(payload["plan_artifact"]["claim_label"], "proven")
            self.assertTrue(payload["ledger"]["summary"]["entries"] >= 1)
            self.assertEqual(payload["evidence_refs"]["items"][0]["exists"], True)
            written = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(written["report_version"], "forgekeeper.proof_report.v1")
            self.assertEqual(written["generated_at_utc"], "2026-05-27T19:40:00Z")

    def test_cli_report_mode_is_byte_stable_with_fixed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            proof_dir = temp_root / "proof"
            proof_dir.mkdir(parents=True, exist_ok=True)
            plan_path = proof_dir / "stage2_attested_plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "deterministic_seed": "stable-seed",
                        "rollback_token": "rbk-stable-seed",
                        "attestation_overall": "proven",
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            evidence_path = proof_dir / "evidence-b.txt"
            evidence_path.write_text("stable-evidence", encoding="utf-8")
            ledger_path = temp_root / "decision_ledger.jsonl"
            request = ForgekeeperRequest(plan_id="bf-plan-byte-stable", goal="judge", scope="src")
            append_decision_record(
                build_decision_record(
                    judge_request(request, decision="reject", reason="guarded", reviewer="gov-stable")
                ),
                ledger_path,
            )

            report_path = proof_dir / "stable_report.json"
            argv = [
                "--mode",
                "report",
                "--plan-id",
                "bf-plan-byte-stable",
                "--scope",
                "src",
                "--proof-dir",
                str(proof_dir),
                "--ledger-path",
                str(ledger_path),
                "--report-path",
                str(report_path),
                "--fixed-timestamp",
                "2026-05-27T19:45:00Z",
                "--evidence-ref",
                str(evidence_path),
            ]
            with redirect_stdout(io.StringIO()):
                first_code = main(argv)
            first_bytes = report_path.read_bytes()
            with redirect_stdout(io.StringIO()):
                second_code = main(argv)
            second_bytes = report_path.read_bytes()

            self.assertEqual(first_code, 0)
            self.assertEqual(second_code, 0)
            self.assertEqual(first_bytes, second_bytes)

    def test_hash_manifest_order_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "plan.json"
            ledger_path = root / "ledger.jsonl"
            evidence_one = root / "b.txt"
            evidence_two = root / "a.txt"
            plan_path.write_text(
                json.dumps({"claim_label": "proven", "deterministic_seed": "s", "rollback_token": "r"}, sort_keys=True),
                encoding="utf-8",
            )
            evidence_one.write_text("b", encoding="utf-8")
            evidence_two.write_text("a", encoding="utf-8")
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-order", goal="judge", scope="src"),
                        decision="reject",
                        reason="ordered",
                        reviewer="gov-order",
                    )
                ),
                ledger_path,
            )
            report = build_proof_report(
                plan_artifact_path=plan_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence_one), str(evidence_two)],
                generated_at_utc="2026-05-27T19:50:00Z",
            )
            ordered = [f"{item['artifact']}::{item['path']}" for item in report["hash_manifest"]]
            self.assertEqual(ordered, sorted(ordered))

    def test_status_includes_report_sha_and_claim_label(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "forgekeeper_report.json"
            report_path.write_text(
                json.dumps({"claim_label": "proven", "report_version": "forgekeeper.proof_report.v1"}, sort_keys=True),
                encoding="utf-8",
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-001",
                        "--scope",
                        "src",
                        "--report-path",
                        str(report_path),
                        "--ledger-path",
                        str(root / "missing-ledger.jsonl"),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["report_claim_label"], "proven")
            self.assertTrue(bool(payload["report_sha256"]))

    def test_build_snapshot_index_integrity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            report_path.write_text(
                json.dumps({"claim_label": "proven", "report_version": "forgekeeper.proof_report.v1"}, sort_keys=True),
                encoding="utf-8",
            )
            ledger_path = root / "ledger.jsonl"
            request = ForgekeeperRequest(plan_id="bf-snap-001", goal="judge", scope="src")
            append_decision_record(
                build_decision_record(
                    judge_request(request, decision="reject", reason="safe", reviewer="gov-snap")
                ),
                ledger_path,
            )
            evidence = root / "evidence.txt"
            evidence.write_text("proof", encoding="utf-8")
            snapshot = build_snapshot_index(
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence)],
                created_at_utc="2026-05-27T21:00:00Z",
            )
            self.assertEqual(snapshot["snapshot_version"], "forgekeeper.snapshot.v1")
            self.assertEqual(snapshot["created_at_utc"], "2026-05-27T21:00:00Z")
            self.assertEqual(snapshot["report"]["claim_label"], "proven")
            self.assertEqual(snapshot["ledger"]["claim_label"], "proven")
            self.assertEqual(snapshot["evidence_refs"]["claim_label"], "proven")
            self.assertTrue(snapshot["immutable_metadata"])
            self.assertTrue(snapshot["snapshot_id"].startswith("snap-"))

    def test_snapshot_is_deterministic_with_fixed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-snap-002", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-snap",
                    )
                ),
                ledger_path,
            )
            evidence = root / "evidence.txt"
            evidence.write_text("proof", encoding="utf-8")

            first = build_snapshot_index(
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence)],
                created_at_utc="2026-05-27T21:05:00Z",
            )
            second = build_snapshot_index(
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[str(evidence)],
                created_at_utc="2026-05-27T21:05:00Z",
            )
            self.assertEqual(first, second)

    def test_snapshot_missing_artifacts_marked_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot = build_snapshot_index(
                report_path=root / "missing-report.json",
                ledger_path=root / "missing-ledger.jsonl",
                evidence_refs=[str(root / "missing-evidence.txt")],
                created_at_utc="2026-05-27T21:06:00Z",
            )
            self.assertEqual(snapshot["claim_label"], "rejected")
            self.assertEqual(snapshot["report"]["claim_label"], "rejected")
            self.assertEqual(snapshot["ledger"]["claim_label"], "rejected")
            self.assertEqual(snapshot["evidence_refs"]["claim_label"], "rejected")

    def test_cli_snapshot_mode_writes_snapshot_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-snap-cli", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-snap-cli",
                    )
                ),
                ledger_path,
            )
            evidence = root / "evidence.txt"
            evidence.write_text("proof", encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "snapshot",
                        "--plan-id",
                        "bf-snap-cli",
                        "--scope",
                        "src",
                        "--report-path",
                        str(report_path),
                        "--ledger-path",
                        str(ledger_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--fixed-timestamp",
                        "2026-05-27T21:10:00Z",
                        "--evidence-ref",
                        str(evidence),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["claim_label"], "proven")
            self.assertEqual(payload["created_at_utc"], "2026-05-27T21:10:00Z")
            written = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(written["snapshot_version"], "forgekeeper.snapshot.v1")

    def test_status_includes_snapshot_linkage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            snapshot_path = root / "snapshot.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path.write_text(
                json.dumps({"claim_label": "asserted", "snapshot_id": "snap-test"}, sort_keys=True),
                encoding="utf-8",
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-snap",
                        "--scope",
                        "src",
                        "--report-path",
                        str(report_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--ledger-path",
                        str(root / "missing-ledger.jsonl"),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["snapshot_claim_label"], "asserted")
            self.assertEqual(payload["snapshot_id"], "snap-test")
            self.assertTrue(bool(payload["snapshot_sha256"]))

    def test_snapshot_index_append_only_integrity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps({"snapshot_id": "snap-a", "claim_label": "proven"}, sort_keys=True),
                encoding="utf-8",
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-sidx-1", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-sidx",
                    )
                ),
                ledger_path,
            )
            index_path = root / "snapshot_index.jsonl"
            first = build_snapshot_index_record(
                snapshot_path=snapshot_path,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[],
                created_at_utc="2026-05-27T21:30:00Z",
            )
            append_snapshot_index_record(first, index_path)
            second = build_snapshot_index_record(
                snapshot_path=snapshot_path,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[],
                previous_entry=first,
                created_at_utc="2026-05-27T21:31:00Z",
            )
            append_snapshot_index_record(second, index_path)
            lines = [line for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(lines), 2)
            summary = snapshot_index_summary(index_path)
            self.assertEqual(summary["entries"], 2)

    def test_snapshot_index_deterministic_with_fixed_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps({"snapshot_id": "snap-fixed", "claim_label": "proven"}, sort_keys=True),
                encoding="utf-8",
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-sidx-2", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-sidx",
                    )
                ),
                ledger_path,
            )
            previous = {"snapshot_id": "snap-prev", "claim_label": "asserted"}
            first = build_snapshot_index_record(
                snapshot_path=snapshot_path,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[str(report_path)],
                previous_entry=previous,
                supersedes_snapshot_id="snap-prev",
                created_at_utc="2026-05-27T21:32:00Z",
            )
            second = build_snapshot_index_record(
                snapshot_path=snapshot_path,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[str(report_path)],
                previous_entry=previous,
                supersedes_snapshot_id="snap-prev",
                created_at_utc="2026-05-27T21:32:00Z",
            )
            self.assertEqual(first, second)
            self.assertEqual(first["claim_transition"], "asserted->proven")

    def test_snapshot_index_supersession_chain_integrity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_a = root / "snapshot_a.json"
            snapshot_b = root / "snapshot_b.json"
            snapshot_a.write_text(
                json.dumps({"snapshot_id": "snap-a", "claim_label": "asserted"}, sort_keys=True),
                encoding="utf-8",
            )
            snapshot_b.write_text(
                json.dumps({"snapshot_id": "snap-b", "claim_label": "proven"}, sort_keys=True),
                encoding="utf-8",
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-sidx-3", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-sidx",
                    )
                ),
                ledger_path,
            )
            first = build_snapshot_index_record(
                snapshot_path=snapshot_a,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[],
                created_at_utc="2026-05-27T21:33:00Z",
            )
            second = build_snapshot_index_record(
                snapshot_path=snapshot_b,
                report_path=report_path,
                ledger_path=ledger_path,
                evidence_refs=[],
                previous_entry=first,
                created_at_utc="2026-05-27T21:34:00Z",
            )
            self.assertEqual(second["supersedes_snapshot_id"], "snap-a")
            self.assertEqual(second["claim_transition"], "asserted->asserted")

    def test_snapshot_index_missing_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = build_snapshot_index_record(
                snapshot_path=root / "missing-snapshot.json",
                report_path=root / "missing-report.json",
                ledger_path=root / "missing-ledger.jsonl",
                evidence_refs=[str(root / "missing-evidence.txt")],
                created_at_utc="2026-05-27T21:35:00Z",
            )
            self.assertEqual(record["claim_label"], "rejected")
            self.assertEqual(record["claim_transition"], "origin->rejected")

    def test_cli_snapshot_index_mode_writes_append_only_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps({"snapshot_id": "snap-cli", "claim_label": "proven"}, sort_keys=True),
                encoding="utf-8",
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-sidx-cli", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-sidx",
                    )
                ),
                ledger_path,
            )
            index_path = root / "snapshot_index.jsonl"
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "snapshot-index",
                        "--plan-id",
                        "bf-sidx-cli",
                        "--scope",
                        "src",
                        "--snapshot-path",
                        str(snapshot_path),
                        "--report-path",
                        str(report_path),
                        "--ledger-path",
                        str(ledger_path),
                        "--snapshot-index-path",
                        str(index_path),
                        "--fixed-timestamp",
                        "2026-05-27T21:40:00Z",
                        "--evidence-ref",
                        str(report_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertTrue(payload["index_appended"])
            lines = [line for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(lines), 1)

    def test_status_includes_snapshot_index_linkage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-001",
                        "snapshot_id": "snap-a",
                        "claim_transition": "origin->asserted",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-index",
                        "--scope",
                        "src",
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["snapshot_index"]["entries"], 1)
            self.assertTrue(bool(payload["snapshot_index_sha256"]))

    def test_status_includes_snapshot_index_recent_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {"index_id": "snapidx-1", "snapshot_id": "snap-1", "claim_transition": "origin->asserted"},
                {"index_id": "snapidx-2", "snapshot_id": "snap-2", "claim_transition": "asserted->proven"},
                {"index_id": "snapidx-3", "snapshot_id": "snap-3", "claim_transition": "proven->proven"},
                {"index_id": "snapidx-4", "snapshot_id": "snap-4", "claim_transition": "proven->rejected"},
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-index-recent",
                        "--scope",
                        "src",
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(len(payload["snapshot_index_recent"]), 3)
            self.assertEqual(payload["snapshot_index_recent"][-1]["index_id"], "snapidx-4")

    def test_snapshot_query_missing_index_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = query_snapshot_index(
                index_path=root / "missing-index.jsonl",
                snapshot_id="snap-any",
                claim_label="proven",
                since_utc="2026-05-27T22:00:00Z",
                limit=5,
            )
            self.assertEqual(result["claim_label"], "rejected")
            self.assertEqual(result["matched_count"], 0)

    def test_snapshot_query_filters_and_determinism(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {
                    "index_id": "snapidx-a",
                    "snapshot_id": "snap-a",
                    "claim_label": "asserted",
                    "created_at_utc": "2026-05-27T21:00:00Z",
                    "claim_transition": "origin->asserted",
                },
                {
                    "index_id": "snapidx-b",
                    "snapshot_id": "snap-b",
                    "claim_label": "proven",
                    "created_at_utc": "2026-05-27T21:10:00Z",
                    "claim_transition": "asserted->proven",
                },
                {
                    "index_id": "snapidx-c",
                    "snapshot_id": "snap-c",
                    "claim_label": "proven",
                    "created_at_utc": "2026-05-27T21:20:00Z",
                    "claim_transition": "proven->proven",
                },
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            first = query_snapshot_index(
                index_path=index_path,
                claim_label="proven",
                since_utc="2026-05-27T21:05:00Z",
                limit=2,
            )
            second = query_snapshot_index(
                index_path=index_path,
                claim_label="proven",
                since_utc="2026-05-27T21:05:00Z",
                limit=2,
            )
            self.assertEqual(first, second)
            self.assertEqual(first["claim_label"], "proven")
            self.assertEqual(first["matched_count"], 2)
            self.assertEqual(first["results"][0]["index_id"], "snapidx-b")
            self.assertEqual(first["results"][1]["index_id"], "snapidx-c")

    def test_snapshot_query_is_read_only_for_index_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-ro",
                        "snapshot_id": "snap-ro",
                        "claim_label": "proven",
                        "created_at_utc": "2026-05-27T21:30:00Z",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            before = index_path.read_bytes()
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "snapshot-query",
                        "--plan-id",
                        "bf-query-ro",
                        "--scope",
                        "src",
                        "--snapshot-index-path",
                        str(index_path),
                        "--query-limit",
                        "1",
                    ]
                )
            self.assertEqual(exit_code, 0)
            after = index_path.read_bytes()
            self.assertEqual(before, after)

    def test_trace_query_filters_and_determinism(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-trace-001", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-a",
                    )
                ),
                ledger_path,
            )
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-trace-002", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-b",
                    )
                ),
                ledger_path,
            )
            ledger_hash = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

            report_path = root / "report.json"
            report_path.write_text(
                json.dumps(
                    {"claim_label": "proven", "generated_at_utc": "2026-05-27T23:15:00Z"},
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()

            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "snapshot_id": "snap-trace",
                        "linkage": {"report_hash": report_hash, "ledger_hash": ledger_hash},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            snapshot_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()

            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-trace",
                        "claim_label": "proven",
                        "claim_transition": "proven->proven",
                        "report_sha256": report_hash,
                        "ledger_sha256": ledger_hash,
                        "snapshot_sha256": snapshot_hash,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            first = query_governance_trace(
                ledger_path=ledger_path,
                report_path=report_path,
                snapshot_path=snapshot_path,
                index_path=index_path,
                ledger_claim_status="rejected",
                reviewer="gov-b",
                since_utc="2026-05-27T00:00:00Z",
                limit=5,
            )
            second = query_governance_trace(
                ledger_path=ledger_path,
                report_path=report_path,
                snapshot_path=snapshot_path,
                index_path=index_path,
                ledger_claim_status="rejected",
                reviewer="gov-b",
                since_utc="2026-05-27T00:00:00Z",
                limit=5,
            )
            self.assertEqual(first, second)
            self.assertEqual(first["claim_label"], "proven")
            self.assertEqual(first["ledger"]["matched_count"], 1)
            self.assertEqual(first["ledger"]["results"][0]["reviewer"], "gov-b")
            self.assertEqual(first["traceability_checks"]["claim_label"], "proven")

    def test_trace_query_missing_artifacts_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = query_governance_trace(
                ledger_path=root / "missing-ledger.jsonl",
                report_path=root / "missing-report.json",
                snapshot_path=root / "missing-snapshot.json",
                index_path=root / "missing-index.jsonl",
                ledger_claim_status="rejected",
                limit=3,
            )
            self.assertEqual(payload["claim_label"], "rejected")
            self.assertEqual(payload["ledger"]["claim_label"], "rejected")
            self.assertEqual(payload["report"]["claim_label"], "rejected")
            self.assertEqual(payload["snapshot"]["claim_label"], "rejected")
            self.assertEqual(payload["snapshot_index"]["claim_label"], "rejected")

    def test_trace_query_rejects_linkage_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-trace-003", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-a",
                    )
                ),
                ledger_path,
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "snapshot_id": "snap-mismatch",
                        "linkage": {"report_hash": "bad", "ledger_hash": "bad"},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-mismatch",
                        "claim_label": "proven",
                        "claim_transition": "asserted->proven",
                        "report_sha256": "bad",
                        "ledger_sha256": "bad",
                        "snapshot_sha256": "bad",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            payload = query_governance_trace(
                ledger_path=ledger_path,
                report_path=report_path,
                snapshot_path=snapshot_path,
                index_path=index_path,
            )
            self.assertEqual(payload["traceability_checks"]["claim_label"], "rejected")
            self.assertEqual(payload["claim_label"], "rejected")

    def test_cli_trace_query_mode_outputs_correlation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-trace-cli", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-cli",
                    )
                ),
                ledger_path,
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps({"claim_label": "asserted", "snapshot_id": "snap-cli"}, sort_keys=True),
                encoding="utf-8",
            )
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps({"index_id": "snapidx-cli", "claim_label": "asserted"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "trace-query",
                        "--plan-id",
                        "bf-trace-cli",
                        "--scope",
                        "src",
                        "--ledger-path",
                        str(ledger_path),
                        "--report-path",
                        str(report_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--snapshot-index-path",
                        str(index_path),
                        "--query-ledger-claim-status",
                        "rejected",
                        "--query-reviewer",
                        "gov-cli",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["mode"], "trace-query")
            self.assertEqual(payload["ledger"]["matched_count"], 1)
            self.assertIn("traceability_checks", payload)

    def test_reconcile_query_detects_drift_and_recommendations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-recon-001", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-recon",
                    )
                ),
                ledger_path,
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "snapshot_id": "snap-recon",
                        "linkage": {"report_hash": "bad", "ledger_hash": "bad"},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-recon",
                        "claim_label": "proven",
                        "claim_transition": "asserted->proven",
                        "report_sha256": "bad",
                        "ledger_sha256": "bad",
                        "snapshot_sha256": "bad",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            payload = query_governance_reconciliation(
                plan_id="bf-recon-001",
                ledger_path=ledger_path,
                report_path=report_path,
                snapshot_path=snapshot_path,
                index_path=index_path,
            )
            self.assertEqual(payload["mode"], "reconcile-query")
            self.assertEqual(payload["claim_label"], "rejected")
            self.assertGreaterEqual(payload["drift_count"], 1)
            action_ids = [item["action_id"] for item in payload["recommendations"]]
            self.assertIn("rebuild-snapshot", action_ids)
            self.assertIn("append-snapshot-index", action_ids)

    def test_reconcile_query_clean_state_no_action_required(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-recon-002", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-recon",
                    )
                ),
                ledger_path,
            )
            ledger_hash = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
            report_path = root / "report.json"
            report_path.write_text(
                json.dumps({"claim_label": "proven", "generated_at_utc": "2026-05-27T23:50:00Z"}, sort_keys=True),
                encoding="utf-8",
            )
            report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "snapshot_id": "snap-recon-clean",
                        "linkage": {"report_hash": report_hash, "ledger_hash": ledger_hash},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            snapshot_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-recon-clean",
                        "claim_label": "proven",
                        "claim_transition": "proven->proven",
                        "report_sha256": report_hash,
                        "ledger_sha256": ledger_hash,
                        "snapshot_sha256": snapshot_hash,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            payload = query_governance_reconciliation(
                plan_id="bf-recon-002",
                ledger_path=ledger_path,
                report_path=report_path,
                snapshot_path=snapshot_path,
                index_path=index_path,
            )
            self.assertEqual(payload["claim_label"], "proven")
            self.assertEqual(payload["drift_count"], 0)
            self.assertEqual(payload["recommendations"][0]["action_id"], "no-action-required")
            self.assertEqual(payload["recommendation_claim_label"], "proven")

    def test_cli_reconcile_query_mode_outputs_recommendations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "decision_ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-recon-cli", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-recon",
                    )
                ),
                ledger_path,
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(json.dumps({"claim_label": "asserted"}, sort_keys=True), encoding="utf-8")
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text("", encoding="utf-8")

            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "reconcile-query",
                        "--plan-id",
                        "bf-recon-cli",
                        "--scope",
                        "src",
                        "--ledger-path",
                        str(ledger_path),
                        "--report-path",
                        str(report_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["mode"], "reconcile-query")
            self.assertIn("recommendations", payload)
            self.assertTrue(len(payload["recommendations"]) >= 1)

    def test_drift_window_query_transitions_improving(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {"index_id": "snapidx-1", "claim_label": "asserted", "claim_transition": "origin->asserted", "created_at_utc": "2026-05-27T21:00:00Z"},
                {"index_id": "snapidx-2", "claim_label": "proven", "claim_transition": "asserted->proven", "created_at_utc": "2026-05-27T21:10:00Z"},
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            payload = query_drift_window(index_path=index_path, since_utc="2026-05-27T20:00:00Z", limit=5)
            self.assertEqual(payload["claim_label"], "proven")
            self.assertEqual(payload["trend"], "improving")
            self.assertEqual(payload["entries"], 2)

    def test_drift_window_query_transitions_degrading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {"index_id": "snapidx-1", "claim_label": "proven", "claim_transition": "origin->proven", "created_at_utc": "2026-05-27T21:00:00Z"},
                {"index_id": "snapidx-2", "claim_label": "rejected", "claim_transition": "proven->rejected", "created_at_utc": "2026-05-27T21:10:00Z"},
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            payload = query_drift_window(index_path=index_path, since_utc="2026-05-27T20:00:00Z", limit=5)
            self.assertEqual(payload["claim_label"], "rejected")
            self.assertEqual(payload["trend"], "degrading")
            self.assertEqual(payload["trend_basis"], "pair")
            self.assertIn("proven->rejected", payload["drift_transitions"])

    def test_drift_window_pair_only_ignores_old_window_degradation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {"index_id": "snapidx-1", "claim_label": "proven", "claim_transition": "origin->proven", "created_at_utc": "2026-05-27T20:00:00Z"},
                {"index_id": "snapidx-2", "claim_label": "asserted", "claim_transition": "proven->asserted", "created_at_utc": "2026-05-27T21:00:00Z"},
                {"index_id": "snapidx-3", "claim_label": "proven", "claim_transition": "asserted->proven", "created_at_utc": "2026-05-27T22:00:00Z"},
                {"index_id": "snapidx-4", "claim_label": "proven", "claim_transition": "proven->proven", "created_at_utc": "2026-05-27T23:00:00Z"},
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            payload = query_drift_window(index_path=index_path, limit=10, pair_only=True)
            self.assertEqual(payload["trend_basis"], "pair")
            self.assertEqual(payload["trend_pair"], ["proven", "proven"])
            self.assertIn(payload["trend"], {"stable", "recovered"})
            self.assertNotEqual(payload["trend"], "degrading")

    def test_cli_drift_window_query_mode_outputs_window(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps(
                    {
                        "index_id": "snapidx-cli-window",
                        "claim_label": "asserted",
                        "claim_transition": "origin->asserted",
                        "created_at_utc": "2026-05-27T21:20:00Z",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "drift-window-query",
                        "--plan-id",
                        "bf-drift-window-cli",
                        "--scope",
                        "src",
                        "--snapshot-index-path",
                        str(index_path),
                        "--query-limit",
                        "3",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["mode"], "drift-window-query")
            self.assertEqual(payload["entries"], 1)

    def test_status_includes_traceability_flags(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text(
                json.dumps({"index_id": "snapidx-trace", "claim_label": "proven"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-status-trace", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-status",
                    )
                ),
                ledger_path,
            )
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-trace",
                        "--scope",
                        "src",
                        "--ledger-path",
                        str(ledger_path),
                        "--report-path",
                        str(report_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertTrue(payload["traceability"]["report_exists"])
            self.assertTrue(payload["traceability"]["snapshot_exists"])
            self.assertTrue(payload["traceability"]["snapshot_index_exists"])
            self.assertTrue(payload["traceability"]["ledger_exists"])

    def test_status_includes_traceability_drift_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger_path = root / "ledger.jsonl"
            append_decision_record(
                build_decision_record(
                    judge_request(
                        ForgekeeperRequest(plan_id="bf-status-drift", goal="judge", scope="src"),
                        decision="reject",
                        reason="safe",
                        reviewer="gov-status",
                    )
                ),
                ledger_path,
            )
            report_path = root / "report.json"
            report_path.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot_path = root / "snapshot.json"
            snapshot_path.write_text(
                json.dumps({"claim_label": "proven", "linkage": {"report_hash": "bad", "ledger_hash": "bad"}}, sort_keys=True),
                encoding="utf-8",
            )
            index_path = root / "snapshot_index.jsonl"
            index_path.write_text("", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-drift",
                        "--scope",
                        "src",
                        "--ledger-path",
                        str(ledger_path),
                        "--report-path",
                        str(report_path),
                        "--snapshot-path",
                        str(snapshot_path),
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertTrue(payload["traceability_drift"]["drift_detected"])
            self.assertIn("snapshot_report_hash_match", payload["traceability_drift"]["drift_checks"])

    def test_status_includes_snapshot_index_window_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / "snapshot_index.jsonl"
            rows = [
                {"index_id": "snapidx-1", "claim_label": "asserted", "claim_transition": "origin->asserted"},
                {"index_id": "snapidx-2", "claim_label": "proven", "claim_transition": "asserted->proven"},
                {"index_id": "snapidx-3", "claim_label": "rejected", "claim_transition": "proven->rejected"},
            ]
            index_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "status",
                        "--plan-id",
                        "bf-status-window",
                        "--scope",
                        "src",
                        "--snapshot-index-path",
                        str(index_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["snapshot_index_window"]["entries"], 3)
            self.assertEqual(payload["snapshot_index_window"]["rejected_count"], 1)

    def test_latest_plan_artifact_returns_newest_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "a_plan.json"
            second = root / "z_plan.json"
            first.write_text("{}", encoding="utf-8")
            second.write_text("{}", encoding="utf-8")
            os.utime(first, (1000, 1000))
            os.utime(second, (2000, 2000))
            newest = latest_plan_artifact(root)
            self.assertIsNotNone(newest)
            self.assertEqual(newest.name, "z_plan.json")


class TestForgekeeperVerifyAndChaos(unittest.TestCase):
    """Stage 4-prep verification and adversarial read-only drills."""

    def test_build_verification_report_includes_presence_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir(parents=True)
            (proof_dir / "stage2_dry_run_plan.json").write_text("{}", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            ledger.write_text("", encoding="utf-8")
            report = root / "report.json"
            report.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot = root / "snapshot.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "claim_label": "proven",
                        "linkage": {
                            "report_hash": hashlib.sha256(report.read_bytes()).hexdigest().upper(),
                            "ledger_hash": hashlib.sha256(ledger.read_bytes()).hexdigest().upper(),
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            index = root / "index.jsonl"
            index.write_text("", encoding="utf-8")
            payload = build_verification_report(
                plan_id="bf-verify-001",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
            )
            self.assertEqual(payload["mode"], "verify")
            self.assertIn(payload["claim_label"], {"asserted", "proven", "rejected"})
            self.assertGreaterEqual(len(payload["presence_checks"]), 5)
            self.assertIn("verification_steps", payload)

    def test_cross_machine_replay_inactive_by_default(self):
        env_before = os.environ.pop("FORGE_CROSS_MACHINE_REPLAY_ACTIVE", None)
        try:
            status = cross_machine_replay_status()
            self.assertTrue(status["scaffold_built"])
            self.assertEqual(status["operational_status"], "inactive")
            self.assertEqual(status["claim_label"], "asserted")
            self.assertFalse(status["activation_env_set"])
        finally:
            if env_before is not None:
                os.environ["FORGE_CROSS_MACHINE_REPLAY_ACTIVE"] = env_before

    def test_verify_includes_cross_machine_inactive_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir()
            payload = build_verification_report(
                plan_id="bf-xm-inactive",
                proof_dir=proof_dir,
                ledger_path=root / "ledger.jsonl",
                report_path=root / "report.json",
                snapshot_path=root / "snapshot.json",
                index_path=root / "index.jsonl",
            )
            xm = payload["cross_machine_replay"]
            self.assertEqual(xm["operational_status"], "inactive")

    def test_run_chaos_checks_all_scenarios_pass(self):
        payload = run_chaos_checks()
        self.assertEqual(payload["mode"], "chaos-check")
        self.assertEqual(payload["scenarios_run"], 3)
        self.assertEqual(payload["scenarios_passed"], 3)
        self.assertEqual(payload["claim_label"], "proven")
        for item in payload["results"]:
            self.assertTrue(item["passed"])

    def test_cli_verify_mode(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(
                [
                    "--mode",
                    "verify",
                    "--plan-id",
                    "bf-verify-cli",
                    "--scope",
                    ".",
                ]
            )
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["mode"], "verify")

    def test_verify_write_report_is_deterministic_with_fixed_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir()
            (proof_dir / "plan.json").write_text("{}", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            ledger.write_text("", encoding="utf-8")
            report = root / "report.json"
            report.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot = root / "snapshot.json"
            snapshot.write_text(json.dumps({"claim_label": "proven", "linkage": {}}, sort_keys=True), encoding="utf-8")
            index = root / "index.jsonl"
            index.write_text("", encoding="utf-8")
            out_a = root / "verify_a.json"
            out_b = root / "verify_b.json"
            fixed = "2026-05-28T12:00:00Z"
            base = [
                "--mode",
                "verify",
                "--plan-id",
                "bf-verify-deterministic",
                "--scope",
                ".",
                "--proof-dir",
                str(proof_dir),
                "--ledger-path",
                str(ledger),
                "--report-path",
                str(report),
                "--snapshot-path",
                str(snapshot),
                "--snapshot-index-path",
                str(index),
                "--fixed-timestamp",
                fixed,
            ]
            self.assertEqual(main(base + ["--write-report", str(out_a)]), 0)
            self.assertEqual(main(base + ["--write-report", str(out_b)]), 0)
            bytes_a = out_a.read_bytes()
            bytes_b = out_b.read_bytes()
            self.assertEqual(bytes_a, bytes_b)
            payload = json.loads(bytes_a.decode("utf-8"))
            self.assertEqual(payload["generated_at_utc"], fixed)
            self.assertEqual(payload["cross_machine_replay"]["operational_status"], "inactive")

    def test_cli_chaos_check_mode(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = main(["--mode", "chaos-check", "--plan-id", "bf-chaos-cli", "--scope", "."])
        self.assertEqual(exit_code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["mode"], "chaos-check")
        self.assertEqual(payload["claim_label"], "proven")

    def test_bundle_export_manifest_sorted_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir()
            (proof_dir / "z_plan.json").write_text("{}", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            ledger.write_text("", encoding="utf-8")
            report = root / "report.json"
            report.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            snapshot = root / "snapshot.json"
            snapshot.write_text(json.dumps({"claim_label": "proven", "linkage": {}}, sort_keys=True), encoding="utf-8")
            index = root / "index.jsonl"
            index.write_text("", encoding="utf-8")
            verify = root / "verify.json"
            verify.write_text(json.dumps({"claim_label": "asserted"}, sort_keys=True), encoding="utf-8")
            fixed = "2026-05-28T12:00:00Z"
            one = build_bundle_export_manifest(
                plan_id="bf-bundle",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
                verify_report_path=verify,
                generated_at_utc=fixed,
            )
            two = build_bundle_export_manifest(
                plan_id="bf-bundle",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
                verify_report_path=verify,
                generated_at_utc=fixed,
            )
            self.assertEqual(one["generated_at_utc"], fixed)
            self.assertEqual(one["hash_manifest"], two["hash_manifest"])
            artifacts = [item["artifact"] for item in one["hash_manifest"]]
            self.assertEqual(artifacts, sorted(artifacts))

    def test_run_reconcile_artifacts_clears_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir()
            plan = proof_dir / "plan.json"
            plan.write_text(json.dumps({"claim_label": "proven"}, sort_keys=True), encoding="utf-8")
            ledger = root / "ledger.jsonl"
            ledger.write_text(
                json.dumps(
                    {
                        "record_id": "r1",
                        "recorded_at_utc": "2026-05-28T00:00:00Z",
                        "mode": "judge",
                        "decision": "reject",
                        "claim_status": "rejected",
                        "evidence_refs": [],
                        "reviewer": "t",
                        "reason": "x",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            report = root / "report.json"
            report.write_text("{}", encoding="utf-8")
            snapshot = root / "snapshot.json"
            snapshot.write_text(
                json.dumps({"claim_label": "proven", "linkage": {"report_hash": "bad", "ledger_hash": "bad"}}, sort_keys=True),
                encoding="utf-8",
            )
            index = root / "index.jsonl"
            index.write_text("", encoding="utf-8")
            payload = run_reconcile_artifacts(
                plan_id="bf-reconcile-test",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
                plan_artifact_path=plan,
                generated_at_utc="2026-05-28T12:00:00Z",
            )
            self.assertEqual(payload["mode"], "reconcile-artifacts")
            self.assertEqual(int(payload["post_reconcile"]["drift_count"]), 0)

    def test_verify_uses_artifact_sync_not_claim_trend(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            proof_dir = root / "proof"
            proof_dir.mkdir()
            plan = proof_dir / "plan.json"
            plan.write_text("{}", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            ledger.write_text("", encoding="utf-8")
            report = root / "report.json"
            snapshot = root / "snapshot.json"
            index = root / "index.jsonl"
            run_reconcile_artifacts(
                plan_id="bf-verify-sync",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
                plan_artifact_path=plan,
                generated_at_utc="2026-05-28T12:00:00Z",
            )
            payload = build_verification_report(
                plan_id="bf-verify-sync",
                proof_dir=proof_dir,
                ledger_path=ledger,
                report_path=report,
                snapshot_path=snapshot,
                index_path=index,
                generated_at_utc="2026-05-28T12:00:00Z",
            )
            self.assertEqual(payload["artifact_sync_claim_label"], "proven")

    def test_cli_bundle_export_writes_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out = root / "bundle.json"
            stream = io.StringIO()
            with redirect_stdout(stream):
                exit_code = main(
                    [
                        "--mode",
                        "bundle-export",
                        "--plan-id",
                        "bf-bundle-cli",
                        "--scope",
                        ".",
                        "--fixed-timestamp",
                        "2026-05-28T12:00:00Z",
                        "--write-bundle-export",
                        str(out),
                        "--verify-report-path",
                        str(root / "missing_verify.json"),
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertTrue(out.exists())
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["mode"], "bundle-export")
            self.assertIn("bundle_export_sha256", payload)


if __name__ == "__main__":
    unittest.main()
