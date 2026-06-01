from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class NightlyEvolutionTests(unittest.TestCase):
    def test_nightly_evolution_dry_run(self) -> None:
        script = REPO_ROOT / "wolf-cog-os" / "scripts" / "test" / "forge-nightly-evolution.sh"
        result = subprocess.run(
            ["bash", str(script), "--dry-run"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
