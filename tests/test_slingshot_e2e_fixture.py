"""Slingshot E2E fixture — preload, verify, launch receipt (production hardening M5)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN_CASE = "slingshot-e2e-fixture"
CLEAN_FIXTURE = ROOT / "mechanic" / "fixtures" / "sample-customer-repo-clean"
CLEAN_TRACE = CLEAN_FIXTURE / "traces" / "session.ndjson"


class TestSlingshotE2EFixture(unittest.TestCase):
    def test_preload_verify_launch_receipt_chain(self):
        runtime = ROOT / ".runtime" / "slingshot" / CLEAN_CASE
        if runtime.exists():
            for path in sorted(runtime.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
            for path in sorted(runtime.rglob("*"), reverse=True):
                if path.is_dir():
                    path.rmdir()

        preload = subprocess.run(
            [
                sys.executable,
                "-m",
                "slingshot",
                "preload",
                "--case-id",
                CLEAN_CASE,
                "--repo",
                str(CLEAN_FIXTURE),
                "--trace-path",
                str(CLEAN_TRACE),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(preload.returncode, 0, preload.stderr)

        frame_path = runtime / "SLINGSHOT_FRAME.v1.json"
        packet_path = runtime / "SLINGSHOT_PACKET.v1.json"
        self.assertTrue(frame_path.is_file())
        self.assertTrue(packet_path.is_file())
        frame = json.loads(frame_path.read_text(encoding="utf-8"))
        self.assertFalse(frame.get("launch_blocked"))
        self.assertEqual(int(frame.get("drift_count") or 0), 0)

        verify = subprocess.run(
            [sys.executable, "-m", "slingshot", "verify", "--case-id", CLEAN_CASE, "--repo", str(CLEAN_FIXTURE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)
        verify_payload = json.loads(verify.stdout or "{}")
        self.assertTrue(verify_payload.get("ok"))

        status = subprocess.run(
            [sys.executable, "-m", "slingshot", "status", "--case-id", CLEAN_CASE],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        status_payload = json.loads(status.stdout or "{}")
        self.assertTrue(status_payload.get("artifacts_present"))


if __name__ == "__main__":
    unittest.main()
