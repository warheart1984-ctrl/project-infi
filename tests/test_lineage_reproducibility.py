from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-lineage-reproducibility.py"
EMITTER = REPO_ROOT / "wolf-cog-os" / "scripts" / "emit-forge-lineage.py"


class LineageReproducibilityTests(unittest.TestCase):
    def test_same_components_same_lineage_id(self) -> None:
        out_a = REPO_ROOT / "ci-artifacts" / "test-lineage-repro-a.json"
        out_b = REPO_ROOT / "ci-artifacts" / "test-lineage-repro-b.json"
        base = [
            sys.executable,
            str(EMITTER),
            "--pipeline",
            "wolf-cog-os/forge/pipelines/daily-driver.yaml",
            "--git-commit",
            "deadbeef",
        ]
        emit_a = subprocess.run(
            [*base, "--output", str(out_a.relative_to(REPO_ROOT)), "--build-host", "host-a"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        emit_b = subprocess.run(
            [*base, "--output", str(out_b.relative_to(REPO_ROOT)), "--build-host", "host-b"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(emit_a.returncode, 0, msg=emit_a.stdout + emit_a.stderr)
        self.assertEqual(emit_b.returncode, 0, msg=emit_b.stdout + emit_b.stderr)

        check = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--lineage-a",
                str(out_a.relative_to(REPO_ROOT)),
                "--lineage-b",
                str(out_b.relative_to(REPO_ROOT)),
                "--ignore-build-host",
                "--mode",
                "fail",
            ],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, msg=check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
