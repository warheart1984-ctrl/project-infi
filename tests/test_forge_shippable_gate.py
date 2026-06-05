from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / ".github" / "scripts" / "check-forge-shippable-gate.py"
FORGE_GATES_AVAILABLE = sys.platform != "win32" and shutil.which("bash") is not None


@unittest.skipUnless(FORGE_GATES_AVAILABLE, "forge shippable gate requires bash on a Unix host")
class ForgeShippableGateTests(unittest.TestCase):
    def test_local_gate_produces_pass_report(self) -> None:
        output = REPO_ROOT / "ci-artifacts" / "test-forge-shippable-gate-report.json"
        cmd = [
            sys.executable,
            str(CHECKER),
            "--mode",
            "fail",
            "--output",
            str(output),
        ]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(any(row.get("gate_id") == "F" and row.get("status") == "pending" for row in payload["checks"]))

    def test_fixture_artifacts_gate_passes(self) -> None:
        fixture = REPO_ROOT / "wolf-cog-os" / "scripts" / "test" / "fixtures" / "promotion-forge-rc"
        if not fixture.is_dir():
            self.skipTest("promotion fixture missing")
        output = REPO_ROOT / "ci-artifacts" / "test-forge-shippable-gate-artifacts.json"
        cmd = [
            sys.executable,
            str(CHECKER),
            "--mode",
            "fail",
            "--artifacts-dir",
            str(fixture.relative_to(REPO_ROOT)),
            "--source-run-id",
            "424242",
            "--expected-profile-id",
            "forge-selfhosted",
            "--output",
            str(output),
        ]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(output.read_text(encoding="utf-8"))
        gate_f = next(row for row in payload["checks"] if row.get("gate_id") == "F")
        self.assertEqual(gate_f.get("status"), "warn")


if __name__ == "__main__":
    unittest.main()
