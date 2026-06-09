from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / ".github" / "scripts" / "check-forge-shippable-gate.py"


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
        cog_os_active = (REPO_ROOT / "cog-os" / "host" / "src" / "init.c").is_file()
        if cog_os_active:
            self.assertFalse(payload.get("retired"))
        else:
            self.assertTrue(payload.get("retired"))
        meta = payload.get("meta_architect_gate") or {}
        self.assertEqual(meta.get("gate_id"), "F")

    def test_fixture_artifacts_gate_passes(self) -> None:
        fixture = REPO_ROOT / "cog-os" / "scripts" / "test" / "fixtures" / "promotion-forge-rc"
        legacy = REPO_ROOT / "wolf-cog-os" / "scripts" / "test" / "fixtures" / "promotion-forge-rc"
        if not fixture.is_dir() and legacy.is_dir():
            fixture = legacy
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
