from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = REPO_ROOT / "wolf-cog-os" / "scripts" / "forge-platform-dashboard.py"


class ForgePlatformDashboardTests(unittest.TestCase):
    def test_json_dashboard_loads_registries(self) -> None:
        cmd = [sys.executable, str(DASHBOARD), "--json"]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "forge-platform-dashboard.v1")
        self.assertGreater(payload["substrates"]["substrate_count"], 0)
        self.assertGreater(len(payload["backends"]["backends"]), 0)
        self.assertGreater(len(payload["replay_adapters"]["adapters"]), 0)
        enabled = [row for row in payload["replay_adapters"]["adapters"] if row["enabled"]]
        self.assertTrue(any(row["id"] == "debian-live-layout" for row in enabled))

    def test_text_dashboard_renders_sections(self) -> None:
        cmd = [sys.executable, str(DASHBOARD)]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Substrate classes", result.stdout)
        self.assertIn("Rootfs backends", result.stdout)
        self.assertIn("Replay adapters", result.stdout)
        self.assertIn("Lineage / gates", result.stdout)


if __name__ == "__main__":
    unittest.main()
