"""Tests for UGR + Cloud Forge operator console."""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.ugr.operator_console.snapshot import build_operator_console_snapshot
from src.ugr.operator_console.mesh_health import poll_mesh_health
from src.ugr.operator_console.trace_viewer import load_deliberation_traces
from src.ugr.operator_console.forge_platform import load_forge_platform_dashboard


class TestOperatorConsoleSnapshot(unittest.TestCase):
    def test_snapshot_is_advisory_readout(self):
        snapshot = build_operator_console_snapshot(runtime=None)
        self.assertEqual(snapshot.get("runtime_effect"), "readout_only")
        self.assertIn("ugr", snapshot)
        self.assertIn("cloud_forge", snapshot)
        self.assertIn("debt_register", snapshot)
        self.assertIn("readout", snapshot)
        self.assertIn("mesh_health", snapshot)
        self.assertIn("deliberation_traces", snapshot)
        self.assertIn("forge_platform", snapshot)
        self.assertEqual(snapshot.get("console_version"), "1.2")
        self.assertIn("infinity1", snapshot)
        infinity1 = snapshot.get("infinity1") or {}
        self.assertEqual(infinity1.get("runtime_effect"), "readout_only")
        self.assertIn("seam_stress", infinity1)
        self.assertEqual(snapshot["readout"].get("runtime_effect"), "readout_only")

    def test_trust_bundle_status_from_runtime(self):
        temp_root = Path(tempfile.mkdtemp(prefix="operator-console-trust-"))
        bundle_dir = temp_root / "trust-bundles" / "latest"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "bundle_id": "ugr-trust-bundle-organ-v1",
            "overall_status": "pass",
            "generated_at_utc": "2026-05-28T18:00:00Z",
        }
        serialized = json.dumps(payload, sort_keys=True)
        (bundle_dir / "proof_bundle.json").write_text(serialized + "\n", encoding="utf-8")
        (bundle_dir / "proof_bundle.sha256").write_text("abc123\n", encoding="utf-8")
        original = os.environ.get("AAIS_RUNTIME_DIR")
        os.environ["AAIS_RUNTIME_DIR"] = str(temp_root)
        try:
            snapshot = build_operator_console_snapshot(runtime=None)
            trust = snapshot.get("trust_bundle") or {}
            self.assertEqual(trust.get("overall_status"), "pass")
            self.assertEqual(trust.get("claim_status"), "proven")
        finally:
            if original is None:
                os.environ.pop("AAIS_RUNTIME_DIR", None)
            else:
                os.environ["AAIS_RUNTIME_DIR"] = original
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_debt_register_lists_open_items(self):
        snapshot = build_operator_console_snapshot(runtime=None)
        debt = snapshot.get("debt_register") or {}
        self.assertGreaterEqual(debt.get("open", 0), 1)
        ids = {item.get("id") for item in debt.get("items") or []}
        self.assertIn("UGR-D5", ids)


class TestOperatorConsoleMeshHealth(unittest.TestCase):
    def test_mesh_health_poll_is_readout_only(self):
        payload = poll_mesh_health(timeout=0.5)
        self.assertEqual(payload.get("runtime_effect"), "readout_only")
        self.assertIn("services", payload)
        self.assertIn("poll_status", payload)


class TestOperatorConsoleTraceViewer(unittest.TestCase):
    def test_trace_viewer_empty_when_missing(self):
        temp_root = Path(tempfile.mkdtemp(prefix="operator-console-traces-"))
        original = os.environ.get("AAIS_RUNTIME_DIR")
        os.environ["AAIS_RUNTIME_DIR"] = str(temp_root)
        try:
            payload = load_deliberation_traces(runtime=None, limit=5)
            self.assertEqual(payload.get("status"), "empty")
            self.assertEqual(payload.get("trace_count"), 0)
        finally:
            if original is None:
                os.environ.pop("AAIS_RUNTIME_DIR", None)
            else:
                os.environ["AAIS_RUNTIME_DIR"] = original
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_trace_viewer_reads_jsonl(self):
        temp_root = Path(tempfile.mkdtemp(prefix="operator-console-traces-"))
        trace_dir = temp_root / "ugr"
        trace_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "trace_id": "trace-test-1",
            "status": "ok",
            "intent": "smoke",
            "lane_count": 2,
            "accepted_beliefs": 1,
            "rail_decision": {"rail": "NORMAL", "risk": "low"},
        }
        (trace_dir / "traces.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
        original = os.environ.get("AAIS_RUNTIME_DIR")
        os.environ["AAIS_RUNTIME_DIR"] = str(temp_root)
        try:
            payload = load_deliberation_traces(runtime=None, limit=5)
            self.assertEqual(payload.get("status"), "ok")
            self.assertEqual(payload.get("trace_count"), 1)
            summaries = payload.get("summaries") or []
            self.assertEqual(summaries[0].get("trace_id"), "trace-test-1")
            detail = load_deliberation_traces(runtime=None, trace_id="trace-test-1")
            self.assertEqual(detail.get("status"), "ok")
            self.assertEqual(len(detail.get("traces") or []), 1)
        finally:
            if original is None:
                os.environ.pop("AAIS_RUNTIME_DIR", None)
            else:
                os.environ["AAIS_RUNTIME_DIR"] = original
            shutil.rmtree(temp_root, ignore_errors=True)


class TestOperatorConsoleForgePlatform(unittest.TestCase):
    def test_forge_platform_dashboard_loads(self):
        payload = load_forge_platform_dashboard(live_checks=False)
        self.assertEqual(payload.get("runtime_effect"), "readout_only")
        self.assertIn(payload.get("status"), {"ok", "missing", "error"})


if __name__ == "__main__":
    unittest.main()
