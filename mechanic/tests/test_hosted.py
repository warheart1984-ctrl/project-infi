"""Tests for the Mechanic hosted pilot surface."""

from __future__ import annotations

import json
import hmac
import hashlib
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from mechanic.hosted.api import create_app
from mechanic.hosted.control_plane import HostedMechanicService
from mechanic.hosted.github_app import GitHubAppClient
from mechanic.hosted.models import SignoffPolicy
from mechanic.hosted.obd_report import build_obd_report
from mechanic.hosted.security import hash_api_key, redact_json, verify_github_webhook_signature
from mechanic.hosted.smoke import run_stubbed_smoke
from mechanic.hosted.stubs import create_stubbed_service
from mechanic.hosted.trace_import import import_trace_file, normalize_trace_records
from mechanic.hosted.worker import run_hosted_scan
from mechanic.hosted.worker import replay_scan

FIXTURE_REPO = Path(__file__).resolve().parents[1] / "fixtures" / "sample-customer-repo"
SAMPLE_TRACE = Path(__file__).resolve().parents[1] / "fixtures" / "traces" / "sample_trace.ndjson"
LANGSMITH_TRACE = Path(__file__).resolve().parents[1] / "fixtures" / "traces" / "langsmith_export.json"
N8N_TRACE = Path(__file__).resolve().parents[1] / "fixtures" / "traces" / "n8n_export.json"
MAKE_TRACE = Path(__file__).resolve().parents[1] / "fixtures" / "traces" / "make_export.json"
CURSOR_TRACE = Path(__file__).resolve().parents[1] / "fixtures" / "traces" / "cursor_export.json"


class TestHostedModels(unittest.TestCase):
    def test_signoff_policy_defaults(self):
        policy = SignoffPolicy()
        drift = {"severity": "high", "ma13_class": "II"}
        self.assertTrue(policy.requires_signoff(drift))
        self.assertEqual(policy.remediation_class(drift), "review_required")


class TestHostedTraceImport(unittest.TestCase):
    def test_langsmith_trace_normalizes_to_model_node(self):
        records = normalize_trace_records(
            source="langsmith",
            payload={"runs": [{"id": "r1", "run_type": "llm", "name": "planner", "model": "gpt-x"}]},
            source_name="langsmith.json",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["model_call"], "planner")
        self.assertEqual(records[0]["source_system"], "langsmith")

    def test_n8n_trace_normalizes_to_tool_node(self):
        records = normalize_trace_records(
            source="n8n",
            payload={"executions": [{"id": "n1", "name": "deploy", "operation": "http"}]},
            source_name="n8n.json",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["tool_call"], "deploy")

    def test_vendor_fixtures_import_to_ndjson(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixtures = [
                ("langsmith", LANGSMITH_TRACE),
                ("n8n", N8N_TRACE),
                ("make", MAKE_TRACE),
                ("cursor", CURSOR_TRACE),
            ]
            for source, fixture in fixtures:
                output = Path(tmp) / f"{source}.ndjson"
                result = import_trace_file(source=source, input_path=fixture, output_path=output)
                self.assertGreater(result["record_count"], 0, msg=source)
                self.assertTrue(output.is_file(), msg=source)


class TestHostedObdReport(unittest.TestCase):
    def test_obd_report_classifies_signoff_and_owner(self):
        scan = {
            "drifts": [
                {
                    "code": "RNT-20",
                    "family": "RNT",
                    "severity": "high",
                    "ma13_class": "III",
                    "drift_summary": "tool trace missing audit",
                    "evidence": {"source_path": "traces/session.ndjson"},
                }
            ]
        }
        report = build_obd_report(case_id="case", scan=scan, policy=SignoffPolicy())
        self.assertEqual(report["top_risk_class"], "red")
        self.assertEqual(report["requires_human_signoff_count"], 1)
        self.assertEqual(report["findings"][0]["likely_owner"], "AI runtime owner")
        self.assertEqual(report["findings"][0]["remediation_class"], "legal_or_security_signoff")


class TestHostedWorker(unittest.TestCase):
    def test_worker_emits_evidence_bundle_and_does_not_mutate_repo(self):
        before = (FIXTURE_REPO / "agent_bot.py").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            bundle = run_hosted_scan(
                case_id="hosted-worker",
                scan_id="scan-hosted-worker",
                repo_path=FIXTURE_REPO,
                artifact_dir=tmp,
                trace_paths=[SAMPLE_TRACE],
            )
            case_dir = Path(bundle.artifact_dir)
            self.assertTrue((case_dir / "evidence_bundle.v1.json").is_file())
            self.assertTrue((case_dir / "mechanic_obd_report.v1.json").is_file())
            self.assertEqual(bundle.confidence_label, "local_proven")
            self.assertFalse(bundle.customer_repo_mutated)
        after = (FIXTURE_REPO / "agent_bot.py").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_worker_rejects_oversized_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                run_hosted_scan(
                    case_id="hosted-too-big",
                    scan_id="scan-too-big",
                    repo_path=FIXTURE_REPO,
                    artifact_dir=tmp,
                    max_repo_bytes=1,
                )

    def test_worker_scrubs_secret_like_trace_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "secret.ndjson"
            trace.write_text('{"id":"s1","tool":"ghp_123456789012345678901234567890123456"}\n', encoding="utf-8")
            bundle = run_hosted_scan(
                case_id="hosted-secret",
                scan_id="scan-secret",
                repo_path=FIXTURE_REPO,
                artifact_dir=tmp,
                trace_paths=[trace],
            )
            genome_text = (Path(bundle.artifact_dir) / "process_genome.v1.json").read_text(encoding="utf-8")
            self.assertIn("[REDACTED]", genome_text)
            self.assertNotIn("ghp_123456789012345678901234567890123456", genome_text)

    def test_ci_replay_is_asserted_without_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = run_hosted_scan(
                case_id="hosted-replay",
                scan_id="scan-replay",
                repo_path=FIXTURE_REPO,
                artifact_dir=tmp,
            )
            result = replay_scan(
                case_id="hosted-replay",
                repo_path=FIXTURE_REPO,
                original_case_dir=Path(bundle.artifact_dir),
                tier="ci",
            )
            self.assertEqual(result["claim_label"], "asserted")
            self.assertTrue(result["external_runner_unavailable"])


class TestHostedControlPlane(unittest.TestCase):
    def test_control_plane_scan_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = HostedMechanicService(artifact_root=tmp)
            installed = service.github_installation_callback(
                {"customer_id": "cust", "org": "org", "repo_id": "org/repo", "installation_id": "inst"}
            )
            self.assertEqual(installed["installation"]["provider"], "github")
            result = service.create_scan(
                {
                    "installation_id": "inst",
                    "scan_id": "scan1",
                    "case_id": "case1",
                    "repo_path": str(FIXTURE_REPO),
                    "trace_paths": [str(SAMPLE_TRACE)],
                }
            )
            self.assertEqual(result["job"]["status"], "complete")
            report = service.get_scan_report("scan1")
            self.assertEqual(report["schema_version"], "mechanic.obd_report.v1")
            artifacts = service.get_scan_artifacts("scan1")
            self.assertEqual(artifacts["bundle_version"], "mechanic.evidence_bundle.v1")
            self.assertIn("signed_artifact_links", artifacts)
            self.assertIn("POST /v1/scans", service.routes())

    def test_control_plane_persists_scan_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "hosted.sqlite3"
            service = HostedMechanicService(artifact_root=Path(tmp) / "artifacts", db_path=db_path)
            service.github_installation_callback(
                {"customer_id": "cust", "org": "org", "repo_id": "org/repo", "installation_id": "inst"}
            )
            service.create_scan(
                {
                    "installation_id": "inst",
                    "scan_id": "scan-persist",
                    "case_id": "case-persist",
                    "repo_path": str(FIXTURE_REPO),
                }
            )
            reopened = HostedMechanicService(artifact_root=Path(tmp) / "artifacts", db_path=db_path)
            self.assertEqual(reopened.get_scan("scan-persist")["status"], "complete")
            self.assertEqual(reopened.get_scan_artifacts("scan-persist")["scan_id"], "scan-persist")


class TestHostedSecurity(unittest.TestCase):
    def test_github_webhook_signature(self):
        body = b'{"ok":true}'
        secret = "webhook-secret"
        sig = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_github_webhook_signature(body=body, signature_header=sig, webhook_secret=secret))
        self.assertFalse(verify_github_webhook_signature(body=body, signature_header=sig, webhook_secret="wrong"))

    def test_github_webhook_payload_adapter(self):
        payload = GitHubAppClient.installation_payload_from_webhook(
            {
                "installation": {"id": 123, "account": {"login": "acme"}},
                "repository": {"full_name": "acme/repo", "default_branch": "main"},
            }
        )
        self.assertEqual(payload["installation_id"], "123")
        self.assertEqual(payload["repo_id"], "acme/repo")

    def test_redact_json_removes_secret_fields(self):
        payload = redact_json({"token": "abc", "nested": {"message": "Bearer abcdefghijklmnopqrstuvwxyz"}})
        self.assertEqual(payload["token"], "[REDACTED]")
        self.assertIn("[REDACTED]", payload["nested"]["message"])


class TestHostedApi(unittest.TestCase):
    def test_api_contract_with_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = HostedMechanicService(artifact_root=Path(tmp) / "artifacts", db_path=Path(tmp) / "db.sqlite3")
            app = create_app(service=service, api_key_hash=hash_api_key("dev-key"))
            client = TestClient(app)
            self.assertEqual(client.get("/healthz").status_code, 200)
            self.assertEqual(client.get("/v1/scans/missing").status_code, 401)
            headers = {"X-API-Key": "dev-key"}
            install = client.post(
                "/v1/installations/github/callback",
                headers=headers,
                json={"customer_id": "cust", "org": "org", "repo_id": "org/repo", "installation_id": "inst"},
            )
            self.assertEqual(install.status_code, 200)
            scan = client.post(
                "/v1/scans",
                headers=headers,
                json={
                    "installation_id": "inst",
                    "scan_id": "api-scan",
                    "case_id": "api-case",
                    "repo_path": str(FIXTURE_REPO),
                    "trace_paths": [str(SAMPLE_TRACE)],
                },
            )
            self.assertEqual(scan.status_code, 200)
            self.assertEqual(client.get("/v1/scans/api-scan", headers=headers).json()["status"], "complete")
            self.assertEqual(
                client.get("/v1/scans/api-scan/report", headers=headers).json()["schema_version"],
                "mechanic.obd_report.v1",
            )

    def test_api_github_signature_required_when_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(
                service=HostedMechanicService(artifact_root=Path(tmp) / "artifacts", db_path=Path(tmp) / "db.sqlite3"),
                api_key_hash=hash_api_key("dev-key"),
                github_webhook_secret="hook-secret",
            )
            client = TestClient(app)
            response = client.post(
                "/v1/installations/github/callback",
                headers={"X-API-Key": "dev-key", "X-Hub-Signature-256": "sha256=bad"},
                json={"repo_id": "org/repo"},
            )
            self.assertEqual(response.status_code, 401)

    def test_api_checkout_scan_without_repo_path_uses_stub_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            service = create_stubbed_service(
                artifact_root=Path(tmp) / "artifacts",
                db_path=Path(tmp) / "db.sqlite3",
                source_repo=FIXTURE_REPO,
            )
            app = create_app(service=service, api_key_hash=hash_api_key("dev-key"))
            client = TestClient(app)
            headers = {"X-API-Key": "dev-key"}
            client.post(
                "/v1/installations/github/callback",
                headers=headers,
                json={"customer_id": "cust", "org": "org", "repo_id": "org/repo", "installation_id": "inst"},
            )
            response = client.post(
                "/v1/scans",
                headers=headers,
                json={
                    "installation_id": "inst",
                    "scan_id": "checkout-scan",
                    "case_id": "checkout-case",
                    "checkout": True,
                    "repo_ref": "main",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["job"]["status"], "complete")


class TestHostedStubSmoke(unittest.TestCase):
    def test_stubbed_external_smoke(self):
        result = run_stubbed_smoke(repo_path=FIXTURE_REPO)
        self.assertTrue(result["ok"])
        self.assertEqual(result["job_status"], "complete")
        self.assertIn(result["confidence_label"], {"local_proven", "asserted"})
        self.assertTrue(result["signed_artifacts"])


if __name__ == "__main__":
    unittest.main()
