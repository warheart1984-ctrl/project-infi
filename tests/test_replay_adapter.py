from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-replay-adapter.py"


class ReplayAdapterTests(unittest.TestCase):
    def test_replay_adapter_registry_passes(self) -> None:
        cmd = [sys.executable, str(VALIDATOR), "--mode", "fail"]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("production=2", result.stdout)

    def test_production_modules_exist(self) -> None:
        module_dir = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "replay-adapters"
        for adapter in ("debian-live-layout", "ubuntu-live-layout"):
            self.assertTrue((module_dir / f"{adapter}.sh").is_file(), msg=adapter)


if __name__ == "__main__":
    unittest.main()
