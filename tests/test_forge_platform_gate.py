from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / ".github" / "scripts" / "check-forge-platform-gate.py"


class ForgePlatformGateTests(unittest.TestCase):
    def test_platform_gate_produces_pass_report(self) -> None:
        output = REPO_ROOT / "ci-artifacts" / "test-forge-platform-gate-report.json"
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
        self.assertTrue(any(row.get("gate_id") == "G" and row.get("status") == "pass" for row in payload["checks"]))
        self.assertEqual(payload["meta_architect_gate"].get("decision"), "approve")


if __name__ == "__main__":
    unittest.main()
