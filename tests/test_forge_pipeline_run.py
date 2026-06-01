from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RESOLVER = REPO_ROOT / "wolf-cog-os" / "scripts" / "lib" / "resolve-pipeline-env.py"
RUNNER = REPO_ROOT / "wolf-cog-os" / "scripts" / "run-forge-pipeline.sh"


class ForgePipelineRunTests(unittest.TestCase):
    def test_resolve_daily_driver_backend(self) -> None:
        pipeline = REPO_ROOT / "wolf-cog-os" / "forge" / "pipelines" / "daily-driver.yaml"
        result = subprocess.run(
            [sys.executable, str(RESOLVER), str(pipeline), "--json"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("daily-driver", result.stdout)
        self.assertIn("debootstrap", result.stdout)
        self.assertIn("raw-img", result.stdout)

    def test_resolve_arch_pipeline_backend(self) -> None:
        pipeline = REPO_ROOT / "wolf-cog-os" / "forge" / "pipelines" / "daily-driver-arch.yaml"
        result = subprocess.run(
            [sys.executable, str(RESOLVER), str(pipeline), "--json"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("pacstrap", result.stdout)

    def test_run_forge_pipeline_script_exists(self) -> None:
        self.assertTrue(RUNNER.is_file())
        text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("forge_pipeline_emit_cloud_outputs", text)


if __name__ == "__main__":
    unittest.main()
