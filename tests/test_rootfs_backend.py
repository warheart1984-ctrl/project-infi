from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "wolf-cog-os" / "scripts" / "validate-rootfs-backend.py"


class RootfsBackendTests(unittest.TestCase):
    def test_backend_registry_loads(self) -> None:
        registry_path = REPO_ROOT / "wolf-cog-os" / "forge" / "backends" / "registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["default_backend_id"], "debootstrap")
        for backend_id in ("debootstrap", "pacstrap", "dnfroot", "apkroot"):
            self.assertIn(backend_id, registry["backends"])

    def test_registry_only_validation_passes(self) -> None:
        cmd = [
            sys.executable,
            str(VALIDATOR),
            "--backend",
            "debootstrap",
            "--registry-only",
            "--mode",
            "fail",
        ]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_pacstrap_registry_only_passes(self) -> None:
        cmd = [
            sys.executable,
            str(VALIDATOR),
            "--backend",
            "pacstrap",
            "--registry-only",
            "--mode",
            "fail",
        ]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_stub_backend_reports_warn(self) -> None:
        cmd = [
            sys.executable,
            str(VALIDATOR),
            "--backend",
            "dnfroot",
            "--registry-only",
            "--mode",
            "fail",
        ]
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("stub-only", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
