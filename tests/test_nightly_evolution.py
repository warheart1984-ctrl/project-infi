"""Smoke tests for nightly evolution ledger script paths."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class NightlyEvolutionTests(unittest.TestCase):
    def test_nightly_evolution_dry_run_script(self) -> None:
        script = REPO_ROOT / "cog-os/scripts/test/forge-nightly-evolution.sh"
        self.assertTrue(script.is_file(), msg=str(script))
        proc = subprocess.run(
            ["bash", str(script.relative_to(REPO_ROOT)), "--dry-run"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
